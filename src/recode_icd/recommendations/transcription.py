"""Intégrité des transcriptions curées du guide méthodologique.

Le pattern
----------
Les extraits du guide suivent la chaîne maison **brut → curé → validé →
figé** :

- `data/guide_mco/extraits_bruts/` : sortie `pdftotext -layout` intacte.
  **Artefact mécanique**, régénérable à l'identique.
- `data/guide_mco/extraits/` : **transcription curée**, relue et validée
  par un humain, puis figée. C'est elle sur laquelle s'ancre l'extraction
  des candidates du chantier B.

La curation est un **reformatage sans réécriture**. Autorisé : recoller
les lignes coupées, reconstruire les tableaux disloqués, replier les
notes de bas de page à leur point d'appel, baliser articles et sections.
**Interdit : paraphrase, condensation, réordonnancement du corps,
correction du texte du guide.** Les erreurs de l'original se signalent
en marge — en commentaire HTML — elles ne se réparent pas.

⚠ Le brut est LOSSY, et c'est structurel
----------------------------------------
`pdftotext` perd du contenu que le PDF porte : mesuré sur le pilote, le
tableau du §4.1 de l'article MALNUTRITION, DÉNUTRITION (12 seuils
chiffrés) sort en **quatre lignes vides**.

Conséquence sur la portée de ce module, à avoir en tête avant de lui
faire confiance : **il garantit la fidélité À L'EXTRAIT, jamais la
complétude vis-à-vis du PDF.** Un curé peut être parfaitement vert et
amputé d'un tableau entier. Seule la relecture humaine du PDF détecte ce
contenu perdu — et c'est l'une des raisons d'être de la couche curée,
qui serait sans objet si le brut était fidèle.

D'où le troisième mécanisme, les **restitutions** : du contenu retrouvé
dans le PDF et absent du brut. Comme il n'existe nulle part dans
l'extrait, aucune machine ne peut le vérifier — chaque restitution porte
donc sa page PDF, pour contre-vérification visuelle. C'est le seul
contrôle possible, et il est humain.

Les trois mécanismes déclarés (`extraits/curation.yaml`)
-------------------------------------------------------
1. **suppressions mécaniques** — artefacts de pagination, par motif de
   ligne (numéro de page isolé, ligne blanche) ;
2. **suppressions éditoriales** — renvois de « couche 2 » (pointeurs
   vers d'autres chapitres du guide, URL), retirés avec leur motif ;
3. **restitutions** — contenu du PDF absent du brut, avec sa page.

⚠ **Rien n'est deviné.** Un curé qui laisse tomber un paragraphe doit
échouer bruyamment ; un curé qui invente une phrase aussi. C'est tout
l'objet de la déclaration.

Les contrôles, et ce que chacun attrape
---------------------------------------
1. **Conservation** — multiensemble du curé = multiensemble du brut
   (moins les suppressions déclarées) + restitutions déclarées. Attrape
   paraphrase, condensation, ajout non déclaré.
2. **Ordre du corps** — le corps, restitutions et notes retirées, forme
   une sous-séquence du brut. Attrape le réordonnancement.
3. **Ordre des notes** — même contrôle sur les notes repliées.

Ce qui échappe, et c'est assumé : une permutation de deux notes entre
elles. Le contrôle 1 borne le dégât à un déplacement.
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
CURATION_PATH = CURES_DIR / "curation.yaml"

#: Titre de la section de notes en fin de fichier, pour les notes qu'on
#: ne peut pas replier (renvoi depuis plusieurs points d'appel).
TITRE_NOTES = "## Notes de bas de page"

#: Note **repliée à son point d'appel** : `[^57: texte de la note]`.
#:
#: Replier plutôt que rejeter en fin de fichier est un choix de fond :
#: la fiche est injectée d'un bloc dans un prompt, et une note à 700
#: lignes de son appel est un contexte perdu. La syntaxe doit rester
#: explicite — des parenthèses nues seraient indiscernables de celles
#: du guide, qui en emploie beaucoup.
#:
#: ⚠ **Le marqueur se place APRÈS le mot complet, ponctuation comprise** :
#: « précision58. [^58: …] » et non « précision[^58: …]. ». L'insérer à
#: l'intérieur couperait le token en deux et ferait échouer le contrôle,
#: à juste titre — le brut, lui, porte « précision58. » d'un bloc.
_RE_NOTE_REPLIEE = re.compile(r"\[\^([^:\]]+):\s*(.*?)\]", re.DOTALL)

#: Marqueur de renvoi nu (« [^57] »), pour une note restée en fin.
_RE_MARQUEUR_NOTE = re.compile(r"\[\^[^\]]+\]")

#: Annotation de curation : commentaire HTML. Invisible au flux de mots,
#: donc c'est là — et seulement là — qu'on signale une erreur de
#: l'original sans la réparer.
_RE_ANNOTATION = re.compile(r"<!--.*?-->", re.DOTALL)

#: Balisage markdown introduit par la curation. On retire les
#: CARACTÈRES, jamais les mots.
#:
#: ⚠ L'ordre des deux passes est load-bearing : une ligne de filet de
#: tableau (« |---|---| ») doit être reconnue AVANT que les barres ne
#: soient retirées, sinon elle devient « --- --- » et ses tirets entrent
#: dans le flux de mots.
_RE_LIGNE_FILET = re.compile(r"^[-:| ]+$", re.MULTILINE)
_RE_BALISAGE = re.compile(r"^[#>\s]*|[|]", re.MULTILINE)

#: Puces de liste. Le guide emploie « • » et « - » ; le curé emploie la
#: syntaxe markdown « - » et « * ». Ce sont deux notations du MÊME
#: balisage : on les retire des deux côtés, jamais un seul.
#:
#: Un tiret isolé qui serait du texte (« l'adulte - novembre 2019 ») est
#: retiré lui aussi — mais symétriquement, donc sans perte de pouvoir de
#: détection.
_PUCES = frozenset("-–—*•‣·")

#: Ponctuation que le rendu détache ou colle au gré des exposants.
_PONCTUATION = frozenset(".,;:!?»)")

#: Code CIM-10, éventuellement suivi d'un tiret de subdivision. Ses
#: chiffres ne sont JAMAIS un appel de note, même quand ils coïncident :
#: le chapitre XXI numérote ses notes de 23 à 48 et cite Z29, Z33, Z37,
#: Z40, Z51.30… Amputer un code le corromprait des deux côtés à la fois.
_RE_CODE_CIM = re.compile(r"[A-Z]\d{2}(\.\d{1,3})?[–—-]?$")

#: En-tête de provenance d'un fichier brut. Ce n'est pas du texte de guide.
_RE_ENTETE_BRUT = re.compile(r"\A(?:#[^\n]*\n)+", re.MULTILINE)


class TranscriptionError(ValueError):
    """Le curé ne conserve pas fidèlement le brut."""


@dataclass(frozen=True)
class Restitution:
    """Contenu du PDF absent du brut, réintroduit dans le curé.

    `page_pdf` est **obligatoire** : c'est le seul moyen de
    contre-vérifier. Aucune machine ne peut valider une restitution,
    puisque par définition son contenu n'est nulle part dans l'extrait.
    """

    texte: str
    page_pdf: int
    motif: str
    section: str = ""


@dataclass(frozen=True)
class Bornes:
    """Lignes du brut que le curé couvre.

    L'extraction se fait en **pages entières**, donc un extrait déborde
    sur l'article voisin. Le curé, lui, porte UN article. Déclarer ce
    débordement en suppressions demanderait d'y recopier des centaines
    de mots ; des bornes le disent en trois lignes.

    `titre` est vérifié à `premiere_ligne` : sans lui, un décalage du
    brut passerait pour une borne valide. Le brut est verrouillé par
    empreinte, mais la ceinture ne coûte rien.
    """

    premiere_ligne: int
    derniere_ligne: int
    titre: str = ""


@dataclass(frozen=True)
class Curation:
    """Ce qui est déclaré comme légitimement retiré ou ajouté."""

    lignes_regex: tuple[str, ...] = ()
    bornes: Bornes | None = None
    #: Numéros d'appel de note de l'article. Ce sont des EXPOSANTS, donc
    #: du balisage : `pdftotext` les colle au mot (« précision58. »,
    #: « kg/m261; ») ou les hisse seuls sur une ligne. Le curé les
    #: remplace par des marqueurs `[^n: …]`, donc on les retire des deux
    #: côtés. Déclarés article par article : les deviner reviendrait à
    #: supprimer des nombres qui sont, eux, de la donnée.
    appels_notes: tuple[int, ...] = ()
    suppressions_editoriales: tuple[tuple[str, str], ...] = ()  # (texte, motif)
    restitutions: tuple[Restitution, ...] = ()
    #: Ancre DÉCLARÉE d'une note dont l'appel est ambigu, par numéro.
    #: La valeur est une chaîne unique du texte, après laquelle la note
    #: se replie. **On ne devine pas, on déclare** : le script refuse de
    #: produire un curé tant qu'une note ambiguë n'a pas la sienne.
    ancres_notes: dict[str, str] = field(default_factory=dict)
    #: Jetons que le rendu a SOUDÉS et que le curé sépare, déclarés cas
    #: par cas : `{"obligatoire33.On": ["obligatoire.", "On"]}`. Le
    #: contrôle vérifie que les fragments recomposés, appel retiré,
    #: redonnent le jeton du brut — sans quoi une scission pourrait
    #: réécrire le texte. Pas de scission automatique : on ne généralise
    #: que sur décompte, si le chantier B en produit des familles.
    scissions: dict[str, tuple[str, ...]] = field(default_factory=dict)
    #: Relecteur et date, renseignés au gel du curé après relecture.
    relecteur: str = ""
    date_validation: str = ""

    def retire_lignes(self, texte: str) -> str:
        if not self.lignes_regex:
            return texte
        motifs = [re.compile(m) for m in self.lignes_regex]
        return "\n".join(
            ligne for ligne in texte.split("\n") if not any(m.fullmatch(ligne) for m in motifs)
        )


@dataclass
class RapportIntegrite:
    """Verdict, et de quoi localiser la divergence."""

    article: str
    n_mots_bruts: int = 0
    n_mots_corps: int = 0
    n_mots_notes: int = 0
    n_mots_restitues: int = 0
    manquants: list[str] = field(default_factory=list)
    ajoutes: list[str] = field(default_factory=list)
    restitutions_absentes: list[str] = field(default_factory=list)
    suppressions_inutiles: list[str] = field(default_factory=list)
    desordre_corps: str | None = None
    desordre_notes: str | None = None

    @property
    def conforme(self) -> bool:
        return not (
            self.manquants
            or self.ajoutes
            or self.restitutions_absentes
            or self.suppressions_inutiles
            or self.desordre_corps
            or self.desordre_notes
        )

    def message(self) -> str:
        if self.conforme:
            return (
                f"{self.article} : conforme — {self.n_mots_corps} mots de corps, "
                f"{self.n_mots_notes} de notes, {self.n_mots_restitues} restitués."
            )
        parties = [f"{self.article} : transcription NON conforme."]
        if self.manquants:
            parties.append(
                f"  {len(self.manquants)} mot(s) perdu(s) — ex. {self.manquants[:8]}. "
                f"Soit du texte a été condensé, soit une suppression légitime "
                f"n'est pas déclarée dans curation.yaml."
            )
        if self.ajoutes:
            parties.append(
                f"  {len(self.ajoutes)} mot(s) ajouté(s) — ex. {self.ajoutes[:8]}. "
                f"La curation reformate, elle ne rédige pas. Si ce contenu vient "
                f"du PDF et manque au brut, le déclarer en `restitutions` avec sa page."
            )
        if self.restitutions_absentes:
            parties.append(
                f"  {len(self.restitutions_absentes)} restitution(s) déclarée(s) mais "
                f"absente(s) du curé : {self.restitutions_absentes[:3]}. Une "
                f"restitution qui ne sert pas est une déclaration périmée."
            )
        if self.suppressions_inutiles:
            parties.append(
                f"  {len(self.suppressions_inutiles)} suppression(s) éditoriale(s) "
                f"introuvable(s) dans le brut : {self.suppressions_inutiles[:3]}. "
                f"Le texte déclaré ne correspond plus à la source."
            )
        if self.desordre_corps:
            parties.append(f"  Ordre du corps rompu : {self.desordre_corps}")
        if self.desordre_notes:
            parties.append(f"  Ordre des notes rompu : {self.desordre_notes}")
        return "\n".join(parties)


def charge_curation(path: Path | None = None) -> dict[str, Curation]:
    """Charge `curation.yaml`. La clé `""` porte le commun seul."""
    chemin = path if path is not None else CURATION_PATH
    if not chemin.is_file():
        return {"": Curation()}
    brut: dict[str, Any] = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}

    mecaniques = brut.get("suppressions_mecaniques") or {}
    commun = tuple(mecaniques.get("commun", {}).get("lignes_regex", []))
    par_article = mecaniques.get("articles") or {}
    editoriales = brut.get("suppressions_editoriales") or {}
    restitutions = brut.get("restitutions") or {}
    bornes = brut.get("bornes") or {}
    appels = brut.get("appels_notes") or {}
    ancres = brut.get("ancres_notes") or {}
    validations = brut.get("validations") or {}
    scissions = brut.get("scissions") or {}

    articles = (
        set(par_article)
        | set(editoriales)
        | set(restitutions)
        | set(bornes)
        | set(appels)
        | set(ancres)
        | set(validations)
        | set(scissions)
    )
    sortie: dict[str, Curation] = {"": Curation(commun)}
    for article in articles:
        b = (bornes.get(article) or {}) or None
        sortie[article] = Curation(
            lignes_regex=commun + tuple((par_article.get(article) or {}).get("lignes_regex", [])),
            appels_notes=tuple(int(a) for a in (appels.get(article) or [])),
            ancres_notes={str(k): str(v) for k, v in (ancres.get(article) or {}).items()},
            scissions={
                str(k): tuple(str(f) for f in v) for k, v in (scissions.get(article) or {}).items()
            },
            relecteur=str((validations.get(article) or {}).get("relecteur", "")),
            date_validation=str((validations.get(article) or {}).get("date", "")),
            bornes=Bornes(
                premiere_ligne=int(b["premiere_ligne"]),
                derniere_ligne=int(b["derniere_ligne"]),
                titre=str(b.get("titre", "")),
            )
            if b
            else None,
            suppressions_editoriales=tuple(
                (str(e["texte"]), str(e["motif"])) for e in (editoriales.get(article) or [])
            ),
            restitutions=tuple(
                Restitution(
                    texte=str(r["texte"]),
                    page_pdf=int(r["page_pdf"]),
                    motif=str(r["motif"]),
                    section=str(r.get("section", "")),
                )
                for r in (restitutions.get(article) or [])
            ),
        )
    return sortie


def _mots(texte: str) -> list[str]:
    """Flux de mots : whitespace normalisé, texte intact.

    On ne touche **ni à la casse, ni aux accents, ni à la ponctuation** :
    la curation n'a pas le droit d'y toucher non plus, donc le contrôle
    doit les voir. Seule normalisation : NFC, deux encodages Unicode du
    même caractère accentué étant le même mot pour un lecteur.
    """
    return unicodedata.normalize("NFC", texte).split()


def _depouille(mots: list[str], appels: tuple[int, ...]) -> list[str]:
    """Retire le balisage de liste et les appels de note d'un flux.

    Appliqué **des deux côtés** : ce qui est du balisage dans le brut
    l'est aussi dans le curé, seule la notation change.

    L'appel est **ancré en fin de token**, éventuellement suivi de
    ponctuation : c'est un exposant, il se place après le mot
    (« précision58. », « kg/m261; »). Un garde interdit d'amputer un
    nombre qui serait de la donnée — « 2061 » n'est pas « 20 » suivi de
    l'appel 61.
    """
    if not appels:
        return [m for m in mots if not all(c in _PUCES for c in m)]

    alternance = "|".join(str(a) for a in sorted(appels, reverse=True))
    motif = re.compile(rf"(?:{alternance})(?=[;:.,!?»)]*$)")
    sortie: list[str] = []
    for mot in mots:
        if all(c in _PUCES for c in mot):
            continue
        noyau = mot.rstrip(";:.,!?»)")
        if _RE_CODE_CIM.search(noyau):
            sortie.append(mot)
            continue
        # Un token entièrement numérique et plus long que l'appel est une
        # donnée, pas un appel collé.
        if not (noyau.isdigit() and len(noyau) > max(len(str(a)) for a in appels)):
            depouille = motif.sub("", mot, count=1)
            if depouille != mot:
                if not depouille or all(c in _PUCES for c in depouille):
                    continue
                sortie.append(depouille)
                continue
        sortie.append(mot)
    return sortie


def _sans_appel(jeton: str, appels: tuple[int, ...]) -> str:
    """Le jeton privé de son appel de note, où qu'il soit placé.

    `_depouille` n'ancre l'appel qu'en FIN de jeton — ce qui est juste
    pour « précision58. » mais pas pour un jeton soudé au mot suivant
    (« obligatoire33.On »), où l'appel est au milieu.
    """
    for appel in sorted(appels, reverse=True):
        remplace = jeton.replace(str(appel), "", 1)
        if remplace != jeton:
            return remplace
    return jeton


def _applique_scissions(mots: list[str], curation: Curation) -> tuple[list[str], list[str]]:
    """Remplace un jeton soudé par ses fragments déclarés.

    Invariant vérifié : les fragments concaténés, appel de note retiré,
    doivent redonner EXACTEMENT le jeton du brut. Sans lui, une
    déclaration de scission pourrait réécrire le texte sous couvert de
    le séparer.
    """
    if not curation.scissions:
        return mots, []
    fautives = [
        f"scission « {jeton} » : les fragments recomposés donnent « {''.join(frags)} »"
        for jeton, frags in curation.scissions.items()
        if "".join(frags) != _sans_appel(jeton, curation.appels_notes)
    ]
    sortie: list[str] = []
    for mot in mots:
        depouille = _depouille([mot], curation.appels_notes)
        cle = next(
            (j for j in curation.scissions if _depouille([j], curation.appels_notes) == depouille),
            None,
        )
        sortie.extend(curation.scissions[cle] if cle else [mot])
    return sortie, fautives


def _fusionne_ponctuation(mots: list[str]) -> list[str]:
    """Recolle au mot précédent un token fait de seule ponctuation.

    Le rendu détache la ponctuation de façon erratique — « (G83.5) . »,
    « kg/m261; » — parce qu'un exposant s'intercalait. La typographie
    française détache d'ailleurs légitimement « 18,5 ; ». Normaliser des
    DEUX côtés rend le contrôle indifférent à cette variation, qui n'est
    jamais du texte.
    """
    sortie: list[str] = []
    for mot in mots:
        if sortie and mot and all(c in _PONCTUATION for c in mot):
            sortie[-1] += mot
        else:
            sortie.append(mot)
    return sortie


def _retire_sequence(mots: list[str], sequence: list[str]) -> list[str] | None:
    """Retire la première occurrence contiguë de `sequence`, ou `None`."""
    if not sequence:
        return mots
    for i in range(len(mots) - len(sequence) + 1):
        if mots[i : i + len(sequence)] == sequence:
            return mots[:i] + mots[i + len(sequence) :]
    return None


def mots_bruts(texte: str, curation: Curation) -> tuple[list[str], list[str]]:
    """`(flux de mots du brut, suppressions éditoriales introuvables)`."""
    corps = _RE_ENTETE_BRUT.sub("", texte)
    if curation.bornes is not None:
        # Numérotation depuis le fichier COMPLET, en-tête compris : c'est
        # celle qu'affichent un éditeur et grep, donc celle qu'un humain
        # peut vérifier. `split("\n")` et non `splitlines()`, qui couperait
        # aussi sur les sauts de page \f de pdftotext.
        lignes = texte.split("\n")
        b = curation.bornes
        if b.titre and b.titre not in lignes[b.premiere_ligne - 1]:
            raise TranscriptionError(
                f"Borne fausse : la ligne {b.premiere_ligne} ne porte pas "
                f"« {b.titre} » mais « {lignes[b.premiere_ligne - 1].strip()[:60]} »."
            )
        corps = "\n".join(lignes[b.premiere_ligne - 1 : b.derniere_ligne])
    mots = _mots(curation.retire_lignes(corps))
    introuvables: list[str] = []
    for texte_supprime, _motif in curation.suppressions_editoriales:
        reste = _retire_sequence(mots, _mots(texte_supprime))
        if reste is None:
            introuvables.append(texte_supprime[:60])
        else:
            mots = reste
    return mots, introuvables


def partitionne_cure(texte: str) -> tuple[list[str], list[str]]:
    """`(mots du corps, mots des notes)` d'un extrait curé.

    Les notes repliées `[^n: …]` sont extraites du corps : sans cela, le
    contrôle d'ordre les verrait remonter avant leur position d'origine
    dans le brut, où elles vivent en bas de page.
    """
    sans_annotation = _RE_ANNOTATION.sub(" ", texte)
    notes = [m.group(2) for m in _RE_NOTE_REPLIEE.finditer(sans_annotation)]
    sans_repliees = _RE_NOTE_REPLIEE.sub(" ", sans_annotation)
    corps, _, finales = sans_repliees.partition(TITRE_NOTES)
    return _nettoie(corps), _nettoie(" ".join(notes) + " " + finales)


def _nettoie(fragment: str) -> list[str]:
    sans_marqueur = _RE_MARQUEUR_NOTE.sub(" ", fragment)
    sans_filet = _RE_LIGNE_FILET.sub(" ", sans_marqueur)
    return _mots(_RE_BALISAGE.sub(" ", sans_filet))


def _premier_desordre(sous_suite: list[str], reference: list[str]) -> str | None:
    """`None` si `sous_suite` est une sous-séquence de `reference`."""
    it = iter(reference)
    for position, mot in enumerate(sous_suite):
        if not any(candidat == mot for candidat in it):
            contexte = " ".join(sous_suite[max(0, position - 6) : position + 1])
            return f"« …{contexte} » (mot n° {position + 1}) n'apparaît plus dans l'ordre du brut."
    return None


def verifie_integrite(
    texte_brut: str, texte_cure: str, curation: Curation, article: str = "?"
) -> RapportIntegrite:
    """Compare un curé à son brut. Aucune I/O, fonction pure."""
    bruts_bruts, suppressions_inutiles = mots_bruts(texte_brut, curation)
    corps_brut, notes_brut = partitionne_cure(texte_cure)
    bruts = _fusionne_ponctuation(_depouille(bruts_bruts, curation.appels_notes))
    bruts, scissions_fautives = _applique_scissions(bruts, curation)
    corps = _fusionne_ponctuation(_depouille(corps_brut, curation.appels_notes))
    notes = _fusionne_ponctuation(_depouille(notes_brut, curation.appels_notes))

    # Les restitutions n'existent pas dans le brut : on les retire du
    # corps avant tout contrôle d'ordre, et on les ajoute au brut avant
    # le contrôle de conservation.
    corps_sans_restitution = list(corps)
    absentes: list[str] = []
    mots_restitues: list[str] = []
    for restitution in curation.restitutions:
        # `_nettoie` et non `_mots` : la restitution est écrite dans la
        # syntaxe du curé (tableau markdown), elle doit subir le même
        # dépouillement du balisage — sinon ses barres verticales
        # compteraient d'un côté et pas de l'autre.
        attendus = _fusionne_ponctuation(
            _depouille(_nettoie(restitution.texte), curation.appels_notes)
        )
        mots_restitues += attendus
        reste = _retire_sequence(corps_sans_restitution, attendus)
        if reste is None:
            absentes.append(f"p.{restitution.page_pdf} {restitution.section or restitution.motif}")
        else:
            corps_sans_restitution = reste

    compte_attendu = Counter(bruts) + Counter(mots_restitues)
    compte_obtenu = Counter(corps) + Counter(notes)

    return RapportIntegrite(
        article=article,
        n_mots_bruts=len(bruts),
        n_mots_corps=len(corps),
        n_mots_notes=len(notes),
        n_mots_restitues=len(mots_restitues),
        manquants=sorted((compte_attendu - compte_obtenu).elements()),
        ajoutes=sorted((compte_obtenu - compte_attendu).elements()),
        restitutions_absentes=absentes,
        suppressions_inutiles=suppressions_inutiles + scissions_fautives,
        desordre_corps=_premier_desordre(corps_sans_restitution, bruts),
        desordre_notes=_premier_desordre(notes, bruts),
    )


def articles_cures(cures_dir: Path | None = None) -> list[str]:
    """Noms des articles ayant une transcription curée."""
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
    curations = charge_curation(cures / "curation.yaml")
    return verifie_integrite(
        chemin_brut.read_text(encoding="utf-8"),
        (cures / f"{article}.md").read_text(encoding="utf-8"),
        curations.get(article, curations[""]),
        article,
    )


__all__ = (
    "BRUTS_DIR",
    "CURATION_PATH",
    "CURES_DIR",
    "TITRE_NOTES",
    "Bornes",
    "Curation",
    "RapportIntegrite",
    "Restitution",
    "TranscriptionError",
    "articles_cures",
    "charge_curation",
    "mots_bruts",
    "partitionne_cure",
    "verifie_article",
    "verifie_integrite",
)
