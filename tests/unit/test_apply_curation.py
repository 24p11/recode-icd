"""Tests unitaires pour `relations.dagger_asterisk.apply_curation`.

La fonction lit un CSV de curation (séparateur autodétecté) et applique
`redundancy_level=subordinate` aux paires curées dans la table DAGSTAR
enrichie. Cf docs/source_mapping.md §"Couples dague/astérisque"."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.relations import dagger_asterisk

pytestmark = pytest.mark.unit


def _make_table(rows: list[dict[str, object]]) -> pl.DataFrame:
    """Mini table DAGSTAR enrichie pour fixtures de test."""
    defaults: dict[str, object] = {
        "association_id": 0,
        "dagger_code": None,
        "dagger_label": None,
        "asterisk_code": None,
        "asterisk_label": None,
        "combination_labels": [],
        "levels_present": [],
        "redundancy_level": "independent",
        "source_lids": [],
    }
    return pl.DataFrame(
        [{**defaults, **r, "association_id": i} for i, r in enumerate(rows)],
        schema={
            "association_id": pl.Int64,
            "dagger_code": pl.String,
            "dagger_label": pl.String,
            "asterisk_code": pl.String,
            "asterisk_label": pl.String,
            "combination_labels": pl.List(pl.String),
            "levels_present": pl.List(pl.String),
            "redundancy_level": pl.String,
            "source_lids": pl.List(pl.Int64),
        },
    )


def _write_curation_csv(
    path: Path,
    rows: list[dict[str, object]],
    *,
    separator: str = ",",
) -> None:
    """Écrit un CSV de curation au format attendu par apply_curation."""
    cols = (
        "dagger_code",
        "dagger_label",
        "asterisk_code",
        "asterisk_label",
        "combination_labels",
        "levels_present",
        "redundancy_level",
        "rationale",
        "curated_by",
        "curated_date",
        "_orphan",
    )
    defaults: dict[str, object] = {
        "dagger_code": "",
        "dagger_label": "",
        "asterisk_code": "",
        "asterisk_label": "",
        "combination_labels": "",
        "levels_present": "",
        "redundancy_level": "independent",
        "rationale": "",
        "curated_by": "TEST",
        "curated_date": "2026-05-21",
        "_orphan": "false",
    }
    full = [{**defaults, **r} for r in rows]
    df = pl.DataFrame(full).select(*cols)
    df.write_csv(path, separator=separator)


# --------------------------------------------------------------------------- #
def test_apply_curation_marks_subordinate(tmp_path: Path) -> None:
    table = _make_table(
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0"},
            {"dagger_code": "A18.1", "asterisk_code": "N33.0"},
            {"dagger_code": "E10.2", "asterisk_code": "N08.3"},
        ]
    )
    csv = tmp_path / "curation.csv"
    _write_curation_csv(
        csv,
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0", "redundancy_level": "subordinate"},
            {"dagger_code": "A18.1", "asterisk_code": "N33.0", "redundancy_level": "subordinate"},
            {"dagger_code": "E10.2", "asterisk_code": "N08.3", "redundancy_level": "independent"},
        ],
    )
    curated, report = dagger_asterisk.apply_curation(table, csv)

    levels = dict(
        zip(
            zip(
                curated["dagger_code"].to_list(),
                curated["asterisk_code"].to_list(),
                strict=True,
            ),
            curated["redundancy_level"].to_list(),
            strict=True,
        )
    )
    assert levels[("A17.8", "G05.0")] == "subordinate"
    assert levels[("A18.1", "N33.0")] == "subordinate"
    assert levels[("E10.2", "N08.3")] == "independent"
    assert report.n_subordinate_applied == 2
    assert report.n_independent_in_csv == 1
    assert report.n_undecided == 0
    assert report.n_orphan_in_csv == 0


def test_apply_curation_autodetects_semicolon_separator(tmp_path: Path) -> None:
    table = _make_table(
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0"},
        ]
    )
    csv = tmp_path / "curation_excel_fr.csv"
    _write_curation_csv(
        csv,
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0", "redundancy_level": "subordinate"},
        ],
        separator=";",
    )
    curated, report = dagger_asterisk.apply_curation(table, csv)
    assert (
        curated.filter(pl.col("dagger_code") == "A17.8").row(0, named=True)["redundancy_level"]
        == "subordinate"
    )
    assert report.n_subordinate_applied == 1


def test_apply_curation_pair_absent_from_table_logged_as_orphan(tmp_path: Path) -> None:
    table = _make_table(
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0"},
        ]
    )
    csv = tmp_path / "curation.csv"
    _write_curation_csv(
        csv,
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0", "redundancy_level": "subordinate"},
            # Paire absente de la table
            {"dagger_code": "Z99.9", "asterisk_code": "X00.0", "redundancy_level": "subordinate"},
        ],
    )
    _curated, report = dagger_asterisk.apply_curation(table, csv)
    assert report.n_orphan_in_csv == 1
    # Seule la paire effectivement présente est comptée comme appliquée
    assert report.n_subordinate_applied == 1


def test_apply_curation_orphan_flagged_pair_is_ignored(tmp_path: Path) -> None:
    """Une ligne du CSV avec _orphan=true ne doit pas influencer la table."""
    table = _make_table(
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0"},
        ]
    )
    csv = tmp_path / "curation.csv"
    _write_curation_csv(
        csv,
        [
            {
                "dagger_code": "A17.8",
                "asterisk_code": "G05.0",
                "redundancy_level": "subordinate",
                "_orphan": "true",
            },
        ],
    )
    curated, report = dagger_asterisk.apply_curation(table, csv)
    assert curated.row(0, named=True)["redundancy_level"] == "independent"
    assert report.n_subordinate_applied == 0


def test_apply_curation_undecided_and_empty_are_counted(tmp_path: Path) -> None:
    table = _make_table(
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0"},
            {"dagger_code": "A18.1", "asterisk_code": "N33.0"},
        ]
    )
    csv = tmp_path / "curation.csv"
    _write_curation_csv(
        csv,
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0", "redundancy_level": "undecided"},
            {"dagger_code": "A18.1", "asterisk_code": "N33.0", "redundancy_level": ""},
        ],
    )
    curated, report = dagger_asterisk.apply_curation(table, csv)
    # Pas de subordinate → table inchangée
    for row in curated.iter_rows(named=True):
        assert row["redundancy_level"] == "independent"
    assert report.n_undecided == 2
    assert report.n_subordinate_applied == 0


def test_apply_curation_invalid_level_raises(tmp_path: Path) -> None:
    table = _make_table(
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0"},
        ]
    )
    csv = tmp_path / "curation.csv"
    _write_curation_csv(
        csv,
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0", "redundancy_level": "BOGUS"},
        ],
    )
    with pytest.raises(ValueError, match="redundancy_level"):
        dagger_asterisk.apply_curation(table, csv)


def test_apply_curation_table_pairs_absent_from_csv_counted(tmp_path: Path) -> None:
    """Paires complètes de la table non listées dans le CSV → comptées
    pour audit (elles gardent leur défaut)."""
    table = _make_table(
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0"},
            {"dagger_code": "A18.1", "asterisk_code": "N33.0"},
        ]
    )
    csv = tmp_path / "curation.csv"
    _write_curation_csv(
        csv,
        [
            {"dagger_code": "A17.8", "asterisk_code": "G05.0", "redundancy_level": "subordinate"},
        ],
    )
    _curated, report = dagger_asterisk.apply_curation(table, csv)
    assert report.n_pairs_in_table_absent_from_csv == 1


def test_apply_curation_report_serializes_to_long_rows() -> None:
    report = dagger_asterisk.CurationReport(
        n_subordinate_applied=5,
        n_independent_in_csv=10,
        n_undecided=1,
        n_orphan_in_csv=0,
        n_pairs_in_table_absent_from_csv=2,
    )
    rows = report.as_long_rows()
    assert len(rows) == 5
    keys = {(r["dimension"], r["value"]) for r in rows}
    assert ("curation", "subordinate_applied") in keys
    assert ("coherence", "csv_pairs_absent_from_table") in keys
