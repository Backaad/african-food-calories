#!/usr/bin/env python3
"""Download the photo shown in the README screenshots and run the real model on it.

    python app/tool/screenshot_photo.py OUT_DIR    # needs tensorflow, numpy, pillow, requests

Writes OUT_DIR/photo.jpg and OUT_DIR/prediction.json (the model's probabilities),
so the screenshot of the result screen shows what the model really answers.
The photo comes from Wikimedia Commons; its licence is checked before use.
"""

import json
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "app" / "assets"
FILE = "File:Du bon Alloko.JPG"
EXPECTED_LICENSE = "CC BY-SA 4.0"
API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "african-food-calories/0.1 (https://github.com/Backaad/african-food-calories)"}


def fetch_photo() -> tuple[Image.Image, dict]:
    params = {"action": "query", "titles": FILE, "prop": "imageinfo", "iiprop": "url|extmetadata",
              "iiurlwidth": 1024, "format": "json"}
    page = next(iter(requests.get(API, params=params, headers=HEADERS, timeout=60).json()["query"]["pages"].values()))
    info = page["imageinfo"][0]
    meta = info["extmetadata"]
    license_name = meta["LicenseShortName"]["value"]
    if license_name != EXPECTED_LICENSE:
        raise SystemExit(f"{FILE}: licence is now {license_name!r}, expected {EXPECTED_LICENSE!r}")
    data = requests.get(info["thumburl"], headers=HEADERS, timeout=120).content
    credit = {"file": FILE, "page": info["descriptionurl"], "license": license_name,
              "author": meta.get("Artist", {}).get("value", "")}
    return Image.open(BytesIO(data)).convert("RGB"), credit


def predict(photo: Image.Image) -> list[float]:
    import tensorflow as tf

    info = json.loads((ASSETS / "model_info.json").read_text(encoding="utf-8"))
    size = info["input"]["size"][0]
    # Same as the app: the picker gives at most 512 px, then the whole image is
    # resized to the model's input like tf.image.resize.
    small = photo.copy()
    small.thumbnail((512, 512))
    x = tf.image.resize(tf.constant(np.asarray(small, dtype=np.float32)), (size, size))
    x = tf.clip_by_value(x, 0, 255)[tf.newaxis]
    interpreter = tf.lite.Interpreter(model_path=str(ASSETS / "model.tflite"))
    interpreter.allocate_tensors()
    interpreter.set_tensor(interpreter.get_input_details()[0]["index"], x.numpy())
    interpreter.invoke()
    return [float(p) for p in interpreter.get_tensor(interpreter.get_output_details()[0]["index"])[0]]


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    photo, credit = fetch_photo()
    photo.save(out / "photo.jpg", quality=90)
    labels = json.loads((ASSETS / "model_info.json").read_text(encoding="utf-8"))["labels"]
    probabilities = predict(photo)
    result = {"labels": labels, "probabilities": probabilities, "photo": credit}
    (out / "prediction.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({l: round(p, 3) for l, p in zip(labels, probabilities)}))


if __name__ == "__main__":
    main()
