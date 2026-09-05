"""Le résolveur sur les artefacts réels : témoins de chaque classe de la phase 1."""

from __future__ import annotations

from pathlib import Path

import pytest

from recode_icd.couverture import charge_contexte, resoudre_code

pytestmark = pytest.mark.regression

_RACINE = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def ctx():  # type: ignore[no-untyped-def]
    if not (_RACINE / "referentials/processed/atih_codes.parquet").is_file():
        pytest.skip("atih_codes.parquet absent (`recode-icd build atih`).")
    return charge_contexte()


@pytest.mark.parametrize(
    ("saisie", "statut", "code"),
    [
        ("A181", "fiche", "A18.1"),
        ("A18.1", "fiche", "A18.1"),
        ("O0490", "fiche", "O04.-0.9"),  # famille inversée O04
        ("O04.90", "fiche", "O04.-0.9"),
        ("M62810", "fiche", "M62.8-01"),  # famille inversée M62.8
        ("B24+0", "fiche", "B24.+0"),  # + ponctué
        ("T08+0", "fiche", "T08+0"),  # + non ponctué
        ("U0713", "fiche", "U07.13"),
        ("M000", "intermediaire", "M00.0"),  # codable, subdivisé
        ("F000", "intermediaire", "F00.0"),
        ("U071", "pere_interdit", "U07.1"),  # type 3
        ("A00", "pere_interdit", "A00"),
        ("Z3710", "sans_ligne", "Z37.10"),  # feuille sans ligne (D3)
        ("U822+0", "sans_ligne", "U82.2+0"),
        ("I7000", "absent_du_maitre", "I70.00"),  # extension ATIH absente (D3)
        ("W0004", "tronc_chapitre_xx", "W00.04"),  # chapitre XX (D5)
        ("N069", "inconnu_atih", None),  # hors kit ET sans fiche ? non : N06.9 a une fiche
        ("Z99.99", "inconnu", "Z99.99"),
        ("O04.123", "inconnu", "O04.123"),
        ("XYZ", "notation_invalide", None),
    ],
)
def test_temoins(ctx, saisie: str, statut: str, code: str | None) -> None:  # type: ignore[no-untyped-def]
    r = resoudre_code(saisie, ctx)
    if saisie == "N069":
        # N06.9 est au maître (fiche) mais inconnu du kit : `fiche`, non codable.
        assert r.statut == "fiche" and r.statut_mco == "inconnu_atih" and r.codable_mco is False
        return
    assert r.statut == statut, r
    if code is not None:
        assert r.code == code
    assert r.raison


def test_lintermediaire_m00_0_rend_ses_dix_feuilles(ctx) -> None:  # type: ignore[no-untyped-def]
    r = resoudre_code("M00.0", ctx)
    assert len(r.codes_avec_fiche) == 10 and all(c.startswith("M00.0") for c in r.codes_avec_fiche)


def test_le_tronc_xx_pointe_sur_une_fiche(ctx) -> None:  # type: ignore[no-untyped-def]
    r = resoudre_code("W0004", ctx)
    assert r.ancetre == "W00" and r.codes_avec_fiche == ("W00",)


def test_les_codes_supprimes_ont_encore_une_fiche_avant_d4(ctx) -> None:  # type: ignore[no-untyped-def]
    """Avant D4, M07.20 (SU09) est dans la bibliothèque : `fiche`, avec avertissement."""
    r = resoudre_code("M0720", ctx)
    assert r.statut in ("fiche", "supprime")
    assert r.codable_mco is False and r.statut_mco == "supprime"
