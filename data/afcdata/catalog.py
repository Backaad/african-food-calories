"""Load and validate data/sources.yaml and data/dishes.yaml."""

from pathlib import Path

import yaml

from .licenses import ALLOWED

DATA_DIR = Path(__file__).resolve().parent.parent
SOURCES_PATH = DATA_DIR / "sources.yaml"
DISHES_PATH = DATA_DIR / "dishes.yaml"

OPEN = {"approved", "approved_per_item"}  # licence verified
TRAINING_ONLY = "approved_training_only"  # risk accepted by the owner, never redistributed
USABLE = OPEN | {TRAINING_ONLY}
STATUSES = USABLE | {"pending", "excluded"}
SOURCE_REQUIRED = ("id", "name", "url", "kind", "status", "review")
DISH_REQUIRED = ("id", "names", "countries")


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_sources(doc: dict) -> list[str]:
    errors = []
    policy_licenses = set(doc.get("policy", {}).get("allowed_licenses", []))
    if policy_licenses != set(ALLOWED):
        errors.append(f"policy.allowed_licenses {sorted(policy_licenses)} != licenses.ALLOWED {sorted(ALLOWED)}")
    seen = set()
    for i, source in enumerate(doc.get("sources", [])):
        where = source.get("id", f"sources[{i}]")
        for key in SOURCE_REQUIRED:
            if not source.get(key):
                errors.append(f"{where}: missing '{key}'")
        if source.get("id") in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(source.get("id"))
        status = source.get("status")
        if status not in STATUSES:
            errors.append(f"{where}: unknown status {status!r}")
        if status in OPEN:
            if not source.get("license"):
                errors.append(f"{where}: usable source without 'license'")
            if not source.get("attribution"):
                errors.append(f"{where}: usable source without 'attribution'")
        elif not source.get("status_reason"):
            errors.append(f"{where}: status {status!r} needs a 'status_reason'")
        if status == TRAINING_ONLY:
            risk = source.get("risk_accepted") or {}
            if not (risk.get("by") and risk.get("date")):
                errors.append(f"{where}: training-only source needs risk_accepted.by and risk_accepted.date")
            if not doc.get("policy", {}).get("training_only_conditions"):
                errors.append(f"{where}: training-only source but policy.training_only_conditions is empty")
            if not source.get("citation"):
                errors.append(f"{where}: training-only source needs a 'citation' for the model card")
        if not (source.get("review") or {}).get("verified_by"):
            errors.append(f"{where}: review.verified_by must say how the licence was checked")
    return errors


def validate_dishes(doc: dict) -> list[str]:
    errors = []
    thresholds = doc.get("thresholds", {})
    if not (0 < thresholds.get("few_shot", 0) < thresholds.get("model", 0)):
        errors.append("thresholds: need 0 < few_shot < model")
    seen = set()
    for i, dish in enumerate(doc.get("dishes", [])):
        where = dish.get("id", f"dishes[{i}]")
        for key in DISH_REQUIRED:
            if not dish.get(key):
                errors.append(f"{where}: missing '{key}'")
        if dish.get("id") in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(dish.get("id"))
        names = dish.get("names") or {}
        for lang in ("en", "fr"):
            if not names.get(lang):
                errors.append(f"{where}: missing names.{lang}")
    return errors


def validate_cross(sources_doc: dict, dishes_doc: dict) -> list[str]:
    dish_ids = {d["id"] for d in dishes_doc.get("dishes", [])}
    errors = []
    for source in sources_doc.get("sources", []):
        for dish_id in source.get("dishes") or []:
            if dish_id not in dish_ids:
                errors.append(f"{source['id']}: dish {dish_id!r} not in dishes.yaml")
        for dish_id in ((source.get("segmentation") or {}).get("class_map") or {}).values():
            if dish_id is not None and dish_id not in dish_ids:
                errors.append(f"{source['id']}: class_map dish {dish_id!r} not in dishes.yaml")
        for dish_id in source.get("dish_counts") or {}:
            if dish_id not in dish_ids:
                errors.append(f"{source['id']}: dish_counts dish {dish_id!r} not in dishes.yaml")
        for dish_id in source.get("reported_counts") or {}:
            if dish_id not in dish_ids:
                errors.append(f"{source['id']}: reported_counts dish {dish_id!r} not in dishes.yaml")
    return errors


def load_and_validate(sources_path: Path = SOURCES_PATH, dishes_path: Path = DISHES_PATH) -> tuple[dict, dict]:
    sources_doc = load_yaml(sources_path)
    dishes_doc = load_yaml(dishes_path)
    errors = validate_sources(sources_doc) + validate_dishes(dishes_doc) + validate_cross(sources_doc, dishes_doc)
    if errors:
        raise ValueError("Invalid data catalogue:\n  " + "\n  ".join(errors))
    return sources_doc, dishes_doc


def source_by_id(sources_doc: dict, source_id: str) -> dict:
    for source in sources_doc["sources"]:
        if source["id"] == source_id:
            return source
    raise KeyError(source_id)


def is_training_only(sources_doc: dict, source_id: str) -> bool:
    return source_by_id(sources_doc, source_id)["status"] == TRAINING_ONLY


def require_usable(sources_doc: dict, source_id: str) -> None:
    status = source_by_id(sources_doc, source_id)["status"]
    if status not in USABLE:
        raise PermissionError(f"Source {source_id!r} has status {status!r}; refusing to use it.")
