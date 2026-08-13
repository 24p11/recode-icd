# Chantier `chapter_policy` — implémentation de R1/R2/R3 v5 dans `src/`

## Context

Les trois règles de composition de la section « Formulations cliniques
alternatives » sont instruites, calibrées et **figées en v5**. Elles vivent en
prototype dans le notebook ; ce chantier les porte dans `src/` sous
configuration YAML. C'est le premier chantier autorisé à modifier `cards.py`.

**Finalité de R3, qui départage toute ambiguïté future** — à inscrire en tête
de la section R3 du document de trace et du CLAUDE.md :

> La section Formulations sert à **(1) refléter le langage réellement employé
> par les médecins dans les CRH** et **(2) ne jamais élargir ni brouiller le
> périmètre du code**. Quand le comportement mesuré et la consigne écrite
> divergent, c'est cette finalité qui fait foi — et le bon réflexe reste de
> poser la question.

**Invariant absolu** : les trois règles s'appliquent à l'**assemblage des
fiches**. Le CSV maître, les Parquets et la colonne `texte` ne sont jamais
modifiés. Garantie affirmée par un test.

**Décisions actées** : YAML dans `referentials/curation/` ; plafond **par
famille** aux deux niveaux (10 feuilles, 20 catégories) ; exclusion (jamais
amputation) pour abréviations et méta-termes ; seuil de dominance **2×**.

---

## Résultat de la v5 — la règle d'arrêt tient

| Étiquette | v4 (100) | **v5 (96)** | Seuil |
|---|---|---|---|
| `correcte` | 85 % | **87,5 %** | — |
| `degradee` | 15 % | **12,5 %** | ≤ 15 % ✅ |
| `fautive` | 0 | **0** | 0 ✅ |

Aucun nouveau tirage : 4 entrées du tirage `4242` sortent du périmètre, 1
change de forme. Les 12 dégradées restantes relèvent toujours du joint non
inséré faute d'attestation — limite de **couverture de données**, non
corrigeable par motif. **R3 est figée en v5.**

**Périmètre final** : sur 36 627 entrées d'Index, **11 638 retenues**
(10 922 réécrites + 716 conservées), **24 989 écartées**.

Motifs d'exclusion : 3+ segments 12 452 · renvois 9 495 · abréviation ou
méta-terme 2 129 (dont **610 marginales**, les autres déjà exclues par
ailleurs) · tête douteuse 644 · **zone grise 209** · **énumération 60**.

### Le seuil 2× est tranché par les données

| Seuil | Zone grise (mots) | Zone grise (entrées) | Périmètre |
|---|---|---|---|
| **2×** | 416 / 1 442 (28,8 %) | **209** | **11 638** |
| 3× | 670 / 1 442 (46,5 %) | 449 | 11 398 |

À 3×, « langue » (ratio 2,61) bascule en zone grise et **« hémorragie de la
langue » — normalisation validée en v4 — deviendrait une exclusion.** C'est
l'argument décisif pour 2×.

Exemples de zone grise à 2× (exclus, à raison) : « palais » A=164/J=102,
« foetus » A=556/J=572, « bacille ducrey » A=2/J=2, « mésentère » A=2/J=3.

---

## Trois lexiques, trois périmètres — le pitfall central

Le garde-fou de dominance ajoute un **troisième** lexique, avec un périmètre
encore différent. Chaque exclusion a une justification linguistique propre ;
les fusionner « par simplification » casse une garantie différente à chaque
fois. **C'est le pitfall n°1 à documenter.**

| Lexique | Périmètre | Justification |
|---|---|---|
| **Rections** (`du X`, `de la X`) | **Index inclus** | La syntaxe interne des entrées est du français naturel (« … adénofibromateuse **de la** prostate ») : elle témoigne du genre. |
| **Casse** (mots vus en minuscule) | **Index exclu** | L'Index capitalise **toute tête d'entrée** par convention : il ne peut pas dire si un mot est un nom commun. |
| **Juxtaposition `J`** (dominance adjectivale) | **CepiDc exclu**, virgules et parenthèses = **frontières dures** | CepiDc est **télégraphique** : il supprime les articles, donc tout nom y paraît adjectival. Et sans frontières, « Hypoplasie (de), cerveau » se compte lui-même en juxtaposition — **l'Index se contaminerait**. |

> Mesuré : sans exclure CepiDc, « cerveau » ressort adjectival (ratio 0,46) et
> « hypoplasie du cerveau » serait cassé. Sans frontières, même effet.
> Avec les deux corrections : cerveau 78/1, estomac 79/1, médullaire 1/72.

---

## Spécification v5 (à porter à l'identique)

**Exclusions**, dans l'ordre : renvoi (« voir ») · **abréviation d'index
(`nca`, `sai`) ou méta-terme de classification (`précisé*`, `autre*`) en tête
OU en queue de segment nettoyé — exclue, jamais amputée** · 3 segments ou
plus · **énumération de synonymes** · tête douteuse · **zone grise de
dominance**.

**Énumération de synonymes** : deux segments, tous deux d'un seul mot, sans
connecteur ni préposition traînante, préfixe commun ≥ 5 caractères **et**
≥ 50 % du plus court. Le critère « un seul mot » protège la tête nue
(« Autosome, **site fragile** » reste inversée). 60 entrées concernées.

**Garde-fou de dominance**, sur les seules familles `de`/`à` — un connecteur
littéral (« avec », « par ») ne s'accorde pas et garde la gate v4 :

- `A ≥ 2·J` → **substantif** : joint inséré (comportement v4) ;
- `J ≥ 2·A` → **adjectif** : connecteur consommé **sans** joint ;
- sinon → **exclusion**.

> Restreindre le garde-fou aux familles fléchies était nécessaire : appliqué
> aux littéraux, il cassait « varicelle **avec** pneumopathie »
> (pneumopathie A=3/J=128 → classé adjectival à tort).

`A=0 et J=0` → **juxtaposition** (variante souple, retenue) : la présence même
du connecteur atteste que le mot est un complément nominal. La variante
stricte (exclusion) coûterait 958 entrées de plus pour un gain marginal.

---

## Schéma YAML — `referentials/curation/chapter_policy.yaml`

```yaml
# Politique de composition de la section « Formulations cliniques
# alternatives ». S'applique à l'ASSEMBLAGE DES FICHES uniquement.
# Justification métier : docs/analyses/2026-08-09_qualite_sources_par_chapitre.md
#
# ⚠ RÉSOLUTION PAR REMPLACEMENT, PAS PAR FUSION.
#   bloc > chapitre > défaut ; la règle la plus spécifique REMPLACE
#   intégralement la moins spécifique. Une entrée de bloc doit REDÉCLARER
#   tout ce qu'elle veut conserver du chapitre.
version: 1

familles_sources:
  "CIM-10 index": INDEX
  "CepiDc 2015":  CEPIDC
  "ORPHANET":     ORPHANET
  "CIM-10":       OFS
  "CIM-10 frères": OFS
  "ANS":          ANS
prefixes_familles: {"AP-HP": APHP}

familles_formulations: [INDEX, APHP, CEPIDC, ORPHANET, LLM]
familles_externes:     [APHP, ORPHANET, CEPIDC, LLM]
familles_llm:          [LLM]

# R2 — deux valeurs distinctes, et c'est voulu : une fiche feuille tire
# d'un seul code, une catégorie agrège toutes ses feuilles (3 007
# formulations pour C79). Balayage 5/10/15/20/30 : 20 = dernier palier
# avant dégradation.
plafond_famille_feuilles: 10
plafond_famille_categories: 20
plafond_global_categories: 50

defaut:  {sources_externes: true,  generation_llm: true}
chapitres:
  XVIII: {sources_externes: true,  generation_llm: false}
  XIX:   {sources_externes: false, generation_llm: false}
  XX:    {sources_externes: false, generation_llm: false}
  XXI:   {sources_externes: false, generation_llm: false}
blocs:
  # Redéclare XIX à l'identique (remplacement). Existe pour documenter la
  # décision métier propre au bloc et survivre à un assouplissement de XIX.
  T36-T50: {sources_externes: false, generation_llm: false}

normalisation_index:
  active: true
  seuil_dominance: 2.0
  inconnu_est_adjectif: true          # A=0 et J=0 → juxtaposition
  tetes_nues: [syndrome, maladie, "site fragile"]
  abreviations_index: [nca, sai]
  meta_termes: [précisé, précisée, précisés, précisées, autre, autres]
  enumeration: {prefixe_min: 5, ratio_min: 0.5}
```

---

## Modules

| Fichier | Rôle |
|---|---|
| `src/recode_icd/policy.py` | Dataclasses + `load_policy(path)` (`yaml.safe_load`) + `politique_pour(chapitre, blocs)` (remplacement, du plus interne au plus large) + `famille_de`. **Premier import de `yaml` dans `src/`** — pyyaml déjà dépendance dure, `types-pyyaml` déjà en dev. |
| `src/recode_icd/hierarchie.py` | `chapitre_et_blocs(merged)` — blocs = **tous** les segments de `path` de forme `A00-B99` (le chapitre XIII en imbrique trois) ; catégorie = partie avant le point. |
| `src/recode_icd/lexicons.py` | Les **trois** lexiques, chacun avec son périmètre documenté ; `to_parquet` / `load_lexicons`. |
| `src/recode_icd/normalize_index.py` | Port v5 **à l'identique**. Fonctions **pures**, lexiques en paramètre, aucune I/O. |
| `src/recode_icd/loaders/schemas.py` | +3 `pa.DataFrameModel` (`strict=True, coerce=False`). |
| `src/recode_icd/cards.py` | Câblage R1/R2/R3 ; RNG dérivé par code ; plafond par famille. |
| `src/recode_icd/cli/{build,cards}.py` | `build lexicons` (patron `build dagger-asterisk`) ; `--policy` / `--lexicons-dir` sur les deux commandes cards. |
| `src/recode_icd/reports/cards_policy.py` | `reports/cards_policy_effect.csv`. |
| `scripts/explore/relectures/` | Export CSV des échantillons : un fichier par graine, colonnes `code, texte_source, forme_normalisee, etiquette, motif_exclusion, version_regle`. |

**Pipeline d'assemblage** (ordre load-bearing) : familles autorisées (R1) →
**normalisation Index (R3)** → dédup tolérante → plafond par famille (R2) →
plafond global (catégories) → tri final. La normalisation **avant** la dédup
est essentielle : elle crée des doublons qu'il faut absorber.

### Piège de reproductibilité à corriger au passage

`build_cards_library` partage **un seul** `random.Random(seed)` sur toute la
bibliothèque, et les `rng.sample` sont conditionnels : une fiche produite avec
`--limit 5` diffère de la même fiche en build complet. Le passage au plafond
par famille change de toute façon tous les rendus — **je dérive donc un RNG
par code** (`random.Random(f"{seed}:{code}")`), ce qui rend chaque fiche
indépendante de sa position. C'est le seul moment où ça ne coûte rien.

---

## Commits

1. `feat(policy)` — `policy.py`, `hierarchie.py`, le YAML, tests de résolution
   (dont le test dédié « remplacement, pas fusion »).
2. `feat(lexicons)` — trois lexiques, schémas, `build lexicons`, test de
   séparation des trois périmètres.
3. `feat(normalize-index)` — port v5 + tests dorés.
4. `feat(cards)` — câblage, RNG par code, options CLI.
5. `chore` — rebuild des 18 000 fiches, rapport de composition, artefacts.
6. `docs` — CLAUDE.md, migration du notebook, récap de session.

---

## Tests

- `tests/unit/test_policy.py` — résolution bloc > chapitre > défaut ; **test
  dédié au remplacement** (un bloc qui ne redéclare pas `generation_llm` ne
  l'hérite pas) ; les trois blocs imbriqués de `C50.8`.
- `tests/unit/test_lexicons.py` — **les trois périmètres testés séparément** :
  `Borrelia`/`Lipschütz` absents du lexique de casse ; les ~265 noms apportés
  par l'Index présents dans les rections ; **`cerveau` substantif** (preuve que
  CepiDc est bien exclu du comptage J) et **`médullaire` adjectival**.
- `tests/unit/test_normalize_index.py` — **~20 paires dorées** issues des
  relectures (seeds 777, 4242), dont les nouvelles : « Paralysie (de),
  médullaire » → « paralysie médullaire » ; « Syphilis (acquise) (de),
  utérus » → « syphilis de l'utérus » ; « Deutéranomalie, deutéranopie » →
  exclue ; « Hypoparathyroïdie, hypoparathyroïdisme » → exclue ; « Autosome,
  site fragile » → « site fragile Autosome » (**non** exclue par similarité) ;
  « Anomalie (de), vessie nca » → exclue ; « Oculopathie (à), syphilitique
  (tardive) nca » → exclue ; « Encéphalite (…), précisée nca » → exclue ;
  **zone grise réelle** « Kyste (de), mésentère » → exclue ; « Rectite (à),
  amibienne » → « rectite amibienne » ; « varicelle avec pneumopathie »
  (non-régression du garde-fou littéral).
- `tests/unit/test_cards_policy.py` — **contexte synthétique**
  (`ExplorationContext` est un dataclass frozen à défauts complets) avec une
  **source LLM factice**, pour vérifier que `generation_llm: false` la filtre
  sur XVIII alors qu'aucune source LLM n'existe encore.
- `tests/regression/test_chapter_policy_witnesses.py` — fiches témoins ; **test
  affirmant que le CSV n'est pas modifié** (la forme source de l'Index est
  toujours dans `csv_final_df` après un build).
- Extension du verrou existant `test_cards_formulations_sources.py` : « toute
  famille du YAML est tranchée ».
- À mettre à jour : `test_build_card_deterministic_same_seed` (RNG par code),
  les fourchettes des tests de bibliothèque, `test_build_category_card_formulations_plafonnees`.
- `test_build_cards_library_index_csv_schema` fige l'ensemble **exact** des
  9 colonnes de `_index.csv` : **je n'ajoute aucune colonne**, le rapport va
  dans `reports/`.

---

## Documentation

Nouvelle section CLAUDE.md « chapter_policy » : les trois règles, le YAML, la
résolution par remplacement, et **trois pitfalls** — (1) les trois lexiques et
leurs périmètres, (2) exclusion des fiches ≠ exclusion du pipeline de données,
(3) `U07.1`-style : la relecture de forme ne contrôle pas le périmètre.

Document de trace, mentions datées du 2026-08-13 :
- la **finalité** de R3 en tête de section ;
- l'option B actée avec ses deux raisons de fond ;
- **« la relecture de forme ne contrôle pas le périmètre — ce sont deux
  validations distinctes »**, illustrée par les deux entrées jugées correctes
  et pourtant fausses de périmètre (« oculopathie syphilitique »,
  « dystrophie cutanée ») ;
- le rendement de la règle unifiée vient de `nca` (425) et `précisé*` (183),
  « autres » étant quasi inerte (2) — conservé pour protection future ;
- le troisième lexique et ses deux artefacts de comptage.

---

## Vérification de bout en bout

1. `build lexicons` puis **double build** → artefacts byte-identiques.
2. `cards build` + `cards build-categories` complets.
3. Rapport `reports/cards_policy_effect.csv` : par chapitre, conservées /
   normalisées / écartées par règle ; codes dont la section devient vide ;
   distribution des parts par source des catégories (**médiane ~0,48, ~41-54
   catégories > 80 %** au plafond 20).
4. **Fiches témoins avant/après** : `R51` (XVIII, non-fuite LLM), un S hors
   T36-T50, un T4x, un V ou W, `Z51.1`, une entrée Index normalisée sur un
   chapitre non exclu, et `C79` / `C34`.
5. **Migration du notebook** : les sections (d) et R3 importent
   l'implémentation réelle ; les cellules pédagogiques restent. Chiffres
   identiques au prototype figé — **tout écart est bloquant**.
6. `uv run pytest` (référence **366 verts**), `ruff check`, `ruff format
   --check`, `mypy`.
