from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.exporters import flat_csv

pytestmark = pytest.mark.unit


def _make_merged(rows: list[dict[str, object]]) -> pl.DataFrame:
    defaults = {
        "code": "",
        "label": None,
        "type": "category",
        "left": 1,
        "right": 2,
    }
    return pl.DataFrame(
        [{**defaults, **r} for r in rows],
        schema={
            "code": pl.String,
            "label": pl.String,
            "type": pl.String,
            "left": pl.Int64,
            "right": pl.Int64,
        },
    )


def _make_propagated(rows: list[dict[str, object]]) -> pl.DataFrame:
    defaults = {
        "code": "",
        "code_label": None,
        "code_type": "category",
        "note_type": "inclusion",
        "texte": "",
        "source": "OFS",
        "inherited_from": None,
        "inherited_from_label": None,
        "inherited_from_type": None,
    }
    return pl.DataFrame(
        [{**defaults, **r} for r in rows],
        schema={
            "code": pl.String,
            "code_label": pl.String,
            "code_type": pl.String,
            "note_type": pl.String,
            "texte": pl.String,
            "source": pl.String,
            "inherited_from": pl.String,
            "inherited_from_label": pl.String,
            "inherited_from_type": pl.String,
        },
    )


def _make_siblings(rows: list[dict[str, object]]) -> pl.DataFrame:
    defaults = {
        "code": "",
        "code_label": None,
        "code_type": "category",
        "note_type": "exclusion",
        "texte": "",
        "source": "SYNTHESIZED_SIBLING",
        "sibling_code": "",
        "sibling_label": None,
    }
    return pl.DataFrame(
        [{**defaults, **r} for r in rows],
        schema={
            "code": pl.String,
            "code_label": pl.String,
            "code_type": pl.String,
            "note_type": pl.String,
            "texte": pl.String,
            "source": pl.String,
            "sibling_code": pl.String,
            "sibling_label": pl.String,
        },
    )


def _make_owl(rows: list[dict[str, object]]) -> pl.DataFrame:
    defaults = {"code": "", "synonymes": []}
    return pl.DataFrame(
        [{**defaults, **r} for r in rows],
        schema={"code": pl.String, "synonymes": pl.List(pl.String)},
    )


def _make_ofs(rows: list[dict[str, object]]) -> pl.DataFrame:
    defaults = {"code": "", "synonymes": []}
    return pl.DataFrame(
        [{**defaults, **r} for r in rows],
        schema={"code": pl.String, "synonymes": pl.List(pl.String)},
    )


def test_leaf_filter_excludes_non_leaves() -> None:
    merged = _make_merged([
        {"code": "I", "label": "Chap I", "type": "chapter", "left": 1, "right": 10},
        {"code": "A00-A09", "label": "Bloc", "type": "block", "left": 2, "right": 9},
        {"code": "A00", "label": "A00 internal", "type": "category", "left": 3, "right": 6},
        {"code": "A00.0", "label": "A00.0 leaf", "type": "category", "left": 4, "right": 5},
        {"code": "A99", "label": "A99 standalone", "type": "category", "left": 7, "right": 8},
    ])
    propagated = _make_propagated([
        {"code": "A00.0", "texte": "incl1", "source": "OFS"},
        {"code": "A00", "texte": "incl_internal", "source": "OFS"},
        {"code": "A99", "texte": "incl_a99", "source": "OFS"},
    ])
    out = flat_csv.build(
        merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([])
    )
    codes = set(out["code"].to_list())
    assert codes == {"A00.0", "A99"}
    assert "A00" not in codes
    assert "I" not in codes


def test_inclusions_and_exclusions_passed_through() -> None:
    merged = _make_merged([
        {"code": "A00.0", "label": "x", "left": 1, "right": 2},
    ])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "i1", "source": "OFS"},
        {"code": "A00.0", "note_type": "exclusion", "texte": "e1", "source": "OWL_ANS"},
    ])
    out = flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]))
    types = dict(out.group_by("type").len().iter_rows())
    assert types == {"inclusion": 1, "exclusion": 1}


def test_note_editorial_dropped() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "note_editorial", "texte": "note", "source": "OFS"},
    ])
    out = flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]))
    assert len(out) == 0


def test_sibling_exclusions_included_with_csv_label() -> None:
    merged = _make_merged([{"code": "F06.8", "label": "F06.8", "left": 1, "right": 2}])
    siblings = _make_siblings([
        {"code": "F06.8", "texte": "Catatonie (F06.1)", "source": "SYNTHESIZED_SIBLING",
         "sibling_code": "F06.1"},
    ])
    out = flat_csv.build(merged, _make_propagated([]), siblings, _make_owl([]), _make_ofs([]))
    assert len(out) == 1
    row = out.row(0, named=True)
    assert row["type"] == "exclusion"
    assert row["source"] == "CIM-10 frères"


def test_synonymes_ofs_priority_dedup() -> None:
    """Source mapping (doc canonique) : OFS prio sur les synonymes.
    Si même texte normalisé dans les deux, source=CIM-10 (OFS)."""
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    owl = _make_owl([{"code": "A00.0", "synonymes": ["choléra-élor"]}])
    ofs = _make_ofs([{"code": "A00.0", "synonymes": ["choléra-élor"]}])
    out = flat_csv.build(merged, _make_propagated([]), _make_siblings([]), owl, ofs)
    syn = out.filter(pl.col("type") == "synonyme")
    assert len(syn) == 1
    assert syn.row(0, named=True)["source"] == "CIM-10"


def test_synonymes_normalized_match_dedups() -> None:
    """Variantes typographiques (accents, casse) → 1 seule ligne, OFS gagne."""
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    owl = _make_owl([{"code": "A00.0", "synonymes": ["CHOLÉRA"]}])
    ofs = _make_ofs([{"code": "A00.0", "synonymes": ["cholera"]}])
    out = flat_csv.build(merged, _make_propagated([]), _make_siblings([]), owl, ofs)
    syn = out.filter(pl.col("type") == "synonyme")
    assert len(syn) == 1
    row = syn.row(0, named=True)
    # Texte OFS original conservé (forme normalisée), source=CIM-10
    assert row["texte"] == "cholera"
    assert row["source"] == "CIM-10"


def test_synonymes_ofs_only_kept() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    ofs = _make_ofs([{"code": "A00.0", "synonymes": ["unique OFS syn"]}])
    out = flat_csv.build(merged, _make_propagated([]), _make_siblings([]), _make_owl([]), ofs)
    syn = out.filter(pl.col("type") == "synonyme")
    assert len(syn) == 1
    row = syn.row(0, named=True)
    assert row["source"] == "CIM-10"
    assert row["texte"] == "unique OFS syn"


def test_synonymes_ofs_parens_normalized() -> None:
    merged = _make_merged([{"code": "A00-A09", "label": "Bloc", "type": "block",
                             "left": 1, "right": 2}])  # techniquement non-leaf, mais on teste juste la normalisation
    # → on contourne en utilisant un leaf
    merged = _make_merged([{"code": "A00-A09", "label": "Bloc", "type": "category",
                             "left": 1, "right": 2}])
    ofs = _make_ofs([{"code": "(A00-A09)", "synonymes": ["syn OFS"]}])
    out = flat_csv.build(merged, _make_propagated([]), _make_siblings([]), _make_owl([]), ofs)
    assert len(out) == 1
    assert out.row(0, named=True)["code"] == "A00-A09"


def test_dedup_on_quadruple() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "duplicate", "source": "OFS"},
        {"code": "A00.0", "note_type": "inclusion", "texte": "duplicate", "source": "OFS",
         "inherited_from": "I"},  # propagé d'un ancêtre, même texte
    ])
    out = flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]))
    assert len(out) == 1


def test_libelle_attached_correctly() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "Choléra à V. cholerae",
                             "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "x", "source": "OFS"},
    ])
    out = flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]))
    assert out.row(0, named=True)["libelle"] == "Choléra à V. cholerae"


def test_sort_order_type_inclusion_first() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "exclusion", "texte": "e", "source": "OFS"},
        {"code": "A00.0", "note_type": "inclusion", "texte": "i", "source": "OFS"},
    ])
    owl = _make_owl([{"code": "A00.0", "synonymes": ["syn"]}])
    out = flat_csv.build(merged, propagated, _make_siblings([]), owl, _make_ofs([]))
    types = out["type"].to_list()
    assert types == ["inclusion", "exclusion", "synonyme"]


def test_deterministic() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "a", "source": "OFS"},
        {"code": "A00.0", "note_type": "inclusion", "texte": "b", "source": "OWL_ANS"},
    ])
    first = flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]))
    second = flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]))
    assert first.equals(second)


def test_unknown_source_raises() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "x", "source": "UNKNOWN_SOURCE"},
    ])
    with pytest.raises(Exception):  # noqa: B017  (polars wraps multiple exception types)
        flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]))


def test_source_mapping_complete() -> None:
    # Sanity : chaque source interne doit avoir un mapping français défini
    expected_keys = {"OFS", "OWL_ANS", "INDEX_CIM10_VOL3", "SYNTHESIZED_SIBLING",
                     "ORPHANET", "AP_HP"}
    assert set(flat_csv._SOURCE_CSV_MAP.keys()) == expected_keys


def test_to_csv_writes_file(tmp_path: Path) -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "i", "source": "OFS"},
    ])
    siblings = _make_siblings([])
    owl = _make_owl([])
    ofs = _make_ofs([])

    paths = {
        "merged": tmp_path / "merged.parquet",
        "propagated": tmp_path / "propagated.parquet",
        "siblings": tmp_path / "siblings.parquet",
        "owl": tmp_path / "owl.parquet",
        "ofs": tmp_path / "ofs.parquet",
    }
    merged.write_parquet(paths["merged"])
    propagated.write_parquet(paths["propagated"])
    siblings.write_parquet(paths["siblings"])
    owl.write_parquet(paths["owl"])
    ofs.write_parquet(paths["ofs"])

    out_path = tmp_path / "out.csv"
    result = flat_csv.to_csv(
        paths["merged"], paths["propagated"], paths["siblings"],
        paths["owl"], paths["ofs"], out_path,
    )
    assert result == out_path
    assert out_path.exists()
    loaded = pl.read_csv(out_path)
    assert len(loaded) == 1
    assert loaded.columns == ["code", "libelle", "type", "source", "texte"]
