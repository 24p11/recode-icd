"""Table de notations guide <-> référentiel (arbitrage n° 12 du registre).

Ce qui est verrouillé ici
-------------------------
1. **Les cinq expressions de l'article ITG** (O04.90, O04.4, O04.-1,
   O04.-2, O04.-3) traduisent vers les bons nœuds du référentiel, avec
   la bonne granularité. Ce sont les dorés de l'arbitrage.
2. **Chaque entrée de la table va et revient** : guide -> référentiel ->
   guide, et référentiel -> guide -> référentiel, pour toutes les
   positions déclarées. Une correspondance qui ne serait vraie que dans
   un sens serait une devinette.
3. **Hors table = non parsable**, jamais une traduction devinée : 5e
   position non déclarée, trois chiffres, plage sur la catégorie.
4. **Les formes génériques et les catégories non déclarées ne sont pas
   touchées** : la table ne fait pas un métier de plus que le sien.
5. **Sans table, rien n'est traduit** : « O04.-1 » reste non parsable,
   « O04.90 » ressemble à un code et le sera (introuvable ensuite).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from recode_icd.recommendations.code_expr import CodeExprError, TypeExpr, parse_code_expr
from recode_icd.recommendations.notations import (
    DEFAULT_NOTATIONS_PATH,
    CategorieInversee,
    Notations,
    NotationsError,
    charge_notations,
)

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def notations() -> Notations:
    """La table réelle, versionnée dans referentials/curation/."""
    return charge_notations(DEFAULT_NOTATIONS_PATH)


# -- 1. dorés : les cinq expressions d'ITG --------------------------------


@pytest.mark.parametrize(
    ("expr", "type_attendu", "noeuds_attendus"),
    [
        ("O04.90", TypeExpr.CODE, ("O04.-0.9",)),
        ("O04.4", TypeExpr.CATEGORIE, ("O04.-0.4", "O04.-1.4", "O04.-2.4", "O04.-3.4")),
        ("O04.-1", TypeExpr.CATEGORIE, ("O04.-1",)),
        ("O04.-2", TypeExpr.CATEGORIE, ("O04.-2",)),
        ("O04.-3", TypeExpr.CATEGORIE, ("O04.-3",)),
    ],
)
def test_les_cinq_expressions_ditg(
    notations: Notations, expr: str, type_attendu: TypeExpr, noeuds_attendus: tuple[str, ...]
) -> None:
    parsee = parse_code_expr(expr, notations)
    assert parsee.type is type_attendu
    assert parsee.noeuds == noeuds_attendus
    assert parsee.brut == expr, "la notation du guide est conservée pour le rapport"


def test_tiret_typographique_du_guide_est_normalise(notations: Notations) -> None:
    """Le guide écrit « O04.–1 » ; la table curée saisie au clavier « O04.-1 »."""
    typo = parse_code_expr("O04.–1", notations)
    ascii_ = parse_code_expr("O04.-1", notations)
    assert typo.valeur == ascii_.valeur == "O04.-1"
    assert typo.noeuds == ascii_.noeuds == ("O04.-1",)


# -- 2. chaque entrée, dans les deux sens ---------------------------------


def test_chaque_feuille_declaree_va_et_revient(notations: Notations) -> None:
    """guide -> référentiel -> guide, sur toutes les positions déclarées."""
    for cat in notations.categories.values():
        for quatrieme in cat.quatriemes:
            for cinquieme in cat.cinquiemes:
                guide = f"{cat.categorie}.{quatrieme}{cinquieme}"
                feuille = cat.feuille(quatrieme, cinquieme)
                parsee = notations.traduit(guide)
                assert parsee is not None and parsee.noeuds == (feuille,), guide
                assert parsee.type is TypeExpr.CODE
                assert notations.vers_guide(feuille) == guide, feuille


def test_chaque_noeud_declare_va_et_revient(notations: Notations) -> None:
    """référentiel -> guide -> référentiel, sur les nœuds de 5e position."""
    for cat in notations.categories.values():
        for cinquieme in cat.cinquiemes:
            noeud = cat.noeud(cinquieme)
            guide = notations.vers_guide(noeud)
            assert guide == f"{cat.categorie}.-{cinquieme}", noeud
            parsee = notations.traduit(guide)
            assert parsee is not None and parsee.noeuds == (noeud,)
            assert parsee.type is TypeExpr.CATEGORIE


def test_quatrieme_seul_couvre_une_feuille_par_cinquieme(notations: Notations) -> None:
    """« O04.4 » = toutes les 5e positions déclarées, dans l'ordre de la table."""
    for cat in notations.categories.values():
        for quatrieme in cat.quatriemes:
            parsee = notations.traduit(f"{cat.categorie}.{quatrieme}")
            assert parsee is not None
            assert parsee.noeuds == tuple(cat.feuille(quatrieme, c) for c in cat.cinquiemes)


# -- 3. hors table : non parsable, jamais deviné ---------------------------


@pytest.mark.parametrize(
    "expr",
    [
        "O04.94",  # 5e position 4 non déclarée
        "O04.-5",  # nœud de 5e position inexistant
        "O04.123",  # trois chiffres : ni feuille ni nœud
        "O04.1-O04.3",  # plage sur une catégorie inversée : ordre ambigu
        "O04.9-O04.9",
    ],
)
def test_forme_hors_table_leve(notations: Notations, expr: str) -> None:
    with pytest.raises(CodeExprError, match="hors de la table"):
        parse_code_expr(expr, notations)


def test_position_hors_table_en_sens_inverse_leve_aussi(notations: Notations) -> None:
    """Le sens référentiel -> guide détecte une table incomplète."""
    with pytest.raises(CodeExprError, match="hors de la table"):
        notations.vers_guide("O04.-7.9")


# -- 4. les formes génériques et les autres catégories restent intactes ----


@pytest.mark.parametrize(
    ("expr", "type_attendu", "valeur_attendue"),
    [
        ("O04", TypeExpr.CATEGORIE, "O04"),
        ("O04.–", TypeExpr.CATEGORIE, "O04"),
        ("O04-O06", TypeExpr.PLAGE, "O04-O06"),
        ("O03.4", TypeExpr.CODE, "O03.4"),  # catégorie non déclarée : forme générique
        ("Z86.70", TypeExpr.CODE, "Z86.70"),
        ("XXI", TypeExpr.CHAPITRE, "XXI"),
    ],
)
def test_les_formes_generiques_ne_sont_pas_traduites(
    notations: Notations, expr: str, type_attendu: TypeExpr, valeur_attendue: str
) -> None:
    parsee = parse_code_expr(expr, notations)
    assert parsee.type is type_attendu
    assert parsee.valeur == valeur_attendue
    assert parsee.noeuds == (), "aucune traduction sur une forme générique"


def test_vers_guide_ignore_les_categories_non_declarees(notations: Notations) -> None:
    assert notations.vers_guide("O05.-1.9") is None
    assert notations.vers_guide("Z86.70") is None


# -- 5. sans table, rien n'est traduit ------------------------------------


def test_sans_table_la_notation_du_guide_reste_non_parsable() -> None:
    with pytest.raises(CodeExprError):
        parse_code_expr("O04.-1")
    parsee = parse_code_expr("O04.90")
    assert parsee.type is TypeExpr.CODE and parsee.noeuds == (), (
        "sans table, « O04.90 » est pris pour un code : il sera non résolu, au rapport"
    )


# -- la table réelle et son chargement ------------------------------------


def test_la_table_reelle_declare_o04(notations: Notations) -> None:
    o04 = notations.categories["O04"]
    assert o04.cinquiemes == ("0", "1", "2", "3")
    assert o04.quatriemes == tuple("0123456789")


@pytest.mark.parametrize(
    ("yaml_texte", "motif"),
    [
        (
            "categories_inversees:\n  O4:\n    quatriemes: ['1']\n    cinquiemes: ['0']\n",
            "3 caractères",
        ),
        (
            "categories_inversees:\n  O04:\n    quatriemes: ['10']\n    cinquiemes: ['0']\n",
            "non chiffrées",
        ),
        (
            "categories_inversees:\n  O04:\n    quatriemes: ['1', '1']\n    cinquiemes: ['0']\n",
            "doublons",
        ),
        ("categories_inversees:\n  O04:\n    quatriemes: []\n    cinquiemes: ['0']\n", "non vide"),
        ("categories_inversees:\n  O04:\n    cinquiemes: ['0']\n", "non vide"),
    ],
)
def test_une_table_mal_formee_leve(tmp_path: Path, yaml_texte: str, motif: str) -> None:
    chemin = tmp_path / "notations.yaml"
    chemin.write_text(yaml_texte, encoding="utf-8")
    with pytest.raises(NotationsError, match=motif):
        charge_notations(chemin)


def test_une_table_vide_ne_traduit_rien(tmp_path: Path) -> None:
    chemin = tmp_path / "notations.yaml"
    chemin.write_text("categories_inversees: {}\n", encoding="utf-8")
    vide = charge_notations(chemin)
    assert vide.traduit("O04.90") is None
    assert parse_code_expr("O04.90", vide).noeuds == ()


def test_entree_synthetique() -> None:
    """Le module ne dépend pas de O04 : une autre catégorie inversée se déclare pareil."""
    table = Notations(categories={"X99": CategorieInversee("X99", ("1", "2"), ("0",))})
    assert table.traduit("X99.10") is not None
    assert table.traduit("X99.10").noeuds == ("X99.-0.1",)  # type: ignore[union-attr]
    assert table.vers_guide("X99.-0.2") == "X99.20"
    with pytest.raises(CodeExprError):
        table.traduit("X99.31")
