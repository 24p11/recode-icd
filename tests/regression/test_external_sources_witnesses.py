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
    "CepiDc_2015",
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
    """A52.7 (Autres formes tardives de syphilis symptomatique) reste
    le cas riche en synonymes Index CIM-10 vol3. Refonte 2026-05-30 :
    sans expansion par paire, A52.7 passe de ~2478 à ~150 lignes Index
    (×12 paires éliminées). Reste dominé par l'Index."""
    sub = csv_final_df.filter(pl.col("code") == "A52.7")
    assert sub.height > 100, f"A52.7 attendu >100 lignes, obtenu {sub.height}"
    index_syn = sub.filter(pl.col("source") == "CIM-10 index")
    assert index_syn.height > 100, (
        f"A52.7 doit avoir >100 synonymes Index ; obtenu {index_syn.height}"
    )
    # L'Index doit toujours dominer (majorité des lignes).
    assert index_syn.height / sub.height > 0.5, (
        f"A52.7 doit être dominé par l'Index ; obtenu {100*index_syn.height/sub.height:.0f} %"
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
    """A18.1 (code dague de paires DAGSTAR avec N33.0 et 9 autres) doit :
    - avoir `is_dagger_in_pair=True` sur toutes ses lignes (refonte
      2026-05-30 : le détail des paires est dans dagger_asterisk.parquet,
      plus dans le CSV)
    - coexister avec des entrées externes (Index, AP-HP Néphro, ORPHANET).
    """
    sub = csv_final_df.filter(pl.col("code") == "A18.1")
    assert sub.height > 50, f"A18.1 attendu >50 lignes, obtenu {sub.height}"

    # Flag dague True sur toutes les lignes (propriété du code, pas de la ligne).
    assert sub.filter(~pl.col("is_dagger_in_pair")).is_empty(), (
        "A18.1 doit avoir is_dagger_in_pair=True sur toutes ses lignes"
    )
    # A18.1 n'est jamais côté astérisque.
    assert sub.filter(pl.col("is_asterisk_in_pair")).is_empty(), (
        "A18.1 ne doit jamais avoir is_asterisk_in_pair=True"
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
# G. Propagation hiérarchique (Chantier A)
# ----------------------------------------------------------------------


def test_e80_7_propagation_levels(csv_final_df: pl.DataFrame) -> None:
    """E80.7 (Anomalie du métabolisme de la bilirubine) illustre les
    4 niveaux de source_level : une note propre (code), une héritée de
    la catégorie E80, une du bloc E70-E90, une du chapitre IV.

    Vérifie que source_level et inherited_from_code sont cohérents."""
    sub = csv_final_df.filter(pl.col("code") == "E80.7")
    assert sub.height > 0, "E80.7 doit être présent dans le CSV"
    levels = set(sub["source_level"].unique().to_list())
    # Au moins les niveaux propagés block et chapter doivent être présents
    # (la composition exacte peut bouger, on exige la diversité).
    assert "code" in levels, "E80.7 doit avoir au moins une note propre (code)"
    assert len(levels) >= 3, (
        f"E80.7 doit illustrer plusieurs niveaux de propagation ; obtenu : {levels}"
    )

    # Cohérence inherited_from_code pour les notes propagées.
    block_notes = sub.filter(pl.col("source_level") == "block")
    if block_notes.height > 0:
        parents = set(block_notes["inherited_from_code"].unique().to_list())
        assert parents == {"E70-E90"}, (
            f"notes block de E80.7 doivent venir de E70-E90 ; obtenu : {parents}"
        )
    chapter_notes = sub.filter(pl.col("source_level") == "chapter")
    if chapter_notes.height > 0:
        parents = set(chapter_notes["inherited_from_code"].unique().to_list())
        assert parents == {"IV"}, (
            f"notes chapter de E80.7 doivent venir du chapitre IV ; obtenu : {parents}"
        )


# ----------------------------------------------------------------------
# Cohérences globales
# ----------------------------------------------------------------------


def test_external_entries_propagate_dagger_flags_from_code(
    csv_final_df: pl.DataFrame,
) -> None:
    """Refonte 2026-05-30 : les flags is_dagger_in_pair /
    is_asterisk_in_pair sont calculés au niveau du code (propriété du
    code, pas de la ligne). Donc une entrée externe sur un code dague
    porte aussi is_dagger_in_pair=True, sans que l'expansion par paire
    ne soit faite.

    Témoin : A18.1 (dague), toutes ses lignes (y compris externes) ont
    is_dagger_in_pair=True.
    """
    a18_external = csv_final_df.filter(
        (pl.col("code") == "A18.1")
        & pl.col("source").is_in(list(_EXTERNAL_SOURCES))
    )
    assert a18_external.height > 0, (
        "A18.1 doit avoir des entrées externes pour valider la propagation des flags"
    )
    assert a18_external.filter(~pl.col("is_dagger_in_pair")).is_empty(), (
        "toutes les entrées externes sur A18.1 doivent avoir is_dagger_in_pair=True"
    )


# ----------------------------------------------------------------------
# F. CepiDc 2015 (formulations vie réelle, certificats de décès)
# ----------------------------------------------------------------------


def test_r51_has_cepidc_synonyms(csv_final_df: pl.DataFrame) -> None:
    """R51 (Céphalée) doit porter plusieurs entrées CepiDc (formulations
    télégraphiques de certificats de décès) — au moins une dizaine."""
    cepidc = csv_final_df.filter(
        (pl.col("code") == "R51") & (pl.col("source") == "CepiDc_2015")
    )
    assert cepidc.height >= 10, (
        f"R51 doit avoir au moins 10 entrées CepiDc ; obtenu {cepidc.height}"
    )
    # Toutes en type=synonyme.
    assert set(cepidc["type"].unique().to_list()) == {"synonyme"}


def test_cepidc_global_volumetry(csv_final_df: pl.DataFrame) -> None:
    """CepiDc doit représenter ~120 000 lignes du CSV (mesuré : ~121 426
    avant absorption inter-externes). On accepte une fourchette ±10 %."""
    cepidc = csv_final_df.filter(pl.col("source") == "CepiDc_2015")
    assert 100_000 <= cepidc.height <= 135_000, (
        f"volumétrie CepiDc inattendue : {cepidc.height}"
    )


def test_cepidc_all_synonyme(csv_final_df: pl.DataFrame) -> None:
    """Toutes les entrées CepiDc dans le CSV sont en type=synonyme."""
    cepidc = csv_final_df.filter(pl.col("source") == "CepiDc_2015")
    assert set(cepidc["type"].unique().to_list()) == {"synonyme"}


def test_csv_final_schema_unchanged(csv_final_df: pl.DataFrame) -> None:
    """Refonte 2026-05-30 : le CSV a 9 colonnes (au lieu de 11). Les
    colonnes dague/astérisque détaillées (dagger_code, asterisk_code,
    redundancy_level, is_redundant_dagger) ont été remplacées par 2
    flags booléens (is_dagger_in_pair, is_asterisk_in_pair). Le détail
    des paires vit désormais exclusivement dans
    dagger_asterisk.parquet."""
    expected = [
        "code",
        "libelle",
        "type",
        "source",
        "texte",
        "source_level",
        "inherited_from_code",
        "is_dagger_in_pair",
        "is_asterisk_in_pair",
    ]
    assert csv_final_df.columns == expected, (
        f"colonnes inattendues : {csv_final_df.columns} vs {expected}"
    )


def test_external_entries_have_source_level_code(csv_final_df: pl.DataFrame) -> None:
    """Toutes les entrées de sources externes ont source_level=code et
    inherited_from_code vide (les sources externes ne propagent pas)."""
    external = csv_final_df.filter(pl.col("source").is_in(list(_EXTERNAL_SOURCES)))
    bad_level = external.filter(pl.col("source_level") != "code")
    assert bad_level.is_empty(), (
        f"{bad_level.height} entrées externes avec source_level != code"
    )
    bad_parent = external.filter(pl.col("inherited_from_code").is_not_null())
    assert bad_parent.is_empty(), (
        f"{bad_parent.height} entrées externes avec inherited_from_code rempli"
    )


def test_source_level_always_filled(csv_final_df: pl.DataFrame) -> None:
    """source_level n'est JAMAIS null (valeur 'code' par défaut)."""
    assert csv_final_df.filter(pl.col("source_level").is_null()).is_empty()
    valid = {"chapter", "block", "category", "code"}
    observed = set(csv_final_df["source_level"].unique().to_list())
    assert observed.issubset(valid), f"valeurs source_level invalides : {observed - valid}"


def test_inherited_from_code_consistent_with_source_level(
    csv_final_df: pl.DataFrame,
) -> None:
    """inherited_from_code rempli ⟺ source_level != code."""
    # source_level=code → inherited_from_code doit être null.
    code_level = csv_final_df.filter(pl.col("source_level") == "code")
    assert code_level.filter(pl.col("inherited_from_code").is_not_null()).is_empty(), (
        "source_level=code ne doit jamais avoir inherited_from_code rempli"
    )
    # source_level != code → inherited_from_code doit être rempli.
    propagated = csv_final_df.filter(pl.col("source_level") != "code")
    assert propagated.filter(pl.col("inherited_from_code").is_null()).is_empty(), (
        "source_level propagé doit toujours avoir inherited_from_code rempli"
    )
