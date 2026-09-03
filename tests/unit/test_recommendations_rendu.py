"""Rendu de la section « Consignes de codage » — règles de sélection et de forme.

Données synthétiques : quelques associations suffisent à prouver chaque
règle, et elles restent lisibles. Le rendu sur données réelles est
verrouillé par les tests de régression des témoins du prototype
(`tests/regression/test_cards_consignes.py`).
"""

from __future__ import annotations

import polars as pl
import pytest

from recode_icd.recommendations.code_expr import TypeExpr
from recode_icd.recommendations.rendu import consignes_pour, rendre_section_consignes

pytestmark = pytest.mark.unit


def _rec_codes(lignes: list[tuple[str, str, str, str, str, TypeExpr]]) -> pl.DataFrame:
    """Associations synthétiques : (rec_id, code_expr, code, role, centralite, type_expr)."""
    return pl.DataFrame(
        {
            "rec_id": [rec_id for rec_id, *_ in lignes],
            "code_expr": [expr for _, expr, *_ in lignes],
            "code": [code for _, _, code, *_ in lignes],
            "role": [role for _, _, _, role, *_ in lignes],
            "centralite": [c for _, _, _, _, c, _ in lignes],
            "specificite": pl.Series([int(t) for *_, t in lignes], dtype=pl.Int64),
        }
    )


def _recs(rec_ids: list[str], *, situations: dict[str, str] | None = None) -> pl.DataFrame:
    """Consignes synthétiques : texte et situation dérivés du rec_id."""
    situations = situations or {}
    return pl.DataFrame(
        {
            "rec_id": rec_ids,
            "texte": [f"texte de {r}" for r in rec_ids],
            "type": ["condition_emploi"] * len(rec_ids),
            "millesime": ["2026-test"] * len(rec_ids),
            "situation": [situations.get(r, f"situation de {r}") for r in rec_ids],
        }
    )


def test_le_filtre_contexte_s_applique_avant_la_dedup() -> None:
    """Une consigne qui cite le code en `contexte` ET le régit au niveau
    chapitre doit rester — c'est l'association chapitre qui est rendue,
    pas rien du tout."""
    rc = _rec_codes(
        [
            ("R1", "I63.0", "I63.0", "contexte", "sujet", TypeExpr.CODE),
            ("R1", "IX", "I63.0", "regi", "sujet", TypeExpr.CHAPITRE),
        ]
    )
    lignes = consignes_pour(rc, _recs(["R1"]), "I63.0")
    assert len(lignes) == 1
    assert TypeExpr(lignes[0]["specificite"]) is TypeExpr.CHAPITRE


def test_un_role_contexte_seul_ne_rend_rien() -> None:
    rc = _rec_codes([("R1", "I63.0", "I63.0", "contexte", "sujet", TypeExpr.CODE)])
    assert consignes_pour(rc, _recs(["R1"]), "I63.0") == []
    assert rendre_section_consignes(rc, _recs(["R1"]), "I63.0") is None


def test_dedup_sujet_prime_sur_exemple() -> None:
    """Cas mesuré Z20.1 : la consigne l'atteint en `exemple` au niveau
    code ET en `sujet` via sa catégorie. Elle norme le code : une seule
    ligne, dans la liste principale, pas dans le bloc cité — même si
    l'association `exemple` est la plus spécifique."""
    rc = _rec_codes(
        [
            ("R1", "Z20.1", "Z20.1", "DP", "exemple", TypeExpr.CODE),
            ("R1", "Z20", "Z20.1", "regi", "sujet", TypeExpr.CATEGORIE),
        ]
    )
    lignes = consignes_pour(rc, _recs(["R1"]), "Z20.1", avec_exemples=True)
    assert len(lignes) == 1
    assert lignes[0]["centralite"] == "sujet"

    section = rendre_section_consignes(rc, _recs(["R1"]), "Z20.1")
    assert section is not None
    assert "- [R1] texte de R1" in section
    assert "À titre d'exemple" not in section


def test_dedup_au_niveau_le_plus_specifique() -> None:
    """Une consigne atteinte par la catégorie ET par le code ne se rend
    qu'une fois, au niveau le plus spécifique (30 couples mesurés)."""
    rc = _rec_codes(
        [
            ("R1", "Z51", "Z51.31", "regi", "sujet", TypeExpr.CATEGORIE),
            ("R1", "Z51.31", "Z51.31", "DP", "sujet", TypeExpr.CODE),
        ]
    )
    lignes = consignes_pour(rc, _recs(["R1"]), "Z51.31")
    assert len(lignes) == 1
    assert TypeExpr(lignes[0]["specificite"]) is TypeExpr.CODE


def test_tri_par_specificite_decroissante_puis_rec_id() -> None:
    rc = _rec_codes(
        [
            ("R3", "XXI", "Z51.5", "regi", "sujet", TypeExpr.CHAPITRE),
            ("R2", "Z51", "Z51.5", "regi", "sujet", TypeExpr.CATEGORIE),
            ("R4", "Z40-Z54", "Z51.5", "regi", "sujet", TypeExpr.PLAGE),
            ("R1", "Z51.5", "Z51.5", "DP", "sujet", TypeExpr.CODE),
            ("R0", "Z51", "Z51.5", "DAS", "sujet", TypeExpr.CATEGORIE),
        ]
    )
    lignes = consignes_pour(rc, _recs(["R0", "R1", "R2", "R3", "R4"]), "Z51.5")
    assert [r["rec_id"] for r in lignes] == ["R1", "R0", "R2", "R4", "R3"]


def test_regles_generales_regroupees_avec_leur_situation() -> None:
    """Les consignes de niveau chapitre partent en fin de section, sous
    leur sous-titre, chacune précédée de sa situation entre parenthèses :
    c'est elle qui borne la portée de la règle."""
    rc = _rec_codes(
        [
            ("R1", "Z86.70", "Z86.70", "DP", "sujet", TypeExpr.CODE),
            ("R2", "XXI", "Z86.70", "regi", "sujet", TypeExpr.CHAPITRE),
        ]
    )
    recs = _recs(["R1", "R2"], situations={"R2": "Emploi général des codes Z"})
    section = rendre_section_consignes(rc, recs, "Z86.70")
    assert section is not None
    assert "### Règles générales du chapitre XXI" in section
    assert "- [R2] (Emploi général des codes Z) texte de R2" in section
    # La règle de chapitre ne figure pas dans la liste principale.
    avant_sous_titre = section.split("### Règles générales")[0]
    assert "[R2]" not in avant_sous_titre


def test_bloc_exemples_avant_les_regles_generales() -> None:
    """Le bloc cité des exemples précède le `###` des règles générales,
    sinon il serait visuellement rattaché à ce sous-titre."""
    rc = _rec_codes(
        [
            ("R1", "Z95.1", "Z95.1", "DP", "sujet", TypeExpr.CODE),
            ("R2", "Z95.1", "Z95.1", "DP", "exemple", TypeExpr.CODE),
            ("R3", "XXI", "Z95.1", "regi", "sujet", TypeExpr.CHAPITRE),
        ]
    )
    section = rendre_section_consignes(rc, _recs(["R1", "R2", "R3"]), "Z95.1")
    assert section is not None
    assert (
        section.find("- [R1]")
        < section.find("> À titre d'exemple dans le guide :")
        < section.find("> - [R2] texte de R2")
        < section.find("### Règles générales du chapitre XXI")
    )


def test_liste_principale_vide_saute_directement_aux_regles_generales() -> None:
    """Cas Z23.0 : un code que le guide ne cite pas ne reçoit que les
    règles de chapitre — pas de puce vide ni de triple saut de ligne."""
    rc = _rec_codes([("R1", "XXI", "Z23.0", "regi", "sujet", TypeExpr.CHAPITRE)])
    recs = _recs(["R1"], situations={"R1": "Emploi général"})
    section = rendre_section_consignes(rc, recs, "Z23.0")
    assert section == (
        "## Consignes de codage (guide méthodologique 2026-test)\n"
        "\n"
        "### Règles générales du chapitre XXI\n"
        "\n"
        "- [R1] (Emploi général) texte de R1"
    )


def test_le_millesime_du_titre_vient_de_la_table() -> None:
    rc = _rec_codes([("R1", "I64", "I64", "DP", "sujet", TypeExpr.CODE)])
    section = rendre_section_consignes(rc, _recs(["R1"]), "I64")
    assert section is not None
    assert section.startswith("## Consignes de codage (guide méthodologique 2026-test)")


def test_exemples_exclus_par_defaut_de_consignes_pour() -> None:
    """`avec_exemples=False` (défaut) : mêmes résultats que le prototype
    du notebook — ses assertions restent valides à l'identique."""
    rc = _rec_codes(
        [
            ("R1", "F32", "F32.1", "DAS", "exemple", TypeExpr.CATEGORIE),
        ]
    )
    assert consignes_pour(rc, _recs(["R1"]), "F32.1") == []
    lignes = consignes_pour(rc, _recs(["R1"]), "F32.1", avec_exemples=True)
    assert [r["rec_id"] for r in lignes] == ["R1"]
