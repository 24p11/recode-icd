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
    inspect_code_extended,
    load_exploration_context,
)

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def ctx() -> ExplorationContext:
    c = load_exploration_context()
    if c.flat is None or c.merged is None:
        pytest.skip("Artefacts pipeline absents — lancer build flat-csv d'abord.")
    return c


@pytest.fixture(scope="module")
def ctx_rdf() -> ExplorationContext:
    """Contexte avec graphe RDF chargé pour inspect_code_extended.

    Skip si le RDF ANS n'est pas disponible (build pipeline-only).
    """
    c = load_exploration_context(load_rdf=True)
    if c.flat is None or c.merged is None:
        pytest.skip("Artefacts pipeline absents — lancer build flat-csv d'abord.")
    if c.ans_graph is None:
        pytest.skip("RDF ANS absent — chemin par défaut introuvable.")
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


def test_inspect_code_verbose_smoke(ctx: ExplorationContext, capsys) -> None:  # type: ignore[no-untyped-def]
    """`verbose=True` ajoute BLOC 2bis et BLOC 5 sans planter."""
    inspect_code("A18.1", ctx=ctx, verbose=True)
    out = capsys.readouterr().out
    assert "BLOC 2bis" in out
    assert "BLOC 5" in out
    # Le tableau du BLOC 5 doit lister toutes les étapes attendues.
    for step in (
        "ofs_codes.parquet",
        "owl_codes.parquet",
        "merged_codes.parquet",
        "propagated_notes.parquet",
        "flat_csv",
    ):
        assert step in out


def test_inspect_code_verbose_false_equivalent_to_omitted(
    ctx: ExplorationContext, capsys,
) -> None:  # type: ignore[no-untyped-def]
    """`verbose=False` doit produire la même sortie que sans le param."""
    inspect_code("A18.1", ctx=ctx)
    out_default = capsys.readouterr().out
    inspect_code("A18.1", ctx=ctx, verbose=False)
    out_explicit = capsys.readouterr().out
    assert out_default == out_explicit
    # Sans verbose, aucun bloc debug.
    assert "BLOC 2bis" not in out_default
    assert "BLOC 5" not in out_default


def test_inspect_code_verbose_no_dagger_pair(
    ctx: ExplorationContext, capsys,
) -> None:  # type: ignore[no-untyped-def]
    """Pour un code sans paire dague/astérisque, le commentaire du
    BLOC 5 mentionne que Δ2 vient des synonymes/externes seuls."""
    # Z00.0 (examen médical général) n'a pas d'association.
    inspect_code("Z00.0", ctx=ctx, verbose=True)
    out = capsys.readouterr().out
    assert "BLOC 5" in out
    # Soit Δ2 = 0 (rare), soit le message "synonymes et sources externes seuls".
    assert ("Δ2 = 0" in out) or ("synonymes et sources externes seuls" in out)


def test_inspect_code_verbose_propagated_delta(
    ctx: ExplorationContext, capsys,
) -> None:  # type: ignore[no-untyped-def]
    """E80.7 illustre les 4 niveaux de propagation → Δ1 > 0."""
    inspect_code("E80.7", ctx=ctx, verbose=True)
    out = capsys.readouterr().out
    assert "héritage hiérarchique détecté" in out


# ----------------------------------------------------------------------
# inspect_code_extended (variante avec lecture RDF directe)
# ----------------------------------------------------------------------


def test_inspect_code_extended_leaf_smoke(
    ctx_rdf: ExplorationContext, capsys,
) -> None:  # type: ignore[no-untyped-def]
    """Smoke : M01.08 (feuille) doit produire les 5 BLOCs et exposer les
    propriétés RDF spécifiques (hasCausality vers A39.8, 6 altLabel)."""
    inspect_code_extended("M01.08", ctx_rdf)
    out = capsys.readouterr().out
    assert "M01.08" in out
    assert "BLOC 1" in out and "BLOC 2" in out and "BLOC 3" in out and "BLOC 4" in out
    assert "Type de nœud : leaf" in out
    assert "ANS — RDF source" in out
    assert "hasCausality" in out
    assert "A39.8" in out


def test_inspect_code_extended_chapter_roman(
    ctx_rdf: ExplorationContext, capsys,
) -> None:  # type: ignore[no-untyped-def]
    """XIII (chiffre romain) doit être mappé vers l'URI RDF 13, et
    l'affichage doit reprendre la notation romaine."""
    inspect_code_extended("XIII", ctx_rdf)
    out = capsys.readouterr().out
    assert "XIII" in out
    assert "Type de nœud : chapter" in out
    assert "/13" in out  # URI RDF
    # BLOC 4 doit indiquer l'absence du CSV pour un nœud non-feuille.
    assert "absent du CSV final" in out


def test_inspect_code_extended_absent_does_not_crash(
    ctx_rdf: ExplorationContext, capsys,
) -> None:  # type: ignore[no-untyped-def]
    """ZZZ99 (inexistant) ne doit pas lever, et signaler l'absence."""
    inspect_code_extended("ZZZ99", ctx_rdf)
    out = capsys.readouterr().out
    assert "Type de nœud : absent" in out
    assert "absent du RDF" in out


def test_inspect_code_extended_no_rdf_raises(
    ctx: ExplorationContext,
) -> None:
    """Sans ans_graph (load_rdf=False par défaut), la fonction doit
    lever une erreur claire."""
    with pytest.raises(RuntimeError, match="ans_graph"):
        inspect_code_extended("M01.08", ctx)
