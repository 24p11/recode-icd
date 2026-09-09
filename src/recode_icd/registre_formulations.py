"""Registre des formulations écartées pour registre archaïque.

Charge `referentials/curation/registre_formulations.yaml` : la liste
des formulations de la section « Formulations cliniques alternatives »
écartées pour registre archaïque (vocabulaire de certificat de décès,
terminologie désuète), validée ligne à ligne par relecture clinicienne.

C'est un **filtre de rendu**, au même titre que R1/R3 de la
`chapter_policy` : appliqué à l'assemblage des fiches, jamais au CSV
maître ni aux Parquets. Une entrée identifie une formulation par le
triplet **(code, source, texte)** — la forme source exacte, pas la
forme rendue : le filtre s'applique avant R3.

⚠ **Sonde ≠ verdict — granularité formulation, validation clinicienne.**
La liste a été produite par sondes lexicales puis tranchée ligne à
ligne par RF : la même sonde porte des écartées et des gardées. Ne
jamais transformer ce registre en règle par terme.

⚠ **OFS et ANS ne sont JAMAIS filtrés.** Seules les familles de la
section Formulations (`familles_formulations` de la chapter_policy :
INDEX, APHP, CEPIDC, LLM) sont admissibles ; toute autre famille est
refusée bruyamment au chargement.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from recode_icd.policy import ChapterPolicy, PolicyError

#: Emplacement par défaut, versionné avec le référentiel (ancré sur le
#: paquet, pas sur le répertoire courant — cf. policy.py).
_RACINE_DEPOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRE_PATH = _RACINE_DEPOT / "referentials/curation/registre_formulations.yaml"


@dataclass(frozen=True)
class RegistreFormulations:
    """Les formulations écartées, indexées par (code, source, texte)."""

    ecartees: frozenset[tuple[str, str, str]]

    def est_ecartee(self, code: str, source: str, texte: str) -> bool:
        return (code, source, texte) in self.ecartees


#: Registre inerte — aucun filtrage (fichier absent, ou tests).
REGISTRE_VIDE = RegistreFormulations(ecartees=frozenset())


def load_registre(policy: ChapterPolicy, path: Path | None = None) -> RegistreFormulations:
    """Charge le registre et vérifie que chaque entrée est admissible.

    Un fichier absent rend le registre vide (filtre inerte) : le
    registre est né après les bibliothèques, les contextes de test
    minimaux n'en ont pas. Une entrée dont la source n'appartient pas
    aux familles de la section Formulations lève `PolicyError` — c'est
    la garantie « OFS/ANS jamais filtrés ».
    """
    chemin = path if path is not None else DEFAULT_REGISTRE_PATH
    if not chemin.exists():
        return REGISTRE_VIDE
    brut: dict[str, Any] = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}

    ecartees: set[tuple[str, str, str]] = set()
    for entree in brut.get("ecartees") or []:
        code = str(entree["code"])
        source = str(entree["source"])
        texte = str(entree["texte"])
        famille = policy.famille_de(source)
        if famille not in policy.familles_formulations:
            raise PolicyError(
                f"registre_formulations : la source « {source} » (famille {famille}) "
                f"n'alimente pas la section Formulations — seules "
                f"{sorted(policy.familles_formulations)} peuvent être filtrées, "
                f"OFS et ANS jamais (entrée {code} / {texte!r})."
            )
        ecartees.add((code, source, texte))
    return RegistreFormulations(ecartees=frozenset(ecartees))


__all__ = (
    "DEFAULT_REGISTRE_PATH",
    "REGISTRE_VIDE",
    "RegistreFormulations",
    "load_registre",
)
