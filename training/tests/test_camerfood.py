import numpy as np
from PIL import Image

from afctrain import OTHER
from afctrain.camerfood import bbox, crop_image, crops_for, iter_pairs

GRAY = {0: "BG", 25: "taro", 50: "sauce jaune", 150: "riz blanc", 250: "frites de plantains"}
CLASS_MAP = {"taro": "achu", "sauce jaune": "achu", "riz blanc": None, "frites de plantains": "alloco"}


def mask_with(regions, shape=(100, 100)):
    mask = np.zeros(shape, dtype=np.uint8)
    for value, (y0, y1, x0, x1) in regions:
        mask[y0:y1, x0:x1] = value
    return mask


def test_classes_of_one_dish_are_merged_and_non_dishes_become_other():
    mask = mask_with([(25, (0, 20, 0, 50)), (50, (20, 40, 0, 50)), (150, (50, 100, 50, 100)), (250, (0, 5, 95, 100))])
    crops = crops_for(mask, GRAY, CLASS_MAP, min_area=0.10, pad=0.0)
    labels = {label: (box, round(area, 3)) for label, box, area in crops}
    assert labels["achu"] == ((0, 0, 50, 40), 0.2)  # taro + yellow soup, one box
    assert labels[OTHER] == ((50, 50, 100, 100), 0.25)  # white rice
    assert "alloco" not in labels  # 0.25 % of the plate: below min_area


def test_bbox_padding_is_clamped_to_the_image():
    hit = np.zeros((10, 10), bool)
    hit[2:8, 0:4] = True
    assert bbox(hit, 0.5) == (0, 0, 6, 10)


def test_crop_rescales_mask_coordinates(tmp_path):
    Image.new("RGB", (200, 100), "red").save(tmp_path / "a.jpg")
    crop = crop_image(tmp_path / "a.jpg", (50, 100), (10, 5, 60, 25))
    assert crop.size == (100, 40)


def test_iter_pairs_matches_stems(tmp_path):
    (tmp_path / "images").mkdir()
    (tmp_path / "masks").mkdir()
    for stem in ("1", "2"):
        Image.new("RGB", (4, 4)).save(tmp_path / "images" / f"{stem}.jpg")
    Image.new("L", (4, 4)).save(tmp_path / "masks" / "1.png")
    Image.new("L", (4, 4)).save(tmp_path / "masks" / "3.png")
    assert [(i.name, m.name) for i, m in iter_pairs(tmp_path / "images", tmp_path / "masks")] == [("1.jpg", "1.png")]
