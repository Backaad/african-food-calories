import openpyxl
import pytest

import wafct

HEADER_EN = ["Code", "Food name in English", "Food name in French", "Scientific name", "BiblioID/Source",
             "Edible portion coefficient 1", "Energy (kJ)", "Energy (kcal)", "Water (g)", "Protein, total (g)",
             "Fat, total or [fat, derived by analysis using continuous extraction] (g)",
             "Carbohydrate, available; calculated by difference (g)",
             "Fibre, total dietary or [fibre, crude] (g)", "Ash (g)"]
HEADER_FR = ["Code", "Nom d’aliment en anglais", "Nom d’aliment en français", "", "", "", "Énergie (kJ)",
             "Énergie (kcal)", "Eau (g)", "Protéines totales (g)", "Lipides", "Glucides", "Fibres", "Cendres (g)"]
TAGS = ["", "", "", "", "", "EDIBLE1", "ENERC", "ENERC", "WATER", "PROTCNT", "FAT", "CHOAVLDF", "FIBTG", "ASH"]


@pytest.fixture
def workbook(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = wafct.MAIN_SHEET
    for row in (HEADER_EN, HEADER_FR, TAGS, ["Cereals and their products/Céréales et produits céréaliers"]):
        ws.append(row)
    ws.append(["01_001", "Rice, white, boiled", "Riz, blanc, bouilli", "Oryza sativa", "x", 1, 553, 130, 68.5,
               2.6, "[0.3]", 28.1, "tr", 0.2])
    ws.append(["04_007", "Cassava, tuber, raw", "Manioc, tubercule, cru", "", "", 0.8, 670, 158, 59.7, 1.1,
               0.3, 36.5, 1.8, 0.6])
    path = tmp_path / "WAFCT_2019.xlsx"
    wb.save(path)
    return path


def test_find_header_uses_the_english_header_row():
    index, cols = wafct.find_header([tuple(HEADER_EN), tuple(HEADER_FR), tuple(TAGS)])
    assert index == 0
    assert cols["code"] == 0 and cols["name_en"] == 1 and cols["name_fr"] == 2
    assert cols["energy_kcal"] == 7  # not the kJ column
    assert (cols["water_g"], cols["protein_g"], cols["fat_g"], cols["carbohydrate_g"], cols["fibre_g"]) == (8, 9, 10, 11, 12)


def test_load_table_skips_title_and_tag_rows(workbook):
    sheet, records = wafct.load_table(workbook)
    assert sheet == wafct.MAIN_SHEET
    assert [r["code"] for r in records] == ["01_001", "04_007"]
    assert records[0]["energy_kcal"] == 130 and records[0]["fat_g"] == "[0.3]"


@pytest.mark.parametrize("raw, value", [(130, 130.0), ("[0.3]", 0.3), ("tr", 0.0), ("2,5", 2.5), (None, None), ("-", None)])
def test_to_number(raw, value):
    assert wafct.to_number(raw) == value


def test_search_matches_english_and_french_names(workbook):
    text = wafct.search(["manioc", "rice"], workbook)
    assert "04_007 | Cassava, tuber, raw" in text
    assert "01_001 | Rice, white, boiled" in text


def test_find_excel_urls_prefers_wafct():
    html = '<a href="/fileadmin/user_upload/faoweb/2020/WAFCT_2019.xlsx">x</a><a href="other.xls">y</a>'
    assert wafct.find_excel_urls(html, "https://www.fao.org/infoods/") == [
        "https://www.fao.org/fileadmin/user_upload/faoweb/2020/WAFCT_2019.xlsx"]


def test_extract_rows_flags_bracketed_values(workbook):
    rows = wafct.extract_rows(["01_001", "04_007"], workbook)
    assert rows[0]["code"] == "01_001" and rows[0]["name_fr"] == "Riz, blanc, bouilli"
    assert rows[0]["fat_g"] == "0.3" and rows[0]["fibre_g"] == "0"
    assert rows[0]["estimated"] == "fat_g"
    assert rows[1]["estimated"] == ""
    text = wafct.rows_to_csv(rows)
    assert text.splitlines()[0] == "code,name_en,name_fr,energy_kcal,water_g,protein_g,fat_g,carbohydrate_g,fibre_g,estimated"


def test_extract_rows_rejects_unknown_codes(workbook):
    with pytest.raises(KeyError, match="99_999"):
        wafct.extract_rows(["99_999"], workbook)
