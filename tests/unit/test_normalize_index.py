"""Paires dorées de la normalisation R3, issues des relectures humaines.

Chaque doré porte **deux champs au-delà de son attendu** :

- `raison` — ce qu'il protège, pour qu'un échec soit interprétable sans
  remonter au document de trace ;
- `statut` — ce que signifie un échec :

  * **`specification`** : la cible a été choisie pour sa correction
    clinique ou de périmètre. Un échec est une **régression** : le code
    a cessé de produire la bonne forme.
  * **`caracterisation`** : la cible fige une **limitation acceptée**
    (typiquement du télégraphique faute de rection attestée). Un échec
    est un **candidat à l'amélioration** : la nouvelle sortie est
    peut-être meilleure. Le message d'échec le dit explicitement.

Cette distinction vient d'un épisode réel : un doré avait été spécifié
en recopiant la sortie observée au lieu de la cible voulue, ce qui
aurait figé une régression (« infection mycoplasma » au lieu de
« infection à mycoplasma »). Séparer cible et observation évite de
refaire l'erreur.

Sources des relectures : tirages `seed=777` (v3) et `seed=4242` (v4),
cf. `docs/analyses/2026-08-09_qualite_sources_par_chapitre.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pytest

from recode_icd.lexicons import Lexiques, load_lexicons
from recode_icd.normalize_index import forme_normalisee
from recode_icd.policy import NormalisationIndex, load_policy

pytestmark = pytest.mark.unit

_PROCESSED = Path(__file__).resolve().parents[2] / "referentials" / "processed"


@dataclass(frozen=True)
class Dore:
    source: str
    attendu: str | None
    raison: str
    statut: Literal["specification", "caracterisation"]


#: Cibles choisies pour leur correction — un échec est une régression.
SPECIFICATIONS: tuple[Dore, ...] = (
    Dore(
        "Hypoplasie (de), cerveau",
        "hypoplasie du cerveau",
        "contraction `de + le` : le genre vient du corpus, pas de la source",
        "specification",
    ),
    Dore(
        "Perforation (non traumatique) (de) (due à), estomac",
        "perforation de l'estomac",
        "élision `de l'` — collée au mot, sans espace",
        "specification",
    ),
    Dore(
        "Hypertrophie (de), amygdales (avec infection)",
        "hypertrophie des amygdales",
        "contraction au pluriel `des`",
        "specification",
    ),
    Dore(
        "Atrophie (de), prostate",
        "atrophie de la prostate",
        "contraction au féminin `de la`",
        "specification",
    ),
    Dore(
        "Phlegmon (avec lymphangite aiguë) (à) (de), orbite",
        "phlegmon de l'orbite",
        "départage d'une file de connecteurs, famille `de` : `(à)` seul ne "
        "donne rien, `(de)` donne le joint",
        "specification",
    ),
    Dore(
        "Infection (à) (de), mycoplasma (pneumoniae)",
        "infection à mycoplasma",
        "symétrique du précédent pour la famille `à` : protège les rections "
        "dominantes de cette famille",
        "specification",
    ),
    Dore(
        "Maladie (à) (de) pancréas",
        "maladie du pancréas",
        "file de connecteurs sur un segment unique",
        "specification",
    ),
    Dore(
        "Ligne(s) (de), stähli",
        "ligne de stähli",
        "forme nue en dernier recours, quand aucune contractée n'est attestée",
        "specification",
    ),
    Dore(
        "Rectite (à), amibienne",
        "rectite amibienne",
        "adjectif : aucun joint inséré — l'absence d'attestation le révèle",
        "specification",
    ),
    Dore(
        "Paralysie (de), médullaire",
        "paralysie médullaire",
        "garde-fou de dominance : « de la médullaire » existe (A=1) mais "
        "« médullaire » est massivement adjectival (J=72)",
        "specification",
    ),
    Dore(
        "Syphilis (acquise) (de), utérus",
        "syphilis de l'utérus",
        "dominance substantive nette — contre-épreuve du garde-fou",
        "specification",
    ),
    Dore(
        "Varicelle (sans complication) (avec), pneumopathie",
        "varicelle avec pneumopathie",
        "un connecteur littéral ne s'accorde pas : il échappe au garde-fou "
        "de dominance, sinon « pneumopathie » (A=3, J=128) le ferait sauter",
        "specification",
    ),
    Dore(
        "Problème (avec) (de), psycho-social",
        "problème psycho-social",
        "un connecteur littéral reste soumis à l'attestation nominale, "
        "sinon on colle « problème avec psycho-social »",
        "specification",
    ),
    Dore(
        "Lipschütz, ulcère de",
        "ulcère de Lipschütz",
        "inversion d'éponyme sur préposition traînante ; la casse du nom propre est préservée",
        "specification",
    ),
    Dore(
        "Eberth, maladie d'",
        "maladie d'Eberth",
        "élision de l'éponyme : recollement sans espace",
        "specification",
    ),
    Dore(
        "Xxxx, syndrome",
        "syndrome Xxxx",
        "inversion sur substantif de tête nu (liste blanche)",
        "specification",
    ),
    Dore(
        "Nca, bien portant",
        None,
        "abréviation d'index en tête : ce n'est pas un terme",
        "specification",
    ),
    Dore(
        "Anomalie (congénitale) (type non précisé) (de), vessie nca",
        None,
        "abréviation en queue : EXCLUE, jamais amputée — « anomalie de la "
        "vessie » élargirait le périmètre au-delà du résidu non classé",
        "specification",
    ),
    Dore(
        "Oculopathie (à), syphilitique (tardive) nca",
        None,
        "même règle, sur une forme trompeuse : « oculopathie syphilitique » "
        "est correcte de FORME et fausse de PÉRIMÈTRE",
        "specification",
    ),
    Dore(
        "Deutéranomalie, deutéranopie",
        None,
        "énumération de synonymes : exclusion, car garder un segment choisirait silencieusement",
        "specification",
    ),
    Dore(
        "Hypoparathyroïdie, hypoparathyroïdisme",
        None,
        "énumération, préfixe commun long",
        "specification",
    ),
    Dore(
        "Borrelia vincenti, infection (amygdales)",
        None,
        "tête douteuse : premier segment non attesté en minuscule ⇒ écartée, "
        "jamais normalisée (asymétrie du critère d'acceptation)",
        "specification",
    ),
    Dore(
        "Kyste (colloïde) (muqueux) (séreux) (de), mésentère",
        None,
        "zone grise de dominance (A=2, J=3) : ni substantif ni adjectif ⇒ écartée",
        "specification",
    ),
)

#: Limitations acceptées — un échec est un candidat à l'amélioration.
CARACTERISATIONS: tuple[Dore, ...] = (
    Dore(
        "Crampe (des) (due à), dactylos",
        "crampe dactylos",
        "aucune rection attestée pour « dactylos » : joint non inséré. "
        "Limite de COUVERTURE du corpus, pas défaut de règle",
        "caracterisation",
    ),
    Dore(
        "Carence (en), sélénium (alimentaire)",
        "carence sélénium",
        "« sélénium » sans attestation nominale : le connecteur littéral "
        "« en » n'est pas appliqué, par asymétrie prudente",
        "caracterisation",
    ),
    Dore(
        "Autosome, site fragile",
        "site fragile Autosome",
        "« autosome » n'est attesté en minuscule nulle part hors Index : la "
        "capitale est conservée par précaution nom propre. Même famille que "
        "« Powassan » — limite de couverture du lexique de casse",
        "caracterisation",
    ),
)


@pytest.fixture(scope="module")
def outils() -> tuple[Lexiques, NormalisationIndex]:
    if not (_PROCESSED / "lexique_rections.parquet").is_file():
        pytest.skip("Lexiques absents. Lancer `uv run recode-icd build lexicons` d'abord.")
    return load_lexicons(_PROCESSED), load_policy().normalisation_index


@pytest.mark.parametrize("dore", SPECIFICATIONS, ids=lambda d: d.source[:40])
def test_specification(outils: tuple[Lexiques, NormalisationIndex], dore: Dore) -> None:
    """Cible voulue. Un échec est une **régression**."""
    lexiques, config = outils
    obtenu = forme_normalisee(dore.source, lexiques, config)
    assert obtenu == dore.attendu, (
        f"RÉGRESSION sur une spécification.\n"
        f"  source  : {dore.source!r}\n"
        f"  attendu : {dore.attendu!r}\n"
        f"  obtenu  : {obtenu!r}\n"
        f"  protège : {dore.raison}\n"
        f"  → La cible a été choisie pour sa correction clinique ou de "
        f"périmètre. Corriger le code, pas le test."
    )


@pytest.mark.parametrize("dore", CARACTERISATIONS, ids=lambda d: d.source[:40])
def test_caracterisation(outils: tuple[Lexiques, NormalisationIndex], dore: Dore) -> None:
    """Limitation acceptée. Un échec est un **candidat à l'amélioration**."""
    lexiques, config = outils
    obtenu = forme_normalisee(dore.source, lexiques, config)
    assert obtenu == dore.attendu, (
        f"CARACTÉRISATION modifiée — ce n'est pas forcément une régression.\n"
        f"  source     : {dore.source!r}\n"
        f"  figé       : {dore.attendu!r}\n"
        f"  obtenu     : {obtenu!r}\n"
        f"  limitation : {dore.raison}\n"
        f"  → RELIRE LA NOUVELLE SORTIE AVANT TOUT REVERT. Ce doré fige une "
        f"limitation connue, pas une cible : si la nouvelle forme est "
        f"meilleure, mettre à jour l'attendu et le passer en spécification."
    )


def test_les_deux_grilles_sont_disjointes() -> None:
    """Un doré a un statut et un seul."""
    sources_spec = {d.source for d in SPECIFICATIONS}
    sources_car = {d.source for d in CARACTERISATIONS}
    assert not (sources_spec & sources_car)


def test_chaque_dore_porte_une_raison() -> None:
    """Un doré sans raison est ininterprétable le jour où il casse."""
    for dore in SPECIFICATIONS + CARACTERISATIONS:
        assert len(dore.raison) > 20, f"raison trop courte pour {dore.source!r}"
