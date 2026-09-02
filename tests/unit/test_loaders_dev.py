"""Test minimal du helper d'exploration.

Vérifie que `load_exploration_context()` charge sans erreur les sources
principales présentes dans le repo. Marker `unit` mais I/O réelle (les
fichiers sont petits sauf LIBELLE ~11 MB / quelques centaines de ms).
"""

from __future__ import annotations

import polars as pl
import pytest

from recode_icd.utils.loaders_dev import (
    ExplorationContext,
    load_exploration_context,
)

pytestmark = pytest.mark.unit


def test_context_loads_main_sources() -> None:
    ctx = load_exploration_context()
    assert isinstance(ctx, ExplorationContext)

    # Tables OFS principales doivent être présentes.
    required_ofs = {"master", "libelle", "include", "exclude", "dagstar", "memo"}
    missing = required_ofs - set(ctx.ofs.keys())
    assert not missing, f"Tables OFS manquantes : {missing}"

    # ANS Parquet doit être chargé.
    assert ctx.ans is not None, "ctx.ans est None — owl_codes.parquet manquant ?"
    assert isinstance(ctx.ans, pl.DataFrame)

    # Artefacts pipeline présents.
    assert ctx.merged is not None
    assert ctx.propagated is not None
    assert ctx.flat is not None

    # Tables du guide MCO présentes (versées au chantier A).
    assert ctx.recommendations is not None
    assert ctx.recommendation_codes is not None
    assert isinstance(ctx.recommendation_codes, pl.DataFrame)
    assert "specificite" in ctx.recommendation_codes.columns

    # Au moins un rapport présent (note_merges produit après chaque build merged).
    assert "note_merges" in ctx.reports


def test_context_lazy_returns_lazyframes() -> None:
    ctx = load_exploration_context(lazy=True)
    assert isinstance(ctx.ofs["master"], pl.LazyFrame)
    assert isinstance(ctx.ans, pl.LazyFrame)
    assert isinstance(ctx.merged, pl.LazyFrame)


def test_context_graceful_on_missing_paths(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Quand tous les chemins overrides pointent vers du vide, on a un ctx vide sans exception."""
    ctx = load_exploration_context(
        root=tmp_path,
        ofs_dir=tmp_path / "nope_ofs",
        processed_dir=tmp_path / "nope_processed",
        reports_dir=tmp_path / "nope_reports",
    )
    assert ctx.ofs == {}
    assert ctx.ans is None
    assert ctx.merged is None
    assert ctx.propagated is None
    assert ctx.flat is None
    assert ctx.reports == {}
