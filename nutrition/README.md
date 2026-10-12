# Nutrition

Calorie and macronutrient estimates for every dish. Method:
[`docs/nutrition-method.md`](../docs/nutrition-method.md).

| File | What it is |
|---|---|
| [`recipes.yaml`](recipes.yaml) | Standard recipe of each dish (grams per 100 g, WAFCT codes, ranges, portions). **Drafts.** |
| [`wafct_extract.csv`](wafct_extract.csv) | WAFCT 2019 values of the foods used by the recipes. Generated. |
| [`dishes.json`](dishes.json) | Result used by the app. Generated. |
| [`wafct.py`](wafct.py) | Downloads WAFCT 2019 from FAO, searches it, writes the extract. |
| [`compute.py`](compute.py) | Computes `dishes.json` from the recipes and the extract. |

```bash
pip install -r nutrition/requirements.txt
python nutrition/wafct.py search "cassava|manioc"   # find a food code
python nutrition/wafct.py extract                  # after adding a code to recipes.yaml
python nutrition/compute.py                        # regenerate dishes.json
python -m pytest -q nutrition/tests
```

`wafct.py` downloads the Excel file into `nutrition/cache/` (ignored by git).

## Source and licence

Values come from the FAO/INFOODS Food Composition Table for Western Africa
(2019), FAO, Rome, 2020 (Vincent A., Grande F., Compaoré E. et al.). Only the
rows used by the recipes are stored here, with their WAFCT codes, so anyone can
check them against the original. The full table is not redistributed. The
licence of the WAFCT datasheets has not been confirmed yet: FAO publications
are usually CC BY-NC-SA 3.0 IGO, which would require attribution,
non-commercial use and sharing derived data under the same terms.
