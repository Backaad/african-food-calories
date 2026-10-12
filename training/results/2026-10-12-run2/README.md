# Training run 2 (2026-10-12)

Outputs of `training/notebooks/train_classifier.ipynb` run on Kaggle (GPU) by
the project owner, with `USE_CAMERFOOD10 = True` and `USE_TEACHER = True`, after
the change that leaves look-alike staples (banku, kenkey, amala, pounded yam)
out instead of learning them as `other`. Shared in
Backaad/african-food-calories#9. The distilled model did better on validation
than the student alone, so it is the one exported. Summary, comparison with
run 1 and interpretation: `docs/model-card.md`.

| File | Content |
|---|---|
| `model.tflite` | The model for the phone (TensorFlow Lite, float16 weights, 6.0 MB). Licence CC BY-NC 4.0 |
| `metrics.json` | Test-set measures, confusion matrix, TFLite parity |
| `confusion_test.png` | Confusion matrix of the test set, as a picture |
| `training_log.json` | Validation accuracy of student, teacher and distilled model; per-epoch history |
| `dataset_summary.json` | Images per label and split, sources, dishes learnt as `other`, dishes left out |
| `model_info.json` | Labels, names, input format, threshold, licence |
| `labels.txt` | Label order of the model output |
| `ATTRIBUTION.csv` | Author and licence of every Commons image downloaded |
