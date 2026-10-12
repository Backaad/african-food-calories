#!/usr/bin/env python3
"""Make the fixtures of test/preprocess_test.dart: synthetic PNG photos and what
TensorFlow's training pipeline (training/afctrain/model.py `load_image`) makes of them.

    python app/tool/make_preprocess_fixtures.py   # needs tensorflow, numpy, pillow

The images are generated (noise and gradients), so they carry no licence issue.
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "app" / "test" / "fixtures"
sys.path.insert(0, str(ROOT / "training"))

SIZE = 224
STEP = 97  # keep every 97th value of the 224 x 224 x 3 output


def synthetic(width: int, height: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:height, 0:width]
    r = 255 * x / max(width - 1, 1)
    g = 255 * y / max(height - 1, 1)
    b = 127 + 127 * np.sin(x / 7.0) * np.cos(y / 5.0)
    img = np.stack([r, g, b], axis=-1) + rng.normal(0, 10, (height, width, 3))
    return np.clip(img, 0, 255).astype(np.uint8)


def main():
    from afctrain.model import load_image

    OUT.mkdir(parents=True, exist_ok=True)
    for name, (w, h, seed) in {"downscale": (400, 300, 1), "upscale": (150, 100, 2)}.items():
        path = OUT / f"{name}.png"
        Image.fromarray(synthetic(w, h, seed)).save(path)
        out = load_image(str(path), SIZE).numpy().reshape(-1)
        ref = {
            "size": SIZE,
            "step": STEP,
            "values": [round(float(v), 3) for v in out[::STEP]],
            "channel_means": [round(float(m), 4) for m in out.reshape(-1, 3).mean(axis=0)],
        }
        (OUT / f"{name}.json").write_text(json.dumps(ref) + "\n", encoding="utf-8")
        print(f"wrote {path.name} ({w}x{h}) and {name}.json")


if __name__ == "__main__":
    main()
