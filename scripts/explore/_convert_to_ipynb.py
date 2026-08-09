"""Convertit un script d'exploration `.py` en notebook `.ipynb`.

Le `.py` est la **source de vérité** : il se lit en diff, se lint et
s'exécute directement (`uv run python <fichier>.py`). Le `.ipynb` en est
un rendu régénérable — ne pas l'éditer à la main.

Conventions de découpage (format « percent », compatible jupytext) :

- `# %% <titre>` démarre une **cellule de code**. Le titre, optionnel,
  est rendu au-dessus en cellule markdown (`## <titre>`).
- `# %% [markdown]` démarre une **cellule markdown** : son corps est
  fait de lignes commentées, dont le `# ` initial est retiré. C'est ce
  qui permet d'écrire un notebook didactique tout en gardant un `.py`
  exécutable et lintable.

Le docstring de module devient l'en-tête du notebook.

Usage :
    uv run --extra notebook python scripts/explore/_convert_to_ipynb.py <fichier.py>

Sans argument, convertit `2026-05-17_divergences_textuelles.py` pour
rester compatible avec l'usage historique.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

import nbformat as nbf

DEFAUT = Path(__file__).parent / "2026-05-17_divergences_textuelles.py"


MARQUEUR_MARKDOWN = "[markdown]"


def _demarque(body: list[str]) -> str:
    """Retire le `# ` de tête des lignes d'une cellule markdown."""
    out = []
    for ligne in body:
        depouillee = ligne.lstrip()
        if depouillee.startswith("#"):
            out.append(depouillee[1:].removeprefix(" "))
        elif not depouillee:
            out.append("")
        else:
            # Ligne non commentée dans une cellule markdown : on la
            # garde telle quelle plutôt que de la perdre silencieusement.
            out.append(ligne)
    return "\n".join(out).strip("\n")


def split_cells(text: str) -> list[tuple[str, str]]:
    """Découpe le source `.py` en (titre_cellule, contenu).

    Le titre vaut `MARQUEUR_MARKDOWN` pour une cellule markdown.
    Le préambule avant le 1er `# %%` (imports, docstring) est conservé
    comme première cellule de code : il porte le chargement du contexte.
    """
    lines = text.splitlines()
    cells: list[tuple[str, list[str]]] = []
    current_title = "Preamble"
    current_body: list[str] = []

    for line in lines:
        if line.startswith("# %%"):
            cells.append((current_title, current_body))
            current_title = line.removeprefix("# %%").strip() or "(sans titre)"
            current_body = []
        else:
            current_body.append(line)
    cells.append((current_title, current_body))

    out: list[tuple[str, str]] = []
    for title, body in cells:
        contenu = _demarque(body) if title == MARQUEUR_MARKDOWN else "\n".join(body).strip("\n")
        if title == "Preamble" and not contenu:
            continue
        out.append((title, contenu))
    return out


def _entete(src: Path, text: str) -> str:
    """En-tête markdown : docstring de module + rappel de régénération."""
    docstring = ast.get_docstring(ast.parse(text)) or src.stem
    return (
        f"{docstring}\n\n---\n\n"
        f"*Notebook généré depuis `{src.as_posix()}` via "
        f"`_convert_to_ipynb.py`. **Ne pas éditer directement** — "
        f"modifier le `.py` et reconvertir.*"
    )


def convert(src: Path) -> Path:
    text = src.read_text(encoding="utf-8")
    dst = src.with_suffix(".ipynb")

    nb = nbf.v4.new_notebook()
    nb_cells: list = [nbf.v4.new_markdown_cell(_entete(src, text))]

    for title, contenu in split_cells(text):
        if title == MARQUEUR_MARKDOWN:
            if contenu:
                nb_cells.append(nbf.v4.new_markdown_cell(contenu))
            continue
        if title == "Preamble":
            # Docstring + directives ruff déjà rendus dans l'en-tête ;
            # on ne garde que du code exécutable s'il en reste.
            lignes = [
                ligne
                for ligne in contenu.splitlines()
                if not ligne.startswith("#") and ligne.strip()
            ]
            if not lignes:
                continue
        elif title != "(sans titre)":
            nb_cells.append(nbf.v4.new_markdown_cell(f"### {title}"))
        nb_cells.append(nbf.v4.new_code_cell(contenu))

    nb["cells"] = nb_cells
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3 (.venv)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.13"},
    }
    nbf.write(nb, str(dst))
    print(f"Écrit {dst} ({len(nb_cells)} cellules)")
    return dst


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=DEFAUT,
        help="script .py à convertir (défaut : le notebook historique)",
    )
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(f"introuvable : {args.source}")
    convert(args.source)


if __name__ == "__main__":
    main()
