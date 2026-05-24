from __future__ import annotations

from pathlib import Path

import polars as pl
import pyarrow.parquet as pq
import pytest

from recode_icd.loaders import ofs
from recode_icd.loaders.schemas import OfsCodesSchema, OfsDaggerAsteriskSchema

FIXTURE = Path(__file__).parent.parent / "fixtures" / "ofs_sample"

EXPECTED_VALID_CODES = {
    "(A00-B99)",
    "(A00-A09)",
    "A00",
    "A00.0",
    "A01",
    "A02",
    "A03",
    "(I00-I99)",
    "(I40-I49)",
    "I41",
    "(J00-J99)",
    "(J10-J18)",
    "J11",
}  # 13 valides (A99 a valid=0 et est filtré)


pytestmark = pytest.mark.unit


def test_load_codes_filters_invalid() -> None:
    df = ofs.load_codes(FIXTURE)
    assert set(df["code"].to_list()) == EXPECTED_VALID_CODES
    assert "A99" not in df["code"].to_list()


def test_type_mapping() -> None:
    df = ofs.load_codes(FIXTURE)
    chap = df.filter(pl.col("code") == "(A00-B99)").row(0, named=True)
    block = df.filter(pl.col("code") == "(A00-A09)").row(0, named=True)
    cat = df.filter(pl.col("code") == "A00").row(0, named=True)
    sub = df.filter(pl.col("code") == "A00.0").row(0, named=True)
    assert chap["type"] == "chapter"
    assert block["type"] == "block"
    assert cat["type"] == "category"
    assert sub["type"] == "category"


def test_ofs_type_preserved() -> None:
    df = ofs.load_codes(FIXTURE)
    chap = df.filter(pl.col("code") == "(A00-B99)").row(0, named=True)
    sub = df.filter(pl.col("code") == "A00.0").row(0, named=True)
    assert chap["ofs_type"] == "C"
    assert sub["ofs_type"] == "S"


def test_label_from_libelle_source_S() -> None:
    df = ofs.load_codes(FIXTURE)
    row = df.filter(pl.col("code") == "A00").row(0, named=True)
    assert row["label"] == "choléra"


def test_hierarchy_path() -> None:
    df = ofs.load_codes(FIXTURE)
    chap = df.filter(pl.col("code") == "(A00-B99)").row(0, named=True)
    a000 = df.filter(pl.col("code") == "A00.0").row(0, named=True)

    # A00.0 (level 4) doit être à profondeur 3 (chapter=0, block=1, cat=2, subcat=3)
    assert chap["depth"] == 0
    assert a000["depth"] == 3
    # nested set : chap contient A00.0
    assert chap["left"] < a000["left"] < a000["right"] < chap["right"]
    # path commence par le code du chapitre et finit par A00.0
    assert a000["path"].startswith("(A00-B99)/(A00-A09)/A00/A00.0")


def test_inclusions_list() -> None:
    df = ofs.load_codes(FIXTURE)
    a00 = df.filter(pl.col("code") == "A00").row(0, named=True)
    assert a00["inclusions"] is not None
    assert "diarrhée à V. cholerae" in list(a00["inclusions"])


def test_exclusions_text_and_redirect_aligned() -> None:
    df = ofs.load_codes(FIXTURE)
    a01 = df.filter(pl.col("code") == "A01").row(0, named=True)
    assert "salmonelloses à autres germes" in list(a01["exclusions_text"])
    assert "A02" in list(a01["exclusions_redirect"])


def test_dagger_asterisk_pair_extracted() -> None:
    df = ofs.load_dagger_asterisk(FIXTURE)
    assert len(df) == 1
    pair = df.row(0, named=True)
    # I41 < J11 lexicographiquement → start_code='I41', end_code='J11' après .sort()
    assert pair["start_code"] == "I41"
    assert pair["end_code"] == "J11"
    assert pair["daget"] == "H"
    assert pair["source"] == "OFS"


def test_dagger_asterisk_daget_in_range() -> None:
    df = ofs.load_dagger_asterisk(FIXTURE)
    for daget in df["daget"].to_list():
        if daget is not None:
            assert daget in {"F", "G", "H", "S", "T", "U"}


def test_codes_schema_validate() -> None:
    df = ofs.load_codes(FIXTURE)
    OfsCodesSchema.validate(df)


def test_dagger_asterisk_schema_validate() -> None:
    df = ofs.load_dagger_asterisk(FIXTURE)
    OfsDaggerAsteriskSchema.validate(df)


def test_load_codes_deterministic() -> None:
    first = ofs.load_codes(FIXTURE)
    second = ofs.load_codes(FIXTURE)
    assert first.equals(second)


def test_load_dagger_asterisk_deterministic() -> None:
    first = ofs.load_dagger_asterisk(FIXTURE)
    second = ofs.load_dagger_asterisk(FIXTURE)
    assert first.equals(second)


def test_descr_extract_synonymes() -> None:
    df = ofs.load_codes(FIXTURE)
    a03 = df.filter(pl.col("code") == "A03").row(0, named=True)
    assert a03["synonymes"] is not None
    assert "dysenterie bacillaire" in list(a03["synonymes"])


def test_notes_editorial_via_memo() -> None:
    df = ofs.load_codes(FIXTURE)
    a03 = df.filter(pl.col("code") == "A03").row(0, named=True)
    assert a03["notes_editorial"] is not None
    notes = list(a03["notes_editorial"])
    assert any("dysenterie de Sonne" in n for n in notes)


def test_chapter_count() -> None:
    df = ofs.load_codes(FIXTURE)
    chapters = df.filter(pl.col("type") == "chapter")
    assert len(chapters) == 3  # I, IX, X dans le fixture


def test_to_parquet_writes_metadata(tmp_path: Path) -> None:
    codes_path, pairs_path = ofs.to_parquet(FIXTURE, tmp_path)
    assert codes_path.exists()
    assert pairs_path.exists()

    table = pq.read_table(codes_path)
    metadata = {
        k.decode(): v.decode() for k, v in (table.schema.metadata or {}).items()
    }
    assert metadata["terminology"] == "cim10_ofs_2006"
    assert metadata["version"] == "V0001"
    assert metadata["source_dir"] == str(FIXTURE)
    assert "generated_at" in metadata
