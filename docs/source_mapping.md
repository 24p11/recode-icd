# Mapping canonique OFS ↔ OWL/ANS

> Document de référence ABSOLU. Tout loader, tout merger, tout exporter
> du projet recode-icd doit s'y conformer. En cas de doute sur la
> sémantique d'un champ ou d'une propriété, c'est ici qu'on tranche,
> pas dans le code source.

## Principe directeur

Les deux sources OFS (relationnelle, suisse, 2006) et OWL/ANS (RDF/OWL,
française, à jour) décrivent le **même domaine sémantique** : la
classification CIM-10. Les noms diffèrent ; les concepts sous-jacents
sont identiques pour les types de notes structurantes.

**Quand un concept existe dans les deux sources, OFS est la source de
référence pour la sémantique fine.** L'OFS distingue par construction
ce que l'OWL aplatit parfois en annotations textuelles. La fusion doit
donc rapprocher les concepts via leur sémantique, pas via leurs noms
techniques.

## Table de correspondance maître

| Concept canonique recode-icd     | OFS (table → champ source)         | OWL/ANS (propriété)                | Priorité fusion       |
|----------------------------------|-------------------------------------|-------------------------------------|------------------------|
| Code CIM-10 (entité)             | MASTER (filtré valid=True)         | `skos:Concept` avec notation        | ANS (à jour) puis OFS |
| Libellé systématique             | LIBELLE via SYSTEM, source='S'     | `skos:prefLabel` (lang=fr)          | ANS puis OFS          |
| Inclusion explicite ("Comprend:")| LIBELLE via INCLUDE, source='I'    | `xkos:inclusionNote` (lang=fr)      | **OFS** puis ANS      |
| Synonyme / descripteur           | LIBELLE via DESCR, source='D'      | `skos:altLabel` (lang=fr)           | **OFS** puis ANS      |
| Exclusion typée                  | LIBELLE via EXCLUDE, source='E'    | `xkos:exclusionNote` (lang=fr)      | **OFS** puis ANS      |
| Exclusion indirecte              | LIBELLE via INDIR, source='N'      | `xkos:exclusionNote` (indistinct)   | **OFS** uniquement    |
| Note éditoriale (4000 car)       | MEMO via NOTE                       | `xkos:note` ou `rdfs:comment`       | **OFS** puis ANS      |
| Terme de glossaire               | MEMO via GLOSSAIRE                  | `xkos:codingHint` (si présent)      | **OFS** puis ANS      |
| Appariement dague/astérisque     | DAGSTAR (toutes lignes)             | `atih-cim10:hasCausality` + `atih-cim10:hasManifestation` | **OFS** + audit ANS |
| Hiérarchie parent/enfant         | MASTER champs id1..id7              | `skos:broader` / `skos:narrower`    | identique             |

### Lecture du tableau

- **Priorité = ANS** : on prend la valeur ANS, OFS sert de fallback
  pour les codes que l'ANS ne contient pas.
- **Priorité = OFS** : on prend la valeur OFS, ANS sert de fallback
  uniquement pour les codes post-2006 absents de l'OFS.
- **Priorité = OFS uniquement** : l'ANS ne fournit pas l'information
  de manière fiable pour ce concept, on ignore sa version même si
  présente.
- **Priorité = OFS + audit ANS** : on utilise OFS comme source en
  sortie, mais on charge l'ANS en parallèle pour faire un contrôle
  de cohérence (rapport de divergence).

## Pourquoi l'OFS prime pour les notes typées

Quatre raisons fondamentales :

1. **Sémantique portée par la structure.** OFS a des tables séparées
   `INCLUDE`, `DESCR`, `EXCLUDE`, `INDIR`. Quand on lit une ligne de
   `INCLUDE`, on sait avec certitude que c'est une inclusion explicite
   "Comprend:". OWL/ANS utilise `xkos:inclusionNote` qui peut couvrir
   à la fois les inclusions explicites ET les descripteurs/synonymes,
   sans qu'on puisse les distinguer par le seul nom de la propriété.
   Cette confusion est explicitement constatée : la classification
   CIM-10 distingue bien inclusions et synonymes (deux concepts
   différents), et l'OFS reflète cette distinction là où l'ANS la
   perd.

2. **Atomicité native.** OFS fournit chaque note comme une entité
   atomique distincte. Par exemple, pour I78.1 (exclusions), OFS
   livre 11 lignes EXCLUDE, une par affection exclue, chacune avec
   son propre LID. ANS livre la même information sous forme d'**un
   seul bloc textuel** avec puces et codes entre crochets, ce qui
   exige un parsing fragile pour récupérer l'atomicité. Voir la
   section "Limitation connue : atomisation ANS" ci-dessous.

3. **Cohérence éditoriale.** L'OFS est issu d'une seule équipe de
   curation (Nice Computing pour l'OFS) qui a appliqué des règles
   uniformes. L'OWL/ANS est un export automatisé qui hérite des choix
   d'éditorialisation de l'ANS, parfois inégaux selon les chapitres,
   et qui introduit des artefacts d'export (voir section "Conventions
   d'export ANS" ci-dessous).

4. **Audit possible.** Le champ `source` de LIBELLE en OFS (valeurs
   S/I/D/E/N/R) constitue un témoin direct de la sémantique, qu'on
   peut vérifier en relisant la spec OFS. Aucun équivalent en OWL/ANS.

### Précision sur la dimension textuelle

La priorité OFS s'applique à TROIS dimensions distinctes :

1. La typologie (inclusion vs synonyme vs exclusion vs indirecte)
2. L'attribution sémantique (rattachement au bon code parent)
3. Le libellé textuel exact

Pour les dimensions 1 et 2, OFS est strictement supérieur (cf raisons
1-4 ci-dessus).

Pour la dimension 3, la situation est plus nuancée : ANS reflète
l'éditorialisation actuelle de l'OMS qui peut avoir évolué depuis
2006 (corrections OMS, ajustements orthographiques). Toutefois :

- L'OFS V2B004 a inclus les corrections OMS de 1997.
- Les changements de libellé post-2006 sont marginaux pour les notes
  pré-existantes ; ils concernent surtout les codes nouveaux.
- ANS peut introduire des coquilles ou variations non OMS-officielles.

**DÉCISION** : OFS prime aussi sur le libellé textuel pour les notes
typées. Le risque d'importer un libellé vieilli est faible et accepté.
**EN CONTREPARTIE**, le rapport `reports/note_merges.csv` doit logger
SYSTÉMATIQUEMENT la version ANS alternative pour chaque note matchée,
afin de permettre une révision a posteriori.

## Limitation connue : atomisation ANS

### Description du problème

L'OWL/ANS livre les notes multi-éléments sous forme de **blocs
textuels uniques** avec puces et indentation, là où OFS fournit
chaque élément comme une entité atomique distincte.

Exemple concret pour le code I78.1 (exclusions) :

**Côté OFS** — 11 lignes EXCLUDE distinctes, chacune avec son LID :

```
LID=29901, texte="naevus (à) (en) bleu"
LID=29902, texte="naevus (à) (en) flammeus"
LID=29903, texte="naevus (à) (en) fraise"
...
LID=29911, texte="naevus (à) (en) verruqueux"
```

**Côté ANS** — 1 seule chaîne dans `xkos:exclusionNote` :

```
"nævus (à) (en) :
 - SAI [D22.-]
 - bleu [D22.-]
 - flammeus [Q82.5]
 - fraise [Q82.5]
 - mélanocytes [D22.-]
 ...
 - verruqueux [Q82.5]"
```

### Conséquences

1. **L'information est sémantiquement identique** mais formatée de
   manière incompatible.
2. **Toute tentative de re-atomisation de l'ANS** (parser les puces,
   distribuer le préambule) est une inférence fragile qui produira
   du bruit silencieux. **On ne fait PAS ce parsing.**
3. **Pour les codes pré-2006**, la limitation est inoffensive : OFS
   fournit l'atomisation native, on utilise OFS. Les blocs ANS
   correspondants servent uniquement au contrôle de cohérence dans
   `note_merges.csv` (avec un `match_type` adapté).
4. **Pour les codes post-2006**, la limitation a un impact : ANS
   est la seule source, donc les notes restent sous forme de blocs
   dans le CSV final. C'est accepté et documenté (voir "Codes
   post-2006" ci-dessous).

### Pourquoi on ne tente pas le parsing

Plusieurs raisons :

- Format des puces variable selon les chapitres (`-`, `*`, espaces
  d'indentation différents).
- Distribution du préambule (`"naevus (à) (en) :"`) sur chaque puce
  exige de la sémantique, pas du simple texte.
- Codes redirigés entre crochets `[D22.-]` à différencier des codes
  inline qui pourraient apparaître naturellement dans la formulation.
- Cas particuliers (notes imbriquées, listes mixtes) non détectables
  par regex.

Coût attendu d'un parser fiable : plusieurs sessions de développement
+ tests exhaustifs + audit qualité. Bénéfice : marginal puisque OFS
fournit déjà l'atomisation pour les codes pré-2006.

**Décision : on accepte les blocs ANS tels quels pour les codes
post-2006.**

## Conventions d'export ANS

L'OWL/ANS introduit certaines conventions de formatage qui ne sont
PAS standard CIM-10 OMS et qu'il faut connaître quand on consomme
les notes ANS directement :

1. **Codes entre crochets = associations dague/astérisque.** ANS
   écrit `[D22.-]`, `[Q82.5]` dans les notes (inclusions, exclusions)
   pour référencer les codes vers lesquels rediriger. **Ce ne sont
   pas un simple choix typographique** : ces codes correspondent
   sémantiquement aux associations dague/astérisque définies dans la
   table DAGSTAR de l'OFS. L'ANS a ainsi aplati dans le texte une
   information qui était structurée dans la table DAGSTAR. La
   convention CIM-10 OMS standard utilise les parenthèses
   `(D22.-)` pour ces mêmes références.

   **Conséquence** : si on consomme un bloc ANS contenant des codes
   entre crochets, ces codes sont à traiter comme des références
   d'association dague/astérisque, pas comme du texte arbitraire.

2. **Caractères spéciaux** : ANS utilise `nævus` avec ligature æ là
   où OFS utilise `naevus`. La normalisation tolérante (NFKD + strip
   accents) résout ce point pour le matching mais pas pour
   l'affichage final.

3. **Puces et indentation** : voir "Limitation connue : atomisation
   ANS" ci-dessus.

Ces conventions ne sont pas considérées comme des bugs ANS, juste
des choix d'export qui diffèrent de la convention OFS / OMS.

## Pourquoi l'ANS prime pour le libellé et l'existence

Deux raisons opposées :

1. **Couverture temporelle.** L'OFS est gelé au 1er novembre 2006.
   Tous les codes ajoutés depuis (U07.1 COVID, mises à jour OMS
   ultérieures, etc.) ne sont QUE dans l'ANS.

2. **Conformité française actuelle.** Le libellé officiel français
   évolue (corrections OMS, ajustements d'orthographe). L'ANS reflète
   la version utilisée actuellement en France.

## Règle de réconciliation pour les notes typées

**Problème** : la même information peut apparaître à la fois dans
OFS et dans OWL/ANS, mais avec deux différences possibles :

- Différences mineures de libellé (ponctuation, accents, casse,
  apostrophes typographiques).
- Différences de format (OFS atomique, ANS bloc concaténé — voir
  "Limitation connue : atomisation ANS").

**Règle de matching** :

Pour chaque (code, type_de_note), produire les correspondances avec
un champ `match_type` qui prend l'une des 5 valeurs suivantes :

1. **`exact_match`** : un texte OFS et un texte ANS ont le même
   libellé après normalisation tolérante (lowercase + NFKD + strip
   accents + normalisation ponctuation + collapse whitespace). On
   garde la version OFS, on log la version ANS dans `note_merges.csv`.

2. **`atomic_regroupement`** : N textes OFS atomiques pour un même
   code sont tous présents (comme sous-chaînes, après normalisation)
   dans UN bloc ANS. On considère que l'information est équivalente.
   On garde les N textes OFS, on log le bloc ANS dans `note_merges.csv`
   avec un flag `atomic_regroupement=True` et le nombre N.

3. **`real_divergence`** : textes différents même après normalisation,
   pas de relation de sous-chaîne. C'est une vraie divergence
   éditoriale. On garde OFS (priorité), on log ANS dans
   `note_merges.csv` avec `real_divergence=True`. C'est cette
   catégorie qui mérite un audit manuel.

4. **`ofs_only`** : un texte OFS sans contrepartie ANS détectable
   pour ce code/type. On le garde tel quel.

5. **`ans_only`** : un texte ANS sans contrepartie OFS détectable.
   - Pour les codes pré-2006 : à signaler dans `note_merges.csv`
     pour audit (potentielle note absente d'OFS).
   - Pour les codes post-2006 : c'est le cas normal, ANS est la
     seule source.

**Aucune attribution `source='ANS'` n'est faite dans le CSV final
si la note est aussi présente dans OFS (cas `exact_match` ou
`atomic_regroupement`).**

### Migration du schéma note_merges.csv

L'ancien schéma `note_merges.csv` (colonnes : `texte_retenu`,
`texte_alternatif_ans`, `libelles_identiques_apres_normalisation`,
`difference_significative`) est **obsolète et doit être migré** vers
le nouveau schéma basé sur `match_type`.

**Nouveau schéma** (à appliquer) :

| Colonne                       | Type     | Description |
|-------------------------------|----------|-------------|
| `code`                        | str      | Code CIM-10 |
| `type`                        | str      | Type canonique de note (INCLUSION, EXCLUSION, ...) |
| `match_type`                  | str      | exact_match / atomic_regroupement / real_divergence / ofs_only / ans_only |
| `texte_ofs`                   | str?     | Texte côté OFS (null pour ans_only) |
| `texte_ans`                   | str?     | Texte côté ANS (null pour ofs_only) |
| `lid_ofs`                     | int?     | LID OFS pour traçabilité |
| `atomic_regroupement_count`   | int?     | N (nombre d'atomes OFS dans le bloc ANS), null sauf si match_type=atomic_regroupement |
| `code_post_2006`              | bool     | True si le code est absent d'OFS |

L'ancien schéma ne doit plus être produit. Tous les consommateurs
(rapports d'audit, notebooks d'exploration) doivent être migrés
vers le nouveau format.

## Déduplication des synonymes

**Attention** : `smt2parquet/cim10.py` utilise actuellement un
`.unique()` polars pour dédupliquer les synonymes ANS par code :

```python
pl.col("synonyme").drop_nulls().unique().alias("synonymes")
```

Cette déduplication se fait par **égalité stricte de chaîne**, ce qui
laisse passer les variantes mineures (casse, ponctuation, accents,
ligature æ vs ae). Exemples qui passent à travers :

- `"Mucoviscidose"` et `"mucoviscidose"` → 2 entrées
- `"Nævus pigmentaire"` et `"Naevus pigmentaire"` → 2 entrées

**Politique recode-icd** : la déduplication finale des synonymes doit
se faire dans `merge.py` (ou `flat_csv.py`) avec la **normalisation
tolérante** définie ci-dessus (NFKD + lowercase + strip ponctuation +
collapse whitespace), exactement comme pour les inclusions et
exclusions. On ne fait PAS confiance au `.unique()` upstream pour
éviter les doublons "presque identiques" dans le CSV final.

Un test de régression doit vérifier l'absence de paires
`(code, synonyme_normalisé)` dupliquées dans le CSV final.

 
## Couples dague/astérisque : politique de représentation
 
Les couples dague (+) / astérisque (*) sont une convention CIM-10
permettant d'attribuer deux codes à un diagnostic qui contient à la
fois une maladie initiale (étiologie, code dague) et une manifestation
localisée (code astérisque). Exemple : A18.1+ Tuberculose
génito-urinaire (étiologie) + N33.0* Cystite tuberculeuse
(manifestation).
 
### Les trois niveaux d'association
 
Les associations dague/astérisque peuvent exister à trois niveaux
hiérarchiques distincts, reflétés par les 6 valeurs du champ `daget`
dans la table DAGSTAR de l'OFS :
 
| `daget` | Sens                                | Niveau de l'association     | Côté         |
|---------|-------------------------------------|------------------------------|--------------|
| F       | Départ astérisque non pointé        | Catégorie / code            | astérisque   |
| G       | Départ astérisque systématique      | Libellé systématique (code) | astérisque   |
| H       | Départ astérisque descripteur       | Descripteur (synonyme)      | astérisque   |
| S       | Départ dague non pointé             | Catégorie / code            | dague        |
| T       | Départ dague systématique           | Libellé systématique (code) | dague        |
| U       | Départ dague descripteur            | Descripteur (synonyme)      | dague        |
 
Une même association sémantique apparaît typiquement plusieurs fois
dans DAGSTAR.txt, vue depuis chacun des deux côtés et à des niveaux
potentiellement différents. Par exemple, le couple A18.1+/N33.0* est
matérialisé par :
- Une ligne `daget='U'` du côté A18.1 (descripteur "tuberculose (de) vessie")
- Une ligne `daget='G'` du côté N33.0 (libellé systématique "cystite tuberculeuse")
### Sémantique des cas non pointés (F, S)
 
Les cas F et S correspondent à des associations dague/astérisque qui
existent dans la classification mais ne sont pas signalées
typographiquement (pas de symbole + ou * dans le libellé imprimé). Ces
appariements ne portent pas d'information textuelle additionnelle.
 
**Décision** :
- Les cas F et S ne génèrent **PAS** de lignes spécifiques dans le CSV
  principal. Ils ne remplissent pas les colonnes `dagger_code` ou
  `asterisk_code`.
- Ils restent intégralement préservés dans la table DAGSTAR dédiée
  (objectif 2 du projet) pour conserver une vision complète de la
  topologie des associations.
### Table DAGSTAR enrichie (objectif 2 du projet)
 
En complément du CSV principal, on produit une **table relationnelle
dédiée** d'associations dague/astérisque. Cette table est plus
structurée et conserve les 6 valeurs du champ `daget`.
 
**Format** : une ligne par association sémantique unique
(paire `(dague, astérisque)`). Les lignes DAGSTAR.txt qui pointent
vers la même paire sont regroupées via un identifiant `association_id`.
 
**Schéma** :
 
| Colonne                | Type      | Description                                        |
|------------------------|-----------|----------------------------------------------------|
| `association_id`       | int       | Identifiant unique de l'association                |
| `dagger_code`          | str       | Code dague de la paire                             |
| `dagger_label`         | str       | Libellé systématique du code dague                 |
| `asterisk_code`        | str       | Code astérisque de la paire                        |
| `asterisk_label`       | str       | Libellé systématique du code astérisque            |
| `combination_labels`   | list[str] | Libellés observés pour cette combinaison           |
| `levels_present`       | list[str] | Sous-ensemble de {F, G, H, S, T, U}                |
| `redundancy_level`     | str       | none / independent / subordinate                   |
| `source_lids`          | list[int] | LID des entrées OFS qui contribuent à l'association|
 
**Stockage** : Parquet dans `referentials/processed/dagger_asterisk.parquet`,
exporté aussi en CSV pour consommation hors Python.
 
**Construction** :
1. Pour chaque ligne DAGSTAR.txt, déterminer la paire `(dagger, asterisk)`
   en fonction du `daget` :
   - daget ∈ {S, T, U} : le SID est le dague, l'assoc est l'astérisque
   - daget ∈ {F, G, H} : le SID est l'astérisque, l'assoc est le dague
   - Cas daget S ou F sans assoc (SID=0) : la paire n'a pas de code
     opposé pointé, on stocke `asterisk_code=NULL` ou `dagger_code=NULL`
     selon le côté.
2. Regrouper les lignes DAGSTAR par paire pour obtenir une ligne unique.
3. Agréger les libellés observés dans `combination_labels` (déduplication
   tolérante par normalisation NFKD + lowercase).
4. `redundancy_level` initialisé à `independent` par défaut, ou `none`
   si la paire est incomplète (un seul côté présent). Mis à jour à
   `subordinate` pour les paires listées dans
   `docs/dagger_subordinate_pairs.yaml`.

### CSV principal : politique de représentation
 
**Principe 1 — On garde tous les codes dans le CSV par défaut.**
 
Tant le code dague que le code astérisque restent dans le CSV avec
leurs libellés systématiques, leurs inclusions propres, leurs
exclusions propres et leurs notes éditoriales. Aucune suppression au
moment du build.
 
Justification : un code dague peut être utilisé seul lorsque la
manifestation n'est pas précisée (cas `independent`). Supprimer ses
lignes dégraderait la capacité du LLM à coder ce code en tant que tel.
 
**Principe 2 — Une ligne CSV par association.** Pour les renvois
multiples (ex : M32.1+ associé à N08.5* ET N16.4*, ou M49.2* associé
à un intervalle de dagues A01-A04), on produit autant de lignes que
d'associations. Chaque ligne contient les mêmes informations sauf le
code apparié.
 
**Principe 3 — Deux colonnes dédiées dans le CSV final** :
 
| Colonne          | Remplie quand                                       | Contenu                             |
|------------------|------------------------------------------------------|-------------------------------------|
| `dagger_code`    | la ligne courante est un code astérisque (daget G/H) | le code dague associé (étiologie)   |
| `asterisk_code`  | la ligne courante est un code dague (daget T/U)      | le code astérisque associé          |
 
Ces colonnes restent vides pour les codes sans association
dague/astérisque, et pour les cas non pointés (daget F/S).
 
**Principe 4 — Colonne `redundancy_level`** (remplie pour TOUTES les
lignes du CSV) :
 
- `none` : le code n'a pas d'association dague/astérisque. Valeur par
  défaut pour la majorité des lignes.
- `independent` : le code a une association dague/astérisque, et les
  deux codes décrivent des réalités cliniques distinctes (par défaut
  pour les couples).
- `subordinate` : le code a une association dague/astérisque où l'un
  des deux codes se "résume" dans la combinaison (typique des
  maladies infectieuses). Valeur attribuée via le YAML curé.
**Principe 5 — Colonne `is_redundant_dagger`** (booléen, remplie pour
toutes les lignes du CSV) :
 
- `True` quand la ligne correspond à un code dague impliqué dans un
  couple `subordinate`. Le consommateur peut filtrer cette colonne à
  l'export pour ne garder que le code astérisque dans les cas
  subordinate. **Non-destructif au build.**
- `False` dans tous les autres cas.
Cette colonne incarne le choix de **réversibilité** : la décision
clinique "le code dague est redondant" est encodée mais pas appliquée
au build. L'usage en aval (entraînement LLM, génération de prompts,
analyse statistique) peut choisir indépendamment de filtrer ou non.
 
### Schéma final du CSV principal
 
| #  | Colonne                | Type | Description                                              |
|----|------------------------|------|----------------------------------------------------------|
| 1  | `code`                 | str  | Code CIM-10                                              |
| 2  | `libelle`              | str  | Libellé systématique du code                             |
| 3  | `type`                 | str  | inclusion / exclusion / synonyme                         |
| 4  | `source`               | str  | CIM-10 / ANS / CIM-10 index / CIM-10 frères / ORPHANET / AP-HP |
| 5  | `texte`                | str  | Texte de la note                                         |
| 6  | `dagger_code`          | str? | Code dague apparié (rempli côté astérisque uniquement)   |
| 7  | `asterisk_code`        | str? | Code astérisque apparié (rempli côté dague uniquement)   |
| 8  | `redundancy_level`     | str  | none / independent / subordinate                         |
| 9  | `is_redundant_dagger`  | bool | True si ligne dague impliquée dans un couple subordinate |
 
### Filtrage des synonymes redondants — règle validée empiriquement
 
Le script `scripts/explore/<date>_dagger_asterisk_dedup.py` a mesuré
que **15,8% des descripteurs OFS** (table DESCR) rattachés à un code
dague (SID dans DAGSTAR avec daget ∈ {S, T, U}) sont des **doublons
sémantiques exacts** avec un descripteur côté astérisque.
 
Ce taux étant minoritaire, la règle initialement envisagée ("filtrer
systématiquement tous les descripteurs côté dague") est trop radicale :
elle supprimerait 411 descripteurs alors que seuls ~88 sont des vrais
doublons. La règle est donc affinée comme suit :
 
**Règle finale** : on filtre uniquement les descripteurs côté dague qui
sont **textuellement identiques** (après normalisation NFKD + lowercase
+ strip ponctuation + collapse whitespace) à un descripteur OU au
libellé systématique présent côté astérisque pour la même paire.
Les descripteurs qui apportent une **formulation différente** sont
conservés des deux côtés, car ils enrichissent le dataset linguistique
(le LLM bénéficie de variations naturelles : "tuberculose de la vessie"
vs "cystite tuberculeuse").
 
**Mesures empiriques sur INCLUDE et EXCLUDE** :
- INCLUDE : 0 doublon observé. La règle de filtrage **ne s'applique pas**
  aux inclusions.
- EXCLUDE : 0 doublon observé. La règle de filtrage **ne s'applique pas**
  aux exclusions.
Seuls les descripteurs (table DESCR) sont concernés par le filtrage.
 

### Le fichier de curation `referentials/curation/dagger_curation.csv`
 
Fichier CSV de curation manuelle où sont déclarées les décisions
`redundancy_level` pour les paires dague/astérisque. Il sert à la fois
de fichier de travail (édité dans Excel ou LibreOffice pendant la
curation) et de fichier de référence consommé par le merger au build.
 
**Schéma du CSV** :
 
| Colonne              | Type | Description                                      |
|----------------------|------|--------------------------------------------------|
| `dagger_code`        | str  | Code dague de la paire                           |
| `dagger_label`       | str  | Libellé du code dague (aide à la décision)       |
| `asterisk_code`      | str  | Code astérisque de la paire                      |
| `asterisk_label`     | str  | Libellé du code astérisque (aide à la décision)  |
| `combination_labels` | str  | Libellés observés, séparés par " \| "            |
| `levels_present`     | str  | Niveaux DAGSTAR présents, séparés par ", "       |
| `redundancy_level`   | str  | subordinate / independent / undecided / vide     |
| `rationale`          | str  | Justification (optionnelle si évident)           |
| `curated_by`         | str  | Nom du curateur                                  |
| `curated_date`       | str  | Date au format YYYY-MM-DD                        |
 
**Génération** : produit par
`scripts/explore/export_curation_csv.py` à partir de la table DAGSTAR
enrichie. Lors d'une régénération (typiquement après une mise à jour
des référentiels OFS ou ANS), les colonnes de curation existantes
(`redundancy_level`, `rationale`, `curated_by`, `curated_date`) sont
**préservées** pour ne pas perdre le travail manuel. Les paires
absentes de la nouvelle table DAGSTAR mais présentes dans l'ancien
CSV de curation sont signalées comme orphelines (à investiguer
manuellement).
 
**Consommation par le merger** : règle d'application au build :
 
- Paire dans le CSV avec `redundancy_level = subordinate` → la ligne
  du code dague dans le CSV principal reçoit `is_redundant_dagger = True`.
- Paire avec `redundancy_level` ∈ {`independent`, `undecided`, vide}
  → comportement par défaut (`is_redundant_dagger = False`).
- Le merger lit la valeur `redundancy_level` du CSV de curation et la
  propage dans la colonne `redundancy_level` du CSV principal.
**Politique de curation** :
 
- Le CSV est pré-rempli pour toutes les paires complètes de la table
  DAGSTAR enrichie.
- La curation se fait par chapitre, à rythme libre, dans Excel ou
  LibreOffice avec les filtres natifs et les listes déroulantes.
- Chaque décision peut comporter un `rationale` court, qui peut être
  commun à un bloc de cas similaires (ex : "Tuberculose pulmonaire —
  étiologie portée par la combinaison").
- La traçabilité minimale (`curated_by`, `curated_date`) est
  obligatoire pour les paires non vides.
- En cas de doute, marquer `undecided` plutôt que de forcer une
  décision. Le statut `undecided` peut être revu plus tard (par
  exemple validé par un médecin).
- Le CSV est versionné dans Git pour conserver l'historique de la
  curation.
**Pourquoi un CSV plutôt qu'un YAML** :
 
Initialement nous envisagions un YAML. Le passage au CSV simplifie le
workflow :
- Le fichier de curation et le fichier de référence sont identiques
  (pas de transformation intermédiaire).
- L'édition dans Excel/LibreOffice est radicalement plus pratique
  qu'un éditeur de texte pour parcourir et trier 1000+ paires.
- Le CSV reste versionnable proprement par Git et son schéma est
  simple à parser.

### Séquencement de l'implémentation
 
Pour limiter les allers-retours et permettre la validation empirique
à chaque étape, l'implémentation suit cette séquence :
 
1. **Phase 1 — Construire la table DAGSTAR enrichie**.
   - Le merger ne change pas encore.
   - On produit `referentials/processed/dagger_asterisk.parquet` et
     `referentials/processed/dagger_asterisk.csv`.
   - À ce stade, `redundancy_level` est rempli avec sa valeur par
     défaut (`independent` pour toutes les paires).
   - On vérifie empiriquement que la table contient bien le nombre
     d'associations attendu (~1300 + cas F/S), et que `combination_labels`
     est correctement agrégé.
2. **Phase 2 — Curation manuelle du CSV**.
   - À partir de la table produite en phase 1, on génère
     `referentials/curation/dagger_curation.csv` via
     `scripts/explore/export_curation_csv.py`.
   - Le data scientist (ou un expert médical) ouvre ce CSV dans Excel
     ou LibreOffice, et cure les paires une par une.
   - Pas de modification de code à cette étape.
   - Sauvegarde régulière, commit dans Git pour conserver l'historique.
3. **Phase 3 — Mise à jour du merger et de l'exporter**.
   - Le merger lit `referentials/curation/dagger_curation.csv`.
   - Pour chaque paire avec `redundancy_level = subordinate` dans le
     CSV de curation, il :
     - Met à jour `redundancy_level = subordinate` dans la table
       DAGSTAR enrichie pour cette paire.
     - Marque `is_redundant_dagger = True` pour la ligne du code dague
       dans le CSV principal.
   - L'exporter CSV génère bien les 9 colonnes du schéma final.
   - Le filtrage des descripteurs doublons (règle validée
     empiriquement à 15,8 % sur DESCR uniquement) est appliqué.
4. **Phase 4 — Tests de régression**.
   - Les codes témoins (cf. `CLAUDE.md`) doivent passer.
   - Au minimum : A17.8/G05.0 (subordinate, dague avec
     `is_redundant_dagger=True`), A18.1/N33.0 (à curer, probablement
     subordinate), E10.2/N08.3 (independent).

### Conséquences sur les rapports
 
À chaque build, en plus des rapports existants :
 
- `reports/dagger_asterisk_conflicts.csv` : écarts OFS / ANS sur les
  appariements (déjà documenté).
- `reports/dagger_asterisk_summary.csv` : nouveau. Donne la liste des
  paires avec leurs métadonnées (cardinalité des libellés, niveaux
  présents, etc.) pour faciliter l'audit et la curation.
- `reports/curation_applied.csv` : nouveau. Liste les paires où
  une décision de curation a été appliquée au build, avec leur
  impact (nombre de lignes dague marquées `is_redundant_dagger=True`
  pour les `subordinate`, nombre de paires `undecided` à reprendre,
  etc.). Permet de vérifier rapidement après chaque build que la
  curation a bien été prise en compte.


### Principes de représentation dans le CSV final

**Principe 1 — On garde TOUS les codes.** Tant le code dague que le
code astérisque restent dans le CSV avec leurs libellés
systématiques, leurs inclusions propres, leurs exclusions propres et
leurs notes éditoriales. **Aucune suppression**.

Justification : un code dague peut être utilisé seul lorsque la
manifestation n'est pas précisée. Supprimer ses lignes du dataset
empêcherait le LLM d'apprendre que ce code existe en tant que tel.

**Principe 2 — Une ligne CSV par association.** Pour les renvois
multiples (ex : M32.1+ associé à N08.5* ET N16.4*, ou M49.2*
associé à un intervalle de dagues A01-A04), on produit autant de
lignes que d'associations. Chaque ligne contient les mêmes
informations sauf le code apparié.

Justification : symétrique avec la philosophie déjà adoptée pour les
exclusions OFS multi-cibles (une ligne par code exclu). Le consommateur
peut toujours faire un `group_by(code)` pour reconsolider.

**Principe 3 — Deux colonnes dédiées dans le CSV final**.

| Colonne          | Remplie quand                                | Contenu                             |
|------------------|----------------------------------------------|-------------------------------------|
| `dagger_code`    | la ligne courante est un code astérisque     | le code dague associé (étiologie)   |
| `asterisk_code`  | la ligne courante est un code dague          | le code astérisque associé (manifestation) |

Ces deux colonnes restent vides pour les codes sans association
dague/astérisque (la majorité).

**Principe 4 — Colonne `redundancy_level`** (remplie pour TOUTES les
lignes du CSV) :

- `none` : le code n'a pas d'association dague/astérisque. Valeur
  par défaut pour la majorité des lignes.
- `independent` : le code a une association dague/astérisque, mais
  les deux codes décrivent des réalités cliniques distinctes (par
  exemple E10.2+ Diabète avec complications rénales / N08.3*
  Glomérulopathie au cours du diabète : le diabète est une maladie
  systémique dont la glomérulopathie n'est qu'une manifestation
  parmi d'autres).
- `subordinate` : le code a une association dague/astérisque où l'un
  des deux codes se "résume" dans la combinaison (par exemple
  A17.8+ Tuberculose du système nerveux / G05.0* Encéphalite au
  cours d'infections bactériennes : l'étiologie tuberculeuse est
  entièrement portée par le nom de la combinaison, le code dague
  apporte peu d'information autonome).

**Valeur par défaut** : `independent` pour les couples dague/astérisque,
`none` pour les autres codes. Les cas `subordinate` sont identifiés
au cas par cas via un fichier YAML curé : `docs/dagger_subordinate_pairs.yaml`.

**Pour les renvois multiples** : si un code dague est associé à
plusieurs astérisques (ou vice-versa), `redundancy_level` reste
`independent` par défaut, mais le YAML peut surclasser cette valeur
au cas par cas si l'expert métier le juge pertinent.

### Le fichier `docs/dagger_subordinate_pairs.yaml`

Format proposé :

```yaml
# Couples dague/astérisque où le code dague est sémantiquement
# subordonné à la combinaison (typique des maladies infectieuses).
# Format : liste de couples explicites, identifiés à la main.

subordinate_pairs:
  - dagger: A17.8
    asterisk: G05.0
    rationale: "tuberculose du système nerveux — l'étiologie est portée par le nom de la combinaison"
  - dagger: ...
    asterisk: ...
    rationale: ...
```

Le fichier est versionné, revu manuellement, et étendu au fil du
temps par le data scientist ou un expert métier (médecin, codeur).
Le contenu initial est vide ou contient quelques cas évidents
identifiés pendant l'exploration.

### Filtrage des synonymes redondants côté dague (TBD)

**Statut** : en attente de validation empirique.

**Hypothèse** : pour les couples dague/astérisque, un descripteur
OFS (table DESCR) peut être présent côté dague ET côté astérisque
quand il décrit la combinaison des deux (par exemple "cystite
tuberculeuse" rattaché à la fois à A18.1 et N33.0). Garder les deux
crée un doublon sémantique trompeur pour le LLM.

**Règle envisagée** : ne garder le descripteur que côté astérisque
(manifestation). On exclut donc du CSV final les descripteurs OFS
(table DESCR) dont le SID apparaît dans DAGSTAR avec un `daget` ∈
{S, T, U} (les départs dague).

**À valider empiriquement** :
- Cardinalité du filtrage : combien de descripteurs sont concernés ?
- Extension à INCLUDE : la même règle s'applique-t-elle aux inclusions ?
- Extension à EXCLUDE : la même règle s'applique-t-elle aux exclusions ?
- Cas où le descripteur dague n'est PAS le même que le descripteur
  astérisque : faut-il alors garder les deux ?

Le script d'exploration `scripts/explore/<date>_dagger_asterisk_dedup.py`
produit les données nécessaires à cette décision. La règle sera
gravée dans ce document une fois validée.

### Table DAGSTAR comme livrable séparé (objectif 2 du projet)

En complément du CSV principal, on produit une **table dédiée**
d'associations dague/astérisque (objectif 2 du projet recode-icd).
Cette table est plus structurée et conserve les 6 valeurs du champ
`daget` (F/G/H/S/T/U) qui distinguent les cas (départ astérisque
non pointé, systématique, descripteur, et symétriquement pour dague).

Cette table sert à des usages où la sémantique fine de l'appariement
est utile (analyse statistique, validation manuelle, contrôle de
cohérence). Le CSV principal, lui, expose une vue simplifiée à deux
colonnes `dagger_code` / `asterisk_code` pour la consommation par le
prompt builder LLM.

## Conséquences pratiques pour les loaders

### Loader OFS (`loaders/ofs.py`)

Doit produire des DataFrames typés où chaque note porte explicitement :
- Son `code` de rattachement
- Son `type` canonique (INCLUSION / SYNONYM / EXCLUSION / INDIRECT_EXCLUSION / COMMENT / CODING_HINT)
- Son `source` = `"OFS"`
- Son `libellé` original
- Le `LID` OFS pour traçabilité

Le typage canonique se fait via le mapping :
- table INCLUDE → type=INCLUSION
- table DESCR → type=SYNONYM
- table EXCLUDE → type=EXCLUSION (+ champ `excluded_code` et `plus`)
- table INDIR → type=INDIRECT_EXCLUSION
- table NOTE (via MEMO) → type=COMMENT
- table GLOSSAIRE (via MEMO) → type=CODING_HINT

### Loader OWL/ANS (`loaders/owl.py`)

Doit produire des DataFrames avec le MÊME schéma canonique. Le typage
se fait via le mapping :

- `xkos:inclusionNote` → **type=INCLUSION sans exception**.
  L'heuristique de détection synonyme vs inclusion à partir de cette
  propriété **n'est pas implémentée** dans la version actuelle. Tout
  `xkos:inclusionNote` est traité comme INCLUSION. Le rapport
  `reports/owl_inclusion_ambiguity.csv` reste prévu pour une
  itération future mais n'est pas peuplé actuellement.
- `xkos:exclusionNote` → type=EXCLUSION (bloc textuel, non atomisé,
  voir limitation ANS)
- `xkos:note` ou `rdfs:comment` → type=COMMENT
- `xkos:codingHint` → type=CODING_HINT
- `skos:altLabel` → type=SYNONYM

Source = `"ANS"`. Le libellé est extrait tel quel (sans
normalisation, sans tentative d'atomisation).

### Merger (`merge.py`)

Applique la règle de réconciliation ci-dessus. Pour chaque (code,
type), agrège les notes des deux sources, applique la normalisation
pour le matching, conserve les originaux, applique la priorité,
produit un `match_type` par correspondance.

La déduplication des synonymes (incluant la déduplication tolérante
qui dépasse ce que fait `.unique()` upstream) est aussi la
responsabilité du merger.

Le merger lit aussi `docs/dagger_subordinate_pairs.yaml` pour
attribuer `redundancy_level=subordinate` aux couples curés.

## Cas particuliers et exceptions

### Exclusions indirectes (INDIR)

L'OWL/ANS ne distingue pas les exclusions indirectes des exclusions
typées. On a deux choix possibles :

- **Choix retenu** : importer INDIR depuis OFS uniquement (priorité
  OFS uniquement), ne JAMAIS essayer de matcher avec une
  `xkos:exclusionNote` ANS. Conséquence : 46 entrées INDIR de l'OFS,
  sans risque de conflit.
- Choix alternatif (non retenu) : tenter un matching textuel sur les
  patterns typiques d'exclusion indirecte ("voir...", "selon...").
  Trop fragile.

### Dague/astérisque — audit de cohérence

L'OFS expose 1352 entrées DAGSTAR parfaitement typées avec 6 codes
(F/G/H/S/T/U). L'OWL/ANS expose 1317 relations via
`atih-cim10:hasCausality` et `atih-cim10:hasManifestation` dans
`terminologie-cim-10-2025-01-01.rdf`.

**Décision** : OFS est la source primaire pour la table dédiée
d'associations (objectif 2 du projet) et pour les colonnes
`dagger_code` / `asterisk_code` du CSV final. L'ANS est chargé en
parallèle pour permettre un **audit de cohérence** : les 35 entrées
d'écart peuvent être de vraies absences ANS (à signaler), ou des
appariements ANS supplémentaires (à étudier pour les codes post-2006).

Tout désaccord OFS ↔ ANS est loggué dans
`reports/dagger_asterisk_conflicts.csv` avec colonnes :
- `code_dagger`, `code_asterisk`
- `present_ofs` (bool), `present_ans` (bool)
- `daget_code_ofs` (F/G/H/S/T/U si présent côté OFS)
- `type_ans` (causality/manifestation si présent côté ANS)
- `commentaire` (catégorie qualitative : ans_post_2006, ans_extra,
  ofs_extra, etc.)

### Codes post-2006

Un code présent dans l'ANS mais absent de l'OFS (champ MASTER) doit
être créé dans le merge avec :
- `source=ANS` pour le libellé
- toutes ses notes (inclusions, exclusions, etc.) avec `source=ANS`
- **Les notes restent sous forme de blocs si elles le sont en ANS**
  (pas de tentative d'atomisation, cf "Limitation connue").
- Les artefacts ANS (crochets, ligatures, puces) sont préservés
  tels quels dans le CSV.
- Pas d'association dague/astérisque sauf si présente dans
  `atih-cim10:hasCausality` ou `atih-cim10:hasManifestation`.

Loguer ces codes dans `reports/post_2006_codes.csv` pour audit avec
colonnes :
- `code`
- `libelle`
- `n_inclusions`, `n_exclusions`, `n_synonymes`
- `has_dagger_asterisk` (bool)
- `notes_atomisees` (bool — False si au moins une note est un bloc
  multi-éléments)

Le code témoin de référence pour ce cas est **U07.1** (COVID-19),
ajouté à la classification en 2020 et donc absent de l'OFS.

## Reporting obligatoire

À chaque build, produire :

- `reports/merge_conflicts.csv` : codes où OFS et ANS donnent un
  libellé différent (après normalisation).
- `reports/note_merges.csv` : paires de notes (OFS, ANS) avec
  `match_type` ∈ {exact_match, atomic_regroupement, real_divergence,
  ofs_only, ans_only} et flags associés (voir schéma ci-dessus).
- `reports/owl_inclusion_ambiguity.csv` : pas peuplé actuellement.
  Réservé pour une future heuristique de séparation inclusion vs
  synonyme à partir de `xkos:inclusionNote`.
- `reports/post_2006_codes.csv` : codes présents uniquement en ANS,
  avec colonnes décrites ci-dessus.
- `reports/dagger_asterisk_conflicts.csv` : écarts OFS / ANS sur
  les appariements dague/astérisque.
- `reports/synthesized_skipped.csv` : codes .8 où la synthèse a été
  skippée (cf catégories C00-C75 et autres cas limites).

Ces rapports sont les yeux du data scientist sur le merge. Ils ne
sont pas optionnels.
