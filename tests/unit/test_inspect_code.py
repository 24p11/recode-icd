"""Smoke tests pour l'outil d'exploration `inspect_code`.

Pas de validation exhaustive (outil interactif) : on vérifie que les
4 cas d'usage (code exact, code absent, préfixe, liste) s'exécutent
sans erreur et produisent une sortie non vide.

Les tests passent un `ctx` chargé SANS sources externes (rapide) :
le BLOC 2 externes affiche alors un message "(non chargées)" — ce qui
suffit pour le smoke test et évite le coût ~5 s du parse XML/xlsx.
Skip automatique si les artefacts du pipeline sont absents.
"""

from __future__ import annotations

import pytest

from recode_icd.utils.loaders_dev import (
    ExplorationContext,
    inspect_code,
    load_exploration_context,
)

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def ctx() -> ExplorationContext:
    c = load_exploration_context()
    if c.flat is None or c.merged is None:
        pytest.skip("Artefacts pipeline absents — lancer build flat-csv d'abord.")
    return c


def test_inspect_code_exact_smoke(ctx: ExplorationContext, capsys) -> None:  # type: ignore[no-untyped-def]
    inspect_code("A18.1", ctx=ctx)
    out = capsys.readouterr().out
    assert "A18.1" in out
    assert "BLOC 1" in out and "BLOC 4" in out


def test_inspect_code_absent_does_not_crash(ctx: ExplorationContext, capsys) -> None:  # type: ignore[no-untyped-def]
    """A90 a été retiré de la classification ANS 2025 → absent du CSV.
    inspect_code ne doit pas planter et doit signaler l'absence."""
    inspect_code("A90", ctx=ctx)
    out = capsys.readouterr().out
    assert "A90" in out
    assert "absent du CSV final" in out


def test_inspect_code_prefix(ctx: ExplorationContext, capsys) -> None:  # type: ignore[no-untyped-def]
    """Le préfixe 'A18' doit matcher plusieurs sous-codes (A18.0, A18.1, ...)."""
    inspect_code("A18", ctx=ctx)
    out = capsys.readouterr().out
    assert "A18.0" in out
    assert "A18.1" in out
    # Plusieurs boîtes de code distinctes affichées.
    assert out.count("BLOC 1 : IDENTITÉ") >= 2


def test_inspect_code_list(ctx: ExplorationContext, capsys) -> None:  # type: ignore[no-untyped-def]
    inspect_code(["A18.1", "N33.0"], ctx=ctx)
    out = capsys.readouterr().out
    assert "A18.1" in out
    assert "N33.0" in out
    assert out.count("BLOC 1 : IDENTITÉ") == 2


def test_inspect_code_unknown_token(ctx: ExplorationContext, capsys) -> None:  # type: ignore[no-untyped-def]
    """Un token qui ne matche rien ne plante pas."""
    inspect_code("ZZZ99", ctx=ctx)
    out = capsys.readouterr().out
    # Le code littéral est affiché ; les blocs signalent l'absence.
    assert "ZZZ99" in out
