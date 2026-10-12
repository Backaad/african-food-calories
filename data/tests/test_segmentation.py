from collections import Counter
from types import SimpleNamespace

import pytest
from PIL import Image

import fetch_datasets
from afcdata import segmentation

COLOR_MAP = """Id\t|\tName(FR)\t\t|\tName(Eng)\t|\tColor (GRAY)\t
0\t|\tBG\t\t\t|\tBG\t\t|\t0
1\t|\ttaro \t\t\t|\tTaro\t\t|\t25
2\t|\tsauce jaune\t\t|\tyellow soup\t|\t50
6\t|\triz blanc\t\t|\twhite rice\t|\t150
10\t|\tfrites de plantains\t| \tfried plantain\t|\t250
"""
GRAY = {0: "BG", 25: "taro", 50: "sauce jaune", 150: "riz blanc", 250: "frites de plantains"}
CLASS_MAP = {"taro": "achu", "sauce jaune": "achu", "riz blanc": None, "frites de plantains": "alloco"}


def make_mask(path, areas):
    """areas: {gray value: number of pixels}; the rest is background."""
    im = Image.new("L", (10, 10), 0)
    pixels = [v for v, n in areas.items() for _ in range(n)]
    for i, v in enumerate(pixels):
        im.putpixel((i % 10, i // 10), v)
    im.save(path)
    return path


def test_parse_color_map():
    assert segmentation.parse_color_map(COLOR_MAP) == GRAY


def test_dominant_merges_classes_of_the_same_dish():
    # taro 20 + yellow soup 20 = achu 40 beats fried plantain 30
    assert segmentation.dominant(Counter({"taro": 20, "sauce jaune": 20, "frites de plantains": 30}), CLASS_MAP) == "achu"


def test_dominant_non_dish_class_wins_nothing():
    assert segmentation.dominant(Counter({"riz blanc": 60, "frites de plantains": 30}), CLASS_MAP) is None
    assert segmentation.dominant(Counter(), CLASS_MAP) is None


def test_stats_counts_presence_dominance_and_unknown_values(tmp_path):
    masks = [
        make_mask(tmp_path / "1.png", {25: 20, 50: 20, 250: 30}),
        make_mask(tmp_path / "2.png", {150: 60, 250: 30}),
        make_mask(tmp_path / "3.png", {250: 5, 99: 1}),
    ]
    result = segmentation.stats(masks, GRAY, CLASS_MAP)
    assert result["images"] == 3
    assert result["present"]["frites de plantains"] == 3
    assert result["present"]["taro"] == 1
    assert result["dominant_dish"] == {"achu": 1, "alloco": 1}
    assert result["unknown"] == {"unknown:99": 1}


def test_segmentation_stats_table(tmp_path):
    (tmp_path / "train").mkdir()
    (tmp_path / "Color_map.txt").write_text(COLOR_MAP)
    make_mask(tmp_path / "train" / "1.png", {25: 20, 50: 20})
    config = {"color_map": "Color_map.txt", "masks": {"train": "train"}, "class_map": CLASS_MAP}
    text = fetch_datasets.segmentation_stats(tmp_path, config)
    assert "| taro | achu | 1 |" in text
    assert "| achu | 1 | 1 |" in text
    assert "| riz blanc | - | 0 |" in text


def test_segmentation_stats_rejects_unmapped_class(tmp_path):
    (tmp_path / "Color_map.txt").write_text(COLOR_MAP)
    config = {"color_map": "Color_map.txt", "masks": {}, "class_map": {"taro": "achu"}}
    with pytest.raises(ValueError, match="sauce jaune"):
        fetch_datasets.segmentation_stats(tmp_path, config)


def test_select_files_keeps_only_wanted_and_reports_missing():
    listing = [SimpleNamespace(id="a", path="CamerFood10.zip"), SimpleNamespace(id="b", path="UECFOODPIXCOMPLETE.zip")]
    assert [f.id for f in fetch_datasets.select_files(listing, ["CamerFood10.zip"])] == ["a"]
    with pytest.raises(RuntimeError, match="Other.zip"):
        fetch_datasets.select_files(listing, ["Other.zip"])
