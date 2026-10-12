"""Licence normalisation shared by every source.

Sources spell licences in many ways ("CC BY-SA 4.0", "cc-by-sa-4.0", "by-sa",
"Public domain", "pdm" ...). `normalize` maps them to a small set of families;
only the families in ALLOWED are kept for training.
"""

import re

ALLOWED = frozenset({"cc0", "pd", "cc-by", "cc-by-sa"})


def normalize(raw: str | None) -> str:
    """Return the licence family for a raw licence string.

    Families: cc0, pd, cc-by, cc-by-sa, cc-by-nc, cc-by-nd, cc-by-nc-sa,
    cc-by-nc-nd, or "unknown:<raw>" for anything else (GFDL-only, fair use,
    copyrighted, empty ...).
    """
    if not raw:
        return "unknown:"
    text = raw.strip().lower()
    slug = re.sub(r"[\s_]+", "-", text)

    if slug.startswith(("cc0", "cc-zero", "cc-0")):
        return "cc0"
    if slug in {"pd", "pdm", "public-domain", "publicdomain"} or slug.startswith(
        ("pd-", "public-domain-", "pdm-")
    ):
        return "pd"

    # Strip an optional "cc-" prefix and any version suffix ("-4.0", " 2.5 in").
    body = slug[3:] if slug.startswith("cc-") else slug
    body = re.sub(r"-?\d+(\.\d+)*.*$", "", body).strip("-")
    parts = body.split("-")
    if not parts or parts[0] != "by":
        return f"unknown:{raw.strip()}"

    terms = set(parts[1:])
    if not terms <= {"sa", "nc", "nd"}:
        return f"unknown:{raw.strip()}"
    family = "cc-by"
    for term in ("nc", "nd", "sa"):
        if term in terms:
            family += f"-{term}"
    return family


def is_allowed(family: str) -> bool:
    return family in ALLOWED
