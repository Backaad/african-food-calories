#!/usr/bin/env python3
"""Publish the model and the description of the data on Hugging Face.

    python hub/publish.py --out /tmp/hub              # build the two folders only
    HF_TOKEN=... python hub/publish.py --out /tmp/hub --upload

Two repositories under HF_USER (default: backaad):
- model   `african-food-calories`: model.tflite, labels, model_info.json,
  metrics, the model card (docs/model-card.md with Hugging Face metadata).
- dataset `african-food-calories-data`: no image (CamerFood10 must never be
  redistributed and Commons photos stay on Commons); the list of sources and
  licences, the per-image credits, the data inventory and the nutrition data.

The token comes from the environment (a GitHub secret in CI), never from a file.
"""

import argparse
import os
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "training" / "results" / "2026-10-12-run2"
GITHUB = "https://github.com/Backaad/african-food-calories"

MODEL_FILES = ["model.tflite", "model_info.json", "labels.txt", "metrics.json", "training_log.json",
               "dataset_summary.json", "confusion_test.png"]

MODEL_HEADER = {
    "license": "cc-by-nc-4.0",
    "language": ["en", "fr"],
    "pipeline_tag": "image-classification",
    "tags": ["food", "africa", "tflite", "mobilenetv3", "calories", "offline"],
    "datasets": ["{user}/african-food-calories-data"],
    "metrics": ["accuracy"],
}

DATA_HEADER = {
    "license": "other",
    "license_name": "per-source",
    "license_link": "LICENSES.md",
    "language": ["en", "fr"],
    "pretty_name": "African Food Calories: data sources and nutrition",
    "tags": ["food", "africa", "nutrition", "data-provenance"],
    "size_categories": ["n<1K"],
}


def card(header: dict, body: str, user: str) -> str:
    text = yaml.safe_dump(header, sort_keys=False, allow_unicode=True).replace("{user}", user)
    return f"---\n{text}---\n\n{body}"


def relink(text: str) -> str:
    """Make repository-relative links of a docs/ page absolute GitHub links."""
    return text.replace("](../", f"]({GITHUB}/blob/main/")


def build_model(out: Path, user: str) -> Path:
    folder = out / "model"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    for name in MODEL_FILES:
        shutil.copy(RUN / name, folder / name)
    model_card = relink((ROOT / "docs" / "model-card.md").read_text(encoding="utf-8"))
    intro = (f"Source code, training notebook and Flutter app: {GITHUB}. "
             f"Data sources and licences: [{user}/african-food-calories-data]"
             f"(https://huggingface.co/datasets/{user}/african-food-calories-data).\n\n")
    title, rest = model_card.split("\n", 1)
    (folder / "README.md").write_text(card(MODEL_HEADER, f"{title}\n\n{intro}{rest}", user), encoding="utf-8")
    return folder


def build_data(out: Path, user: str) -> Path:
    folder = out / "data"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    shutil.copy(ROOT / "data" / "sources.yaml", folder / "sources.yaml")
    shutil.copy(ROOT / "data" / "dishes.yaml", folder / "dishes.yaml")
    shutil.copy(RUN / "ATTRIBUTION.csv", folder / "ATTRIBUTION.csv")
    shutil.copy(ROOT / "nutrition" / "dishes.json", folder / "nutrition_dishes.json")
    shutil.copy(ROOT / "nutrition" / "recipes.yaml", folder / "nutrition_recipes.yaml")
    shutil.copy(ROOT / "docs" / "data-inventory.md", folder / "data-inventory.md")
    shutil.copy(ROOT / "docs" / "nutrition-method.md", folder / "nutrition-method.md")

    sources = yaml.safe_load((ROOT / "data" / "sources.yaml").read_text(encoding="utf-8"))["sources"]
    rows = []
    for s in sources:
        lic = s.get("license") or {}
        name = (lic.get("name") if isinstance(lic, dict) else lic) or s.get("declared_license", "")
        rows.append(f"| {s['name']} | {s['status']} | {str(name).replace('|', '/')} |")
    table = "\n".join(rows)
    (folder / "LICENSES.md").write_text(f"""# Licences

Each file here keeps the licence of what it describes:

- `ATTRIBUTION.csv`: one row per Wikimedia Commons photo used to train the model,
  with its author and licence (CC0, public domain, CC BY or CC BY-SA). The photos
  themselves are not copied here; they stay on Commons.
- `nutrition_dishes.json`: values computed from the FAO/INFOODS Food Composition
  Table for Western Africa (2019), © FAO 2020, used for a non-commercial product
  with acknowledgement of FAO as source and copyright holder; FAO does not
  endorse this project.
- The other files (lists, recipes, inventory, method) are part of the project
  and under the MIT licence of its code: {GITHUB}/blob/main/LICENSE.

## Image sources considered

| Source | Status | Licence (as declared by the source) |
|---|---|---|
{table}

`approved_training_only` (CamerFood10): copyright of the images is not cleared;
used for training only, never redistributed; a model trained on it is CC BY-NC 4.0.
Details and reasons for every status: `sources.yaml`.
""", encoding="utf-8")

    body = f"""# African Food Calories: data sources and nutrition

This repository **contains no image**. It describes the data behind the
[African Food Calories]({GITHUB}) app and model
([{user}/african-food-calories](https://huggingface.co/{user}/african-food-calories)):
where every training image comes from, under which licence, and how the
calories of each dish are estimated.

| File | Content |
|---|---|
| `sources.yaml` | Every image source considered, its licence, authors to credit, and the decision (approved, training only, excluded...) with its reason |
| `ATTRIBUTION.csv` | Author and licence of each Wikimedia Commons photo used for training |
| `data-inventory.md` | Number of usable images per dish and source |
| `dishes.yaml` | The 44 dishes, their names in English and French, countries |
| `nutrition_recipes.yaml` | Standard recipe of each dish: grams of each WAFCT 2019 food per 100 g |
| `nutrition_dishes.json` | Energy, protein, fat, carbohydrate, fibre per 100 g and per portion, as low / typical / high |
| `nutrition-method.md` | How the values are computed, and their limits |
| `LICENSES.md` | Licence of each file and of each source |

The images can be downloaded again from their sources with the scripts in
[`data/`]({GITHUB}/tree/main/data). CamerFood10 is used for training only and is
never redistributed.

**Nutrition values are estimates to be validated by a nutritionist. They are
not medical advice.**
"""
    (folder / "README.md").write_text(card(DATA_HEADER, body, user), encoding="utf-8")
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--user", default=os.environ.get("HF_USER", "backaad"))
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()
    model, data = build_model(args.out, args.user), build_data(args.out, args.user)
    print(f"built {model} and {data}")
    if not args.upload:
        return
    from huggingface_hub import HfApi

    token = os.environ.get("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN is not set")
    api = HfApi(token=token)
    for folder, repo, kind in [(model, "african-food-calories", "model"),
                               (data, "african-food-calories-data", "dataset")]:
        repo_id = f"{args.user}/{repo}"
        api.create_repo(repo_id, repo_type=kind, exist_ok=True)
        api.upload_folder(folder_path=str(folder), repo_id=repo_id, repo_type=kind,
                          commit_message=f"Publish from {GITHUB}")
        print(f"uploaded https://huggingface.co/{'datasets/' if kind == 'dataset' else ''}{repo_id}")


if __name__ == "__main__":
    main()
