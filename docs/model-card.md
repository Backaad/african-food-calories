# Model card: african-food-calories dish classifier

> **Status: training run 2 (2026-10-12), not yet in the app.** Values below
> come from `training/results/2026-10-12-run2/` (Kaggle GPU, MobileNetV3-Large
> distilled from an EfficientNetV2-S teacher); the model file is
> `training/results/2026-10-12-run2/model.tflite`. They are measured on a test
> set from the same sources as the training images; accuracy on real phone
> photos is not measured yet.

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
least 150 images after duplicate removal). 28 catalogue dishes with fewer
images are learnt as `other` (list in `dataset_summary.json`), so the model
refuses them; the user picks them from the list. Four dishes that look like
fufu or ugali (banku, kenkey, amala, pounded yam; 183 images) are left out
entirely instead (`lookalikes_not_other` in `training/config.yaml`): the model
was never shown them, so it may name fufu or ugali for them.

## Data

| Source | Licence | Use |
|---|---|---|
| Wikimedia Commons categories of each dish | CC0, public domain, CC BY, CC BY-SA, checked per file | train / val / test; credits in `ATTRIBUTION.csv` |
| Wikimedia Commons categories of other foods (`data/other_foods.yaml`) | same | class `other` |
| CamerFood10 (Baban A Erep & Chaari, 2024) | "non-commercial research purpose"; images scraped from search engines and social media | **training only**, risk accepted by the project owner; never redistributed |

2 662 images after removing 17 duplicates, 78 images filed under two dishes
and the 183 look-alike images: 1 656 from Commons, 1 006 crops from CamerFood10.

| Label | Train | Validation | Test |
|---|---:|---:|---:|
| alloco | 194 | 34 | 45 |
| bobolo | 143 | 23 | 21 |
| fufu | 140 | 27 | 37 |
| puff_puff | 118 | 28 | 26 |
| ugali | 133 | 21 | 21 |
| other | 1 181 | 218 | 252 |

## Training

MobileNetV3-Large (ImageNet weights), 224 × 224 RGB input in 0–255, head
training then fine-tuning of the top 40 layers, inverse-frequency class
weights. Then an EfficientNetV2-S teacher is trained and distilled into a copy
of the student (α = 0.3, T = 4); the distilled copy is kept only if better on
validation. Run 2 validation accuracy before refusals: student 0.761, teacher
0.764, distilled 0.798, so the distilled model is the one exported. Settings:
`training/config.yaml`.

## Evaluation

Test set of run 2: 402 images (150 of the five dishes, 252 `other`), never used
for training or for choosing the threshold.

| Measure | Run 2 (current) | Run 1 |
|---|---|---|
| Model | distilled student | student alone |
| Refusal threshold (chosen on validation) | 0.65 | 0.85 |
| Final accuracy, with refusals | 0.841 | 0.852 |
| Top-1 / top-3 accuracy without refusal | 0.769 / 0.970 | 0.759 / 0.970 |
| Images of the five dishes: correct / refused / wrong dish | **0.773** / 0.200 / 0.027 | 0.693 / 0.293 / 0.013 |
| Other foods and other catalogue dishes: correctly refused / wrongly accepted | 0.881 / **0.119** | 0.936 / 0.064 |
| Per source, final accuracy: CamerFood10 / Commons | 0.911 / 0.795 | 0.905 / 0.821 |
| TFLite float16 vs original: top-1 agreement, max probability difference | 0.995, 0.015 | 0.993, 0.021 |

Per dish (test set):

| Dish | Test images | Run 2 recall | Run 2 precision | Run 1 recall |
|---|---:|---:|---:|---:|
| alloco | 45 | 0.89 | 0.85 | 0.82 |
| puff_puff | 26 | 0.85 | 0.71 | 0.85 |
| bobolo | 21 | 0.81 | 0.77 | 0.76 |
| fufu | 37 | 0.68 | 0.83 | 0.59 |
| ugali | 21 | 0.57 | 0.60 | 0.33 |
| other | 252 | 0.88 | 0.88 | 0.94 |

What this means: run 2 recognises more dish photos (77 % instead of 69 %),
mostly because it refuses less; ugali and fufu gain the most. The price is
that it names a dish for 12 % of photos of other foods (30 of 252, against 18
of 281 in run 1), most often puff-puff, ugali or alloco. In the app the user
confirms the dish, so a wrong suggestion is corrected like a refusal; run 2 is
therefore the model proposed for the app.

Three things changed at once between the runs (look-alikes left out, teacher
and distillation, a lower threshold chosen on validation), so these numbers
do not say which change helped. The `other` part of the test set also changed
(the look-alikes are no longer in it), so the two `other` rows are not
measured on exactly the same images. The dish part has the same counts (150)
and the split is deterministic, so it is very likely the same images, but this
was not checked file by file.

Known limits of this evaluation:

- Test images come from the same sources as training images (Commons photos,
  web images in CamerFood10). There are no photos taken with phones in real
  conditions yet; accuracy on such photos is likely lower and must be measured
  separately once some exist.
- Labels were not checked by hand; some Commons images may show the wrong dish.
- Per-dish results rest on 21 to 45 test images per dish: a difference of a
  few images changes them by several points.
- Banku, kenkey, amala and pounded yam are in no part of the data, so how often
  the model calls them fufu or ugali is not measured.

## Licence

Trained with CamerFood10 → **CC BY-NC 4.0** (non-commercial), as recorded in
`model_info.json`. The code is MIT.

## Intended use and limits

For logging meals in the app, as a convenience: the user confirms or corrects
the dish. Not for medical or dietary decisions. Calorie values are estimates
to be validated by a nutritionist.
