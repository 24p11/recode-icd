"""Résolution officielle d'un code pour les consommateurs (chantier couverture ATIH, D0).

`resoudre_code(code)` accepte **toute écriture** — compacte ATIH
(`O0490`), pointée (`O04.90`), maître (`O04.-0.9`), familles
divergentes — et répond soit **la fiche**, soit **la raison motivée de
son absence**. Objectif : aucun traitement aval ne peut plus échouer en
silence sur une jointure naïve ; les réponses négatives, journalisées
par les consommateurs, deviennent la mesure d'usage qui priorise la
suite.

Statuts de résolution (`Resolution.statut`) :

| Statut | Sens | Ce que porte la réponse |
|---|---|---|
| `fiche` | une fiche existe dans la bibliothèque visée | son chemin, le statut MCO du code |
| `intermediaire` | code codable MCO, subdivisé au maître, sans fiche propre (D2 en cours) | ses feuilles avec fiche |
| `sans_ligne` | feuille codable du maître à laquelle aucune source n'attache de ligne (D3) | libellé |
| `pere_interdit` | type 3 non supprimé : ne se code pas, ses enfants oui | ses enfants avec fiche |
| `supprime` | code supprimé du kit ATIH (`*** SUaa ***`) | millésime de suppression |
| `tronc_chapitre_xx` | extension lieu/activité du chapitre XX (D5 étendra à la validation de la composition) | le tronc et sa fiche |
| `absent_du_maitre` | connu du kit, absent du nested set (extensions ATIH récentes, D3) | l'ancêtre le plus proche |
| `inconnu_atih` | au maître mais inconnu du kit : pas codable en MCO | la fiche si elle existe |
| `inconnu` | ni au kit ni au maître | — |
| `notation_invalide` | l'écriture ne relève d'aucune forme connue | le message du parseur |

Un code présent dans la bibliothèque mais non codable (père interdit,
supprimé, inconnu du kit — tant que D4 ne les a pas exclus du profil
génération) est rendu `fiche` avec `codable_mco=False` : la réponse
dit la fiche **et** avertit. Le consommateur qui tire un code pour
générer filtre sur `codable_mco`.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from recode_icd.loaders.atih import LIBELLES_STATUT, STATUT_INCONNU
from recode_icd.notations import Notations, charge_notations
from recode_icd.policy import _RACINE_DEPOT
from recode_icd.recommendations.code_expr import CodeExprError

DEFAULT_PROCESSED_DIR = _RACINE_DEPOT / "referentials/processed"
DEFAULT_INDEX_PATH = _RACINE_DEPOT / "outputs/cards_library/_index.csv"

STATUTS_RESOLUTION = (
    "fiche",
    "intermediaire",
    "sans_ligne",
    "pere_interdit",
    "supprime",
    "tronc_chapitre_xx",
    "absent_du_maitre",
    "inconnu_atih",
    "inconnu",
    "notation_invalide",
)

_RE_CHAPITRE_XX = re.compile(r"^[VWXY]\d{2}")


@dataclass(frozen=True)
class Resolution:
    """La réponse — toujours motivée."""

    saisie: str
    statut: str
    code: str | None = None
    code_atih: str | None = None
    libelle: str | None = None
    statut_mco: str | None = None
    codable_mco: bool | None = None
    fiche: str | None = None
    raison: str = ""
    #: Feuilles (ou enfants) qui, elles, ont une fiche — la réponse de
    #: repli pour un intermédiaire ou un père interdit.
    codes_avec_fiche: tuple[str, ...] = field(default_factory=tuple)
    #: Ancêtre le plus proche au maître (absent du maître, tronc XX).
    ancetre: str | None = None

    @property
    def negative(self) -> bool:
        return self.statut != "fiche"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


@dataclass(frozen=True)
class ContexteResolution:
    """Les trois tables que la résolution lit — chargées une fois."""

    notations: Notations
    atih: pl.DataFrame
    merged: pl.DataFrame
    #: `code → chemin de la fiche` de la bibliothèque visée (son `_index.csv`).
    fiches: dict[str, str]
    bibliotheque: str = ""


def charge_contexte(
    processed_dir: Path | None = None,
    index_path: Path | None = None,
    notations_path: Path | None = None,
) -> ContexteResolution:
    """Charge `atih_codes.parquet`, `merged_codes.parquet` et l'index de la bibliothèque.

    Sans index (bibliothèque non générée), les fiches sont réputées être
    les codes du CSV maître : c'est la liste que `cards build` produit.
    """
    processed = processed_dir if processed_dir is not None else DEFAULT_PROCESSED_DIR
    index = index_path if index_path is not None else DEFAULT_INDEX_PATH
    atih = pl.read_parquet(processed / "atih_codes.parquet")
    merged = pl.read_parquet(processed / "merged_codes.parquet")
    if index.is_file():
        idx = pl.read_csv(index, columns=["code", "filepath"])
        fiches = dict(zip(idx["code"].to_list(), idx["filepath"].to_list(), strict=True))
        bibliotheque = str(index.parent)
    else:
        csv = pl.read_csv(processed / "inclusions_exclusions_synonymes.csv", columns=["code"])
        fiches = {c: "" for c in csv["code"].unique().to_list()}
        bibliotheque = "(CSV maître : bibliothèque non générée)"
    return ContexteResolution(
        notations=charge_notations(notations_path),
        atih=atih,
        merged=merged,
        fiches=fiches,
        bibliotheque=bibliotheque,
    )


def _ligne(df: pl.DataFrame, code: str) -> dict[str, object] | None:
    sub = df.filter(pl.col("code") == code)
    return None if sub.is_empty() else sub.row(0, named=True)


def _entier(valeur: object) -> int:
    """Une borne du nested set, typée (polars rend `object` par ligne)."""
    assert isinstance(valeur, int), valeur
    return valeur


def _feuilles_sous(merged: pl.DataFrame, noeud: dict[str, object]) -> list[str]:
    return (
        merged.filter(
            (pl.col("left") > _entier(noeud["left"]))
            & (pl.col("right") < _entier(noeud["right"]))
            & (pl.col("right") == pl.col("left") + 1)
        )["code"]
        .sort()
        .to_list()
    )


def _ancetre_au_maitre(ctx: ContexteResolution, code_atih: str) -> str | None:
    """Le plus long préfixe compact du code qui existe au maître."""
    for n in range(len(code_atih) - 1, 2, -1):
        prefixe = code_atih[:n].rstrip("+")
        maitre = ctx.notations.ecriture_maitre(prefixe)
        if _ligne(ctx.merged, maitre) is not None:
            return maitre
    return None


def resoudre_code(saisie: str, ctx: ContexteResolution) -> Resolution:
    """Toute écriture → la fiche, ou la raison motivée de l'absence."""
    try:
        code = ctx.notations.resout_ecriture(saisie)
    except CodeExprError as err:
        return Resolution(saisie=saisie, statut="notation_invalide", raison=str(err))

    code_atih = ctx.notations.cle_compacte(code)
    kit = _ligne(ctx.atih, code)
    noeud = _ligne(ctx.merged, code)
    libelle = (
        str(noeud["label"]) if noeud is not None else (str(kit["libelle_long"]) if kit else None)
    )
    statut_mco = (
        str(kit["statut_mco"])
        if kit is not None
        else (STATUT_INCONNU if noeud is not None else None)
    )
    codable = (
        bool(kit["codable_mco"]) if kit is not None else (False if noeud is not None else None)
    )
    base = {
        "saisie": saisie,
        "code": code,
        "code_atih": code_atih,
        "libelle": libelle,
        "statut_mco": statut_mco,
        "codable_mco": codable,
    }

    fiche = ctx.fiches.get(code)
    if fiche is not None:
        raison = "Fiche disponible."
        if statut_mco is not None and not codable:
            raison = (
                f"Fiche disponible, mais le code n'est pas codable en MCO : "
                f"{LIBELLES_STATUT.get(statut_mco, statut_mco)}."
            )
        return Resolution(statut="fiche", fiche=fiche, raison=raison, **base)  # type: ignore[arg-type]

    if kit is None and noeud is None:
        return Resolution(
            statut="inconnu",
            raison="Code inconnu du kit ATIH et du référentiel : aucune forme ne lui correspond.",
            **base,  # type: ignore[arg-type]
        )

    if kit is not None and bool(kit["supprime"]):
        su = kit["supprime_millesime"]
        return Resolution(
            statut="supprime",
            raison=f"Code supprimé du kit ATIH (SU{su}) : il ne se code plus en MCO.",
            **base,  # type: ignore[arg-type]
        )

    if noeud is None:
        # Connu du kit, absent du nested set.
        ancetre = _ancetre_au_maitre(ctx, str(code_atih))
        if _RE_CHAPITRE_XX.match(code) and kit is not None and _entier(kit["type_mco"]) == 2:
            return Resolution(
                statut="tronc_chapitre_xx",
                ancetre=ancetre,
                codes_avec_fiche=tuple(c for c in (ancetre,) if c in ctx.fiches),
                raison=(
                    "Extension lieu/activité du chapitre XX : la fiche est celle du tronc "
                    f"{ancetre or '(introuvable)'} ; la composition (lieu, activité) se valide "
                    "contre le kit — D5 l'outillera."
                ),
                **base,  # type: ignore[arg-type]
            )
        return Resolution(
            statut="absent_du_maitre",
            ancetre=ancetre,
            codes_avec_fiche=tuple(c for c in (ancetre,) if c in ctx.fiches),
            raison=(
                "Code du kit ATIH absent du référentiel ANS (extension récente) : "
                f"ancêtre le plus proche au maître {ancetre or '(aucun)'} — D3 l'injectera."
            ),
            **base,  # type: ignore[arg-type]
        )

    est_feuille = _entier(noeud["right"]) == _entier(noeud["left"]) + 1
    feuilles = [] if est_feuille else _feuilles_sous(ctx.merged, noeud)
    avec_fiche = tuple(f for f in feuilles if f in ctx.fiches)

    if kit is None:
        return Resolution(
            statut="inconnu_atih",
            codes_avec_fiche=avec_fiche,
            raison="Code du référentiel inconnu du kit ATIH : il n'est pas codable en MCO.",
            **base,  # type: ignore[arg-type]
        )
    if not codable:
        return Resolution(
            statut="pere_interdit",
            codes_avec_fiche=avec_fiche,
            raison=(
                f"Non codable en MCO (catégorie non vide ou code père interdit) : le code ne "
                f"se code pas tel quel ; {len(avec_fiche)} subdivision(s) ont une fiche."
            ),
            **base,  # type: ignore[arg-type]
        )
    if est_feuille:
        return Resolution(
            statut="sans_ligne",
            raison=(
                "Code codable en MCO, présent au référentiel, mais aucune source ne lui "
                "attache de ligne : pas de fiche tant que D3 n'est pas fait (libellé seul)."
            ),
            **base,  # type: ignore[arg-type]
        )
    return Resolution(
        statut="intermediaire",
        codes_avec_fiche=avec_fiche,
        raison=(
            f"Code codable en MCO, subdivisé au référentiel : {len(feuilles)} feuille(s), "
            f"dont {len(avec_fiche)} avec fiche — pas de fiche propre tant que D2 n'est pas fait."
        ),
        **base,  # type: ignore[arg-type]
    )


def journalise(resolution: Resolution, journal: Path) -> None:
    """Ajoute une réponse NÉGATIVE au journal JSONL (mesure d'usage)."""
    if not resolution.negative:
        return
    journal.parent.mkdir(parents=True, exist_ok=True)
    ligne = {"horodatage": datetime.now(UTC).isoformat(), **asdict(resolution)}
    with journal.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ligne, ensure_ascii=False) + "\n")


__all__ = (
    "DEFAULT_INDEX_PATH",
    "DEFAULT_PROCESSED_DIR",
    "STATUTS_RESOLUTION",
    "ContexteResolution",
    "Resolution",
    "charge_contexte",
    "journalise",
    "resoudre_code",
)
