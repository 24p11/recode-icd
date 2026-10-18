# Nouveautés de la livraison — 2026-10-18

> À l'attention des consommateurs : **fictomed** (CHU Brest),
> **Stream** (AP-HP) et **codeur** (24p11/codeur, nouvel inscrit au
> contrat). Cumulatif depuis la livraison du 2026-09-14.
> `format_version` **1 — inchangée** : le noyau garanti d'`index.csv`
> (`code`, `fichier`, `statut_mco`, `format_version`) n'a pas bougé.

## Quatre fichiers nouveaux dans le paquet (chantier codeur)

- **`codes.csv`** — TOUS les codes du kit ATIH 2025 (42 897), codables
  ou non : `code_atih` (sans point, extension PMSI collée : `Z992+0` —
  la clé recommandée), forme pointée, libellé, `codable_mco`,
  `statut_mco`, `interdit_dp/dr/das`, millésime, version de livraison.
  **recode-icd est la seule source de la liste des codes** : ne
  retraitez pas LIBCIM10MULTI vous-mêmes.
- **`descendants_codables.csv`** — 19 977 couples (nœud, descendant
  codable avec fiche) pour la boucle de correction : `noeud_codable`
  porte le régime — `false` = le nœud ne se code pas, correction
  OBLIGATOIRE (E11, R521) ; `true` = le nœud est un code valide,
  affinage PROPOSÉ vers plus précis, jamais imposé (Z992). Même
  logique que le résolveur, invariant testé. Un nœud absent du fichier
  n'a aucun descendant codable.
- **`formulations.csv`** — 109 987 formulations rendues (après les
  filtres de qualité R1/R3/registre archaïque, SANS plafond) pour la
  recherche par mots-clés, clé `code_atih`.
- **`extensions_preambule.md`** — les extensions PMSI expliquées,
  généré du kit (pas de sémantique transversale des « + » ; « ni »
  n'existe pas au kit).

## Les fiches (rappel cumulatif depuis le 14/09)

- **Trois sections nouvelles** sur les fiches, issues des notes
  officielles de la CIM-10 validées ligne à ligne : `## Définition
  (CIM-10)` (E43), `## Description clinique (OMS)` (F20.0, glossaire
  du chapitre F), `## Notes de la CIM-10` (règles d'emploi — I21.08
  porte la règle des 28 jours héritée du bloc I20-I25, avec sa
  provenance).
- **43 fiches de bloc et de chapitre** dans la bibliothèque des
  catégories (index : 2 054 → 2 097 lignes ; codes non-catégorie
  `I20-I25`, `X`…).
- **Colonnes informatives nouvelles à `index.csv`** :
  `has_definition`, `has_description_clinique`, `has_notes_cim` — avec
  les `has_*` existantes, de quoi arbitrer quelles fiches valent leur
  coût en tokens (3 fiches seulement n'ont aucune section).

## ⚠ Pour le générateur de scénarios comme pour les consommateurs : les codes se tirent de `codes.csv`

Trouvaille du chantier (témoin `M142`) : **le kit ATIH ne subdivise pas
tout ce que le référentiel maître connaît**. Les localisations à 5ᵉ
caractère du chapitre XIII (`M1427`, `M1467`…) existent au maître
(héritage OFS) mais sont `inconnu_atih` : **non codables en MCO**. Un
scénario qui porte un tel code produit un corpus intransmissible — et
les « arrondis LLM » observés sur le chapitre XIII en étaient le
symptôme : `M142` n'était pas une troncature fautive, c'était le seul
code codable. Règle : **tout code de scénario ou de codage se tire de
`codes.csv` avec `codable_mco=true`** (ou de l'index generation) ;
en cas de doute, `recode-icd resoudre <code>` répond toujours — la
fiche, ou la raison motivée.

## Transition `_index.csv`

`_index.csv` (déprécié depuis le 2026-09-13) est encore double-écrit
dans cette livraison ; son retrait est imminent — si vous le lisez
encore, migrez vers `index.csv` (colonne `fichier`) maintenant.
