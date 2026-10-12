# App

The Flutter app: take or choose a photo, see the most likely dish (or "dish not
recognised"), choose the portion, see the calories and nutrients as a range, and
keep a journal of the day. It works offline, in English and French, in light and
dark theme. Nothing leaves the phone: the model runs on it and the journal is
stored on it.

| Path | What it is |
|---|---|
| `lib/src/recognition/` | Photo preparation (same as training), TensorFlow Lite model, decision rule (threshold, "other") |
| `lib/src/nutrition/dish.dart` | Reads `assets/dishes.json`: values per 100 g, portions, ranges |
| `lib/src/journal/journal.dart` | The journal, stored with shared preferences |
| `lib/src/ui/` | Screens: home and journal, result, dish list, portion, settings |
| `lib/l10n/` | Texts: `app_en.arb`, `app_fr.arb` (the `.dart` files are generated) |
| `assets/` | Copies of `training/results/2026-10-12-run2/model.tflite`, its `model_info.json` and `nutrition/dishes.json` |
| `tool/sync_assets.py` | Refreshes those copies; `--check` fails if they differ (CI) |
| `tool/make_preprocess_fixtures.py` | Makes `test/fixtures/`: synthetic images and TensorFlow's result for them |

## Install on a phone (Android 8.0 or later)

Each change to the app builds an APK on GitHub: *Actions* → *app* → the latest
green run → *Artifacts* → `african-food-calories-apk`. Unzip it, copy
`app-release.apk` to the phone and open it (allow installing from this source).
This test build is signed with a debug key; it is not a store release.

## Develop

```bash
cd app
flutter pub get
flutter test          # unit tests and screen tests (the model is replaced by a fake)
flutter analyze
flutter run           # on a connected phone
```

After a new training run or a change to `nutrition/dishes.json`, update
`MODEL_RUN` in `tool/sync_assets.py` if needed and run
`python3 tool/sync_assets.py`. After editing a `.arb` file, run `flutter gen-l10n`.

## What the tests cover, and what they do not

- Photo preparation gives the same numbers as TensorFlow during training
  (largest difference below 0.01 on a 0–255 scale), including EXIF rotation and
  grey images.
- The decision rule, the reading of the real `dishes.json` and `model_info.json`,
  the journal and its storage, and the screens in French and English, light and
  dark, with or without the model.
- The TensorFlow Lite model itself is not run by `flutter test` (it needs the
  phone's native library). Its answers were compared with the original model
  during export (`metrics.json`, `tflite_parity`); on the phone it must be
  checked by hand.

## Licence

Code: MIT. The model (`assets/model.tflite`) is under CC BY-NC 4.0, so the app
as a whole may only be distributed for non-commercial use. Nutrition values
come from the FAO/INFOODS West Africa table (WAFCT 2019), credited in the app
under *Settings → About*.
