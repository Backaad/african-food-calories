# How the calories are estimated

> **Estimate to be validated by a nutritionist. This is not medical advice.**
> The recipes and portion sizes below are drafts. No value in
> `nutrition/dishes.json` has been checked by a nutritionist yet
> (`validated_by_nutritionist: false` on every dish).

A photo does not give calories. The app recognises the dish, then looks up a
pre-computed estimate for that dish. This page explains how those estimates are
made, so anyone can check or improve them.

## 1. A standard recipe per dish

Each dish in `data/dishes.yaml` has one standard recipe in
[`nutrition/recipes.yaml`](../nutrition/recipes.yaml): the grams of each
ingredient in **100 g of the dish as eaten**. Each ingredient is a food of the
West African food composition table (below), identified by its code, in the
state it has in the dish (boiled, stewed, fried, raw...). Plain water has no
nutrients.

**Soups and sauces are described without what they are eaten with.** Ndolé,
eru, egusi soup, palm nut soup, mafé, yassa, doro wat… are the soup or stew
only. The fufu, pounded yam, rice, plantain or injera is a separate dish in the
list, and the user logs both. Achu is the exception: the pounded taro and
yellow soup are always served together and are one recipe.

The recipes were drafted from general knowledge of how these dishes are cooked.
They were not measured in kitchens. They need to be reviewed by people who
cook these dishes.

## 2. Nutrient values from WAFCT 2019

Ingredient values come from the **FAO/INFOODS Food Composition Table for
Western Africa (2019)** (WAFCT 2019): Vincent A., Grande F., Compaoré E. et al.,
FAO, Rome, 2020. The Excel datasheets are downloaded from FAO by
`nutrition/wafct.py`; only the rows of the foods the recipes use are kept, in
[`nutrition/wafct_extract.csv`](../nutrition/wafct_extract.csv), with their
WAFCT code. CI checks that this file matches the WAFCT exactly.

Values used, per 100 g edible portion: energy (kcal), protein, fat, available
carbohydrate and total dietary fibre. The WAFCT writes some values in brackets
(estimated, borrowed from another food or calculated); the `estimated` column of
the extract lists them.

**Proxies.** The WAFCT has no entry for some ingredients. A similar food is used
instead and the recipe says so (`proxy: true` with a note):

| Missing ingredient | Used instead | Dishes |
|---|---|---|
| Eru / okok leaves (*Gnetum africanum*) | cassava leaves, boiled | eru, okok |
| Kale (sukuma wiki) | amaranth leaves, boiled | sukuma wiki |
| Chickpea flour | dehulled cowpea, raw | shiro |
| Bobolo, miondo, attiéké | fermented cassava paste (wet fufu) | bobolo, miondo, attiéké |
| Banku | kenkey (cooked fermented maize dough) | banku |

The WAFCT covers West Africa. East African dishes (ugali, injera, sukuma wiki,
pilau...) use the same table for their basic ingredients (maize meal, teff,
rice, beef); a Kenyan or Ethiopian table would be more accurate for them.

## 3. The calculation

`nutrition/compute.py` computes, for each dish:

```
nutrient per 100 g of dish = Σ (grams of ingredient × nutrient per 100 g of ingredient) / total grams
```

Dividing by the total weight means a recipe whose amounts do not add up to
exactly 100 g is rescaled to 100 g.

## 4. A range, not a single number

The same dish varies a lot from one cook to another, mostly because of the
**oil**. In the recipes, the oil (and for swallows like ugali, amala or injera,
the share of flour) is a range `[low, high]`:

- **low**: every range at its low end;
- **typical**: every range at its middle;
- **high**: every range at its high end.

More oil means proportionally less of everything else (the recipe stays 100 g).
The app shows the range (for example "180–260 kcal") rather than one number.

Dishes made of a single food (fufu, kenkey, bobolo, nyama choma...) have no
range: low, typical and high are equal. That does not mean they do not vary,
only that the recipe has nothing to vary.

The range only covers what the recipe says varies. It does **not** cover:
different recipes for the same dish name, the cook's choice of meat or fish,
measurement error in the WAFCT, or a wrong portion size. The true value of a
given plate can fall outside the range.

## 5. Portions

Each dish has three portion sizes in grams (small, medium, large), chosen by
the user. The energy of a portion is the per-100 g range times the portion
weight. Estimating the portion from the photo is a research problem and is not
part of this version.

The portion sizes are drafts too: they should be checked against real servings
(a fufu ball, a plate of jollof, one chapati or injera...).

## 6. Output

[`nutrition/dishes.json`](../nutrition/dishes.json) holds, for every dish:
names in English and French, the per-100 g range of energy, protein, fat,
carbohydrate and fibre, the three portions with their energy range, the recipe
used, `recipe_status` and `validated_by_nutritionist`. It is generated: edit
`recipes.yaml`, then run `python nutrition/compute.py`. CI fails if the
committed file is out of date.

## 7. How to help

- Cook one of these dishes? Weigh the ingredients and the finished dish, and
  open an issue or a pull request on `nutrition/recipes.yaml`.
- Nutritionist? Review a recipe and its values; a reviewed dish gets
  `status: reviewed` in the recipe and, once validated,
  `validated_by_nutritionist: true`.
