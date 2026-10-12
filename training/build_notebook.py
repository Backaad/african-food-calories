#!/usr/bin/env python3
"""Generate training/notebooks/train_classifier.ipynb (run after editing this file).

The notebook is a thin wrapper around training/run.py, so the logic stays in
tested Python files. It runs unchanged on Kaggle and on Google Colab.
"""

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

OUT = Path(__file__).resolve().parent / "notebooks" / "train_classifier.ipynb"

CELLS = [
    new_markdown_cell("""# african-food-calories: train the dish classifier

Runs on **Kaggle** or **Google Colab**, with a GPU.

1. Downloads the images (Wikimedia Commons, open licences; CamerFood10, training only).
2. Trains a small MobileNetV3 model for the phone; optionally a bigger teacher model and distillation.
3. Measures it honestly on a test set never used for training (per-dish accuracy, confusion matrix, refusals).
4. Exports it to TensorFlow Lite (float16) and checks the phone model answers like the original.
5. Packs the results in `afc_model_outputs.zip`: model, labels, metrics, plots. **No image is included**:
   CamerFood10 images must never be redistributed (see `data/sources.yaml`).

Before running: Kaggle: *Settings → Accelerator → GPU*, and *Settings → Internet → On*.
Colab: *Runtime → Change runtime type → T4 GPU*. Then *Run all*."""),
    new_markdown_cell("## 1. Setup"),
    new_code_cell("""import os, sys

ON_KAGGLE = os.path.exists("/kaggle/working")
ON_COLAB = "google.colab" in sys.modules
# Images and models stay in a temporary folder that is not saved or shared.
WORK = "/tmp/afc" if (ON_KAGGLE or ON_COLAB) else os.path.abspath("afc_work")
SAVE_DIR = "/kaggle/working" if ON_KAGGLE else ("/content" if ON_COLAB else os.getcwd())
REPO, BRANCH = "https://github.com/Backaad/african-food-calories.git", "main"
CODE = "/tmp/african-food-calories" if (ON_KAGGLE or ON_COLAB) else os.path.abspath("african-food-calories")

if not os.path.exists(CODE):
    !git clone --depth 1 -b {BRANCH} {REPO} {CODE}
%cd {CODE}
!pip install -q -r training/requirements.txt -r data/requirements.txt
print("platform:", "Kaggle" if ON_KAGGLE else "Colab" if ON_COLAB else "local", "| work dir:", WORK)"""),
    new_code_cell("""import tensorflow as tf, keras
print("TensorFlow", tf.__version__, "| Keras", keras.__version__)
gpus = tf.config.list_physical_devices("GPU")
print("GPU:", gpus or "NONE - training will be very slow; turn the GPU on (see top of the notebook)")"""),
    new_markdown_cell("""## 2. Options

- `USE_CAMERFOOD10`: CamerFood10 adds most Cameroonian images (bobolo, koki, achu, puff-puff...). A model
  trained with it is **non-commercial (CC BY-NC 4.0)**. Set to `False` for open-licence images only.
- `USE_TEACHER`: also trains a big EfficientNetV2-S "teacher" and distils it into the small model. This
  adds two more trainings, so it takes much longer. The distilled model is kept **only if it scores better
  on validation**."""),
    new_code_cell("""USE_CAMERFOOD10 = True
USE_TEACHER = False"""),
    new_markdown_cell("## 3. Prepare the images"),
    new_code_cell("""flag = "" if USE_CAMERFOOD10 else "--no-camerfood"
!python training/run.py prepare --work {WORK} {flag}"""),
    new_markdown_cell("## 4. Train"),
    new_code_cell("""flag = "--teacher" if USE_TEACHER else ""
!python training/run.py train --work {WORK} {flag}"""),
    new_markdown_cell("## 5. Evaluate on the test set and export to TensorFlow Lite"),
    new_code_cell("""!python training/run.py finish --work {WORK}"""),
    new_code_cell("""import json
from IPython.display import Image, display

m = json.load(open(f"{WORK}/outputs/metrics.json"))
print(f"threshold {m['threshold']} | final accuracy {m['accuracy_final']} | top-3 (no refusal) {m['accuracy_top3_no_refusal']}")
print("dish images:", m["dish_images"])
print("other images:", m["other_images"])
print("per source:", m.get("per_source"))
print("TFLite vs original:", m["tflite_parity"])
for name, c in m["per_class"].items():
    print(f"  {name:15} test images {c['support']:4}  accuracy {c['recall']}  precision {c['precision']}")
display(Image(f"{WORK}/outputs/confusion_test.png"))"""),
    new_markdown_cell("""## 6. Get the results

Kaggle: the archive is in the notebook's **Output** tab (right-hand panel, or *Save Version → Save & Run All*
then the *Output* section of the version). Colab: the download starts by itself.
Send `afc_model_outputs.zip` back so it can be added to the app and the model card."""),
    new_code_cell("""import shutil

archive = shutil.copy(f"{WORK}/afc_model_outputs.zip", os.path.join(SAVE_DIR, "afc_model_outputs.zip"))
print("saved:", archive)
if ON_COLAB:
    from google.colab import files
    files.download(archive)"""),
]


def build() -> nbformat.NotebookNode:
    nb = new_notebook(cells=CELLS)
    for i, cell in enumerate(nb.cells):
        cell.id = f"cell-{i:02d}"  # stable ids, so regenerating does not change the file
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.metadata["accelerator"] = "GPU"
    nb.metadata["colab"] = {"provenance": [], "gpuType": "T4"}
    return nb


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(build(), OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
