"""Assemble the image dataset of the classifier.

Sources (see data/sources.yaml):
  - Wikimedia Commons categories of each catalogue dish (open licences, checked
    per file; title-search hits and Openverse are left out: too noisy);
  - Commons categories of other foods (data/other_foods.yaml) -> class "other";
  - CamerFood10 crops (training only, never redistributed).

Steps: download -> near-duplicate removal -> class choice -> split. The result is
a folder of resized JPEGs and a manifest.csv; images never leave the machine.
"""

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from . import OTHER, ROOT

sys.path.insert(0, str(ROOT / "data"))

MAX_SIDE = 512  # stored images are downscaled to this size (the model uses 224)
MANIFEST_FIELDS = ["path", "label", "dish", "source", "group", "split"]


@dataclass
class Item:
    path: str  # image file, relative to the dataset folder once written
    dish: str  # catalogue dish id, or OTHER
    source: str  # wikimedia-commons, camerfood10
    group: str  # items of one group always land in the same split (same photo)
    origin_split: str | None = None  # split imposed by the source dataset, if any
    label: str = ""
    split: str = ""


# ---------------------------------------------------------------- splitting


def split_for(group: str, origin_split: str | None, fractions: dict) -> str:
    """Deterministic split from a hash of the group key.

    A source's own test set stays test; its train set is shared between train
    and val only, so no test image of the source is ever trained on.
    """
    h = int(hashlib.sha1(group.encode("utf-8")).hexdigest()[:8], 16) % 10_000 / 10_000
    train, val = fractions["train"], fractions["val"]
    if origin_split == "test":
        return "test"
    if origin_split == "train":
        return "val" if h < val / (train + val) else "train"
    if h < train:
        return "train"
    if h < train + val:
        return "val"
    return "test"


# ---------------------------------------------------------------- duplicates


def drop_duplicates(items: list[Item], hashes: dict[str, str]) -> tuple[list[Item], dict]:
    """Remove images with the same perceptual hash.

    Same hash and same dish: keep the first. Same hash and different dishes (one
    photo filed under two dishes): drop them all, the label is ambiguous.
    """
    by_hash: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        by_hash[hashes[item.path]].append(item)
    kept, stats = [], Counter()
    for group in by_hash.values():
        dishes = {i.dish for i in group}
        if len(dishes) > 1:
            stats["conflicting_labels"] += len(group)
            continue
        kept.append(group[0])
        stats["duplicates"] += len(group) - 1
    return kept, dict(stats)


# ---------------------------------------------------------------- classes


def choose_classes(items: list[Item], min_images: int) -> list[str]:
    """Dishes with at least `min_images` images become classes; OTHER is always last."""
    counts = Counter(i.dish for i in items if i.dish != OTHER)
    return sorted(d for d, n in counts.items() if n >= min_images) + [OTHER]


def assign_labels(items: list[Item], classes: list[str]) -> None:
    """Dishes that are not classes are learnt as OTHER (the model must refuse them)."""
    for item in items:
        item.label = item.dish if item.dish in classes else OTHER


def cap_per_dish(items: list[Item], max_per_dish: int) -> list[Item]:
    """Keep at most `max_per_dish` images per dish, chosen deterministically."""
    by_dish: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        by_dish[item.dish].append(item)
    kept = []
    for group in by_dish.values():
        group.sort(key=lambda i: hashlib.sha1(i.group.encode()).hexdigest())
        kept += group[:max_per_dish]
    return kept


# ---------------------------------------------------------------- images


def save_resized(src: Path, dst: Path, max_side: int = MAX_SIDE) -> bool:
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((max_side, max_side))
            dst.parent.mkdir(parents=True, exist_ok=True)
            im.save(dst, "JPEG", quality=90)
        return True
    except Exception as exc:  # broken or unsupported file: skip it
        print(f"  skip {src.name}: {exc}", file=sys.stderr)
        return False


def perceptual_hash(path: Path) -> str:
    import imagehash

    with Image.open(path) as im:
        return str(imagehash.phash(im.convert("RGB")))


# ---------------------------------------------------------------- sources


def collect_commons(work: Path, max_per_dish: int, attribution: list[dict]) -> tuple[list[Item], dict]:
    """Download Commons category images of every catalogue dish and of other foods."""
    import download as dl
    from afcdata import commons
    from afcdata.catalog import load_and_validate, load_yaml, require_usable
    from afcdata.http import Client

    sources_doc, dishes_doc = load_and_validate()
    require_usable(sources_doc, commons.SOURCE_ID)
    other = load_yaml(ROOT / "data" / "other_foods.yaml")
    api, files = Client(min_interval=0.2), Client(min_interval=0.2, timeout=60)
    raw = work / "raw" / "commons"
    report = {"missing_categories": []}

    jobs = [(d, {"depth": 1}) for d in dishes_doc["dishes"]]
    jobs.append(({"id": OTHER, "commons_categories": other["categories"]},
                 {"depth": other.get("depth", 1), "max_per_category": other.get("max_per_category")}))
    items = []
    for dish, options in jobs:
        result = commons.collect(api, dish, with_search=False, **options)
        report["missing_categories"] += [f"{dish['id']}: {c}" for c in result.missing_categories]
        records = dl.dedupe(result.records)[:max_per_dish]
        n = 0
        for record in records:
            target = dl.file_path(raw, record)
            try:
                if not dl.fetch(files, record, target):
                    continue
            except Exception as exc:
                print(f"  failed {record.landing_url}: {exc}", file=sys.stderr)
                continue
            items.append(Item(str(target), dish["id"], commons.SOURCE_ID, f"commons:{record.identifier}"))
            attribution.append({
                "file": target.name, "dish": dish["id"], "author": record.author,
                "license": record.license_name, "license_url": record.license_url, "page": record.landing_url,
            })
            n += 1
        print(f"commons {dish['id']}: {n} images", file=sys.stderr)
    return items, report


def collect_camerfood10(work: Path, min_area: float, pad: float) -> list[Item]:
    """Download CamerFood10 (training only) and crop each dish out of its plates."""
    import numpy as np
    import fetch_datasets as fd
    from afcdata import segmentation
    from afcdata.catalog import load_and_validate, require_usable, source_by_id

    from .camerfood import crop_image, crops_for, iter_pairs

    sources_doc, _ = load_and_validate()
    require_usable(sources_doc, "camerfood10")
    source = source_by_id(sources_doc, "camerfood10")
    root = work / "raw" / "camerfood10"
    root.mkdir(parents=True, exist_ok=True)
    fd.fetch_gdrive_folder(source["download"]["url"], root, source["download"]["files"], list_only=False)
    fd.extract_archives(root)

    seg = source["segmentation"]  # paths relative to the unpacked dataset, as in fetch_datasets --stats
    gray_to_class = segmentation.parse_color_map((root / seg["color_map"]).read_text(encoding="utf-8"))
    out_dir = work / "raw" / "camerfood10_crops"
    items = []
    for split, masks_rel in seg["masks"].items():
        masks_dir = root / masks_rel
        images_dir = masks_dir.parent / "images"
        for image_path, mask_path in iter_pairs(images_dir, masks_dir):
            mask = np.array(Image.open(mask_path).convert("L"))
            for label, box, _area in crops_for(mask, gray_to_class, seg["class_map"], min_area, pad):
                dst = out_dir / split / f"{image_path.stem}__{label}.jpg"
                if not dst.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    crop_image(image_path, mask.shape, box).save(dst, "JPEG", quality=92)
                items.append(Item(str(dst), label, "camerfood10", f"camerfood10:{image_path.stem}",
                                  origin_split="test" if split == "test" else "train"))
    print(f"camerfood10: {len(items)} crops", file=sys.stderr)
    return items


# ---------------------------------------------------------------- assembly


def finalize(items: list[Item], out: Path, config: dict, report: dict) -> dict:
    """Deduplicate, choose classes, split, write resized images and the manifest."""
    hashes = {}
    readable = []
    for item in items:
        try:
            hashes[item.path] = perceptual_hash(Path(item.path))
            readable.append(item)
        except Exception as exc:
            print(f"  unreadable {item.path}: {exc}", file=sys.stderr)
    items, dup_stats = drop_duplicates(readable, hashes)
    items = cap_per_dish(items, config["max_per_class"])
    classes = choose_classes(items, config["min_images"])
    assign_labels(items, classes)

    rows = []
    for item in items:
        item.split = split_for(item.group, item.origin_split, config["split"])
        name = hashlib.sha1(item.path.encode()).hexdigest()[:16] + ".jpg"
        rel = Path("images") / item.split / item.label / name
        if save_resized(Path(item.path), out / rel):
            rows.append({**{k: getattr(item, k) for k in ("label", "dish", "source", "group", "split")}, "path": str(rel)})

    out.mkdir(parents=True, exist_ok=True)
    with open(out / "manifest.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    counts = defaultdict(Counter)
    for row in rows:
        counts[row["label"]][row["split"]] += 1
    dish_counts = Counter(r["dish"] for r in rows)
    summary = {
        "classes": classes,
        "images": len(rows),
        "per_class": {label: dict(c) for label, c in sorted(counts.items())},
        "per_source": dict(Counter(r["source"] for r in rows)),
        "dishes_learnt_as_other": sorted(d for d in dish_counts if d not in classes and d != OTHER),
        "dish_counts": dict(sorted(dish_counts.items())),
        "duplicates": dup_stats,
        **report,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def prepare(work: Path, config: dict, with_camerfood: bool = True) -> dict:
    attribution: list[dict] = []
    items, report = collect_commons(work, config["max_per_class"], attribution)
    if with_camerfood:
        cf = config["camerfood10"]
        items += collect_camerfood10(work, cf["min_area"], cf["pad"])
    out = work / "dataset"
    summary = finalize(items, out, config, report)
    with open(out / "ATTRIBUTION.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "dish", "author", "license", "license_url", "page"])
        writer.writeheader()
        writer.writerows(attribution)
    return summary


def read_manifest(dataset: Path) -> list[dict]:
    with open(dataset / "manifest.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
