"""Injection des codes du kit ATIH dans le nested set OWL (chantier couverture ATIH, D3).

Existence du code : OWL_ANS, fallback ATIH — codables, absents de
l'ANS, hors chapitre XX, rattachés à leur ancêtre le plus proche. Ce
qui est verrouillé : le choix de l'ancêtre par troncature, le filtre
(codable, absent, hors XX), l'erreur bruyante sans ancêtre, et le
nested set recalculé avec le code injecté à sa place, `source_existence`
à l'appui.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd.loaders.owl import (
    ATIH_URI_PREFIX,
    codes_atih_a_injecter,
    load_codes,
    parent_au_maitre,
)

pytestmark = pytest.mark.unit

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "owl_sample.rdf"


def _atih(rows: list[tuple[str, str, int, bool, str]]) -> pl.DataFrame:
    """(code, code_atih, type_mco, codable_mco, libelle_long)."""
    return pl.DataFrame(
        rows,
        schema={
            "code": pl.String,
            "code_atih": pl.String,
            "type_mco": pl.Int64,
            "codable_mco": pl.Boolean,
            "libelle_long": pl.String,
        },
        orient="row",
    ).with_columns(pl.lit("2025").alias("millesime"), pl.lit("codable").alias("statut_mco"))


@pytest.mark.parametrize(
    ("code", "attendu"),
    [
        ("I70.00", "I70.0"),
        ("J96.100", "J96.10"),
        ("M45+0", "M45"),
        ("M62.80", "M62.8"),
        ("M11.90", "M11.9"),
        ("A99.9", None),
    ],
)
def test_parent_au_maitre_par_troncature(code: str, attendu: str | None) -> None:
    codes = {"I70", "I70.0", "J96", "J96.1", "J96.10", "M45", "M62", "M62.8", "M11", "M11.9"}
    assert parent_au_maitre(code, codes) == attendu


def test_codes_a_injecter_filtre_codables_absents_hors_xx() -> None:
    presents = {"I70", "I70.0", "W00"}
    atih = _atih(
        [
            ("I70.00", "I7000", 0, True, "Athérosclérose de l'aorte, sans gangrène"),
            ("I70.0", "I700", 3, False, "déjà présent"),
            ("O04.0", "O040", 3, False, "type 3 absent : jamais injecté"),
            ("W00.0", "W000", 2, True, "chapitre XX : composition, pas injection"),
        ]
    )
    out = codes_atih_a_injecter(atih, presents)
    assert out.select("code", "parent").rows() == [("I70.00", "I70.0")]
    assert out["libelle"][0].startswith("Athérosclérose")


def test_un_code_sans_ancetre_est_une_erreur_bruyante() -> None:
    atih = _atih([("Q99.99", "Q9999", 0, True, "sans catégorie au maître")])
    with pytest.raises(ValueError, match="sans ancêtre"):
        codes_atih_a_injecter(atih, {"A00"})


def test_load_codes_injecte_le_code_a_sa_place_dans_le_nested_set() -> None:
    """`F02.01` (synthétique) sous `F02.0`, à côté de `F02.00` du fixture."""
    atih = _atih([("F02.01", "F0201", 0, True, "Démence de la maladie de Pick, sévère")])
    sans = load_codes(FIXTURE)
    avec = load_codes(FIXTURE, atih)
    assert avec.height == sans.height + 1
    assert set(sans["source_existence"].to_list()) == {"OWL_ANS"}
    ligne = avec.filter(pl.col("code") == "F02.01").row(0, named=True)
    assert ligne["source_existence"] == "ATIH"
    assert ligne["label"] == "Démence de la maladie de Pick, sévère"
    assert ligne["path"].endswith("/F02/F02.0/F02.01")
    parent = avec.filter(pl.col("code") == "F02.0").row(0, named=True)
    assert parent["left"] < ligne["left"] < ligne["right"] < parent["right"]
    assert ligne["right"] == ligne["left"] + 1, "injecté comme feuille"
    # Le tri des enfants est par code : F02.00 avant F02.01, déterminisme.
    f0200 = avec.filter(pl.col("code") == "F02.00").row(0, named=True)
    assert f0200["left"] < ligne["left"]
    assert avec.equals(load_codes(FIXTURE, atih)), "byte-déterministe"
    assert ATIH_URI_PREFIX.startswith("http://")
