# Chantier B — rapport du lot 3 (2026-09-03)

Six articles relus et validés par RF (verdict global OK, gras du PDF
reporté par RF sur EFFETS NOCIFS), versés, figés, mergés dans `main`.
Base après lot : **133 consignes, 315 associations curées → 18 055
couples résolus sur 15 009 codes** (après lot 2 : 120 / 291 / 17 225).

Le lot embarque aussi les **arbitrages 9 et 10** rendus entre les deux
lots : plages à borne absente au rapport (cas OMS-01/U00-U49, test
d'invariant), et `rendu_fiche` déclaratif au niveau consigne (ANT-01
basculée à `non` — 1 561 fiches avec consignes après bascule, contre
~14 500 avant).

## Volumétrie par article

| Article | Consignes | Associations |
|---|---|---|
| EFFETS NOCIFS DES MÉDICAMENTS | 4 (EFN-01..04) | 10 |
| EMPLOI DES CODES DU GROUPE B95–B98 | 2 (B95-01..02) | 8 (dont 6 `exemple`) |
| EMPLOI DES CATÉGORIES O80 À O84 | 1 (O80-01) | 2 |
| EMPLOI DES CATÉGORIES P00 À P04 | 1 (P00-01) | 2 |
| ENFANTS NÉS SANS VIE | 4 (ENF-01..04) | 1 |
| ÉTAT GRABATAIRE | 1 (GRA-01) | 1 |
| **Total** | **13** | **24** |

Incident de versement corrigé au fil : l'association GRA-01/`R26.30`
manquait à la grille des candidates (le rapport sans-code l'a signalée
au premier build — le procédé a fait son travail).

## Associations `ensemble` déclarées (1)

| Association | Rôle | Justification |
|---|---|---|
| O80-01 / `XV` | `regi` | « parmi les autres codes du chapitre XV » : domaine du choix du DP de remplacement (précédent AVC-14) |

## Consignes sans code résolu (6, toutes attendues)

ACC-02, AVC-18, REB-01, et les trois nouvelles **ENF-01/03/04**
(seuils de production du RUM, autopsie, naissance hors établissement —
règles de production sans code CIM). Non-résolue : OMS-01/`U00-U49`
(arbitrage 9, invariant testé).

## Balayage `rendu_fiche` (demandé au lot précédent)

**Aucune autre candidate à `non`.** ANT-01 était l'anomalie d'un ordre
de grandeur ; les consignes les plus larges restantes aident réellement
le rédacteur sur leurs fiches cibles :

| rec_id | Codes | Verdict |
|---|---|---|
| XXI-01 | 750 | rendue — cadre l'emploi des codes Z, décision verrouillée par le témoin Z23.0 |
| COMP-02 | 264 | rendue — apprend au rédacteur le complément T du dossier |
| ANT-02 / ANT-04 | ~235 | rendues — délimitent le périmètre des fiches Z80-Z99 |
| XXI-49 | 167 | rendue — position, sert la cohérence du séjour |
| COMP-03 | 140 | rendue — circonstances à mentionner dans le CRH |

## Signalements (artefacts de l'original, en marge des curés)

- O80 : « 19 » isolé au fil du texte (résidu d'ancienne numérotation de
  note à côté de l'appel 21) — conservé, commenté.
- ENFANTS : « être produire de RUM » (coquille du guide) et « lor sque »
  (espace parasite du rendu) — conservés, commentés.

## Évolution des témoins de fiches

Aucun attendu modifié par le versement du lot (604 tests verts) ; les
attendus avaient déjà bougé aux arbitrages 9-10 (D62, E43, F01.000,
chapitre III, A18.1 ramenés à l'état pré-ANT-01 ; R51 et J18.9
nouveaux témoins du filtre `rendu_fiche`). Bibliothèques feuilles et
catégories régénérées : **2 005 fiches avec consignes sur 16 058**.

## Outillage (au fil du lot)

- Marqueur `[^n: …]` : un niveau de crochets appariés admis (note 13
  des COMPLICATIONS, relecture RF lot 2).
- `curer_guide_mco.py` : la capture d'une note s'arrête sur un titre de
  section numéroté ; les numéros de définitions de notes *voisines* en
  colonne 0 sont sautés comme mise en page (cas 21, 47, 48).

## Prochain article

HÉMANGIOME ET LYMPHANGIOME (p. 104), puis HYPOTENSION ET BAISSE DE LA
TENSION ARTÉRIELLE (p. 104) et IDENTIFICATION DU POLYHANDICAP LOURD
(pp. 104-105).
