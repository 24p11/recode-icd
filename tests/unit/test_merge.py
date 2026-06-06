from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd import merge
from recode_icd.loaders.schemas import MergedCodesSchema

pytestmark = pytest.mark.unit


def _make_owl(rows: list[dict[str, object]]) -> pl.DataFrame:
    """Petit DataFrame OWL avec toutes les colonnes attendues."""
    defaults = {
        "code": "",
        "label": None,
        "type": "category",
        "depth": 1,
        "left": 1,
        "right": 2,
        "path": "/",
        "synonymes": [],
        "inclusion_note": None,
        "exclusion_notes": [],
        "definitions": [],
        "scope_notes": [],
        "structured_exclusions": [],
    }
    return pl.DataFrame(
        [{**defaults, **r} for r in rows],
        schema={
            "code": pl.String,
            "label": pl.String,
            "type": pl.String,
            "depth": pl.Int64,
            "left": pl.Int64,
            "right": pl.Int64,
            "path": pl.String,
            "synonymes": pl.List(pl.String),
            "inclusion_note": pl.String,
            "exclusion_notes": pl.List(pl.String),
            "definitions": pl.List(pl.String),
            "scope_notes": pl.List(pl.String),
            "structured_exclusions": pl.List(pl.String),
        },
    )


def _make_ofs(rows: list[dict[str, object]]) -> pl.DataFrame:
    defaults = {
        "code": "",
        "abbrev": "",
        "label": None,
        "type": "category",
        "ofs_type": "K",
        "depth": 1,
        "left": 1,
        "right": 2,
        "path": "/",
        "synonymes": [],
        "inclusions": [],
        "exclusions_text": [],
        "exclusions_redirect": [],
        "notes_editorial": [],
    }
    return pl.DataFrame(
        [{**defaults, **r} for r in rows],
        schema={
            "code": pl.String,
            "abbrev": pl.String,
            "label": pl.String,
            "type": pl.String,
            "ofs_type": pl.String,
            "depth": pl.Int64,
            "left": pl.Int64,
            "right": pl.Int64,
            "path": pl.String,
            "synonymes": pl.List(pl.String),
            "inclusions": pl.List(pl.String),
            "exclusions_text": pl.List(pl.String),
            "exclusions_redirect": pl.List(pl.String),
            "notes_editorial": pl.List(pl.String),
        },
    )


def test_owl_only_code_kept() -> None:
    owl = _make_owl([{"code": "X99", "label": "Code OWL seul", "left": 1, "right": 2}])
    ofs = _make_ofs([{"code": "Y00", "abbrev": "Y00", "label": "Code OFS seul"}])
    out = merge.merge_codes(owl, ofs)
    assert len(out) == 1
    row = out.row(0, named=True)
    assert row["code"] == "X99"
    assert row["label"] == "Code OWL seul"
    assert row["has_ofs_match"] is False
    assert row["inclusions"] == []
    assert row["inclusions_source"] == "none"


def test_ofs_code_normalization_strips_parens() -> None:
    owl = _make_owl([{"code": "A00-A09", "type": "block", "label": "Bloc OWL"}])
    ofs = _make_ofs([{"code": "(A00-A09)", "abbrev": "(A00-A09)", "type": "block",
                      "label": "Bloc OFS", "inclusions": ["incl OFS"]}])
    out = merge.merge_codes(owl, ofs)
    assert out["has_ofs_match"].to_list() == [True]
    assert out["inclusions"].to_list() == [["incl OFS"]]


def test_inclusions_element_wise_keeps_distinct_owl_note() -> None:
    """Source mapping: OFS prio sur normalisation match ; les notes OWL textuellement
    différentes ne sont PAS silencieusement dropées."""
    owl = _make_owl([{"code": "A00", "label": "A00", "inclusion_note": "OWL inclusion"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00",
                      "inclusions": ["OFS incl 1", "OFS incl 2"]}])
    out = merge.merge_codes(owl, ofs)
    row = out.row(0, named=True)
    assert sorted(row["inclusions"]) == ["OFS incl 1", "OFS incl 2", "OWL inclusion"]
    assert row["inclusions_source"] == "OFS+OWL_ANS"


def test_inclusions_normalized_match_keeps_ofs_drops_owl() -> None:
    """Quand OFS et OWL ont une inclusion équivalente après normalisation
    (casse + accents + ponctuation interne), on garde la version OFS
    (texte original préservé) et on drop la version OWL."""
    owl = _make_owl([{"code": "A00", "label": "A00",
                      "inclusion_note": "DIARRHÉE à V.cholerae"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00",
                      "inclusions": ["diarrhee a v cholerae"]}])
    out = merge.merge_codes(owl, ofs)
    row = out.row(0, named=True)
    # La version OFS gagne (texte original conservé) ; OWL drope.
    assert row["inclusions"] == ["diarrhee a v cholerae"]
    assert row["inclusions_source"] == "OFS"


def test_inclusions_owl_fallback_when_ofs_empty() -> None:
    owl = _make_owl([{"code": "A00", "label": "A00", "inclusion_note": "OWL inclusion"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00", "inclusions": []}])
    out = merge.merge_codes(owl, ofs)
    row = out.row(0, named=True)
    assert row["inclusions"] == ["OWL inclusion"]
    assert row["inclusions_source"] == "OWL_ANS"


def test_inclusions_none_when_both_empty() -> None:
    owl = _make_owl([{"code": "A00", "label": "A00"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00"}])
    out = merge.merge_codes(owl, ofs)
    row = out.row(0, named=True)
    assert row["inclusions"] == []
    assert row["inclusions_source"] == "none"


def test_exclusions_element_wise_keeps_distinct_owl() -> None:
    owl = _make_owl([{"code": "A00", "label": "A00", "exclusion_notes": ["OWL excl"]}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00",
                      "exclusions_text": ["OFS excl A", "OFS excl B"]}])
    out = merge.merge_codes(owl, ofs)
    row = out.row(0, named=True)
    assert sorted(row["exclusions"]) == ["OFS excl A", "OFS excl B", "OWL excl"]
    assert row["exclusions_source"] == "OFS+OWL_ANS"


def test_exclusions_owl_fallback() -> None:
    owl = _make_owl([{"code": "A00", "label": "A00", "exclusion_notes": ["OWL excl"]}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00", "exclusions_text": []}])
    out = merge.merge_codes(owl, ofs)
    row = out.row(0, named=True)
    assert row["exclusions"] == ["OWL excl"]
    assert row["exclusions_source"] == "OWL_ANS"


def test_synonymes_union_dedup() -> None:
    owl = _make_owl([{"code": "A00", "label": "A00", "synonymes": ["s1", "s2"]}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00",
                      "synonymes": ["s2", "s3"]}])
    out = merge.merge_codes(owl, ofs)
    row = out.row(0, named=True)
    assert sorted(row["synonymes"]) == ["s1", "s2", "s3"]


def test_owl_only_fields_pass_through() -> None:
    owl = _make_owl([{"code": "A00", "label": "A00",
                      "definitions": ["def 1"],
                      "scope_notes": ["scope 1"],
                      "structured_exclusions": ["uri/B00"]}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00"}])
    out = merge.merge_codes(owl, ofs)
    row = out.row(0, named=True)
    assert row["definitions"] == ["def 1"]
    assert row["scope_notes"] == ["scope 1"]
    assert row["structured_exclusions"] == ["uri/B00"]


def test_ofs_only_fields_pass_through() -> None:
    owl = _make_owl([{"code": "A00", "label": "A00"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00",
                      "notes_editorial": ["note OFS"],
                      "exclusions_redirect": ["B01"]}])
    out = merge.merge_codes(owl, ofs)
    row = out.row(0, named=True)
    assert row["notes_editorial"] == ["note OFS"]
    assert row["exclusions_redirect"] == ["B01"]


def test_label_conflict_logged() -> None:
    owl = _make_owl([{"code": "A00", "label": "Sepsis à Salmonella"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "Septicémie à Salmonella"}])
    conflicts = merge.find_conflicts(owl, ofs)
    label_conflicts = conflicts.filter(pl.col("field") == "label")
    assert len(label_conflicts) == 1
    row = label_conflicts.row(0, named=True)
    assert row["owl_value"] == "Sepsis à Salmonella"
    assert row["ofs_value"] == "Septicémie à Salmonella"
    assert row["resolved_to"] == "OWL_ANS"


def test_label_no_conflict_on_case_only() -> None:
    owl = _make_owl([{"code": "A00", "label": "À Vibrio cholerae"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "à vibrio cholerae"}])
    conflicts = merge.find_conflicts(owl, ofs)
    label_conflicts = conflicts.filter(pl.col("field") == "label")
    assert len(label_conflicts) == 0


def test_orphan_ofs_logged() -> None:
    owl = _make_owl([{"code": "A00", "label": "A00"}])
    ofs = _make_ofs([
        {"code": "A00", "abbrev": "A00", "label": "A00 match"},
        {"code": "ZZZ", "abbrev": "ZZZ", "label": "orphan OFS"},
    ])
    orphans = merge.find_orphans(owl, ofs)
    assert len(orphans) == 1
    assert orphans.row(0, named=True)["code"] == "ZZZ"


def test_schema_validates() -> None:
    owl = _make_owl([{"code": "A00", "label": "L1"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "L2"}])
    out = merge.merge_codes(owl, ofs)
    MergedCodesSchema.validate(out)


def test_deterministic() -> None:
    owl = _make_owl([
        {"code": "B01", "label": "B01", "left": 3, "right": 4},
        {"code": "A00", "label": "A00", "left": 1, "right": 2,
         "synonymes": ["s1"]},
    ])
    ofs = _make_ofs([
        {"code": "A00", "abbrev": "A00", "label": "A00",
         "synonymes": ["s2"], "inclusions": ["i1"]},
    ])
    first = merge.merge_codes(owl, ofs)
    second = merge.merge_codes(owl, ofs)
    assert first.equals(second)


def test_to_parquet_and_reports_writes_all(tmp_path: Path) -> None:
    owl = _make_owl([
        {"code": "A00", "label": "A00"},
        {"code": "U07.1", "label": "COVID-19 post-2006"},
    ])
    ofs = _make_ofs([
        {"code": "A00", "abbrev": "A00", "label": "A00", "inclusions": ["i"]},
        {"code": "ZZZ", "abbrev": "ZZZ", "label": "orphan"},
    ])
    owl_path = tmp_path / "owl.parquet"
    ofs_path = tmp_path / "ofs.parquet"
    owl.write_parquet(owl_path)
    ofs.write_parquet(ofs_path)

    out_dir = tmp_path / "out"
    reports_dir = tmp_path / "reports"
    paths = merge.to_parquet_and_reports(owl_path, ofs_path, out_dir, reports_dir)

    assert set(paths.keys()) == {
        "merged", "conflicts", "orphans", "note_merges", "post_2006",
        "orphan_type_d",
    }
    for p in paths.values():
        assert p.exists()

    merged = pl.read_parquet(paths["merged"])
    assert len(merged) == 2
    orphans = pl.read_csv(paths["orphans"])
    assert orphans["code"].to_list() == ["ZZZ"]
    post_2006 = pl.read_csv(paths["post_2006"])
    assert post_2006["code"].to_list() == ["U07.1"]


def test_find_note_merges_identique_apres_normalisation() -> None:
    owl = _make_owl([{"code": "A00", "label": "A00", "inclusion_note": "DIARRHÉE à V."}])
    ofs = _make_ofs([
        {"code": "A00", "abbrev": "A00", "label": "A00",
         "inclusions": ["diarrhee a v"]},
    ])
    nm = merge.find_note_merges(owl, ofs)
    assert len(nm) == 1
    row = nm.row(0, named=True)
    assert row["code"] == "A00"
    assert row["type"] == "inclusion"
    assert row["texte_retenu"] == "diarrhee a v"
    assert row["texte_alternatif_ans"] is None
    assert row["libelles_identiques_apres_normalisation"] is True
    assert row["difference_significative"] is False


def test_find_note_merges_difference_significative() -> None:
    owl = _make_owl([{"code": "A00", "label": "A00", "inclusion_note": "Inclusion ANS distincte"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00",
                      "inclusions": ["Inclusion OFS"]}])
    nm = merge.find_note_merges(owl, ofs)
    assert len(nm) == 1
    row = nm.row(0, named=True)
    assert row["texte_retenu"] == "Inclusion OFS"
    assert row["texte_alternatif_ans"] == "Inclusion ANS distincte"
    assert row["libelles_identiques_apres_normalisation"] is False
    assert row["difference_significative"] is True


def test_find_note_merges_no_log_when_ofs_only() -> None:
    """Une note OFS sans contrepartie ANS n'est pas loggée."""
    owl = _make_owl([{"code": "A00", "label": "A00"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00",
                      "inclusions": ["OFS only"]}])
    nm = merge.find_note_merges(owl, ofs)
    assert len(nm) == 0


def test_find_post_2006_codes() -> None:
    owl = _make_owl([
        {"code": "A00", "label": "A00"},
        {"code": "U07.1", "label": "COVID"},
    ])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "A00"}])
    post = merge.find_post_2006_codes(owl, ofs)
    assert post["code"].to_list() == ["U07.1"]


def test_label_conflict_with_accent_difference_not_flagged() -> None:
    """Source mapping : la normalisation strip les accents, donc cosmétique
    accent ≠ conflit sémantique."""
    owl = _make_owl([{"code": "A00", "label": "Démence à Salmonella"}])
    ofs = _make_ofs([{"code": "A00", "abbrev": "A00", "label": "DEMENCE A SALMONELLA"}])
    conf = merge.find_conflicts(owl, ofs)
    assert len(conf) == 0


def test_label_conflict_real_semantic_difference_flagged() -> None:
    owl = _make_owl([{"code": "A02.1", "label": "Sepsis à Salmonella"}])
    ofs = _make_ofs([{"code": "A02.1", "abbrev": "A02.1", "label": "Septicémie à Salmonella"}])
    conf = merge.find_conflicts(owl, ofs)
    assert len(conf) == 1
    row = conf.row(0, named=True)
    assert row["code"] == "A02.1"
    assert row["resolved_to"] == "OWL_ANS"
