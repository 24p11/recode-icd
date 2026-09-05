"""Résolution des expressions vers les codes feuilles, et tri.

Données synthétiques : un nested set miniature suffit à prouver les
propriétés d'expansion, et il reste lisible — un extrait du vrai
référentiel ne le serait pas. La résolution sur données réelles est
vérifiée par les tests de régression des témoins du pilote.
"""

from __future__ import annotations

import polars as pl
import pytest

from recode_icd.recommendations.code_expr import TypeExpr, parse_code_expr
from recode_icd.recommendations.notations import CategorieInversee, Notations
from recode_icd.recommendations.resolution import ResolutionError, cle_de_tri, resout

pytestmark = pytest.mark.unit


@pytest.fixture
def merged() -> pl.DataFrame:
    """Nested set miniature : un chapitre, un bloc, trois catégories.

    IX (1,16)
    └── I60-I69 (2,15)
        ├── I63 (3,8)      → I63.0 I63.1 I63.2
        ├── I64 (9,10)     → feuille SANS subdivision
        └── I69 (11,14)    → I69.3 I69.4
    """
    lignes = [
        ("IX", "chapter", 1, 16),
        ("I60-I69", "block", 2, 15),
        ("I63", "category", 3, 8),
        ("I63.0", "category", 4, 5),
        ("I63.1", "category", 6, 7),
        ("I64", "category", 9, 10),
        ("I69", "category", 11, 14),
        ("I69.3", "category", 12, 13),
    ]
    return pl.DataFrame(
        {
            "code": [c for c, _, _, _ in lignes],
            "type": [t for _, t, _, _ in lignes],
            "left": [g for _, _, g, _ in lignes],
            "right": [d for _, _, _, d in lignes],
        }
    )


def test_categorie_se_resout_en_ses_feuilles(merged: pl.DataFrame) -> None:
    assert resout(parse_code_expr("I63"), merged) == ["I63.0", "I63.1"]


def test_categorie_sans_subdivision_est_sa_propre_feuille(merged: pl.DataFrame) -> None:
    """I64 n'a pas de subdivision : c'est lui-même la feuille.

    Piège : filtrer « les descendants stricts » renverrait une liste
    vide, et la consigne d'emploi de I64 — pourtant l'une des plus
    importantes de l'article AVC — n'atteindrait aucune fiche.
    """
    assert resout(parse_code_expr("I64"), merged) == ["I64"]


def test_chapitre_se_resout_jusqu_aux_feuilles(merged: pl.DataFrame) -> None:
    """Décision actée : les consignes de chapitre descendent aux fiches.

    Les fiches sont injectées telles quelles dans des prompts : elles
    doivent être autonomes. Le bruit est maîtrisé au rendu (regroupement
    en « Règles générales du chapitre »), pas en amputant la résolution.
    """
    assert resout(parse_code_expr("IX"), merged) == ["I63.0", "I63.1", "I64", "I69.3"]


def test_plage_couvre_les_bornes_incluses(merged: pl.DataFrame) -> None:
    assert resout(parse_code_expr("I63-I64"), merged) == ["I63.0", "I63.1", "I64"]


def test_code_absent_du_referentiel_leve(merged: pl.DataFrame) -> None:
    """Une expression bien formée mais introuvable est une erreur.

    Elle sera listée au rapport de build : un code cité par le guide et
    absent du référentiel est une information, pas un incident à taire.
    """
    with pytest.raises(ResolutionError, match="absent du référentiel"):
        resout(parse_code_expr("Z99.9"), merged)


def test_resolution_est_triee(merged: pl.DataFrame) -> None:
    """Tri explicite : sans lui, le build ne serait pas byte-déterministe."""
    codes = resout(parse_code_expr("IX"), merged)
    assert codes == sorted(codes)


# -- tri par spécificité ------------------------------------------------


def test_tri_par_specificite_decroissante() -> None:
    consignes = [
        (TypeExpr.CHAPITRE, "sujet", "GM2026-V-XXI-01"),
        (TypeExpr.CODE, "sujet", "GM2026-V-AVC-05"),
        (TypeExpr.PLAGE, "sujet", "GM2026-V-AVC-03"),
        (TypeExpr.CATEGORIE, "sujet", "GM2026-V-AVC-02"),
    ]
    tries = sorted(consignes, key=lambda c: cle_de_tri(*c))
    assert [c[0] for c in tries] == [
        TypeExpr.CODE,
        TypeExpr.CATEGORIE,
        TypeExpr.PLAGE,
        TypeExpr.CHAPITRE,
    ]


def test_sujet_passe_avant_exemple_a_specificite_egale() -> None:
    """`centralite` départage : la fiche de F32 ne doit pas ouvrir sur l'AVC."""
    consignes = [
        (TypeExpr.CATEGORIE, "exemple", "GM2026-V-AVC-01"),
        (TypeExpr.CATEGORIE, "sujet", "GM2026-V-AVC-02"),
    ]
    tries = sorted(consignes, key=lambda c: cle_de_tri(*c))
    assert [c[1] for c in tries] == ["sujet", "exemple"]


def test_le_tri_est_total() -> None:
    """À spécificité ET centralité égales, `rec_id` tranche.

    Sans ce troisième critère, l'ordre dépendrait de l'ordre d'arrivée
    des lignes, et deux builds successifs pourraient différer.
    """
    a = cle_de_tri(TypeExpr.CODE, "sujet", "GM2026-V-AVC-02")
    b = cle_de_tri(TypeExpr.CODE, "sujet", "GM2026-V-AVC-01")
    assert b < a


# -- expressions traduites par la table de notations (arbitrage n° 12) ----


@pytest.fixture
def merged_o04() -> pl.DataFrame:
    """Nested set miniature d'une catégorie à encodage inversé.

    O04 (1,14)
    ├── O04.-0 (2,7)    → O04.-0.4  O04.-0.9
    └── O04.-1 (8,13)   → O04.-1.4  O04.-1.9
    """
    lignes = [
        ("O04", "category", 1, 14),
        ("O04.-0", "category", 2, 7),
        ("O04.-0.4", "category", 3, 4),
        ("O04.-0.9", "category", 5, 6),
        ("O04.-1", "category", 8, 13),
        ("O04.-1.4", "category", 9, 10),
        ("O04.-1.9", "category", 11, 12),
    ]
    return pl.DataFrame(
        {
            "code": [c for c, _, _, _ in lignes],
            "type": [t for _, t, _, _ in lignes],
            "left": [g for _, _, g, _ in lignes],
            "right": [d for _, _, _, d in lignes],
        }
    )


@pytest.fixture
def notations_o04() -> Notations:
    return Notations(categories={"O04": CategorieInversee("O04", ("4", "9"), ("0", "1", "2"))})


def test_feuille_traduite_se_resout_en_elle_meme(
    merged_o04: pl.DataFrame, notations_o04: Notations
) -> None:
    """« O04.90 » du guide est la feuille O04.-0.9 du référentiel."""
    assert resout(parse_code_expr("O04.90", notations_o04), merged_o04) == ["O04.-0.9"]


def test_noeud_de_cinquieme_position_se_resout_en_ses_feuilles(
    merged_o04: pl.DataFrame, notations_o04: Notations
) -> None:
    assert resout(parse_code_expr("O04.-1", notations_o04), merged_o04) == ["O04.-1.4", "O04.-1.9"]


def test_quatrieme_seul_se_resout_a_travers_les_cinquiemes(
    merged_o04: pl.DataFrame, notations_o04: Notations
) -> None:
    """« O04.4 » traverse les nœuds de 5e position : une feuille par nœud."""
    with pytest.raises(ResolutionError, match=r"O04\.-2\.4"):
        # La table déclare la 5e position 2, que ce référentiel miniature
        # n'a pas : un nœud traduit absent lève comme un code absent.
        resout(parse_code_expr("O04.4", notations_o04), merged_o04)
    table_ajustee = Notations(categories={"O04": CategorieInversee("O04", ("4", "9"), ("0", "1"))})
    assert resout(parse_code_expr("O04.4", table_ajustee), merged_o04) == ["O04.-0.4", "O04.-1.4"]


def test_la_categorie_nue_reste_resolue_par_le_nested_set(
    merged_o04: pl.DataFrame, notations_o04: Notations
) -> None:
    """« O04 » n'est pas traduite : la table ne touche pas aux formes génériques."""
    assert resout(parse_code_expr("O04", notations_o04), merged_o04) == [
        "O04.-0.4",
        "O04.-0.9",
        "O04.-1.4",
        "O04.-1.9",
    ]
