from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd import propagation
from recode_icd.loaders.schemas import PropagatedNotesSchema

pytestmark = pytest.mark.unit


def _make_merged(rows: list[dict[str, object]]) -> pl.DataFrame:
    """Mini merged_codes DataFrame avec toutes les colonnes attendues par propagation.

    Si `inclusions_per_source` / `exclusions_per_source` ne sont pas fournis,
    on dérive automatiquement une liste de la même longueur que `inclusions` /
    `exclusions` en répétant `inclusions_source` / `exclusions_source`.
    """
    materialized = []
    for r in rows:
        row = dict(r)
        for col, src in (("inclusions", "inclusions_source"), ("exclusions", "exclusions_source")):
            per_col = f"{col}_per_source"
            if per_col not in row:
                texts = row.get(col, [])
                src_val = row.get(src, "none")
                row[per_col] = [src_val] * len(texts) if texts else []
        materialized.append(row)

    defaults = {
        "code": "",
        "label": None,
        "type": "category",
        "depth": 0,
        "left": 1,
        "right": 2,
        "path": "",
        "inclusions": [],
        "inclusions_per_source": [],
        "inclusions_source": "none",
        "exclusions": [],
        "exclusions_per_source": [],
        "exclusions_source": "none",
        "exclusions_redirect": [],
        "structured_exclusions": [],
        "notes_editorial": [],
        "definitions": [],
        "scope_notes": [],
        "synonymes": [],
        "has_ofs_match": False,
    }
    return pl.DataFrame(
        [{**defaults, **r} for r in materialized],
        schema={
            "code": pl.String,
            "label": pl.String,
            "type": pl.String,
            "depth": pl.Int64,
            "left": pl.Int64,
            "right": pl.Int64,
            "path": pl.String,
            "inclusions": pl.List(pl.String),
            "inclusions_per_source": pl.List(pl.String),
            "inclusions_source": pl.String,
            "exclusions": pl.List(pl.String),
            "exclusions_per_source": pl.List(pl.String),
            "exclusions_source": pl.String,
            "exclusions_redirect": pl.List(pl.String),
            "structured_exclusions": pl.List(pl.String),
            "notes_editorial": pl.List(pl.String),
            "definitions": pl.List(pl.String),
            "scope_notes": pl.List(pl.String),
            "synonymes": pl.List(pl.String),
            "has_ofs_match": pl.Boolean,
        },
    )


def test_chapter_own_inclusion_emitted() -> None:
    merged = _make_merged(
        [
            {
                "code": "I",
                "label": "Chapter I",
                "type": "chapter",
                "path": "I",
                "inclusions": ["chapter_incl"],
                "inclusions_source": "OWL_ANS",
            },
        ]
    )
    out = propagation.propagate(merged)
    assert len(out) == 1
    row = out.row(0, named=True)
    assert row["code"] == "I"
    assert row["note_type"] == "inclusion"
    assert row["texte"] == "chapter_incl"
    assert row["inherited_from"] is None
    assert row["source"] == "OWL_ANS"


def test_leaf_inherits_from_chapter() -> None:
    merged = _make_merged(
        [
            {
                "code": "I",
                "label": "Chapter I",
                "type": "chapter",
                "path": "I",
                "inclusions": ["chapter_incl"],
                "inclusions_source": "OWL_ANS",
            },
            {"code": "A00", "label": "Choléra", "type": "category", "path": "I/A00-A09/A00"},
        ]
    )
    out = propagation.propagate(merged)
    a00_rows = out.filter(pl.col("code") == "A00")
    assert len(a00_rows) == 1
    row = a00_rows.row(0, named=True)
    assert row["texte"] == "chapter_incl"
    assert row["inherited_from"] == "I"
    assert row["inherited_from_label"] == "Chapter I"
    assert row["inherited_from_type"] == "chapter"


def test_leaf_inherits_from_multiple_ancestors() -> None:
    merged = _make_merged(
        [
            {
                "code": "I",
                "label": "Chap",
                "type": "chapter",
                "path": "I",
                "inclusions": ["chap_incl"],
                "inclusions_source": "OWL_ANS",
            },
            {
                "code": "A00-A09",
                "label": "Bloc",
                "type": "block",
                "path": "I/A00-A09",
                "exclusions": ["bloc_excl"],
                "exclusions_source": "OFS",
            },
            {
                "code": "A00",
                "label": "Cat",
                "type": "category",
                "path": "I/A00-A09/A00",
                "notes_editorial": ["cat_note"],
            },
            {"code": "A00.0", "label": "Sub", "type": "category", "path": "I/A00-A09/A00/A00.0"},
        ]
    )
    out = propagation.propagate(merged)
    leaf = out.filter(pl.col("code") == "A00.0")
    inherited_from = sorted(leaf["inherited_from"].drop_nulls().to_list())
    assert inherited_from == ["A00", "A00-A09", "I"]
    assert len(leaf) == 3


def test_own_note_kept_alongside_inherited() -> None:
    merged = _make_merged(
        [
            {
                "code": "I",
                "label": "Chap",
                "type": "chapter",
                "path": "I",
                "inclusions": ["chap_incl"],
                "inclusions_source": "OWL_ANS",
            },
            {
                "code": "A00",
                "label": "Cat",
                "type": "category",
                "path": "I/A00",
                "inclusions": ["own_incl"],
                "inclusions_source": "OFS",
            },
        ]
    )
    out = propagation.propagate(merged)
    a00 = out.filter(pl.col("code") == "A00").sort("inherited_from", nulls_last=False)
    assert len(a00) == 2
    own_row = a00.filter(pl.col("inherited_from").is_null()).row(0, named=True)
    inh_row = a00.filter(pl.col("inherited_from").is_not_null()).row(0, named=True)
    assert own_row["texte"] == "own_incl"
    assert own_row["source"] == "OFS"
    assert inh_row["texte"] == "chap_incl"
    assert inh_row["inherited_from"] == "I"


def test_no_propagation_for_synonymes() -> None:
    merged = _make_merged(
        [
            {
                "code": "I",
                "label": "Chap",
                "type": "chapter",
                "path": "I",
                "synonymes": ["chap_syn"],
            },
            {
                "code": "A00",
                "label": "Cat",
                "type": "category",
                "path": "I/A00",
                "synonymes": ["own_syn"],
            },
        ]
    )
    out = propagation.propagate(merged)
    assert len(out) == 0  # aucun note_type ne couvre synonymes


def test_code_without_notes_absent() -> None:
    merged = _make_merged(
        [
            {"code": "I", "label": "Chap", "type": "chapter", "path": "I"},
            {"code": "A00", "label": "Cat", "type": "category", "path": "I/A00"},
        ]
    )
    out = propagation.propagate(merged)
    assert len(out) == 0


def test_source_preserved_for_inclusions() -> None:
    merged = _make_merged(
        [
            {
                "code": "A",
                "label": "A",
                "type": "chapter",
                "path": "A",
                "inclusions": ["x"],
                "inclusions_source": "OFS",
            },
            {
                "code": "B",
                "label": "B",
                "type": "chapter",
                "path": "B",
                "inclusions": ["y"],
                "inclusions_source": "OWL_ANS",
            },
        ]
    )
    out = propagation.propagate(merged)
    assert out.filter(pl.col("code") == "A").row(0, named=True)["source"] == "OFS"
    assert out.filter(pl.col("code") == "B").row(0, named=True)["source"] == "OWL_ANS"


def test_source_constant_for_notes_editorial() -> None:
    merged = _make_merged(
        [
            {
                "code": "A00",
                "label": "A00",
                "type": "category",
                "path": "A00",
                "notes_editorial": ["note1"],
            },
        ]
    )
    out = propagation.propagate(merged)
    assert out.row(0, named=True)["source"] == "OFS"
    assert out.row(0, named=True)["note_type"] == "note_editorial"


def test_inherited_from_label_resolved() -> None:
    merged = _make_merged(
        [
            {
                "code": "I",
                "label": "Mon chapitre",
                "type": "chapter",
                "path": "I",
                "inclusions": ["x"],
                "inclusions_source": "OWL_ANS",
            },
            {"code": "A00", "label": "A00", "type": "category", "path": "I/A00"},
        ]
    )
    out = propagation.propagate(merged)
    row = out.filter(pl.col("code") == "A00").row(0, named=True)
    assert row["inherited_from_label"] == "Mon chapitre"
    assert row["inherited_from_type"] == "chapter"


def test_schema_validates() -> None:
    merged = _make_merged(
        [
            {
                "code": "A",
                "label": "A",
                "type": "chapter",
                "path": "A",
                "inclusions": ["x"],
                "inclusions_source": "OFS",
            },
        ]
    )
    out = propagation.propagate(merged)
    PropagatedNotesSchema.validate(out)


def test_deterministic() -> None:
    merged = _make_merged(
        [
            {
                "code": "I",
                "label": "I",
                "type": "chapter",
                "path": "I",
                "inclusions": ["x", "y"],
                "inclusions_source": "OWL_ANS",
            },
            {
                "code": "A00",
                "label": "A00",
                "type": "category",
                "path": "I/A00",
                "inclusions": ["z"],
                "inclusions_source": "OFS",
            },
        ]
    )
    first = propagation.propagate(merged)
    second = propagation.propagate(merged)
    assert first.equals(second)


def test_to_parquet_writes_file(tmp_path: Path) -> None:
    merged = _make_merged(
        [
            {
                "code": "A",
                "label": "A",
                "type": "chapter",
                "path": "A",
                "inclusions": ["x"],
                "inclusions_source": "OFS",
            },
        ]
    )
    merged_path = tmp_path / "m.parquet"
    out_path = tmp_path / "p.parquet"
    merged.write_parquet(merged_path)

    result = propagation.to_parquet(merged_path, out_path)
    assert result == out_path
    assert out_path.exists()
    loaded = pl.read_parquet(out_path)
    assert len(loaded) == 1
