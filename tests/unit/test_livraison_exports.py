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


# ----------------------------------------------------------------------
# descendants_codables.csv (phase B, recadrage RF 2026-10-18)
# ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def descendants(atih: pl.DataFrame) -> pl.DataFrame:
    from recode_icd.couverture import charge_contexte
    from recode_icd.livraison import construit_descendants_codables

    return construit_descendants_codables(charge_contexte(), atih, "abc1234")


def _liste(descendants: pl.DataFrame, noeud: str) -> list[str]:
    return descendants.filter(pl.col("noeud_atih") == noeud)["code_atih"].to_list()


def test_descendants_temoins_du_brief(descendants: pl.DataFrame, atih: pl.DataFrame) -> None:
    assert _liste(descendants, "Z992") == ["Z992+0", "Z992+1", "Z992+8"], (
        "père CODABLE à descendants plus précis — régime affinage"
    )
    assert _liste(descendants, "R521") == ["R5210", "R5218"]
    e11 = _liste(descendants, "E11")
    assert len(e11) == 20 and "E1100" in e11, "père interdit — régime correction"
    # Notation divergente (O04 : 4e/5e caractères inversés au maître) :
    # les descendants sortent bien en forme kit (O0400…O0495).
    o04 = _liste(descendants, "O04")
    assert "O0490" in o04 and len(o04) == 40
    # F01/F02 — les plus longs : exacts au compte du kit.
    attendu_f01 = atih.filter(
        pl.col("codable_mco") & pl.col("code_atih").str.starts_with("F01")
    ).height
    assert len(_liste(descendants, "F01")) == attendu_f01 == 126


def test_descendants_m142_absent_le_kit_fait_loi(descendants: pl.DataFrame) -> None:
    """Le kit 2025 ne connaît pas les M14.2x : M142 n'a AUCUN descendant
    codable — un nœud absent du fichier ne se corrige pas, il est déjà
    au bon niveau (les scénarios citant M1427/M1467 citent des codes
    non codables en MCO : à instruire côté générateur)."""
    assert _liste(descendants, "M142") == []
    from recode_icd.couverture import charge_contexte, resoudre_code

    assert resoudre_code("M1427", charge_contexte()).statut == "inconnu_atih"


def test_descendants_invariant_resolveur(descendants: pl.DataFrame, atih: pl.DataFrame) -> None:
    """Pour tout nœud NON codable : l'export == resoudre_code(...).codes_avec_fiche."""
    from recode_icd.couverture import charge_contexte, resoudre_code

    ctx = charge_contexte()
    vers_kit = dict(atih.select("code", "code_atih").iter_rows())
    for noeud in ("E11", "R521", "A00", "U071"):
        resolution = resoudre_code(noeud, ctx)
        attendu = sorted(vers_kit[c] for c in resolution.codes_avec_fiche if c in vers_kit)
        assert sorted(_liste(descendants, noeud)) == attendu, noeud
