# Training run 1 (2026-10-12)

Outputs of `training/notebooks/train_classifier.ipynb` run on Kaggle (GPU) by
the project owner, with `USE_CAMERFOOD10 = True` and `USE_TEACHER = False`.
Shared in Backaad/african-food-calories#6. The `model.tflite` file is not here
yet (GitHub issues do not accept that file type). Summary and interpretation:
`docs/model-card.md`.

| File | Content |
|---|---|
| `metrics.json` | Test-set measures, confusion matrix, TFLite parity |
| `training_log.json` | Validation accuracy and per-epoch history |
| `dataset_summary.json` | Images per label and split, sources, dishes learnt as `other` |
| `model_info.json` | Labels, names, input format, threshold, licence |
| `labels.txt` | Label order of the model output |
| `ATTRIBUTION.csv` | Author and licence of every Commons image downloaded |
