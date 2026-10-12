"""Turn CamerFood10 segmentation images into classification crops.

A CamerFood10 image often shows several foods. For each catalogue dish present
on the plate (after merging classes of the same dish, e.g. taro + yellow soup =
achu), we crop the bounding box of its mask, with some margin. Classes that are
not catalogue dishes (white rice, beans, tomato sauce) become "other" crops.
"""

from pathlib import Path

import numpy as np
from PIL import Image

from . import OTHER

BACKGROUND = "BG"


def label_masks(mask: np.ndarray, gray_to_class: dict[int, str], class_map: dict) -> dict[str, np.ndarray]:
    """Boolean mask per training label (dish id, or OTHER for non-dish classes)."""
    out: dict[str, np.ndarray] = {}
    for gray, name in gray_to_class.items():
        if name == BACKGROUND:
            continue
        label = class_map.get(name) or OTHER
        hit = mask == gray
        if hit.any():
            out[label] = out[label] | hit if label in out else hit
    return out


def bbox(hit: np.ndarray, pad: float) -> tuple[int, int, int, int]:
    """Bounding box (x0, y0, x1, y1) of True pixels, enlarged by `pad` of its size."""
    ys, xs = np.nonzero(hit)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    dx, dy = int((x1 - x0) * pad), int((y1 - y0) * pad)
    h, w = hit.shape
    return max(0, x0 - dx), max(0, y0 - dy), min(w, x1 + dx), min(h, y1 + dy)


def crops_for(mask: np.ndarray, gray_to_class: dict[int, str], class_map: dict, min_area: float, pad: float):
    """[(label, box, area_fraction)] for every label covering at least `min_area` of the image."""
    result = []
    for label, hit in sorted(label_masks(mask, gray_to_class, class_map).items()):
        area = float(hit.mean())
        if area >= min_area:
            result.append((label, bbox(hit, pad), area))
    return result


def iter_pairs(images_dir: Path, masks_dir: Path):
    """(image, mask) path pairs with the same file stem."""
    images = {p.stem: p for p in images_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}}
    for mask in sorted(masks_dir.glob("*.png")):
        if mask.stem in images:
            yield images[mask.stem], mask


def crop_image(image_path: Path, mask_shape: tuple[int, int], box) -> Image.Image:
    """Crop `box` (given in mask coordinates) from the image, rescaling if sizes differ."""
    with Image.open(image_path) as im:
        im = im.convert("RGB")
        sx, sy = im.width / mask_shape[1], im.height / mask_shape[0]
        x0, y0, x1, y1 = box
        return im.crop((int(x0 * sx), int(y0 * sy), int(x1 * sx), int(y1 * sy)))
