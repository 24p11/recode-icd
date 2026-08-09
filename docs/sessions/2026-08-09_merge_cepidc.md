# Merge CepiDc 2015 + renommage libellé + correctif des témoins (chantier 1)

**Date** : 2026-08-09
**Type** : merge de branche + deux correctifs amendés + un correctif imprévu
**Statut** : terminé — 361 tests verts, 0 skip, ruff et mypy propres, artefacts régénérés
**Plan validé** : cf. session `2026-08-09_etat_des_lieux_reprise.md` pour le diagnostic amont

---

## 1. Résultat en une ligne

`feat/cepidc-integration` est intégrée à `main`. Le CSV maître passe de
**199 970 à 321 097 lignes** (15 sources), la couverture de la section
Formulations des fiches de **47,1 % à 53,7 %**. Les trois tests témoins qui se
skippaient silencieusement passent désormais, et trois artefacts dont l'ordre
des lignes était instable d'un build à l'autre sont devenus déterministes.

## 2. Ce qui a été fait, dans l'ordre

### 2.1 Neutralisation de `.DS_Store` (commit `a84430d`)

`main` et la branche divergeaient d'un commit chacune, mais le commit de `main`
(`25bd0f5`, « maj ») ne touchait que `.DS_Store`. L'intersection des fichiers
modifiés des deux côtés depuis la base commune `2edf6c5` étant **vide**, le
merge était prouvé sans conflit avant même d'être tenté.

`.DS_Store` figurait déjà dans `.gitignore` (ligne 20), mais la règle est
arrivée après le commit initial des fichiers — et `.gitignore` n'affecte pas ce
qui est déjà suivi. Les **4 fichiers** encore dans l'index ont été dépistés par
`git rm --cached` (ils restent sur le disque), *avant* le merge, pour que
celui-ci ne porte que sur CepiDc. Le commit `25bd0f5` devient ainsi sans objet
sans aucune réécriture d'historique.

> **Incident rencontré.** Le premier `git commit` a échoué : le hook installé
> par `uv run pre-commit install` lors de la session précédente refuse de
> tourner car **`.pre-commit-config.yaml` n'existe pas dans le dépôt**. Le
> CLAUDE.md documente pourtant `uv run pre-commit install` comme commande
> courante. Le hook a été désinstallé (annulation de l'action de la session
> précédente) — cf § Constats à traiter.

### 2.2 Merge (commit `9658f80`)

`git merge --no-ff` — aucun conflit, 24 fichiers, +139 446 / −8 826. Vérifié
après coup : aucun `.DS_Store` n'est revenu dans l'index.

### 2.3 Renommage du libellé CSV `CepiDc_2015` → `CepiDc 2015`

L'enum Python `CEPIDC_SOURCE = "CEPIDC_2015"` est inchangé ; seul le libellé
d'export bouge. **10 occurrences** dans 5 fichiers, toutes traitées avant le
build pour ne régénérer les artefacts qu'une fois.

Le point sensible était `cards.py` : les lignes 435 et 948 filtraient le
libellé par **égalité stricte** (contrairement au `starts_with("AP-HP")` des
sources AP-HP). Renommer sans elles aurait fait perdre CepiDc à la section
Formulations **silencieusement** — pas d'exception, juste la cible de 54 % non
atteinte, et aucun test ne couvre ce chemin de rendu. Vérifié après build par
inspection de la fiche `R51` : les formulations télégraphiques CepiDc
(« céphalée brutale », « céphalées aigües », « douleurs maxillo-faciales ») y
côtoient bien les entrées Index en casse titre.

Correctif documentaire au passage : les docstrings de
`loaders/external/_schemas.py` parlaient encore de « trois loaders ».

### 2.4 Build

Portée volontairement limitée à la chaîne aval (`external` → `flat-csv` →
`stats` → `cards build` → `cards build-categories`). `build owl` et `build ofs`
n'ont **pas** été rejoués : ils embarquent un `generated_at` horodaté dans les
métadonnées Parquet (`owl.py:120`, `ofs.py:229`) et produiraient un diff binaire
parasite sur des artefacts que CepiDc ne modifie pas.

### 2.5 Correctif des témoins

Trois tests de régression se terminaient par `pytest.skip()` parce que leur
code témoin n'atteint pas le CSV final. La cause est le filtre `_leaf_codes()`
(`flat_csv.py:77`), qui restreint le CSV aux feuilles strictes du nested set :
`U07.1` porte les sous-divisions ATIH `U07.10`..`U07.15` et `L62` a deux
enfants (`L62.0`, `L62.8`). L'arbitrage du backlog
`inclure_codes_intermediaires.md` n'a **pas** été rouvert ; on a remplacé les
témoins et transformé les skips en faits affirmés.

| Ancien témoin | Nouveau | Pourquoi ce choix |
|---|---|---|
| `U07.1` | **`U07.13`** | Vraie feuille du bloc COVID, et surtout : les trois redirections vérifiées `(B34.2)`, `(B97.2)`, `(U04.9)` lui sont propagées **mot pour mot** depuis `U07.1` (`source_level=category`). Le test assertionne donc exactement la même chose qu'avant, et exerce en prime la propagation. |
| — | **`A92.5`** (Zika) | Témoin post-2006 riche ajouté : 3 types, 3 sources (ANS, CIM-10, ORPHANET), propagation chapitre + catégorie + code. Couvre l'enrichissement externe, impossible sur le bloc COVID (sources externes toutes pré-2020). |
| `L62` | **`L62.8`** | Jumeau sémantique exact dans DAGSTAR (`dagger_code=null`, `redundancy_level=none`, une seule association). Sémantique du test préservée à l'identique. |
| — | **`N16.8`** | Second témoin non pointé, choisi pour sa richesse (3 types, 4 sources) là où `L62.8` se limite à 4 lignes d'exclusion. |

Deux nouveaux tests **affirment l'absence** de `U07.1` et de `L62` du CSV, avec
un message d'échec qui renvoie explicitement au backlog et indique quoi inverser
si l'option B est un jour implémentée. Les trois `pytest.skip()` restants de
`test_dagger_asterisk_flags.py` ont aussi été convertis en assertions : un
témoin qui disparaît doit faire échouer la suite, pas la faire taire.

### 2.6 Correctif de déterminisme — **hors plan initial**

En comparant les artefacts régénérés, deux rapports apparaissaient modifiés
alors que leur contenu était **identique après tri**. Diagnostic conduit avant
toute correction :

- **Observation** : deux builds consécutifs sur entrées identiques produisent
  des octets différents pour `reports/cepidc_ignored.csv`,
  `reports/external_overlaps.csv` et
  `referentials/processed/external_to_add.parquet`. Vérifié empiriquement par
  double build et comparaison md5.
- **Cause** : `group_by()` polars ne garantit pas l'ordre de sortie, les joins
  non plus. `_build_cepidc_ignored_report` triait sur la seule colonne
  `n_formulations_perdues`, laissant les ex æquo permuter ; `overlaps_df` et
  `to_add_df` n'étaient pas triés du tout.
- **Portée réelle** : le **CSV maître est resté stable de bout en bout**, car
  `flat_csv.build()` applique son propre tri. Seuls les artefacts intermédiaires
  et les rapports d'audit étaient concernés.

C'est une violation directe de la convention du CLAUDE.md (« fonctions pures et
déterministes — mêmes entrées → byte-equivalent en sortie »), et sans correctif
chaque build aurait produit ~3 200 lignes de diff parasite. Trois tris explicites
ont été ajoutés dans `merge_external.py`, avec commentaire justificatif.
Vérification : deux builds successifs produisent désormais des artefacts
strictement identiques sur les 6 sorties de la chaîne.

> Ce correctif sort du plan validé. Il est signalé ici explicitement ; il est
> isolable en un commit si tu préfères le sortir du chantier.

### 2.7 Lint

Les 5 erreurs ruff préexistantes (toutes dans `tests/`) sont corrigées :
2 espaces insécables en docstring, un `zip()` sans `strict=`, un import `re`
inutilisé, une concaténation remplacée par de l'unpacking.

`ruff format --check` signale 46 fichiers non conformes — **condition
préexistante**, vérifiée identique avec mes changements remisés. Le dépôt n'a
jamais été passé au formateur ; lancer `ruff format` créerait un diff massif
sans rapport avec ce chantier. Non fait.

## 3. Contrôles de sortie

| Contrôle | Attendu | Mesuré |
|---|---|---|
| Lignes CSV maître | 321 097 | **321 097** ✓ |
| Sources | 15 | **15** ✓ |
| Libellé `CepiDc 2015` | présent | 121 127 lignes ✓ |
| Libellé `CepiDc_2015` | absent | 0 ✓ |
| Bilan CepiDc | 146 948 → 121 127 | 146 948 chargées, 1 658 absorbées, 6 928 orphelines, 17 235 non terminales, **121 127 ajoutées** ✓ |
| Couverture Formulations | ~54 % | **53,7 %** (7 523 → 8 629 fiches) ✓ |
| Fiches générées | — | 16 058 feuilles (+80) et 2 054 catégories |

### Disjonction de l'apport CepiDc — les deux chiffres réconciliés

Le brief annonçait 99,5 %, la doc de la branche « ~1,1 % d'absorption ». Les
deux sont justes, ils ne portent pas sur le même dénominateur :

| Périmètre d'absorption | Entrées | Disjonction |
|---|---|---|
| vs **Index + AP-HP** seulement | 775 | **99,47 %** ← le « 99,5 % » du brief |
| vs toutes les sources externes | 1 144 | 99,22 % |
| vs tout, OFS/ANS inclus | 1 658 | 98,87 % ← le « 1,1 % » de la doc |

### Tests

**361 passed, 0 skipped** (contre 334 passed + 3 skipped avant chantier).

| Marqueur | Avant | Après | Prévu au plan |
|---|---|---|---|
| unit | 245 | **247** | 247 ✓ |
| integration | 21 | **26** | 26 ✓ |
| regression | 68 (+3 skip) | **90** | 82 |

L'écart sur `regression` s'explique intégralement : `test_cepidc.py` porte un
`pytestmark = regression` au niveau module **et** un `@pytest.mark.unit` sur deux
fonctions, si bien que ces deux-là comptent dans les *deux* sélecteurs — d'où
+13 en regression (et non +11) et +2 en unit. Soit 71 + 13 + 3 = 87, plus mes
ajouts : 2 tests d'absence et 1 cas de paramétrage (`N16.8`) = **90**. Les 84
annoncés dans le brief correspondaient aux *passed* de la branche seule, skips
exclus (87 − 3 = 84).

`ruff check` : *All checks passed*. `mypy` : *no issues found in 30 source files*.

## 4. Diffs significatifs, fichier par fichier

### Code de production

| Fichier | Nature |
|---|---|
| `src/recode_icd/loaders/external/cepidc.py` | **nouveau** (branche), 116 lignes — loader CSV `;`, réutilise `normalize_compact_code` / `normalize_for_match` / `_STANDARD_CODE_RE` de `_normalize.py`, tout en `type=synonyme` |
| `src/recode_icd/merge_external.py` | branche : +66 (CepiDc en dernier dans `_EXTERNAL_ORDER`, rapport `cepidc_ignored`). **Session** : 3 tris explicites pour le déterminisme |
| `src/recode_icd/cli/build.py` | branche : option `--cepidc-csv`, défaut renseigné, garde d'existence non fatale |
| `src/recode_icd/cards.py` | branche : CepiDc dans les deux sections Formulations. **Session** : renommage du libellé (l. 435 et 948) |
| `src/recode_icd/exporters/flat_csv.py` | mapping enum→libellé : `CEPIDC_2015` → `CepiDc 2015` |
| `src/recode_icd/loaders/external/_schemas.py` | docstrings « trois » → « quatre » loaders |

### Tests

| Fichier | Nature |
|---|---|
| `tests/unit/loaders/external/test_cepidc.py` | **nouveau** (branche), 13 tests |
| `tests/regression/test_flat_csv_witnesses.py` | 2 tests retargetés sur `U07.13`, skips supprimés, +`test_u07_1_absent_du_csv` |
| `tests/regression/test_dagger_asterisk_flags.py` | `_ASTERISK_TRUE` : `L62`→`L62.8`, +`N16.8` ; 3 skips → assertions ; +`test_l62_absent_du_csv` ; tableau du docstring à jour |
| `tests/fixtures/sample_codes.yaml` | entrée `L62` → `L62.8` (libellé corrigé au passage), + `N16.8`, `U07.13`, `A92.5` |
| `tests/{integration,regression}/…` | renommage du libellé (6 lignes) |
| 4 fichiers `tests/unit/` et `tests/regression/` | correctifs ruff |

### Documentation

| Fichier | Nature |
|---|---|
| `CLAUDE.md` | section CepiDc complétée (libellé, pattern CLI, volumétrie, disjonction) ; mapping enum→libellé ; **nouveau pitfall** sur `U07.1` non utilisable comme témoin CSV ; liste des codes témoins |
| `docs/source_mapping.md` | témoins post-2006 : `U07.1` → `U07.13` + `A92.5`, avec l'explication du filtre `_leaf_codes()` |

### Artefacts régénérés

`inclusions_exclusions_synonymes.csv`, `external_to_add.parquet`,
`reports/{cepidc_ignored,external_overlaps,csv_stats,curation_applied}`.
Les deux `_index.csv` des bibliothèques de fiches sont ressortis
**byte-identiques** à ceux committés par la branche — bonne validation du
déterminisme de `cards.py`.

## 5. Constats à traiter, non traités ici

1. **`.pre-commit-config.yaml` absent du dépôt.** Le CLAUDE.md documente
   `uv run pre-commit install`, mais aucun fichier de configuration n'est
   versionné : installer le hook rend tout commit impossible. Le hook a été
   désinstallé. Il faut soit committer une configuration (ruff check + format +
   mypy seraient les candidats naturels), soit retirer la commande du CLAUDE.md.
2. **Artefact de codes CepiDc sur 5 caractères.** 91 des 123 codes ignorés ont
   une décimale à 2 chiffres (`R58.09`, `I63.59`, `I21.99`…). CepiDc utilise une
   convention interne où le 5ᵉ caractère est une extension maison, pas une
   sous-division CIM-10 ; `normalize_compact_code` en fait un code inexistant.
   Coût : **6 928 formulations perdues**, dont 1 781 sur les quatre plus gros
   codes (AVC, IDM, hémorragies). Tronquer le 5ᵉ caractère en récupérerait
   l'essentiel.
3. **Les fiches catégories vont être dominées par CepiDc.** Mesuré : CepiDc
   représente 75 % du vivier global des formulations éligibles. Sur les **737
   catégories dont le vivier dépasse le plafond `CATEGORY_FORMULATIONS_MAX = 50`**,
   la part médiane de CepiDc est de **76,4 %**, et **325 d'entre elles dépassent
   80 %**. Contrairement aux fiches feuilles (où Index et CepiDc sont plafonnés
   à 10 chacun, AP-HP restant non plafonné), les fiches catégories n'ont
   **aucun plafond par source**. À traiter dans le chantier `chapter_policy`,
   qui touche déjà cette zone de `cards.py`.
4. **Marqueurs pytest incohérents** dans `tests/unit/loaders/external/test_cepidc.py` :
   fichier sous `tests/unit/` mais `pytestmark = regression`, avec deux fonctions
   portant un `@pytest.mark.unit` contradictoire — d'où le double comptage
   expliqué au §3. Non modifié pour ne pas fausser la comparaison des compteurs.
5. **`ruff format` jamais passé** sur le dépôt (46 fichiers non conformes,
   condition préexistante).

---

# Volet A — clôture des questions ouvertes

Trois des cinq constats du § 5 sont traités ; deux restent ouverts et sont
renvoyés au chantier `chapter_policy`.

## A.1 Verrou sur les libellés de source des fiches (constat n° 3 bis)

Le chemin de rendu de la section Formulations n'était couvert par aucun test :
`cards.py` filtre par **égalité stricte** sur le libellé CSV, donc un renommage
non répercuté fait disparaître une source **sans exception ni test rouge**.

Mécanisme retenu, après avoir écarté les alternatives : plutôt que d'énumérer
des textes attendus (fragile — le contenu bouge à chaque mise à jour de source)
ou d'analyser le source de `cards.py` (fragile — parsing), les libellés sont
sortis en **constantes** de `cards.py` (substitution littérale, zéro changement
de comportement) et confrontés au mapping `_SOURCE_CSV_MAP`.

`tests/regression/test_cards_formulations_sources.py`, 5 tests sur trois
niveaux :

1. **`test_toute_source_du_mapping_est_tranchee`** — le verrou principal.
   Chaque libellé du mapping doit être soit inclus (`FORMULATION_SOURCES_EXACT`
   / `FORMULATION_SOURCE_PREFIXES`), soit explicitement exclu
   (`FORMULATION_SOURCES_EXCLUDED`). Symétriquement, aucun libellé déclaré dans
   `cards.py` ne peut être absent du mapping — c'est la signature exacte d'un
   renommage à moitié fait. **Ajouter une source sans statuer sur son sort fait
   échouer la suite.**
2. **`test_source_exacte_produit_des_lignes_dans_le_csv`** — un libellé peut
   être cohérent entre les deux modules et ne rien produire (faute de frappe
   partagée, source vidée en amont).
3. **`test_r51_formulations_couvre_les_sources_plafonnees`** — bout en bout :
   la fiche R51 rendue contient au moins une entrée dont le CSV atteste
   qu'elle vient de l'Index, et une de CepiDc.

**Validé par mutation** : en remettant `CepiDc_2015` dans la constante,
3 des 5 tests virent au rouge, dont le verrou structurel et le contrôle bout
en bout. Le test détecte donc bien la panne qu'il est censé prévenir.

## A.2 pre-commit (constat n° 1)

`.pre-commit-config.yaml` versionné. Trois hooks : `ruff check --fix`,
`ruff format`, et une garde `language: fail` interdisant les `.DS_Store`
(vérifiée : un `git add -f .DS_Store` fait bien échouer le commit).

Deux décisions de conception :

- **Hooks `language: system`** appuyés sur le ruff déjà installé par `uv sync`
  (0.15.13, épinglé dans `uv.lock`), plutôt que `ruff-pre-commit` avec son
  propre `rev:`. Le hook et `uv run ruff check` utilisent ainsi strictement la
  même version, sans seconde installation qui dériverait silencieusement.
- **Périmètre ruff limité à `src/` et `tests/`**, celui des commandes du
  CLAUDE.md. `scripts/explore/` est du code exploratoire jamais linté — il y
  dort 31 erreurs, et l'inclure bloquerait des commits sans rapport. `arXiv/`
  (archive legacy figée) est ajouté à `extend-exclude` de ruff.

**Effet de bord assumé** : le hook `ruff format` était inutilisable sur un
dépôt jamais formaté (47 fichiers non conformes) — tout commit les touchant
aurait été interrompu. Un commit dédié `style: passer ruff format sur src/ et
tests/` établit la baseline (45 fichiers, +1 697 / −1 207, purement mécanique,
suite verte avant et après). C'est le prix d'entrée du hook demandé ; il est
isolé dans son propre commit.

## A.3 Vérifications finales

| Contrôle | Résultat |
|---|---|
| `pytest` | **366 passed, 0 skipped** (247 unit / 95 regression / 26 integration) |
| `ruff check src/ tests/` | All checks passed |
| `ruff format --check src/ tests/` | 69 files already formatted |
| `mypy src/recode_icd` | no issues found in 30 source files |
| Rebuild des fiches | `_index.csv` byte-identiques → l'extraction en constantes n'a rien changé au rendu |

Le passage de 90 à 95 tests de régression correspond aux 5 tests du § A.1.

## A.4 Ce qui reste ouvert

Les constats n° 2 (artefact des codes CepiDc à 5 caractères, 6 928 formulations
perdues) et n° 3 (déséquilibre CepiDc des fiches catégories) ne sont pas
traités : ils relèvent du chantier `chapter_policy` et de l'analyse de qualité
des sources (`docs/analyses/2026-08-09_qualite_sources_par_chapitre.md`). Le
constat n° 4 (marqueurs pytest incohérents dans `test_cepidc.py`) reste
signalé, non modifié.

## État git

Sept commits sur `main`, aucun poussé :

| Commit | Objet |
|---|---|
| `a84430d` | dépistage des `.DS_Store` |
| `9658f80` | merge de `feat/cepidc-integration` |
| `f989d16` | libellé `CepiDc 2015` + correctif des témoins |
| `fc42373` | déterminisme des sorties externes |
| `a74200d` | régénération des artefacts |
| `4fe64c9` | `.pre-commit-config.yaml` |
| `e13697c` | baseline `ruff format` |
| `17d22b8` | verrou sur les libellés de source des fiches |

**Rien n'a été poussé sur `origin`.**
