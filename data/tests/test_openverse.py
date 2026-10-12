from conftest import FakeClient

from afcdata import openverse


def item(i, license="by-sa", version="2.0"):
    return {
        "id": f"uuid-{i}",
        "title": f"Waakye {i}",
        "foreign_landing_url": f"https://www.flickr.com/photos/x/{i}",
        "url": f"https://live.staticflickr.com/{i}.jpg",
        "creator": "Kofi",
        "license": license,
        "license_version": version,
        "license_url": "https://creativecommons.org/licenses/by-sa/2.0/",
        "filetype": "jpg",
    }


def test_parse_result():
    record, family = openverse.parse_result(item(1), "waakye")
    assert family == "cc-by-sa"
    assert record.license_name == "CC BY-SA 2.0"
    assert record.landing_url.startswith("https://www.flickr.com")
    assert openverse.parse_result(item(2, license="by-nc"), "waakye") == (None, "cc-by-nc")
    record, _ = openverse.parse_result(item(3, license="pdm", version="1.0"), "waakye")
    assert record.license_name == "Public Domain Mark 1.0"


def test_count_sends_licence_filter_and_excludes_wikimedia():
    client = FakeClient([(lambda u, p: u.endswith("/images/"), {"result_count": 42, "results": []})])
    assert openverse.count(client, "waakye") == 42
    params = client.calls[0][1]
    assert params["license"] == "cc0,pdm,by,by-sa"
    assert params["excluded_source"] == "wikimedia"


def test_search_stops_at_last_page():
    pages = {1: [item(1), item(2, license="by-nd")], 2: [item(3)]}
    client = FakeClient([(lambda u, p: True, lambda p: {"page_count": 2, "results": pages[p["page"]]})])
    records = list(openverse.search(client, "waakye", "waakye", max_pages=5))
    assert [r.identifier for r in records] == ["uuid-1", "uuid-3"]
    assert len(client.calls) == 2


def test_auth_headers_absent_without_env(monkeypatch):
    monkeypatch.delenv("OPENVERSE_CLIENT_ID", raising=False)
    monkeypatch.delenv("OPENVERSE_CLIENT_SECRET", raising=False)
    assert openverse.auth_headers(object()) == {}
