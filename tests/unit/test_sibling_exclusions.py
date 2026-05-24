from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.loaders.schemas import SiblingExclusionsSchema
from recode_icd.relations import sibling_exclusions

pytestmark = pytest.mark.unit


def _make_merged(rows: list[dict[str, object]]) -> pl.DataFrame:
    """Mini merged_codes DataFrame avec seulement les colonnes consommées par sibling_exclusions."""
    defaults = {
        "code": "",
        "label": None,
        "type": "category",
    }
    return pl.DataFrame(
        [{**defaults, **r} for r in rows],
        schema={
            "code": pl.String,
            "label": pl.String,
            "type": pl.String,
        },
    )


def test_basic_f068_with_8_siblings() -> None:
    rows = [{"code": f"F06.{i}", "label": f"F06.{i} libellé"} for i in range(10)]
    merged = _make_merged(rows)
    out, skipped = sibling_exclusions.synthesize(merged)
    f068 = out.filter(pl.col("code") == "F06.8")
    assert len(f068) == 8
    assert sorted(f068["sibling_code"].to_list()) == [f"F06.{i}" for i in range(8)]
    assert len(skipped) == 0


def test_j458_with_partial_siblings() -> None:
    merged = _make_merged([
        {"code": "J45.0", "label": "Asthme allergique"},
        {"code": "J45.1", "label": "Asthme non allergique"},
        {"code": "J45.8", "label": "Asthme association"},
    ])
    out, _ = sibling_exclusions.synthesize(merged)
    assert len(out) == 2
    assert sorted(out["sibling_code"].to_list()) == ["J45.0", "J45.1"]


def test_no_siblings_emits_nothing() -> None:
    merged = _make_merged([{"code": "Z99.8", "label": "z99.8 seul"}])
    out, skipped = sibling_exclusions.synthesize(merged)
    assert len(out) == 0
    assert len(skipped) == 0


def test_dot9_excluded_from_siblings() -> None:
    merged = _make_merged([
        {"code": "A00.0", "label": "a00.0"},
        {"code": "A00.8", "label": "a00.8"},
        {"code": "A00.9", "label": "a00.9"},
    ])
    out, _ = sibling_exclusions.synthesize(merged)
    assert out["sibling_code"].to_list() == ["A00.0"]


def test_c00_c75_skipped_with_log() -> None:
    merged = _make_merged([
        {"code": "C05.0", "label": "C05.0"},
        {"code": "C05.1", "label": "C05.1"},
        {"code": "C05.8", "label": "C05.8 — lésion contiguë"},
    ])
    out, skipped = sibling_exclusions.synthesize(merged)
    assert len(out) == 0
    assert len(skipped) == 1
    row = skipped.row(0, named=True)
    assert row["code"] == "C05.8"
    assert "C00-C75" in row["reason"]


def test_c76_not_skipped() -> None:
    merged = _make_merged([
        {"code": "C76.0", "label": "C76.0"},
        {"code": "C76.8", "label": "C76.8"},
    ])
    out, skipped = sibling_exclusions.synthesize(merged)
    assert len(out) == 1
    assert len(skipped) == 0


def test_non_standard_codes_ignored() -> None:
    merged = _make_merged([
        {"code": "S82.10", "label": "S82.10 (6 chars)"},
        {"code": "S82.18", "label": "S82.18 (6 chars, ends in .8)"},
        {"code": "B24.+0", "label": "B24.+0 (extension)"},
    ])
    out, skipped = sibling_exclusions.synthesize(merged)
    assert len(out) == 0
    assert len(skipped) == 0


def test_chapter_block_codes_not_processed() -> None:
    merged = _make_merged([
        {"code": "(A00-B99)", "label": "Chap I", "type": "chapter"},
        {"code": "A00-A09", "label": "Bloc", "type": "block"},
        {"code": "A00.8", "label": "A00.8"},
        {"code": "A00.0", "label": "A00.0"},
    ])
    out, _ = sibling_exclusions.synthesize(merged)
    # Une seule ligne, pour A00.8 + A00.0
    assert len(out) == 1
    assert out.row(0, named=True)["code"] == "A00.8"


def test_schema_validates() -> None:
    merged = _make_merged([
        {"code": "F06.0", "label": "x"},
        {"code": "F06.8", "label": "y"},
    ])
    out, _ = sibling_exclusions.synthesize(merged)
    SiblingExclusionsSchema.validate(out)


def test_deterministic() -> None:
    merged = _make_merged([
        {"code": f"F06.{i}", "label": f"lib{i}"} for i in range(10)
    ])
    first, _ = sibling_exclusions.synthesize(merged)
    second, _ = sibling_exclusions.synthesize(merged)
    assert first.equals(second)


def test_texte_format() -> None:
    merged = _make_merged([
        {"code": "J45.0", "label": "Asthme à prédominance allergique"},
        {"code": "J45.8", "label": "J45.8"},
    ])
    out, _ = sibling_exclusions.synthesize(merged)
    row = out.row(0, named=True)
    assert row["texte"] == "Asthme à prédominance allergique (J45.0)"


def test_to_parquet_writes_files(tmp_path: Path) -> None:
    merged = _make_merged([
        {"code": "F06.0", "label": "x"},
        {"code": "F06.8", "label": "y"},
        {"code": "C05.8", "label": "skipped"},
    ])
    merged_path = tmp_path / "m.parquet"
    out_path = tmp_path / "siblings.parquet"
    rep_path = tmp_path / "skipped.csv"
    merged.write_parquet(merged_path)

    sibling_exclusions.to_parquet_and_report(merged_path, out_path, rep_path)
    assert out_path.exists()
    assert rep_path.exists()

    siblings = pl.read_parquet(out_path)
    skipped = pl.read_csv(rep_path)
    assert len(siblings) == 1
    assert len(skipped) == 1
