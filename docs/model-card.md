# Model card: african-food-calories dish classifier

> **Status: first training run (2026-10-12), not yet in the app.** Values below
> come from `training/results/2026-10-12-run1/` (Kaggle GPU, student only, no
> teacher). They are measured on a test set from the same sources as the
> training images; accuracy on real phone photos is not measured yet.

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

`alloco`, `bobolo`, `fufu`, `puff_puff`, `ugali` and `other` (the dishes with at
least 150 images after duplicate removal). 32 catalogue dishes with fewer
images are learnt as `other` (list in `dataset_summary.json`), so the model
refuses them; the user picks them from the list.

## Data

| Source | Licence | Use |
|---|---|---|
| Wikimedia Commons categories of each dish | CC0, public domain, CC BY, CC BY-SA, checked per file | train / val / test; credits in `ATTRIBUTION.csv` |
| Wikimedia Commons categories of other foods (`data/other_foods.yaml`) | same | class `other` |
| CamerFood10 (Baban A Erep & Chaari, 2024) | "non-commercial research purpose"; images scraped from search engines and social media | **training only**, risk accepted by the project owner; never redistributed |

2 845 images after removing 17 duplicates and 78 images filed under two dishes:
1 839 from Commons, 1 006 crops from CamerFood10.

| Label | Train | Validation | Test |
|---|---:|---:|---:|
| alloco | 194 | 34 | 45 |
| bobolo | 143 | 23 | 21 |
| fufu | 140 | 27 | 37 |
| puff_puff | 118 | 28 | 26 |
| ugali | 133 | 21 | 21 |
| other | 1 303 | 250 | 281 |

## Training

MobileNetV3-Large (ImageNet weights), 224 × 224 RGB input in 0–255, head
training then fine-tuning of the top 40 layers, inverse-frequency class
weights. Optional EfficientNetV2-S teacher with distillation (α = 0.3, T = 4),
kept only if better on validation. Settings: `training/config.yaml`.

## Evaluation

Test set: 431 images (150 of the five dishes, 281 `other`), never used for
training or for choosing the threshold. Run 1, student MobileNetV3-Large
(validation accuracy before refusals 0.778; the teacher was not used).

| Measure | Value |
|---|---|
| Refusal threshold (chosen on validation) | 0.85 |
| Final accuracy, with refusals (dominated by the 281 `other` images) | 0.852 |
| Top-1 / top-3 accuracy without refusal | 0.759 / 0.970 |
| Images of the five dishes: correct / refused / wrong dish | 0.693 / 0.293 / 0.013 |
| Other foods and other catalogue dishes: correctly refused / wrongly accepted | 0.936 / 0.064 |
| Per source, final accuracy: CamerFood10 / Commons | 0.905 (158 images) / 0.821 (273 images) |
| TFLite float16 vs original: top-1 agreement, max probability difference | 0.993, 0.021 |

Per dish (test set):

| Dish | Test images | Accuracy (recall) | Precision |
|---|---:|---:|---:|
| puff_puff | 26 | 0.85 | 0.85 |
| alloco | 45 | 0.82 | 0.90 |
| bobolo | 21 | 0.76 | 0.80 |
| fufu | 37 | 0.59 | 0.96 |
| ugali | 21 | 0.33 | 0.50 |
| other | 281 | 0.94 | 0.86 |

What this means: when the model names one of the five dishes it is rarely
wrong (2 of 150 dish images given the wrong dish), but it refuses often (29 %
of dish images), above all ugali and fufu. Most of their errors are refusals
(`other`); a likely cause is that look-alike staples (banku, kenkey, amala,
pounded yam) are learnt as `other`. 3 of 431 test images change their top
answer between the Keras and the TFLite model.

Known limits of this evaluation:

- Test images come from the same sources as training images (Commons photos,
  web images in CamerFood10). There are no photos taken with phones in real
  conditions yet; accuracy on such photos is likely lower and must be measured
  separately once some exist.
- Labels were not checked by hand; some Commons images may show the wrong dish.
- Per-dish results rest on 21 to 45 test images per dish: a difference of a
  few images changes them by several points.

## Licence

Trained with CamerFood10 → **CC BY-NC 4.0** (non-commercial), as recorded in
`model_info.json`. The code is MIT.

## Intended use and limits

For logging meals in the app, as a convenience: the user confirms or corrects
the dish. Not for medical or dietary decisions. Calorie values are estimates
to be validated by a nutritionist.
