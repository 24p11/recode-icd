from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from recode_icd import merge, propagation
from recode_icd.exporters import flat_csv
from recode_icd.loaders import ofs, owl
from recode_icd.relations import sibling_exclusions

build_app = typer.Typer(help="Construire les Parquet de référence.")


@build_app.command("owl")
def build_owl(
    rdf_path: Annotated[
        Path,
        typer.Option(
            "--rdf-path",
            "-r",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Chemin du RDF ANS (terminologie-cim-10-YYYY-MM-DD.rdf).",
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            help="Répertoire de sortie pour les Parquet.",
        ),
    ] = Path("referentials/processed"),
) -> None:
    """Construire owl_codes.parquet et owl_dagger_asterisk.parquet depuis le RDF ANS."""
    codes_path, pairs_path = owl.to_parquet(rdf_path, output_dir)
    typer.echo(f"Écrit : {codes_path}")
    typer.echo(f"Écrit : {pairs_path}")


@build_app.command("ofs")
def build_ofs(
    ofs_dir: Annotated[
        Path,
        typer.Option(
            "--ofs-dir",
            "-d",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Répertoire OFS (contient MASTER.txt, LIBELLE.txt, etc.).",
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            help="Répertoire de sortie pour les Parquet.",
        ),
    ] = Path("referentials/processed"),
) -> None:
    """Construire ofs_codes.parquet et ofs_dagger_asterisk.parquet depuis OFS suisse 2006."""
    codes_path, pairs_path = ofs.to_parquet(ofs_dir, output_dir)
    typer.echo(f"Écrit : {codes_path}")
    typer.echo(f"Écrit : {pairs_path}")


@build_app.command("merged")
def build_merged(
    owl_path: Annotated[
        Path,
        typer.Option(
            "--owl",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Chemin du Parquet OWL codes.",
        ),
    ] = Path("referentials/processed/owl_codes.parquet"),
    ofs_path: Annotated[
        Path,
        typer.Option(
            "--ofs",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Chemin du Parquet OFS codes.",
        ),
    ] = Path("referentials/processed/ofs_codes.parquet"),
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            help="Répertoire de sortie pour merged_codes.parquet.",
        ),
    ] = Path("referentials/processed"),
    reports_dir: Annotated[
        Path,
        typer.Option(
            "--reports-dir",
            file_okay=False,
            help="Répertoire de sortie pour les rapports de conflits/orphelins.",
        ),
    ] = Path("reports"),
) -> None:
    """Fusionner owl_codes + ofs_codes selon la politique CLAUDE.md."""
    paths = merge.to_parquet_and_reports(
        owl_path, ofs_path, output_dir, reports_dir
    )
    for p in paths.values():
        typer.echo(f"Écrit : {p}")


@build_app.command("propagated")
def build_propagated(
    merged_path: Annotated[
        Path,
        typer.Option(
            "--merged",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Chemin du Parquet merged_codes.",
        ),
    ] = Path("referentials/processed/merged_codes.parquet"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            dir_okay=False,
            help="Chemin de sortie pour propagated_notes.parquet.",
        ),
    ] = Path("referentials/processed/propagated_notes.parquet"),
) -> None:
    """Propager les notes des ancêtres (chapter/block/category) vers tous les codes."""
    path = propagation.to_parquet(merged_path, output_path)
    typer.echo(f"Écrit : {path}")


@build_app.command("siblings")
def build_siblings(
    merged_path: Annotated[
        Path,
        typer.Option(
            "--merged",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Chemin du Parquet merged_codes.",
        ),
    ] = Path("referentials/processed/merged_codes.parquet"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            dir_okay=False,
            help="Chemin de sortie pour sibling_exclusions.parquet.",
        ),
    ] = Path("referentials/processed/sibling_exclusions.parquet"),
    report_path: Annotated[
        Path,
        typer.Option(
            "--report",
            dir_okay=False,
            help="Chemin du rapport CSV des .8 codes ignorés (C00-C75).",
        ),
    ] = Path("reports/synthesized_skipped.csv"),
) -> None:
    """Synthétiser les exclusions frères pour les codes XYZ.8."""
    out_path, rep_path = sibling_exclusions.to_parquet_and_report(
        merged_path, output_path, report_path
    )
    typer.echo(f"Écrit : {out_path}")
    typer.echo(f"Écrit : {rep_path}")


@build_app.command("flat-csv")
def build_flat_csv(
    merged_path: Annotated[
        Path,
        typer.Option("--merged", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/processed/merged_codes.parquet"),
    propagated_path: Annotated[
        Path,
        typer.Option("--propagated", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/processed/propagated_notes.parquet"),
    siblings_path: Annotated[
        Path,
        typer.Option("--siblings", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/processed/sibling_exclusions.parquet"),
    owl_path: Annotated[
        Path,
        typer.Option("--owl", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/processed/owl_codes.parquet"),
    ofs_path: Annotated[
        Path,
        typer.Option("--ofs", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/processed/ofs_codes.parquet"),
    output_path: Annotated[
        Path,
        typer.Option("--output", "-o", dir_okay=False),
    ] = Path("referentials/processed/inclusions_exclusions_synonymes.csv"),
) -> None:
    """Construire le CSV maître à 5 colonnes (inclusions / exclusions / synonymes)."""
    path = flat_csv.to_csv(
        merged_path, propagated_path, siblings_path, owl_path, ofs_path, output_path
    )
    typer.echo(f"Écrit : {path}")
