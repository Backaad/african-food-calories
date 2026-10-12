"""Openverse: count and list openly licensed images matching a search query."""

import os

from . import ImageRecord
from .licenses import is_allowed, normalize

API = "https://api.openverse.org/v1"
SOURCE_ID = "openverse"
# Openverse licence codes matching licenses.ALLOWED.
LICENSE_FILTER = "cc0,pdm,by,by-sa"
# Commons images are collected by the Commons source; skip them here to avoid duplicates.
EXCLUDED_SOURCES = "wikimedia"
ANONYMOUS_PAGE_SIZE = 20
LICENSE_NAMES = {"cc0": "CC0", "pd": "Public Domain Mark", "cc-by": "CC BY", "cc-by-sa": "CC BY-SA"}


def auth_headers(client) -> dict:
    """Return an Authorization header if OPENVERSE_CLIENT_ID/SECRET are set, else {}."""
    client_id = os.environ.get("OPENVERSE_CLIENT_ID")
    client_secret = os.environ.get("OPENVERSE_CLIENT_SECRET")
    if not (client_id and client_secret):
        return {}
    token = client.post_form(
        f"{API}/auth_tokens/token/",
        {"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
    )["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _params(query: str, page: int, page_size: int) -> dict:
    return {
        "q": query,
        "license": LICENSE_FILTER,
        "excluded_source": EXCLUDED_SOURCES,
        "page": page,
        "page_size": page_size,
        "mature": "false",
    }


def count(client, query: str) -> int:
    """Number of matching images reported by the API (one request)."""
    return int(client.get_json(f"{API}/images/", _params(query, 1, 1))["result_count"])


def parse_result(item: dict, dish_id: str) -> tuple[ImageRecord | None, str]:
    family = normalize(item.get("license"))
    if not is_allowed(family):
        return None, family
    name = f"{LICENSE_NAMES[family]} {item.get('license_version') or ''}".strip()
    record = ImageRecord(
        source=SOURCE_ID,
        dish_id=dish_id,
        identifier=item["id"],
        title=item.get("title") or "",
        landing_url=item.get("foreign_landing_url") or "",
        image_url=item.get("url") or "",
        license_family=family,
        license_name=name,
        license_url=item.get("license_url") or "",
        author=item.get("creator") or "unknown (see landing page)",
        mime=f"image/{item['filetype']}" if item.get("filetype") else "",
    )
    return record, family


def search(client, query: str, dish_id: str, max_pages: int, page_size: int = ANONYMOUS_PAGE_SIZE):
    """Yield allowed records for a query, page by page."""
    for page in range(1, max_pages + 1):
        data = client.get_json(f"{API}/images/", _params(query, page, page_size))
        for item in data.get("results", []):
            record, _ = parse_result(item, dish_id)
            if record:
                yield record
        if page >= int(data.get("page_count", 0)):
            return
