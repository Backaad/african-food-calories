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

Values come from WAFCT 2019. Required citation:

> Vincent, A., Grande, F., Compaoré, E., Amponsah Annor, G., Addy, P.A., Aburime, L.C., Ahmed, D., Bih Loh, A.M., Dahdouh Cabia, S., Deflache, N., Dembélé, F.M., Dieudonné, B., Edwige, O.B., Ene-Obong, H.N., Fanou Fogny, N., Ferreira, M., Omaghomi Jemide, J., Kouebou, P.C., Muller, C., Nájera Espinosa, S., Ouattara, F., Rittenschober, D., Schönfeldt, H., Stadlmayr, B., van Deventer, M., Razikou Yiagnigni, A. & Charrondière, U.R. 2020. FAO/INFOODS Food Composition Table for Western Africa (2019) User Guide & Condensed Food Composition Table / Table de composition des aliments FAO/INFOODS pour l’Afrique de l’Ouest (2019) Guide d’utilisation & table de composition des aliments condensée. Rome, FAO.

Terms of use, from the introduction sheet of the WAFCT Excel datasheets
(© FAO, 2020): the material "may be copied, downloaded and printed for private
study, research and teaching purposes, or for use in non-commercial products
or services, provided that appropriate acknowledgement of FAO as the source and
copyright holder is given and that FAO's endorsement of users' views, products
or services is not implied in any way." Translation, adaptation, resale and
commercial use need FAO's permission (www.fao.org/contact-us/licence-request).

So: this project may use these values because it is non-commercial and credits
FAO. FAO does not endorse it. Only the rows used by the recipes are stored here,
with their WAFCT codes, so anyone can check them; the full table is not
redistributed. Whether computing dish values from the table counts as an
"adaptation" is not settled: ask FAO before any commercial use.
