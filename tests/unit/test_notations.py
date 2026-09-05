"""Table de notation unique des codes (arbitrage n° 12, étendu par D1-c).

Ce qui est verrouillé ici
-------------------------
1. **Les dorés** : les cinq expressions de l'article ITG (O04.90, O04.4,
   O04.-1, O04.-2, O04.-3) et les trois formes de la seconde famille
   inversée (M62.810, M62.8-0, M62.81) traduisent vers les bons nœuds du
   maître, avec la bonne granularité.
2. **Chaque famille va et revient** : pointée -> maître -> pointée,
   compacte -> maître -> compacte, sur toutes les positions déclarées.
3. **Hors table = non parsable**, jamais deviné.
4. **Les formes génériques et les catégories non déclarées ne sont pas
   touchées** ; sans table, rien n'est traduit.
5. **Le sens ATIH** : compacte -> maître (`ecriture_maitre`), maître ->
   compacte (`cle_compacte`, `None` pour un nœud de regroupement) et le
   résolveur toute-écriture (`resout_ecriture`).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from recode_icd.notations import (
    DEFAULT_NOTATIONS_PATH,
    FamilleInversee,
    Notations,
    NotationsError,
    charge_notations,
    ecriture_pointee,
)
from recode_icd.recommendations.code_expr import CodeExprError, TypeExpr, parse_code_expr

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def notations() -> Notations:
    """La table réelle, versionnée dans referentials/curation/."""
    return charge_notations(DEFAULT_NOTATIONS_PATH)


# -- 1. dorés ------------------------------------------------------------


@pytest.mark.parametrize(
    ("expr", "type_attendu", "noeuds_attendus"),
    [
        ("O04.90", TypeExpr.CODE, ("O04.-0.9",)),
        ("O04.4", TypeExpr.CATEGORIE, ("O04.-0.4", "O04.-1.4", "O04.-2.4", "O04.-3.4")),
        ("O04.-1", TypeExpr.CATEGORIE, ("O04.-1",)),
        ("O04.-2", TypeExpr.CATEGORIE, ("O04.-2",)),
        ("O04.-3", TypeExpr.CATEGORIE, ("O04.-3",)),
        ("M62.810", TypeExpr.CODE, ("M62.8-01",)),
        ("M62.8-0", TypeExpr.CATEGORIE, ("M62.8-0",)),
        ("M62.81", TypeExpr.CATEGORIE, ("M62.8-01", "M62.8-81")),
    ],
)
def test_les_dores(
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


# -- 2. chaque famille, dans les deux sens --------------------------------


def test_chaque_feuille_declaree_va_et_revient(notations: Notations) -> None:
    """pointée -> maître -> pointée et compacte -> maître -> compacte."""
    for fam in notations.familles.values():
        for a in fam.a:
            for b in fam.b:
                compact = fam.compact(a, b)
                feuille = fam.feuille(a, b)
                pointee = ecriture_pointee(compact)
                parsee = notations.traduit(pointee)
                assert parsee is not None and parsee.noeuds == (feuille,), pointee
                assert parsee.type is TypeExpr.CODE
                assert notations.vers_guide(feuille) == pointee, feuille
                assert notations.ecriture_maitre(compact) == feuille, compact
                assert notations.cle_compacte(feuille) == compact, feuille


def test_chaque_noeud_declare_va_et_revient(notations: Notations) -> None:
    for fam in notations.familles.values():
        for b in fam.b:
            noeud = fam.noeud(b)
            assert notations.vers_guide(noeud) == noeud
            parsee = notations.traduit(noeud)
            assert parsee is not None and parsee.noeuds == (noeud,)
            assert parsee.type is TypeExpr.CATEGORIE
            assert notations.cle_compacte(noeud) is None, (
                "un nœud de regroupement n'a pas de compacte"
            )


def test_a_seul_couvre_une_feuille_par_b(notations: Notations) -> None:
    for fam in notations.familles.values():
        for a in fam.a:
            parsee = notations.traduit(ecriture_pointee(fam.base_compacte + a))
            assert parsee is not None
            assert parsee.noeuds == tuple(fam.feuille(a, b) for b in fam.b)


def test_la_table_reelle_declare_deux_familles_et_neuf_plus(notations: Notations) -> None:
    assert set(notations.familles) == {"O04", "M62.8"}
    assert notations.familles["O04"].b == ("0", "1", "2", "3")
    assert notations.familles["M62.8"].b == ("0", "8")
    assert notations.plus_ponctue == frozenset(
        {"B24", "B99", "F55", "F61", "P95", "R53", "R54", "S47", "T68"}
    )


# -- 3. hors table : non parsable, jamais deviné ---------------------------


@pytest.mark.parametrize(
    "expr",
    [
        "O04.94",  # position b = 4 non déclarée
        "O04.-5",  # nœud de regroupement inexistant
        "O04.123",  # trois chiffres : ni feuille ni nœud
        "O04.1-O04.3",  # plage sur une famille inversée : ordre ambigu
        "O04.9-O04.9",
        "M62.815",  # position b = 5 non déclarée
        "M62.8-01",  # écriture du maître, pas du guide
    ],
)
def test_forme_hors_table_leve(notations: Notations, expr: str) -> None:
    with pytest.raises(CodeExprError, match="hors de la table"):
        parse_code_expr(expr, notations)


def test_position_hors_table_en_sens_inverse_leve_aussi(notations: Notations) -> None:
    with pytest.raises(CodeExprError, match="hors de la table"):
        notations.vers_guide("O04.-7.9")


# -- 4. formes génériques, catégories non déclarées, sans table ------------


@pytest.mark.parametrize(
    ("expr", "type_attendu", "valeur_attendue"),
    [
        ("O04", TypeExpr.CATEGORIE, "O04"),
        ("O04.–", TypeExpr.CATEGORIE, "O04"),
        ("O04-O06", TypeExpr.PLAGE, "O04-O06"),
        ("M62.8", TypeExpr.CODE, "M62.8"),  # la base elle-même : forme générique
        ("O03.4", TypeExpr.CODE, "O03.4"),
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
    assert parsee.noeuds == ()


def test_vers_guide_ignore_les_categories_non_declarees(notations: Notations) -> None:
    assert notations.vers_guide("O05.-1.9") is None
    assert notations.vers_guide("Z86.70") is None


def test_sans_table_la_notation_du_guide_reste_non_parsable() -> None:
    with pytest.raises(CodeExprError):
        parse_code_expr("O04.-1")
    parsee = parse_code_expr("O04.90")
    assert parsee.type is TypeExpr.CODE and parsee.noeuds == ()


# -- 5. le sens ATIH : compacte <-> maître ---------------------------------


@pytest.mark.parametrize(
    ("compact", "maitre"),
    [
        ("A00", "A00"),
        ("A000", "A00.0"),
        ("M0000", "M00.00"),
        ("S37800", "S37.800"),
        ("C169+0", "C16.9+0"),  # `+` en 5e : point après le 3e
        ("T08+0", "T08+0"),  # `+` en 4e hors table : pas de point
        ("F03+00", "F03+00"),
        ("B24+0", "B24.+0"),  # `+` en 4e ponctué (table)
        ("O0490", "O04.-0.9"),  # famille inversée
        ("O040", "O04.0"),  # niveau intermédiaire du kit : pointée
        ("M62810", "M62.8-01"),  # seconde famille inversée
        ("M62808", "M62.8-80"),
        ("M6280", "M62.80"),
        ("W0004", "W00.04"),
    ],
)
def test_compacte_vers_maitre(notations: Notations, compact: str, maitre: str) -> None:
    assert notations.ecriture_maitre(compact) == maitre
    assert notations.cle_compacte(maitre) == compact, "et retour"


@pytest.mark.parametrize("noeud", ["O04.-1", "M62.8-0", "S37.8-0", "A00-A09"])
def test_les_noeuds_de_regroupement_nont_pas_de_compacte(notations: Notations, noeud: str) -> None:
    assert notations.cle_compacte(noeud) is None


@pytest.mark.parametrize(
    ("saisie", "maitre"),
    [
        ("O0490", "O04.-0.9"),
        ("O04.90", "O04.-0.9"),
        ("o04.90", "O04.-0.9"),
        ("O04.-0.9", "O04.-0.9"),
        ("M62810", "M62.8-01"),
        ("M62.810", "M62.8-01"),
        ("M62.8-01", "M62.8-01"),
        ("B24+0", "B24.+0"),
        ("B24.+0", "B24.+0"),
        ("  a000 ", "A00.0"),
        ("S37.8-0", "S37.8-0"),
    ],
)
def test_resout_ecriture_accepte_toute_forme(
    notations: Notations, saisie: str, maitre: str
) -> None:
    assert notations.resout_ecriture(saisie) == maitre


def test_resout_ecriture_refuse_le_vide(notations: Notations) -> None:
    with pytest.raises(CodeExprError):
        notations.resout_ecriture("  ")


# -- la table et son chargement --------------------------------------------


@pytest.mark.parametrize(
    ("yaml_texte", "motif"),
    [
        (
            "familles_inversees:\n  X:\n    base_compacte: 'O4'\n    base_maitre: 'O4'\n    feuille_maitre: '{base}.-{b}.{a}'\n    noeud_maitre: '{base}.-{b}'\n    a: ['1']\n    b: ['0']\n",
            "préfixe compact",
        ),
        (
            "familles_inversees:\n  X:\n    base_compacte: 'O04'\n    base_maitre: 'O05'\n    feuille_maitre: '{base}.-{b}.{a}'\n    noeud_maitre: '{base}.-{b}'\n    a: ['1']\n    b: ['0']\n",
            "même préfixe",
        ),
        (
            "familles_inversees:\n  X:\n    base_compacte: 'O04'\n    base_maitre: 'O04'\n    feuille_maitre: '{base}.-{b}'\n    noeud_maitre: '{base}.-{b}'\n    a: ['1']\n    b: ['0']\n",
            "feuille_maitre",
        ),
        (
            "familles_inversees:\n  X:\n    base_compacte: 'O04'\n    base_maitre: 'O04'\n    feuille_maitre: '{base}.-{b}.{a}'\n    noeud_maitre: '{base}.-{b}'\n    a: ['10']\n    b: ['0']\n",
            "non chiffrées",
        ),
        (
            "familles_inversees:\n  X:\n    base_compacte: 'O04'\n    base_maitre: 'O04'\n    feuille_maitre: '{base}.-{b}.{a}'\n    noeud_maitre: '{base}.-{b}'\n    a: ['1', '1']\n    b: ['0']\n",
            "doublons",
        ),
        ("plus_ponctue: ['B2']\n", "3 caractères"),
    ],
)
def test_une_table_mal_formee_leve(tmp_path: Path, yaml_texte: str, motif: str) -> None:
    chemin = tmp_path / "notations.yaml"
    chemin.write_text(yaml_texte, encoding="utf-8")
    with pytest.raises(NotationsError, match=motif):
        charge_notations(chemin)


def test_une_table_vide_ne_traduit_rien(tmp_path: Path) -> None:
    chemin = tmp_path / "notations.yaml"
    chemin.write_text("familles_inversees: {}\n", encoding="utf-8")
    vide = charge_notations(chemin)
    assert vide.traduit("O04.90") is None
    assert parse_code_expr("O04.90", vide).noeuds == ()
    assert vide.ecriture_maitre("O0490") == "O04.90"
    assert vide.ecriture_maitre("B24+0") == "B24+0"


def test_famille_synthetique() -> None:
    """Le module ne dépend d'aucune famille : une autre se déclare pareil."""
    fam = FamilleInversee("X99", "X99", "X99", "{base}.-{b}.{a}", "{base}.-{b}", ("1", "2"), ("0",))
    table = Notations(familles={"X99": fam})
    parsee = table.traduit("X99.10")
    assert parsee is not None and parsee.noeuds == ("X99.-0.1",)
    assert table.vers_guide("X99.-0.2") == "X99.20"
    assert table.ecriture_maitre("X9920") == "X99.-0.2"
    with pytest.raises(CodeExprError):
        table.traduit("X99.31")
