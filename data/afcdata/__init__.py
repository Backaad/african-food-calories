"""Data inventory and download tools for african-food-calories."""

from dataclasses import asdict, dataclass

USER_AGENT = (
    "african-food-calories-data/0.1 "
    "(+https://github.com/backaad/african-food-calories; open-source dataset inventory)"
)


@dataclass(frozen=True)
class ImageRecord:
    """One openly licensed image candidate and everything needed to credit it."""

    source: str  # id from sources.yaml
    dish_id: str
    identifier: str  # stable id inside the source (Commons page id, Openverse uuid)
    title: str
    landing_url: str  # human page that shows the licence
    image_url: str  # file to download (a resized thumbnail when available)
    license_family: str  # normalised, see licenses.py
    license_name: str  # as displayed by the source, e.g. "CC BY-SA 4.0"
    license_url: str
    author: str
    mime: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
