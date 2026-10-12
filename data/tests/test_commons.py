from conftest import FakeClient

from afcdata import commons


def file_page(pageid, license_code, short_name, mime="image/jpeg", artist='<a href="//x">Jane Doe</a>'):
    return {
        "pageid": pageid,
        "ns": 6,
        "title": f"File:Dish {pageid}.jpg",
        "imageinfo": [
            {
                "url": f"https://upload.wikimedia.org/full/{pageid}.jpg",
                "thumburl": f"https://upload.wikimedia.org/thumb/{pageid}.jpg",
                "descriptionurl": f"https://commons.wikimedia.org/wiki/File:Dish_{pageid}.jpg",
                "mime": mime,
                "extmetadata": {
                    "License": {"value": license_code, "source": "commons-desc-page"},
                    "LicenseShortName": {"value": short_name, "source": "commons-desc-page"},
                    "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0", "source": "x"},
                    "Artist": {"value": artist, "source": "commons-desc-page"},
                },
            }
        ],
    }


def test_parse_page_keeps_open_licence_and_strips_html():
    record, family = commons.parse_page(file_page(1, "cc-by-sa-4.0", "CC BY-SA 4.0"), "ndole")
    assert family == "cc-by-sa"
    assert record.author == "Jane Doe"
    assert record.image_url.endswith("/thumb/1.jpg")
    assert record.license_name == "CC BY-SA 4.0"
    assert record.identifier == "1"


def test_parse_page_rejects_non_commercial_and_non_photos():
    assert commons.parse_page(file_page(2, "cc-by-nc-2.0", "CC BY-NC 2.0"), "ndole") == (None, "cc-by-nc")
    assert commons.parse_page(file_page(3, "cc0", "CC0", mime="image/svg+xml"), "ndole") == (None, "not-a-photo")
    assert commons.parse_page({"pageid": 4, "title": "File:x"}, "ndole") == (None, "no-imageinfo")


def test_parse_page_falls_back_to_short_name():
    page = file_page(5, "", "Public domain")
    record, family = commons.parse_page(page, "ndole")
    assert family == "pd" and record is not None


def test_existing_categories_handles_normalisation_and_empty_pages():
    client = FakeClient([
        (lambda u, p: p.get("prop") == "categoryinfo", {
            "query": {
                "normalized": [{"from": "Category:ndolé", "to": "Category:Ndolé"}],
                "pages": [
                    {"title": "Category:Ndolé", "categoryinfo": {"size": 12, "files": 12, "subcats": 0}},
                    {"title": "Category:Ndole", "missing": True},
                    {"title": "Category:Empty", "categoryinfo": {"size": 0}},
                ],
            }
        }),
    ])
    existing, missing = commons.existing_categories(client, ["ndolé", "Ndole", "Empty"])
    assert existing == ["Category:Ndolé"]
    assert missing == ["Category:Ndole", "Category:Empty"]


def test_walk_categories_respects_depth_cycles_and_exclusions():
    tree = {
        "Category:A": ["Category:B", "Category:Skip"],
        "Category:B": ["Category:C", "Category:A"],
        "Category:C": ["Category:D"],
    }
    client = FakeClient([
        (lambda u, p: p.get("list") == "categorymembers",
         lambda p: {"query": {"categorymembers": [{"title": t} for t in tree.get(p["cmtitle"], [])]}}),
    ])
    assert commons.walk_categories(client, ["Category:A"], depth=0) == ["Category:A"]
    assert commons.walk_categories(client, ["Category:A"], depth=1, exclude=["Skip"]) == ["Category:A", "Category:B"]
    assert commons.walk_categories(client, ["Category:A"], depth=5, exclude=["Skip"]) == [
        "Category:A", "Category:B", "Category:C", "Category:D"]


def test_collect_follows_continuation_and_dedupes_across_categories():
    def files(params):
        cat = params["gcmtitle"]
        if cat == "Category:Ndolé" and "gcmcontinue" not in params:
            return {"continue": {"gcmcontinue": "page2", "continue": "gcmcontinue||"},
                    "query": {"pages": [file_page(1, "cc-by-4.0", "CC BY 4.0"), file_page(2, "cc-by-nc-4.0", "CC BY-NC 4.0")]}}
        if cat == "Category:Ndolé":
            return {"query": {"pages": [file_page(3, "cc0", "CC0")]}}
        return {"query": {"pages": [file_page(1, "cc-by-4.0", "CC BY 4.0"), file_page(4, "pd", "Public domain")]}}

    client = FakeClient([
        (lambda u, p: p.get("prop") == "categoryinfo",
         {"query": {"pages": [{"title": "Category:Ndolé", "categoryinfo": {"size": 3}},
                              {"title": "Category:Nope", "missing": True}]}}),
        (lambda u, p: p.get("list") == "categorymembers",
         lambda p: {"query": {"categorymembers": [{"title": "Category:Ndolé in Douala"}] if p["cmtitle"] == "Category:Ndolé" else []}}),
        (lambda u, p: p.get("generator") == "categorymembers", files),
    ])
    result = commons.collect(client, {"id": "ndole", "commons_categories": ["Ndolé", "Nope"]}, depth=1)
    assert sorted(r.identifier for r in result.records) == ["1", "3", "4"]
    assert dict(result.rejected) == {"cc-by-nc": 1}
    assert result.missing_categories == ["Category:Nope"]
    assert result.walked_categories == ["Category:Ndolé", "Category:Ndolé in Douala"]
    assert all(params["maxlag"] == 5 for _, params in client.calls)


def test_title_search_is_separate_capped_and_deduped(monkeypatch):
    monkeypatch.setattr(commons, "SEARCH_MAX_BATCHES", 2)

    def search(params):
        offset = int(params.get("gsroffset", 0))
        assert params["gsrsearch"] == 'intitle:"eru"' and params["gsrnamespace"] == 6
        return {"continue": {"gsroffset": offset + 1, "continue": "gsroffset||"},
                "query": {"pages": [file_page(1, "cc-by-4.0", "CC BY 4.0") if offset == 0 else file_page(10 + offset, "cc0", "CC0")]}}

    client = FakeClient([
        (lambda u, p: p.get("prop") == "categoryinfo", {"query": {"pages": [{"title": "Category:Eru", "categoryinfo": {"size": 1}}]}}),
        (lambda u, p: p.get("list") == "categorymembers", {"query": {"categorymembers": []}}),
        (lambda u, p: p.get("generator") == "categorymembers", {"query": {"pages": [file_page(1, "cc-by-4.0", "CC BY 4.0")]}}),
        (lambda u, p: p.get("generator") == "search", search),
    ])
    result = commons.collect(client, {"id": "eru", "commons_categories": ["Eru"], "commons_search": ["eru"]}, depth=1)
    assert [r.identifier for r in result.records] == ["1"]
    assert [r.identifier for r in result.search_records] == ["11"]  # page 1 already found in the category; cap after 2 batches
