# Couverture ATIH — phase 1 : mesure (2026-09-05)

**Branche** `feat/couverture-atih` · **Type** : mesure, aucune modification
des livrables · **Statut** : rapport chiffré soumis, en attente de l'accord
RF avant toute proposition d'architecture (phase 2).

Question du chantier : *tout code autorisé en MCO doit avoir une fiche*.
Ce rapport mesure l'écart dans les deux sens entre le kit de nomenclature
ATIH 2025 et les livrables (`merged_codes.parquet` = nested set, CSV
maître = feuilles avec fiche), classe chaque écart par cause, et
documente les pièges de notation. Il instruit les backlogs
`codes_cites_sans_fiche.md` et `inclure_codes_intermediaires.md`.

Outillage (versionné, lecture seule) : `loaders_dev.load_atih_libcim10`
(+ 3 tests unitaires), `scripts/explore/2026-09-05_couverture_atih.py`,
artefacts dans `reports/couverture_atih/` (note de lecture : `reports/couverture_atih/README.md`).

---

## 1. Le référentiel ATIH : quel fichier, quelle sémantique

`data/CIM_ATIH_2025/` contient trois candidats. **Retenu :
`LIBCIM10MULTI.TXT`** (42 897 enregistrements).

| Fichier | Lignes | Verdict |
|---|---|---|
| `LIBCIM10MULTI.TXT` | 42 897 | **kit ATIH courant** : profil « SMR » sur 3 positions (dénomination post-2023), codes U08-U12 présents (post-COVID, 2021+) |
| `LIBCIM10MULTI_ch20.TXT` + `_saufch20.TXT` | 27 097 + 15 800 | les deux moitiés du précédent (concaténation identique à l'octet près, vérifié) — le chapitre XX pèse 63 % du kit |
| `cim_10_atih_2019.tsv` | 15 750 | millésime antérieur : profil « SSR » sur 4 positions, sans U08-U12, **sans le chapitre XX** (≈ `saufch20`) — écarté |

`ls.jpg` est une capture Teams sans rapport avec le kit (à retirer du
dossier de données).

**Format** (`cim.pdf`, p. 4) : ISO-8859-1, CR LF, 6 champs séparés par
`|`, sans en-tête. Code sur **6 positions, point omis, bourrage par des
espaces** ; positions 4 et 5 : chiffre, espace ou `+` ; position 6 :
chiffre ou espace. Puis Type MCO/HAD, Profil SMR (3 × O/N :
manifestation morbide principale / affection étiologique / DAS), Type PSY
(0, 1, 3), libellé court (≤ 70 car., ANSI sans accent), libellé long
(officiel, accentué).

**Type MCO/HAD** (`cim.pdf` p. 5, `type_mco_had.jpg`) :

| Valeur | Sens | n |
|---|---|---|
| 0 | pas de restriction | 13 366 |
| 1 | interdit en DP et DR, autorisé ailleurs | 441 |
| 2 | interdit en DP et DR — cause externe de morbidité | 26 536 |
| 3 | **interdit en DP, DR et DA** — catégories et sous-catégories non vides, ou code père interdit | 2 478 |
| 4 | interdit en DP, autorisé ailleurs | 76 |

**Autorisé en MCO = type ≠ 3 : 40 419 codes.** Le kit conserve aussi des
codes **supprimés**, libellé préfixé `*** SUaa ***` : 401 codes
(millésimes 06, 09, 10, 11, 12, 14, 16, 17, 19, 22, 99), tous de type 3 —
donc hors périmètre par construction.

Formes des codes du kit : `A99` 2 063 · `A999` 12 379 · `A9999` 25 117 ·
`A99999` 2 978 · `A999+9` 294 · `A99+9` 51 · `A99+99` 15.

## 2. Correspondance des écritures — la règle, et ses trois exceptions

Le kit écrit le code compact ; le maître écrit avec un point. La règle
« **point après le 3e caractère** » est vraie pour 14 350 des 14 439
appariements (99,4 %), **y compris pour les codes à `+`** quand le `+`
est en 5e position (`C169+0` ↔ `C16.9+0`) et quand il est en 4e
position (`T08+0` ↔ `T08+0`, `F03+00` ↔ `F03+00` : pas de point, il
séparerait la lettre du `+`). Le maître s'en écarte sur **89 feuilles,
trois familles**, toutes avec fiche :

| Famille | n | ATIH | Maître | Nature |
|---|---|---|---|---|
| O04 inversé | 40 | `O0490` (= 4e `9`, 5e `0`) | `O04.-0.9` (= `O04.-<5e>.<4e>`) | inversion 4e/5e — l'arbitrage 12 du chantier B |
| M62.8 inversé à tiret | 20 | `M62810` (= 5e `1` localisation, 6e `0` rhabdomyolyse) | `M62.8-01` (= `M62.8-<6e><5e>`) | **inversion 5e/6e**, vérifiée sur les libellés (`M62.8-01` « Rhabdomyolyse - Région scapulaire » = ATIH `M62810`) |
| `+` ponctué | 29 | `B24+0` | `B24.+0` | le maître ponctue le `+` de 4e position pour 9 catégories (B24, B99, F55, F61, P95, R53, R54, S47, T68) et ne le ponctue pas pour F03, T08, T10, T12 |

Trois constats sur le maître lui-même :

- **deux écritures pour une même structure** : `S37.800` (5e puis 6e,
  naturel) contre `M62.8-01` (6e puis 5e, inversé) ; `B24.+0` contre
  `T08+0` ;
- **8 nœuds de regroupement sans équivalent ATIH** — `O04.-0..3`,
  `M62.8-0`, `M62.8-8`, `S37.8-0`, `S37.8-8` — qui groupent par le
  *dernier* caractère. Retirer leur tiret ferait collisionner `S37.8-0`
  (glande surrénale, nœud) avec `S37.80` (sans plaie, feuille) ;
- la clé de correspondance (`cle_maitre` du script : point retiré,
  dés-inversion O04 et M62.8, tiret des nœuds conservé, `+` conservé)
  est **injective sur les 16 058 feuilles et les 2 654 nœuds** ;
  l'écriture naïve composée avec la clé est l'identité sur les 42 897
  codes du kit (testé dans les deux sens par assertions du script).

## 3. (a) Codes autorisés MCO (type ≠ 3) : 40 419 — qui a une fiche ?

| Classe | n | % |
|---|---|---|
| **fiche, écriture directe** | 14 051 | 34,8 % |
| notation divergente — fiche existante sous une autre écriture | 89 | 0,2 % |
| niveau intermédiaire autorisé (la branche existe au maître à un autre niveau) | 800 | 2,0 % |
| feuille du nested set sans aucune ligne au maître | 59 | 0,1 % |
| réellement absent — hors chapitre XX | 72 | 0,2 % |
| réellement absent — **extension chapitre XX** (lieu/activité) | **25 348** | **62,7 %** |

**Lecture : hors chapitre XX, 14 140 codes autorisés sur 15 071 ont une
fiche (93,8 %) ; les 931 restants se répartissent en quatre causes
identifiées, aucun écart inexpliqué.**

### 3.1 Niveau intermédiaire autorisé — 800 (787 type 0, 13 type 1)

Le code est autorisé en MCO **et** possède des subdivisions au maître.
Deux situations très différentes, à trancher en phase 2 :

| Situation | n | Exemples |
|---|---|---|
| l'ATIH connaît **aussi** les feuilles (les deux niveaux sont codables) | 563 | `F00.0` → `F00.000…` (dément Alzheimer, sévérité × symptômes ; 231 codes F), `M00.0` → `M00.00…` (252 M), `S37.80` → `S37.800/808` (43 S), `I21.00` → `I21.000…`, `B18.0`, `C16.9`, `G82.0…`, `J96.0`, `N01.7`, `O72.0`, `Z37.0` |
| l'ATIH **s'arrête** à ce niveau (les feuilles du maître lui sont inconnues) | 109 | `M16.0` → `M16.0x` (104 catégories du chapitre XIII, 5e position OFS type D), `I70.20/21` → `I70.200…`, `Z37.0/2/5` → `Z37.00…` |
| mixte | 123 | catégories du chapitre XIII où l'ATIH ne liste qu'une partie des localisations |
| dont : descendants **sans** fiche (0/2) | 4 | `C25.9` (`C25.9+0/+8` sans ligne), `Z37.0`, `Z37.2`, `Z37.5` (`Z37.x0/x1` sans ligne) |

C'est exactement le bug `U07.1` du backlog *codes intermédiaires*
(`_leaf_codes()` ne retient que les feuilles strictes), chiffré ici sur
l'autorisation MCO : **800 codes codables sans fiche**, dont 109 sont le
seul niveau codable de leur branche.

### 3.2 Feuilles du nested set sans aucune ligne — 59

Codes présents dans l'ANS mais auxquels **aucune source n'attache une
ligne** : ils n'existent pas au CSV, donc pas de fiche. Familles :

- **17 des 23 codes du backlog `codes_cites_sans_fiche`** : `Z37.10..71`
  (10), `Z60.20/28`, `Z75.80/88`, `Z76.800/850/880` — les 6 autres
  (`Z37.00/01/20/21/50/51`) sont inconnus de l'ATIH (cf. §4) ;
- codes OMS d'usage urgent et COVID : `U07.2..U07.7`, `U07.9`, `U08.9`,
  `U09.9`, `U12.9` (11) ;
- résistances aux antimicrobiens à `+` : `U82.2+0/+1 … U83.8+0/+1`,
  `U83.780/781` (16) — **cités par RAM-01..05 du guide MCO** ;
- chapitre XX : `X34.1/9`, `Y89.0`, `Y90.0..7`, `Y97`, `Y98` (13) ;
- `C11.8`, `C25.9+0`, `C25.9+8`.

### 3.3 Réellement absents hors chapitre XX — 72

Aucune forme au maître ni au nested set ; l'ancêtre existe (feuille : 62,
nœud : 10). Six familles, toutes des **extensions ATIH récentes** :

| Famille | n | Ancêtre au maître |
|---|---|---|
| `I70.00/01`, `I70.80/81`, `I70.90/91` — athérosclérose avec/sans gangrène (article ATHÉROSCLÉROSE du guide) | 6 | `I70.0/8/9` (feuilles, **type 3 à l'ATIH** — le code père est interdit) |
| `J96.100/101 … J96.190/191` — IRC obstructive/restrictive | 6 | `J96.10/11/19` |
| `M11.90..99`, `M13.00`, `M13.91..99` — localisations | 20 | `M11.9`, `M13.0`, `M13.9` |
| `M45+0..+9` — spondylarthrite ankylosante, localisation vertébrale | 10 | `M45` |
| `M62.80..89` — niveau intermédiaire ATIH (localisation seule) | 10 | `M62.8` (nœud) |
| `M83.00..09`, `M83.10..19` — ostéomalacie, localisations | 20 | `M83.0/1` |

### 3.4 Extension chapitre XX — 25 348 (tous type 2)

Le kit porte, pour les catégories V01-Y98, une sous-nomenclature
**lieu × activité** absente de l'ANS : 4e caractère = lieu (`W000`
« chute de plain-pied due à la glace et la neige, **domicile** » … `W009`),
5e = activité (`W2600…`), 6e, et une variante à `+` (`W260+0`). Formes :
`A9999` 20 405 · `A99999` 2 590 · `A999` 2 108 · `A999+9` 245, sur
2 918 codes à 4 caractères. Le maître connaît 1 396 feuilles du chapitre
XX (essentiellement les catégories à 3 caractères et le 4e caractère
OMS des V01-V99) ; l'ATIH, 27 097 codes. Ce bloc est d'une autre nature
que le reste (combinatoire de circonstances, type 2 = jamais DP/DR) et
appelle une décision propre en phase 2.

## 4. (b) Feuilles du maître : 16 058 — que dit l'ATIH ?

| Classe | n |
|---|---|
| connu de l'ATIH, autorisé (type 0/1/2/4) | 14 140 |
| connu de l'ATIH, **type 3 — interdit en MCO** | **299** |
| l'ATIH s'arrête à un niveau supérieur (le maître est plus fin) | 1 618 |
| réellement absent (catégorie seule à l'ATIH) | 1 |

- **299 fiches sur des codes interdits en MCO** : 209 catégories à 3
  caractères du chapitre XX (`W00`, `X06`…) — feuilles au maître, mais
  **pères** à l'ATIH (leurs enfants lieu/activité sont les 25 348 du
  §3.4) ; 79 codes **supprimés** (`*** SU09 ***`, ex. `M07.20`,
  `M21.40`, chapitre XIII surtout, 79 codes à 6 caractères) ; et une
  poignée de pères interdits (`C79.9`, `C80.9`, `J98.7`, `I70.0/8/9`).
  Une fiche de génération sur `W00` ou `M07.20` décrit un code qu'aucun
  RUM ne peut porter.
- **1 618 fiches sur des codes inconnus de l'ATIH** : 1 612 localisations
  du chapitre XIII (`M16.0x`, `M92.xx`… — 5e position OFS type D, que
  l'ATIH ne liste pas pour ces catégories, cf. §3.1), `I70.200/201/210/211`
  et `Z37.90/91`. Le code MCO réel est le niveau au-dessus.
- **1 réellement absent** : `N06.9` — l'ATIH ne connaît que `N06.0..8`.
- 8 nœuds du maître sans équivalent ATIH : les regroupements à tiret
  (§2). Les 2 646 autres nœuds sont connus : 800 autorisés, 1 846 pères
  interdits.

## 5. Ce que les deux backlogs deviennent

- `inclure_codes_intermediaires.md` (différé le 2026-05-25, « 2 893
  codes catégorie absents du CSV ») : la mesure ATIH le recadre à
  **800 codes intermédiaires codables** (dont 109 seul niveau codable) ;
  les 1 846 autres nœuds sont des pères interdits, à ne pas doter d'une
  fiche. `U07.1` est type 3 à l'ATIH (père) : **le témoin du backlog
  n'est pas un code autorisé** — ses feuilles `U07.10..15` le sont.
- `codes_cites_sans_fiche.md` (23 codes) : 17 sont autorisés MCO et
  vides de toute source (§3.2), 6 sont inconnus de l'ATIH (§4). Le
  comportement voulu se décide sur la classe « feuille sans ligne »
  entière (59), pas sur ces 23.

## 6. Invariant cible, et ce qu'il faut pour le poser

« Tout code autorisé MCO a une fiche » se pose sur **15 071 codes hors
chapitre XX** (931 manquants aujourd'hui, quatre causes) ; le chapitre
XX (25 348) demande une décision de périmètre préalable. Les deux
questions d'architecture de la phase 2 (fiche propre ou héritée pour
les intermédiaires ; liste pilotée par l'autorisation ATIH ; table de
notation unique partagée avec le parseur du chantier B — la clé de ce
script en est le prototype, avec **deux** familles inversées, pas une)
seront chiffrées sur ces classes. Rien n'est proposé ici.

## Artefacts

| Fichier | Contenu |
|---|---|
| `a_atih_autorises.csv` | les 40 419 codes type ≠ 3 avec classe, sous-classe, correspondant/ancêtre au maître |
| `a_atih_autorises_sans_fiche.csv` | les 26 368 sans fiche directe |
| `b_maitre_vs_atih.csv` / `b_maitre_inconnu_atih.csv` | les 16 058 feuilles du maître avec classe, type MCO, préfixe ATIH |
| `notations_divergentes.csv` | les 89 appariements où l'écriture naïve ≠ maître |
| `noeuds_intermediaires_maitre.csv` | les 2 654 nœuds du maître et leur statut ATIH |
