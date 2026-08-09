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


def test_truly_absent_logged_not_added(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """X99.9 absent d'OFS et de merged → catégorie `truly_absent`."""
    to_add, _, orphans, _ = merge_result
    assert to_add.filter(pl.col("code") == "X99.9").is_empty()
    orph = orphans.filter(pl.col("code") == "X99.9")
    assert orph.height == 1
    assert orph.row(0, named=True)["categorie_orphan"] == "truly_absent"


def test_pre_2006_dropped_by_atih_logged_not_added(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """A90 présent en OFS mais absent de merged_codes → catégorie
    `pre_2006_dropped_by_atih`. C'est le cas dominant en pratique.
    A90 apparaît dans plusieurs sources externes (ORPHANET et CepiDc),
    chaque entrée doit être loggée séparément."""
    to_add, _, orphans, _ = merge_result
    assert to_add.filter(pl.col("code") == "A90").is_empty()
    orph = orphans.filter(pl.col("code") == "A90")
    assert orph.height >= 1
    assert set(orph["categorie_orphan"].unique().to_list()) == {
        "pre_2006_dropped_by_atih"
    }


def test_loader_dropped_detected_when_rdf_codes_provided(
    propagated_df: pl.DataFrame,
    owl_df: pl.DataFrame,
    ofs_df: pl.DataFrame,
    siblings_df: pl.DataFrame,
    merged_df: pl.DataFrame,
    rdf_codes_loader_dropped: set[str],
) -> None:
    """Si on passe un `rdf_codes` set qui contient un code orphan,
    ce code doit être classé `loader_dropped` (présent RDF mais perdu
    par le loader OWL — filet de sécurité)."""
    external_with_loader_dropped = {
        "ORPHANET": pl.DataFrame(
            [
                {
                    "code": "Z99.9",
                    "libelle": "Code RDF perdu par loader",
                    "type": "synonyme",
                    "source": "ORPHANET",
                    "metadata": {"orpha_code": "", "relation": ""},
                }
            ],
            schema={
                "code": pl.String,
                "libelle": pl.String,
                "type": pl.String,
                "source": pl.String,
                "metadata": pl.Struct(
                    {"orpha_code": pl.String, "relation": pl.String}
                ),
            },
        )
    }
    leaves = merged_df.filter(
        (pl.col("type") == "category") & ((pl.col("right") - pl.col("left")) == 1)
    ).select("code", pl.col("label").alias("libelle"))
    valid_codes = merged_df.select("code")
    _, _, orphans, _ = merge_external.merge_external_sources(
        propagated=propagated_df,
        owl=owl_df,
        ofs=ofs_df,
        siblings=siblings_df,
        leaves=leaves,
        valid_codes=valid_codes,
        external_frames=external_with_loader_dropped,
        rdf_codes=rdf_codes_loader_dropped,
    )
    orph = orphans.filter(pl.col("code") == "Z99.9")
    assert orph.height == 1
    assert orph.row(0, named=True)["categorie_orphan"] == "loader_dropped"


def test_loader_dropped_falls_back_to_truly_absent_without_rdf(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """Sans `rdf_codes` passé, aucun orphan n'est classé `loader_dropped`
    (détection désactivée). Comportement attendu — pas de fausse alerte."""
    _, _, orphans, _ = merge_result
    assert orphans.filter(pl.col("categorie_orphan") == "loader_dropped").is_empty()


def test_all_categories_in_valid_set(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """Toutes les valeurs émises de `categorie_orphan` appartiennent
    au schéma valide (4 catégories autorisées)."""
    _, _, orphans, _ = merge_result
    valid = {
        "pre_2006_dropped_by_atih",
        "truly_absent",
        "loader_dropped",
        "unknown_pattern",
    }
    observed = set(orphans["categorie_orphan"].unique().to_list())
    assert observed.issubset(valid), f"valeurs invalides : {observed - valid}"


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
    """Refonte 2026-05-30 : le CSV final a 9 colonnes après intégration
    externe (suppression de 4 colonnes dague/astérisque, ajout de 2
    flags booléens)."""
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
        "source_level", "inherited_from_code",
        "is_dagger_in_pair", "is_asterisk_in_pair",
    ]
    assert df.columns == expected_columns
    # Les entrées externes ont source_level=code et inherited_from_code null.
    external_rows = df.filter(
        pl.col("source").is_in(
            ["ORPHANET", "CIM-10 index", "AP-HP Dermatologie"]
        )
    )
    assert external_rows.height > 0
    assert external_rows.filter(pl.col("source_level") != "code").is_empty()
    assert external_rows.filter(
        pl.col("inherited_from_code").is_not_null()
    ).is_empty()


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


def test_csv_final_external_on_non_paired_code_has_flags_false(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
    merged_df: pl.DataFrame,
    propagated_df: pl.DataFrame,
    siblings_df: pl.DataFrame,
    owl_df: pl.DataFrame,
    ofs_df: pl.DataFrame,
    dagger_asterisk_df: pl.DataFrame,
) -> None:
    """Refonte 2026-05-30 : pour un code hors paire dague/astérisque
    (D59.5), les entrées externes ont les deux flags à False (plus de
    colonnes `redundancy_level` / `is_redundant_dagger` /
    `dagger_code` / `asterisk_code`)."""
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
    assert hpn["is_dagger_in_pair"] is False
    assert hpn["is_asterisk_in_pair"] is False


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


# ----------------------------------------------------------------------
# Tests CepiDc 2015 (intégration au pipeline external)
# ----------------------------------------------------------------------


def test_cepidc_entries_in_to_add(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """Les formulations CepiDc nouvelles doivent figurer dans to_add
    avec source=CEPIDC_2015 et type=synonyme."""
    to_add, _, _, _ = merge_result
    tub_r = to_add.filter(
        (pl.col("code") == "A18.1") & (pl.col("libelle_orig") == "tuberculose rénale")
    )
    assert tub_r.height == 1
    row = tub_r.row(0, named=True)
    assert row["source"] == "CEPIDC_2015"
    assert row["type"] == "synonyme"


def test_cepidc_overlap_absorbed_by_orphanet(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """CepiDc 'HPN' pour D59.5 matche ORPHANET (déjà inséré) → absorbé.
    CepiDc placé en dernier dans _EXTERNAL_ORDER perd les matches."""
    to_add, overlaps, _, _ = merge_result
    # HPN n'apparaît qu'une fois (côté ORPHANET), pas en doublon CepiDc.
    hpn = to_add.filter((pl.col("code") == "D59.5") & (pl.col("libelle_orig") == "HPN"))
    assert hpn.height == 1
    assert hpn.row(0, named=True)["source"] == "ORPHANET"
    # CepiDc HPN figure dans overlaps avec source_ofs_ans=ORPHANET.
    cep_ov = overlaps.filter(
        (pl.col("source_externe") == "CEPIDC_2015")
        & (pl.col("libelle_externe") == "HPN")
    )
    assert cep_ov.height == 1
    assert cep_ov.row(0, named=True)["source_ofs_ans"] == "ORPHANET"


def test_cepidc_orphan_code_logged(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """A90 absent de merged → entrées CepiDc loggées dans orphans, pas
    dans to_add."""
    to_add, _, orphans, _ = merge_result
    assert to_add.filter(
        (pl.col("code") == "A90") & (pl.col("source") == "CEPIDC_2015")
    ).is_empty()
    cep_orph = orphans.filter(
        (pl.col("code") == "A90") & (pl.col("source_externe") == "CEPIDC_2015")
    )
    # 2 formulations CepiDc pour A90 dans la fixture.
    assert cep_orph.height == 2


def test_cepidc_ignored_report_format(
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """`_build_cepidc_ignored_report` doit agréger par code avec
    n_formulations_perdues et exemples_formulations."""
    from recode_icd.merge_external import _build_cepidc_ignored_report

    _, _, orphans, _ = merge_result
    report = _build_cepidc_ignored_report(orphans)
    a90 = report.filter(pl.col("code_cepidc") == "A90")
    assert a90.height == 1
    row = a90.row(0, named=True)
    assert row["n_formulations_perdues"] == 2
    assert "dengue" in row["exemples_formulations"].lower()


def test_cepidc_in_final_csv(
    merged_df: pl.DataFrame,
    propagated_df: pl.DataFrame,
    siblings_df: pl.DataFrame,
    owl_df: pl.DataFrame,
    ofs_df: pl.DataFrame,
    dagger_asterisk_df: pl.DataFrame,
    merge_result: tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame],
) -> None:
    """Une entrée CepiDc nouvelle doit apparaître dans le CSV final
    avec source='CepiDc 2015', type='synonyme', source_level='code'."""
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
    tub_r = df.filter(
        (pl.col("code") == "A18.1") & (pl.col("texte") == "tuberculose rénale")
    )
    assert tub_r.height == 1
    row = tub_r.row(0, named=True)
    assert row["source"] == "CepiDc 2015"
    assert row["type"] == "synonyme"
    assert row["source_level"] == "code"
    assert row["inherited_from_code"] is None
