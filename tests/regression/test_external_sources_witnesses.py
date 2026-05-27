"""Tests de régression Phase 3 — 11 codes témoins + 3 cohérences.

Valide empiriquement que le pipeline complet (OFS + ANS + dague/
astérisque + sources externes) produit le résultat attendu pour des
codes spécifiquement choisis. Cf `tests/regression/README.md` et
`tests/fixtures/sample_codes.yaml`.

Les fixtures `csv_final_df`, `orphan_report_df`, `overlaps_report_df`
sont définies dans `conftest.py` (scope module).

Style :
- Fourchettes pour la volumétrie, pas de valeur exacte.
- Présence d'au moins 1 entrée d'une source plutôt qu'égalité stricte.
- Pas de libellé exact sauf libellé systématique OFS.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.regression


_EXTERNAL_SOURCES = {
    "ORPHANET",
    "CIM-10 index",
    "AP-HP Dermatologie",
    "AP-HP Endocrinologie",
    "AP-HP GRONES",
    "AP-HP Troubles métaboliques",
    "AP-HP Néphrologie",
    "AP-HP Ophtalmologie",
    "AP-HP Rhumatologie",
    "AP-HP Germes (SPILF)",
    "AP-HP SRLF",
}


# ----------------------------------------------------------------------
# A. ORPHANET relation E (synonyme)
# ----------------------------------------------------------------------


def test_e84_8_has_orphanet_mucoviscidose(csv_final_df: pl.DataFrame) -> None:
    """E84.8 (Mucoviscidose avec autres manifestations) doit porter
    au moins une entrée ORPHANET. Note : E84 (parent) est non-leaf
    donc absent du CSV — on teste sur la sous-catégorie."""
    sub = csv_final_df.filter(pl.col("code") == "E84.8")
    assert sub.height > 0, "E84.8 doit être présent dans le CSV"
    orphanet = sub.filter(pl.col("source") == "ORPHANET")
    assert orphanet.height >= 1, "E84.8 doit avoir au moins une entrée ORPHANET"
    # Vérifie qu'au moins un texte ORPHANET parle de mucoviscidose.
    texts = orphanet["texte"].str.to_lowercase().to_list()
    assert any("mucoviscidose" in t for t in texts), (
        f"libellé 'mucoviscidose' attendu parmi les entrées ORPHANET ; "
        f"obtenu : {texts}"
    )


def test_d59_5_has_orphanet_synonym(csv_final_df: pl.DataFrame) -> None:
    """D59.5 (Hémoglobinurie paroxystique nocturne) doit avoir au
    moins une entrée ORPHANET de type synonyme."""
    sub = csv_final_df.filter(pl.col("code") == "D59.5")
    orphanet_syn = sub.filter(
        (pl.col("source") == "ORPHANET") & (pl.col("type") == "synonyme")
    )
    assert orphanet_syn.height >= 1, (
        "D59.5 doit avoir au moins une entrée synonyme ORPHANET"
    )


# ----------------------------------------------------------------------
# B. ORPHANET relation NTBT (inclusion)
# ----------------------------------------------------------------------


def test_q87_8_dominated_by_orphanet_inclusions(csv_final_df: pl.DataFrame) -> None:
    """Q87.8 (Autres syndromes congénitaux malformatifs précisés) est
    un code-fourre-tout dominé par ORPHANET NTBT — chaque syndrome
    rare précisé non classé ailleurs y est rangé."""
    sub = csv_final_df.filter(pl.col("code") == "Q87.8")
    assert sub.height > 500, f"Q87.8 attendu >500 entrées, obtenu {sub.height}"
    orphanet_inc = sub.filter(
        (pl.col("source") == "ORPHANET") & (pl.col("type") == "inclusion")
    )
    assert orphanet_inc.height > 500, (
        f"Q87.8 doit avoir >500 inclusions ORPHANET ; obtenu {orphanet_inc.height}"
    )
    # Majoritairement ORPHANET.
    assert orphanet_inc.height / sub.height > 0.8, (
        "Q87.8 doit être dominé (>80 %) par les inclusions ORPHANET"
    )


def test_e74_0_has_orphanet_ntbt_inclusions(csv_final_df: pl.DataFrame) -> None:
    """E74.0 (Thésaurismose glycogénique) doit avoir des inclusions
    ORPHANET (sous-classification des glycogénoses)."""
    sub = csv_final_df.filter(pl.col("code") == "E74.0")
    orphanet_inc = sub.filter(
        (pl.col("source") == "ORPHANET") & (pl.col("type") == "inclusion")
    )
    assert orphanet_inc.height >= 50, (
        f"E74.0 attendu >=50 inclusions ORPHANET, obtenu {orphanet_inc.height}"
    )


# ----------------------------------------------------------------------
# C. Index CIM-10 vol3
# ----------------------------------------------------------------------


def test_a52_7_dominated_by_index_synonyms(csv_final_df: pl.DataFrame) -> None:
    """A52.7 (Autres formes tardives de syphilis symptomatique) est
    le cas extrême de l'Index CIM-10 vol3 — la syphilis tardive a
    historiquement des centaines de manifestations cliniques nommées."""
    sub = csv_final_df.filter(pl.col("code") == "A52.7")
    assert sub.height > 1500, f"A52.7 attendu >1500 lignes, obtenu {sub.height}"
    index_syn = sub.filter(pl.col("source") == "CIM-10 index")
    assert index_syn.height > 1500, (
        f"A52.7 doit avoir >1500 synonymes Index ; obtenu {index_syn.height}"
    )


def test_i10_has_index_synonyms(csv_final_df: pl.DataFrame) -> None:
    """I10 (Hypertension essentielle) — code standard, sanity test
    de présence d'au moins un synonyme Index."""
    sub = csv_final_df.filter(pl.col("code") == "I10")
    index_syn = sub.filter(pl.col("source") == "CIM-10 index")
    assert index_syn.height >= 1, "I10 doit avoir au moins 1 synonyme Index"


# ----------------------------------------------------------------------
# D. Sources AP-HP
# ----------------------------------------------------------------------


def test_h22_0_has_aphp_ophtalmologie(csv_final_df: pl.DataFrame) -> None:
    """H22.0 doit porter au moins une entrée AP-HP Ophtalmologie
    (témoin du chargement de la feuille Ophtalmologie HECTOR)."""
    sub = csv_final_df.filter(pl.col("code") == "H22.0")
    aphp = sub.filter(pl.col("source") == "AP-HP Ophtalmologie")
    assert aphp.height >= 1, (
        "H22.0 doit avoir au moins une entrée AP-HP Ophtalmologie"
    )


def test_n08_5_has_aphp_nephrologie(csv_final_df: pl.DataFrame) -> None:
    """N08.5 doit porter au moins une entrée AP-HP Néphrologie
    (témoin du chargement de la feuille Néphrologie HECTOR)."""
    sub = csv_final_df.filter(pl.col("code") == "N08.5")
    aphp = sub.filter(pl.col("source") == "AP-HP Néphrologie")
    assert aphp.height >= 1, (
        "N08.5 doit avoir au moins une entrée AP-HP Néphrologie"
    )


# ----------------------------------------------------------------------
# E. Cohérence avec phases précédentes
# ----------------------------------------------------------------------


def test_a18_1_dagger_and_external_coexist(csv_final_df: pl.DataFrame) -> None:
    """A18.1 (côté dague de la paire A18.1+/N33.0*, subordinate)
    doit :
    - avoir ses caractéristiques dague préservées (asterisk_code
      rempli, is_redundant_dagger=True sur les lignes subordinate)
    - coexister avec des entrées externes (Index, AP-HP Néphro, ORPHANET).
    """
    sub = csv_final_df.filter(pl.col("code") == "A18.1")
    assert sub.height > 100, f"A18.1 attendu >100 lignes, obtenu {sub.height}"

    # Caractéristiques dague préservées (au moins 1 ligne subordinate).
    subordinate = sub.filter(pl.col("redundancy_level") == "subordinate")
    assert subordinate.height > 0, "A18.1 doit garder ses lignes subordinate"
    # Le côté dague subordinate a is_redundant_dagger=True.
    assert subordinate.filter(pl.col("is_redundant_dagger")).height > 0, (
        "A18.1 doit avoir des lignes dague marquées is_redundant_dagger=True"
    )
    # asterisk_code rempli sur les lignes dague.
    with_asterisk = sub.filter(pl.col("asterisk_code").is_not_null())
    assert with_asterisk.height > 0, (
        "A18.1 doit avoir des lignes avec asterisk_code rempli"
    )

    # Entrées externes présentes.
    sources = set(sub["source"].unique().to_list())
    assert "CIM-10 index" in sources, "A18.1 doit avoir des entrées CIM-10 index"
    assert sources & _EXTERNAL_SOURCES, (
        f"A18.1 doit avoir au moins une source externe parmi {_EXTERNAL_SOURCES}"
    )


def test_u07_10_no_external_entries(csv_final_df: pl.DataFrame) -> None:
    """U07.10 (COVID-19 forme respiratoire virus identifié) est un
    code post-2006 ANS-only. Les sources externes (ORPHANET 2025,
    Index CIM-10 vol3 2019, AP-HP HECTOR 2019) ne le référencent pas."""
    sub = csv_final_df.filter(pl.col("code") == "U07.10")
    assert sub.height > 0, "U07.10 doit être présent dans le CSV (ANS only)"
    sources = set(sub["source"].unique().to_list())
    external_present = sources & _EXTERNAL_SOURCES
    assert not external_present, (
        f"U07.10 ne doit avoir aucune entrée externe ; trouvé : {external_present}"
    )


# ----------------------------------------------------------------------
# F. Nouvelle catégorisation orphan
# ----------------------------------------------------------------------


def test_a90_not_in_csv_final(csv_final_df: pl.DataFrame) -> None:
    """A90 (Dengue, retiré par l'ATIH dans la FR-PMSI 2025) ne doit
    pas être dans le CSV final."""
    sub = csv_final_df.filter(pl.col("code") == "A90")
    assert sub.height == 0, (
        f"A90 ne doit pas être dans le CSV (orphan) ; obtenu {sub.height} lignes"
    )


def test_a90_classified_as_pre_2006_dropped_by_atih(
    orphan_report_df: pl.DataFrame,
) -> None:
    """A90 doit apparaître dans `reports/external_orphan_codes.csv`
    avec `categorie_orphan=pre_2006_dropped_by_atih` (présent OFS,
    absent ANS)."""
    sub = orphan_report_df.filter(pl.col("code") == "A90")
    assert sub.height > 0, "A90 doit apparaître dans le rapport orphan"
    cats = set(sub["categorie_orphan"].unique().to_list())
    assert cats == {"pre_2006_dropped_by_atih"}, (
        f"A90 doit être classé pre_2006_dropped_by_atih ; obtenu : {cats}"
    )


# ----------------------------------------------------------------------
# Cohérences globales
# ----------------------------------------------------------------------


def test_external_sources_never_fill_dagger_columns_for_non_paired_codes(
    csv_final_df: pl.DataFrame,
) -> None:
    """Les sources externes (ORPHANET, Index, AP-HP) ne fournissent
    pas d'information dague/astérisque par elles-mêmes.

    Pour les codes qui ne sont PAS membres d'une paire dague/astérisque
    (= `redundancy_level=none`), aucune entrée externe ne doit
    remplir `dagger_code` ou `asterisk_code`.

    Pour les codes membres d'une paire, les entrées externes héritent
    de l'expansion comme les autres — c'est testé séparément
    (`test_external_entries_inherit_subordinate_redundancy`)."""
    external_no_pair = csv_final_df.filter(
        pl.col("source").is_in(list(_EXTERNAL_SOURCES))
        & (pl.col("redundancy_level") == "none")
    )
    with_dagger = external_no_pair.filter(pl.col("dagger_code").is_not_null())
    with_asterisk = external_no_pair.filter(pl.col("asterisk_code").is_not_null())
    assert with_dagger.is_empty(), (
        f"{with_dagger.height} entrées externes hors paire ont un "
        f"dagger_code — incohérent"
    )
    assert with_asterisk.is_empty(), (
        f"{with_asterisk.height} entrées externes hors paire ont un "
        f"asterisk_code — incohérent"
    )


def test_external_entries_inherit_subordinate_redundancy(
    csv_final_df: pl.DataFrame,
) -> None:
    """Les entrées externes ajoutées sur des codes membres de paires
    subordinate héritent de `redundancy_level=subordinate` après
    expansion dague/astérisque. Témoin : A18.1 (dague subordinate)."""
    a18_external = csv_final_df.filter(
        (pl.col("code") == "A18.1")
        & pl.col("source").is_in(list(_EXTERNAL_SOURCES))
    )
    assert a18_external.height > 0, (
        "A18.1 doit avoir des entrées externes pour valider l'héritage"
    )
    subordinate_external = a18_external.filter(
        pl.col("redundancy_level") == "subordinate"
    )
    assert subordinate_external.height > 0, (
        "Les entrées externes sur A18.1 doivent hériter de subordinate"
    )


def test_csv_final_schema_unchanged(csv_final_df: pl.DataFrame) -> None:
    """Le CSV final a toujours exactement 9 colonnes (régression
    contre l'ajout silencieux d'une colonne)."""
    expected = [
        "code",
        "libelle",
        "type",
        "source",
        "texte",
        "dagger_code",
        "asterisk_code",
        "redundancy_level",
        "is_redundant_dagger",
    ]
    assert csv_final_df.columns == expected, (
        f"colonnes inattendues : {csv_final_df.columns} vs {expected}"
    )
