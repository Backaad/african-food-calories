import zipfile

import pytest
from PIL import Image

import fetch_datasets


def test_extract_archives_once(tmp_path):
    archive = tmp_path / "CamerFood10.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("train/images/a.jpg", b"x")
    assert fetch_datasets.extract_archives(tmp_path) == [archive]
    assert (tmp_path / "CamerFood10" / "train" / "images" / "a.jpg").exists()
    assert fetch_datasets.extract_archives(tmp_path) == []  # already unpacked


def test_extract_archives_refuses_path_traversal(tmp_path):
    with zipfile.ZipFile(tmp_path / "evil.zip", "w") as zf:
        zf.writestr("../outside.txt", b"x")
    with pytest.raises(ValueError):
        fetch_datasets.extract_archives(tmp_path)
    assert not (tmp_path.parent / "outside.txt").exists()


def test_describe_lists_folders_text_files_and_mask_values(tmp_path):
    (tmp_path / "train" / "images").mkdir(parents=True)
    (tmp_path / "train" / "masks").mkdir(parents=True)
    (tmp_path / "train" / "images" / "1.jpg").write_bytes(b"x")
    (tmp_path / "classes.txt").write_text("0 background\n1 ndole\n2 plantain\n")
    mask = Image.new("L", (4, 4), 0)
    mask.putpixel((0, 0), 2)
    mask.save(tmp_path / "train" / "masks" / "1.png")

    text = fetch_datasets.describe(tmp_path)
    assert "3 files in 3 folders" in text
    assert "train/images/: 1 .jpg" in text
    assert "1 ndole" in text
    assert "modes {'L': 1}" in text
    assert "  0: 1" in text and "  2: 1" in text
