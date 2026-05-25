"""Tests d'intégration de Phase 2 — merge externe.

Utilisent les fixtures `conftest.py` (mini-pipeline 10 codes) pour
couvrir les cas critiques de la dédup tolérante, du logging
overlaps/orphans, et de l'intégration au CSV final.
"""

from __future__ import annotations

import polars as pl
import pytest

from recode_icd import merge_external
from recode_icd.exporters import flat_csv

pytestmark = pytest.mark.integration


@pytest.fixture
def merge_result(
    propagated_df: pl.DataFrame,
    owl_df: pl.DataFrame,
    ofs_df: pl.DataFrame,
    siblings_df: pl.DataFrame,
    merged_df: pl.DataFrame,
    post_2006_codes_df: pl.DataFrame,
    external_frames: dict[str, pl.DataFrame],
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    leaves = merged_df.filter(
        (pl.col("type") == "category") & ((pl.col("right") - pl.col("left")) == 1)
    ).select("code", pl.col("label").alias("libelle"))
    valid_codes = merged_df.select("code")
    return merge_external.merge_external_sources(
        propagated=propagated_df,
        owl=owl_df,
        ofs=ofs_df,
        siblings=siblings_df,
        leaves=leaves,
        valid_codes=valid_codes,
        post_2006_codes=post_2006_codes_df,
        external_frames=external_frames,
    )


# ----------------------------------------------------------------------
# Tests fondamentaux du merge
# ----------------------------------------------------------------------


def test_orphanet_E_relations_in_final_csv(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """ORPHANET relation E (D59.5 / HPN) doit aboutir comme synonyme."""
    to_add, _, _, _ = merge_result
    hpn = to_add.filter(
        (pl.col("code") == "D59.5") & (pl.col("source") == "ORPHANET")
        & (pl.col("libelle_orig") == "HPN")
    )
    assert hpn.height == 1
    assert hpn.row(0, named=True)["type"] == "synonyme"


def test_orphanet_NTBT_as_inclusion(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """ORPHANET relation NTBT (A01.0 / Salmonella typhi) doit aboutir
    comme inclusion."""
    to_add, _, _, _ = merge_result
    row = to_add.filter(
        (pl.col("code") == "A01.0") & (pl.col("libelle_orig") == "Infection à Salmonella typhi")
    )
    assert row.height == 1
    assert row.row(0, named=True)["type"] == "inclusion"


def test_absorbed_when_match_ofs(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """A00.0 / 'Choléra classique' existe comme inclusion OFS → doit
    être absorbé (pas dans to_add) et loggé dans overlaps."""
    to_add, overlaps, _, _ = merge_result
    assert to_add.filter(
        (pl.col("code") == "A00.0") & (pl.col("libelle_orig") == "Choléra classique")
    ).is_empty()
    ov = overlaps.filter(
        (pl.col("code") == "A00.0")
        & (pl.col("libelle_externe") == "Choléra classique")
    )
    assert ov.height == 1
    row = ov.row(0, named=True)
    assert row["source_ofs_ans"] == "OFS"
    assert row["type_ofs_ans"] == "inclusion"


def test_absorbed_when_match_ans_synonym(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """Index CIM-10 'asiatic cholera' matche le synonyme ANS
    'Asiatic cholera' (dédup tolérante casse/accent)."""
    to_add, overlaps, _, _ = merge_result
    assert to_add.filter(
        (pl.col("code") == "A00.0") & (pl.col("libelle_orig") == "asiatic cholera")
    ).is_empty()
    ov = overlaps.filter(
        (pl.col("code") == "A00.0") & (pl.col("libelle_externe") == "asiatic cholera")
    )
    assert ov.height == 1


def test_absorbed_inter_externes_orphanet_wins_over_aphp(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """ORPHANET ajoute "HPN" pour D59.5 ; AP-HP propose la même paire.
    AP-HP doit être absorbé avec source_ofs_ans=ORPHANET dans l'overlap."""
    to_add, overlaps, _, _ = merge_result
    # On a 1 entrée "HPN" (celle d'ORPHANET), pas 2.
    hpn = to_add.filter(
        (pl.col("code") == "D59.5") & (pl.col("libelle_orig") == "HPN")
    )
    assert hpn.height == 1
    assert hpn.row(0, named=True)["source"] == "ORPHANET"

    # AP-HP "HPN" est dans overlaps avec source_ofs_ans=ORPHANET.
    aphp_ov = overlaps.filter(
        (pl.col("source_externe") == "APHP_DERMATOLOGIE")
        & (pl.col("libelle_externe") == "HPN")
    )
    assert aphp_ov.height == 1
    assert aphp_ov.row(0, named=True)["source_ofs_ans"] == "ORPHANET"


def test_absorbed_inter_externes_orphanet_wins_over_index(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """Idem mais Index CIM-10 propose HPN après ORPHANET — Index absorbé."""
    _, overlaps, _, _ = merge_result
    idx_ov = overlaps.filter(
        (pl.col("source_externe") == "INDEX_CIM10_VOL3")
        & (pl.col("libelle_externe") == "HPN")
    )
    assert idx_ov.height == 1
    assert idx_ov.row(0, named=True)["source_ofs_ans"] == "ORPHANET"


def test_orphan_codes_logged_not_added(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """X99.9 n'existe pas dans merged → loggé comme orphan, pas dans to_add."""
    to_add, _, orphans, _ = merge_result
    assert to_add.filter(pl.col("code") == "X99.9").is_empty()
    orph = orphans.filter(pl.col("code") == "X99.9")
    assert orph.height == 1
    assert orph.row(0, named=True)["categorie_orphan"] == "vraiment_orphan"


def test_non_terminal_silently_dropped_but_counted(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """U07.1 existe dans merged (donc PAS orphan) mais n'est pas leaf →
    `entries_dropped_non_terminal=1` dans summary, pas dans orphans."""
    _, _, orphans, summary = merge_result
    assert orphans.filter(pl.col("code") == "U07.1").is_empty()
    orphanet_row = summary.filter(pl.col("source") == "ORPHANET").row(0, named=True)
    assert orphanet_row["entries_dropped_non_terminal"] == 1


def test_summary_volumetry_consistent(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """Pour chaque source : loaded = absorbed + orphan + non_terminal + added."""
    _, _, _, summary = merge_result
    for row in summary.iter_rows(named=True):
        total = (
            row["entries_absorbed"]
            + row["entries_orphan"]
            + row["entries_dropped_non_terminal"]
            + row["entries_added_to_csv"]
        )
        assert total == row["entries_loaded"], f"incohérence pour {row['source']}: {row}"


def test_overlaps_logs_type_divergence(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """ORPHANET ajoute A00.0 / 'Choléra classique' comme inclusion ;
    OFS a aussi A00.0 / 'Choléra classique' comme inclusion : type_divergence=False.

    Test orthogonal : si on ajoute une entrée externe synonyme qui matche
    une inclusion OFS, type_divergence doit être True. On utilise la
    réalité de la fixture : A01.0 a une exclusion OWL_ANS 'Porteur de la
    typhoïde', et ORPHANET ne propose rien qui matche ici. On teste donc
    plutôt la mécanique sur l'entrée existante.
    """
    _, overlaps, _, _ = merge_result
    chol_ov = overlaps.filter(
        (pl.col("code") == "A00.0") & (pl.col("libelle_externe") == "Choléra classique")
    ).row(0, named=True)
    # ORPHANET émet type=inclusion ; OFS aussi inclusion → divergence=False.
    assert chol_ov["type_externe"] == "inclusion"
    assert chol_ov["type_ofs_ans"] == "inclusion"
    assert chol_ov["type_divergence"] is False


def test_dedup_index_includes_propagated_and_synonymes(
    propagated_df: pl.DataFrame,
    owl_df: pl.DataFrame,
    ofs_df: pl.DataFrame,
    siblings_df: pl.DataFrame,
) -> None:
    """L'index couvre bien inclusions+exclusions+synonymes OFS+ANS+synth."""
    idx = merge_external.build_dedup_index(propagated_df, owl_df, ofs_df, siblings_df)
    # propagated inclusion "Choléra classique"
    assert idx.filter(
        (pl.col("code") == "A00.0") & (pl.col("source") == "OFS")
        & (pl.col("note_type") == "inclusion")
    ).height == 1
    # synonyme OWL A00.0 "Asiatic cholera"
    assert idx.filter(
        (pl.col("code") == "A00.0") & (pl.col("source") == "OWL_ANS")
        & (pl.col("note_type") == "synonyme")
    ).height >= 1
    # synonyme OFS A01.0 "Typhoïde"
    assert idx.filter(
        (pl.col("code") == "A01.0") & (pl.col("source") == "OFS")
        & (pl.col("note_type") == "synonyme")
    ).height == 1


# ----------------------------------------------------------------------
# Tests d'intégration au CSV final via flat_csv.build()
# ----------------------------------------------------------------------


def test_csv_final_schema_unchanged_after_external_merge(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
    merged_df: pl.DataFrame,
    propagated_df: pl.DataFrame,
    siblings_df: pl.DataFrame,
    owl_df: pl.DataFrame,
    ofs_df: pl.DataFrame,
    dagger_asterisk_df: pl.DataFrame,
) -> None:
    """Le CSV final conserve ses 9 colonnes après intégration externe."""
    to_add, _, _, _ = merge_result
    df, _ = flat_csv.build(
        merged=merged_df,
        propagated=propagated_df,
        siblings=siblings_df,
        owl=owl_df,
        ofs=ofs_df,
        dagger_asterisk=dagger_asterisk_df,
        external=to_add,
    )
    expected_columns = [
        "code", "libelle", "type", "source", "texte",
        "dagger_code", "asterisk_code", "redundancy_level", "is_redundant_dagger",
    ]
    assert df.columns == expected_columns


def test_csv_final_contains_orphanet_E(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
    merged_df: pl.DataFrame,
    propagated_df: pl.DataFrame,
    siblings_df: pl.DataFrame,
    owl_df: pl.DataFrame,
    ofs_df: pl.DataFrame,
    dagger_asterisk_df: pl.DataFrame,
) -> None:
    """HPN (D59.5, ORPHANET E) doit apparaître dans le CSV avec
    source CSV='ORPHANET' et type=synonyme."""
    to_add, _, _, _ = merge_result
    df, _ = flat_csv.build(
        merged=merged_df,
        propagated=propagated_df,
        siblings=siblings_df,
        owl=owl_df,
        ofs=ofs_df,
        dagger_asterisk=dagger_asterisk_df,
        external=to_add,
    )
    hpn = df.filter((pl.col("code") == "D59.5") & (pl.col("texte") == "HPN"))
    assert hpn.height >= 1
    assert hpn.row(0, named=True)["source"] == "ORPHANET"
    assert hpn.row(0, named=True)["type"] == "synonyme"


def test_csv_final_contains_aphp_with_french_label(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
    merged_df: pl.DataFrame,
    propagated_df: pl.DataFrame,
    siblings_df: pl.DataFrame,
    owl_df: pl.DataFrame,
    ofs_df: pl.DataFrame,
    dagger_asterisk_df: pl.DataFrame,
) -> None:
    """L'entrée AP-HP Dermatologie ajoutée (C50.8 tumeur du sein) doit
    apparaître avec source='AP-HP Dermatologie'."""
    to_add, _, _, _ = merge_result
    df, _ = flat_csv.build(
        merged=merged_df,
        propagated=propagated_df,
        siblings=siblings_df,
        owl=owl_df,
        ofs=ofs_df,
        dagger_asterisk=dagger_asterisk_df,
        external=to_add,
    )
    aphp = df.filter(
        (pl.col("code") == "C50.8")
        & (pl.col("texte") == "Tumeur du sein, sites multiples")
    )
    assert aphp.height >= 1
    assert aphp.row(0, named=True)["source"] == "AP-HP Dermatologie"


def test_csv_final_external_inherits_redundancy_level_none(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
    merged_df: pl.DataFrame,
    propagated_df: pl.DataFrame,
    siblings_df: pl.DataFrame,
    owl_df: pl.DataFrame,
    ofs_df: pl.DataFrame,
    dagger_asterisk_df: pl.DataFrame,
) -> None:
    """Les entrées externes pour des codes hors paire dague/astérisque
    héritent de redundancy_level='none' et is_redundant_dagger=False."""
    to_add, _, _, _ = merge_result
    df, _ = flat_csv.build(
        merged=merged_df,
        propagated=propagated_df,
        siblings=siblings_df,
        owl=owl_df,
        ofs=ofs_df,
        dagger_asterisk=dagger_asterisk_df,
        external=to_add,
    )
    hpn = df.filter((pl.col("code") == "D59.5") & (pl.col("texte") == "HPN")).row(0, named=True)
    assert hpn["redundancy_level"] == "none"
    assert hpn["is_redundant_dagger"] is False
    assert hpn["dagger_code"] is None
    assert hpn["asterisk_code"] is None


def test_build_without_external_unchanged(
    merged_df: pl.DataFrame,
    propagated_df: pl.DataFrame,
    siblings_df: pl.DataFrame,
    owl_df: pl.DataFrame,
    ofs_df: pl.DataFrame,
    dagger_asterisk_df: pl.DataFrame,
) -> None:
    """Rétro-compatibilité : appeler `build()` sans external doit
    fonctionner exactement comme avant Phase 2."""
    df, _ = flat_csv.build(
        merged=merged_df,
        propagated=propagated_df,
        siblings=siblings_df,
        owl=owl_df,
        ofs=ofs_df,
        dagger_asterisk=dagger_asterisk_df,
    )
    # CSV non vide (au moins l'inclusion A00.0 et le synonyme A01.0).
    assert df.height >= 1
    assert df.columns[0] == "code"
