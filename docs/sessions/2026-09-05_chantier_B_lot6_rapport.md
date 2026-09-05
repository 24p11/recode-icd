# Chantier B — rapport du lot 6 (2026-09-05) — clôture de la série 1

Six articles relus et validés par RF (verdict global OK, sans
correction), versés, figés, mergés dans `main`. **La file des 35
articles du chapitre V est intégralement traitée.** Base après lot :
**185 consignes, 447 associations curées → 20 282 couples résolus sur
15 803 codes** (après lot 5 : 170 / 397 / 18 489 / 15 045).

Les curés et les candidates de ce lot ont été produits sur l'autre
poste (commit `73dcf19`, poppler 26.08.0) ; la relecture RF, le
versement, le gel et le build ont été faits ici.

## Volumétrie par article

| Article | Consignes | Associations |
|---|---|---|
| SEPSIS ET CHOC SEPTIQUE | 4 (SEP-01..04) | 16 (dont R65.1 `interdit`) |
| SÉQUELLES DE MALADIES ET DE LÉSIONS TRAUMATIQUES | 4 (SEQ-01..04) | 20 (dont 6 `exemple`) |
| SUICIDES ET TENTATIVES DE SUICIDE | 1 (SUI-01) | 2 |
| TRAITEMENT DES GRANDS BRÛLÉS | 1 (BRU-01) | 1 |
| TUMEURS À ÉVOLUTION IMPRÉVISIBLE OU INCONNUE | 2 (TUM-01..02) | 4 (dont 2 `exemple`) |
| VIOLENCE ROUTIÈRE | 3 (VIO-01..03) | 7 |
| **Total** | **15** | **50** |

## Décisions de relecture (RF, 2026-09-05)

- **Z86.70 n'est pas visé par SÉQUELLES.** La passation du 2026-09-04
  attendait que « le témoin Z86.70 gagnera des consignes » ; l'article
  régit les catégories « Séquelles de… » (B90-B94, E64, E68, G09, I69,
  O94, O97, T90-T98) en DAS et la priorité au code de nature — pas
  l'antécédent Z86.70, qui reste régi par l'article AVC seul. Validé
  tel quel : la doctrine (on associe ce que la consigne régit) prime
  sur l'attendu.
- **VIO-03 reste `chaque`** (R78, F10-F19, Y40-Y59, Y90-Y91 : 590
  couples) — chaque code de facteur favorisant est régi quand il est
  le facteur ; ni `ensemble`, ni `rendu_fiche=non`.
- **Trois portées `ensemble`** : SUI-01/XIX (DP du suicide ou de la
  tentative), BRU-01/XX (causes des brûlures), VIO-01/XIX (nature des
  lésions) — domaine du choix fait par le motif de séjour, précédent
  AVC-14. Le message du commit de soumission en annonçait quatre : la
  table en porte trois, et c'est la table qui fait foi.
- **Les 8 extensions sepsis de P36** (P36.00 … P36.90) sont énumérées
  mécaniquement dans SEP-01, précédent DIA/E11.

## Consignes sans code résolu (13, toutes attendues)

Les dix du lot 5, plus **SEQ-01** (définition), **BRU-01** et **VIO-01**
(leur seule association est `ensemble`). Non-résolue : OMS-01/`U00-U49`
(arbitrage 9). Non parsable : **aucune**. Traduites (arbitrage 12) :
les cinq d'ITG, inchangées.

## Configurations de transcription notables

- SEPSIS : la référence bibliographique « [1] » du choc septique (non
  numérique) reste dans le corps, avec sa bibliographie en fin
  d'article ; suppressions croisées avec SÉQUELLES (pages partagées).
- SÉQUELLES : 6 notes (69-74) ; **nouvelle règle mécanique déclarée
  par article** — ligne à deux appels hissés côte à côte (« 70 71 »).
- SUICIDES / BRÛLÉS / TUMEURS : trois articles sur deux pages
  partagées, suppressions éditoriales croisées (précédents établis).

## Évolution des témoins de fiches

Aucun attendu modifié — **687 tests verts** (12 paramétrés ajoutés
par les six curés et leurs citations). Bibliothèques feuilles et
catégories régénérées : **3 473 fiches avec consignes sur 16 058**
(2 139 après lot 5). Parmi les nouvelles : les codes sepsis (A40-A41,
B37.7, O85, P36.x0), R65.0/R65.1, A49, R57.2, les catégories de
séquelles, X60-X84, V01-V89, D37-D48, R78, F10-F19, Y40-Y59, Y85-Y91.

## Bilan de la série 1 (chantier B)

| | Après chantier A | Après lot 6 |
|---|---|---|
| Articles traités | 4 (pilote) | 4 + 35 |
| Consignes | 94 | 185 |
| Associations curées | 187 | 447 |
| Couples (consigne, feuille) | 2 806 | 20 282 |
| Codes feuilles touchés | 1 018 | 15 803 |
| Arbitrages au registre | 8 | 12 |

Ce qui reste ouvert vit dans `docs/backlog/` : diff de millésime à la
parution du guide définitif, 23 codes cités sans fiche, référentiels
externes cités (listes ATIH du polyhandicap), plafond par fiche et
conditions par code pour le rendu, obligation vs permission (DP « est
codé » vs « peut être codé »).
