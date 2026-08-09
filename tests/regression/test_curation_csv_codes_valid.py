"""Régression sur le format des codes du CSV de curation
dague/astérisque.

Garde-fou anti-corruption Excel : si une cellule de code dague ou
astérisque est altérée par auto-formatage (ex : "F00" devenu
"0,00 F" via le format monétaire français), ce test détecte la
corruption immédiatement plutôt que de la laisser passer en orpheline
silencieuse dans `reports/curation_applied.csv`.

Diagnostic initial : voir
`docs/sessions/2026-05-25_phase3_dagger_asterisk.md` §4 (cellule G30
→ "0,00 F" corrigée le 2026-05-25).
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.regression


_CURATION_CSV = (
    Path(__file__).resolve().parents[2]
    / "referentials"
    / "curation"
    / "dagger_curation.csv"
)

# Code CIM-10 : lettre + 2 chiffres + suffixe optionnel ATIH
# (point + 1 à 3 chiffres). Couvre G30, F00, A17.8, U07.13 ...
_CODE_RE = re.compile(r"^[A-Z]\d{2}(?:\.\d{1,3})?$")
# Intervalle de codes — légitime côté `dagger_code` pour les cas daget F
# (M49.2* associé à un intervalle A01-A04 par ex.).
_INTERVAL_RE = re.compile(r"^\([A-Z]\d{2}-[A-Z]\d{2}\)$")


def _is_valid_code(value: str | None) -> bool:
    if value is None:
        return False
    return bool(_CODE_RE.match(value) or _INTERVAL_RE.match(value))


@pytest.fixture(scope="module")
def curation_df() -> pl.DataFrame:
    if not _CURATION_CSV.is_file():
        pytest.skip(f"{_CURATION_CSV} absent — test régression skippé.")
    first_line = _CURATION_CSV.read_text(encoding="utf-8").splitlines()[0]
    sep = ";" if first_line.count(";") > first_line.count(",") else ","
    return pl.read_csv(_CURATION_CSV, infer_schema_length=0, separator=sep)


def test_dagger_codes_are_well_formed(curation_df: pl.DataFrame) -> None:
    invalid = [
        c for c in curation_df["dagger_code"].to_list() if not _is_valid_code(c)
    ]
    assert not invalid, (
        f"{len(invalid)} dagger_code mal formé(s) : {invalid[:5]}. "
        "Vérifier qu'Excel n'a pas auto-formaté de cellule (cf historique "
        "G30 → '0,00 F')."
    )


def test_asterisk_codes_are_well_formed(curation_df: pl.DataFrame) -> None:
    invalid = [
        c for c in curation_df["asterisk_code"].to_list() if not _is_valid_code(c)
    ]
    assert not invalid, (
        f"{len(invalid)} asterisk_code mal formé(s) : {invalid[:5]}. "
        "Vérifier qu'Excel n'a pas auto-formaté de cellule (cf historique "
        "G30 → '0,00 F')."
    )


def test_no_invisible_chars_in_codes(curation_df: pl.DataFrame) -> None:
    """Aucun code ne doit contenir d'espace insécable (U+00A0) ou autre
    caractère de contrôle. Le format monétaire FR d'Excel écrit
    `0,00 F` avec NBSP, ce qui peut passer un regex naïf mais pas
    celui-ci."""
    suspicious: list[tuple[str, str]] = []
    for col in ("dagger_code", "asterisk_code"):
        for v in curation_df[col].to_list():
            if v is None:
                continue
            if any(ord(c) < 0x20 or c == "\xa0" for c in v):
                suspicious.append((col, v))
    assert not suspicious, (
        f"Caractères invisibles détectés dans des codes : {suspicious[:5]}"
    )
