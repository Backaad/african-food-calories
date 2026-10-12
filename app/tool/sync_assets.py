#!/usr/bin/env python3
"""Copy the model and the nutrition data into the app's assets.

    python app/tool/sync_assets.py           # copy
    python app/tool/sync_assets.py --check   # fail if the assets differ from their sources (CI)

The app is built from app/ alone, so it carries its own copies. Git stores
identical files once, so the copies cost no space in the repository.
"""

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_RUN = ROOT / "training" / "results" / "2026-10-12-run2"
ASSETS = ROOT / "app" / "assets"
FILES = {
    "model.tflite": MODEL_RUN / "model.tflite",
    "model_info.json": MODEL_RUN / "model_info.json",
    "dishes.json": ROOT / "nutrition" / "dishes.json",
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="only compare, do not copy")
    args = parser.parse_args(argv)
    stale = []
    for name, src in FILES.items():
        dst = ASSETS / name
        if dst.exists() and filecmp.cmp(src, dst, shallow=False):
            continue
        if args.check:
            stale.append(name)
        else:
            ASSETS.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            print(f"copied {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")
    if stale:
        print(f"out of date: {', '.join(stale)}; run python app/tool/sync_assets.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
