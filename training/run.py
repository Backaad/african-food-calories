#!/usr/bin/env python3
"""Prepare the images, train, evaluate and export the classifier.

    python training/run.py prepare --work /kaggle/working/afc
    python training/run.py train   --work /kaggle/working/afc [--teacher]
    python training/run.py finish  --work /kaggle/working/afc
    python training/run.py all     --work /kaggle/working/afc [--teacher]

Everything goes under --work: raw downloads, the dataset, the models and
`outputs/` (model.tflite, labels.txt, model_info.json, metrics.json, plots).
Only `outputs/` is meant to leave the machine; it contains no image.
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from afctrain import OTHER, ROOT  # noqa: E402

CONFIG = Path(__file__).resolve().parent / "config.yaml"
MODEL_LICENSE = "CC BY-NC 4.0"


def load_config(path: Path = CONFIG, overrides: dict | None = None) -> dict:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key, value in (overrides or {}).items():
        config[key] = value
    return config


# ---------------------------------------------------------------- data


def split_rows(dataset: Path) -> tuple[list[str], dict[str, list[dict]]]:
    from afctrain.prepare import read_manifest

    summary = json.loads((dataset / "summary.json").read_text(encoding="utf-8"))
    rows = read_manifest(dataset)
    by_split = {s: [r for r in rows if r["split"] == s] for s in ("train", "val", "test")}
    return summary["classes"], by_split


def as_arrays(rows: list[dict], classes: list[str], dataset: Path):
    index = {c: i for i, c in enumerate(classes)}
    return [str(dataset / r["path"]) for r in rows], [index[r["label"]] for r in rows]


def datasets(dataset: Path, config: dict, batch_size: int):
    from afctrain.model import make_dataset

    classes, rows = split_rows(dataset)
    size, seed = config["image_size"], config["seed"]
    built = {}
    for split in ("train", "val", "test"):
        paths, labels = as_arrays(rows[split], classes, dataset)
        built[split] = (make_dataset(paths, labels, size, batch_size, training=split == "train", seed=seed), labels)
    return classes, rows, built


# ---------------------------------------------------------------- commands


def cmd_prepare(work: Path, config: dict, with_camerfood: bool) -> dict:
    from afctrain.prepare import prepare

    summary = prepare(work, config, with_camerfood=with_camerfood)
    print(json.dumps({k: summary[k] for k in ("classes", "images", "per_class", "per_source")}, indent=2))
    return summary


def _train_one(kind: str, config: dict, dataset: Path, weights_source="imagenet"):
    import keras
    from afctrain.model import build_classifier, class_weights, train_classifier

    keras.utils.set_random_seed(config["seed"])
    cfg = config[kind]
    classes, _, built = datasets(dataset, config, cfg["batch_size"])
    model, backbone = build_classifier(cfg["arch"], len(classes), config["image_size"], weights_source, cfg["dropout"])
    weights = class_weights(built["train"][1], len(classes))
    history = train_classifier(model, backbone, built["train"][0], built["val"][0], cfg, weights)
    val_acc = float(model.evaluate(built["val"][0], verbose=0, return_dict=True)["accuracy"])
    return model, backbone, history, val_acc, built


def cmd_train(work: Path, config: dict, with_teacher: bool, weights_source="imagenet") -> dict:
    import keras

    dataset, models = work / "dataset", work / "models"
    models.mkdir(parents=True, exist_ok=True)
    log = {"started": time.strftime("%Y-%m-%d %H:%M:%S")}

    student, _, history, val_acc, built = _train_one("student", config, dataset, weights_source)
    student.save(models / "student.keras")
    log["student"] = {"arch": config["student"]["arch"], "val_accuracy": round(val_acc, 4), "history": history}
    final, final_name = student, "student"

    if with_teacher:
        from afctrain.model import class_weights, distill

        teacher, _, t_history, t_acc, _ = _train_one("teacher", config, dataset, weights_source)
        teacher.save(models / "teacher.keras")
        log["teacher"] = {"arch": config["teacher"]["arch"], "val_accuracy": round(t_acc, 4), "history": t_history}

        distilled = keras.models.clone_model(student)
        distilled.set_weights(student.get_weights())
        backbone = next(layer for layer in distilled.layers if isinstance(layer, keras.Model))
        classes, _ = split_rows(dataset)
        d_history = distill(distilled, backbone, teacher, built["train"][0], built["val"][0], config["distillation"],
                            class_weights(built["train"][1], len(classes)))
        distilled.compile(metrics=["accuracy"])
        d_acc = float(distilled.evaluate(built["val"][0], verbose=0, return_dict=True)["accuracy"])
        log["distilled"] = {"val_accuracy": round(d_acc, 4), "history": d_history}
        if d_acc > val_acc:  # keep distillation only if it measurably helps on validation
            final, final_name = distilled, "distilled"

    final.save(models / "final.keras")
    log["final"] = final_name
    log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    (models / "training_log.json").write_text(json.dumps(log, indent=2, default=float) + "\n", encoding="utf-8")
    print(f"final model: {final_name}")
    return log


def _predict(model, ds):
    import numpy as np

    return np.concatenate([model.predict_on_batch(x) for x, _ in ds], axis=0)


def _images(paths: list[str], size: int):
    import numpy as np
    from afctrain.model import load_image

    return np.stack([load_image(p, size).numpy() for p in paths])


def dish_names(classes: list[str]) -> dict[str, dict]:
    dishes = yaml.safe_load((ROOT / "data" / "dishes.yaml").read_text(encoding="utf-8"))["dishes"]
    names = {d["id"]: d["names"] for d in dishes}
    names[OTHER] = {"en": "Dish not recognised", "fr": "Plat non reconnu"}
    return {c: names.get(c, {"en": c, "fr": c}) for c in classes}


def model_license(per_source: dict) -> dict:
    """CamerFood10 is a training-only source: any model trained on it is non-commercial."""
    if "camerfood10" in per_source:
        return {"license": MODEL_LICENSE,
                "license_reason": "trained partly on CamerFood10 (training-only source, see data/sources.yaml)"}
    return {"license": "to be chosen by the project owner",
            "license_reason": "trained on openly licensed images only (CC0, PD, CC BY, CC BY-SA)"}


def cmd_finish(work: Path, config: dict) -> dict:
    import keras
    import numpy as np
    from afctrain.evaluate import choose_threshold, plot_confusion, report
    from afctrain.export import parity, tflite_predict, to_tflite_float16
    from afctrain.model import with_softmax

    dataset, out = work / "dataset", work / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    classes, rows, built = datasets(dataset, config, config["student"]["batch_size"])
    other = classes.index(OTHER)
    model = with_softmax(keras.models.load_model(work / "models" / "final.keras"))

    val_probs = _predict(model, built["val"][0])
    threshold = choose_threshold(val_probs, np.asarray(built["val"][1]), other)
    test_probs = _predict(model, built["test"][0])
    y_test = np.asarray(built["test"][1])
    metrics = report(test_probs, y_test, classes, other, threshold, [r["source"] for r in rows["test"]])
    metrics["validation"] = report(val_probs, np.asarray(built["val"][1]), classes, other, threshold)["accuracy_final"]
    cm = np.asarray(metrics["confusion_matrix"]["rows_true_cols_predicted"])
    plot_confusion(cm, classes, out / "confusion_test.png", f"Test set, threshold {threshold:.2f}")

    tflite = to_tflite_float16(model, out / "model.tflite")
    paths, _ = as_arrays(rows["test"], classes, dataset)
    lite = np.concatenate([tflite_predict(tflite, _images(paths[i:i + 64], config["image_size"]))
                           for i in range(0, len(paths), 64)])
    metrics["tflite_parity"] = parity(test_probs, lite)

    training_log = json.loads((work / "models" / "training_log.json").read_text(encoding="utf-8"))
    summary = json.loads((dataset / "summary.json").read_text(encoding="utf-8"))
    (out / "labels.txt").write_text("\n".join(classes) + "\n", encoding="utf-8")
    info = {
        "labels": classes,
        "names": dish_names(classes),
        "other_label": OTHER,
        "input": {"size": [config["image_size"], config["image_size"]], "channels": "RGB",
                  "dtype": "float32", "range": [0, 255], "resize": "whole image, bilinear, no crop"},
        "output": "probabilities (softmax), one per label",
        "threshold": threshold,
        "decision": "show the top label if its probability >= threshold and it is not 'other'; else 'dish not recognised'",
        "model": {"final": training_log["final"], "student_arch": config["student"]["arch"]},
        **model_license(summary["per_source"]),
        "dataset": {k: summary[k] for k in ("images", "per_class", "per_source", "dishes_learnt_as_other")},
        "created": time.strftime("%Y-%m-%d"),
    }
    (out / "model_info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    shutil.copy(work / "models" / "training_log.json", out / "training_log.json")
    shutil.copy(dataset / "summary.json", out / "dataset_summary.json")
    shutil.copy(dataset / "ATTRIBUTION.csv", out / "ATTRIBUTION.csv")
    archive = shutil.make_archive(str(work / "afc_model_outputs"), "zip", out)
    print(json.dumps({k: metrics[k] for k in ("threshold", "accuracy_final", "dish_images", "other_images",
                                                "tflite_parity")}, indent=2))
    print(f"outputs: {out}\narchive: {archive}")
    return metrics


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["prepare", "train", "finish", "all"])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--teacher", action="store_true", help="also train a teacher and try distillation")
    parser.add_argument("--no-camerfood", action="store_true", help="leave out CamerFood10 (open-licence data only)")
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.command in ("prepare", "all"):
        cmd_prepare(args.work, config, with_camerfood=not args.no_camerfood)
    if args.command in ("train", "all"):
        cmd_train(args.work, config, with_teacher=args.teacher)
    if args.command in ("finish", "all"):
        cmd_finish(args.work, config)


if __name__ == "__main__":
    main()
