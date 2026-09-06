from __future__ import annotations

from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from recode_icd import lexicons, merge, merge_external, propagation
from recode_icd import policy as policy_mod
from recode_icd.exporters import flat_csv
from recode_icd.loaders import atih, ofs, owl
from recode_icd.notations import charge_notations
from recode_icd.recommendations import build as guide_mco
from recode_icd.relations import dagger_asterisk, sibling_exclusions
from recode_icd.reports import csv_stats

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
    atih_path: Annotated[
        Path,
        typer.Option(
            "--atih",
            dir_okay=False,
            help="atih_codes.parquet (`build atih`) : les codes codables absents de l'ANS "
            "(hors chapitre XX) sont injectés dans le nested set (D3). Absent → pas d'injection.",
        ),
    ] = Path("referentials/processed/atih_codes.parquet"),
    reports_dir: Annotated[
        Path,
        typer.Option("--reports-dir", file_okay=False),
    ] = Path("reports"),
) -> None:
    """Construire owl_codes.parquet et owl_dagger_asterisk.parquet depuis le RDF ANS."""
    if not atih_path.is_file():
        typer.echo(
            f"Avertissement : {atih_path} introuvable — aucun code ATIH injecté "
            f"(lancer `recode-icd build atih`).",
            err=True,
        )
    codes_path, pairs_path = owl.to_parquet(
        rdf_path, output_dir, atih_path if atih_path.is_file() else None, reports_dir
    )
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


@build_app.command("atih")
def build_atih(
    kit_path: Annotated[
        Path,
        typer.Option(
            "--kit",
            "-k",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Kit de nomenclature ATIH (LIBCIM10MULTI.TXT).",
        ),
    ] = Path("data/CIM_ATIH_2025/LIBCIM10MULTI.TXT"),
    millesime: Annotated[
        str,
        typer.Option("--millesime", help="Millésime du kit (il ne le porte pas lui-même)."),
    ] = atih.MILLESIME_DEFAUT,
    notations_path: Annotated[
        Path,
        typer.Option("--notations", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/curation/notations_codes.yaml"),
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", file_okay=False),
    ] = Path("referentials/processed"),
    reports_dir: Annotated[
        Path,
        typer.Option("--reports-dir", file_okay=False),
    ] = Path("reports"),
) -> None:
    """Construire atih_codes.parquet depuis le kit de nomenclature ATIH.

    Statut MCO de chaque code (type 0-4, codes supprimés) et règles
    positionnelles dérivées par construction ; écriture du maître via la
    table de notation unique. Rapport : reports/atih_kit_summary.csv.
    """
    paths = atih.to_parquet(kit_path, output_dir, reports_dir, notations_path, millesime)
    for p in paths.values():
        typer.echo(f"Écrit : {p}")


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
    atih_path: Annotated[
        Path,
        typer.Option(
            "--atih",
            dir_okay=False,
            help="atih_codes.parquet (`build atih`) : statut MCO joint à merged. "
            "S'il est absent, les colonnes restent nulles et un avertissement est émis.",
        ),
    ] = Path("referentials/processed/atih_codes.parquet"),
) -> None:
    """Fusionner owl_codes + ofs_codes selon la politique CLAUDE.md."""
    if not atih_path.is_file():
        typer.echo(
            f"Avertissement : {atih_path} introuvable — statut MCO non joint "
            f"(lancer `recode-icd build atih`).",
            err=True,
        )
    paths = merge.to_parquet_and_reports(
        owl_path, ofs_path, output_dir, reports_dir, atih_path if atih_path.is_file() else None
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


@build_app.command("dagger-asterisk")
def build_dagger_asterisk(
    ofs_dir: Annotated[
        Path,
        typer.Option(
            "--ofs-dir",
            "-d",
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            help="Répertoire OFS (MASTER.txt, DAGSTAR.txt, LIBELLE.txt).",
        ),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            file_okay=False,
            help="Répertoire pour dagger_asterisk.parquet + .csv.",
        ),
    ] = Path("referentials/processed"),
    summary_report: Annotated[
        Path,
        typer.Option(
            "--summary-report",
            dir_okay=False,
            help="Rapport synthèse de la table enrichie.",
        ),
    ] = Path("reports/dagger_asterisk_summary.csv"),
    curation_csv: Annotated[
        Path | None,
        typer.Option(
            "--curation-csv",
            dir_okay=False,
            help=(
                "CSV de curation (optionnel). Si fourni, applique "
                "redundancy_level=subordinate aux paires curées."
            ),
        ),
    ] = Path("referentials/curation/dagger_curation.csv"),
    curation_report: Annotated[
        Path,
        typer.Option(
            "--curation-report",
            dir_okay=False,
            help="Rapport d'application de la curation.",
        ),
    ] = Path("reports/curation_applied.csv"),
) -> None:
    """Construire la table DAGSTAR enrichie + appliquer la curation."""
    effective_curation = curation_csv if (curation_csv and curation_csv.is_file()) else None
    if curation_csv and not effective_curation:
        typer.echo(
            f"⚠ Curation CSV introuvable ({curation_csv}) — build sans curation.",
            err=True,
        )
    parquet_path, csv_path, report_path = dagger_asterisk.to_parquet_and_csv_and_report(
        ofs_dir=ofs_dir,
        processed_dir=output_dir,
        report_path=summary_report,
        curation_path=effective_curation,
        curation_report_path=curation_report if effective_curation else None,
    )
    typer.echo(f"Écrit : {parquet_path}")
    typer.echo(f"Écrit : {csv_path}")
    typer.echo(f"Écrit : {report_path}")
    if effective_curation:
        typer.echo(f"Écrit : {curation_report}")


@build_app.command("external")
def build_external(
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
    orphanet_xml: Annotated[
        Path,
        typer.Option(
            "--orphanet-xml",
            exists=True,
            dir_okay=False,
            readable=True,
            help="XML ORPHA_ICD10_mapping_fr_2025.xml.",
        ),
    ] = Path("data/Orphanet_Nomenclature_Pack_FR_2025/ORPHA_ICD10_mapping_fr_2025.xml"),
    hector_xlsx: Annotated[
        Path,
        typer.Option(
            "--hector-xlsx",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Classeur HECTOR (Index CIM-10 vol3 + thésaurus AP-HP).",
        ),
    ] = Path("data/CIM_APHP_2019/Dictionnaire_Hector_MAJ062019.xlsx"),
    cepidc_csv: Annotated[
        Path | None,
        typer.Option(
            "--cepidc-csv",
            dir_okay=False,
            help=(
                "CSV CepiDc_Dictionnaire2015.csv (optionnel). Si fourni "
                "et existant, CepiDc 2015 est ajouté aux sources externes."
            ),
        ),
    ] = Path("data/CIM_CEPIDC_2015/CepiDc_Dictionnaire2015.csv"),
    output_path: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            dir_okay=False,
            help="Parquet `external_to_add` à consommer par `build flat-csv`.",
        ),
    ] = Path("referentials/processed/external_to_add.parquet"),
    reports_dir: Annotated[
        Path,
        typer.Option(
            "--reports-dir",
            file_okay=False,
            help="Répertoire des 3 rapports external_*.csv.",
        ),
    ] = Path("reports"),
) -> None:
    """Charger ORPHANET + Index CIM-10 + AP-HP (+ CepiDc 2015 si
    `--cepidc-csv` fourni), dédupliquer contre OFS/ANS et inter-externes,
    produire le Parquet `external_to_add` + rapports."""
    effective_cepidc = cepidc_csv if (cepidc_csv and cepidc_csv.is_file()) else None
    if cepidc_csv and not effective_cepidc:
        typer.echo(
            f"⚠ CepiDc CSV introuvable ({cepidc_csv}) — build sans CepiDc.",
            err=True,
        )
    paths = merge_external.to_parquet_and_reports(
        merged_path=merged_path,
        propagated_path=propagated_path,
        siblings_path=siblings_path,
        owl_path=owl_path,
        ofs_path=ofs_path,
        orphanet_xml=orphanet_xml,
        hector_xlsx=hector_xlsx,
        output_path=output_path,
        reports_dir=reports_dir,
        cepidc_csv=effective_cepidc,
    )
    for label, path in paths.items():
        typer.echo(f"Écrit ({label}) : {path}")


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
    dagger_asterisk_path: Annotated[
        Path,
        typer.Option("--dagger-asterisk", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/processed/dagger_asterisk.parquet"),
    output_path: Annotated[
        Path,
        typer.Option("--output", "-o", dir_okay=False),
    ] = Path("referentials/processed/inclusions_exclusions_synonymes.csv"),
    curation_report: Annotated[
        Path,
        typer.Option(
            "--curation-report",
            dir_okay=False,
            help="Rapport curation_applied.csv enrichi avec les stats du CSV final.",
        ),
    ] = Path("reports/curation_applied.csv"),
    external_path: Annotated[
        Path | None,
        typer.Option(
            "--external",
            dir_okay=False,
            help=(
                "Parquet `external_to_add` produit par `build external`. "
                "Si fourni et existant, les entrées sont intégrées au CSV final."
            ),
        ),
    ] = Path("referentials/processed/external_to_add.parquet"),
) -> None:
    """Construire le CSV maître à 9 colonnes (inclusions / exclusions / synonymes + dague/astérisque)."""
    effective_external = external_path if (external_path and external_path.is_file()) else None
    if external_path and not effective_external:
        typer.echo(
            f"⚠ External Parquet introuvable ({external_path}) — build sans externes.",
            err=True,
        )
    path = flat_csv.to_csv(
        merged_path,
        propagated_path,
        siblings_path,
        owl_path,
        ofs_path,
        dagger_asterisk_path,
        output_path,
        curation_report_path=curation_report,
        external_path=effective_external,
    )
    typer.echo(f"Écrit : {path}")


@build_app.command("stats")
def build_stats(
    csv_path: Annotated[
        Path,
        typer.Option("--csv", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/processed/inclusions_exclusions_synonymes.csv"),
    output_path: Annotated[
        Path,
        typer.Option("--output", "-o", dir_okay=False),
    ] = Path("reports/csv_stats.md"),
) -> None:
    """Générer reports/csv_stats.md (statistiques déterministes du CSV maître)."""
    path = csv_stats.generate_csv_stats(csv_path, output_path)
    typer.echo(f"Écrit : {path}")


@build_app.command("lexicons")
def build_lexicons(
    csv_path: Annotated[
        Path,
        typer.Option("--csv", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/processed/inclusions_exclusions_synonymes.csv"),
    policy_path: Annotated[
        Path,
        typer.Option("--policy", exists=True, dir_okay=False, readable=True),
    ] = policy_mod.DEFAULT_POLICY_PATH,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", file_okay=False),
    ] = Path("referentials/processed"),
) -> None:
    """Construire les trois lexiques (rections, casse, juxtaposition).

    Trois périmètres DIFFÉRENTS, à ne jamais fusionner — cf. le pitfall
    en tête de `recode_icd.lexicons`.
    """
    csv = pl.read_csv(csv_path, infer_schema_length=200_000)
    paths = lexicons.to_parquet(csv, policy_mod.load_policy(policy_path), output_dir)
    for label, path in paths.items():
        typer.echo(f"Écrit ({label}) : {path}")


@build_app.command("guide-mco")
def build_guide_mco(
    curation_dir: Annotated[
        Path,
        typer.Option("--curation-dir", exists=True, file_okay=False, readable=True),
    ] = Path("data/guide_mco"),
    merged_path: Annotated[
        Path,
        typer.Option("--merged", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/processed/merged_codes.parquet"),
    csv_path: Annotated[
        Path,
        typer.Option("--csv", dir_okay=False, readable=True),
    ] = Path("referentials/processed/inclusions_exclusions_synonymes.csv"),
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", file_okay=False),
    ] = Path("referentials/processed"),
    reports_dir: Annotated[
        Path,
        typer.Option("--reports-dir", file_okay=False),
    ] = Path("reports"),
    notations_path: Annotated[
        Path,
        typer.Option("--notations", exists=True, dir_okay=False, readable=True),
    ] = Path("referentials/curation/notations_codes.yaml"),
) -> None:
    """Construire la base des recommandations du guide méthodologique MCO.

    Part EXCLUSIVEMENT des tables curées de `--curation-dir`, validées
    humainement ligne à ligne. L'extraction LLM ne rentre jamais dans le
    pipeline : les fichiers de `data/guide_mco/extraction/` sont une
    trace de curation, pas une entrée.

    `--notations` : table de correspondance notation du guide ↔ encodage
    du référentiel (catégories à encodage inversé, O04). Les tables
    curées portent la notation du guide ; la résolution traduit.
    """
    recs_curees, codes_cures = guide_mco.charge_tables_curees(curation_dir)
    merged = pl.read_parquet(merged_path)
    notations = charge_notations(notations_path)

    # Le CSV maître n'est lu que pour le rapport de recouvrement — une
    # heuristique de repérage, jamais un dédoublonnage. Son absence ne
    # bloque pas le build.
    flat: pl.DataFrame | None = None
    if csv_path.exists():
        flat = pl.read_csv(csv_path, infer_schema_length=200_000)
    else:
        typer.echo(
            f"Avertissement : {csv_path} introuvable — rapport de recouvrement non produit.",
            err=True,
        )

    recs, resolus, rapport = guide_mco.construit(
        recs_curees, codes_cures, merged, flat, notations=notations
    )

    for label, chemin in guide_mco.ecrit_parquets(recs, resolus, output_dir).items():
        typer.echo(f"Écrit ({label}) : {chemin}")
    guide_mco.ecrit_rapport(rapport, reports_dir)
    typer.echo(f"Rapport de build : {reports_dir}/guide_mco_*.csv")

    stats = rapport.statistiques
    typer.echo(
        f"{stats['recommandations']} recommandations, "
        f"{stats['associations_curees']} associations curées → "
        f"{stats['couples_rec_code']} couples (rec, code) sur "
        f"{stats['codes_touches']} codes."
    )
    if rapport.expressions_traduites:
        typer.echo(
            f"{len(rapport.expressions_traduites)} expression(s) traduite(s) par la table "
            f"de notations — voir guide_mco_expressions_traduites.csv."
        )
    if rapport.recommandations_sans_code:
        typer.echo(
            f"{len(rapport.recommandations_sans_code)} recommandation(s) sans code résolu : "
            f"{', '.join(rapport.recommandations_sans_code)}"
        )
    if rapport.a_des_erreurs:
        typer.echo(
            f"{len(rapport.expressions_non_parsables)} expression(s) non parsable(s), "
            f"{len(rapport.expressions_non_resolues)} non résolue(s) — voir le rapport.",
            err=True,
        )
