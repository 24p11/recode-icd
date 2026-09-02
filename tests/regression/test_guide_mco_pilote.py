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
def merged_codes() -> pl.DataFrame:
    path = _PROCESSED / "merged_codes.parquet"
    if not path.is_file():
        pytest.skip(f"{path} absent.")
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


# -- témoins ajoutés au versement du pilote complet ---------------------


def test_i64_recoit_sa_condition_demploi(resolus: pl.DataFrame) -> None:
    """AVC-02 : « I64 n'est employé qu'en l'absence de neuro-imagerie ».

    C'est le témoin du rôle `regi` : la consigne régit l'emploi de I64
    sans lui assigner de position. Avant la création du rôle, elle
    n'avait aucune association et n'atteignait donc aucune fiche.
    """
    lignes = resolus.filter(pl.col("code") == "I64")
    roles = dict(lignes.select("rec_id", "role").rows())
    assert roles["GM2026-V-AVC-02"] == "regi"
    assert roles["GM2026-V-AVC-03"] == "contexte", (
        "AVC-03 vise I60-I64 pour situer la consigne, pas pour régir I64 — "
        "si ce rôle bascule, la distinction regi/contexte a été perdue"
    )


def test_toutes_les_feuilles_du_chapitre_xxi_sont_couvertes(
    resolus: pl.DataFrame, merged_codes: pl.DataFrame
) -> None:
    """Une consigne de chapitre descend sur TOUTES ses feuilles.

    Décision actée : les fiches sont injectées telles quelles dans des
    prompts, donc autonomes. Un trou ici signifierait qu'une fiche Z
    ignore les règles générales du chapitre XXI.
    """
    xxi = merged_codes.filter(pl.col("code") == "XXI")
    gauche, droite = int(xxi["left"][0]), int(xxi["right"][0])
    feuilles = merged_codes.filter(
        (pl.col("right") == pl.col("left") + 1)
        & (pl.col("left") >= gauche)
        & (pl.col("right") <= droite)
    )
    non_couvertes = sorted(set(feuilles["code"].to_list()) - set(resolus["code"].to_list()))
    assert not non_couvertes, (
        f"{len(non_couvertes)} feuilles du chapitre XXI sans consigne : {non_couvertes[:5]}"
    )


def test_un_z_non_cite_ne_recoit_que_des_consignes_de_chapitre(
    resolus: pl.DataFrame,
) -> None:
    """Test de complétude ET de maîtrise du bruit.

    `Z23.0` (vaccination contre le choléra) n'est nommé nulle part dans
    l'article du guide. Il doit recevoir les consignes de niveau
    chapitre — sinon la résolution ne descend pas — et **rien d'autre**,
    sinon une consigne fuit hors de son périmètre.

    Depuis l'amendement `portee` (2026-09-02), la seule consigne de
    chapitre à portée « pour tout » est XXI-01 : AVC-14 (domaine de
    choix, `ensemble`) ne descend plus. L'assertion est directe.

    ⚠ Ne pas prendre `Z55.0` comme témoin : il porte des subdivisions,
    ce n'est donc pas une feuille du nested set et il n'apparaît dans
    aucun artefact feuille. Même piège que `U07.1` pour le CSV maître.
    """
    lignes = resolus.filter(pl.col("code") == "Z23.0")
    assert lignes.height > 0, "Z23.0 ne reçoit rien : la résolution ne descend plus"
    assert set(lignes["rec_id"].to_list()) == {"GM2026-V-XXI-01"}, (
        f"Z23.0 reçoit {sorted(set(lignes['rec_id'].to_list()))} alors qu'il n'est "
        f"nommé nulle part dans l'article. Soit une consigne fuit hors de son "
        f"périmètre (doctrine §4.2 bis), soit une association `ensemble` a été "
        f"résolue (portée, §4.2)."
    )


# -- témoins de l'amendement `portee` (2026-09-02) ----------------------


def test_une_association_ensemble_nest_jamais_resolue(resolus: pl.DataFrame) -> None:
    """Invariant ABSOLU : (AVC-14, XXI) ne produit aucune ligne résolue.

    « Le DP appartient au chapitre XXI » est le domaine d'un choix fait
    par le motif de séjour — pas une prescription sur chaque code Z.
    L'association est déclarée `ensemble` dans la table curée ; si une
    ligne résolue réapparaît, la garantie par construction est morte et
    le bug AVC-14/Z23.0 avec elle.
    """
    fuite = resolus.filter((pl.col("rec_id") == "GM2026-V-AVC-14") & (pl.col("code_expr") == "XXI"))
    assert fuite.height == 0, "l'association `ensemble` (AVC-14, XXI) a été résolue"
    assert set(resolus["portee"].to_list()) == {"chaque"}, (
        "toute ligne résolue doit être une prescription « pour tout »"
    )


def test_les_fiches_i69_portent_toujours_avc_14(resolus: pl.DataFrame) -> None:
    """La bascule `ensemble` ne touche que l'association XXI d'AVC-14.

    Son association I69 (« un code de séquelle I69 est placé en DR »)
    régit chaque code de séquelle : elle reste `chaque` et descend sur
    les feuilles I69.x.
    """
    lignes = resolus.filter(pl.col("rec_id") == "GM2026-V-AVC-14")
    assert lignes.height > 0, "AVC-14 a disparu de la table résolue"
    assert set(lignes["code_expr"].to_list()) == {"I69"}
    assert set(lignes["role"].to_list()) == {"DR"}
    assert all(c.startswith("I69") for c in lignes["code"].to_list())


def test_z86_70_conserve_xxi_49(resolus: pl.DataFrame) -> None:
    """XXI-49 (plage Z80-Z92, interdit_DR) reste de portée `chaque`.

    Une interdiction est un « pour tout » par nature (« un DP
    d'antécédent ne justifie JAMAIS de diagnostic relié ») : la bascule
    d'AVC-14 ne doit pas entraîner les plages à rôle d'interdiction.
    """
    lignes = resolus.filter((pl.col("code") == "Z86.70") & (pl.col("rec_id") == "GM2026-V-XXI-49"))
    assert lignes.height == 1
    ligne = lignes.row(0, named=True)
    assert ligne["type_expr"] == "PLAGE"
    assert ligne["role"] == "interdit_DR"
    assert ligne["portee"] == "chaque"


def test_lassociation_ensemble_est_au_rapport_de_build() -> None:
    """Non résolue ≠ silencieuse : la trace vit au rapport, justifiée."""
    chemin = _RACINE / "reports" / "guide_mco_associations_ensemble.csv"
    if not chemin.is_file():
        pytest.skip(f"{chemin} absent. Lancer `uv run recode-icd build guide-mco`.")
    rapport = pl.read_csv(chemin)
    lignes = rapport.filter(pl.col("rec_id") == "GM2026-V-AVC-14")
    assert lignes.height == 1
    ligne = lignes.row(0, named=True)
    assert ligne["code_expr"] == "XXI"
    assert ligne["n_codes_domaine"] > 0
    assert str(ligne["justification"]).strip(), "une bascule de portée porte son pourquoi"


def test_les_dix_roles_du_catalogue_sont_tous_admis(resolus: pl.DataFrame) -> None:
    """Le pilote emploie effectivement `regi` et `interdit_DAS`.

    Les deux modalités ont été créées pour ce pilote : si elles
    disparaissaient des données, c'est que la migration des rôles aurait
    été défaite.
    """
    employes = set(resolus["role"].to_list())
    assert "regi" in employes and "interdit_DAS" in employes
    assert "contexte" in employes, (
        "plus aucun `contexte` : le rôle a probablement été absorbé par `regi`, "
        "alors qu'ils répondent à deux questions différentes"
    )
