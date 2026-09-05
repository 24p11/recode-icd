"""Notations du guide <-> référentiel, sur le VRAI référentiel (arbitrage n° 12).

Les tests unitaires prouvent que la table est cohérente avec elle-même.
Ici on prouve qu'elle est **complète face au référentiel**, dans les
deux sens :

1. chaque nœud et chaque feuille que la table déclare existe dans
   `merged_codes.parquet` — une position déclarée qui n'existerait pas
   résoudrait dans le vide ;
2. chaque code du référentiel sous une catégorie déclarée retraduit vers
   une forme du guide qui reparse vers lui — une position du référentiel
   absente de la table serait non parsable au premier article qui la
   cite.

Puis les témoins de l'article INTERRUPTION DE LA GROSSESSE sur le
Parquet résolu et les rapports de build, et l'invariant absolu de
l'arbitrage : **la table curée ne porte jamais la notation interne du
référentiel** (`Xnn.-<5e>.<4e>`).
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.recommendations.build import RECOMMENDATION_CODES_FILENAME
from recode_icd.recommendations.code_expr import parse_code_expr
from recode_icd.recommendations.notations import Notations, charge_notations

pytestmark = pytest.mark.regression

_RACINE = Path(__file__).resolve().parents[2]
_PROCESSED = _RACINE / "referentials" / "processed"
_REPORTS = _RACINE / "reports"
_CURATION = _RACINE / "data" / "guide_mco"

#: Les cinq expressions de l'arbitrage, telles qu'écrites par le guide.
_DORES_ITG = {
    ("GM2026-V-ITG-02", "O04.90"),
    ("GM2026-V-ITG-05", "O04.4"),
    ("GM2026-V-ITG-07", "O04.-1"),
    ("GM2026-V-ITG-07", "O04.-2"),
    ("GM2026-V-ITG-07", "O04.-3"),
}


@pytest.fixture(scope="module")
def notations() -> Notations:
    return charge_notations()


@pytest.fixture(scope="module")
def merged_codes() -> pl.DataFrame:
    path = _PROCESSED / "merged_codes.parquet"
    if not path.is_file():
        pytest.skip(f"{path} absent.")
    return pl.read_parquet(path)


@pytest.fixture(scope="module")
def resolus() -> pl.DataFrame:
    path = _PROCESSED / RECOMMENDATION_CODES_FILENAME
    if not path.is_file():
        pytest.skip(f"{path} absent. Lancer `uv run recode-icd build guide-mco`.")
    return pl.read_parquet(path)


def _rapport(nom: str) -> pl.DataFrame:
    chemin = _REPORTS / f"{nom}.csv"
    if not chemin.is_file():
        pytest.skip(f"{chemin} absent. Lancer `uv run recode-icd build guide-mco`.")
    return pl.read_csv(chemin, schema_overrides={"code_expr": pl.String})


# -- 1 et 2 : la table face au référentiel, dans les deux sens ------------


def test_chaque_position_declaree_existe_dans_le_referentiel(
    notations: Notations, merged_codes: pl.DataFrame
) -> None:
    codes = set(merged_codes["code"].to_list())
    for cat in notations.categories.values():
        assert cat.categorie in codes
        for cinquieme in cat.cinquiemes:
            assert cat.noeud(cinquieme) in codes, cat.noeud(cinquieme)
            for quatrieme in cat.quatriemes:
                assert cat.feuille(quatrieme, cinquieme) in codes, cat.feuille(quatrieme, cinquieme)


def test_chaque_code_du_referentiel_retraduit_vers_le_guide(
    notations: Notations, merged_codes: pl.DataFrame
) -> None:
    """Sens référentiel -> guide -> référentiel, exhaustif sur la catégorie."""
    for cat in notations.categories.values():
        sous = merged_codes.filter(pl.col("code").str.starts_with(f"{cat.categorie}.-"))
        assert sous.height > 0
        for code in sous["code"].to_list():
            guide = notations.vers_guide(code)
            assert guide is not None, f"{code} n'a pas de notation guide"
            assert parse_code_expr(guide, notations).noeuds == (code,), (code, guide)


# -- témoins d'ITG sur le Parquet résolu ---------------------------------


def test_o04_90_recoit_itg_02_en_dp(resolus: pl.DataFrame) -> None:
    """« O04.90 » du guide atteint la feuille O04.-0.9, en DP, granularité CODE."""
    lignes = resolus.filter(
        (pl.col("code") == "O04.-0.9") & (pl.col("rec_id") == "GM2026-V-ITG-02")
    )
    assert lignes.height == 1
    ligne = lignes.row(0, named=True)
    assert ligne["code_expr"] == "O04.90", "la notation du guide est conservée"
    assert ligne["role"] == "DP"
    assert ligne["type_expr"] == "CODE"


def test_o04_4_atteint_une_feuille_par_cinquieme_position(resolus: pl.DataFrame) -> None:
    """ITG-05 : « O04.4 » = avortement incomplet sans complication, quelle
    que soit la 5e position (IVG, IMG fœtale, maternelle, associée)."""
    lignes = resolus.filter(pl.col("code_expr") == "O04.4")
    assert set(lignes["code"].to_list()) == {"O04.-0.4", "O04.-1.4", "O04.-2.4", "O04.-3.4"}
    assert set(lignes["type_expr"].to_list()) == {"CATEGORIE"}


def test_o04_tiret_1_couvre_ses_dix_feuilles(resolus: pl.DataFrame) -> None:
    """ITG-07 : « O04.-1 » = IMG pour cause fœtale, tous 4e caractères."""
    lignes = resolus.filter(pl.col("code_expr") == "O04.-1")
    codes = lignes["code"].to_list()
    assert len(codes) == 10 and all(c.startswith("O04.-1.") for c in codes)
    assert set(lignes["rec_id"].to_list()) == {"GM2026-V-ITG-07"}


def test_o04_tiret_1_4_est_au_carrefour_ditg_05_et_07(resolus: pl.DataFrame) -> None:
    """La fiche O04.-1.4 reçoit ITG-05 (par O04.4) ET ITG-07 (par O04.-1)."""
    recs = set(resolus.filter(pl.col("code") == "O04.-1.4")["rec_id"].to_list())
    assert {"GM2026-V-ITG-05", "GM2026-V-ITG-07"} <= recs


# -- rapports de build ------------------------------------------------------


def test_aucune_expression_ditg_nest_non_parsable() -> None:
    rapport = _rapport("guide_mco_expressions_non_parsables")
    itg = rapport.filter(pl.col("rec_id").str.starts_with("GM2026-V-ITG-"))
    assert itg.height == 0, itg["code_expr"].to_list()


def test_les_cinq_expressions_ditg_sont_tracees_comme_traduites() -> None:
    """Traduite n'est pas silencieuse : la trace dit ce qui a été traduit."""
    rapport = _rapport("guide_mco_expressions_traduites")
    tracees = set(rapport.select("rec_id", "code_expr").rows())
    assert tracees >= _DORES_ITG, _DORES_ITG - tracees


# -- invariant absolu de l'arbitrage ---------------------------------------


def test_la_table_curee_ne_porte_jamais_la_notation_du_referentiel() -> None:
    """La curation est fidèle à la notation du guide, la résolution traduit.

    Une expression `Xnn.-<5e>.<4e>` dans la table curée serait la notation
    interne du référentiel : elle ne prouverait plus ce que le guide dit.
    Invariant testé sur la table entière, pas sur un cas.
    """
    codes = pl.read_csv(
        _CURATION / "recommendation_codes_curated.csv",
        schema_overrides={"condition": pl.String, "portee": pl.String, "justification": pl.String},
    )
    fautives = codes.filter(pl.col("code_expr").str.contains(r"^[A-Z]\d{2}\.-\d\.\d$"))
    assert fautives.height == 0, fautives.select("rec_id", "code_expr").rows()
