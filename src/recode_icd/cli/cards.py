from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from recode_icd.cards import (
    DEFAULT_SEED,
    build_cards_library,
    build_categories_library,
)

cards_app = typer.Typer(help="Bibliothèque de fiches CIM-10.")


@cards_app.command("build")
def build_library_cmd(
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            help="Dossier racine de sortie (sous-dossiers <chapitre>/<code>.md).",
        ),
    ] = Path("outputs/cards_library"),
    chapter: Annotated[
        str | None,
        typer.Option(
            "--chapter",
            "-c",
            help="Filtrer par chapitre (notation romaine, ex. XIII). Par défaut : tous.",
        ),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            "-n",
            help="Limiter à N codes (utile pour tests). Par défaut : tous.",
        ),
    ] = None,
    seed: Annotated[
        int,
        typer.Option(
            "--seed",
            "-s",
            help="Seed du Random pour l'échantillonnage déterministe.",
        ),
    ] = DEFAULT_SEED,
) -> None:
    """Génère la bibliothèque complète des fiches CIM-10 sous output-dir."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    summary = build_cards_library(
        output_dir=output_dir,
        chapter_filter=chapter,
        limit=limit,
        seed=seed,
    )

    typer.echo("")
    typer.echo("=" * 60)
    typer.echo(f"Bibliothèque générée sous : {summary.output_dir}")
    typer.echo(f"Codes total              : {summary.n_codes_total}")
    typer.echo(f"Fiches écrites           : {summary.n_written}")
    typer.echo(f"Erreurs                  : {summary.n_errors}")
    typer.echo(f"Durée                    : {summary.elapsed_seconds:.1f}s")
    typer.echo(f"Index                    : {summary.index_path}")
    if summary.errors:
        typer.echo("\nPremières erreurs :")
        for code, err in summary.errors[:10]:
            typer.echo(f"  {code} : {err}")


@cards_app.command("build-categories")
def build_categories_cmd(
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            help="Dossier racine de sortie pour les fiches catégories.",
        ),
    ] = Path("outputs/cards_library_categories"),
    chapter: Annotated[
        str | None,
        typer.Option(
            "--chapter",
            "-c",
            help="Filtrer par chapitre romain (ex. XIII). Par défaut : tous.",
        ),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            "-n",
            help="Limiter à N catégories (utile pour tests).",
        ),
    ] = None,
    seed: Annotated[
        int,
        typer.Option("--seed", "-s"),
    ] = DEFAULT_SEED,
) -> None:
    """Génère la bibliothèque de fiches catégories CIM-10 3-car.

    Une fiche est produite par catégorie 3-caractères (A18, M01,
    R51, …), agrégeant les contenus de ses feuilles descendantes
    depuis le CSV maître.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    summary = build_categories_library(
        output_dir=output_dir,
        chapter_filter=chapter,
        limit=limit,
        seed=seed,
    )

    typer.echo("")
    typer.echo("=" * 60)
    typer.echo(f"Bibliothèque catégories sous : {summary.output_dir}")
    typer.echo(f"Catégories total            : {summary.n_codes_total}")
    typer.echo(f"Fiches écrites              : {summary.n_written}")
    typer.echo(f"Erreurs                     : {summary.n_errors}")
    typer.echo(f"Durée                       : {summary.elapsed_seconds:.1f}s")
    typer.echo(f"Index                       : {summary.index_path}")
    if summary.errors:
        typer.echo("\nPremières erreurs :")
        for code, err in summary.errors[:10]:
            typer.echo(f"  {code} : {err}")
