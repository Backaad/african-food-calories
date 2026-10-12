#!/usr/bin/env python3
"""Count openly licensed images per dish and write the inventory table.

Only metadata is fetched; no image is downloaded.

    python data/inventory.py                      # all dishes, Commons + Openverse
    python data/inventory.py --only ndole,eru     # a few dishes
    python data/inventory.py --no-openverse       # Commons only (no rate limit worries)

Writes data/inventory/counts.json and data/inventory/inventory.md.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from afcdata import commons, openverse  # noqa: E402
from afcdata.catalog import DATA_DIR, USABLE, load_and_validate, require_usable  # noqa: E402
from afcdata.http import Client, RateLimited  # noqa: E402
from afcdata.inventory import render_markdown, summarize_dish  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="comma-separated dish ids")
    parser.add_argument("--out", type=Path, default=DATA_DIR / "inventory")
    parser.add_argument("--commons-depth", type=int, default=1, help="sub-category levels to follow (default 1)")
    parser.add_argument("--no-commons", action="store_true")
    parser.add_argument("--no-openverse", action="store_true")
    parser.add_argument("--manifest", type=Path, help="also write every allowed Commons image as JSON lines")
    return parser.parse_args(argv)


def count_commons(client, dish, depth, manifest):
    try:
        result = commons.collect(client, dish, depth=depth)
    except Exception as exc:  # keep going: one broken dish must not hide the others
        print(f"  commons error: {exc}", file=sys.stderr)
        return {"error": str(exc)}
    if manifest:
        for record in result.records + result.search_records:
            manifest.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
    return {
        "allowed": len(result.records),
        "search_allowed": len(result.search_records),
        "rejected": dict(result.rejected),
        "licenses": _family_counts(result.records),
        "identifiers": sorted(r.identifier for r in result.records + result.search_records),
        "missing_categories": result.missing_categories,
        "walked_categories": result.walked_categories,
    }


def _family_counts(records):
    counts = {}
    for record in records:
        counts[record.license_family] = counts.get(record.license_family, 0) + 1
    return counts


def count_openverse(client, dish):
    per_query = {}
    for query in dish.get("openverse_queries", []):
        per_query[query] = openverse.count(client, query)
    # Queries overlap, so the largest single result is the safe (lower) estimate of their union.
    return {"hits": max(per_query.values(), default=0), "per_query": per_query}


def main(argv=None):
    args = parse_args(argv)
    sources_doc, dishes_doc = load_and_validate()
    thresholds = dishes_doc["thresholds"]
    dishes = dishes_doc["dishes"]
    if args.only:
        wanted = set(args.only.split(","))
        dishes = [d for d in dishes if d["id"] in wanted]
        unknown = wanted - {d["id"] for d in dishes}
        if unknown:
            sys.exit(f"Unknown dish ids: {', '.join(sorted(unknown))}")

    use_commons = not args.no_commons
    use_openverse = not args.no_openverse
    if use_commons:
        require_usable(sources_doc, commons.SOURCE_ID)
    if use_openverse:
        require_usable(sources_doc, openverse.SOURCE_ID)

    commons_client = Client(min_interval=0.2)
    openverse_client = Client(min_interval=1.5)
    if use_openverse:
        openverse_client.session.headers.update(openverse.auth_headers(openverse_client))
    openverse_stopped = None

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = open(args.manifest, "w", encoding="utf-8") if args.manifest else None
    rows = []
    try:
        for dish in dishes:
            print(f"{dish['id']}", file=sys.stderr)
            commons_counts = count_commons(commons_client, dish, args.commons_depth, manifest) if use_commons else None
            openverse_counts = None
            if use_openverse:
                if openverse_stopped:
                    openverse_counts = {"error": openverse_stopped}
                else:
                    try:
                        openverse_counts = count_openverse(openverse_client, dish)
                    except RateLimited as exc:
                        print(f"  openverse rate limited, skipping the rest: {exc}", file=sys.stderr)
                        openverse_stopped = "rate-limited"
                        openverse_counts = {"error": openverse_stopped}
                    except Exception as exc:
                        print(f"  openverse error: {exc}", file=sys.stderr)
                        openverse_counts = {"error": "error"}
            # Usable datasets whose per-dish counts were measured (see `dish_counts` in sources.yaml).
            datasets = {
                s["id"]: s["dish_counts"][dish["id"]]
                for s in sources_doc["sources"]
                if s["status"] in USABLE and dish["id"] in (s.get("dish_counts") or {})
            }
            rows.append(summarize_dish(dish, commons_counts, openverse_counts, datasets, thresholds))
    finally:
        if manifest:
            manifest.close()

    run_info = {"date": date.today().isoformat(), "commons_depth": args.commons_depth}
    (args.out / "counts.json").write_text(
        json.dumps({"run": run_info, "thresholds": thresholds, "dishes": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(rows, sources_doc, thresholds, run_info)
    (args.out / "inventory.md").write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
