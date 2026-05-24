"""Convertit `2026-05-17_divergences_textuelles.py` → `.ipynb` cellule par cellule.

Usage :
    uv run python scripts/explore/_convert_to_ipynb.py
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

SRC = Path(__file__).parent / "2026-05-17_divergences_textuelles.py"
DST = SRC.with_suffix(".ipynb")


def split_cells(text: str) -> list[tuple[str, str]]:
    """Découpe le source `.py` en (titre_cellule, code).

    Convention : chaque marqueur `# %%` démarre une nouvelle cellule.
    Le titre suit le marqueur sur la même ligne (optionnel).
    Le préambule avant le 1er `# %%` est concaténé à la 1ère cellule.
    """
    lines = text.splitlines()
    cells: list[tuple[str, list[str]]] = []
    current_title = "Preamble"
    current_body: list[str] = []

    for line in lines:
        if line.startswith("# %%"):
            cells.append((current_title, current_body))
            current_title = line.removeprefix("# %%").strip() or "(unnamed)"
            current_body = []
        else:
            current_body.append(line)
    cells.append((current_title, current_body))

    # On garde toutes les cellules nommées (même vides — utiles pour
    # les "(vide) — à remplir"). Seul le preamble pur est filtré.
    out: list[tuple[str, str]] = []
    for title, body in cells:
        code = "\n".join(body).strip("\n")
        if title == "Preamble" and not code:
            continue
        out.append((title, code))
    return out


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    cells = split_cells(text)

    nb = nbf.v4.new_notebook()
    nb_cells: list = []

    # Header markdown
    nb_cells.append(
        nbf.v4.new_markdown_cell(
            "# Exploration interactive — divergences textuelles ANS ↔ OFS\n\n"
            "Source canonique : `reports/note_merges.csv`.\n\n"
            "Version notebook du fichier "
            "`scripts/explore/2026-05-17_divergences_textuelles.py`. "
            "Régénérée via `_convert_to_ipynb.py`. **Ne pas éditer "
            "directement le notebook** — modifier le `.py` et re-convertir."
        )
    )

    for title, code in cells:
        if title in {"Preamble", "(unnamed)"}:
            # Préambule docstring : on le saute (déjà capté en markdown ci-dessus)
            if "ruff: noqa" in code or code.startswith('"""'):
                continue
        nb_cells.append(nbf.v4.new_markdown_cell(f"## {title}"))
        nb_cells.append(nbf.v4.new_code_cell(code))

    nb["cells"] = nb_cells
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3 (.venv)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.13"},
    }
    nbf.write(nb, str(DST))
    print(f"Wrote {DST} ({len(nb_cells)} cells)")


if __name__ == "__main__":
    main()
