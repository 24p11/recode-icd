"""Tests du registre des formulations écartées (registre archaïque).

Trois garanties :

1. le chargement valide chaque entrée — une source OFS ou ANS est
   refusée bruyamment (« OFS/ANS jamais filtrés ») ;
2. le point d'application filtre la forme source exacte, formulation
   entière, et couvre la **future famille LLM** (source factice, comme
   le flag `generation_llm` l'a été) ;
3. un fichier absent rend un registre inerte.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd import cards
from recode_icd.lexicons import Lexiques
from recode_icd.policy import PolicyError, load_policy
from recode_icd.registre_formulations import (
    REGISTRE_VIDE,
    load_registre,
)

pytestmark = pytest.mark.unit

#: Politique minimale avec une source LLM factice : aucune source LLM
#: n'existe dans le CSV, mais le point d'application doit déjà la
#: couvrir (même patron que le test du flag `generation_llm`).
_POLICY_LLM = """\
familles: [OFS, ANS, INDEX, APHP, ORPHANET, CEPIDC, LLM]
familles_sources:
  "CIM-10": OFS
  "ANS": ANS
  "CIM-10 index": INDEX
  "CepiDc 2015": CEPIDC
  "Synonymes LLM (factice)": LLM
familles_formulations: [INDEX, APHP, CEPIDC, LLM]
familles_externes: [APHP, ORPHANET, CEPIDC, LLM]
familles_llm: [LLM]
defaut: {sources_externes: true, generation_llm: true}
normalisation_index: {active: false}
"""


def _politique(tmp_path: Path, registre_yaml: str | None) -> cards.PolitiqueFiches:
    policy_path = tmp_path / "chapter_policy.yaml"
    policy_path.write_text(_POLICY_LLM, encoding="utf-8")
    policy = load_policy(policy_path)
    registre = REGISTRE_VIDE
    if registre_yaml is not None:
        registre_path = tmp_path / "registre_formulations.yaml"
        registre_path.write_text(registre_yaml, encoding="utf-8")
        registre = load_registre(policy, registre_path)
    return cards.PolitiqueFiches(
        policy=policy,
        lexiques=Lexiques(rections={}, casse=frozenset(), juxtaposition={}),
        hierarchie={},
        registre=registre,
    )


def test_chargement_indexe_le_triplet_code_source_texte(tmp_path: Path) -> None:
    outils = _politique(
        tmp_path,
        "ecartees:\n"
        "  - {code: I64, source: CIM-10 index, texte: 'Apoplexie (de), congestive',\n"
        "     motif: registre archaïque}\n",
    )
    assert outils.registre.est_ecartee("I64", "CIM-10 index", "Apoplexie (de), congestive")
    # La formulation entière, sur SON code : ni un autre code, ni une
    # autre source, ni la forme rendue ne matchent.
    assert not outils.registre.est_ecartee("I61", "CIM-10 index", "Apoplexie (de), congestive")
    assert not outils.registre.est_ecartee("I64", "CepiDc 2015", "Apoplexie (de), congestive")
    assert not outils.registre.est_ecartee("I64", "CIM-10 index", "apoplexie congestive")


def test_source_ofs_ou_ans_refusee_au_chargement(tmp_path: Path) -> None:
    """« OFS et ANS ne sont JAMAIS filtrés » — refus bruyant, pas silencieux."""
    policy_path = tmp_path / "chapter_policy.yaml"
    policy_path.write_text(_POLICY_LLM, encoding="utf-8")
    policy = load_policy(policy_path)
    for source in ("CIM-10", "ANS"):
        registre_path = tmp_path / "registre.yaml"
        registre_path.write_text(
            f"ecartees:\n  - {{code: I64, source: {source}, texte: peu importe, motif: m}}\n",
            encoding="utf-8",
        )
        with pytest.raises(PolicyError, match="jamais"):
            load_registre(policy, registre_path)


def test_fichier_absent_registre_inerte(tmp_path: Path) -> None:
    policy_path = tmp_path / "chapter_policy.yaml"
    policy_path.write_text(_POLICY_LLM, encoding="utf-8")
    registre = load_registre(load_policy(policy_path), tmp_path / "inexistant.yaml")
    assert registre is REGISTRE_VIDE


def test_le_filtre_couvre_la_future_famille_llm(tmp_path: Path) -> None:
    """Le point d'application est prêt pour LLM avant toute source réelle."""
    outils = _politique(
        tmp_path,
        "ecartees:\n"
        "  - {code: I64, source: Synonymes LLM (factice), texte: apoplexie foudroyante,\n"
        "     motif: registre archaïque}\n",
    )
    sub = pl.DataFrame(
        {
            "code": ["I64", "I64", "I64"],
            "source": ["Synonymes LLM (factice)", "Synonymes LLM (factice)", "CepiDc 2015"],
            "texte": ["apoplexie foudroyante", "AVC massif", "ramollissement cérébral"],
        }
    )
    candidates = cards._candidates_formulations(sub, None, [], outils)
    textes = [c.texte for c in candidates]
    assert "apoplexie foudroyante" not in textes, "l'écartée LLM doit disparaître"
    assert "AVC massif" in textes, "l'autre formulation LLM reste"
    assert "ramollissement cérébral" in textes, "une formulation non déclarée reste"


def test_registre_vide_ne_filtre_rien(tmp_path: Path) -> None:
    outils = _politique(tmp_path, None)
    sub = pl.DataFrame(
        {"code": ["I64"], "source": ["CepiDc 2015"], "texte": ["ramollissement cérébral"]}
    )
    candidates = cards._candidates_formulations(sub, None, [], outils)
    assert [c.texte for c in candidates] == ["ramollissement cérébral"]
