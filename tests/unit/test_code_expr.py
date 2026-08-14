"""Parseur des expressions de codes du guide méthodologique.

Ce qui est verrouillé ici
-------------------------
1. **Les cinq formes** sont reconnues, et chacune porte la bonne
   granularité — c'est elle qui pilote le tri par spécificité au rendu.
2. **Les deux tirets** sont acceptés. Le guide écrit « I63.– » avec un
   tiret typographique (U+2013) ; une table curée saisie au clavier
   portera un tiret ASCII. Refuser l'un des deux ferait échouer des
   lignes correctes sur un caractère invisible à l'œil.
3. **Les invalides lèvent**, jamais ne passent en silence. Une
   expression avalée est une consigne perdue, et une consigne perdue est
   indétectable en aval : rien dans la fiche ne signale son absence.
"""

from __future__ import annotations

import pytest

from recode_icd.recommendations.code_expr import (
    CodeExprError,
    TypeExpr,
    parse_code_expr,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("expr", "type_attendu", "valeur_attendue"),
    [
        ("Z86.70", TypeExpr.CODE, "Z86.70"),
        ("I63.0", TypeExpr.CODE, "I63.0"),
        ("U07.13", TypeExpr.CODE, "U07.13"),
        ("I69", TypeExpr.CATEGORIE, "I69"),
        ("D62", TypeExpr.CATEGORIE, "D62"),
        ("I60-I64", TypeExpr.PLAGE, "I60-I64"),
        ("G46.0-G46.2", TypeExpr.PLAGE, "G46.0-G46.2"),
        ("XXI", TypeExpr.CHAPITRE, "XXI"),
        ("XX", TypeExpr.CHAPITRE, "XX"),
        ("I", TypeExpr.CHAPITRE, "I"),
    ],
)
def test_les_cinq_formes(expr: str, type_attendu: TypeExpr, valeur_attendue: str) -> None:
    parsee = parse_code_expr(expr)
    assert parsee.type is type_attendu
    assert parsee.valeur == valeur_attendue
    assert parsee.brut == expr, "le brut doit être conservé pour le rapport de build"


@pytest.mark.parametrize("tiret", ["–", "—", "-"])
def test_notation_a_tiret_accepte_les_trois_tirets(tiret: str) -> None:
    """« I63.– » : typographique (guide), demi-cadratin, ou ASCII (clavier).

    Le tiret est invisible à l'œil dans un CSV : refuser l'un des trois
    ferait échouer une ligne correcte sans que le curateur comprenne
    pourquoi.
    """
    parsee = parse_code_expr(f"I63.{tiret}")
    assert parsee.type is TypeExpr.CATEGORIE
    assert parsee.valeur == "I63"


def test_notation_a_tiret_equivaut_a_la_categorie_nue() -> None:
    """« I63.– » et « I63 » désignent la même chose, donc la même spécificité.

    Les distinguer donnerait deux niveaux de tri pour une seule réalité,
    et l'ordre des consignes dépendrait alors de la typographie du guide.
    """
    assert parse_code_expr("I63.–").type is parse_code_expr("I63").type
    assert parse_code_expr("I63.–").valeur == parse_code_expr("I63").valeur


@pytest.mark.parametrize("tiret", ["–", "—", "-"])
def test_plage_accepte_les_trois_tirets(tiret: str) -> None:
    parsee = parse_code_expr(f"I60{tiret}I64")
    assert parsee.type is TypeExpr.PLAGE
    assert (parsee.debut, parsee.fin) == ("I60", "I64")


@pytest.mark.parametrize(
    "expr",
    [
        "",
        "   ",
        "I6X",  # caractère non numérique
        "Z",  # lettre seule
        "I60-",  # intervalle ouvert
        "-I64",
        "i69",  # minuscule
        "I69.",  # point orphelin
        "I200+0",  # notation dague exotique de l'Index
        "nocode",
    ],
)
def test_expressions_invalides_levent(expr: str) -> None:
    with pytest.raises(CodeExprError):
        parse_code_expr(expr)


def test_chapitre_romain_inexistant_a_un_message_explicite() -> None:
    """« XXV » ressemble à un chapitre : le message doit le dire.

    Sans cela, le curateur cherche une faute de format alors que c'est le
    contenu qui est faux — la CIM-10 s'arrête au chapitre XXII.
    """
    with pytest.raises(CodeExprError, match="22 chapitres"):
        parse_code_expr("XXV")


def test_plage_a_bornes_de_granularites_differentes_leve() -> None:
    """« I60-I63.2 » est ambigu : la borne finale coupe une catégorie."""
    with pytest.raises(CodeExprError, match="granularités différentes"):
        parse_code_expr("I60-I63.2")


def test_plage_inversee_leve() -> None:
    with pytest.raises(CodeExprError, match="antérieure"):
        parse_code_expr("I64-I60")


def test_ordre_de_specificite() -> None:
    """L'ordre CODE > CATEGORIE > PLAGE > CHAPITRE est porté par l'enum.

    C'est la même convention que la `chapter_policy` (bloc > chapitre >
    défaut) : une seule règle de résolution dans tout le projet.
    """
    assert TypeExpr.CODE > TypeExpr.CATEGORIE > TypeExpr.PLAGE > TypeExpr.CHAPITRE


def test_espaces_autour_sont_tolerés() -> None:
    """Un CSV curé à la main porte des espaces parasites."""
    assert parse_code_expr("  I69  ").valeur == "I69"
