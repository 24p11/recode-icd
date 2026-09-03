# Chantier B — rapport du lot 2 (2026-09-03)

Six articles relus et validés par RF (verdict global OK, deux
corrections de curé intégrées), versés, figés, mergés dans `main`.
Base après lot : **120 consignes, 291 associations curées → 17 225
couples résolus sur 14 824 codes** (après lot 1 : 108 / 226 / 16 548).

## Volumétrie par article

| Article | Consignes | Associations |
|---|---|---|
| CODES OMS RÉSERVÉS A UN USAGE URGENT | 2 (OMS-01..02) | 3 |
| COMPLICATIONS DES ACTES MÉDICAUX ET CHIRURGICAUX | 6 (COMP-01..06) | 49 (dont 23 `exemple`) |
| CYSTITE AIGÜE | 1 (CYS-01) | 2 |
| DIABÈTE DE TYPE 2 TRAITÉ PAR INSULINE | 1 (DIA-01) | 10 (E11.00..E11.90) |
| DOULEUR CHRONIQUE | 1 (DOU-01) | 1 |
| DOULEUR CHRONIQUE REFRACTAIRE (REBELLE) | 1 (REB-01) | 0 |
| **Total** | **12** | **65** |

## Corrections de relecture intégrées

- **Note 13 des COMPLICATIONS repliée à son point d'appel** (RF) : la
  section « Notes de bas de page » disparaît. Le marqueur `[^n: …]`
  admet désormais un niveau de crochets appariés dans le texte de la
  note (« Atteintes [Troubles]... ») — extension de `_RE_NOTE_REPLIEE`
  dans `transcription.py`, test unitaire
  `test_note_repliee_a_crochets_internes`.
- Paragraphe final du réfractaire recollé (coupure de page).

## Associations `ensemble` : aucune dans ce lot

## Signalements

1. **`GM2026-V-OMS-01` / `U00-U49` non résolue** (rapport
   `guide_mco_expressions_non_resolues.csv`) : la résolution d'une
   plage exige l'existence de ses deux bornes dans le nested set, et
   `U00` n'existe pas — les codes U sont clairsemés (U04, U07, U09,
   U10…). La consigne atteint néanmoins les fiches U07.* par sa seconde
   association (`U07`). **Arbitrage ouvert** : étendre la résolution
   aux plages à bornes creuses (toutes les catégories dont le code
   trie dans [U00, U49]) ou laisser l'association au rapport. Aucune
   perte silencieuse en attendant.
2. **Trois consignes sans code résolu** (normal, précédent AVC-18) :
   ACC-02, AVC-18, REB-01 — REB-01 est une `definition` d'un article
   qui ne nomme aucun code.
3. **COMP-04** : la règle « toutes subdivisions .8/.9 du groupe
   T80-T88 hors T86 interdites en DP » reste dans le texte de la
   consigne — pas d'expression parsable, l'énumérer serait interpréter.
   Validé RF avec le lot.

## Évolution des témoins de fiches

Aucun attendu modifié : le lot n'ajoute pas de règle de chapitre, et
aucun témoin (D62, E43, F01.000, Z23.0, Z86.70, I64, Z51.5, Z20.1,
W65, A18.1) n'est visé par les nouvelles associations. Suite : **583
tests verts** (582 + le test unitaire du marqueur à crochets).

## Gel

Six curés au manifeste avec `relecteur: RF, date: 2026-09-03` ; six
bruts ajoutés au manifeste des bruts. Cases 6-11 cochées dans
`file_chantier_B.md`.

## Prochain article

EFFETS NOCIFS DES MÉDICAMENTS (pp. 90-91, notes 16-19), puis EMPLOI
DES CODES DU GROUPE B95–B98.
