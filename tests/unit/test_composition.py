"""Chapitre XX par composition (D5) : dérivation sur un mini-kit synthétique.

Ce qui est verrouillé : les rôles se décident par VALEUR d'après les
libellés (lieu, activité, précision, code OMS), une variante de libellé
du kit reste sa valeur, les branches de type 3 ne sont ni troncs ni
composées, la forme `+` est une activité sans lieu, une catégorie
hybride (sous-codes OMS en 0/9, lieu en 1-8) donne un tronc partiel, et
tout code codable non couvert est une erreur bruyante.
"""

from __future__ import annotations

import polars as pl
import pytest

from recode_icd.composition import (
    CompositionError,
    decompose,
    derive_composition,
    explique_suffixe_invalide,
)
from recode_icd.notations import charge_notations

pytestmark = pytest.mark.unit

LIEU = [
    "domicile",
    "établissement collectif",
    "école et lieu public",
    "lieu de sport",
    "rue ou route",
    "zone de commerce",
    "local industriel et chantier",
    "exploitation agricole",
    "autres lieux précisés",
    "lieu sans précision",
]
ACT = {
    "0": "en pratiquant un sport",
    "1": "en participant à un jeu et à des activités de loisirs",
    "2": "en exerçant un travail à des fins lucratives",
    "3": "en exerçant d'autres formes de travail",
    "4": "en se reposant, en dormant, en mangeant ou en participant à d'autres activités essentielles",
    "8": "en participant à d'autres activités précisées",
    "9": "en participant à une activité non précisée",
}


def _kit(lignes: list[tuple[str, int, str]]) -> pl.DataFrame:
    """`(code_atih, type_mco, libelle_long)` → extrait d'`atih_codes`."""
    notations = charge_notations()
    return pl.DataFrame(
        {
            "code_atih": [c for c, _, _ in lignes],
            "code": [notations.ecriture_maitre(c) for c, _, _ in lignes],
            "type_mco": [t for _, t, _ in lignes],
            "codable_mco": [t != 3 for _, t, _ in lignes],
            "libelle_long": [lib for _, _, lib in lignes],
        }
    )


def _lieu_activite(
    cat: str, base: str, lieux: range = range(10), variante_2: str | None = None
) -> list[tuple[str, int, str]]:
    """Une catégorie « lieu + activité » complète (1 + 10 + 70 codes)."""
    out = [(cat, 3, base)]
    for i in lieux:
        lib_lieu = variante_2 if (i == 2 and variante_2) else LIEU[i]
        out.append((f"{cat}{i}", 2, f"{base}, {lib_lieu}"))
        for a, lib_a in ACT.items():
            out.append((f"{cat}{i}{a}", 2, f"{base}, {lib_lieu}, {lib_a}"))
    return out


@pytest.fixture(scope="module")
def composition():  # type: ignore[no-untyped-def]
    lignes: list[tuple[str, int, str]] = []
    # W00 : lieu + activité, avec la variante « école, lieu public » en 2.
    lignes += _lieu_activite(
        "W00", "Chute de plain-pied due à la glace", variante_2="école, lieu public"
    )
    # W01 : idem, canonique — c'est lui qui fait la majorité.
    lignes += _lieu_activite("W01", "Chute de plain-pied par glissade")
    lignes += _lieu_activite("W02", "Chute impliquant patins")
    # V01 : OMS (4e) + activité (5e).
    lignes += [("V01", 3, "Piéton blessé"), ("V010", 2, "Piéton blessé, accident hors circulation")]
    lignes += [
        (f"V010{a}", 2, f"Piéton blessé, accident hors circulation, {lib_a}")
        for a, lib_a in ACT.items()
    ]
    # W26 : OMS (4e) + lieu (5e) + activité (6e), forme + ; branche morte W261 (type 3).
    lignes += [("W26", 3, "Contact objets tranchants"), ("W260", 2, "Contact couteau")]
    lignes += [(f"W260+{a}", 2, f"Contact couteau, {lib_a}") for a, lib_a in ACT.items()]
    for i in range(10):
        lignes.append((f"W260{i}", 2, f"Contact couteau, {LIEU[i]}"))
        lignes += [
            (f"W260{i}{a}", 2, f"Contact couteau, {LIEU[i]}, {lib_a}") for a, lib_a in ACT.items()
        ]
    lignes += [("W261", 3, "Contact couteau, établissement collectif")]
    lignes += [
        (f"W261{a}", 3, f"Contact couteau, établissement collectif, {lib_a}")
        for a, lib_a in ACT.items()
    ]
    # X59 : hybride — 0 et 9 sous-codes OMS codables, 1-8 lieu.
    lignes += [
        ("X59", 3, "Exposition à des facteurs, sans précision"),
        ("X590", 2, "Exposition responsable de fracture"),
        ("X599", 2, "Exposition responsable de lésions autres"),
    ]
    lignes += [
        (f"X59{i}", 2, f"Exposition à des facteurs, sans précision, {LIEU[i]}") for i in range(1, 9)
    ]
    # Y97 : sans subdivision, codable.
    lignes += [("Y97", 2, "Facteurs liés à la pollution")]
    # Un code hors chapitre XX : ignoré.
    lignes += [("A00", 3, "Choléra"), ("A000", 0, "Choléra à Vibrio")]
    return derive_composition(_kit(lignes))


def test_les_patrons_et_les_classes(composition) -> None:  # type: ignore[no-untyped-def]
    t = composition.troncs
    par = {r["tronc"]: r for r in t.iter_rows(named=True)}
    assert par["W00"]["patron"] == "lieu_activite" and par["W00"]["classe"] == "tronc_composition"
    assert par["W00"]["valeurs_lieu"] == "0123456789", (
        "la variante « école, lieu public » reste le lieu 2"
    )
    assert par["W00"]["n_codes_composes"] == 80
    assert par["V01.0"]["patron"] == "oms_activite" and par["V01.0"]["classe"] == "tronc_codable"
    assert par["W26.0"]["patron"] == "oms_lieu_activite" and par["W26.0"]["forme_plus"]
    assert par["X59"]["patron"] == "lieu_seul" and par["X59"]["valeurs_lieu"] == "12345678"
    assert "V01" not in par and "W26" not in par, (
        "une catégorie sans enfant lieu n'est pas un tronc"
    )
    assert "W26.1" not in par, "une branche de type 3 n'est pas un tronc"
    mortes = composition.patrons.filter(pl.col("dimension") == "branches_mortes_type_3")["n"][0]
    assert mortes == 8


def test_les_codes_composes_sont_decomposes(composition) -> None:  # type: ignore[no-untyped-def]
    d = decompose("W0024", composition)
    assert d is not None and (d["tronc"], d["lieu"], d["activite"]) == ("W00", "2", "4")
    plus = decompose("W260+4", composition)
    assert (
        plus is not None and plus["forme_plus"] and plus["lieu"] is None and plus["activite"] == "4"
    )
    six = decompose("W26034", composition)
    assert six is not None and (six["tronc"], six["lieu"], six["activite"]) == ("W26.0", "3", "4")
    assert decompose("X590", composition) is None, "un sous-code OMS codable n'est pas un composé"
    assert decompose("W2610", composition) is None, "branche morte"
    assert composition.codes["code"].n_unique() == composition.codes.height


def test_les_tables_sont_majoritaires_et_les_variantes_rapportees(composition) -> None:  # type: ignore[no-untyped-def]
    v = composition.valeurs
    assert (
        v.filter((pl.col("table") == "lieu") & (pl.col("valeur") == "2"))["libelle"][0]
        == "école et lieu public"
    )
    assert v.filter(pl.col("table") == "activite").height == 7
    variantes = composition.variantes.filter(~pl.col("canonique"))
    assert variantes.select("table", "valeur", "libelle").rows() == [
        ("lieu", "2", "école, lieu public")
    ]


@pytest.mark.parametrize(
    ("code", "motif"),
    [
        ("W0005", "activite « 5 » hors table"),
        ("X590", "lieu « 0 » hors table"),  # 0 est un sous-code OMS, pas un lieu de X59
        ("W000+4", "hors table"),
        ("V0105", "activite « 5 » hors table"),
        ("W00245", "3 caractère"),
        ("Y970", "Aucun tronc"),
    ],
)
def test_un_suffixe_invalide_est_explique(composition, code: str, motif: str) -> None:  # type: ignore[no-untyped-def]
    assert decompose(code, composition) is None
    message = explique_suffixe_invalide(code, composition)
    assert message is not None and motif in message, message


def test_un_code_codable_non_couvert_est_une_erreur() -> None:
    """Un codable qui n'est ni tronc, ni OMS, ni composé ne se tait pas."""
    kit = _kit(
        [
            ("W00", 3, "Chute"),
            ("W000", 2, "Chute, domicile"),
            (
                "W0007",
                2,
                "Chute, domicile, en faisant autre chose que la table",
            ),  # activité inconnue
        ]
    )
    with pytest.raises(CompositionError, match="ni composé"):
        derive_composition(kit)


def test_la_derivation_est_deterministe(composition) -> None:  # type: ignore[no-untyped-def]
    assert composition.troncs["tronc"].to_list() == sorted(composition.troncs["tronc"].to_list())
    assert composition.codes["code_atih"].to_list() == sorted(
        composition.codes["code_atih"].to_list()
    )
