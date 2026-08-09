from __future__ import annotations

from pathlib import Path

import polars as pl
import pyarrow.parquet as pq
import pytest

from recode_icd.loaders import owl
from recode_icd.loaders.schemas import DaggerAsteriskSchema, OwlCodesSchema

FIXTURE = Path(__file__).parent.parent / "fixtures" / "owl_sample.rdf"
EXPECTED_CODES = {
    "II",
    "C00-C14",
    "C12",
    "D40-D48",
    "D48",
    "D48.5",
    "V",
    "F00-F09",
    "F02",
    "F02.0",
    "F02.00",
    "F60-F69",
    "F66",
    "F66.2",
    "VI",
    "G30-G32",
    "G31",
    "G31.0",
    "IX",
    "I40-I49",
    "I41",
    "I41.1",
    "X",
    "J10-J18",
    "J11",
    "J11.8",
}


pytestmark = pytest.mark.unit


def test_load_codes_returns_all_concepts() -> None:
    df = owl.load_codes(FIXTURE)
    assert set(df["code"].to_list()) == EXPECTED_CODES


def test_chapter_type_distribution() -> None:
    df = owl.load_codes(FIXTURE)
    counts = df.group_by("type").len().sort("type")
    by_type = dict(counts.iter_rows())
    assert by_type["chapter"] == 5
    assert by_type["block"] == 7
    assert by_type["category"] == 14


def test_synonymes_aggregated() -> None:
    df = owl.load_codes(FIXTURE)
    row = df.filter(pl.col("code") == "F02.00").row(0, named=True)
    assert sorted(row["synonymes"]) == [
        "Démence frontotemporale type Pick",
        "Pick (maladie de) avec démence",
    ]


def test_inclusion_note_extracted() -> None:
    df = owl.load_codes(FIXTURE)
    row = df.filter(pl.col("code") == "F02").row(0, named=True)
    assert row["inclusion_note"] is not None
    assert "Démence due" in row["inclusion_note"]


def test_exclusion_note_extracted() -> None:
    df = owl.load_codes(FIXTURE)
    row = df.filter(pl.col("code") == "C12").row(0, named=True)
    assert row["exclusion_notes"] is not None
    notes = list(row["exclusion_notes"])
    assert any("marge anale" in n for n in notes)


def test_structured_exclusion_extracted() -> None:
    df = owl.load_codes(FIXTURE)
    row = df.filter(pl.col("code") == "C12").row(0, named=True)
    assert row["structured_exclusions"] is not None
    structured = list(row["structured_exclusions"])
    assert any(uri.endswith("/D48.5") for uri in structured)


def test_definition_extracted() -> None:
    df = owl.load_codes(FIXTURE)
    row = df.filter(pl.col("code") == "F66.2").row(0, named=True)
    assert row["definitions"] is not None
    defs = list(row["definitions"])
    assert any("orientation sexuelle" in d for d in defs)


def test_scope_note_extracted() -> None:
    df = owl.load_codes(FIXTURE)
    row = df.filter(pl.col("code") == "F00-F09").row(0, named=True)
    assert row["scope_notes"] is not None
    notes = list(row["scope_notes"])
    assert any("étiologie organique" in n for n in notes)


def test_ans_brackets_normalized_in_label() -> None:
    """Chantier 4 : `[G31.0]` du label F02.00 doit devenir `(G31.0)`."""
    df = owl.load_codes(FIXTURE)
    row = df.filter(pl.col("code") == "F02.00").row(0, named=True)
    assert "[G31.0]" not in row["label"]
    assert "(G31.0)" in row["label"]


def test_ans_brackets_normalized_in_exclusion_notes() -> None:
    """Chantier 4 : `[D48.5]` dans les exclusions C12 → `(D48.5)`."""
    df = owl.load_codes(FIXTURE)
    row = df.filter(pl.col("code") == "C12").row(0, named=True)
    joined = " | ".join(row["exclusion_notes"])
    assert "[D48.5]" not in joined
    assert "(D48.5)" in joined


def test_nested_set_hierarchy() -> None:
    df = owl.load_codes(FIXTURE)
    f0200 = df.filter(pl.col("code") == "F02.00").row(0, named=True)
    f02 = df.filter(pl.col("code") == "F02").row(0, named=True)
    chap_v = df.filter(pl.col("code") == "V").row(0, named=True)

    # F02.00 ⊂ F02 ⊂ V
    assert f02["left"] < f0200["left"] < f0200["right"] < f02["right"]
    assert chap_v["left"] < f02["left"] < f02["right"] < chap_v["right"]
    assert f0200["depth"] == f02["depth"] + 2  # F02 -> F02.0 -> F02.00
    assert f0200["path"].endswith("/F02/F02.0/F02.00")


def test_dagger_asterisk_direct() -> None:
    df = owl.load_dagger_asterisk(FIXTURE)
    pair = df.filter((pl.col("asterisk_code") == "F02.00") & (pl.col("dagger_code") == "G31.0"))
    assert len(pair) == 1
    evidence = list(pair.row(0, named=True)["evidence"])
    assert "direct_causality" in evidence


def test_dagger_asterisk_axiom() -> None:
    df = owl.load_dagger_asterisk(FIXTURE)
    pair = df.filter((pl.col("asterisk_code") == "I41.1") & (pl.col("dagger_code") == "J11.8"))
    assert len(pair) == 1
    evidence = list(pair.row(0, named=True)["evidence"])
    assert "axiom_causality" in evidence


def test_dagger_asterisk_count() -> None:
    df = owl.load_dagger_asterisk(FIXTURE)
    assert len(df) == 2  # exactement les 2 paires du fixture


def test_dagger_asterisk_source_constant() -> None:
    df = owl.load_dagger_asterisk(FIXTURE)
    assert set(df["source"].to_list()) == {"OWL_ANS"}


def test_codes_schema_validation() -> None:
    df = owl.load_codes(FIXTURE)
    OwlCodesSchema.validate(df)


def test_dagger_asterisk_schema_validation() -> None:
    df = owl.load_dagger_asterisk(FIXTURE)
    DaggerAsteriskSchema.validate(df)


def test_load_codes_deterministic() -> None:
    first = owl.load_codes(FIXTURE)
    second = owl.load_codes(FIXTURE)
    assert first.equals(second)


def test_load_dagger_asterisk_deterministic() -> None:
    first = owl.load_dagger_asterisk(FIXTURE)
    second = owl.load_dagger_asterisk(FIXTURE)
    assert first.equals(second)


def test_to_parquet_writes_metadata(tmp_path: Path) -> None:
    # extract_version exige le préfixe officiel — on copie la fixture sous le bon nom
    renamed = tmp_path / "terminologie-cim-10-2025-01-01.rdf"
    renamed.write_text(FIXTURE.read_text())
    output_dir = tmp_path / "out"

    codes_path, pairs_path = owl.to_parquet(renamed, output_dir)

    assert codes_path.exists()
    assert pairs_path.exists()

    table = pq.read_table(codes_path)
    metadata = {k.decode(): v.decode() for k, v in (table.schema.metadata or {}).items()}
    assert metadata["terminology"] == "cim10_ans"
    assert metadata["version"] == "2025-01-01"
    assert metadata["source_file"] == "terminologie-cim-10-2025-01-01.rdf"
    assert "generated_at" in metadata


def test_to_parquet_extract_version_fails_on_bad_filename(tmp_path: Path) -> None:
    bad_path = tmp_path / "wrong-prefix-2025-01-01.rdf"
    bad_path.write_text(FIXTURE.read_text())
    with pytest.raises(ValueError, match="does not start with prefix"):
        owl.to_parquet(bad_path, tmp_path)
