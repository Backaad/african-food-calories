import pytest

import compute

FOODS = {
    "01_001": {"name_en": "Rice, boiled", "energy_kcal": 130, "protein_g": 2.6, "fat_g": 0.3, "carbohydrate_g": 28.1, "fibre_g": 0.4},
    "11_001": {"name_en": "Oil, palm", "energy_kcal": 884, "protein_g": 0, "fat_g": 100, "carbohydrate_g": 0, "fibre_g": 0},
}
PORTIONS = {"small": 200, "medium": 300, "large": 450}


def recipe(ingredients, **extra):
    return {"id": "jollof_rice", "portions": PORTIONS, "ingredients": ingredients, **extra}


def test_fixed_recipe():
    values = compute.recipe_values([{"code": "01_001", "g": 90}, {"code": "11_001", "g": 10}], FOODS, 1)
    assert values["energy_kcal"] == pytest.approx(0.9 * 130 + 0.1 * 884)
    assert values["fat_g"] == pytest.approx(0.9 * 0.3 + 10)


def test_water_dilutes():
    values = compute.recipe_values([{"code": "01_001", "g": 50}, {"code": "water", "g": 50}], FOODS, 1)
    assert values["energy_kcal"] == pytest.approx(65)


def test_oil_range_is_rescaled_to_100_g():
    ingredients = [{"code": "01_001", "g": 92}, {"code": "11_001", "g": [4, 12]}]
    low = compute.recipe_values(ingredients, FOODS, 0)
    high = compute.recipe_values(ingredients, FOODS, 2)
    # low: 92 g rice + 4 g oil = 96 g, rescaled to 100 g
    assert low["energy_kcal"] == pytest.approx((92 * 130 + 4 * 884) / 96)
    assert high["energy_kcal"] == pytest.approx((92 * 130 + 12 * 884) / 104)
    assert low["energy_kcal"] < high["energy_kcal"]


def test_dish_nutrition_ranges_and_portions():
    result = compute.dish_nutrition(recipe([{"code": "01_001", "g": 92}, {"code": "11_001", "g": [4, 12]}]), FOODS)
    energy = result["per_100g"]["energy_kcal"]
    assert energy["low"] < energy["typical"] < energy["high"]
    assert isinstance(energy["typical"], int)
    medium = next(p for p in result["portions"] if p["size"] == "medium")
    assert medium["grams"] == 300
    assert medium["energy_kcal"]["typical"] == round(energy["typical"] * 3)


def test_validate_catches_common_mistakes():
    recipes = {"recipes": [
        recipe([{"code": "99_999", "g": 100}]),
        {"id": "ghost", "portions": {"small": 300, "medium": 200, "large": 400}, "ingredients": [{"code": "01_001", "g": 60}]},
        recipe([{"code": "01_001", "g": [20, 10]}, {"code": "water", "g": 85}], id="eru"),
    ]}
    errors = compute.validate(recipes, FOODS, ["jollof_rice", "eru", "ndole"])
    text = "\n".join(errors)
    assert "ndole: no recipe" in text
    assert "jollof_rice: unknown food code '99_999'" in text
    assert "ghost: recipe for a dish not in data/dishes.yaml" in text
    assert "ghost: portions need small < medium < large grams" in text
    assert "ghost: typical recipe weighs 60 g" in text
    assert "eru: bad range [20, 10]" in text


def test_build_carries_names_disclaimer_and_status():
    dishes_doc = {"dishes": [{"id": "jollof_rice", "names": {"en": "Jollof rice", "fr": "Riz jollof"}, "countries": ["GH"]}]}
    recipes = {"recipes": [recipe([{"code": "01_001", "g": 95}, {"code": "11_001", "g": 5, "note": "palm or vegetable oil"}])]}
    out = compute.build(recipes, FOODS, dishes_doc)
    dish = out["dishes"][0]
    assert out["disclaimer"]["fr"].startswith("Estimation à faire valider par un nutritionniste")
    assert dish["names"]["fr"] == "Riz jollof"
    assert dish["recipe_status"] == "draft" and dish["validated_by_nutritionist"] is False
    assert dish["recipe"][1] == {"code": "11_001", "name": "Oil, palm", "g": 5, "note": "palm or vegetable oil"}
