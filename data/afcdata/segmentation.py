"""Per-class and per-dish image counts from segmentation masks (e.g. CamerFood10).

A segmentation image often shows several foods. For classification we count, for
each image, the dish that covers the largest area (its "dominant" dish), after
merging the dataset classes that belong to the same dish (taro + yellow soup =
achu). Classes that are not a dish of the catalogue compete as themselves, so a
plate that is mostly white rice does not count for anything.
"""

from collections import Counter
from pathlib import Path

BACKGROUND = "BG"


def parse_color_map(text: str) -> dict[int, str]:
    """Parse CamerFood10's Color_map.txt: 'Id | Name(FR) | Name(Eng) | Color (GRAY)'.

    Returns {gray value: French class name}, the names used in Classes.txt.
    """
    mapping = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) != 4 or not cells[3].isdigit():
            continue  # header or blank line
        mapping[int(cells[3])] = cells[1]
    return mapping


def mask_areas(path: Path, gray_to_class: dict[int, str]) -> Counter:
    """Pixel area per class in one grayscale mask, background excluded."""
    from PIL import Image

    areas: Counter = Counter()
    with Image.open(path) as im:
        for count, value in im.convert("L").getcolors(maxcolors=256) or []:
            name = gray_to_class.get(value, f"unknown:{value}")
            if name != BACKGROUND:
                areas[name] += count
    return areas


def dominant(areas: Counter, class_map: dict[str, str | None]) -> str | None:
    """Dish id covering the largest area, or None if a non-dish class wins (or empty)."""
    groups: Counter = Counter()
    for name, area in areas.items():
        dish = class_map.get(name)
        groups[f"dish:{dish}" if dish else f"class:{name}"] += area
    if not groups:
        return None
    winner, _ = max(groups.items(), key=lambda kv: (kv[1], kv[0]))
    return winner.removeprefix("dish:") if winner.startswith("dish:") else None


def stats(mask_paths: list[Path], gray_to_class: dict[int, str], class_map: dict[str, str | None]) -> dict:
    present: Counter = Counter()
    dishes: Counter = Counter()
    unknown: Counter = Counter()
    for path in mask_paths:
        areas = mask_areas(path, gray_to_class)
        present.update(areas.keys())
        unknown.update(k for k in areas if k.startswith("unknown:"))
        dish = dominant(areas, class_map)
        if dish:
            dishes[dish] += 1
    return {"images": len(mask_paths), "present": dict(present), "dominant_dish": dict(dishes), "unknown": dict(unknown)}
