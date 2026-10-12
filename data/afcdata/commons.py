"""Wikimedia Commons: list the files of a dish's categories with their licences."""

import html
import re
from collections import Counter
from dataclasses import dataclass, field

from . import ImageRecord
from .licenses import is_allowed, normalize

API = "https://commons.wikimedia.org/w/api.php"
SOURCE_ID = "wikimedia-commons"
PHOTO_MIMES = frozenset({"image/jpeg", "image/png", "image/webp"})
THUMB_WIDTH = 640
SEARCH_MAX_BATCHES = 10  # 500 files per search term at most


@dataclass
class CommonsResult:
    records: list[ImageRecord] = field(default_factory=list)  # from categories
    search_records: list[ImageRecord] = field(default_factory=list)  # from title search only
    rejected: Counter = field(default_factory=Counter)  # licence family or "not-a-photo" -> count
    missing_categories: list[str] = field(default_factory=list)
    walked_categories: list[str] = field(default_factory=list)


def _base_params(**extra) -> dict:
    return {"action": "query", "format": "json", "formatversion": 2, "maxlag": 5, **extra}


def _query_all(client, params: dict, max_batches: int | None = None):
    """Yield every response of a query, following MediaWiki continuation."""
    cont: dict = {}
    batches = 0
    while True:
        data = client.get_json(API, {**params, **cont})
        if "error" in data:
            raise RuntimeError(f"Commons API error: {data['error']}")
        yield data
        batches += 1
        if "continue" not in data or (max_batches and batches >= max_batches):
            return
        cont = data["continue"]


def _cat(title: str) -> str:
    return title if title.startswith("Category:") else f"Category:{title}"


def existing_categories(client, names: list[str]) -> tuple[list[str], list[str]]:
    """Split category names into (existing, missing), using canonical titles."""
    if not names:
        return [], []
    titles = [_cat(n) for n in names]
    data = client.get_json(API, _base_params(titles="|".join(titles), prop="categoryinfo"))
    normalized = {n["from"]: n["to"] for n in data.get("query", {}).get("normalized", [])}
    pages = {p["title"]: p for p in data.get("query", {}).get("pages", [])}
    existing, missing = [], []
    for title in titles:
        canonical = normalized.get(title, title)
        page = pages.get(canonical)
        # A category page can be missing while still holding files, so check categoryinfo.
        has_members = page is not None and page.get("categoryinfo", {}).get("size", 0) > 0
        (existing if has_members else missing).append(canonical)
    return existing, missing


def walk_categories(client, roots: list[str], depth: int, exclude: list[str] = ()) -> list[str]:
    """Return roots plus their sub-categories down to `depth` levels."""
    skip = {_cat(e) for e in exclude}
    seen: list[str] = []
    frontier = [r for r in roots if r not in skip]
    for level in range(depth + 1):
        next_frontier = []
        for cat in frontier:
            if cat in seen or cat in skip:
                continue
            seen.append(cat)
            if level == depth:
                continue
            params = _base_params(list="categorymembers", cmtitle=cat, cmtype="subcat", cmlimit=500)
            for data in _query_all(client, params):
                for member in data.get("query", {}).get("categorymembers", []):
                    next_frontier.append(member["title"])
        frontier = next_frontier
    return seen


def _meta(info: dict, key: str) -> str:
    value = info.get("extmetadata", {}).get(key, {}).get("value", "")
    return value if isinstance(value, str) else str(value)


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()


def parse_page(page: dict, dish_id: str) -> tuple[ImageRecord | None, str]:
    """Turn one API page into a record. Returns (record, family); record is None if rejected."""
    infos = page.get("imageinfo") or []
    if not infos:
        return None, "no-imageinfo"
    info = infos[0]
    if info.get("mime") not in PHOTO_MIMES:
        return None, "not-a-photo"
    family = normalize(_meta(info, "License") or _meta(info, "LicenseShortName"))
    if not is_allowed(family):
        return None, family
    record = ImageRecord(
        source=SOURCE_ID,
        dish_id=dish_id,
        identifier=str(page["pageid"]),
        title=page["title"],
        landing_url=info.get("descriptionurl", ""),
        image_url=info.get("thumburl") or info.get("url", ""),
        license_family=family,
        license_name=_meta(info, "LicenseShortName"),
        license_url=_meta(info, "LicenseUrl"),
        author=_strip_html(_meta(info, "Artist")) or "unknown (see file page)",
        mime=info.get("mime", ""),
    )
    return record, family


_IMAGEINFO = {
    "prop": "imageinfo",
    "iiprop": "url|mime|extmetadata",
    "iiurlwidth": THUMB_WIDTH,
    "iiextmetadatafilter": "License|LicenseShortName|LicenseUrl|Artist",
}


def _files(client, params: dict, max_batches: int | None = None):
    """Yield raw API pages (files with imageinfo) of a generator query."""
    pages: dict[int, dict] = {}
    for data in _query_all(client, params, max_batches):
        for page in data.get("query", {}).get("pages", []):
            merged = pages.setdefault(page["pageid"], page)
            if page.get("imageinfo") and not merged.get("imageinfo"):
                merged["imageinfo"] = page["imageinfo"]
    yield from pages.values()


def list_files(client, category: str):
    """Yield the files of one category."""
    return _files(client, _base_params(generator="categorymembers", gcmtitle=category, gcmtype="file", gcmlimit=50, **_IMAGEINFO))


def search_files(client, term: str):
    """Yield files whose title contains `term` (File namespace only)."""
    params = _base_params(generator="search", gsrsearch=f'intitle:"{term}"', gsrnamespace=6, gsrlimit=50, **_IMAGEINFO)
    return _files(client, params, max_batches=SEARCH_MAX_BATCHES)


def collect(client, dish: dict, depth: int = 1) -> CommonsResult:
    result = CommonsResult()
    existing, missing = existing_categories(client, dish.get("commons_categories", []))
    result.missing_categories = missing
    result.walked_categories = walk_categories(client, existing, depth, dish.get("commons_exclude", []))
    seen_ids: set[int] = set()
    for category in result.walked_categories:
        for page in list_files(client, category):
            if page["pageid"] in seen_ids:
                continue
            seen_ids.add(page["pageid"])
            _keep(result, result.records, page, dish["id"])
    for term in dish.get("commons_search", []):
        for page in search_files(client, term):
            if page["pageid"] in seen_ids:
                continue
            seen_ids.add(page["pageid"])
            _keep(result, result.search_records, page, dish["id"])
    return result


def _keep(result: CommonsResult, bucket: list, page: dict, dish_id: str) -> None:
    record, family = parse_page(page, dish_id)
    if record:
        bucket.append(record)
    else:
        result.rejected[family] += 1
