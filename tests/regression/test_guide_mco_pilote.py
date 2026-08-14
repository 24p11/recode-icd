"""Pilote du guide méthodologique MCO : tables curées et Parquet produits.

Deux niveaux de verrou, et ils ne se remplacent pas :

1. **Pandera sur les tables CURÉES** — c'est la vraie porte d'entrée du
   pipeline. Une faute de frappe dans un rôle (`interdit_dp` au lieu de
   `interdit_DP`) doit être arrêtée à la curation, pas découverte trois
   étapes plus loin.
2. **Pandera sur les PARQUET** — le build ne doit pas dégrader ce que la
   curation garantissait.

S'y ajoutent les témoins du pilote, qui vérifient que la sémantique
survit à la résolution.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.loaders.schemas import (
    RecommendationCodesSchema,
    RecommendationsSchema,
    ResolvedRecommendationCodesSchema,
)
from recode_icd.recommendations.build import (
    RECOMMENDATION_CODES_FILENAME,
    RECOMMENDATIONS_FILENAME,
    charge_tables_curees,
)

pytestmark = pytest.mark.regression

_RACINE = Path(__file__).resolve().parents[2]
_CURATION = _RACINE / "data" / "guide_mco"
_PROCESSED = _RACINE / "referentials" / "processed"


@pytest.fixture(scope="module")
def tables_curees() -> tuple[pl.DataFrame, pl.DataFrame]:
    if not (_CURATION / "recommendations_curated.csv").is_file():
        pytest.skip("Tables curées absentes.")
    return charge_tables_curees(_CURATION)


@pytest.fixture(scope="module")
def resolus() -> pl.DataFrame:
    path = _PROCESSED / RECOMMENDATION_CODES_FILENAME
    if not path.is_file():
        pytest.skip(f"{path} absent. Lancer `uv run recode-icd build guide-mco`.")
    return pl.read_parquet(path)


@pytest.fixture(scope="module")
def recommandations() -> pl.DataFrame:
    path = _PROCESSED / RECOMMENDATIONS_FILENAME
    if not path.is_file():
        pytest.skip(f"{path} absent. Lancer `uv run recode-icd build guide-mco`.")
    return pl.read_parquet(path)


def test_tables_curees_valident_pandera(
    tables_curees: tuple[pl.DataFrame, pl.DataFrame],
) -> None:
    recs, codes = tables_curees
    RecommendationsSchema.validate(recs)
    RecommendationCodesSchema.validate(codes)


def test_parquets_valident_pandera(recommandations: pl.DataFrame, resolus: pl.DataFrame) -> None:
    RecommendationsSchema.validate(recommandations)
    ResolvedRecommendationCodesSchema.validate(resolus)


def test_tous_les_rec_id_sont_du_millesime_annonce(recommandations: pl.DataFrame) -> None:
    """Le millésime est structurel : le guide est annuel.

    Un `rec_id` en `GM2026-` avec un `millesime` 2027 signalerait un
    report de consigne non retracé.
    """
    for rec_id, millesime in recommandations.select("rec_id", "millesime").rows():
        assert rec_id.startswith("GM2026-"), rec_id
        assert millesime == "2026-provisoire", (rec_id, millesime)


def test_le_pilote_porte_sur_le_chapitre_v_du_guide(recommandations: pl.DataFrame) -> None:
    """La section AVC est au chapitre V du guide, pas VII.

    La note de conception disait VII ; vérification faite sur le texte
    extrait, le chapitre V commence page imprimée 75 et l'article AVC
    page 78. Le chapitre du guide est encodé dans le `rec_id` : s'il
    change, les identifiants ne sont plus stables.
    """
    assert all(r.startswith("GM2026-V-") for r in recommandations["rec_id"].to_list())


# -- témoins du pilote --------------------------------------------------


def test_z86_70_recoit_son_role_dp(resolus: pl.DataFrame) -> None:
    """AVC-05 : « DP = Z86.70 ; pas de DR »."""
    lignes = resolus.filter(pl.col("code") == "Z86.70")
    assert lignes.height >= 1
    assert "DP" in lignes["role"].to_list()
    assert "GM2026-V-AVC-05" in lignes["rec_id"].to_list()


def test_d62_porte_deux_consignes_a_roles_opposes(resolus: pl.DataFrame) -> None:
    """Cas d'école : D62 est `interdit` dans un cas, `DAS` dans l'autre.

    C'est précisément ce que le modèle doit savoir représenter — la
    sémantique positionnelle vit dans l'association, pas dans le texte.
    Un modèle « une consigne par code » les aurait écrasées.
    """
    roles = dict(resolus.filter(pl.col("code") == "D62").select("rec_id", "role").rows())
    assert roles["GM2026-V-D62-01"] == "interdit"
    assert roles["GM2026-V-D62-02"] == "DAS"


def test_une_plage_atteint_ses_codes_intermediaires(resolus: pl.DataFrame) -> None:
    """« I60-I64 » doit atteindre I63.x, pas seulement les bornes."""
    codes = set(resolus.filter(pl.col("code_expr") == "I60-I64")["code"].to_list())
    assert "I63.0" in codes and "I61.0" in codes and "I64" in codes


def test_specificite_coherente_avec_la_granularite(resolus: pl.DataFrame) -> None:
    """`specificite` et `type_expr` ne peuvent pas diverger."""
    attendu = {"CHAPITRE": 0, "PLAGE": 1, "CATEGORIE": 2, "CODE": 3}
    for type_expr, specificite in resolus.select("type_expr", "specificite").unique().rows():
        assert attendu[type_expr] == specificite
