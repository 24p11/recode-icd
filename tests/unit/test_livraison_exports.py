"""Témoins des exports additifs de la livraison (phase A, chantier codeur).

Les témoins viennent du brief RF du 2026-10-18 :

- `codes.csv` distingue E11 (père interdit, correction obligatoire) de
  Z992 (codable AVEC descendants plus précis — affinage proposé) ;
  comptes exacts contre le kit ; `code_atih` sans trou ;
- `formulations.csv` est coupé APRÈS les filtres de qualité (le
  registre archaïque s'applique : plus d'apoplexie sur I64) et SANS le
  plafond R2 (R51 garde plus de 10 formulations) ;
- le préambule des extensions est généré du kit et dit que « ni »
  n'existe pas.
"""

from __future__ import annotations

import polars as pl
import pytest

from recode_icd.cards import _eager, charge_politique
from recode_icd.livraison import (
    construit_codes_csv,
    construit_formulations_csv,
    redige_preambule_extensions,
)
from recode_icd.utils.loaders_dev import ExplorationContext, load_exploration_context

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def atih() -> pl.DataFrame:
    import pathlib

    chemin = pathlib.Path("referentials/processed/atih_codes.parquet")
    if not chemin.is_file():
        pytest.skip("atih_codes.parquet absent.")
    return pl.read_parquet(chemin)


@pytest.fixture(scope="module")
def ctx() -> ExplorationContext:
    c = load_exploration_context(with_external=True)
    if c.flat is None or c.merged is None:
        pytest.skip("Artefacts pipeline absents.")
    return c


def test_codes_csv_complet_et_discriminant(atih: pl.DataFrame) -> None:
    codes = construit_codes_csv(atih, "abc1234")
    assert codes.height == atih.height, "TOUS les codes du kit, aucune exclusion"
    assert codes["code_atih"].null_count() == 0

    e11 = codes.filter(pl.col("code_atih") == "E11").row(0, named=True)
    z992 = codes.filter(pl.col("code_atih") == "Z992").row(0, named=True)
    z9920 = codes.filter(pl.col("code_atih") == "Z992+0").row(0, named=True)
    assert e11["codable_mco"] is False and e11["statut_mco"] == "pere_interdit"
    assert z992["codable_mco"] is True, "Z992 est codable au kit — affinage, pas correction"
    assert z9920["codable_mco"] is True
    assert set(codes["version_livraison"].unique().to_list()) == {"abc1234"}
    n_codables = codes.filter(pl.col("codable_mco")).height
    assert n_codables == atih.filter(pl.col("codable_mco")).height


def test_formulations_csv_filtre_sans_plafond(ctx: ExplorationContext, atih: pl.DataFrame) -> None:
    outils = charge_politique(_eager(ctx.merged))
    if not outils.registre.ecartees:
        pytest.skip("registre_formulations.yaml absent.")
    formulations, hors_kit = construit_formulations_csv(_eager(ctx.flat), atih, outils, "abc1234")

    i64 = formulations.filter(pl.col("code_atih") == "I64")["formulation"].to_list()
    assert "accident vasculaire cérébral SAI" in i64
    assert all("apoplexie" not in f.lower() for f in i64), (
        "le registre des formulations archaïques s'applique au vivier"
    )

    r51 = formulations.filter(pl.col("code_atih") == "R51")
    assert r51.height > 10, "SANS plafond R2 : R51 garde tout son vivier"

    assert set(formulations.columns) == {
        "code_atih",
        "formulation",
        "source",
        "version_livraison",
    }
    sources = set(formulations["source"].unique().to_list())
    assert "CIM-10" not in sources and "ANS" not in sources, (
        "les sources officielles ne sont pas des formulations"
    )
    assert hors_kit < 100, f"dérive : {hors_kit} formulations sur des codes inconnus du kit"


def test_preambule_extensions_genere_du_kit(atih: pl.DataFrame) -> None:
    preambule = redige_preambule_extensions(atih)
    assert "Z992+0" in preambule, "l'exemple Z992 illustre le père codable"
    assert "« ni » n'existe pas" in preambule
    assert "sémantique transversale" in preambule
