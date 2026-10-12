import copy

from afcdata.catalog import load_and_validate, load_yaml, validate_cross, validate_dishes, validate_sources, SOURCES_PATH, DISHES_PATH


def test_repository_catalogue_is_valid():
    sources, dishes = load_and_validate()
    assert sources["sources"] and dishes["dishes"]


def test_no_dataset_with_scraped_images_is_usable():
    sources = load_yaml(SOURCES_PATH)
    never = sources["policy"]["never_from"]
    for source in sources["sources"]:
        if source["status"] in {"approved", "approved_per_item"}:
            provenance = source.get("provenance", "").lower()
            assert not any(word in provenance for word in never), source["id"]


def test_excluded_source_needs_reason():
    doc = copy.deepcopy(load_yaml(SOURCES_PATH))
    doc["sources"][-1].pop("status_reason")
    assert any("status_reason" in e for e in validate_sources(doc))


def test_usable_source_needs_attribution():
    doc = copy.deepcopy(load_yaml(SOURCES_PATH))
    doc["sources"][0].pop("attribution")
    assert any("attribution" in e for e in validate_sources(doc))


def test_unknown_status_rejected():
    doc = copy.deepcopy(load_yaml(SOURCES_PATH))
    doc["sources"][0]["status"] = "probably-fine"
    assert any("unknown status" in e for e in validate_sources(doc))


def test_duplicate_dish_and_missing_french_name():
    doc = copy.deepcopy(load_yaml(DISHES_PATH))
    doc["dishes"].append({"id": doc["dishes"][0]["id"], "names": {"en": "x"}, "countries": ["CM"]})
    errors = validate_dishes(doc)
    assert any("duplicate id" in e for e in errors)
    assert any("names.fr" in e for e in errors)


def test_cross_reference_to_unknown_dish():
    sources = copy.deepcopy(load_yaml(SOURCES_PATH))
    dishes = load_yaml(DISHES_PATH)
    sources["sources"][2]["dishes"] = ["not_a_dish"]
    assert validate_cross(sources, dishes) == [f"{sources['sources'][2]['id']}: dish 'not_a_dish' not in dishes.yaml"]
