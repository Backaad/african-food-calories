# Screenshots

Made by `.github/workflows/screenshots.yml` from the real app screens
(`app/screenshots/screenshots_test.dart`). The journal entries are examples.

`2-result-fr.png` shows the photo [File:Du bon Alloko.JPG](https://commons.wikimedia.org/wiki/File:Du_bon_Alloko.JPG) by Aboukam,
licence CC BY-SA 4.0; that screenshot is therefore under CC BY-SA 4.0 too.
This photo is one of the Wikimedia Commons images used to build the model,
so the screen illustrates the app; it is not a measure of accuracy.
The answer shown is the real model's (`app/assets/model.tflite`, run with
TensorFlow Lite on the same input as the app):

| Label | Probability |
|---|---:|
| alloco | 0.989 |
| bobolo | 0.000 |
| fufu | 0.000 |
| puff_puff | 0.006 |
| ugali | 0.000 |
| other | 0.005 |
