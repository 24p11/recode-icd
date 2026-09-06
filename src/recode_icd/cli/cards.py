from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from recode_icd import policy as policy_module
from recode_icd.cards import (
    DEFAULT_SEED,
    build_cards_library,
    build_categories_library,
)

cards_app = typer.Typer(help="Bibliothèque de fiches CIM-10.")


def dossier_par_profil(profil: str) -> Path:
    """`outputs/cards_library` pour le profil de génération, `_<profil>` sinon."""
    if profil == policy_module.PROFIL_DEFAUT:
        return Path("outputs/cards_library")
    return Path(f"outputs/cards_library_{profil}")


@cards_app.command("build")
def build_library_cmd(
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            help="Dossier racine de sortie (sous-dossiers <chapitre>/<code>.md). "
            "Défaut : outputs/cards_library pour `generation`, outputs/cards_library_<profil> sinon.",
        ),
    ] = None,
    profil: Annotated[
        str,
        typer.Option(
            "--profil",
            help="Profil de bibliothèque (chapter_policy.yaml → profils) : "
            "`generation` = codables MCO seulement, `controle` = tous les codes.",
        ),
    ] = policy_module.PROFIL_DEFAUT,
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
    policy_path: Annotated[
        Path,
        typer.Option(
            "--policy",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Politique de composition (R1/R2/R3).",
        ),
    ] = policy_module.DEFAULT_POLICY_PATH,
    lexicons_dir: Annotated[
        Path,
        typer.Option(
            "--lexicons-dir",
            file_okay=False,
            help="Répertoire des trois lexiques (`build lexicons`).",
        ),
    ] = Path("referentials/processed"),
) -> None:
    """Génère la bibliothèque complète des fiches CIM-10 sous output-dir."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    summary = build_cards_library(
        output_dir=output_dir if output_dir is not None else dossier_par_profil(profil),
        chapter_filter=chapter,
        limit=limit,
        seed=seed,
        policy_path=policy_path,
        lexicons_dir=lexicons_dir,
        profil=profil,
    )

    typer.echo("")
    typer.echo("=" * 60)
    typer.echo(f"Bibliothèque générée sous : {summary.output_dir}")
    typer.echo(f"Profil                   : {summary.profil}")
    if summary.n_exclus_non_codables:
        typer.echo(f"Codes non codables exclus: {summary.n_exclus_non_codables}")
    typer.echo(f"Codes total              : {summary.n_codes_total}")
    typer.echo(f"Fiches écrites           : {summary.n_written}")
    typer.echo(f"Erreurs                  : {summary.n_errors}")
    typer.echo(f"Fiches avec consignes    : {summary.n_consignes}")
    if summary.consignes_par_chapitre:
        repartition = ", ".join(f"{chap}: {n}" for chap, n in summary.consignes_par_chapitre)
        typer.echo(f"  par chapitre           : {repartition}")
    typer.echo(f"Durée                    : {summary.elapsed_seconds:.1f}s")
    typer.echo(f"Index                    : {summary.index_path}")
    for avertissement in summary.avertissements:
        typer.echo(f"⚠ {avertissement}")
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
    policy_path: Annotated[
        Path,
        typer.Option(
            "--policy",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Politique de composition (R1/R2/R3).",
        ),
    ] = policy_module.DEFAULT_POLICY_PATH,
    lexicons_dir: Annotated[
        Path,
        typer.Option(
            "--lexicons-dir",
            file_okay=False,
            help="Répertoire des trois lexiques (`build lexicons`).",
        ),
    ] = Path("referentials/processed"),
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
        policy_path=policy_path,
        lexicons_dir=lexicons_dir,
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
