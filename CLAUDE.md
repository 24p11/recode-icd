# recode-icd

> Toolkit Python pour exploiter les référentiels électroniques de la CIM-10
> (formats OFS suisse et OWL/ANS) en vue d'enrichir des prompts destinés à
> la génération de textes médicaux annotés par LLM.

## Consignes de session Claude Code

À chaque session non triviale :
1. Lire les documents de référence pertinents avant d'agir
   (docs/source_mapping.md, docs/sources/, etc.)
2. Pour les changements de design : proposer un plan détaillé et
   attendre validation avant d'implémenter.
3. Lors d'un signalement d'erreur par l'utilisateur, ne pas proposer
   de correction avant d'avoir : (a) reformulé l'observation, (b)
   localisé le code concerné, (c) tracé l'origine des données
   observées, (d) formulé des hypothèses de cause avec moyens de
   vérification. La correction vient seulement après validation
   explicite de la cause.
4. Avant de conclure une session : produire un récap des diffs
   significatifs (file by file, avec explication).
5. À la fin d'une grosse session : produire un récap dans
   docs/sessions/YYYY-MM-DD_<sujet>.md.

## Objectifs métier

1. **Fichier maître `inclusions_exclusions_synonymes.csv`** (9 colonnes) :
   `code`, `libelle`, `type` ∈ {inclusion, exclusion, synonyme},
   `source`, `texte`, `dagger_code`, `asterisk_code`, `redundancy_level`, `is_redundant_dagger`.
   Regroupe toutes les informations textuelles associées à un code
   CIM-10, avec propagation des notes des niveaux supérieurs (bloc,
   catégorie) vers les codes feuilles.
2. **Table des associations dague (†) / astérisque (*)** comme livrable
   séparé (vue plus structurée que les colonnes du CSV principal,
   préserve les 6 valeurs du champ `daget` F/G/H/S/T/U).
3. **API stable** pour enrichir des prompts CIM-10 (réutilisable par
   recode-scenario notamment).

## Stack technique

- Python ≥ 3.13 (aligné sur `smt2parquet`)
- Gestion des paquets : **uv**
- DataFrames : **polars**
- Stockage intermédiaire : **Parquet** (via pyarrow)
- Modèles de données : **pydantic v2**
- Validation : **pandera**
- Tests : **pytest** avec marqueurs `unit`, `regression`, `integration`
- Lint/format : **ruff**
- Type-check : **mypy**
- CLI : **typer**

## Commandes courantes

```bash
uv sync                                  # installer
uv run pytest                            # tous les tests
uv run pytest -m unit                    # unitaires seuls
uv run pytest -m regression              # régression seule
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/recode_icd
uv run pre-commit install                # hooks git
```

## Structure du projet

```
src/recode_icd/
├── loaders/
│   ├── ofs.py             # base relationnelle OFS suisse (2006)
│   ├── owl.py             # surcharge locale de smt2parquet (CIM-10 ANS)
│   └── external/          # ORPHANET, thésaurus AP-HP, etc.
├── model.py               # entités pydantic canoniques
├── merge.py               # fusion OFS ⊕ OWL avec politique de résolution
├── propagation.py         # propagation bloc/catégorie → code (nested set)
├── relations/
│   ├── dagger_asterisk.py # table d'associations dague/astérisque (objectif 2)
│   └── sibling_exclusions.py
├── exporters/
│   └── flat_csv.py        # le fichier 7 colonnes
├── registry.py            # ReferentialRegistry (inspiré de recode-scenario)
└── cli/                   # CLI typer
referentials/
├── raw/                   # fichiers sources (gitignored si volumineux)
└── processed/             # Parquets dérivés (committés)
tests/
├── unit/
├── regression/            # golden-files sur 10 codes témoins
├── integration/
└── fixtures/
scripts/
├── prepare_referentials.py
└── explore/               # notebooks d'exploration ad-hoc
docs/
├── owl_extension.md       # quelles propriétés on ajoute à smt2parquet
├── source_mapping.md      # mapping canonique OFS ↔ OWL/ANS (RÉFÉRENCE ABSOLUE)
├── dagger_subordinate_pairs.yaml  # couples dague/astérisque marqués subordinate
├── sources/
│   └── ofs_schema.md      # schéma détaillé de la base OFS
└── architecture.md
```


## Dépendances externes clés

- **Documents de référence obligatoires.** Avant toute modification du
  code de fusion, des loaders ou de l'exporter, Claude Code DOIT lire :
  - `docs/source_mapping.md` : mapping canonique OFS ↔ OWL/ANS.
    Toute décision sur la sémantique d'un champ se prend selon ce document.
  - `docs/sources/ofs_schema.md` : schéma détaillé de la base OFS.

  Si une situation rencontrée n'est pas couverte par ces documents,
  demander à l'utilisateur avant d'inventer un comportement.

- **`smt2parquet`** (https://github.com/dridk/smt2parquet) — utilisé en
  module pour convertir RDF→Parquet via le modèle *nested set*. **Surcharge
  par wrapper local** dans `loaders/owl.py` : on importe
  `smt2parquet.core` (`load_graph`, `dataframe_from_sparql`,
  `build_nested_set`, `write_parquet_with_metadata`) tel quel et on redéfinit
  les requêtes SPARQL `ATTRS_QUERY` / `EDGES_QUERY` localement pour récupérer
  les propriétés non extraites en amont par `smt2parquet/cim10.py` :
  `xkos:exclusionNote`, `skos:definition`, `skos:scopeNote`, `skos:note`,
  `atih-cim10:hasCausality`, `atih-cim10:hasManifestation`,
  `atih-cim10:exclusion`. Détails et requêtes dans `docs/owl_extension.md`.

  **Attention** : `smt2parquet/cim10.py` déduplique les synonymes via
  `.unique()` polars (égalité stricte de chaîne), ce qui laisse passer
  des doublons "presque identiques" (casse, ponctuation, ligature æ).
  La déduplication tolérante finale est de la responsabilité de
  `merge.py` / `flat_csv.py`. Détails dans `docs/source_mapping.md`
  section "Déduplication des synonymes".

- Référence d'inspiration architecturale : **`Stef500/recode-scenario`**
  pour le pattern `ReferentialRegistry` (accès paresseux, validé Pandera,
  caché aux Parquets et YAML).

## Modèle de données canonique

Tout passe par 4 entités pydantic :

- **`Code`** : code CIM-10 avec hiérarchie (chapitre / bloc / catégorie /
  sous-catégorie), bornes `left`/`right` nested set, et le `path`.
- **`Note`** : avec `type: NoteType` ∈ {INCLUSION, EXCLUSION,
  INDIRECT_EXCLUSION, COMMENT, CODING_HINT}, `source: NoteSource` ∈
  {OFS, OWL_ANS, SYNTHESIZED_SIBLING, ...}, et `inherited_from: Code |
  None` (renseigné si la note vient d'un bloc ou d'une catégorie parente
  par propagation).
- **`Synonym`** : libellé alternatif avec `source: SynonymSource`
  ∈ {OWL_ANS, INDEX_CIM10_VOL3, ORPHANET, AP_HP, ...}.
- **`DaggerAsteriskPair`** : couple `(dagger_code, asterisk_code)` avec
  son contexte d'association (`daget` ∈ {F, G, H, S, T, U} et flag
  `plus`).

Toute donnée exportée porte une colonne `source` — **jamais d'agrégation
silencieuse**.

### Cas particulier des notes synthétisées (`SYNTHESIZED_SIBLING`)

Pour les notes générées automatiquement (exclusions des codes frères
.8) :
- `source = SYNTHESIZED_SIBLING` (libellé CSV : `CIM-10 frères`)
- `inherited_from = None` (la note est conceptuellement attachée
  directement au code .8, pas héritée d'un parent)
- Une colonne dédiée dans l'export final indique le code frère cible

C'est différent de la propagation hiérarchique : la note synthétisée
naît au niveau du code .8 lui-même, ce n'est pas un héritage d'un
bloc ou d'une catégorie.

## Domain pitfalls — à NE PAS confondre

1. **Inclusion ≠ synonyme**. Une inclusion est une affection *rangée dans*
   la catégorie ; un synonyme est un autre nom *pour la même* affection.
   OFS distingue les deux ; OWL/ANS souvent pas (les deux se retrouvent
   dans `xkos:inclusionNote` indifféremment). C'est précisément ce que
   notre fusion doit reconstruire en s'appuyant sur OFS.
2. **Note d'exclusion ≠ négation**. Une exclusion dit "cette affection
   appartient à un AUTRE code, voir XX.Y", pas "cette affection n'existe
   pas". Toujours conserver le code de redirection si présent.
3. **Propagation bloc → code obligatoire**. Les notes au niveau bloc
   s'appliquent à TOUS les codes du bloc, sauf override explicite plus bas.
   Le champ `inherited_from` doit être renseigné pour traçabilité.
4. **Dague (†) / astérisque (*)**. Le code dague est primaire (maladie
   initiale, étiologie), l'astérisque est la manifestation. Ne **JAMAIS**
   inverser. Voir section "Couples dague/astérisque" pour la politique
   de représentation dans le CSV.
5. **CIM-10 OMS vs CIM-10 FR-PMSI**. La FR-PMSI a des extensions ATIH
   absentes de l'OMS. La version cible doit être explicite dans les
   métadonnées Parquet et dans les exports CSV.
6. **Codes .8 vs .9** : `.8` = "autres" (information ajoutée), `.9` =
   "sans précision" (équivalent au titre de catégorie, pas d'information
   ajoutée). Pour C00-C75, `.8` a une sémantique spécifique (lésion à
   localisations contiguës).
7. **Priorité des chapitres "groupes spéciaux"**. Chapitres I, II, XV–XXI
   ont la priorité sur les chapitres "par appareil" en cas de doute de
   classement. Ne jamais "régulariser" en mettant un code par appareil
   alors qu'un groupe spécial s'applique.
8. **Atomicité OFS vs blocs ANS** (limitation connue). L'ANS livre les
   notes multi-éléments comme un seul bloc textuel avec puces, là où
   OFS atomise. Pour les codes pré-2006, OFS prime et fournit
   l'atomisation. Pour les codes post-2006, on accepte les blocs ANS
   tels quels — pas de parsing automatique. Détails dans
   `docs/source_mapping.md` section "Limitation connue : atomisation
   ANS".
9. **Conventions ANS non standard**. ANS utilise des crochets
   `[D22.-]` pour les codes redirigés alors que la convention OMS
   utilise des parenthèses `(D22.-)`. **Ces crochets ne sont pas un
   choix typographique arbitraire** : ils correspondent sémantiquement
   aux associations dague/astérisque. ANS utilise aussi `nævus` avec
   ligature æ. Ces artefacts restent dans le CSV final pour les codes
   post-2006.
10. **Déduplication stricte vs tolérante**. Le `.unique()` de polars
    (utilisé en amont par smt2parquet) ne suffit pas pour les
    synonymes : il laisse passer les variantes de casse, ponctuation,
    ligature. La déduplication finale doit utiliser la normalisation
    tolérante (NFKD + lowercase + ponctuation + whitespace).

## Politique de fusion OFS ⊕ OWL

Politique par champ, à respecter :

| Champ                    | Source primaire    | Fallback   |
|--------------------------|--------------------|------------|
| `libelle` du code        | OWL_ANS            | OFS        |
| Existence du code        | OWL_ANS            | —          |
| Inclusions typées        | OFS                | OWL_ANS    |
| Exclusions typées        | OFS                | OWL_ANS    |
| Notes éditoriales        | OFS                | OWL_ANS    |
| Associations †/*         | OFS + audit ANS    | OWL_ANS    |
| Synonymes                | OFS                | OWL_ANS    |

Tout désaccord OFS ↔ OWL sur le libellé doit être loggué dans
`reports/merge_conflicts.csv` à chaque build.

Pour les associations †/*, OFS (`DAGSTAR.txt`, 1352 entrées) est la
source primaire pour le CSV de sortie. OWL/ANS
(`atih-cim10:hasCausality` + `atih-cim10:hasManifestation`, 1317
relations dans `terminologie-cim-10-2025-01-01.rdf`) est chargé en
parallèle pour permettre un **audit de cohérence**. Tout désaccord
est loggué dans `reports/dagger_asterisk_conflicts.csv`.

Pour les notes typées, le merger doit produire un champ `match_type`
dans `note_merges.csv` qui distingue : `exact_match`,
`atomic_regroupement`, `real_divergence`, `ofs_only`, `ans_only`.
Détails dans `docs/source_mapping.md` section "Règle de réconciliation".

## Couples dague/astérisque

Politique synthétique (détails dans `docs/source_mapping.md` section
"Couples dague/astérisque : politique de représentation") :


**Filtrage des synonymes redondants** : règle en cours de validation
empirique. Le script `scripts/explore/<date>_dagger_asterisk_dedup.py`
fournit les données nécessaires à la décision.

## Notes synthétisées (codes "autres" en .8)

En plus des notes extraites des sources, on **synthétise** des notes
d'exclusion pour les codes en `.8` ("Autres ...") :

- **Règle** : pour tout code `XYZ.8`, on ajoute une note d'exclusion qui
  liste les codes frères `XYZ.0`, `XYZ.1`, ..., `XYZ.7` (les codes de la
  même catégorie à 3 caractères qui ne sont ni `.8` ni `.9`), avec leurs
  libellés.
- **Pourquoi** : aider le LLM à comprendre que `XYZ.8` couvre les affections
  *résiduelles* — celles qui n'ont pas leur propre sous-catégorie spécifique.
  Sans cette information, le LLM risque de générer un compte-rendu décrivant
  une affection qui aurait dû être codée sous `XYZ.0` ou autre, ce qui
  corrompt le dataset annoté.
- **NoteSource** : `SYNTHESIZED_SIBLING` (jamais confondre avec une note
  réelle). **Libellé dans le CSV exporté** : `CIM-10 frères` (mapping
  Python ↔ CSV géré par `exporters/flat_csv.py`).
- **NoteType** : `EXCLUSION`.
- **`inherited_from`** : `None` (la note est attachée directement au
  code .8, pas héritée).
- **Granularité d'export** : **une ligne CSV par code frère**, pas une
  ligne agrégée. Le code frère et son libellé apparaissent dans la
  colonne `texte` au format `<libellé du frère> (<code du frère>)`.
  Symétrique avec l'export des exclusions OFS.
- **Exclusion explicite** : les codes `.9` ne sont JAMAIS inclus comme
  frères. Par définition `.9` n'apporte pas d'information ajoutée
  (équivalent au titre catégorie), donc l'exclure n'a pas de sens.
  Règle : siblings = codes du même parent catégorie, sauf `.8` ET `.9`.

Cas limites à gérer explicitement dans `relations/sibling_exclusions.py` :

1. Catégorie qui n'a que `.8` et `.9` (rien à exclure → pas de note
   synthétisée).
2. Catégorie où `.8` est absent (rien à faire).
3. Catégories à structure non-standard (par exemple les chapitres XIX/XX
   avec leurs caractères additionnels). On se restreint pour l'instant aux
   catégories à structure `.0-.9`.
4. **Cas particulier des C00-C75** : la sous-catégorie `.8` a une sémantique
   différente ("lésion à localisations contiguës"). Pour ces codes, **ne
   pas synthétiser** d'exclusion frère — on log un skip dans le rapport.

## Codes post-2006 (présents en ANS, absents d'OFS)

Pour les ~2300 codes ajoutés à la classification après le gel OFS
(novembre 2006) :

- Le code est créé dans le merge avec `source=ANS`.
- Toutes ses notes (inclusions, exclusions, synonymes) ont
  `source=ANS`.
- **Les notes multi-éléments restent sous forme de blocs textuels**
  (pas de parsing automatique, cf domain pitfall #8).
- Les artefacts ANS (crochets, ligatures, puces) sont préservés
  tels quels dans le CSV.
- Pas d'association dague/astérisque sauf si présente dans
  `atih-cim10:hasCausality` ou `atih-cim10:hasManifestation`.

Ces codes sont loggués dans `reports/post_2006_codes.csv` pour audit.

**Code témoin de référence** : `U07.1` (COVID-19), ajouté en 2020.

## Mapping sources internes ↔ libellés CSV

Le modèle Python utilise des enums UPPERCASE pour les sources. Le CSV
exporté utilise des libellés français lisibles. Le mapping vit dans
`exporters/flat_csv.py` :

| `NoteSource` (Python) | `source` (CSV)   |
|-----------------------|------------------|
| `OFS`                 | `CIM-10`         |
| `OWL_ANS`             | `ANS`            |
| `INDEX_CIM10_VOL3`    | `CIM-10 index`   |
| `SYNTHESIZED_SIBLING` | `CIM-10 frères`  |
| `ORPHANET`            | `ORPHANET`       |
| `AP_HP`               | `AP-HP`          |

Toute nouvelle source ajoutée passe par les DEUX endroits : l'enum
Python et le mapping d'export. Test de régression vérifie qu'il n'y a
pas d'enum sans libellé CSV correspondant.

## Conventions de code

- Toutes les fonctions de fusion et de propagation sont **pures** et
  **déterministes** (mêmes entrées → byte-equivalent en sortie).
- Les loaders renvoient des DataFrames polars **validés par pandera**.
- La source de toute information est tracée par une colonne `source` ;
  jamais d'agrégation silencieuse.
- Les tests de régression utilisent une dizaine de codes témoins fixés
  dans `tests/fixtures/sample_codes.yaml`. Liste obligatoire :
  - Un code avec dague/astérisque (par ex `A18.1`)
  - Un code avec exclusions multiples (ex : `I78.1` et ses 11 nævus)
  - Un code en chapitre XX
  - Un code en chapitre XXI
  - Un code dans C00-C75 avec sous-catégorie `.8` (par ex `C50.8`)
  - **`U07.1`** (COVID-19) comme code post-2006
  - Un couple typique pour tester `redundancy_level=subordinate`
    (par ex `A17.8` / `G05.0`)

## Workflow Claude Code recommandé

- Avant toute modification non-triviale : `/plan` puis validation du plan
  par moi (l'utilisateur) avant implémentation.
- Lancer `uv run pytest -m unit` après chaque modification logique
  significative.
- Pour les explorations OWL/OFS, créer un script ou notebook dans
  `scripts/explore/` plutôt que de polluer `src/`.
- **Tout notebook ou script d'exploration dans `scripts/explore/` doit
  commencer par** :

  ```python
  from recode_icd.utils.loaders_dev import load_exploration_context
  ctx = load_exploration_context()
  ```

  Ne PAS dupliquer la logique de chargement des tables OFS, du Parquet
  ANS, des artefacts du pipeline ou des rapports. Si une source utile
  manque dans `ExplorationContext`, étendre `loaders_dev.py` plutôt que
  de coder un loader ad-hoc dans le notebook.

  `loaders_dev` est **dev only** — ne JAMAIS l'importer depuis
  `src/recode_icd/loaders/`, `merge.py`, `propagation.py`,
  `exporters/`, ou `cli/`.

  `loaders_dev.py` ne contient QUE des fonctions de chargement, jamais
  de calcul ou de transformation métier. Toute logique métier reste
  dans `src/recode_icd/`.

- Les notes d'inclusion/exclusion contiennent souvent des libellés
  médicaux exotiques (latinismes, abréviations) — **ne jamais "normaliser"
  silencieusement** un texte, toujours préserver le texte source.
