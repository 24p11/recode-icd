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


def _make_dagger_asterisk(rows: list[dict[str, object]]) -> pl.DataFrame:
    """Table DAGSTAR enrichie minimaliste pour tests unitaires. Le
    schéma reproduit `EnrichedDaggerAsteriskSchema`. Une liste vide
    produit un DataFrame vide bien typé, qui correspond au cas
    "aucune association"."""
    defaults: dict[str, object] = {
        "association_id": 0,
        "dagger_code": None,
        "dagger_label": None,
        "asterisk_code": None,
        "asterisk_label": None,
        "combination_labels": [],
        "levels_present": [],
        "redundancy_level": "none",
        "source_lids": [],
    }
    return pl.DataFrame(
        [{**defaults, **r} for r in rows],
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


def _df(build_result: object) -> pl.DataFrame:
    """Déballe le tuple `(df, stats)` retourné par `flat_csv.build`."""
    df, _ = build_result  # type: ignore[misc]
    return df


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
    out = _df(flat_csv.build(
        merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([])
    , _make_dagger_asterisk([])))
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
    out = _df(flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), _make_dagger_asterisk([])))
    types = dict(out.group_by("type").len().iter_rows())
    assert types == {"inclusion": 1, "exclusion": 1}


def test_note_editorial_dropped() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "note_editorial", "texte": "note", "source": "OFS"},
    ])
    out = _df(flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), _make_dagger_asterisk([])))
    assert len(out) == 0


def test_sibling_exclusions_included_with_csv_label() -> None:
    merged = _make_merged([{"code": "F06.8", "label": "F06.8", "left": 1, "right": 2}])
    siblings = _make_siblings([
        {"code": "F06.8", "texte": "Catatonie (F06.1)", "source": "SYNTHESIZED_SIBLING",
         "sibling_code": "F06.1"},
    ])
    out = _df(flat_csv.build(merged, _make_propagated([]), siblings, _make_owl([]), _make_ofs([]), _make_dagger_asterisk([])))
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
    out = _df(flat_csv.build(merged, _make_propagated([]), _make_siblings([]), owl, ofs, _make_dagger_asterisk([])))
    syn = out.filter(pl.col("type") == "synonyme")
    assert len(syn) == 1
    assert syn.row(0, named=True)["source"] == "CIM-10"


def test_synonymes_normalized_match_dedups() -> None:
    """Variantes typographiques (accents, casse) → 1 seule ligne, OFS gagne."""
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    owl = _make_owl([{"code": "A00.0", "synonymes": ["CHOLÉRA"]}])
    ofs = _make_ofs([{"code": "A00.0", "synonymes": ["cholera"]}])
    out = _df(flat_csv.build(merged, _make_propagated([]), _make_siblings([]), owl, ofs, _make_dagger_asterisk([])))
    syn = out.filter(pl.col("type") == "synonyme")
    assert len(syn) == 1
    row = syn.row(0, named=True)
    # Texte OFS original conservé (forme normalisée), source=CIM-10
    assert row["texte"] == "cholera"
    assert row["source"] == "CIM-10"


def test_synonymes_ofs_only_kept() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    ofs = _make_ofs([{"code": "A00.0", "synonymes": ["unique OFS syn"]}])
    out = _df(flat_csv.build(merged, _make_propagated([]), _make_siblings([]), _make_owl([]), ofs, _make_dagger_asterisk([])))
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
    out = _df(flat_csv.build(merged, _make_propagated([]), _make_siblings([]), _make_owl([]), ofs, _make_dagger_asterisk([])))
    assert len(out) == 1
    assert out.row(0, named=True)["code"] == "A00-A09"


def test_dedup_on_quadruple() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "duplicate", "source": "OFS"},
        {"code": "A00.0", "note_type": "inclusion", "texte": "duplicate", "source": "OFS",
         "inherited_from": "I", "inherited_from_type": "chapter"},  # propagé, même texte
    ])
    out = _df(flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), _make_dagger_asterisk([])))
    assert len(out) == 1
    # Dédup propre+hérité : on garde la version la plus spécifique (code).
    row = out.row(0, named=True)
    assert row["source_level"] == "code"
    assert row["inherited_from_code"] is None


def test_propagated_note_keeps_source_level_and_parent() -> None:
    """Une note uniquement héritée (pas de version propre) conserve
    son source_level et inherited_from_code."""
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "exclusion", "texte": "héritée du bloc",
         "source": "OFS", "inherited_from": "A00-A09", "inherited_from_type": "block"},
    ])
    out = _df(flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), _make_dagger_asterisk([])))
    row = out.filter(pl.col("texte") == "héritée du bloc").row(0, named=True)
    assert row["source_level"] == "block"
    assert row["inherited_from_code"] == "A00-A09"


def test_libelle_attached_correctly() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "Choléra à V. cholerae",
                             "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "x", "source": "OFS"},
    ])
    out = _df(flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), _make_dagger_asterisk([])))
    assert out.row(0, named=True)["libelle"] == "Choléra à V. cholerae"


def test_sort_order_type_inclusion_first() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "exclusion", "texte": "e", "source": "OFS"},
        {"code": "A00.0", "note_type": "inclusion", "texte": "i", "source": "OFS"},
    ])
    owl = _make_owl([{"code": "A00.0", "synonymes": ["syn"]}])
    out = _df(flat_csv.build(merged, propagated, _make_siblings([]), owl, _make_ofs([]), _make_dagger_asterisk([])))
    types = out["type"].to_list()
    assert types == ["inclusion", "exclusion", "synonyme"]


def test_deterministic() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "a", "source": "OFS"},
        {"code": "A00.0", "note_type": "inclusion", "texte": "b", "source": "OWL_ANS"},
    ])
    first = _df(flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), _make_dagger_asterisk([])))
    second = _df(flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), _make_dagger_asterisk([])))
    assert first.equals(second)


def test_unknown_source_raises() -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "x", "source": "UNKNOWN_SOURCE"},
    ])
    with pytest.raises(Exception):  # noqa: B017  (polars wraps multiple exception types)
        _df(flat_csv.build(merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), _make_dagger_asterisk([])))


def test_source_mapping_complete() -> None:
    # Sanity : chaque source interne doit avoir un mapping français défini.
    # AP-HP est éclaté en 9 valeurs par spécialité depuis Phase 1
    # (cf CLAUDE.md §"Mapping sources internes ↔ libellés CSV").
    expected_keys = {
        "OFS", "OWL_ANS", "SYNTHESIZED_SIBLING", "INDEX_CIM10_VOL3", "ORPHANET",
        "APHP_DERMATOLOGIE", "APHP_ENDOCRINOLOGIE", "APHP_GRONES",
        "APHP_METABOLISME", "APHP_NEPHROLOGIE", "APHP_OPHTALMOLOGIE",
        "APHP_RHUMATOLOGIE", "APHP_GERMES", "APHP_SRLF",
    }
    assert set(flat_csv._SOURCE_CSV_MAP.keys()) == expected_keys


def test_to_csv_writes_file(tmp_path: Path) -> None:
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "i", "source": "OFS"},
    ])
    siblings = _make_siblings([])
    owl = _make_owl([])
    ofs = _make_ofs([])
    dag_aster = _make_dagger_asterisk([])

    paths = {
        "merged": tmp_path / "merged.parquet",
        "propagated": tmp_path / "propagated.parquet",
        "siblings": tmp_path / "siblings.parquet",
        "owl": tmp_path / "owl.parquet",
        "ofs": tmp_path / "ofs.parquet",
        "dag_aster": tmp_path / "dagger_asterisk.parquet",
    }
    merged.write_parquet(paths["merged"])
    propagated.write_parquet(paths["propagated"])
    siblings.write_parquet(paths["siblings"])
    owl.write_parquet(paths["owl"])
    ofs.write_parquet(paths["ofs"])
    dag_aster.write_parquet(paths["dag_aster"])

    out_path = tmp_path / "out.csv"
    result = flat_csv.to_csv(
        paths["merged"], paths["propagated"], paths["siblings"],
        paths["owl"], paths["ofs"], paths["dag_aster"], out_path,
    )
    assert result == out_path
    assert out_path.exists()
    loaded = pl.read_csv(out_path)
    assert len(loaded) == 1
    # Refonte 2026-05-30 : schéma à 9 colonnes, plus d'expansion par
    # paire dague/astérisque ; deux flags booléens au niveau du code.
    assert loaded.columns == [
        "code", "libelle", "type", "source", "texte",
        "source_level", "inherited_from_code",
        "is_dagger_in_pair", "is_asterisk_in_pair",
    ]
    row = loaded.row(0, named=True)
    # Le code de test A00.0 n'a aucune paire dague/astérisque.
    assert row["is_dagger_in_pair"] is False
    assert row["is_asterisk_in_pair"] is False


# --------------------------------------------------------------------------- #
# Tests dague/astérisque — flags booléens + filtrage 15,8 %.
# Refonte 2026-05-30 : suppression de l'expansion par paire. Chaque
# note du code apparaît une seule fois ; les flags is_dagger_in_pair /
# is_asterisk_in_pair signalent la participation à la mécanique sans
# détailler les paires (cf docs/source_mapping.md §"Couples
# dague/astérisque : politique de représentation").
# --------------------------------------------------------------------------- #
def test_flat_csv_is_dagger_in_pair_true_for_dagger_code() -> None:
    """Un code qui apparaît en `dagger_code` dans la table enrichie a
    is_dagger_in_pair=True (et is_asterisk_in_pair=False)."""
    merged = _make_merged([
        {"code": "A18.1", "label": "TBC génito-urinaire", "left": 1, "right": 2},
        {"code": "N33.0", "label": "Cystite tuberculeuse", "left": 3, "right": 4},
    ])
    propagated = _make_propagated([
        {"code": "A18.1", "note_type": "inclusion", "texte": "incl-dag", "source": "OFS"},
    ])
    dag = _make_dagger_asterisk([
        {"dagger_code": "A18.1", "asterisk_code": "N33.0", "redundancy_level": "independent"},
    ])
    out = _df(flat_csv.build(
        merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), dag
    ))
    row = out.filter(pl.col("code") == "A18.1").row(0, named=True)
    assert row["is_dagger_in_pair"] is True
    assert row["is_asterisk_in_pair"] is False


def test_flat_csv_is_asterisk_in_pair_true_for_asterisk_code() -> None:
    """Un code qui apparaît en `asterisk_code` dans la table enrichie a
    is_asterisk_in_pair=True (et is_dagger_in_pair=False)."""
    merged = _make_merged([
        {"code": "A18.1", "label": "TBC génito-urinaire", "left": 1, "right": 2},
        {"code": "N33.0", "label": "Cystite tuberculeuse", "left": 3, "right": 4},
    ])
    propagated = _make_propagated([
        {"code": "N33.0", "note_type": "inclusion", "texte": "incl-aster", "source": "OFS"},
    ])
    dag = _make_dagger_asterisk([
        {"dagger_code": "A18.1", "asterisk_code": "N33.0", "redundancy_level": "independent"},
    ])
    out = _df(flat_csv.build(
        merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), dag
    ))
    row = out.filter(pl.col("code") == "N33.0").row(0, named=True)
    assert row["is_dagger_in_pair"] is False
    assert row["is_asterisk_in_pair"] is True


def test_flat_csv_unrelated_code_both_flags_false() -> None:
    """Code sans aucune entrée DAGSTAR : 1 ligne, deux flags à False."""
    merged = _make_merged([{"code": "A00.0", "label": "x", "left": 1, "right": 2}])
    propagated = _make_propagated([
        {"code": "A00.0", "note_type": "inclusion", "texte": "i", "source": "OFS"},
    ])
    out = _df(flat_csv.build(
        merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]),
        _make_dagger_asterisk([]),
    ))
    assert out.height == 1
    row = out.row(0, named=True)
    assert row["is_dagger_in_pair"] is False
    assert row["is_asterisk_in_pair"] is False


def test_flat_csv_no_expansion_one_line_per_note() -> None:
    """Refonte 2026-05-30 : un code dague associé à plusieurs
    astérisques produit toujours une seule ligne par note (plus
    d'expansion par paire). C'est le bug A01.0 / G01 corrigé."""
    merged = _make_merged([
        {"code": "M32.1", "label": "Lupus", "left": 1, "right": 2},
        {"code": "N08.5", "label": "Glomérulopathie LED", "left": 3, "right": 4},
        {"code": "N16.4", "label": "Néphropathie LED", "left": 5, "right": 6},
    ])
    propagated = _make_propagated([
        {"code": "M32.1", "note_type": "inclusion", "texte": "incl-LED", "source": "OFS"},
    ])
    dag = _make_dagger_asterisk([
        {"dagger_code": "M32.1", "asterisk_code": "N08.5", "redundancy_level": "independent"},
        {"dagger_code": "M32.1", "asterisk_code": "N16.4", "redundancy_level": "independent"},
    ])
    out = _df(flat_csv.build(
        merged, propagated, _make_siblings([]), _make_owl([]), _make_ofs([]), dag
    ))
    m32_lines = out.filter(pl.col("code") == "M32.1")
    # 1 seule ligne (avant : 2 lignes — une par paire).
    assert m32_lines.height == 1
    row = m32_lines.row(0, named=True)
    assert row["is_dagger_in_pair"] is True
    assert row["is_asterisk_in_pair"] is False


def test_filter_redundant_dagger_synonym_dropped() -> None:
    """Synonyme côté dague textuellement identique (normalisation) à un
    synonyme côté astérisque → supprimé du CSV."""
    merged = _make_merged([
        {"code": "A18.1", "label": "TBC génito-urinaire", "left": 1, "right": 2},
        {"code": "N33.0", "label": "Cystite tuberculeuse", "left": 3, "right": 4},
    ])
    ofs = _make_ofs([
        {"code": "A18.1", "synonymes": ["cystite tuberculeuse"]},
        {"code": "N33.0", "synonymes": ["cystite tuberculeuse"]},
    ])
    dag = _make_dagger_asterisk([
        {"dagger_code": "A18.1", "asterisk_code": "N33.0", "redundancy_level": "independent"},
    ])
    out = _df(flat_csv.build(
        merged, _make_propagated([]), _make_siblings([]), _make_owl([]), ofs, dag
    ))
    # Le synonyme survit uniquement côté astérisque (N33.0).
    syn_dagger = out.filter(
        (pl.col("code") == "A18.1") & (pl.col("type") == "synonyme")
    )
    syn_aster = out.filter(
        (pl.col("code") == "N33.0") & (pl.col("type") == "synonyme")
    )
    assert syn_dagger.height == 0
    assert syn_aster.height == 1


def test_filter_redundant_dagger_synonym_dropped_if_matches_asterisk_label() -> None:
    """Synonyme côté dague identique au libellé systématique côté
    astérisque → également supprimé."""
    merged = _make_merged([
        {"code": "A18.1", "label": "TBC génito-urinaire", "left": 1, "right": 2},
        {"code": "N33.0", "label": "cystite tuberculeuse", "left": 3, "right": 4},
    ])
    ofs = _make_ofs([
        {"code": "A18.1", "synonymes": ["cystite tuberculeuse"]},
    ])
    dag = _make_dagger_asterisk([
        {"dagger_code": "A18.1", "asterisk_code": "N33.0", "redundancy_level": "independent"},
    ])
    out = _df(flat_csv.build(
        merged, _make_propagated([]), _make_siblings([]), _make_owl([]), ofs, dag
    ))
    syn_dagger = out.filter(
        (pl.col("code") == "A18.1") & (pl.col("type") == "synonyme")
    )
    assert syn_dagger.height == 0


def test_filter_keeps_distinct_dagger_synonym() -> None:
    """Synonyme côté dague qui apporte une formulation différente →
    conservé (la règle empirique épargne les variations utiles)."""
    merged = _make_merged([
        {"code": "A18.1", "label": "TBC génito-urinaire", "left": 1, "right": 2},
        {"code": "N33.0", "label": "Cystite tuberculeuse", "left": 3, "right": 4},
    ])
    ofs = _make_ofs([
        {"code": "A18.1", "synonymes": ["tuberculose de la vessie"]},
        {"code": "N33.0", "synonymes": ["cystite tuberculeuse"]},
    ])
    dag = _make_dagger_asterisk([
        {"dagger_code": "A18.1", "asterisk_code": "N33.0", "redundancy_level": "independent"},
    ])
    out = _df(flat_csv.build(
        merged, _make_propagated([]), _make_siblings([]), _make_owl([]), ofs, dag
    ))
    syn_dagger = out.filter(
        (pl.col("code") == "A18.1") & (pl.col("type") == "synonyme")
    )
    assert syn_dagger.height == 1
    assert syn_dagger.row(0, named=True)["texte"] == "tuberculose de la vessie"


def test_flat_csv_build_returns_stats() -> None:
    """`FlatCsvStats` ne porte plus `n_dagger_lines_redundant` depuis la
    refonte 2026-05-30 (suppression de l'expansion par paire). Seul
    `n_synonyms_filtered_as_duplicates` (règle des 15,8 %) subsiste."""
    merged = _make_merged([
        {"code": "A18.1", "label": "TBC", "left": 1, "right": 2},
        {"code": "N33.0", "label": "Cystite", "left": 3, "right": 4},
    ])
    ofs = _make_ofs([
        {"code": "A18.1", "synonymes": ["cystite tuberculeuse"]},
        {"code": "N33.0", "synonymes": ["cystite tuberculeuse"]},
    ])
    dag = _make_dagger_asterisk([
        {"dagger_code": "A18.1", "asterisk_code": "N33.0", "redundancy_level": "independent"},
    ])
    _df_out, stats = flat_csv.build(
        merged, _make_propagated([]), _make_siblings([]), _make_owl([]), ofs, dag
    )
    assert stats.n_synonyms_filtered_as_duplicates == 1
