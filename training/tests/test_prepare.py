import csv
import json
from collections import Counter

from PIL import Image

from afctrain import OTHER
from afctrain.prepare import Item, assign_labels, cap_per_dish, choose_classes, drop_duplicates, finalize, split_for

FRACTIONS = {"train": 0.7, "val": 0.15, "test": 0.15}


def test_split_is_deterministic_and_close_to_fractions():
    splits = [split_for(f"commons:{i}", None, FRACTIONS) for i in range(5000)]
    assert splits == [split_for(f"commons:{i}", None, FRACTIONS) for i in range(5000)]
    share = Counter(splits)
    assert abs(share["train"] / 5000 - 0.70) < 0.03 and abs(share["test"] / 5000 - 0.15) < 0.03


def test_source_test_set_stays_test_and_source_train_set_never_becomes_test():
    assert {split_for(f"cf:{i}", "test", FRACTIONS) for i in range(300)} == {"test"}
    assert {split_for(f"cf:{i}", "train", FRACTIONS) for i in range(300)} == {"train", "val"}


def test_duplicates_kept_once_and_conflicting_labels_dropped():
    items = [Item("a", "fufu", "s", "1"), Item("b", "fufu", "s", "2"), Item("c", "eru", "s", "3"),
             Item("d", "fufu", "s", "4"), Item("e", "ugali", "s", "5")]
    hashes = {"a": "h1", "b": "h1", "c": "h2", "d": "h2", "e": "h3"}
    kept, stats = drop_duplicates(items, hashes)
    assert sorted(i.path for i in kept) == ["a", "e"]
    assert stats == {"duplicates": 1, "conflicting_labels": 2}


def test_small_dishes_are_learnt_as_other():
    items = [Item(str(i), "fufu", "s", str(i)) for i in range(5)] + [Item("x", "eru", "s", "x"), Item("y", OTHER, "s", "y")]
    classes = choose_classes(items, min_images=3)
    assert classes == ["fufu", OTHER]
    assign_labels(items, classes)
    assert {i.dish: i.label for i in items} == {"fufu": "fufu", "eru": OTHER, OTHER: OTHER}


def test_cap_per_dish():
    items = [Item(str(i), "fufu", "s", str(i)) for i in range(10)] + [Item("o", OTHER, "s", "o")]
    kept = cap_per_dish(items, 4)
    assert Counter(i.dish for i in kept) == {"fufu": 4, OTHER: 1}


def test_finalize_writes_manifest_without_split_leaks(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    items = []
    for i in range(40):
        dish = ["fufu", "ugali", OTHER, "eru"][i % 4]
        path = raw / f"{i}.png"
        Image.new("RGB", (700, 300), (i * 6 % 255, i * 3 % 255, 100)).save(path)
        # two crops of the same CamerFood10 photo share a group
        items.append(Item(str(path), dish, "camerfood10" if i < 8 else "wikimedia-commons",
                          f"photo:{i // 2}" if i < 8 else f"commons:{i}", origin_split="train" if i < 8 else None))
    config = {"min_images": 8, "max_per_class": 100, "split": FRACTIONS}
    hashes_unique = {it.path: str(n) for n, it in enumerate(items)}

    import afctrain.prepare as prep
    original = prep.perceptual_hash
    prep.perceptual_hash = lambda p: hashes_unique[str(p)]
    try:
        summary = finalize(items, tmp_path / "dataset", config, {"missing_categories": []})
    finally:
        prep.perceptual_hash = original

    assert summary["classes"] == ["eru", "fufu", "ugali", OTHER]
    with open(tmp_path / "dataset" / "manifest.csv") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 40
    groups = {}
    for row in rows:
        assert groups.setdefault(row["group"], row["split"]) == row["split"]
        assert (tmp_path / "dataset" / row["path"]).exists()
    assert all(r["split"] != "test" for r in rows if r["source"] == "camerfood10")
    with Image.open(tmp_path / "dataset" / rows[0]["path"]) as im:
        assert max(im.size) <= 512
    assert json.loads((tmp_path / "dataset" / "summary.json").read_text())["images"] == 40
