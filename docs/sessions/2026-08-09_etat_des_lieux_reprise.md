# État des lieux — reprise du projet sur nouvelle machine (chantier 0)

**Date** : 2026-08-09
**Type** : audit en lecture seule (aucune modification de code)
**Statut** : terminé — environnement installé, suite de tests verte, checklist de rapatriement établie

---

## 1. Contexte et périmètre

Reprise de `recode-icd` sur un nouveau poste, dépôt cloné depuis
`https://github.com/24p11/recode-icd`. Objectif : établir un état des lieux
complet sans rien modifier. Seule écriture autorisée et effectuée : le présent
document.

**Verdict global** : le dépôt est en bien meilleur état que redouté. La quasi-
totalité du code, de la documentation, des données sources et des artefacts de
pipeline est versionnée et présente. Le seul manque réel concerne les sorties
de la campagne LLM (gitignorées, jamais produites dans cette copie de travail)
et la clé API Mistral.

---

## 2. Environnement et suite de tests

`uv sync` et `uv run pre-commit install` se sont déroulés sans erreur
(uv 0.11.16, hook installé dans `.git/hooks/pre-commit`).

### Suite de tests sur `main` — verte

```
334 passed, 3 skipped in 21.83s
```

Répartition par marqueur (à conserver comme référence de base pour mesurer
l'apport du chantier 1) :

| Marqueur | Résultat |
|----------|----------|
| `unit` | 245 passed |
| `regression` | 68 passed, 3 skipped |
| `integration` | 21 passed |
| **Total** | **334 passed, 3 skipped** |

### Les 3 tests skippés — cause identifiée, comportement attendu

```
tests/regression/test_dagger_asterisk_flags.py:59   — L62 absent du CSV final
tests/regression/test_flat_csv_witnesses.py:103     — U07.1 sans exclusion ANS dans le CSV final
tests/regression/test_flat_csv_witnesses.py:211     — U07.1 absent du CSV
```

J'ai tracé l'origine plutôt que de la supposer. `U07.1` est bien présent en
amont du pipeline — dans `owl_codes.parquet` (1 ligne), `merged_codes.parquet`
(1 ligne, `label="COVID-19"`, `type="category"`, `depth=3`) et
`propagated_notes.parquet` (2 notes, une inclusion et une exclusion, source
`OWL_ANS`) — mais absent du CSV final (0 ligne). Même chose pour `L62`.

La cause est le filtre `_leaf_codes()` de
[flat_csv.py](../../src/recode_icd/exporters/flat_csv.py#L77), qui restreint le
CSV aux feuilles strictes au sens nested set (`right - left == 1`). `U07.1`
porte des sous-divisions ATIH `U07.1X` et devient donc un nœud intermédiaire.

**Ce n'est pas une régression** : c'est un arbitrage documenté et
délibérément différé, décrit dans
[docs/backlog/inclure_codes_intermediaires.md](../backlog/inclure_codes_intermediaires.md)
(décision RF du 2026-05-25, on reste sur les codes terminaux). Ce backlog
chiffre l'impact : 2 893 codes `type == category` absents du CSV, dont 916
codes 4-caractères réellement codables en pratique.

**Point de tension à arbitrer un jour** : le CLAUDE.md impose `U07.1` comme
« code témoin de référence » pour les codes post-2006, mais le filtre en cours
l'exclut du livrable principal. Les tests de régression correspondants se
contentent de skipper, donc la couverture post-2006 est en réalité non
vérifiée. Aucune action prise dans cette session.

### Lint et typage

- `uv run mypy src/recode_icd` : **Success: no issues found in 29 source files**
- `uv run ruff check src/ tests/` : **5 erreurs, toutes dans `tests/`**, aucune
  dans `src/` :

| Fichier | Règle |
|---------|-------|
| `tests/regression/test_curation_csv_codes_valid.py:6` et `:81` | RUF002 espace insécable dans docstring |
| `tests/unit/test_apply_curation.py:95` | B905 `zip()` sans `strict=` |
| `tests/unit/test_cards.py:14` | F401 `re` importé mais inutilisé (auto-fixable) |
| `tests/unit/test_export_curation_csv.py:189` | RUF005 concaténation au lieu d'unpacking |

Cosmétique, non bloquant, non corrigé ici (session en lecture seule). À noter
que le hook pre-commit venant d'être installé, ces erreurs se manifesteront au
prochain commit touchant ces fichiers.

---

## 3. Branches distantes

Une seule branche distante en plus de `main` :

### `origin/feat/cepidc-integration`

| Métrique | Valeur |
|----------|--------|
| Ahead / behind vs `main` | **1 commit d'avance, 1 commit de retard** |
| Dernier commit | `9375c06` — 2026-06-08 16:02 — *feat: intégration CepiDc 2015 comme source de synonymes* |
| Base commune | `2edf6c5` (notebooks LLM phase 1 et 2) |

Le « 1 de retard » est sans conséquence : le seul commit que `main` a en plus
est `25bd0f5` (« maj »), qui **ne touche que `.DS_Store`** (0 insertion, 0
suppression). Le merge du chantier 1 sera donc trivial, sans conflit réel
possible sur le code.

Diff `main...origin/feat/cepidc-integration` : 24 fichiers, +139 446 / −8 826.

**Code de production** (5 fichiers) :

| Fichier | Nature |
|---------|--------|
| `src/recode_icd/loaders/external/cepidc.py` | **nouveau**, 116 lignes |
| `src/recode_icd/merge_external.py` | +66 lignes |
| `src/recode_icd/cli/build.py` | +24 lignes (option `--cepidc-csv`) |
| `src/recode_icd/cards.py` | +23 lignes (section Formulations) |
| `src/recode_icd/loaders/external/{__init__,_constants}.py` | export + constante source |
| `src/recode_icd/exporters/flat_csv.py` | +1 ligne (libellé CSV) |

**Tests** (5 fichiers) : `tests/unit/loaders/external/test_cepidc.py`
(nouveau, 132 lignes), `tests/integration/{conftest,test_external_merge}.py`,
`tests/regression/test_external_sources_witnesses.py`, `tests/unit/test_flat_csv.py`.

**Artefacts régénérés** : le CSV maître (+121 127 lignes),
`external_to_add.parquet` (1,4 → 3,3 Mo), les deux `_index.csv` des
bibliothèques de fiches, et 5 rapports.

**Conformité aux conventions CLAUDE.md — vérifiée** : la branche ajoute bien la
valeur d'enum **et** son libellé CSV aux deux endroits requis :

```diff
# src/recode_icd/loaders/external/_constants.py
+CEPIDC_SOURCE = "CEPIDC_2015"
 EXTERNAL_SOURCES = frozenset({"ORPHANET", INDEX_CIM10_SOURCE, CEPIDC_SOURCE, ...})

# src/recode_icd/exporters/flat_csv.py
+    "CEPIDC_2015": "CepiDc_2015",
```

> **Réserve mineure à trancher au chantier 1** : le libellé CSV retenu est
> `CepiDc_2015`, avec underscore et millésime, là où toutes les autres sources
> utilisent un libellé français lisible sans underscore (`AP-HP Dermatologie`,
> `CIM-10 index`, `CIM-10 frères`). C'est un choix assumé côté branche, mais il
> rompt la convention typographique du mapping. À confirmer ou renommer avant
> merge — un renommage après coup invaliderait les artefacts régénérés.

---

## 4. Ce qui existe sur `main`

### `src/recode_icd/cards.py` — **présent sur `main`**

Le module est versionné (commits `c97ad52` et `c59057c`). Les deux commandes
CLI associées existent : `recode-icd cards build` et
`recode-icd cards build-categories`. **Il n'est pas documenté dans la section
« Structure du projet » du CLAUDE.md** — écart à corriger au chantier 3, comme
anticipé.

### Loaders externes — **présents sur `main`, sauf CepiDc**

`aphp_hector.py`, `index_cim10.py`, `orphanet.py`, plus `_constants.py` et
`_schemas.py`. **`cepidc.py` est absent de `main`** et n'existe que sur la
branche.

### Pipeline de génération de synonymes LLM — **présent sur `main`, mais notebooks seuls**

C'est le point le plus important de cet audit, et le résultat est plus
favorable qu'attendu : le chantier LLM **est versionné sur `main`** (commit
`2edf6c5`), et comme ce commit est un ancêtre commun, les deux branches en
contiennent des copies **strictement identiques**.

| Élément | Statut |
|---------|--------|
| `scripts/explore/2026-06-07_test_generation_synonymes.ipynb` (phase 1, 58 Ko, 13 cellules) | **versionné sur `main`** |
| `scripts/explore/2026-06-07_phase2_generation_synonymes.ipynb` (phase 2, 41 Ko, 14 cellules) | **versionné sur `main`** |
| Prompts (`SYSTEM_PROMPT`, `build_user_prompt()`) | **versionnés**, mais en littéraux inline **dupliqués entre les deux notebooks** |
| `config/secrets.yaml.example` | versionné |
| Extra `llm` dans `pyproject.toml` (`mistralai>=1.0`, `pyyaml>=6.0`) | versionné, `mistralai` 2.4.9 dans `uv.lock` |
| Script `.py` de pilotage batch autonome | **inexistant** — aucun `.py` du dépôt ne mentionne Mistral |
| Fichier de prompt séparé | **inexistant** |
| Doc de session du chantier LLM | **inexistante** — commité sans note de session |

**État d'exécution des notebooks** :

- **Phase 1 : exécutée**, sorties conservées (compteurs 12→22). On y lit les
  résultats réels : 20 formulations pour `A18.1` en 4,3 s (2 442 tokens
  entrée / 204 sortie), puis les 3 codes témoins à 20 formulations chacun,
  coût ~0,0175 €. **Mais la cellule 12, celle qui écrit le JSONL, n'a jamais
  été exécutée** (`execution_count: None`). Les sorties révèlent par ailleurs
  que le notebook a tourné depuis un **autre worktree** :
  `/Users/remi/Documents/recode-icd-merge/recode-icd`.
- **Phase 2 : jamais exécutée dans cette copie** — les 14 cellules ont
  `execution_count: None` et zéro sortie.

**Paramètres du dispositif, lisibles dans la phase 2** : `MODEL =
"mistral-large-latest"`, `TEMPERATURE = 0.5`, `MAX_TOKENS = 1500`, `SEED = 42`,
`BATCH_SIZE = 5000` (→ 4 batches sur 15 978 codes), `N_TARGET = 20`,
`MAX_CEPIDC_EXAMPLES = 5`, `POLL_INTERVAL_S = 30`, `BATCH_TIMEOUT_HOURS = 24`,
`response_format={"type": "json_object"}`. La reprise sur interruption est
gérée (`run_batch()` saute un batch dont le fichier de résultats existe déjà).

**Deux problèmes latents détectés dans les notebooks** (à traiter au chantier 2,
non corrigés ici) :

1. **Import cassé.** Les deux notebooks font `from mistralai.client import
   Mistral`, or `uv.lock` épingle **mistralai 2.4.9**, où l'import public est
   `from mistralai import Mistral` — le module `mistralai.client` appartenait au
   SDK 0.x. Le notebook échouera dès la cellule d'imports sur un
   `uv sync --extra llm` frais. L'extra n'est d'ailleurs pas installé
   actuellement (pas de `mistralai` dans `.venv`).
2. **Violation de convention CLAUDE.md.** La consigne « tout notebook de
   `scripts/explore/` doit commencer par `load_exploration_context()` » n'est
   respectée par aucun des deux : ils réimplémentent un `_find_project_root()`
   local et relisent le CSV CepiDc directement en polars.

Enfin, `arXiv/legacy_v1/generation_usable_icd_index_entries.ipynb` contient le
précurseur historique de l'approche batch (avec un `api_key = "xxxx"` en dur et
`os.environ["MISTRAL_API_KEY"]`) — sans rapport avec le chantier courant, mais
utile comme référence.

---

## 5. État des données

**L'arbre de travail est parfaitement propre** : `git status --porcelain`
ne renvoie rien, aucun fichier non suivi. Tout ce qui est sur le disque est
committé.

### Présent et committé

| Emplacement | Contenu |
|-------------|---------|
| `data/` | 114 fichiers suivis, **toutes les sources primaires présentes** : `CIM_OFS_SW_2006/` (DAGSTAR, INCLUDE, EXCLUDE, DESCR…), `CIM_ANS_2026/dat/terminologie-cim-10-2025-01-01.rdf`, `CIM_APHP_2019/Dictionnaire_Hector_MAJ062019.xlsx`, `Orphanet_Nomenclature_Pack_FR_2025/`, **`CIM_CEPIDC_2015/CepiDc_Dictionnaire2015.csv`** |
| `referentials/processed/` | 12 artefacts committés, dont le CSV maître (40 Mo), `merged_codes`, `owl_codes`, `ofs_codes`, `propagated_notes`, `sibling_exclusions`, `dagger_asterisk` |
| `referentials/curation/` | `dagger_curation.csv` |
| `reports/` | 13 rapports committés |
| `outputs/*/_index.csv` | inventaires des deux bibliothèques de fiches |

**Conséquence pratique importante** : le fichier source CepiDc étant déjà dans
le dépôt, **le chantier 1 pourra faire son build complet sans transfert de
données préalable**. Le point 4 du brief du chantier 1 (« si les données ne
sont pas disponibles, arrête-toi là ») ne devrait pas se déclencher.

### CSV maître — état de référence avant CepiDc

`referentials/processed/inclusions_exclusions_synonymes.csv` : **199 970
lignes**, 9 colonnes, 14 sources.

| Source | Lignes |
|--------|--------|
| CIM-10 | 74 105 |
| ANS | 62 365 |
| CIM-10 index | 36 627 |
| ORPHANET | 17 989 |
| CIM-10 frères | 5 031 |
| … AP-HP (9 feuilles) | de 45 (SRLF) à 263 (Endocrinologie) |

Cohérent avec l'attendu du chantier 1 : 199 970 + 121 127 = **321 097 lignes**
après merge CepiDc, ce qui correspond au « ~321 000 » annoncé.

Couverture actuelle de la section Formulations, relevée dans
[docs/cards_library_stats.md](../cards_library_stats.md) : **7 523 fiches,
47,1 %** — c'est bien la valeur de départ des 47 % → 54 % attendus.

### Gitignoré et absent du disque

| Chemin | Régénération |
|--------|--------------|
| `outputs/cards_library/*.md` (0/15 978 fiches) | `uv run recode-icd cards build` (~1,5 min) |
| `outputs/cards_library_categories/*.md` (0/2 054 fiches) | `uv run recode-icd cards build-categories` (~30 s) |
| `outputs/llm_synonymes/` (batches + `synonymes_consolide.jsonl` + `cepidc_examples_used.json`) | **~50 € et 4 à 96 h d'API batch** — à rapatrier, pas à régénérer |
| `outputs/llm_synonymes_test.jsonl` | phase 1, cellule 12 (~0,02 €) |
| `config/secrets.yaml` | à recréer depuis `config/secrets.yaml.example` |

### Commandes de build disponibles

Les deux groupes CLI couvrent l'intégralité du pipeline :

```bash
uv run recode-icd build owl              # owl_codes + owl_dagger_asterisk depuis le RDF ANS
uv run recode-icd build ofs              # ofs_codes + ofs_dagger_asterisk depuis OFS 2006
uv run recode-icd build merged           # fusion selon la politique CLAUDE.md
uv run recode-icd build propagated       # propagation chapitre/bloc/catégorie → code
uv run recode-icd build siblings         # exclusions frères synthétisées (.8)
uv run recode-icd build dagger-asterisk  # table DAGSTAR enrichie + curation
uv run recode-icd build external         # ORPHANET + Index + AP-HP → external_to_add + 3 rapports
uv run recode-icd build flat-csv         # CSV maître 9 colonnes
uv run recode-icd build stats            # reports/csv_stats.md

uv run recode-icd cards build            # bibliothèque de fiches (15 978)
uv run recode-icd cards build-categories # fiches catégories 3-car (2 054)
```

---

## 6. Éléments manquants à récupérer depuis les anciens PC

Checklist opérationnelle. La liste est courte — le gros du travail est déjà
dans le dépôt.

### Bloquant pour le chantier 2

- [ ] **`outputs/llm_synonymes/synonymes_consolide.jsonl`** — sortie consolidée
      de la campagne batch phase 2. Irremplaçable à coût raisonnable (~50 €
      et jusqu'à 96 h de retraitement). **Priorité 1.**
- [ ] **`outputs/llm_synonymes/cepidc_examples_used.json`** — carte des exemples
      few-shot effectivement tirés par code. Nécessaire pour la traçabilité de
      provenance et pour rejouer la génération à l'identique.
- [ ] **`outputs/llm_synonymes/batches/batch_<n>_{requests,results}.jsonl`** —
      batches intermédiaires (4 batches : 5000 + 5000 + 5000 + 978). Utiles
      pour l'audit et la reprise partielle ; moins critiques que le consolidé.
- [ ] **Version réellement exécutée des notebooks phase 1 / phase 2.** Le brief
      indique que « la source de vérité des prompts est un notebook de phase 1
      modifié manuellement ». Les copies versionnées ici ont une phase 2
      **jamais exécutée** et une phase 1 dont la cellule d'écriture n'a pas
      tourné — et dont les sorties pointent vers le worktree
      `~/Documents/recode-icd-merge/recode-icd`. **Il faut récupérer les
      notebooks de ce worktree et les differ contre ceux du dépôt** avant de
      considérer les prompts versionnés comme fiables.
- [ ] `outputs/llm_synonymes_test.jsonl` (facultatif — régénérable pour ~0,02 €).

### Bloquant pour toute exécution LLM

- [ ] **`config/secrets.yaml`** avec la clé API Mistral. À recréer localement
      depuis `config/secrets.yaml.example` (ne jamais commiter). Puis
      `uv sync --extra llm`.

### Non bloquant — régénérable localement

- [ ] Fiches `.md` des deux bibliothèques : régénérables en ~2 min au total via
      les commandes CLI ci-dessus. Aucun transfert nécessaire.

### Rien à récupérer côté données sources ni code

Toutes les sources primaires (OFS, ANS/RDF, HECTOR, ORPHANET, **CepiDc**) et
tous les artefacts `referentials/processed/` sont committés et présents. Le
code du chantier CepiDc est intégralement sur `origin/feat/cepidc-integration`,
et le code du chantier LLM (notebooks) est sur `main`.

---

## 7. Points d'attention pour la suite

1. **Chantier 1 débloqué sans prérequis.** Merge trivial (le seul commit
   divergent de `main` est un `.DS_Store`), données CepiDc présentes, build
   complet possible immédiatement. Base de comparaison des tests : 245 unit /
   68 regression / 21 integration. Les compteurs annoncés dans le brief
   (247 / 84 / 26) impliquent +2 unit, +16 regression, +5 integration — écart à
   confirmer après merge. Seule question ouverte : le libellé CSV
   `CepiDc_2015` (cf. §3).
2. **Chantier 2 partiellement débloqué.** L'inventaire est fait et le code est
   versionné, contrairement à ce que le brief supposait. Ce qui manque est
   uniquement les *sorties* et la version exécutée des notebooks. La question
   de politique (nouvelle source `LLM_MISTRAL` dans le CSV maître, ou artefact
   séparé consommé par les fiches) peut être instruite dès maintenant, sans
   attendre le transfert.
3. **Dette technique identifiée, non traitée** : import `mistralai.client`
   incompatible avec le SDK 2.x épinglé ; prompts dupliqués entre les deux
   notebooks ; non-respect de la convention `load_exploration_context()` ;
   5 erreurs ruff dans `tests/`.
4. **Question de fond à arbitrer** : `U07.1` est à la fois le code témoin
   obligatoire des codes post-2006 et une victime du filtre `_leaf_codes()`.
   Tant que le backlog `inclure_codes_intermediaires` reste différé, la
   couverture de régression post-2006 est en pratique vide.

---

## 8. Diffs de cette session

Aucune modification de code, conformément au brief. Seul ajout :
`docs/sessions/2026-08-09_etat_des_lieux_reprise.md` (ce document).

Effet de bord assumé et attendu : `uv sync` a créé/actualisé `.venv/`
(gitignoré) et `uv run pre-commit install` a écrit `.git/hooks/pre-commit`
(hors index).
