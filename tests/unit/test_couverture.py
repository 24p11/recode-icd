"""Résolveur des consommateurs (`couverture.resoudre_code`) sur données synthétiques.

Chaque statut de résolution a son cas ; la réponse est toujours
motivée et porte de quoi se replier (feuilles avec fiche, ancêtre).
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from recode_icd.couverture import (
    STATUTS_RESOLUTION,
    ContexteResolution,
    Resolution,
    journalise,
    resoudre_code,
)
from recode_icd.notations import charge_notations

pytestmark = pytest.mark.unit


def _atih(rows: list[tuple[str, int, str, bool, bool, str | None, str]]) -> pl.DataFrame:
    return pl.DataFrame(
        rows,
        schema={
            "code": pl.String,
            "type_mco": pl.Int64,
            "statut_mco": pl.String,
            "codable_mco": pl.Boolean,
            "supprime": pl.Boolean,
            "supprime_millesime": pl.String,
            "libelle_long": pl.String,
        },
        orient="row",
    )


def _merged(rows: list[tuple[str, str, int, int]]) -> pl.DataFrame:
    return pl.DataFrame(
        rows,
        schema={"code": pl.String, "label": pl.String, "left": pl.Int64, "right": pl.Int64},
        orient="row",
    )


@pytest.fixture(scope="module")
def ctx() -> ContexteResolution:
    """Un mini-référentiel qui exerce tous les statuts.

    M00 (1,10) : M00.0 (2,7) intermédiaire codable → M00.00 (3,4) fiche,
    M00.01 (5,6) fiche ; M00.9 (8,9) feuille codable sans fiche.
    W00 (11,12) père interdit ; M07.20 (13,14) supprimé ; M16.00 (15,16)
    inconnu du kit mais avec fiche ; O04.-0.9 (17,18) fiche.
    """
    atih = _atih(
        [
            ("M00", 3, "pere_interdit", False, False, None, "Arthrite à pyogènes"),
            ("M00.0", 0, "codable", True, False, None, "Arthrite à staphylocoques"),
            ("M00.00", 0, "codable", True, False, None, "… sièges multiples"),
            ("M00.01", 0, "codable", True, False, None, "… région scapulaire"),
            ("M00.9", 0, "codable", True, False, None, "Arthrite à pyogènes, SP"),
            ("W00", 3, "pere_interdit", False, False, None, "Chute de plain-pied"),
            ("W00.0", 2, "cause_externe", True, False, None, "Chute…, domicile"),
            ("M07.20", 3, "supprime", False, True, "09", "Spondylite psoriasique"),
            ("O04.-0.9", 0, "codable", True, False, None, "IVG sans complication"),
            ("I70.00", 0, "codable", True, False, None, "Athérosclérose aorte sans gangrène"),
            ("I70.0", 3, "pere_interdit", False, False, None, "Athérosclérose de l'aorte"),
        ]
    )
    merged = _merged(
        [
            ("M00", "Arthrite à pyogènes", 1, 10),
            ("M00.0", "Arthrite à staphylocoques", 2, 7),
            ("M00.00", "sièges multiples", 3, 4),
            ("M00.01", "région scapulaire", 5, 6),
            ("M00.9", "Arthrite à pyogènes, SP", 8, 9),
            ("W00", "Chute de plain-pied", 11, 12),
            ("M07.20", "Spondylite psoriasique", 13, 14),
            ("M16.00", "Coxarthrose", 15, 16),
            ("O04.-0.9", "IVG sans complication", 17, 18),
            ("I70.0", "Athérosclérose de l'aorte", 19, 20),
        ]
    )
    fiches = {c: f"X/{c}.md" for c in ("M00.00", "M00.01", "M07.20", "M16.00", "O04.-0.9", "I70.0")}
    return ContexteResolution(charge_notations(), atih, merged, fiches, "lib")


@pytest.mark.parametrize(
    ("saisie", "statut", "code"),
    [
        ("M0000", "fiche", "M00.00"),
        ("M00.00", "fiche", "M00.00"),
        ("O0490", "fiche", "O04.-0.9"),
        ("O04.90", "fiche", "O04.-0.9"),
        ("o04.-0.9", "fiche", "O04.-0.9"),
        ("M000", "intermediaire", "M00.0"),
        ("M00.9", "sans_ligne", "M00.9"),
        ("W00", "pere_interdit", "W00"),
        ("W000", "absent_du_maitre", "W00.0"),  # sans table de composition : absent, motivé
        ("I7000", "absent_du_maitre", "I70.00"),
        ("Z99.9", "inconnu", "Z99.9"),
        ("O04.123", "inconnu", "O04.123"),  # plausible, simplement inconnu
        ("O4", "notation_invalide", None),
        ("S37.8-3", "inconnu", "S37.8-3"),  # forme de nœud, inconnu
        ("A00-1-2", "notation_invalide", None),
    ],
)
def test_chaque_statut(ctx: ContexteResolution, saisie: str, statut: str, code: str | None) -> None:
    r = resoudre_code(saisie, ctx)
    assert r.statut == statut, r
    assert r.code == code
    assert r.raison, "toujours motivée"
    assert statut in STATUTS_RESOLUTION


def test_lintermediaire_rend_ses_feuilles_avec_fiche(ctx: ContexteResolution) -> None:
    r = resoudre_code("M00.0", ctx)
    assert r.codes_avec_fiche == ("M00.00", "M00.01")
    assert r.codable_mco is True and r.statut_mco == "codable"


def test_le_pere_interdit_est_negatif_meme_sans_enfant_au_maitre(ctx: ContexteResolution) -> None:
    r = resoudre_code("W00", ctx)
    assert r.negative and r.codes_avec_fiche == ()


def test_la_fiche_dun_code_non_codable_avertit(ctx: ContexteResolution) -> None:
    """M07.20 (supprimé) et M16.00 (inconnu du kit) ont une fiche : la
    réponse est `fiche`, mais `codable_mco` est faux et la raison le dit."""
    supprime = resoudre_code("M07.20", ctx)
    assert supprime.statut == "fiche" and supprime.codable_mco is False
    assert "supprimé" in supprime.raison
    inconnu = resoudre_code("M16.00", ctx)
    assert inconnu.statut == "fiche" and inconnu.statut_mco == "inconnu_atih"
    assert inconnu.codable_mco is False


def test_le_tronc_xx_et_labsent_portent_leur_ancetre(ctx: ContexteResolution) -> None:
    xx = resoudre_code("W000", ctx)
    assert xx.ancetre == "W00" and xx.code_atih == "W000"
    assert xx.statut == "absent_du_maitre", "sans table de composition, pas de composition devinée"
    absent = resoudre_code("I7000", ctx)
    assert absent.ancetre == "I70.0" and absent.codes_avec_fiche == ("I70.0",)


def test_journal_ne_garde_que_les_negatives(ctx: ContexteResolution, tmp_path: Path) -> None:
    journal = tmp_path / "usage" / "resolutions.jsonl"
    journalise(resoudre_code("M0000", ctx), journal)
    assert not journal.exists(), "une réponse positive ne se journalise pas"
    journalise(resoudre_code("M000", ctx), journal)
    journalise(resoudre_code("Z99.9", ctx), journal)
    lignes = [json.loads(ligne) for ligne in journal.read_text(encoding="utf-8").splitlines()]
    assert [ligne["statut"] for ligne in lignes] == ["intermediaire", "inconnu"]
    assert all("horodatage" in ligne and ligne["raison"] for ligne in lignes)


def test_to_json_est_complet(ctx: ContexteResolution) -> None:
    r = resoudre_code("M000", ctx)
    assert json.loads(r.to_json())["codes_avec_fiche"] == ["M00.00", "M00.01"]
    assert isinstance(r, Resolution)


# ----------------------------------------------------------------------
# Chapitre XX par composition (D5) : résolveur et invariant I2 reformulé
# ----------------------------------------------------------------------


def _composition_synthetique():  # type: ignore[no-untyped-def]
    from recode_icd.composition import Composition

    troncs = pl.DataFrame(
        {
            "tronc": ["W00"],
            "tronc_atih": ["W00"],
            "patron": ["lieu_activite"],
            "positions": [["lieu", "activite"]],
            "forme_plus": [False],
            "classe": ["tronc_composition"],
            "n_codes_composes": [2],
            "libelle": ["Chute de plain-pied"],
            "valeurs_lieu": ["0"],
            "valeurs_activite": ["9"],
        }
    )
    valeurs = pl.DataFrame(
        {
            "tronc": [None, None],
            "table": ["lieu", "activite"],
            "valeur": ["0", "9"],
            "libelle": ["domicile", "en participant à une activité non précisée"],
        },
        schema={"tronc": pl.String, "table": pl.String, "valeur": pl.String, "libelle": pl.String},
    )
    codes = pl.DataFrame(
        {
            "code_atih": ["W000", "W0009"],
            "code": ["W00.0", "W00.09"],
            "tronc": ["W00", "W00"],
            "lieu": ["0", "0"],
            "activite": [None, "9"],
            "precision": [None, None],
            "forme_plus": [False, False],
        },
        schema={
            "code_atih": pl.String,
            "code": pl.String,
            "tronc": pl.String,
            "lieu": pl.String,
            "activite": pl.String,
            "precision": pl.String,
            "forme_plus": pl.Boolean,
        },
    )
    return Composition(
        troncs=troncs,
        valeurs=valeurs,
        codes=codes,
        variantes=pl.DataFrame(),
        patrons=pl.DataFrame(),
    )


@pytest.fixture(scope="module")
def ctx_xx(ctx: ContexteResolution) -> ContexteResolution:
    from dataclasses import replace

    return replace(ctx, composition=_composition_synthetique())


def test_un_code_compose_valide_rend_le_tronc_et_sa_decomposition(
    ctx_xx: ContexteResolution,
) -> None:
    r = resoudre_code("W0009", ctx_xx)
    assert r.statut == "compose" and not r.negative
    assert r.ancetre == "W00" and r.composition["tronc"] == "W00"
    assert r.composition["lieu"] == ("0", "domicile")
    assert r.composition["activite"] == ("9", "en participant à une activité non précisée")
    assert "tronc W00 + lieu 0" in r.raison


def test_un_suffixe_invalide_est_rejete_avec_sa_raison(ctx_xx: ContexteResolution) -> None:
    r = resoudre_code("W0005", ctx_xx)
    assert r.statut == "composition_invalide" and r.negative
    assert "activite « 5 » hors table" in r.raison and r.ancetre == "W00"


def test_verifie_generation_dans_les_deux_sens() -> None:
    """Garde-fou 1 : les troncs passent, un M07.20 échoue, un faux tronc échoue."""
    from recode_icd.couverture import verifie_generation

    troncs = _composition_synthetique().troncs
    index = pl.DataFrame(
        {
            "code": ["A18.1", "W00", "M07.20", "M16.00", "X06"],
            "statut_mco": ["codable", "pere_interdit", "supprime", "inconnu_atih", "pere_interdit"],
            "classe_generation": [
                "emissible",
                "tronc_composition",
                "emissible",
                "emissible",
                "tronc_composition",
            ],
        }
    )
    violations = verifie_generation(index, troncs)
    assert [v.split(" : ")[0] for v in violations] == ["M07.20", "M16.00", "X06"]
    assert verifie_generation(index.filter(pl.col("code").is_in(["A18.1", "W00"])), troncs) == []
    assert verifie_generation(index.filter(pl.col("code") == "W00"), None) == [
        "W00 : classe tronc_composition sans être un tronc du kit"
    ]
