"""Régression sur les flags `is_dagger_in_pair` / `is_asterisk_in_pair`
introduits par la refonte 2026-05-30.

Codes témoins vérifiés (cf docs/sessions/2026-05-30_refonte_dagger_asterisk.md
section 8) :

| Code  | is_dagger_in_pair | is_asterisk_in_pair | Remarque                  |
|-------|-------------------|---------------------|---------------------------|
| A01.0 | True              | False               | 3 paires (cas critique)   |
| G01   | False             | True                | 12 paires (×12 éliminé)   |
| A18.1 | True              | False               | Fil rouge walkthrough     |
| N33.0 | False             | True                | Astérisque de A18.1       |
| E10.2 | True              | False               | Couple independent        |
| A17.8 | True              | False               | Subordinate (curation)    |
| G05.0 | False             | True                | Astérisque de A17.8       |
| N08.3 | False             | True                | Astérisque de E10.2       |
| A52.7 | True              | False               | Code-fourre-tout dague    |
| L62.8 | False             | True                | Non pointé (daget=F)      |
| N16.8 | False             | True                | Non pointé, témoin riche  |
| I10   | False             | False               | Code standard sans paire  |
| Z00.0 | False             | False               | Chapitre XXI sans paire   |

`L62` lui-même a été retiré des témoins (2026-08-09) : c'est un nœud
intermédiaire (enfants L62.0 et L62.8), donc absent du CSV, et le test
se contentait de skipper. Il est remplacé par `L62.8`, son jumeau
sémantique exact dans DAGSTAR (`dagger_code=null`,
`redundancy_level=none`), plus `N16.8` comme témoin non pointé riche.
Son absence est désormais affirmée par `test_l62_absent_du_csv`.

Aussi : tests de non-régression volumétrique sur A01.0 et G01 (cibles
~36 et ~16 lignes, fourchettes prudentes pour absorber la dédup 15,8 %)
et test d'unicité globale.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.regression


_DAGGER_TRUE = {"A01.0", "A18.1", "E10.2", "A17.8", "A52.7"}
_ASTERISK_TRUE = {"G01", "N33.0", "G05.0", "N08.3", "L62.8", "N16.8"}
_BOTH_FALSE = {"I10", "Z00.0"}


@pytest.mark.parametrize("code", sorted(_DAGGER_TRUE))
def test_is_dagger_in_pair_true(csv_final_df: pl.DataFrame, code: str) -> None:
    """Codes côté dague d'au moins une paire DAGSTAR (daget ∈ {S, T, U})."""
    sub = csv_final_df.filter(pl.col("code") == code)
    assert not sub.is_empty(), f"{code} (code témoin) absent du CSV final"
    bad = sub.filter(~pl.col("is_dagger_in_pair"))
    assert bad.is_empty(), (
        f"{code} doit avoir is_dagger_in_pair=True sur toutes ses lignes ; "
        f"{bad.height} contre-exemples"
    )


@pytest.mark.parametrize("code", sorted(_ASTERISK_TRUE))
def test_is_asterisk_in_pair_true(csv_final_df: pl.DataFrame, code: str) -> None:
    """Codes côté astérisque d'au moins une paire DAGSTAR (daget ∈ {F, G, H}).
    Inclut L62.8 et N16.8 (daget=F, assoc=0, cas non pointé)."""
    sub = csv_final_df.filter(pl.col("code") == code)
    assert not sub.is_empty(), f"{code} (code témoin) absent du CSV final"
    bad = sub.filter(~pl.col("is_asterisk_in_pair"))
    assert bad.is_empty(), (
        f"{code} doit avoir is_asterisk_in_pair=True sur toutes ses lignes ; "
        f"{bad.height} contre-exemples"
    )


def test_l62_absent_du_csv(csv_final_df: pl.DataFrame) -> None:
    """L62 est un nœud intermédiaire, donc hors du CSV — fait assumé.

    L62 porte deux enfants (L62.0, L62.8) et n'est donc pas une feuille
    stricte du nested set ; `_leaf_codes()` l'élimine. Décision RF du
    2026-05-25 : on reste sur les codes terminaux, cf
    `docs/backlog/inclure_codes_intermediaires.md`.

    Ce test verrouille l'état actuel plutôt que de le laisser passer en
    skip silencieux. **Si le backlog est implémenté (option B), ce test
    doit être inversé** et L62 réintégré dans `_ASTERISK_TRUE`.
    """
    assert csv_final_df.filter(pl.col("code") == "L62").is_empty(), (
        "L62 est présent dans le CSV : le backlog `inclure_codes_intermediaires` "
        "a-t-il été implémenté ? Si oui, inverser ce test et remettre L62 "
        "dans _ASTERISK_TRUE."
    )


@pytest.mark.parametrize("code", sorted(_BOTH_FALSE))
def test_no_dagger_asterisk_pair(csv_final_df: pl.DataFrame, code: str) -> None:
    """Codes sans paire DAGSTAR : les deux flags doivent être False."""
    sub = csv_final_df.filter(pl.col("code") == code)
    assert not sub.is_empty(), f"{code} (code témoin) absent du CSV final"
    assert sub.filter(pl.col("is_dagger_in_pair")).is_empty()
    assert sub.filter(pl.col("is_asterisk_in_pair")).is_empty()


def test_a01_0_volumetry_after_refonte(csv_final_df: pl.DataFrame) -> None:
    """A01.0 (fil rouge du diagnostic) : 3 paires DAGSTAR. Avant
    refonte : 108 lignes (×3 expansion). Après : ~36 lignes."""
    sub = csv_final_df.filter(pl.col("code") == "A01.0")
    assert 25 <= sub.height <= 50, (
        f"A01.0 attendu 25-50 lignes après refonte (cible ~36), "
        f"obtenu {sub.height}"
    )


def test_g01_volumetry_after_refonte(csv_final_df: pl.DataFrame) -> None:
    """G01 (cas extrême) : 12 paires DAGSTAR côté astérisque. Avant
    refonte : 192 lignes (×12 expansion). Après : ~16 lignes."""
    sub = csv_final_df.filter(pl.col("code") == "G01")
    assert 10 <= sub.height <= 25, (
        f"G01 attendu 10-25 lignes après refonte (cible ~16), "
        f"obtenu {sub.height}"
    )


def test_csv_unique_per_note(csv_final_df: pl.DataFrame) -> None:
    """Refonte 2026-05-30 : la suppression de l'expansion doit garantir
    l'unicité de (code, type, source, texte, source_level,
    inherited_from_code) — plus de doublons résiduels dans le CSV."""
    key = ["code", "type", "source", "texte", "source_level", "inherited_from_code"]
    duplicates = (
        csv_final_df.group_by(key).len().filter(pl.col("len") > 1)
    )
    assert duplicates.is_empty(), (
        f"{duplicates.height} clés (code,type,source,texte,source_level,"
        f"inherited_from_code) dupliquées dans le CSV — la refonte "
        f"dague/astérisque devrait avoir éliminé toute duplication"
    )
