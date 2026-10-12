#!/usr/bin/env python3
"""Download openly licensed images per dish, with their credits.

    python data/download.py --only ndole,jollof_rice
    python data/download.py --dry-run            # list what would be downloaded

Images go to data/raw/<dish_id>/ (ignored by git). Next to them:
  data/raw/manifest.jsonl   one line per image: source, licence, author, URLs
  data/raw/ATTRIBUTION.csv  the same, as a table to ship with any copy of the images

Only sources marked approved / approved_per_item in data/sources.yaml are used,
and every image is re-checked against the licence allow-list.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from afcdata import commons, openverse  # noqa: E402
from afcdata.catalog import DATA_DIR, load_and_validate, require_usable  # noqa: E402
from afcdata.http import Client, RateLimited  # noqa: E402
from afcdata.licenses import is_allowed  # noqa: E402

MAX_BYTES = 15 * 1024 * 1024
EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
ATTRIBUTION_FIELDS = ["dish_id", "file", "source", "title", "author", "license_name", "license_url", "landing_url"]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="comma-separated dish ids")
    parser.add_argument("--out", type=Path, default=DATA_DIR / "raw")
    parser.add_argument("--commons-depth", type=int, default=1)
    parser.add_argument("--openverse-pages", type=int, default=3, help="result pages per query (0 = skip Openverse)")
    parser.add_argument("--max-per-dish", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true", help="collect metadata only")
    return parser.parse_args(argv)


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_")[:80] or "image"


def dedupe(records):
    seen, unique = set(), []
    for record in records:
        key = record.image_url or (record.source, record.identifier)
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def file_path(out: Path, record) -> Path:
    ext = EXTENSIONS.get(record.mime, Path(record.image_url.split("?")[0]).suffix.lower() or ".jpg")
    if ext == ".jpeg":
        ext = ".jpg"
    return out / record.dish_id / f"{record.source}-{safe_name(record.identifier)}{ext}"


def fetch(client, record, target: Path) -> bool:
    if target.exists():
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    with client.get_stream(record.image_url) as response:
        if not response.headers.get("Content-Type", "").startswith("image/"):
            print(f"  skip (not an image): {record.landing_url}", file=sys.stderr)
            return False
        size = 0
        with open(tmp, "wb") as f:
            for chunk in response.iter_content(64 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    f.close()
                    tmp.unlink()
                    print(f"  skip (too large): {record.landing_url}", file=sys.stderr)
                    return False
                f.write(chunk)
    tmp.rename(target)
    return True


def collect_dish(dish, args, commons_client, openverse_client):
    records = commons.collect(commons_client, dish, depth=args.commons_depth).records
    if args.openverse_pages > 0:
        for query in dish.get("openverse_queries", []):
            records.extend(openverse.search(openverse_client, query, dish["id"], args.openverse_pages))
    return dedupe(records)[: args.max_per_dish]


def main(argv=None):
    args = parse_args(argv)
    sources_doc, dishes_doc = load_and_validate()
    require_usable(sources_doc, commons.SOURCE_ID)
    if args.openverse_pages > 0:
        require_usable(sources_doc, openverse.SOURCE_ID)

    dishes = dishes_doc["dishes"]
    if args.only:
        wanted = set(args.only.split(","))
        dishes = [d for d in dishes if d["id"] in wanted]

    commons_client = Client(min_interval=0.2)
    openverse_client = Client(min_interval=1.5)
    if args.openverse_pages > 0:
        openverse_client.session.headers.update(openverse.auth_headers(openverse_client))
    download_client = Client(min_interval=0.3, timeout=60)

    args.out.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out / "manifest.jsonl"
    attribution_path = args.out / "ATTRIBUTION.csv"
    with open(manifest_path, "w", encoding="utf-8") as manifest, open(
        attribution_path, "w", encoding="utf-8", newline=""
    ) as attribution_file:
        attribution = csv.DictWriter(attribution_file, fieldnames=ATTRIBUTION_FIELDS)
        attribution.writeheader()
        for dish in dishes:
            try:
                records = collect_dish(dish, args, commons_client, openverse_client)
            except RateLimited as exc:
                print(f"{dish['id']}: rate limited ({exc}); try again later or set an Openverse token", file=sys.stderr)
                continue
            kept = 0
            for record in records:
                if not is_allowed(record.license_family):  # defensive: sources already filter
                    continue
                target = file_path(args.out, record)
                if not args.dry_run:
                    try:
                        if not fetch(download_client, record, target):
                            continue
                    except Exception as exc:
                        print(f"  failed {record.image_url}: {exc}", file=sys.stderr)
                        continue
                kept += 1
                row = record.to_dict() | {"file": str(target.relative_to(args.out))}
                manifest.write(json.dumps(row, ensure_ascii=False) + "\n")
                attribution.writerow({k: row[k] for k in ATTRIBUTION_FIELDS})
            print(f"{dish['id']}: {kept} images{' (dry run)' if args.dry_run else ''}", file=sys.stderr)
    print(f"Manifest: {manifest_path}\nCredits:  {attribution_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
