"""Fixtures partagées pour les tests de régression Phase 3.

Charge en mémoire le CSV final et le rapport orphan une seule fois
par module pour éviter de re-lire les ~215 000 lignes du CSV dans
chaque test.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

_PROCESSED = Path(__file__).resolve().parents[2] / "referentials" / "processed"
_REPORTS = Path(__file__).resolve().parents[2] / "reports"


@pytest.fixture(scope="module")
def csv_final_df() -> pl.DataFrame:
    """CSV maître post-Phase 2 (9 colonnes, ~215 000 lignes)."""
    path = _PROCESSED / "inclusions_exclusions_synonymes.csv"
    if not path.is_file():
        pytest.skip(
            f"CSV final absent : {path}. "
            "Lancer `uv run recode-icd build flat-csv` d'abord."
        )
    return pl.read_csv(path, infer_schema_length=200_000)


@pytest.fixture(scope="module")
def orphan_report_df() -> pl.DataFrame:
    """Rapport `reports/external_orphan_codes.csv` (post-Phase 2.5b)."""
    path = _REPORTS / "external_orphan_codes.csv"
    if not path.is_file():
        pytest.skip(
            f"Rapport orphan absent : {path}. "
            "Lancer `uv run recode-icd build external` d'abord."
        )
    return pl.read_csv(path)


@pytest.fixture(scope="module")
def overlaps_report_df() -> pl.DataFrame:
    """Rapport `reports/external_overlaps.csv` (utile pour valider que
    certaines entrées AP-HP ont été absorbées au lieu d'être ajoutées)."""
    path = _REPORTS / "external_overlaps.csv"
    if not path.is_file():
        pytest.skip(f"Rapport overlaps absent : {path}.")
    return pl.read_csv(path)
