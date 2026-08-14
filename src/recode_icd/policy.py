"""Politique de composition de la section « Formulations » des fiches.

Charge et résout `referentials/curation/chapter_policy.yaml`. Trois
règles y sont déclarées :

- **R1** — filtrage par plage de codes × famille de sources ;
- **R2** — plafonds par famille (feuilles et catégories) ;
- **R3** — paramètres de normalisation des entrées de l'Index vol3.

Ces règles gouvernent l'**assemblage des fiches** uniquement. Le CSV
maître, les Parquets et la colonne `texte` ne sont jamais modifiés.

⚠ **Résolution par remplacement, pas par fusion.** `politique_pour`
retourne la règle la plus spécifique qui matche (bloc > chapitre >
défaut) *telle quelle* : elle n'hérite pas des champs absents de la
règle moins spécifique. Une entrée de bloc doit redéclarer ce qu'elle
veut conserver du chapitre. C'est le seul choix qui permette de
ré-admettre une source au niveau d'un bloc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

#: Emplacement par défaut de la politique, versionnée avec le référentiel.
# Chemins par défaut ancrés sur l'emplacement du paquet, PAS sur le
# répertoire courant : un chemin relatif au cwd casse dès qu'un appelant
# ne part pas de la racine du dépôt (nbconvert exécute un notebook depuis
# son propre répertoire, par exemple).
_RACINE_DEPOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = _RACINE_DEPOT / "referentials/curation/chapter_policy.yaml"
DEFAULT_LEXICONS_DIR = _RACINE_DEPOT / "referentials/processed"

#: Famille attribuée à un libellé de source inconnu du YAML. Le test de
#: couverture bidirectionnel interdit qu'elle apparaisse en pratique.
FAMILLE_INCONNUE = "AUTRE"


class PolicyError(ValueError):
    """Incohérence détectée dans le YAML de politique."""


@dataclass(frozen=True)
class Regle:
    """Règle applicable à une plage de codes (chapitre ou bloc).

    `sources_externes` : les familles de `familles_externes` sont-elles
    admises dans la section Formulations ?
    `generation_llm` : les familles de `familles_llm` le sont-elles ?
    Les deux flags sont indépendants — le chapitre XVIII conserve les
    sources réelles tout en interdisant la génération LLM.
    """

    sources_externes: bool = True
    generation_llm: bool = True


@dataclass(frozen=True)
class NormalisationIndex:
    """Paramètres de R3 (cf. `normalize_index`)."""

    active: bool = True
    seuil_dominance: float = 2.0
    inconnu_est_adjectif: bool = True
    tetes_nues: frozenset[str] = field(default_factory=frozenset)
    abreviations_index: frozenset[str] = field(default_factory=frozenset)
    meta_termes: frozenset[str] = field(default_factory=frozenset)
    enumeration_prefixe_min: int = 5
    enumeration_ratio_min: float = 0.5


@dataclass(frozen=True)
class ChapterPolicy:
    """Politique complète, résolue depuis le YAML."""

    familles: frozenset[str]
    familles_sources: dict[str, str]
    prefixes_familles: dict[str, str]
    familles_formulations: frozenset[str]
    familles_externes: frozenset[str]
    familles_llm: frozenset[str]
    plafond_famille_feuilles: int
    plafond_famille_categories: int
    plafond_global_categories: int
    defaut: Regle
    chapitres: dict[str, Regle]
    blocs: dict[str, Regle]
    normalisation_index: NormalisationIndex

    # -- R1 ------------------------------------------------------------
    def famille_de(self, libelle: str) -> str:
        """Famille d'un libellé de source CSV.

        Les préfixes sont testés après les libellés exacts : une source
        AP-HP est reconnue par son préfixe, les autres par leur libellé.
        """
        exacte = self.familles_sources.get(libelle)
        if exacte is not None:
            return exacte
        for prefixe, famille in self.prefixes_familles.items():
            if libelle.startswith(prefixe):
                return famille
        return FAMILLE_INCONNUE

    def regle_pour(self, chapitre: str | None, blocs: list[str] | None) -> Regle:
        """Résout la règle applicable — bloc > chapitre > défaut.

        `blocs` est la liste des blocs englobants, du plus large au plus
        étroit (la CIM-10 en imbrique jusqu'à trois : C50.8 vit sous
        « C00-C97 / C00-C75 / C50-C50 »). On les teste du plus **interne**
        au plus large : la règle la plus spécifique gagne.

        **Remplacement, pas fusion** : la règle retournée est celle du
        niveau qui matche, sans complétion par les niveaux supérieurs.
        """
        for bloc in reversed(blocs or []):
            regle = self.blocs.get(bloc)
            if regle is not None:
                return regle
        if chapitre is not None:
            regle = self.chapitres.get(chapitre)
            if regle is not None:
                return regle
        return self.defaut

    def familles_admises(self, chapitre: str | None, blocs: list[str] | None) -> frozenset[str]:
        """Familles autorisées dans la section Formulations pour cette plage."""
        regle = self.regle_pour(chapitre, blocs)
        admises = set(self.familles_formulations)
        if not regle.sources_externes:
            admises -= self.familles_externes
        if not regle.generation_llm:
            admises -= self.familles_llm
        return frozenset(admises)


def _regle(bloc: dict[str, Any] | None, defaut: Regle | None = None) -> Regle:
    if bloc is None:
        return defaut if defaut is not None else Regle()
    return Regle(
        sources_externes=bool(bloc.get("sources_externes", True)),
        generation_llm=bool(bloc.get("generation_llm", True)),
    )


def load_policy(path: Path | None = None) -> ChapterPolicy:
    """Charge la politique depuis le YAML et vérifie sa cohérence interne.

    Lève `PolicyError` si une famille citée n'est pas déclarée dans
    `familles` — la cohérence avec `_SOURCE_CSV_MAP` est vérifiée côté
    tests, ce module n'important rien de l'exporter.
    """
    chemin = path if path is not None else DEFAULT_POLICY_PATH
    brut: dict[str, Any] = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}

    familles = frozenset(brut.get("familles", []))
    familles_sources: dict[str, str] = dict(brut.get("familles_sources", {}))
    prefixes: dict[str, str] = dict(brut.get("prefixes_familles", {}))

    citees = (
        set(familles_sources.values())
        | set(prefixes.values())
        | set(brut.get("familles_formulations", []))
        | set(brut.get("familles_externes", []))
        | set(brut.get("familles_llm", []))
    )
    inconnues = citees - familles
    if inconnues:
        raise PolicyError(
            f"Familles citées mais absentes de `familles` : {sorted(inconnues)}. "
            f"Ajouter chaque famille à la liste `familles`, qui fait autorité."
        )

    ni = dict(brut.get("normalisation_index", {}))
    enum = dict(ni.get("enumeration", {}))

    return ChapterPolicy(
        familles=familles,
        familles_sources=familles_sources,
        prefixes_familles=prefixes,
        familles_formulations=frozenset(brut.get("familles_formulations", [])),
        familles_externes=frozenset(brut.get("familles_externes", [])),
        familles_llm=frozenset(brut.get("familles_llm", [])),
        plafond_famille_feuilles=int(brut.get("plafond_famille_feuilles", 10)),
        plafond_famille_categories=int(brut.get("plafond_famille_categories", 20)),
        plafond_global_categories=int(brut.get("plafond_global_categories", 50)),
        defaut=_regle(brut.get("defaut")),
        chapitres={k: _regle(v) for k, v in (brut.get("chapitres") or {}).items()},
        blocs={k: _regle(v) for k, v in (brut.get("blocs") or {}).items()},
        normalisation_index=NormalisationIndex(
            active=bool(ni.get("active", True)),
            seuil_dominance=float(ni.get("seuil_dominance", 2.0)),
            inconnu_est_adjectif=bool(ni.get("inconnu_est_adjectif", True)),
            tetes_nues=frozenset(ni.get("tetes_nues", [])),
            abreviations_index=frozenset(ni.get("abreviations_index", [])),
            meta_termes=frozenset(ni.get("meta_termes", [])),
            enumeration_prefixe_min=int(enum.get("prefixe_min", 5)),
            enumeration_ratio_min=float(enum.get("ratio_min", 0.5)),
        ),
    )


__all__ = (
    "DEFAULT_LEXICONS_DIR",
    "DEFAULT_POLICY_PATH",
    "FAMILLE_INCONNUE",
    "ChapterPolicy",
    "NormalisationIndex",
    "PolicyError",
    "Regle",
    "load_policy",
)
