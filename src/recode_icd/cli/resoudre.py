"""CLI `recode-icd resoudre` : toute écriture d'un code → fiche ou raison de l'absence."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from recode_icd.couverture import charge_contexte, journalise, resoudre_code


# Commande simple, pas un sous-groupe Typer : un groupe n'intercale pas
# les options après les arguments (`resoudre A18.1 --json` avalait
# `--json` comme un code).
def resoudre(
    codes: Annotated[
        list[str], typer.Argument(help="Codes, sous toute écriture (O0490, O04.90, O04.-0.9).")
    ],
    index_path: Annotated[
        Path | None,
        typer.Option("--index", dir_okay=False, help="_index.csv de la bibliothèque visée."),
    ] = None,
    processed_dir: Annotated[
        Path | None,
        typer.Option("--processed-dir", file_okay=False),
    ] = None,
    journal: Annotated[
        Path | None,
        typer.Option("--journal", dir_okay=False, help="JSONL où ajouter les réponses négatives."),
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Une ligne JSON par code.")] = False,
) -> None:
    """Répond, pour chaque code, la fiche ou la raison motivée de son absence."""
    ctx = charge_contexte(processed_dir=processed_dir, index_path=index_path)
    negatifs = 0
    for saisie in codes:
        resolution = resoudre_code(saisie, ctx)
        if journal is not None:
            journalise(resolution, journal)
        if resolution.negative:
            negatifs += 1
        if as_json:
            typer.echo(resolution.to_json())
            continue
        entete = f"{saisie} → {resolution.code or '?'}"
        if resolution.code_atih and resolution.code_atih != resolution.code:
            entete += f" (ATIH {resolution.code_atih})"
        typer.echo(f"{entete} : {resolution.statut}")
        if resolution.libelle:
            typer.echo(f"  {resolution.libelle}")
        if resolution.fiche:
            typer.echo(f"  fiche : {ctx.bibliotheque}/{resolution.fiche}")
        typer.echo(f"  {resolution.raison}")
        if resolution.codes_avec_fiche:
            apercu = ", ".join(resolution.codes_avec_fiche[:12])
            suite = " …" if len(resolution.codes_avec_fiche) > 12 else ""
            typer.echo(f"  avec fiche : {apercu}{suite}")
    if negatifs:
        raise typer.Exit(code=1)
