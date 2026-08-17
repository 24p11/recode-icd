"""Intégrité des transcriptions curées du guide méthodologique.

Le pattern
----------
Les extraits du guide suivent la chaîne maison **brut → curé → validé →
figé** :

- `data/guide_mco/extraits_bruts/` : sortie `pdftotext -layout` intacte,
  commande et version de poppler en tête. **Artefact mécanique**,
  régénérable à l'identique.
- `data/guide_mco/extraits/` : **transcription curée**, relue et validée
  par un humain, puis figée. C'est elle sur laquelle s'ancre l'extraction
  des candidates du chantier B.

La curation est un **reformatage sans réécriture**. Autorisé : recoller
les lignes coupées par la mise en page, reconstruire les tableaux
disloqués par le rendu en colonnes, déplacer les notes de bas de page
vers la fin avec des marqueurs, baliser articles et sections. **Interdit :
paraphrase, condensation, réordonnancement du corps, correction du texte
du guide.** Les erreurs de l'original se signalent en marge, elles ne se
réparent pas — un guide fautif dont on a corrigé le texte ne prouve plus
rien sur ce que le guide dit.

Ce module rend la règle **vérifiable**, parce qu'une consigne de
transcription qu'aucun test ne contrôle dérive en trois articles.

Les trois contrôles, et ce que chacun attrape
---------------------------------------------
1. **Conservation** — le multiensemble de mots du curé égale celui du
   brut, moins les suppressions déclarées. Attrape toute paraphrase,
   toute condensation, tout ajout : un mot changé casse le test.
2. **Ordre du corps** — les mots du corps curé forment une
   *sous-séquence* des mots du brut. Attrape le réordonnancement. Le
   corps seul, parce que les notes de bas de page ont le droit de bouger.
3. **Ordre des notes** — même contrôle sur la section de notes. Une note
   déplacée en bloc reste dans son ordre interne.

Ce que ça n'attrape pas, et c'est assumé : une permutation de deux notes
entre elles, ou de deux mots à l'intérieur d'une même note. Le contrôle 1
garantit qu'aucun mot n'a été inventé ni perdu, ce qui borne le dégât à
un déplacement — le reste relève de la relecture humaine, qui est de
toute façon l'étape suivante.

⚠ **Les suppressions sont DÉCLARÉES, jamais devinées.** Un curé qui
laisse tomber un paragraphe doit faire échouer le test, pas être
rattrapé par une heuristique compréhensive. C'est tout l'objet du
fichier `suppressions.yaml`.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from recode_icd.policy import _RACINE_DEPOT

BRUTS_DIR = _RACINE_DEPOT / "data/guide_mco/extraits_bruts"
CURES_DIR = _RACINE_DEPOT / "data/guide_mco/extraits"
SUPPRESSIONS_PATH = CURES_DIR / "suppressions.yaml"

#: Titre de la section de notes dans un fichier curé. Tout ce qui suit
#: est traité comme notes de bas de page relocalisées.
TITRE_NOTES = "## Notes de bas de page"

#: Annotation de curation : commentaire HTML. Invisible au flux de mots,
#: donc c'est là — et seulement là — qu'on signale une erreur de
#: l'original sans la réparer.
_RE_ANNOTATION = re.compile(r"<!--.*?-->", re.DOTALL)

#: Marqueur de renvoi vers une note (« [^57] »).
_RE_MARQUEUR_NOTE = re.compile(r"\[\^[^\]]+\]")

#: Balisage markdown introduit par la curation. On retire les
#: CARACTÈRES, jamais les mots — « ## ACCIDENTS VASCULAIRES » rend bien
#: ses deux mots.
#:
#: ⚠ **L'ordre des deux passes est load-bearing.** Une ligne de filet de
#: tableau (« |---|---| ») doit être reconnue AVANT que les barres ne
#: soient retirées : sinon elle devient « --- --- », qui n'est plus une
#: ligne de filet et dont les tirets entrent dans le flux de mots.
_RE_LIGNE_FILET = re.compile(r"^[-:| ]+$", re.MULTILINE)
_RE_BALISAGE = re.compile(r"^[#>\s]*|[|]", re.MULTILINE)

#: En-tête de provenance d'un fichier brut : lignes « # … » jusqu'au
#: filet. Ce n'est pas du texte de guide.
_RE_ENTETE_BRUT = re.compile(r"\A(?:#[^\n]*\n)+", re.MULTILINE)


class TranscriptionError(ValueError):
    """Le curé ne conserve pas fidèlement le brut."""


@dataclass(frozen=True)
class Suppressions:
    """Suppressions autorisées lors de la curation d'un article.

    `lignes_regex` s'applique ligne par ligne au brut : une ligne qui
    matche entièrement est retirée avant comparaison. Sert aux artefacts
    de pagination (numéro de page isolé, en-tête courant répété).
    """

    lignes_regex: tuple[str, ...] = ()

    def applique(self, texte: str) -> str:
        if not self.lignes_regex:
            return texte
        motifs = [re.compile(m) for m in self.lignes_regex]
        gardees = [
            ligne for ligne in texte.splitlines() if not any(m.fullmatch(ligne) for m in motifs)
        ]
        return "\n".join(gardees)


@dataclass
class RapportIntegrite:
    """Verdict, et de quoi localiser la divergence."""

    article: str
    n_mots_bruts: int = 0
    n_mots_corps: int = 0
    n_mots_notes: int = 0
    manquants: list[str] = field(default_factory=list)
    ajoutes: list[str] = field(default_factory=list)
    desordre_corps: str | None = None
    desordre_notes: str | None = None

    @property
    def conforme(self) -> bool:
        return not (self.manquants or self.ajoutes or self.desordre_corps or self.desordre_notes)

    def message(self) -> str:
        if self.conforme:
            return f"{self.article} : conforme ({self.n_mots_bruts} mots)."
        parties = [f"{self.article} : transcription NON conforme."]
        if self.manquants:
            parties.append(
                f"  {len(self.manquants)} mot(s) perdu(s) — ex. {self.manquants[:8]}. "
                f"Soit du texte a été condensé, soit une suppression légitime "
                f"n'est pas déclarée dans suppressions.yaml."
            )
        if self.ajoutes:
            parties.append(
                f"  {len(self.ajoutes)} mot(s) ajouté(s) — ex. {self.ajoutes[:8]}. "
                f"La curation reformate, elle ne rédige pas : une remarque de "
                f"curation va en commentaire HTML, pas dans le texte."
            )
        if self.desordre_corps:
            parties.append(f"  Ordre du corps rompu : {self.desordre_corps}")
        if self.desordre_notes:
            parties.append(f"  Ordre des notes rompu : {self.desordre_notes}")
        return "\n".join(parties)


def charge_suppressions(path: Path | None = None) -> dict[str, Suppressions]:
    """Charge `suppressions.yaml` — `commun` fusionné dans chaque article.

    Retourne un `dict` par article ; la clé `""` porte le commun seul,
    utilisée pour un article sans entrée propre.
    """
    chemin = path if path is not None else SUPPRESSIONS_PATH
    if not chemin.is_file():
        return {"": Suppressions()}
    brut: dict[str, Any] = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    commun = tuple(brut.get("commun", {}).get("lignes_regex", []))
    sortie: dict[str, Suppressions] = {"": Suppressions(commun)}
    for article, config in (brut.get("articles") or {}).items():
        propres = tuple((config or {}).get("lignes_regex", []))
        sortie[article] = Suppressions(commun + propres)
    return sortie


def _mots(texte: str) -> list[str]:
    """Flux de mots : whitespace normalisé, texte intact.

    On ne touche **ni à la casse, ni aux accents, ni à la ponctuation** :
    la curation n'a pas le droit d'y toucher non plus, donc le contrôle
    doit les voir. Seule normalisation : NFC, parce que deux encodages
    Unicode du même caractère accentué sont le même mot pour un lecteur
    et le pdftotext peut varier.
    """
    return unicodedata.normalize("NFC", texte).split()


def mots_bruts(texte: str, suppressions: Suppressions) -> list[str]:
    """Flux de mots d'un extrait brut, en-tête de provenance retiré."""
    corps = _RE_ENTETE_BRUT.sub("", texte)
    return _mots(suppressions.applique(corps))


def partitionne_cure(texte: str) -> tuple[list[str], list[str]]:
    """`(mots du corps, mots des notes)` d'un extrait curé.

    Retire les annotations de curation (commentaires HTML), les marqueurs
    de renvoi et le balisage markdown — sans jamais retirer de mot.
    """
    sans_annotation = _RE_ANNOTATION.sub(" ", texte)
    corps, _, notes = sans_annotation.partition(TITRE_NOTES)
    return _nettoie(corps), _nettoie(notes)


def _nettoie(fragment: str) -> list[str]:
    sans_marqueur = _RE_MARQUEUR_NOTE.sub(" ", fragment)
    sans_filet = _RE_LIGNE_FILET.sub(" ", sans_marqueur)
    return _mots(_RE_BALISAGE.sub(" ", sans_filet))


def _premier_desordre(sous_suite: list[str], reference: list[str]) -> str | None:
    """`None` si `sous_suite` est une sous-séquence de `reference`.

    Sinon, décrit le premier mot qui ne trouve plus sa place — c'est le
    point où l'ordre a été rompu.
    """
    it = iter(reference)
    for position, mot in enumerate(sous_suite):
        if not any(candidat == mot for candidat in it):
            contexte = " ".join(sous_suite[max(0, position - 6) : position + 1])
            return f"« …{contexte} » (mot n° {position + 1}) n'apparaît plus dans l'ordre du brut."
    return None


def verifie_integrite(
    texte_brut: str, texte_cure: str, suppressions: Suppressions, article: str = "?"
) -> RapportIntegrite:
    """Compare un curé à son brut. Aucune I/O, fonction pure."""
    bruts = mots_bruts(texte_brut, suppressions)
    corps, notes = partitionne_cure(texte_cure)

    compte_brut, compte_cure = Counter(bruts), Counter(corps) + Counter(notes)
    manquants = sorted((compte_brut - compte_cure).elements())
    ajoutes = sorted((compte_cure - compte_brut).elements())

    return RapportIntegrite(
        article=article,
        n_mots_bruts=len(bruts),
        n_mots_corps=len(corps),
        n_mots_notes=len(notes),
        manquants=manquants,
        ajoutes=ajoutes,
        desordre_corps=_premier_desordre(corps, bruts),
        desordre_notes=_premier_desordre(notes, bruts),
    )


def articles_cures(cures_dir: Path | None = None) -> list[str]:
    """Noms des articles ayant une transcription curée.

    Vide tant que le chantier B n'en a produit aucune — c'est un état
    normal, pas une erreur.
    """
    dossier = cures_dir if cures_dir is not None else CURES_DIR
    if not dossier.is_dir():
        return []
    return sorted(p.stem for p in dossier.glob("*.md"))


def verifie_article(
    article: str, bruts_dir: Path | None = None, cures_dir: Path | None = None
) -> RapportIntegrite:
    """Vérifie un article curé contre son brut, sur disque."""
    bruts = bruts_dir if bruts_dir is not None else BRUTS_DIR
    cures = cures_dir if cures_dir is not None else CURES_DIR
    chemin_brut = bruts / f"{article}.txt"
    if not chemin_brut.is_file():
        raise TranscriptionError(
            f"Aucun extrait brut pour « {article} » ({chemin_brut}). Un curé "
            f"sans brut n'est pas vérifiable : régénérer le brut avec "
            f"scripts/extraire_guide_mco.sh."
        )
    suppressions = charge_suppressions(cures / "suppressions.yaml")
    return verifie_integrite(
        chemin_brut.read_text(encoding="utf-8"),
        (cures / f"{article}.md").read_text(encoding="utf-8"),
        suppressions.get(article, suppressions[""]),
        article,
    )


__all__ = (
    "BRUTS_DIR",
    "CURES_DIR",
    "SUPPRESSIONS_PATH",
    "TITRE_NOTES",
    "RapportIntegrite",
    "Suppressions",
    "TranscriptionError",
    "articles_cures",
    "charge_suppressions",
    "mots_bruts",
    "partitionne_cure",
    "verifie_article",
    "verifie_integrite",
)
