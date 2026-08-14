"""Construction des tables de recommandations depuis les tables curées.

Données synthétiques : le pilote réel est verrouillé par les tests de
régression sur les codes témoins. Ici on prouve les propriétés du build
lui-même — ce qu'il remonte au rapport, et ce qu'il refuse.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.recommendations.build import (
    CurationError,
    charge_tables_curees,
    construit,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def merged() -> pl.DataFrame:
    lignes = [
        ("IX", "chapter", 1, 12),
        ("I63", "category", 2, 7),
        ("I63.0", "category", 3, 4),
        ("I63.1", "category", 5, 6),
        ("I64", "category", 8, 9),
        ("I65", "category", 10, 11),
    ]
    return pl.DataFrame(
        {
            "code": [c for c, _, _, _ in lignes],
            "type": [t for _, t, _, _ in lignes],
            "left": [g for _, _, g, _ in lignes],
            "right": [d for _, _, _, d in lignes],
        }
    )


def _recs(*rec_ids: str) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "rec_id": list(rec_ids),
            "millesime": ["2026-provisoire"] * len(rec_ids),
            "localisation": ["Guide MCO, chap. V"] * len(rec_ids),
            "situation": ["situation"] * len(rec_ids),
            "type": ["regle_position"] * len(rec_ids),
            "texte": ["texte"] * len(rec_ids),
            "condition": [None] * len(rec_ids),
        },
        schema_overrides={"condition": pl.String},
    )


def _codes(paires: list[tuple[str, str]]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "rec_id": [r for r, _ in paires],
            "code_expr": [e for _, e in paires],
            "role": ["DP"] * len(paires),
            "centralite": ["sujet"] * len(paires),
            "condition": [None] * len(paires),
        },
        schema_overrides={"condition": pl.String},
    )


def test_expansion_produit_une_ligne_par_code_feuille(merged: pl.DataFrame) -> None:
    _, resolus, _ = construit(_recs("GM2026-V-X-01"), _codes([("GM2026-V-X-01", "I63")]), merged)
    assert resolus["code"].to_list() == ["I63.0", "I63.1"]
    assert resolus["code_expr"].unique().to_list() == ["I63"], (
        "l'expression source doit être conservée : sans elle, l'association "
        "compacte n'est plus récupérable"
    )


def test_expression_non_parsable_va_au_rapport_et_pas_dans_la_sortie(
    merged: pl.DataFrame,
) -> None:
    """Une consigne perdue est indétectable en aval : elle doit se voir."""
    _, resolus, rapport = construit(
        _recs("GM2026-V-X-01"), _codes([("GM2026-V-X-01", "I6X")]), merged
    )
    assert resolus.height == 0
    assert len(rapport.expressions_non_parsables) == 1
    assert rapport.expressions_non_parsables[0]["code_expr"] == "I6X"
    assert rapport.a_des_erreurs


def test_expression_introuvable_va_au_rapport(merged: pl.DataFrame) -> None:
    _, _, rapport = construit(_recs("GM2026-V-X-01"), _codes([("GM2026-V-X-01", "Z99.9")]), merged)
    assert len(rapport.expressions_non_resolues) == 1
    assert rapport.a_des_erreurs


def test_recommandation_sans_association_est_signalee(merged: pl.DataFrame) -> None:
    """Cas réel du pilote : AVC-02 et AVC-04 n'ont pas d'association au §5.

    Ce n'est pas une erreur — c'est un manque, et il doit être visible
    plutôt que silencieux : une consigne sans code n'atteint aucune fiche.
    """
    _, _, rapport = construit(
        _recs("GM2026-V-X-01", "GM2026-V-X-02"),
        _codes([("GM2026-V-X-01", "I63")]),
        merged,
    )
    assert rapport.recommandations_sans_code == ["GM2026-V-X-02"]
    assert not rapport.a_des_erreurs, "un manque n'est pas une erreur de build"


def test_association_orpheline_leve(tmp_path: Path) -> None:
    """Une association dont le rec_id n'existe pas : le texte a disparu."""
    _recs("GM2026-V-X-01").write_csv(tmp_path / "recommendations_curated.csv")
    _codes([("GM2026-V-INEXISTANT-99", "I63")]).write_csv(
        tmp_path / "recommendation_codes_curated.csv"
    )
    with pytest.raises(CurationError, match="rec_id inexistant"):
        charge_tables_curees(tmp_path)


def test_sortie_triee_et_deterministe(merged: pl.DataFrame) -> None:
    """Même entrée dans un ordre différent → même sortie, à l'octet près."""
    paires = [("GM2026-V-X-01", "I64"), ("GM2026-V-X-01", "I63"), ("GM2026-V-X-02", "I65")]
    recs = _recs("GM2026-V-X-01", "GM2026-V-X-02")
    _, a, _ = construit(recs, _codes(paires), merged)
    _, b, _ = construit(recs.reverse(), _codes(list(reversed(paires))), merged)
    assert a.equals(b)


def test_specificite_est_portee_par_lexpression(merged: pl.DataFrame) -> None:
    """I63.0 (code) et I63 (catégorie) résolvent au même code, pas au même rang.

    C'est tout l'enjeu : `merged.type` vaut `category` dans les deux cas.
    Sans la spécificité issue de l'expression, une consigne de chapitre
    passerait devant une consigne de code.
    """
    _, resolus, _ = construit(
        _recs("GM2026-V-X-01", "GM2026-V-X-02"),
        _codes([("GM2026-V-X-01", "I63.0"), ("GM2026-V-X-02", "I63")]),
        merged,
    )
    par_rec = dict(resolus.filter(pl.col("code") == "I63.0").select("rec_id", "specificite").rows())
    assert par_rec["GM2026-V-X-01"] > par_rec["GM2026-V-X-02"]


def test_statistiques_distinguent_associations_curees_et_couples(merged: pl.DataFrame) -> None:
    """Une association de plage explose en N couples : les deux comptes diffèrent."""
    _, _, rapport = construit(_recs("GM2026-V-X-01"), _codes([("GM2026-V-X-01", "I63")]), merged)
    assert rapport.statistiques["associations_curees"] == 1
    assert rapport.statistiques["couples_rec_code"] == 2


def test_recouvrement_repere_une_cible_interieure_a_une_plage(merged: pl.DataFrame) -> None:
    """Non-régression : l'heuristique doit voir l'INTÉRIEUR d'une plage.

    Première version : les cibles étaient dérivées des bornes de
    l'expression. « I63-I64 » ne donnait que I63 et I64 ; une exclusion
    renvoyant à un code intermédiaire n'était jamais repérée, et le
    rapport affichait « aucun recouvrement » alors que la mesure ne
    mesurait rien. Les cibles viennent donc des codes RÉSOLUS.
    """
    codes = pl.DataFrame(
        {
            "rec_id": ["GM2026-V-X-01", "GM2026-V-X-01"],
            "code_expr": ["I63-I64", "I65"],
            "role": ["contexte", "interdit_association"],
            "centralite": ["sujet", "sujet"],
            "condition": [None, None],
        },
        schema_overrides={"condition": pl.String},
    )
    flat = pl.DataFrame(
        {
            "code": ["I65"],
            "type": ["exclusion"],
            "texte": ["entraînant un infarctus cérébral (I63.-)"],
            "source": ["ANS"],
        }
    )
    _, _, rapport = construit(_recs("GM2026-V-X-01"), codes, merged, flat)
    assert len(rapport.recouvrement_potentiel) == 1
    assert rapport.recouvrement_potentiel[0]["reference_cible_meme_consigne"] == "oui"
