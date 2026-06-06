"""Wrapper standalone : génère la bibliothèque complète des fiches CIM-10.

Équivalent à `uv run recode-icd cards build` (sous-commande typer
officielle). Conservé pour faciliter l'invocation depuis la racine du
repo sans passer par le point d'entrée recode-icd.

Usage :
    uv run python scripts/build_cards_library.py [--output-dir PATH]
                                                  [--chapter ROMAN]
                                                  [--limit N]
                                                  [--seed S]
"""

from __future__ import annotations

import typer

from recode_icd.cli.cards import build_library_cmd

if __name__ == "__main__":
    typer.run(build_library_cmd)
