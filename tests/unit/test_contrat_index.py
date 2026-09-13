"""Tests du contrat d'index des bibliothèques (CONTRAT.md).

Décisions verrouillées (chantier du 2026-09-13, pré-arbitré RF) :

1. nom canonique `index.csv`, `_index.csv` déprécié double-écrit un
   cycle — contenus identiques au renommage `filepath → fichier` et à
   la colonne `format_version` près ;
2. noyau garanti `code, fichier, statut_mco, format_version` ;
3. l'index fait foi : un build COMPLET nettoie les fiches hors index
   (résidus pré-profils, 1 709 mesurés le 2026-09-12), un build partiel
   (`--limit`, `--chapter`) ne rase rien ;
4. CONTRAT.md est posé à la racine de chaque bibliothèque et documente
   la sémantique `tronc_composition` et les consommateurs connus.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd import couverture
from recode_icd.cards import (
    _CHEMIN_CONTRAT,
    FORMAT_VERSION,
    _nettoie_residus,
    build_cards_library,
)
from recode_icd.utils.loaders_dev import ExplorationContext, load_exploration_context

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def ctx() -> ExplorationContext:
    c = load_exploration_context(with_external=True)
    if c.flat is None or c.merged is None or c.ans is None:
        pytest.skip("Artefacts pipeline absents.")
    return c


def test_index_canonique_et_copie_depreciee(ctx: ExplorationContext, tmp_path: Path) -> None:
    summary = build_cards_library(ctx=ctx, output_dir=tmp_path, limit=3, progress=False)
    assert summary.index_path == tmp_path / "index.csv"

    # `format_version` est une étiquette opaque, pas un nombre.
    canonique = pl.read_csv(tmp_path / "index.csv", schema_overrides={"format_version": pl.String})
    for colonne in ("code", "fichier", "statut_mco", "format_version"):
        assert colonne in canonique.columns, f"noyau garanti : {colonne} manquante"
    assert canonique["format_version"].unique().to_list() == [FORMAT_VERSION]

    deprecie = pl.read_csv(tmp_path / "_index.csv")
    assert "filepath" in deprecie.columns and "format_version" not in deprecie.columns
    assert deprecie["code"].to_list() == canonique["code"].to_list()
    assert deprecie["filepath"].to_list() == canonique["fichier"].to_list()

    contrat = (tmp_path / "CONTRAT.md").read_text(encoding="utf-8")
    assert "index.csv" in contrat and "format_version" in contrat


def test_nettoyage_residus_epargne_index_et_contrat(tmp_path: Path) -> None:
    (tmp_path / "I").mkdir()
    (tmp_path / "I" / "A00.0.md").write_text("fiche", encoding="utf-8")
    (tmp_path / "I" / "residu.md").write_text("résidu pré-profils", encoding="utf-8")
    (tmp_path / "CONTRAT.md").write_text("contrat", encoding="utf-8")

    n = _nettoie_residus(tmp_path, {"I/A00.0.md"})

    assert n == 1
    assert (tmp_path / "I" / "A00.0.md").exists()
    assert not (tmp_path / "I" / "residu.md").exists()
    assert (tmp_path / "CONTRAT.md").exists(), "le contrat n'est pas un résidu"


def test_build_partiel_ne_nettoie_pas(ctx: ExplorationContext, tmp_path: Path) -> None:
    """`--limit` écrit un index partiel : nettoyer raserait la bibliothèque."""
    residu = tmp_path / "XXII" / "residu.md"
    residu.parent.mkdir(parents=True)
    residu.write_text("fiche d'un ancien build", encoding="utf-8")

    summary = build_cards_library(ctx=ctx, output_dir=tmp_path, limit=2, progress=False)

    assert summary.n_residus_nettoyes == 0
    assert residu.exists(), "un build partiel ne doit jamais supprimer de fiche"


def test_contrat_source_documente_les_decisions() -> None:
    contrat = _CHEMIN_CONTRAT.read_text(encoding="utf-8")
    for attendu in (
        "index.csv",
        "_index.csv",
        "fichier",
        "statut_mco",
        "format_version",
        "tronc_composition",
        "emissible",
        "fictomed",
        "Stream",
        "paquet de livraison",
    ):
        assert attendu in contrat, f"CONTRAT.md ne documente plus « {attendu} »"


def test_resolveur_lit_le_canonique_et_le_deprecie(tmp_path: Path) -> None:
    """`charge_contexte` lit `fichier` (canonique) comme `filepath` (déprécié)."""
    processed = couverture.DEFAULT_PROCESSED_DIR
    if not (processed / "atih_codes.parquet").is_file():
        pytest.skip("atih_codes.parquet absent.")

    canonique = tmp_path / "index.csv"
    canonique.write_text(
        "code,fichier,statut_mco,format_version\nA00.0,I/A00.0.md,codable,1\n", encoding="utf-8"
    )
    ctx = couverture.charge_contexte(index_path=canonique)
    assert ctx.fiches["A00.0"] == "I/A00.0.md"

    legacy = tmp_path / "_index.csv"
    legacy.write_text("code,filepath\nA00.0,I/A00.0.md\n", encoding="utf-8")
    ctx = couverture.charge_contexte(index_path=legacy)
    assert ctx.fiches["A00.0"] == "I/A00.0.md"
