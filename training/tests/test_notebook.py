import ast

import nbformat

import build_notebook


def test_committed_notebook_is_up_to_date():
    committed = nbformat.read(build_notebook.OUT, as_version=4)
    assert committed == build_notebook.build(), "run: python training/build_notebook.py"


def test_code_cells_are_valid_python():
    for cell in build_notebook.build().cells:
        if cell.cell_type != "code":
            continue
        # shell (!) and magic (%) lines are IPython syntax: replace them, keeping the indentation
        lines = [l[: len(l) - len(l.lstrip())] + "pass" if l.strip().startswith(("!", "%")) else l
                 for l in cell.source.splitlines()]
        ast.parse("\n".join(lines))


def test_no_image_is_saved_outside_the_temporary_work_dir():
    setup = build_notebook.build().cells[2].source
    assert 'WORK = "/tmp/afc"' in setup
    save = build_notebook.build().cells[-1].source
    assert "afc_model_outputs.zip" in save and "dataset" not in save
