"""Régression sur le CSV maître à 9 colonnes (Phase 3).

Skip si le CSV `referentials/processed/inclusions_exclusions_synonymes.csv`
n'est pas présent ou n'a pas le bon nombre de colonnes — le test n'a de
sens qu'après un `recode-icd build flat-csv` complet."""

from __future__ import annotations

from functools import cache
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.regression


_CSV_PATH = Path("referentials/processed/inclusions_exclusions_synonymes.csv")
_EXPECTED_COLUMNS = [
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


@cache
def _final_csv() -> pl.DataFrame:
    root = Path(__file__).resolve().parents[2]
    path = root / _CSV_PATH
    if not path.is_file():
        pytest.skip(f"CSV maître absent ({path}) — lance `build flat-csv` d'abord.")
    df = pl.read_csv(path, infer_schema_length=10_000)
    if list(df.columns) != _EXPECTED_COLUMNS:
        pytest.skip(
            f"CSV présent mais schéma différent (colonnes : {df.columns}). "
            "Re-générer après les changements de schéma."
        )
    return df


def test_csv_has_9_columns() -> None:
    assert list(_final_csv().columns) == _EXPECTED_COLUMNS


def test_a17_8_is_dagger_in_pair() -> None:
    """Refonte 2026-05-30 : A17.8 (côté dague de la paire avec G05.0,
    subordinate selon la curation) doit avoir `is_dagger_in_pair=True`
    sur toutes ses lignes. Le détail de la subordinate vit désormais
    dans dagger_asterisk.parquet, plus dans le CSV."""
    df = _final_csv()
    subset = df.filter(pl.col("code") == "A17.8")
    if subset.is_empty():
        pytest.skip("A17.8 absent du CSV final.")
    assert subset.filter(~pl.col("is_dagger_in_pair")).is_empty(), (
        "A17.8 doit avoir is_dagger_in_pair=True sur toutes ses lignes"
    )


def test_e10_2_is_dagger_in_pair() -> None:
    """Refonte 2026-05-30 : E10.2 (côté dague de la paire avec N08.3,
    independent) doit avoir `is_dagger_in_pair=True`."""
    df = _final_csv()
    subset = df.filter(pl.col("code") == "E10.2")
    if subset.is_empty():
        pytest.skip("E10.2 absent du CSV final.")
    assert subset.filter(~pl.col("is_dagger_in_pair")).is_empty(), (
        "E10.2 doit avoir is_dagger_in_pair=True sur toutes ses lignes"
    )


def test_a18_1_ans_exclusion_redirects_use_parentheses() -> None:
    """Chantier 4 (2026-06-03) : les codes de redirection ANS des
    exclusions de A18.1 doivent apparaître entre parenthèses et plus
    entre crochets dans le CSV final."""
    df = _final_csv()
    subset = df.filter(
        (pl.col("code") == "A18.1") & (pl.col("type") == "exclusion") & (pl.col("source") == "ANS")
    )
    if subset.is_empty():
        pytest.skip("A18.1 sans exclusion ANS dans le CSV final.")
    joined = " || ".join(subset["texte"].drop_nulls().to_list())
    for code in ("B20.0", "J65", "B90.-", "P37.0"):
        assert f"[{code}]" not in joined, (
            f"crochet [{code}] résiduel dans A18.1 — normalisation incomplète"
        )
        assert f"({code})" in joined, f"redirection ({code}) attendue dans A18.1"


def test_u07_13_ans_exclusion_redirects_use_parentheses() -> None:
    """Chantier 4 (2026-06-03) : les codes post-2006 (ANS exclusivement)
    doivent voir leurs redirections normalisées en parenthèses.

    Témoin U07.13, feuille du bloc COVID. Les trois redirections
    vérifiées lui sont propagées depuis U07.1 (`source_level=category`),
    qui est lui-même absent du CSV — cf `test_u07_1_absent_du_csv`.
    """
    df = _final_csv()
    subset = df.filter(
        (pl.col("code") == "U07.13") & (pl.col("type") == "exclusion") & (pl.col("source") == "ANS")
    )
    assert not subset.is_empty(), "U07.13 sans exclusion ANS dans le CSV final."
    joined = " || ".join(subset["texte"].drop_nulls().to_list())
    for code in ("B34.2", "B97.2", "U04.9"):
        assert f"[{code}]" not in joined, f"crochet [{code}] résiduel dans U07.13"
        assert f"({code})" in joined, f"redirection ({code}) attendue dans U07.13"


def test_m01_08_altlabels_retyped_as_inclusion() -> None:
    """Chantier retypage chap XIII (2026-06-06) : les ex-altLabel ANS
    de M01.08 (« tronc », « cou », etc.) sont retypés en `inclusion`
    ANS au niveau code. Plus aucune ligne `synonyme, source=ANS`."""
    df = _final_csv()
    sub = df.filter(pl.col("code") == "M01.08")
    if sub.is_empty():
        pytest.skip("M01.08 absent du CSV.")

    syn_ans = sub.filter((pl.col("type") == "synonyme") & (pl.col("source") == "ANS"))
    assert syn_ans.is_empty(), (
        f"M01.08 ne doit avoir AUCUN synonyme ANS post-retypage (trouvé : {syn_ans.height} lignes)"
    )

    incl_ans_code = sub.filter(
        (pl.col("type") == "inclusion")
        & (pl.col("source") == "ANS")
        & (pl.col("source_level") == "code")
    )
    # Au moins les 6 composants atomiques de la 5e position « autres ».
    joined = " ".join(t or "" for t in incl_ans_code["texte"].to_list()).lower()
    for localisation in ("tronc", "cou", "crâne", "côtes", "tête", "colonne vertébrale"):
        assert localisation in joined, (
            f"M01.08 inclusion ANS : '{localisation}' attendu (retypage altLabel)"
        )


def test_m00_00_type_d_without_altlabel_is_neutral() -> None:
    """M00.00 : code ofs_type=D sans altLabel ANS dans le RDF. Le
    retypage est un no-op : aucune ligne synonyme/inclusion ANS niveau
    code ne doit avoir été créée artificiellement."""
    df = _final_csv()
    sub = df.filter(pl.col("code") == "M00.00")
    if sub.is_empty():
        pytest.skip("M00.00 absent du CSV.")
    syn_ans = sub.filter((pl.col("type") == "synonyme") & (pl.col("source") == "ANS"))
    assert syn_ans.is_empty(), "M00.00 sans altLabel ANS : pas de synonyme ANS attendu."


def test_u07_0_synonymes_ans_preserved_outside_chap_xiii() -> None:
    """U07.0 (Affection liée au vapotage) : code post-2006 hors
    chapitre XIII avec altLabel ANS effectifs. Le retypage NE doit PAS
    les convertir en inclusion — ils restent étiquetés `synonyme`."""
    df = _final_csv()
    sub = df.filter(pl.col("code") == "U07.0")
    if sub.is_empty():
        pytest.skip("U07.0 absent du CSV.")
    syn_ans_code = sub.filter(
        (pl.col("type") == "synonyme")
        & (pl.col("source") == "ANS")
        & (pl.col("source_level") == "code")
    )
    assert syn_ans_code.height > 0, "U07.0 : synonymes ANS niveau code attendus (préservés)"
    # Texte distinctif présent : « dabbing » est un altLabel propre à U07.0
    joined = " ".join(t or "" for t in syn_ans_code["texte"].to_list()).lower()
    assert "dabbing" in joined or "vapotage" in joined or "cigarette" in joined, (
        "U07.0 : altLabel ANS attendus (dabbing/vapotage/cigarette)"
    )


def test_orphan_type_d_codes_report_exists() -> None:
    """Le rapport orphan_type_d_codes.csv doit être généré avec ~40
    lignes (codes type=D dans OFS absents du RDF ANS ; 90 avant D3, dont
    50 réinjectés depuis le kit ATIH — M11.9x, M13.9x, M83.xx, M62.8x)."""
    root = Path(__file__).resolve().parents[2]
    path = root / "reports" / "orphan_type_d_codes.csv"
    if not path.is_file():
        pytest.skip("Rapport orphan_type_d_codes.csv absent — relance `recode-icd build merged`.")
    df = pl.read_csv(path)
    assert set(df.columns) == {
        "code",
        "libelle_master",
        "chapter",
        "categorie_orphan",
    }
    # Empiriquement 90 codes. Tolérance ±10 si l'OFS ou l'ANS bouge.
    assert (
        30 <= df.height <= 50
    )  # 90 avant D3 ; 50 d'entre eux injectés depuis le kit ATIH, f"orphan_type_d_codes.csv : {df.height} lignes (attendu ~90)"
    # Tous dans le chapitre XIII.
    assert set(df["chapter"].unique().to_list()) == {"(M00-M99)"}


def test_u07_13_has_no_dagger_asterisk_pair() -> None:
    """U07.13 (post-2006) n'a pas d'association dague/astérisque côté OFS.
    Refonte 2026-05-30 : doit avoir les deux flags à False."""
    df = _final_csv()
    subset = df.filter(pl.col("code") == "U07.13")
    assert not subset.is_empty(), "U07.13 absent du CSV (vérifier qu'il est bien dans OWL)."
    assert subset.filter(pl.col("is_dagger_in_pair")).is_empty()
    assert subset.filter(pl.col("is_asterisk_in_pair")).is_empty()


def test_u07_1_absent_du_csv() -> None:
    """U07.1 est un nœud intermédiaire, donc hors du CSV — fait assumé.

    `_leaf_codes()` (`exporters/flat_csv.py`) restreint le CSV aux
    feuilles strictes du nested set. U07.1 porte les sous-divisions
    ATIH U07.10..U07.15 et n'est donc pas une feuille, alors qu'il est
    codable en pratique. Décision RF du 2026-05-25 : on reste sur les
    codes terminaux ; cf `docs/backlog/inclure_codes_intermediaires.md`.

    Ce test verrouille l'état actuel plutôt que de le laisser passer en
    skip silencieux. **Si le backlog est implémenté (option B, inclusion
    des codes intermédiaires), ce test doit être inversé** et les deux
    témoins ci-dessus repassés sur U07.1.
    """
    df = _final_csv()
    assert df.filter(pl.col("code") == "U07.1").is_empty(), (
        "U07.1 est présent dans le CSV : le backlog `inclure_codes_intermediaires` "
        "a-t-il été implémenté ? Si oui, inverser ce test et rebasculer "
        "test_u07_13_* sur U07.1."
    )
    # Les feuilles du bloc, elles, doivent bien être là.
    for code in ("U07.10", "U07.13", "U07.15"):
        assert not df.filter(pl.col("code") == code).is_empty(), (
            f"{code} (feuille du bloc COVID) absent du CSV"
        )


# ----------------------------------------------------------------------
# Codes intermédiaires codables au CSV (chantier couverture ATIH, D2)
# ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def flat_csv() -> pl.DataFrame:
    return _final_csv()


@pytest.mark.parametrize(
    "code",
    [
        "M16.0",  # seul niveau codable : l'ATIH s'arrête là, le maître descend en M16.0x
        "F00.0",  # les deux niveaux codables (F00.0 et F00.000…)
        "M00.0",
        "Z37.0",  # aucune ligne propre : une seule entrée d'Index, pas de note héritée exportable
        "C25.9",  # descendants sans ligne (C25.9+0/+8)
        "B18.0",
    ],
)
def test_un_intermediaire_codable_est_au_csv(flat_csv: pl.DataFrame, code: str) -> None:
    """D2, fiche par héritage : le code est au CSV avec ses lignes."""
    assert flat_csv.filter(pl.col("code") == code).height > 0, f"{code} absent du CSV"


@pytest.mark.parametrize("code", ["M16.0", "F00.0", "B18.0"])
def test_un_intermediaire_herite_des_niveaux_superieurs(flat_csv: pl.DataFrame, code: str) -> None:
    """Les lignes héritées arrivent par la propagation ordinaire, tracées par
    `source_level`. (`Z37.0` n'a qu'une note éditoriale héritée, type que le
    CSV n'exporte pas : il n'est pas témoin ici.)"""
    niveaux = set(flat_csv.filter(pl.col("code") == code)["source_level"].to_list())
    assert niveaux & {"chapter", "block", "category"}, niveaux


def test_un_pere_interdit_reste_hors_du_csv(flat_csv: pl.DataFrame) -> None:
    """`U07.1` (type 3 à l'ATIH) et `A00`, `M00` (catégories non vides) : pas codables, pas au CSV."""
    assert flat_csv.filter(pl.col("code").is_in(["U07.1", "A00", "M00"])).is_empty()


def test_les_entrees_externes_atteignent_les_intermediaires(flat_csv: pl.DataFrame) -> None:
    """Avant D2, ~11 500 entrées externes sur ces codes étaient rejetées comme
    « non terminales » ; `M00.0` en reçoit désormais (Index vol3)."""
    assert (
        flat_csv.filter((pl.col("code") == "M00.0") & (pl.col("source") == "CIM-10 index")).height
        > 0
    )
