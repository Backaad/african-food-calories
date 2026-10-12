import pytest

from afcdata.licenses import is_allowed, normalize


@pytest.mark.parametrize(
    "raw, family",
    [
        ("cc0", "cc0"),
        ("CC0", "cc0"),
        ("CC0 1.0", "cc0"),
        ("pd", "pd"),
        ("Public domain", "pd"),
        ("pdm", "pd"),
        ("PD-self", "pd"),
        ("cc-by-4.0", "cc-by"),
        ("CC BY 2.0", "cc-by"),
        ("by", "cc-by"),
        ("cc-by-sa-3.0", "cc-by-sa"),
        ("CC BY-SA 4.0", "cc-by-sa"),
        ("cc-by-sa-2.5,2.0,1.0", "cc-by-sa"),
        ("by-sa", "cc-by-sa"),
        ("CC BY-NC 2.0", "cc-by-nc"),
        ("by-nc-sa", "cc-by-nc-sa"),
        ("cc-by-nd-4.0", "cc-by-nd"),
        ("CC BY-NC-ND 3.0", "cc-by-nc-nd"),
        ("GFDL", "unknown:GFDL"),
        ("Fair use", "unknown:Fair use"),
        ("", "unknown:"),
        (None, "unknown:"),
        ("bysa-weird", "unknown:bysa-weird"),
    ],
)
def test_normalize(raw, family):
    assert normalize(raw) == family


@pytest.mark.parametrize("family", ["cc0", "pd", "cc-by", "cc-by-sa"])
def test_open_families_allowed(family):
    assert is_allowed(family)


@pytest.mark.parametrize("family", ["cc-by-nc", "cc-by-nd", "cc-by-nc-sa", "cc-by-nc-nd", "unknown:GFDL", "unknown:"])
def test_restricted_families_rejected(family):
    assert not is_allowed(family)
