"""Normalisation des entrées de l'Index CIM-10 vol3 (règle R3, v5 figée).

**Finalité — elle départage toute ambiguïté.** La section Formulations
sert à (1) refléter le langage réellement employé par les médecins dans
les CRH et (2) ne **jamais** élargir ni brouiller le périmètre du code.
Quand le comportement mesuré et une consigne écrite divergent, c'est
cette finalité qui fait foi.

**Transformation de rendu, pas de données.** Ces fonctions sont appelées
par `cards.py` au moment d'assembler une fiche. Le CSV maître n'est
jamais modifié : sa colonne `texte` conserve la forme source de l'Index,
seule référence auditable. Normaliser en amont rendrait le libellé
officiel irrécupérable et violerait le principe « jamais d'agrégation
silencieuse ».

Le module est **pur** : les lexiques et la configuration sont passés en
paramètre, aucune I/O n'a lieu ici.

Calibration, relectures manuelles et justification métier :
`docs/analyses/2026-08-09_qualite_sources_par_chapitre.md`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from recode_icd.lexicons import FAMILLE_A, FAMILLE_DE, Lexiques
from recode_icd.policy import NormalisationIndex

RE_RENVOI = re.compile(r"(?i)\bvoir\b")
RE_PAREN = re.compile(r"\(([^()]*)\)")
RE_PAREN_NUE = re.compile(r"\s*\([^()]*\)")

#: Second segment se terminant par une préposition : sa tête est le
#: terme, le premier segment est l'éponyme (« Lipschütz, ulcère de »).
RE_EPONYME = re.compile(r"(?i)(?:^|\s)(de|d'|du|des)$")

#: Un groupe nominal portant déjà sa rection (« syndrome du choc
#: toxique ») ne reçoit pas de joint externe.
RE_RECTION_INTERNE = re.compile(r"\s(du|de la|de l'|des|de|au|à la|à l'|aux|à)\s")

#: Connecteurs parenthésés de liaison. Ce ne sont **pas** des
#: modificateurs au sens du volume 3 : ce sont des marqueurs de rection
#: grammaticale, qui indiquent comment le terme se construit. On les
#: consomme comme joint au lieu de les supprimer.
CONNECTEURS = (
    "de",
    "du",
    "des",
    "d'",
    "à",
    "au",
    "aux",
    "en",
    "le",
    "la",
    "les",
    "par",
    "pour",
    "avec",
    "sans",
    "sur",
    "dû à",
    "due à",
    "dues à",
    "dus à",
)

#: Connecteurs qui s'accordent — seuls ceux-là subissent le garde-fou de
#: dominance, puisqu'eux seuls doivent choisir un article.
_PREFIXES_FLECHIS = ("de", "du", "des", "d'", "dû", "due", "dus")
_FLECHIS_EXACTS = ("à", "au", "aux")


@dataclass(frozen=True)
class Diagnostic:
    """Trace de la décision prise pour une entrée."""

    forme: str | None
    motif_exclusion: str | None = None
    joint: str | None = None
    #: Nombre de connecteurs en file ayant chacun produit un joint
    #: attesté. > 1 signale un départage par ordre source.
    connecteurs_concurrents: int = 0


def _segments_nettoyes(texte: str) -> list[str]:
    return [s for s in (RE_PAREN_NUE.sub("", x).strip(" ,;") for x in texte.split(",")) if s]


def motif_exclusion(texte: str, config: NormalisationIndex) -> str | None:
    """Abréviation d'index ou méta-terme en tête OU en queue.

    L'entrée est **exclue, jamais amputée** : amputer élargirait
    silencieusement le périmètre. « Anomalie (de), vessie nca » désigne
    le résidu non classé ailleurs, pas toute anomalie vésicale — la
    forme amputée « anomalie de la vessie » enseignerait un périmètre
    faux, et une relecture de *forme* ne peut pas le détecter.
    """
    termes = sorted(config.abreviations_index | config.meta_termes)
    if not termes:
        return None
    motif = re.compile(r"(?i)\b(" + "|".join(re.escape(t) for t in termes) + r")\b")
    segments = _segments_nettoyes(texte)
    if not segments:
        return None
    for position, segment in (("tete", segments[0]), ("queue", segments[-1])):
        trouve = motif.search(segment)
        if trouve:
            return f"{position}:{trouve.group(1).lower()}"
    return None


def _prefixe_commun(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b, strict=False):
        if x != y:
            break
        n += 1
    return n


def est_enumeration(segments: list[str], config: NormalisationIndex) -> bool:
    """Deux synonymes juxtaposés (« Deutéranomalie, deutéranopie »).

    Exclusion, jamais conservation d'un segment : garder l'un des deux
    serait une amputation qui choisit silencieusement, et la détection
    elle-même est incertaine — le doute profite à l'exclusion.

    Le critère « un seul mot par segment » protège la tête nue :
    « Autosome, site fragile » n'est pas une énumération.
    """
    if len(segments) != 2:
        return False
    a, b = segments[0].lower(), segments[1].lower()
    if " " in a or " " in b:
        return False
    if RE_EPONYME.search(b) or b in config.tetes_nues:
        return False
    commun = _prefixe_commun(a, b)
    return (
        commun >= config.enumeration_prefixe_min
        and commun >= config.enumeration_ratio_min * min(len(a), len(b))
    )


def zone_dominance(mot: str, lexiques: Lexiques, config: NormalisationIndex) -> str:
    """`SUBST`, `ADJ` ou `GRIS` — critère de dominance, pas d'existence.

    L'existence ne suffit pas : « de la médullaire » est attesté une fois
    alors que « médullaire » est massivement adjectival (J=72). On
    compare donc les deux comptages.
    """
    a = lexiques.attestations_avec_joint(mot)
    j = lexiques.attestations_juxtaposees(mot)
    if a == 0 and j == 0:
        # Aucune évidence. La présence même du connecteur atteste que le
        # mot est un complément nominal : on juxtapose plutôt que
        # d'exclure (la variante stricte coûtait 958 entrées).
        return "ADJ" if config.inconnu_est_adjectif else "GRIS"
    seuil = config.seuil_dominance
    if j == 0 or a >= seuil * j:
        return "SUBST"
    if a == 0 or j >= seuil * a:
        return "ADJ"
    return "GRIS"


def _rection_attestee(mot: str, famille: tuple[str, ...], lexiques: Lexiques) -> str | None:
    """Forme contractée d'abord (seuil 1), forme nue en dernier (seuil 2).

    L'ordre est porteur de sens : « cuir » est attesté `du` 36 fois et
    `de` 98 fois, mais c'est « du cuir chevelu » qu'il faut produire. La
    contractée porte le genre ; la nue n'est qu'un repli.
    """
    compte = lexiques.rections.get(mot.lower())
    if not compte:
        return None
    contractees = [(n, j) for j, n in compte.items() if j in famille[:-1]]
    if contractees:
        return max(contractees)[1]
    return famille[-1] if compte.get(famille[-1], 0) >= 2 else None


def _est_flechi(connecteur: str) -> bool:
    cle = connecteur.lower()
    return cle.startswith(_PREFIXES_FLECHIS) or cle in _FLECHIS_EXACTS


def joint_pour(connecteur: str, suite: str, lexiques: Lexiques) -> str | None:
    """Joint à insérer, ou None s'il ne faut pas en insérer.

    L'absence d'attestation vaut signal : un adjectif n'est jamais
    précédé d'un article, donc ne reçoit pas de joint. C'est ce qui
    évite « rectite à l'amibienne » sans avoir à identifier les
    adjectifs.
    """
    if RE_RECTION_INTERNE.search(f" {suite.lower()} "):
        return None
    tete = suite.split(" ")[0].strip("',;")
    cle = connecteur.lower()
    if cle.startswith(_PREFIXES_FLECHIS):
        return _rection_attestee(tete, FAMILLE_DE, lexiques)
    if cle in _FLECHIS_EXACTS:
        return _rection_attestee(tete, FAMILLE_A, lexiques)
    # Connecteur littéral (« avec », « par »…) : il ne s'accorde pas, donc
    # échappe au garde-fou de dominance, mais on exige la même preuve de
    # nature nominale — sinon on colle « problème avec psycho-social ».
    if _rection_attestee(tete, FAMILLE_DE, lexiques) or _rection_attestee(
        tete, FAMILLE_A, lexiques
    ):
        return cle
    return None


def _choisir_connecteur(
    connecteurs: list[str], suite: str, lexiques: Lexiques
) -> tuple[str, str | None, int]:
    """Départage une file de connecteurs — `(connecteur, joint, concurrents)`.

    **Règle de départage : l'ordre source.** Une entrée peut porter
    plusieurs connecteurs (« Maladie (à) (de) pancréas ») ; on retient le
    **premier qui produit effectivement un joint attesté**, dans l'ordre
    où l'index les écrit. À défaut, le premier de la file, qui sert alors
    au test de dominance.

    Le cas s'est révélé nécessaire sur « Phlegmon (avec lymphangite
    aiguë) (à) (de), orbite » : `(à)` seul ne donne rien (« à l'orbite »
    n'est pas attesté), `(de)` donne « de l'orbite ». Ne retenir que le
    premier connecteur produisait « phlegmon orbite ».

    `concurrents` compte les connecteurs de la file produisant chacun un
    joint : > 1 signale que le départage a réellement joué.
    """
    joints = [(c, joint_pour(c, suite, lexiques)) for c in connecteurs]
    produisant = [(c, j) for c, j in joints if j is not None]
    if produisant:
        connecteur, joint = produisant[0]
        return connecteur, joint, len(produisant)
    return connecteurs[0], None, 0


def _colle(gauche: str, joint: str, droite: str) -> str:
    """Recolle avec l'espacement correct : les élisions s'attachent."""
    separateur = "" if joint.endswith("'") else " "
    return f"{gauche} {joint}{separateur}{droite}".strip()


def _nettoie_segment(segment: str, lexiques: Lexiques) -> tuple[str, list[str], str | None]:
    """`(texte nettoyé, connecteurs en attente, joint appliqué)`.

    Les parenthèses *qualifiantes* sont retirées : le volume 3 les
    qualifie de modificateurs **non essentiels**, sans effet sur
    l'affectation du code. Les retirer restitue le terme dans sa forme
    minimale affectante — ce n'est pas une approximation.
    """
    morceaux: list[str] = []
    attente: list[str] = []
    reste = segment
    while trouve := RE_PAREN.search(reste):
        avant, contenu, apres = (
            reste[: trouve.start()],
            trouve.group(1).strip(),
            reste[trouve.end() :],
        )
        morceaux.append(avant)
        if contenu.lower() in CONNECTEURS:
            # Le connecteur n'est « suivi » que par du vrai texte : les
            # parenthèses restantes ne comptent pas.
            suite = RE_PAREN.sub("", apres).strip(" ,;")
            if suite:
                _, joint, _ = _choisir_connecteur([contenu], suite, lexiques)
                if joint:
                    gauche = re.sub(r"\s+", " ", "".join(morceaux)).strip(" ,;")
                    droite = re.sub(r"\s+", " ", RE_PAREN.sub("", apres)).strip(" ,;")
                    return _colle(gauche, joint, droite), [], joint
                # Pas de joint pour celui-ci : on laisse sa chance au suivant.
            else:
                attente.append(contenu)
        reste = apres
    morceaux.append(reste)
    return re.sub(r"\s+", " ", "".join(morceaux)).strip(" ,;"), attente, None


def _minuscule_initiale(texte: str, lexiques: Lexiques) -> str:
    """Minuscule initiale, sauf présomption de nom propre.

    Le discriminant est le corpus : on ne minuscule que si le premier mot
    est attesté en minuscule **hors Index** — celui-ci capitalise toute
    tête d'entrée par convention et ne peut donc pas en témoigner.
    """
    if not texte:
        return texte
    premier = texte.split(" ")[0].strip(",;()")
    if lexiques.est_minuscule_attestee(premier):
        return texte[0].lower() + texte[1:]
    return texte


def normalise(texte: str | None, lexiques: Lexiques, config: NormalisationIndex) -> Diagnostic:
    """Forme normalisée d'une entrée d'Index, ou exclusion motivée."""
    if not texte:
        return Diagnostic(None, "vide")
    if RE_RENVOI.search(texte):
        return Diagnostic(None, "renvoi")
    meta = motif_exclusion(texte, config)
    if meta:
        return Diagnostic(None, f"meta:{meta}")

    segments_bruts = [s.strip() for s in texte.split(",")]
    if len(segments_bruts) > 2:
        return Diagnostic(None, "segments_multiples")
    propres = _segments_nettoyes(texte)
    if est_enumeration(propres, config):
        return Diagnostic(None, "enumeration")

    nettoyes: list[str] = []
    attentes: list[list[str]] = []
    joint_inline: str | None = None
    for segment in segments_bruts:
        net, attente, joint = _nettoie_segment(segment, lexiques)
        nettoyes.append(net)
        attentes.append(attente)
        joint_inline = joint_inline or joint

    utiles = [n for n in nettoyes if n]
    if not utiles:
        return Diagnostic(None, "vide_apres_nettoyage")
    if len(utiles) == 1:
        return Diagnostic(_minuscule_initiale(utiles[0], lexiques) or None, joint=joint_inline)

    premier, second = utiles[0], utiles[1]
    if RE_EPONYME.search(second):
        separateur = "" if second.rstrip().endswith("'") else " "
        return Diagnostic(_minuscule_initiale(f"{second}{separateur}{premier}", lexiques) or None)
    if second.lower() in config.tetes_nues:
        return Diagnostic(_minuscule_initiale(f"{second} {premier}", lexiques) or None)
    if not lexiques.est_minuscule_attestee(premier.split(" ")[0].strip(",;()")):
        return Diagnostic(None, "tete_douteuse")

    if attentes[0]:
        connecteur, joint, concurrents = _choisir_connecteur(attentes[0], second, lexiques)
        if _est_flechi(connecteur):
            zone = zone_dominance(second.split(" ")[0].strip("',;"), lexiques, config)
            if zone == "GRIS":
                return Diagnostic(None, "zone_grise")
            if zone == "SUBST" and joint:
                return Diagnostic(
                    _minuscule_initiale(_colle(premier, joint, second), lexiques) or None,
                    joint=joint,
                    connecteurs_concurrents=concurrents,
                )
        elif joint:
            return Diagnostic(
                _minuscule_initiale(_colle(premier, joint, second), lexiques) or None,
                joint=joint,
                connecteurs_concurrents=concurrents,
            )
    return Diagnostic(_minuscule_initiale(f"{premier} {second}", lexiques) or None)


def forme_normalisee(
    texte: str | None, lexiques: Lexiques, config: NormalisationIndex
) -> str | None:
    """Raccourci : la forme seule, ou None si l'entrée est écartée."""
    return normalise(texte, lexiques, config).forme


__all__ = (
    "CONNECTEURS",
    "Diagnostic",
    "est_enumeration",
    "forme_normalisee",
    "joint_pour",
    "motif_exclusion",
    "normalise",
    "zone_dominance",
)
