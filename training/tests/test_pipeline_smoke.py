"""End-to-end smoke test: tiny synthetic dataset, untrained backbone, CPU.

Checks that training (with teacher and distillation), evaluation, TFLite export
and packaging run and produce consistent files. It says nothing about accuracy.
"""

import csv
import json
import zipfile

import numpy as np
import pytest
from PIL import Image

pytest.importorskip("tensorflow")

import run  # noqa: E402

COLORS = {"fufu": (230, 220, 200), "ugali": (250, 250, 240), "other": (40, 90, 200)}


def make_dataset(root):
    rows = []
    rng = np.random.default_rng(0)
    for label, color in COLORS.items():
        for split, n in (("train", 12), ("val", 4), ("test", 4)):
            for i in range(n):
                arr = np.clip(np.array(color) + rng.integers(-20, 20, (40, 40, 3)), 0, 255).astype("uint8")
                rel = f"images/{split}/{label}/{i}.jpg"
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(arr).save(root / rel)
                rows.append({"path": rel, "label": label, "dish": label, "source": "synthetic",
                             "group": f"{label}{split}{i}", "split": split})
    with open(root / "manifest.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "label", "dish", "source", "group", "split"])
        writer.writeheader()
        writer.writerows(rows)
    summary = {"classes": ["fufu", "ugali", "other"], "images": len(rows), "per_class": {},
               "per_source": {"synthetic": len(rows)}, "dishes_learnt_as_other": []}
    (root / "summary.json").write_text(json.dumps(summary))
    (root / "ATTRIBUTION.csv").write_text("file,dish,author,license,license_url,page\n")


def tiny_config():
    config = run.load_config()
    config["image_size"] = 64
    small = {"arch": "mobilenet_v3_small", "batch_size": 8, "dropout": 0.0, "epochs_head": 1, "lr_head": 0.01,
             "epochs_finetune": 1, "fine_tune_layers": 5, "lr_finetune": 0.001, "patience": 1}
    config["student"] = dict(small)
    config["teacher"] = dict(small)
    config["distillation"] = {"alpha": 0.5, "temperature": 2.0, "epochs": 1, "lr": 0.001, "fine_tune_layers": 5,
                              "patience": 1}
    return config


def test_train_finish_with_distillation(tmp_path):
    make_dataset(tmp_path / "dataset")
    config = tiny_config()
    log = run.cmd_train(tmp_path, config, with_teacher=True, weights_source=None)
    assert log["final"] in {"student", "distilled"}
    assert {"student", "teacher", "distilled"} <= set(log)

    metrics = run.cmd_finish(tmp_path, config)
    out = tmp_path / "outputs"
    for name in ("model.tflite", "labels.txt", "model_info.json", "metrics.json", "confusion_test.png",
                 "training_log.json", "dataset_summary.json", "ATTRIBUTION.csv"):
        assert (out / name).exists(), name
    assert metrics["images"] == 12
    assert metrics["tflite_parity"]["top1_agreement"] >= 0.9
    assert metrics["tflite_parity"]["max_abs_probability_difference"] < 0.05
    info = json.loads((out / "model_info.json").read_text())
    assert info["labels"] == ["fufu", "ugali", "other"]
    assert info["names"]["other"]["fr"] == "Plat non reconnu"
    assert info["license"] == "to be chosen by the project owner"
    with zipfile.ZipFile(tmp_path / "afc_model_outputs.zip") as z:
        assert not any(n.endswith(".jpg") for n in z.namelist())  # no image ever leaves the machine


def test_model_license_follows_the_data():
    assert run.model_license({"camerfood10": 3, "wikimedia-commons": 5})["license"] == "CC BY-NC 4.0"
    assert run.model_license({"wikimedia-commons": 5})["license"] == "to be chosen by the project owner"
