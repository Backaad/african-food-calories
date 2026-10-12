from pathlib import Path

import download
from afcdata import ImageRecord
from afcdata.catalog import load_yaml, SOURCES_PATH
from afcdata.inventory import classify, render_markdown, summarize_dish

THRESHOLDS = {"model": 150, "few_shot": 20}
DISH = {"id": "ndole", "names": {"en": "Ndolé", "fr": "Ndolé"}, "countries": ["CM"]}


def test_classify_boundaries():
    assert classify(150, THRESHOLDS) == "model"
    assert classify(149, THRESHOLDS) == "few_shot"
    assert classify(20, THRESHOLDS) == "few_shot"
    assert classify(19, THRESHOLDS) == "manual"


def test_openverse_only_raises_upper_bound():
    row = summarize_dish(DISH, {"allowed": 30, "rejected": {}}, {"hits": 200}, {}, THRESHOLDS)
    assert row["reliable"] == 30 and row["upper_bound"] == 230
    assert row["status"] == "few_shot"
    assert row["status_upper_bound"] == "model"


def test_commons_search_only_raises_upper_bound():
    row = summarize_dish(DISH, {"allowed": 10, "search_allowed": 15, "rejected": {}}, {"hits": 0}, {}, THRESHOLDS)
    assert row["reliable"] == 10 and row["upper_bound"] == 25
    assert row["status"] == "manual" and row["status_upper_bound"] == "few_shot"


def test_failed_sources_are_not_counted_as_zero():
    row = summarize_dish(DISH, {"error": "boom"}, {"hits": 3}, {}, THRESHOLDS)
    assert row["status"] == "unknown" and row["status_upper_bound"] == "unknown"
    row = summarize_dish(DISH, {"allowed": 25, "rejected": {}}, {"error": "rate-limited"}, {}, THRESHOLDS)
    assert row["status"] == "few_shot" and row["status_upper_bound"] == "unknown"


def test_render_markdown_lists_dishes_missing_categories_and_excluded_datasets():
    sources = load_yaml(SOURCES_PATH)
    rows = [
        summarize_dish(DISH, {"allowed": 160, "search_allowed": 4, "rejected": {"cc-by-nc": 3},
                              "missing_categories": ["Category:Ndole"], "walked_categories": ["Category:Ndolè", "Category:Ndolè in Douala"]},
                       {"hits": 240}, {}, THRESHOLDS),
        summarize_dish({**DISH, "id": "eru", "names": {"en": "Eru", "fr": "Eru"}}, None, {"error": "rate-limited"}, {}, THRESHOLDS),
    ]
    text = render_markdown(rows, sources, THRESHOLDS, {"date": "2026-10-12", "commons_depth": 1})
    assert "| Ndolé (`ndole`) | CM | 160 | 4 | 3 | ≥240 | model (needs review) |" in text
    assert "| Eru (`eru`) | CM | not run |  |  | rate-limited | not counted | not counted |" in text
    assert "- `ndole`: Ndolè, Ndolè in Douala" in text
    assert "- `ndole`: Category:Ndole" in text
    assert "Totals: 1 model, 0 few-shot, 0 manual entry, 1 not counted (2 dishes)." in text
    assert "African Foods Datasets" in text and "Nigerian Food Dataset" in text
    assert "Wikimedia Commons" not in text.split("## Datasets not used")[1]


def record(identifier, url, mime="image/jpeg", source="openverse"):
    return ImageRecord(source, "waakye", identifier, "t", "l", url, "cc-by", "CC BY", "u", "a", mime)


def test_dedupe_by_image_url():
    records = [record("1", "https://x/a.jpg"), record("2", "https://x/a.jpg"), record("3", "https://x/b.jpg")]
    assert [r.identifier for r in download.dedupe(records)] == ["1", "3"]


def test_file_path_is_safe_and_typed():
    path = download.file_path(Path("/out"), record("../../etc/passwd", "https://x/a.JPEG?x=1", mime=""))
    assert path.parent == Path("/out/waakye")  # no directory traversal
    assert path.name == "openverse-.._.._etc_passwd.jpg"
    assert download.file_path(Path("/out"), record("7", "https://x/a", mime="image/png")).suffix == ".png"
