#!/usr/bin/env python3
"""Download a whole dataset source listed in data/sources.yaml.

    python data/fetch_datasets.py camerfood10              # download + unpack
    python data/fetch_datasets.py camerfood10 --list-only  # list remote files
    python data/fetch_datasets.py camerfood10 --describe   # download, then print its structure

Files go to data/raw/datasets/<source_id>/ (ignored by git). Only sources with a
usable status are fetched. Training-only sources (see sources.yaml) must never be
redistributed: do not commit, upload or publish what this script downloads.
"""

import argparse
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from afcdata.catalog import DATA_DIR, is_training_only, load_and_validate, require_usable, source_by_id  # noqa: E402

TEXT_SUFFIXES = {".txt", ".csv", ".json", ".yaml", ".yml", ".md", ".names"}
MASK_HINTS = ("mask", "label", "annot", "seg", "gt")
MAX_TEXT_BYTES = 20_000


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source_id")
    parser.add_argument("--out", type=Path, default=DATA_DIR / "raw" / "datasets")
    parser.add_argument("--list-only", action="store_true", help="list remote files without downloading")
    parser.add_argument("--describe", action="store_true", help="print the folder structure after download")
    return parser.parse_args(argv)


def fetch_gdrive_folder(url: str, target: Path, list_only: bool) -> list[str]:
    import gdown  # imported here: only needed for Google Drive sources

    files = gdown.download_folder(url=url, output=str(target), quiet=False, skip_download=list_only)
    if files is None:
        raise RuntimeError(f"gdown could not read {url}")
    return [getattr(f, "path", str(f)) for f in files]


def extract_archives(root: Path) -> list[Path]:
    """Unpack every .zip under root next to itself (once). Returns the archives unpacked."""
    unpacked = []
    for archive in sorted(root.rglob("*.zip")):
        marker = archive.with_suffix(".unpacked")
        if marker.exists():
            continue
        with zipfile.ZipFile(archive) as zf:
            for member in zf.namelist():
                # Refuse paths that would escape the dataset folder.
                if Path(member).is_absolute() or ".." in Path(member).parts:
                    raise ValueError(f"unsafe path in {archive.name}: {member}")
            zf.extractall(archive.parent / archive.stem)
        marker.touch()
        unpacked.append(archive)
    return unpacked


def describe(root: Path, max_dirs: int = 60, mask_samples: int = 30) -> str:
    """Human-readable summary: files per folder and extension, small text files, mask values."""
    lines = [f"# {root}"]
    per_dir: dict[Path, Counter] = defaultdict(Counter)
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix != ".unpacked"):
        per_dir[path.parent.relative_to(root)][path.suffix.lower() or "(none)"] += 1
    total = sum(sum(c.values()) for c in per_dir.values())
    lines.append(f"{total} files in {len(per_dir)} folders")
    for i, (folder, counts) in enumerate(sorted(per_dir.items())):
        if i == max_dirs:
            lines.append(f"... {len(per_dir) - max_dirs} more folders")
            break
        lines.append(f"  {folder}/: " + ", ".join(f"{n} {ext}" for ext, n in counts.most_common()))

    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size <= MAX_TEXT_BYTES:
            lines.append(f"\n## {path.relative_to(root)}")
            lines.extend(path.read_text(encoding="utf-8", errors="replace").splitlines()[:60])

    masks = [
        p for p in sorted(root.rglob("*.png"))
        if any(h in part.lower() for part in p.relative_to(root).parts[:-1] for h in MASK_HINTS)
    ][:mask_samples]
    if masks:
        from PIL import Image  # imported here: only needed when masks exist

        values: Counter = Counter()
        modes = Counter()
        for mask in masks:
            with Image.open(mask) as im:
                modes[im.mode] += 1
                colors = im.getcolors(maxcolors=4096) or []
                values.update(c if isinstance(c, int) else tuple(c) for _, c in colors)
        lines.append(f"\n## mask sample ({len(masks)} files, modes {dict(modes)})")
        lines.append("pixel values seen (value: number of masks containing it):")
        lines.extend(f"  {v}: {n}" for v, n in sorted(values.items(), key=lambda kv: str(kv[0])))
    return "\n".join(lines)


def main(argv=None):
    args = parse_args(argv)
    sources_doc, _ = load_and_validate()
    require_usable(sources_doc, args.source_id)
    source = source_by_id(sources_doc, args.source_id)
    download = source.get("download") or {}
    if is_training_only(sources_doc, args.source_id):
        print(
            f"{args.source_id} is TRAINING ONLY: never commit, upload or publish these files.",
            file=sys.stderr,
        )

    target = args.out / args.source_id
    target.mkdir(parents=True, exist_ok=True)
    if download.get("type") == "gdrive_folder":
        files = fetch_gdrive_folder(download["url"], target, args.list_only)
    else:
        sys.exit(f"{args.source_id}: unsupported download type {download.get('type')!r}")

    if args.list_only:
        print("\n".join(files))
        return
    extract_archives(target)
    if args.describe:
        print(describe(target))


if __name__ == "__main__":
    main()
