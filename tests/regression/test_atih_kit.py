"""Le kit ATIH 2025 réel face à la table de notation et au maître.

1. Le kit charge entièrement et ses effectifs sont ceux du `cim.pdf`
   (cinq types, 401 codes supprimés, 40 419 autorisés).
2. **Deux sens sur le kit entier** : compacte -> maître -> compacte est
   l'identité sur 42 897 codes, et l'écriture du maître y est injective.
3. **Deux sens sur le maître** : sur tout nœud `category` du nested set
   qui a une compacte, maître -> compacte -> maître est l'identité — la
   table décrit TOUTES les écritures du maître, pas seulement les 89
   divergences mesurées en phase 1 ; et la compacte est injective.
4. `atih_codes.parquet` existe, valide son schéma, porte sa version.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pyarrow.parquet as pq
import pytest

from recode_icd.loaders.atih import build_atih_codes, load_atih_kit
from recode_icd.loaders.schemas import AtihCodesSchema
from recode_icd.notations import Notations, charge_notations

pytestmark = pytest.mark.regression

_RACINE = Path(__file__).resolve().parents[2]
_KIT = _RACINE / "data" / "CIM_ATIH_2025" / "LIBCIM10MULTI.TXT"
_PROCESSED = _RACINE / "referentials" / "processed"


@pytest.fixture(scope="module")
def notations() -> Notations:
    return charge_notations()


@pytest.fixture(scope="module")
def kit() -> pl.DataFrame:
    if not _KIT.is_file():
        pytest.skip(f"{_KIT} absent.")
    return load_atih_kit(_KIT)


@pytest.fixture(scope="module")
def atih_codes(kit: pl.DataFrame, notations: Notations) -> pl.DataFrame:
    return build_atih_codes(kit, notations)


@pytest.fixture(scope="module")
def merged_codes() -> pl.DataFrame:
    path = _PROCESSED / "merged_codes.parquet"
    if not path.is_file():
        pytest.skip(f"{path} absent.")
    return pl.read_parquet(path)


def test_le_kit_charge_entierement(kit: pl.DataFrame, atih_codes: pl.DataFrame) -> None:
    assert kit.height == 42_897
    assert dict(kit.group_by("type_mco").len().sort("type_mco").rows()) == {
        0: 13_366,
        1: 441,
        2: 26_536,
        3: 2_478,
        4: 76,
    }
    assert int(atih_codes["supprime"].sum()) == 401
    assert set(atih_codes.filter(pl.col("supprime"))["type_mco"].to_list()) == {3}
    assert int(atih_codes["codable_mco"].sum()) == 40_419


def test_compacte_maitre_compacte_est_lidentite_sur_le_kit(
    atih_codes: pl.DataFrame, notations: Notations
) -> None:
    fautifs = [
        (c, m)
        for c, m in zip(atih_codes["code_atih"], atih_codes["code"], strict=True)
        if notations.cle_compacte(m) != c
    ]
    assert not fautifs, fautifs[:10]
    assert atih_codes["code"].n_unique() == atih_codes.height


def test_maitre_compacte_maitre_est_lidentite_sur_le_nested_set(
    merged_codes: pl.DataFrame, notations: Notations
) -> None:
    """La table décrit toutes les écritures du maître, sans exception."""
    categories = merged_codes.filter(pl.col("type") == "category")["code"].to_list()
    cles: dict[str, str] = {}
    fautifs: list[tuple[str, str | None]] = []
    collisions: list[tuple[str, str, str]] = []
    for code in categories:
        cle = notations.cle_compacte(code)
        if cle is None:
            continue
        if notations.ecriture_maitre(cle) != code:
            fautifs.append((code, cle))
        if cle in cles:
            collisions.append((cle, cles[cle], code))
        cles[cle] = code
    assert not fautifs, f"{len(fautifs)} écriture(s) du maître non décrite(s) : {fautifs[:10]}"
    assert not collisions, collisions[:5]
    sans_cle = [c for c in categories if notations.cle_compacte(c) is None]
    assert set(sans_cle) == {
        "O04.-0",
        "O04.-1",
        "O04.-2",
        "O04.-3",
        "M62.8-0",
        "M62.8-8",
        "S37.8-0",
        "S37.8-8",
    }, "les seuls nœuds sans compacte sont les huit regroupements à tiret"


def test_le_parquet_existe_et_porte_sa_version() -> None:
    path = _PROCESSED / "atih_codes.parquet"
    if not path.is_file():
        pytest.skip(f"{path} absent. Lancer `uv run recode-icd build atih`.")
    AtihCodesSchema.validate(pl.read_parquet(path))
    metadata = {k.decode(): v.decode() for k, v in (pq.read_schema(path).metadata or {}).items()}
    assert metadata["atih_kit_version"] == "2025"
