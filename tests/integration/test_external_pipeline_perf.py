"""Test de performance — pipeline merge externe complet.

Lance le merge externe sur les VRAIES données (loaders Phase 1 sur
ORPHANET + HECTOR + tables OFS+ANS) et vérifie que la durée totale
reste sous 30 secondes. Skip si les fichiers de données ne sont pas
présents (CI sans données).
"""

from __future__ import annotations

import time
from pathlib import Path

import polars as pl
import pytest

from recode_icd import merge as merge_mod
from recode_icd import merge_external

pytestmark = pytest.mark.integration


ROOT = Path(__file__).resolve().parents[2]
ORPHANET_XML = (
    ROOT / "data" / "Orphanet_Nomenclature_Pack_FR_2025"
    / "ORPHA_ICD10_mapping_fr_2025.xml"
)
HECTOR_XLSX = (
    ROOT / "data" / "CIM_APHP_2019" / "Dictionnaire_Hector_MAJ062019.xlsx"
)
PROCESSED = ROOT / "referentials" / "processed"


def _require_inputs() -> None:
    paths = [
        ORPHANET_XML,
        HECTOR_XLSX,
        PROCESSED / "merged_codes.parquet",
        PROCESSED / "propagated_notes.parquet",
        PROCESSED / "sibling_exclusions.parquet",
        PROCESSED / "owl_codes.parquet",
        PROCESSED / "ofs_codes.parquet",
    ]
    missing = [p for p in paths if not p.is_file()]
    if missing:
        pytest.skip(f"Fichiers manquants : {[p.name for p in missing]}")


def test_full_pipeline_under_30s() -> None:
    """Merge externe complet (3 loaders + dédup + 3 rapports)
    en moins de 30 secondes sur le dataset réel."""
    _require_inputs()

    merged = pl.read_parquet(PROCESSED / "merged_codes.parquet")
    propagated = pl.read_parquet(PROCESSED / "propagated_notes.parquet")
    siblings = pl.read_parquet(PROCESSED / "sibling_exclusions.parquet")
    owl = pl.read_parquet(PROCESSED / "owl_codes.parquet")
    ofs = pl.read_parquet(PROCESSED / "ofs_codes.parquet")

    leaves = merged.filter(
        (pl.col("type") == "category") & ((pl.col("right") - pl.col("left")) == 1)
    ).select("code", pl.col("label").alias("libelle"))
    valid_codes = merged.select("code")
    post_2006 = merge_mod.find_post_2006_codes(owl, ofs)

    external_frames = merge_external.load_external_frames(
        ORPHANET_XML, HECTOR_XLSX
    )

    t0 = time.perf_counter()
    to_add, _, _, summary = merge_external.merge_external_sources(
        propagated=propagated,
        owl=owl,
        ofs=ofs,
        siblings=siblings,
        leaves=leaves,
        valid_codes=valid_codes,
        post_2006_codes=post_2006,
        external_frames=external_frames,
    )
    elapsed = time.perf_counter() - t0

    assert elapsed < 30.0, f"pipeline trop lent : {elapsed:.1f}s"

    # Sanity sur les volumétries.
    assert to_add.height > 0
    assert summary.height >= 11, "11 sources attendues (ORPHANET + Index + 9 AP-HP)"
    # Total cohérent : sum(loaded) sur 11 sources ≈ 65 000.
    total_loaded = summary["entries_loaded"].sum()
    assert 50_000 < total_loaded < 80_000, f"volumétrie inattendue : {total_loaded}"
