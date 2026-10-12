# Model card: african-food-calories dish classifier

> **Status: not trained yet.** The training code is ready
> (`training/notebooks/train_classifier.ipynb`); no model has been trained and
> no metric below has been measured. Every "to be measured" value will be
> filled from `metrics.json` after the first training run. Nothing here is a
> verified result until then.

## What it does

Takes a photo of a plate and returns, for each label, a probability: one label
per recognised dish and `other` ("dish not recognised"). The app shows the top
dish with two alternatives, or "dish not recognised" when the top probability
is below the threshold or the top label is `other`. The user can always pick
the dish from the full list. Calories come from `nutrition/dishes.json`, not
from the model.

It does not estimate portion size and does not handle several dishes on one
plate (it answers for the dominant one).

## Labels

Expected from the data inventory (`docs/data-inventory.md`, dishes with at least
150 images): alloco, bobolo, fufu, puff-puff, ugali, and `other`. The actual list
is decided by `training/afctrain/prepare.py` from the images really downloaded:
**to be confirmed** by the training run (`labels.txt`).

Catalogue dishes with fewer images are learnt as `other`, so the model refuses
them instead of guessing a wrong dish.

## Data

| Source | Licence | Use |
|---|---|---|
| Wikimedia Commons categories of each dish | CC0, public domain, CC BY, CC BY-SA, checked per file | train / val / test; credits in `ATTRIBUTION.csv` |
| Wikimedia Commons categories of other foods (`data/other_foods.yaml`) | same | class `other` |
| CamerFood10 (Baban A Erep & Chaari, 2024) | "non-commercial research purpose"; images scraped from search engines and social media | **training only**, risk accepted by the project owner; never redistributed |

Image counts per label and split: **to be measured** (`dataset_summary.json`).

## Training

MobileNetV3-Large (ImageNet weights), 224 × 224 RGB input in 0–255, head
training then fine-tuning of the top 40 layers, inverse-frequency class
weights. Optional EfficientNetV2-S teacher with distillation (α = 0.3, T = 4),
kept only if better on validation. Settings: `training/config.yaml`.

## Evaluation

Test set (15 % of the images, never used for training or for choosing the
threshold). All values **to be measured**:

| Measure | Value |
|---|---|
| Refusal threshold (chosen on validation) | to be measured |
| Final accuracy (with refusals) | to be measured |
| Top-1 / top-3 accuracy without refusal | to be measured |
| Known dishes: correct / refused / wrong dish | to be measured |
| Other foods: correctly refused / wrongly accepted | to be measured |
| Per-dish accuracy and precision | to be measured |
| Per source (Commons vs CamerFood10) | to be measured |
| TFLite vs original: top-1 agreement, max probability difference | to be measured |

Known limits of this evaluation:

- Test images come from the same sources as training images (Commons photos,
  web images in CamerFood10). There are no photos taken with phones in real
  conditions yet; accuracy on such photos is likely lower and must be measured
  separately once some exist.
- Labels were not checked by hand; some Commons images may show the wrong dish.
- Per-dish results on small test sets (a few dozen images) are uncertain.

## Licence

Trained with CamerFood10 → **CC BY-NC 4.0** (non-commercial). The code is MIT.

## Intended use and limits

For logging meals in the app, as a convenience: the user confirms or corrects
the dish. Not for medical or dietary decisions. Calorie values are estimates
to be validated by a nutritionist.
