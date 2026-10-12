#!/usr/bin/env python3
"""Compute energy and macronutrients of every dish from its standard recipe.

    python nutrition/compute.py            # writes nutrition/dishes.json
    python nutrition/compute.py --check    # fails if dishes.json is out of date

Inputs:
  nutrition/recipes.yaml       standard recipes: grams of each ingredient per 100 g of dish
  nutrition/wafct_extract.csv  WAFCT 2019 values (per 100 g edible portion) of the foods used
  data/dishes.yaml             dish names and countries

Method (details in docs/nutrition-method.md): an ingredient amount is either a
number or a [low, high] range. The "low" recipe takes every low amount, the
"high" recipe every high amount, "typical" the midpoints. Amounts are parts of
100 g: if a range makes a recipe weigh more or less than 100 g, the whole recipe
is rescaled to 100 g, so more oil means proportionally less of everything else.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import yaml

NUTRITION_DIR = Path(__file__).resolve().parent
ROOT = NUTRITION_DIR.parent
RECIPES = NUTRITION_DIR / "recipes.yaml"
EXTRACT = NUTRITION_DIR / "wafct_extract.csv"
DISHES = ROOT / "data" / "dishes.yaml"
OUTPUT = NUTRITION_DIR / "dishes.json"

NUTRIENTS = ("energy_kcal", "protein_g", "fat_g", "carbohydrate_g", "fibre_g")
WATER = "water"  # pseudo-ingredient: drinking water, no nutrients
DISCLAIMER = {
    "en": "Estimate to be validated by a nutritionist. Not medical advice.",
    "fr": "Estimation à faire valider par un nutritionniste. Ce n'est pas un conseil médical.",
}
SOURCE = (  # required citation of WAFCT 2019 (datasheet '01 Introduction')
    "Vincent, A., Grande, F., Compaoré, E., Amponsah Annor, G., Addy, P.A., Aburime, L.C., Ahmed, "
    "D., Bih Loh, A.M., Dahdouh Cabia, S., Deflache, N., Dembélé, F.M., Dieudonné, B., Edwige, O.B., "
    "Ene-Obong, H.N., Fanou Fogny, N., Ferreira, M., Omaghomi Jemide, J., Kouebou, P.C., Muller, C., "
    "Nájera Espinosa, S., Ouattara, F., Rittenschober, D., Schönfeldt, H., Stadlmayr, B., van "
    "Deventer, M., Razikou Yiagnigni, A. & Charrondière, U.R. 2020. FAO/INFOODS Food Composition "
    "Table for Western Africa (2019) User Guide & Condensed Food Composition Table / Table de "
    "composition des aliments FAO/INFOODS pour l’Afrique de l’Ouest (2019) Guide d’utilisation & "
    "table de composition des aliments condensée. Rome, FAO."
)
SOURCE_TERMS = "© FAO, 2020. Used for a non-commercial product with acknowledgement of FAO as source and copyright holder; FAO does not endorse this project."


def load_foods(path: Path = EXTRACT) -> dict[str, dict]:
    foods = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            foods[row["code"]] = {
                "name_en": row["name_en"],
                **{k: float(row[k]) if row[k] not in ("", None) else 0.0 for k in NUTRIENTS},
            }
    return foods


def amounts(ingredient: dict) -> tuple[float, float, float]:
    """(low, typical, high) grams of one ingredient."""
    g = ingredient["g"]
    if isinstance(g, list):
        low, high = float(g[0]), float(g[1])
        if not 0 <= low <= high:
            raise ValueError(f"bad range {g} for {ingredient.get('code')}")
        return low, (low + high) / 2, high
    return float(g), float(g), float(g)


def recipe_values(ingredients: list[dict], foods: dict[str, dict], which: int) -> dict[str, float]:
    """Nutrients per 100 g of dish for one variant (0 low, 1 typical, 2 high)."""
    total = 0.0
    sums = dict.fromkeys(NUTRIENTS, 0.0)
    for ingredient in ingredients:
        grams = amounts(ingredient)[which]
        total += grams
        if ingredient["code"] == WATER:
            continue
        food = foods[ingredient["code"]]
        for k in NUTRIENTS:
            sums[k] += grams * food[k] / 100
    if total <= 0:
        raise ValueError("recipe weighs nothing")
    return {k: v * 100 / total for k, v in sums.items()}


def _round(key: str, value: float) -> float | int:
    return round(value) if key == "energy_kcal" else round(value, 1)


def dish_nutrition(recipe: dict, foods: dict[str, dict]) -> dict:
    variants = [recipe_values(recipe["ingredients"], foods, i) for i in range(3)]
    per_100g = {}
    for k in NUTRIENTS:
        low, typical, high = (v[k] for v in variants)
        per_100g[k] = {
            "low": _round(k, min(low, high)),
            "typical": _round(k, typical),
            "high": _round(k, max(low, high)),
        }
    portions = []
    for size in ("small", "medium", "large"):
        grams = recipe["portions"][size]
        portions.append({
            "size": size,
            "grams": grams,
            "energy_kcal": {b: round(per_100g["energy_kcal"][b] * grams / 100) for b in ("low", "typical", "high")},
        })
    return {"per_100g": per_100g, "portions": portions}


def validate(recipes: dict, foods: dict[str, dict], dish_ids: list[str]) -> list[str]:
    errors = []
    by_id = {r["id"]: r for r in recipes["recipes"]}
    for dish_id in dish_ids:
        if dish_id not in by_id:
            errors.append(f"{dish_id}: no recipe")
    for recipe in recipes["recipes"]:
        where = recipe["id"]
        if where not in dish_ids:
            errors.append(f"{where}: recipe for a dish not in data/dishes.yaml")
        portions = recipe.get("portions") or {}
        sizes = [portions.get(s) for s in ("small", "medium", "large")]
        if not all(isinstance(s, (int, float)) and s > 0 for s in sizes) or sizes != sorted(sizes):
            errors.append(f"{where}: portions need small < medium < large grams")
        typical_total = 0.0
        for ingredient in recipe.get("ingredients") or []:
            code = ingredient.get("code")
            if code != WATER and code not in foods:
                errors.append(f"{where}: unknown food code {code!r}")
            try:
                typical_total += amounts(ingredient)[1]
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                errors.append(f"{where}: {exc}")
        if not 95 <= typical_total <= 105:
            errors.append(f"{where}: typical recipe weighs {typical_total:g} g, expected about 100 g")
        if not recipe.get("ingredients"):
            errors.append(f"{where}: no ingredients")
    return errors


def build(recipes: dict, foods: dict[str, dict], dishes_doc: dict) -> dict:
    by_id = {r["id"]: r for r in recipes["recipes"]}
    out = []
    for dish in dishes_doc["dishes"]:
        recipe = by_id[dish["id"]]
        out.append({
            "id": dish["id"],
            "names": dish["names"],
            "countries": dish["countries"],
            **dish_nutrition(recipe, foods),
            "recipe": [
                {
                    "code": i["code"],
                    "name": "water" if i["code"] == WATER else foods[i["code"]]["name_en"],
                    "g": i["g"],
                    **({"note": i["note"]} if i.get("note") else {}),
                }
                for i in recipe["ingredients"]
            ],
            "recipe_status": recipe.get("status", "draft"),
            "validated_by_nutritionist": False,
            **({"notes": recipe["notes"]} if recipe.get("notes") else {}),
        })
    return {
        "disclaimer": DISCLAIMER,
        "source": SOURCE,
        "source_terms": SOURCE_TERMS,
        "method": "docs/nutrition-method.md",
        "units": {"per_100g": "per 100 g of dish as eaten", "energy": "kcal", "others": "g"},
        "dishes": out,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if dishes.json differs from a fresh build")
    args = parser.parse_args(argv)

    with open(RECIPES, encoding="utf-8") as f:
        recipes = yaml.safe_load(f)
    with open(DISHES, encoding="utf-8") as f:
        dishes_doc = yaml.safe_load(f)
    foods = load_foods()
    errors = validate(recipes, foods, [d["id"] for d in dishes_doc["dishes"]])
    if errors:
        sys.exit("Invalid recipes:\n  " + "\n  ".join(errors))

    text = json.dumps(build(recipes, foods, dishes_doc), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != text:
            sys.exit("nutrition/dishes.json is out of date: run python nutrition/compute.py")
        print("dishes.json is up to date")
        return
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(dishes_doc['dishes'])} dishes)")


if __name__ == "__main__":
    main()
