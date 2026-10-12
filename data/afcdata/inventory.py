"""Count candidate images per dish and decide which dishes the model can learn."""

from datetime import date

# Anonymous Openverse searches never report more than this many results (observed
# in the first CI run: many unrelated queries returned exactly 240).
OPENVERSE_CEILING = 240

STATUS_LABELS = {
    "model": "model (needs review)",
    "few_shot": "few-shot test",
    "manual": "manual entry",
    "unknown": "not counted",
}


def classify(count: int, thresholds: dict) -> str:
    if count >= thresholds["model"]:
        return "model"
    if count >= thresholds["few_shot"]:
        return "few_shot"
    return "manual"


def summarize_dish(dish: dict, commons: dict | None, openverse: dict | None, datasets: dict, thresholds: dict) -> dict:
    """Combine the per-source results of one dish.

    `reliable` counts images whose dish label comes from a curated place (Commons
    categories, approved datasets). Openverse search hits are only an upper bound,
    because keyword matches are often not the dish.
    """
    commons_ok = commons is not None and not commons.get("error")
    openverse_ok = openverse is not None and not openverse.get("error")
    reliable = (commons["allowed"] if commons_ok else 0) + sum(datasets.values())
    commons_search = commons.get("search_allowed", 0) if commons_ok else 0
    upper = reliable + commons_search + (openverse["hits"] if openverse_ok else 0)
    return {
        "id": dish["id"],
        "name": dish["names"]["en"],
        "countries": dish["countries"],
        "commons": commons,
        "openverse": openverse,
        "datasets": datasets,
        "reliable": reliable,
        "upper_bound": upper,
        # A source that failed or was skipped must not look like "zero images".
        "status": classify(reliable, thresholds) if commons_ok else "unknown",
        "status_upper_bound": classify(upper, thresholds) if commons_ok and openverse_ok else "unknown",
    }


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|")


def _commons_cell(commons: dict | None) -> str:
    if commons is None:
        return "not run"
    if commons.get("error"):
        return "error"
    return str(commons["allowed"])


def _rejected_cell(commons: dict | None) -> str:
    if not commons or commons.get("error"):
        return ""
    return str(sum(commons.get("rejected", {}).values()))


def _search_cell(commons: dict | None) -> str:
    if not commons or commons.get("error"):
        return ""
    return str(commons.get("search_allowed", 0))


def _openverse_cell(openverse: dict | None) -> str:
    if openverse is None:
        return "not run"
    if openverse.get("error"):
        return openverse["error"]
    hits = openverse["hits"]
    return f"≥{hits}" if hits >= OPENVERSE_CEILING else str(hits)


def render_markdown(rows: list[dict], sources_doc: dict, thresholds: dict, run_info: dict) -> str:
    order = {"model": 0, "few_shot": 1, "manual": 2, "unknown": 3}
    rows = sorted(rows, key=lambda r: (order[r["status"]], -r["reliable"], -r["upper_bound"], r["id"]))
    lines = [
        "# Data inventory",
        "",
        f"Generated on {run_info.get('date', date.today().isoformat())} by `data/inventory.py`"
        f" (Commons category depth {run_info.get('commons_depth', '?')}).",
        "Do not edit by hand: re-run the script.",
        "",
        "## How to read this table",
        "",
        "- **Commons**: files in the dish's Wikimedia Commons categories whose own licence is"
        " CC0, public domain, CC BY or CC BY-SA, and that are JPEG/PNG/WebP.",
        "- **Commons search**: extra open-licence files whose *title* contains the dish name, for dishes"
        " without a good category. Not curated: upper bound only.",
        "- **Rejected**: files in the same categories or searches that were dropped (NC/ND/unknown licence,"
        " or not a photo format).",
        "- **Openverse**: open-licence search hits outside Wikimedia. Keyword matches, *not reviewed*:"
        f" many are not the dish. Upper bound only. Anonymous searches stop at {OPENVERSE_CEILING}, shown as"
        f" ≥{OPENVERSE_CEILING}.",
        f"- **Status** uses the reliable count (Commons + approved datasets):"
        f" ≥ {thresholds['model']} → model, ≥ {thresholds['few_shot']} → few-shot test, otherwise manual entry."
        " *If the upper bound holds* adds Commons search and Openverse hits.",
        "- No count here has been reviewed by a person yet. \"Usable\" photos (right dish, real photo,"
        " no duplicates) will be fewer.",
        "",
        "| Dish | Countries | Commons | Commons search | Rejected | Openverse | Status | If the upper bound holds |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['name']} (`{r['id']}`) | {', '.join(r['countries'])} | {_commons_cell(r['commons'])}"
            f" | {_search_cell(r['commons'])} | {_rejected_cell(r['commons'])} | {_openverse_cell(r['openverse'])}"
            f" | {STATUS_LABELS[r['status']]} | {STATUS_LABELS[r['status_upper_bound']]} |"
        )

    counts = {s: sum(1 for r in rows if r["status"] == s) for s in order}
    lines += [
        "",
        f"Totals: {counts['model']} model, {counts['few_shot']} few-shot, {counts['manual']} manual entry,"
        f" {counts['unknown']} not counted ({len(rows)} dishes).",
        "",
        "## Missing Commons categories",
        "",
        "Category names in `data/dishes.yaml` that do not exist (or are empty) on Commons:",
        "",
    ]
    missing = [(r["id"], c) for r in rows for c in ((r["commons"] or {}).get("missing_categories") or [])]
    lines += [f"- `{dish_id}`: {cat}" for dish_id, cat in missing] or ["- none"]

    lines += [
        "",
        "## Commons categories walked",
        "",
        "Check these for categories that drift away from the dish, and list them under"
        " `commons_exclude` in `data/dishes.yaml`.",
        "",
    ]
    for r in rows:
        walked = (r["commons"] or {}).get("walked_categories") or []
        if walked:
            lines.append(f"- `{r['id']}`: " + ", ".join(c.removeprefix("Category:") for c in walked))

    lines += [
        "",
        "## Datasets not used",
        "",
        "From `data/sources.yaml`. Image counts are the ones reported by the authors; none are used.",
        "",
        "| Source | Declared licence | Status | Reason | Reported images |",
        "|---|---|---|---|---|",
    ]
    for source in sources_doc["sources"]:
        if source["kind"] != "dataset" or source["status"] in {"approved", "approved_per_item"}:
            continue
        reported = source.get("reported_counts")
        if reported:
            reported_text = ", ".join(f"{k} {v}" for k, v in reported.items())
        else:
            reported_text = str(source.get("reported_counts_total", "?"))
        reason = _cell(" ".join(source["status_reason"].split()))
        lines.append(
            f"| [{source['name']}]({source['url']}) | {_cell(source.get('declared_license', '?'))}"
            f" | {source['status']} | {reason} | {reported_text} |"
        )
    return "\n".join(lines) + "\n"
