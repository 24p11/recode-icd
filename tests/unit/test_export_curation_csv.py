"""Tests pour scripts/explore/2026-05-21_export_curation_csv.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import polars as pl
import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def mod() -> ModuleType:
    """Charge le script comme module (nom commençant par chiffre → import
    classique impossible)."""
    script_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "explore"
        / "2026-05-21_export_curation_csv.py"
    )
    spec = importlib.util.spec_from_file_location("export_curation_csv", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["export_curation_csv"] = module
    spec.loader.exec_module(module)
    return module


def _make_table(rows: list[dict]) -> pl.DataFrame:
    """Construit un DataFrame ayant le schéma de la table DAGSTAR enrichie
    (au moins les colonnes utilisées par l'export)."""
    return pl.DataFrame(
        {
            "association_id": [i for i, _ in enumerate(rows)],
            "dagger_code": [r.get("dagger_code") for r in rows],
            "dagger_label": [r.get("dagger_label") for r in rows],
            "asterisk_code": [r.get("asterisk_code") for r in rows],
            "asterisk_label": [r.get("asterisk_label") for r in rows],
            "combination_labels": [r.get("combination_labels", []) for r in rows],
            "levels_present": [r.get("levels_present", []) for r in rows],
            "source_lids": [r.get("source_lids", []) for r in rows],
            "redundancy_level": [r.get("redundancy_level", "independent") for r in rows],
        },
        schema_overrides={
            "association_id": pl.Int64,
            "dagger_code": pl.Utf8,
            "dagger_label": pl.Utf8,
            "asterisk_code": pl.Utf8,
            "asterisk_label": pl.Utf8,
            "combination_labels": pl.List(pl.Utf8),
            "levels_present": pl.List(pl.Utf8),
            "source_lids": pl.List(pl.Int64),
            "redundancy_level": pl.Utf8,
        },
    )


def _write_parquet(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _make_table(rows).write_parquet(path)


# --------------------------------------------------------------------------- #
def test_first_export_creates_csv_with_empty_curation_columns(
    mod: ModuleType, tmp_path: Path
) -> None:
    parquet = tmp_path / "in.parquet"
    csv = tmp_path / "out.csv"
    _write_parquet(
        [
            {
                "dagger_code": "A18.1",
                "dagger_label": "Tuberculose génito-urinaire",
                "asterisk_code": "N33.0",
                "asterisk_label": "Cystite tuberculeuse",
                "combination_labels": ["cystite tuberculeuse"],
                "levels_present": ["G", "U"],
            },
            {
                "dagger_code": "A17.8",
                "dagger_label": "Tuberculose du SNC",
                "asterisk_code": "G05.0",
                "asterisk_label": "Encéphalite",
                "combination_labels": ["méningoencéphalite tuberculeuse"],
                "levels_present": ["T", "H"],
            },
        ],
        parquet,
    )
    rc = mod.main(["--table", str(parquet), "--csv", str(csv)])
    assert rc == 0
    assert csv.is_file()

    df = pl.read_csv(csv, infer_schema_length=0)
    assert list(df.columns) == list(mod.EXPORT_COLS)
    # Tri stable par dagger_code
    assert df["dagger_code"].to_list() == ["A17.8", "A18.1"]
    # Défauts de curation appliqués (paires nouvelles)
    assert df["redundancy_level"].to_list() == [
        mod.DEFAULT_REDUNDANCY_LEVEL,
        mod.DEFAULT_REDUNDANCY_LEVEL,
    ]
    assert df["rationale"].to_list() == [mod.DEFAULT_RATIONALE, mod.DEFAULT_RATIONALE]
    assert df["curated_by"].to_list() == [mod.DEFAULT_CURATED_BY, mod.DEFAULT_CURATED_BY]
    assert df["curated_date"].to_list() == [
        mod.DEFAULT_CURATED_DATE,
        mod.DEFAULT_CURATED_DATE,
    ]
    # _orphan tous False
    assert all(v.lower() in {"false", "0"} for v in df["_orphan"].to_list())
    # Listes formatées
    row_a17 = df.filter(pl.col("dagger_code") == "A17.8").to_dicts()[0]
    assert row_a17["levels_present"] == "T, H"
    assert row_a17["combination_labels"] == "méningoencéphalite tuberculeuse"


def test_re_export_preserves_existing_curation(mod: ModuleType, tmp_path: Path) -> None:
    parquet = tmp_path / "in.parquet"
    csv = tmp_path / "out.csv"
    _write_parquet(
        [
            {
                "dagger_code": "A18.1",
                "dagger_label": "Tuberculose génito-urinaire",
                "asterisk_code": "N33.0",
                "asterisk_label": "Cystite tuberculeuse",
                "combination_labels": ["cystite tuberculeuse"],
                "levels_present": ["G", "U"],
            }
        ],
        parquet,
    )
    assert mod.main(["--table", str(parquet), "--csv", str(csv)]) == 0

    # Simule curation manuelle dans Excel
    df = pl.read_csv(csv, infer_schema_length=0)
    df = df.with_columns(
        pl.lit("subordinate").alias("redundancy_level"),
        pl.lit("étiologie portée par la combinaison").alias("rationale"),
        pl.lit("remi").alias("curated_by"),
        pl.lit("2026-05-21").alias("curated_date"),
    )
    df.write_csv(csv)

    # Re-export : la table parquet n'a pas changé
    assert mod.main(["--table", str(parquet), "--csv", str(csv)]) == 0

    df2 = pl.read_csv(csv, infer_schema_length=0)
    row = df2.filter(pl.col("dagger_code") == "A18.1").to_dicts()[0]
    assert row["redundancy_level"] == "subordinate"
    assert row["rationale"] == "étiologie portée par la combinaison"
    assert row["curated_by"] == "remi"
    assert row["curated_date"] == "2026-05-21"


def test_re_export_adds_new_pairs(mod: ModuleType, tmp_path: Path) -> None:
    parquet = tmp_path / "in.parquet"
    csv = tmp_path / "out.csv"
    rows_v1 = [
        {
            "dagger_code": "A18.1",
            "dagger_label": "Tuberculose génito-urinaire",
            "asterisk_code": "N33.0",
            "asterisk_label": "Cystite tuberculeuse",
        }
    ]
    _write_parquet(rows_v1, parquet)
    assert mod.main(["--table", str(parquet), "--csv", str(csv)]) == 0

    # Cure la paire existante (valeur ≠ défaut) pour vérifier qu'elle
    # n'est pas écrasée
    df = pl.read_csv(csv, infer_schema_length=0).with_columns(
        pl.lit("subordinate").alias("redundancy_level")
    )
    df.write_csv(csv)

    # v2 : ajoute A17.8/G05.0
    rows_v2 = [
        *rows_v1,
        {
            "dagger_code": "A17.8",
            "dagger_label": "Tuberculose du SNC",
            "asterisk_code": "G05.0",
            "asterisk_label": "Encéphalite",
        },
    ]
    _write_parquet(rows_v2, parquet)
    assert mod.main(["--table", str(parquet), "--csv", str(csv)]) == 0

    df2 = pl.read_csv(csv, infer_schema_length=0)
    assert df2.height == 2
    assert set(df2["dagger_code"].to_list()) == {"A17.8", "A18.1"}
    # La curation de A18.1 est préservée
    a18 = df2.filter(pl.col("dagger_code") == "A18.1").to_dicts()[0]
    assert a18["redundancy_level"] == "subordinate"
    # La nouvelle paire reçoit les défauts
    a17 = df2.filter(pl.col("dagger_code") == "A17.8").to_dicts()[0]
    assert a17["redundancy_level"] == mod.DEFAULT_REDUNDANCY_LEVEL
    assert a17["curated_by"] == mod.DEFAULT_CURATED_BY
    assert a17["curated_date"] == mod.DEFAULT_CURATED_DATE


def test_re_export_flags_orphans(mod: ModuleType, tmp_path: Path) -> None:
    parquet = tmp_path / "in.parquet"
    csv = tmp_path / "out.csv"
    rows_v1 = [
        {
            "dagger_code": "A18.1",
            "dagger_label": "Tuberculose génito-urinaire",
            "asterisk_code": "N33.0",
            "asterisk_label": "Cystite tuberculeuse",
        },
        {
            "dagger_code": "A17.8",
            "dagger_label": "Tuberculose du SNC",
            "asterisk_code": "G05.0",
            "asterisk_label": "Encéphalite",
        },
    ]
    _write_parquet(rows_v1, parquet)
    assert mod.main(["--table", str(parquet), "--csv", str(csv)]) == 0

    # v2 : on retire A17.8/G05.0 de la table
    _write_parquet([rows_v1[0]], parquet)
    assert mod.main(["--table", str(parquet), "--csv", str(csv)]) == 0

    df = pl.read_csv(csv, infer_schema_length=0)
    assert df.height == 2  # l'orphelin est conservé
    a17 = df.filter(pl.col("dagger_code") == "A17.8").to_dicts()[0]
    a18 = df.filter(pl.col("dagger_code") == "A18.1").to_dicts()[0]
    assert a17["_orphan"].lower() in {"true", "1"}
    assert a18["_orphan"].lower() in {"false", "0"}
