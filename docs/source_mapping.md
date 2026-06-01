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
| Appariement dague/astérisque     | DAGSTAR (toutes lignes)             | `atih-cim10:hasCausality` + `atih-cim10:hasManifestation` | **OFS** + audit ANS, table dédiée hors CSV principal |
| Hiérarchie parent/enfant         | MASTER champs id1..id7              | `skos:broader` / `skos:narrower`    | identique             |
| Synonyme ORPHANET (relation E)         | —                         | —                          | XML `Disorder/Name` + `SynonymList` | externe (post-dédup)  |
| Inclusion ORPHANET (relation NTBT)     | —                         | —                          | XML `Disorder/Name` + `SynonymList` | externe (post-dédup)  |
| Synonyme Index CIM-10 vol3             | —                         | —                          | Excel "Cim Alphabétique" col 1    | externe (post-dédup)  |
| Synonyme thésaurus AP-HP               | —                         | —                          | Excel 9 feuilles métier col 1     | externe (post-dédup)  |


> **Sources externes** : ces sources sont **complémentaires**, pas
> concurrentielles avec OFS/ANS. Pour chaque entrée externe, on
> applique d'abord une dédup tolérante contre les inclusions et
> synonymes déjà présents dans OFS/ANS pour ce code. Si match, l'entrée
> externe est absorbée (loggée dans `reports/external_overlaps.csv`).
> Si pas de match, elle est ajoutée au CSV avec sa source propre.


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

| `daget` | Sens                                | Niveau de l'association     | Côté         | Type de LID référencé   |
|---------|-------------------------------------|------------------------------|--------------|--------------------------|
| F       | Départ astérisque non pointé        | Catégorie / code            | astérisque   | libellé systématique     |
| G       | Départ astérisque systématique      | Libellé systématique (code) | astérisque   | libellé systématique     |
| H       | Départ astérisque descripteur       | Descripteur (synonyme)      | astérisque   | **descripteur dédié**    |
| S       | Départ dague non pointé             | Catégorie / code            | dague        | libellé systématique     |
| T       | Départ dague systématique           | Libellé systématique (code) | dague        | libellé systématique     |
| U       | Départ dague descripteur            | Descripteur (synonyme)      | dague        | **descripteur dédié**    |

**Observation empirique** (vérifiée sur les 1352 lignes DAGSTAR) : il
existe une partition stricte entre `daget` et la source du LID dans
LIBELLE. Les niveaux H et U sont les niveaux "riches" : ils référencent
un descripteur clinique spécifique de la combinaison (ex : "méningite
leptospirose" pour la paire G01+A27). Les autres niveaux référencent le
libellé systématique du code par défaut.

Une même association sémantique apparaît typiquement plusieurs fois
dans DAGSTAR.txt, vue depuis chacun des deux côtés et à des niveaux
potentiellement différents. Par exemple, le couple A18.1+/N33.0* est
matérialisé par :
- Une ligne `daget='U'` du côté A18.1 (descripteur "tuberculose (de) vessie")
- Une ligne `daget='G'` du côté N33.0 (libellé systématique "cystite tuberculeuse")

### Mécanique relationnelle dans DAGSTAR

Chaque ligne DAGSTAR est un triplet structuré :

```
(SID, LID, assoc, daget, plus)
```

- `SID` : le code principal de la ligne
- `LID` : pointeur vers un libellé de la table LIBELLE (libellé
  systématique si source=S, ou descripteur si source=D)
- `assoc` : le code apparié (0 si pas de code apparié fixe — cas non pointés F/S)
- `daget` : niveau et rôle (cf table ci-dessus)
- `plus` : flag (sens exact non documenté, peu fréquent)

**Le LID est l'élément clé** : il identifie quelle formulation textuelle
matérialise la combinaison. Pour les niveaux H et U, c'est un descripteur
dédié (ex : "méningite leptospirose"). Pour les autres niveaux, c'est le
libellé systématique du code, qui ne porte pas d'information sémantique
nouvelle par rapport au libellé du code lui-même.

### Politique de représentation dans le CSV final

**Le CSV `inclusions_exclusions_synonymes.csv` ne porte plus
l'information détaillée des paires dague/astérisque sur ses lignes.**
Cette information vit exclusivement dans la table DAGSTAR enrichie
(`dagger_asterisk.parquet`), conçue pour être utilisée par les
consommateurs en aval lors de l'analyse de scénarios cliniques.

#### Justification du choix

L'expérience d'usage a montré que l'approche initiale ("une ligne CSV
par paire d'association") produisait :

- Une **duplication massive** des notes (jusqu'à ×12 sur des codes comme
  G01 qui ont 12 codes dague appariés)
- Une **attribution sémantique incorrecte** : une inclusion générique
  du code (ex : "Infection due à Salmonella typhi" sur A01.0) se
  retrouvait dupliquée par paire, comme si elle décrivait spécifiquement
  chaque combinaison
- Un **signal dilué** pour les consommateurs LLM

L'investigation a révélé que :

- Pour les paires "pointées sans descripteur dédié" (daget G/T) et les
  codes "non pointés" (daget F/S), le LID référencé par DAGSTAR est le
  libellé systématique du code lui-même. DAGSTAR n'apporte pas de
  contenu textuel nouveau.
- Pour les paires "pointées avec descripteur dédié" (daget H/U), le LID
  est un descripteur clinique de la combinaison (ex : "méningite
  leptospirose"). Ces descripteurs sont déjà présents dans le CSV via
  la table DESCR comme synonymes.

**Conclusion** : DAGSTAR n'enrichit pas sémantiquement le CSV au-delà
de ce que les tables LIBELLE/DESCR/INCLUDE apportent déjà. L'information
de couplage est par nature une **propriété du scénario clinique** (à
exploiter au moment du codage par le consommateur), pas une propriété
intrinsèque d'un code isolé exposable en CSV.

#### Représentation dans le CSV : deux flags booléens

Le CSV final porte deux colonnes booléennes au niveau du code :

- **`is_dagger_in_pair`** : `True` si le code apparaît dans DAGSTAR
  avec `daget ∈ {S, T, U}` (rôle de dague, peu importe que la paire
  soit pointée ou non).
- **`is_asterisk_in_pair`** : `True` si le code apparaît dans DAGSTAR
  avec `daget ∈ {F, G, H}` (rôle d'astérisque).

Un même code peut avoir les deux flags à `True` simultanément si selon
les paires considérées, il joue les deux rôles.

Ces flags signalent au consommateur que le code participe à la
mécanique dague/astérisque, sans détailler les paires spécifiques.
Pour le détail (quel code apparié, quel niveau, quel descripteur,
quel `redundancy_level`), consulter `dagger_asterisk.parquet`.

### Pas d'expansion par paire dans le CSV

Conséquence directe de la politique ci-dessus : **chaque note d'un
code apparaît une seule fois dans le CSV**, indépendamment du nombre
de paires dague/astérisque auxquelles ce code participe.

Cela élimine la duplication observée précédemment (jusqu'à ×12 sur
G01). La logique d'expansion `_attach_dagger_asterisk_columns` qui
réalisait une jointure cartésienne notes × paires est supprimée.

### Table DAGSTAR enrichie (livrable séparé du CSV)

Cette table reste un livrable du pipeline `recode-icd` car elle est
utile aux consommateurs en aval (notamment pour l'analyse de scénarios
cliniques où la détection des paires se fait dynamiquement).

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
   - Cas daget S ou F sans assoc (assoc=0) : la paire n'a pas de code
     opposé pointé, on stocke `asterisk_code=NULL` ou `dagger_code=NULL`
     selon le côté.
2. Regrouper les lignes DAGSTAR par paire pour obtenir une ligne unique.
3. Agréger les libellés observés dans `combination_labels` (déduplication
   tolérante par normalisation NFKD + lowercase).
4. `redundancy_level` initialisé à `independent` par défaut, ou `none`
   si la paire est incomplète (un seul côté présent). Mis à jour à
   `subordinate` pour les paires marquées comme telles dans
   `referentials/curation/dagger_curation.csv`.


### Schéma final du CSV principal

 
| # | Colonne                  | Type | Description                                              |
|---|--------------------------|------|----------------------------------------------------------|
| 1 | `code`                   | str  | Code CIM-10                                              |
| 2 | `libelle`                | str  | Libellé systématique du code                             |
| 3 | `type`                   | str  | inclusion / exclusion / synonyme / note                  |
| 4 | `source`                 | str  | CIM-10 / ANS / CIM-10 index / CIM-10 frères / ORPHANET / AP-HP ... |
| 5 | `texte`                  | str  | Texte de la note                                         |
| 6 | `source_level`           | str  | chapter / block / category / code — niveau d'origine de la note |
| 7 | `inherited_from_code`    | str? | Code parent si propagé (chapter, bloc, catégorie), vide si attaché directement |
| 8 | `is_dagger_in_pair`      | bool | True si le code participe à au moins une association DAGSTAR comme code dague (daget ∈ {S, T, U}) |
| 9 | `is_asterisk_in_pair`    | bool | True si le code participe à au moins une association DAGSTAR comme code astérisque (daget ∈ {F, G, H}) |

Note : ce schéma à 9 colonnes remplace l'ancien à 11 colonnes (qui
portait `dagger_code`, `asterisk_code`, `redundancy_level`,
`is_redundant_dagger`). Voir la section "Couples dague/astérisque :
politique de représentation" ci-dessus pour la justification de cette
refonte.
 
 
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
 
- Paire dans le CSV avec `redundancy_level = subordinate` → la paire
  dans `dagger_asterisk.parquet` reçoit `redundancy_level = subordinate`.
- Paire avec `redundancy_level` ∈ {`independent`, `undecided`, vide}
  → comportement par défaut (`independent` ou `none` selon que la
  paire est complète).
- **Note** : cette information de curation n'est plus propagée dans
  le CSV principal (politique acquise lors de la refonte). Elle vit
  exclusivement dans la table DAGSTAR enrichie pour usage par les
  consommateurs en aval.
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
3. **Phase 3 — Mise à jour du merger et de la table DAGSTAR enrichie**.
   - Le merger lit `referentials/curation/dagger_curation.csv`.
   - Pour chaque paire avec `redundancy_level = subordinate` dans le
     CSV de curation, il met à jour `redundancy_level = subordinate`
     dans la table DAGSTAR enrichie pour cette paire.
   - Le merger calcule les flags `is_dagger_in_pair` et
     `is_asterisk_in_pair` pour chaque code (cf section sur la
     représentation dans le CSV final).
   - L'exporter CSV génère les 9 colonnes du schéma final.
   - Le filtrage des descripteurs doublons (règle validée
     empiriquement à 15,8 % sur DESCR uniquement) est appliqué.
4. **Phase 4 — Tests de régression**.
   - Les codes témoins (cf. `CLAUDE.md`) doivent passer.
   - Au minimum : A17.8/G05.0 (subordinate dans DAGSTAR enrichie),
     A18.1/N33.0 (à curer, probablement subordinate), E10.2/N08.3
     (independent). Les flags `is_dagger_in_pair` /
     `is_asterisk_in_pair` doivent être correctement calculés pour
     ces codes.

### Conséquences sur les rapports
 
À chaque build, en plus des rapports existants :
 
- `reports/dagger_asterisk_conflicts.csv` : écarts OFS / ANS sur les
  appariements (déjà documenté).
- `reports/dagger_asterisk_summary.csv` : nouveau. Donne la liste des
  paires avec leurs métadonnées (cardinalité des libellés, niveaux
  présents, etc.) pour faciliter l'audit et la curation.
- `reports/curation_applied.csv` : nouveau. Liste les paires où
  une décision de curation a été appliquée au build à la table
  DAGSTAR enrichie, avec leur impact (nombre de paires marquées
  `subordinate`, nombre de paires `undecided` à reprendre, etc.).
  Permet de vérifier rapidement après chaque build que la curation
  a bien été prise en compte.

## Propagation des notes hiérarchiques
 
### Principe
 
La CIM-10 organise les codes en une hiérarchie à 4 niveaux :
- **Chapter** : I, II, III, ..., XXII
- **Block** : A00-A09, A15-A19, ..., U00-U49
- **Category** : A00, A01, ..., U07
- **Code** (feuille) : A00.0, A00.1, ...
Les notes peuvent être attachées à n'importe quel niveau :
- Une note d'inclusion attachée au bloc A15-A19 s'applique à TOUS ses codes 
  (A15.0, A15.1, ..., A19.9).
- Une note éditoriale au chapitre I s'applique à tous les codes du chapitre.
- Une exclusion à la catégorie A00 s'applique à A00.0, A00.1, A00.9.
**Le merger propage** ces notes depuis leur niveau d'attachement vers tous 
les codes feuilles concernés. Sans propagation, le CSV final ne contiendrait 
les notes que des niveaux supérieurs, et le LLM consommateur ne pourrait pas 
voir les notes pertinentes au niveau du code feuille qu'il doit annoter.
 
### Traçabilité de la propagation
 
Pour permettre le filtrage et la lecture humaine, le CSV final expose deux 
colonnes qui tracent la propagation :
 
**`source_level`** : niveau d'origine de la note dans la hiérarchie.
 
| Valeur | Sens |
|--------|------|
| `chapter` | La note est attachée au chapitre (propagation maximale) |
| `block` | La note est attachée au bloc |
| `category` | La note est attachée à la catégorie 3-caractères |
| `code` | La note est attachée directement au code feuille (pas de propagation) |
 
**`inherited_from_code`** : le code parent dont la note est propagée.
 
- Vide (null) si `source_level=code` (note attachée directement)
- Le code du chapitre/bloc/catégorie sinon (ex : "A15-A19" pour un bloc, 
  "A00" pour une catégorie, "I" pour le chapitre)
### Conventions par source
 
| Source | `source_level` typique | `inherited_from_code` |
|--------|------------------------|------------------------|
| OFS (libellé systématique) | `code` | vide |
| OFS (inclusions) | `code` / `category` / `block` / `chapter` selon attachement | code parent si propagé |
| OFS (exclusions) | idem inclusions | idem |
| OFS (descripteurs/synonymes) | `code` (toujours) | vide |
| OFS (notes éditoriales) | tous niveaux possibles | code parent si propagé |
| ANS (toutes notes) | idem OFS | idem |
| ORPHANET | `code` (toujours) | vide |
| Index CIM-10 vol3 | `code` (toujours) | vide |
| AP-HP (toutes spécialités) | `code` (toujours) | vide |
| Notes synthétisées (frères) | `code` (toujours) | vide |
 
**Justification** : les sources externes (ORPHANET, Index, AP-HP) référencent 
toujours un code spécifique, jamais un bloc ou un chapitre. Les descripteurs 
OFS/ANS sont par construction attachés au code feuille (table DESCR en OFS). 
Seules les inclusions, exclusions et notes éditoriales d'OFS et ANS peuvent 
être propagées depuis un niveau supérieur.
 
### Filtrage et lecture humaine
 
Cette traçabilité permet plusieurs usages :
 
**Filtrage par spécificité** : un consommateur LLM qui veut maximiser la 
pertinence peut filtrer les notes propagées depuis un niveau trop haut (par 
exemple ignorer les notes `chapter` pour ne garder que celles plus 
spécifiques au code).
 
**Audit humain** : un lecteur du CSV peut comprendre d'où vient chaque note 
sans avoir à comparer avec d'autres lignes du CSV.
 
**Détection d'anomalies** : si une note "code" apparaît pour un code feuille 
alors qu'on s'attendrait à une propagation, c'est un signal à investiguer.
 
### Test de régression
 
Le sample `tests/fixtures/sample_codes.yaml` doit inclure au moins un code 
avec note propagée depuis un niveau supérieur (par exemple un code A00.0 
qui hérite d'une exclusion attachée au bloc A00-A09), pour vérifier que 
`source_level` et `inherited_from_code` sont correctement remplis.
 


## Sources externes : politique d'intégration
 
En complément des deux sources principales OFS (relationnelle suisse,
2006) et OWL/ANS (RDF française, à jour), le projet intègre trois
familles de sources externes pour enrichir le CSV final en synonymes
et inclusions.
 
### Les trois sources externes
 
**Source 1 — ORPHANET (maladies rares)**
 
- Format : XML structuré, validé par XSD
- Fichier : `data/Orphanet_Nomenclature_Pack_FR_2025/ORPHA_ICD10_mapping_fr_2025.xml`
- Version : 1.3.42, extraction 2025-06-24
- Encodage : UTF-8 déclaré, sans BOM
- Volumétrie : 7 534 `Disorder`, 8 333 `ExternalReference` vers ICD-10
**Source 2 — Index CIM-10 vol3 (index alphabétique officiel)**
 
- Format : feuille Excel "Cim Alphabétique" du fichier HECTOR
- Fichier : `data/CIM_APHP_2019/Dictionnaire_Hector_MAJ062019.xlsx`
- Volumétrie : 45 266 lignes brutes
- Encodage : UTF-8 natif (Office Open XML)
**Source 3 — Thésaurus métiers AP-HP**
 
- Format : 9 feuilles distinctes du même fichier HECTOR
- Schéma : identique à l'Index (4 colonnes)
- Volumétrie totale : 5 080 lignes brutes (réparties sur 9 feuilles)
- Feuilles : Dermatologie, Endocrinologie, GRONES, Troubles
  métaboliques, Néphrologie, Ophtalmologie, Rhumatologie, Germes (SPILF),
  SRLF
- Feuilles **exclues** du fichier HECTOR : "Cim Analytique" (pas des
  synonymes), "Orphanet" (redondant avec la source XML directe),
  "Thesam" (qualité non fiable)
### Sémantique de la relation ORPHANET → CIM-10
 
Le XML ORPHANET définit plusieurs types de relations entre un code
ORPHA et un code CIM-10, portées par la propriété
`DisorderMappingRelation/Name` (à ne pas confondre avec
`DisorderMappingICDRelation/Name` qui porte un axe orthogonal).
 
| Sigle | Sens                                        | Volumétrie | Politique recode-icd |
|-------|---------------------------------------------|------------|----------------------|
| E     | Exact (ORPHA = CIM-10)                      | 611        | `type=synonyme`     |
| NTBT  | Narrower Term, Broader Term (ORPHA ⊂ CIM-10) | 6 883      | `type=inclusion`    |
| BTNT  | Broader Term, Narrower Term (ORPHA ⊃ CIM-10) | 826        | **ignoré**          |
| ND    | Non Déterminé                                | 13         | **ignoré**          |
 
**Justification de la politique** :
 
- **Relation E** : ORPHA et CIM-10 désignent la même entité clinique.
  Le `Name` ORPHA et ses `SynonymList` sont donc de vrais synonymes
  du code CIM-10. Type sémantique correct : synonyme.
- **Relation NTBT** : l'ORPHA décrit une affection plus spécifique
  rangée sous le code CIM-10. C'est exactement la définition d'une
  inclusion en CIM-10 OMS (affection plus précise qui se code par
  cette catégorie). Type sémantique correct : inclusion.
- **Relation BTNT** : l'ORPHA est plus large que le code CIM-10
  spécifique. L'inclusion serait sémantiquement incorrecte, le
  synonyme aussi. On ignore.
- **Relation ND** : volume négligeable, sémantique floue. On ignore.
**Piège d'implémentation** : le code legacy `prep_data_icd_models.ipynb`
lisait `DisorderMappingICDRelation/Name` qui porte "Code attribué /
Code spécifique / Terme d'inclusion / Terme index" — sémantique
différente. Le loader recode-icd doit lire
`DisorderMappingRelation/Name` (sans `ICD`).
 
### Politique de fusion avec OFS/ANS
 
**Principe directeur** : OFS reste la source autoritaire pour la
classification CIM-10. Les sources externes **enrichissent** uniquement
les codes là où l'information n'est pas déjà présente.
 
**Règle de dédup tolérante** : pour chaque entrée externe
`(code, libellé, type)`, le merger :
 
1. Normalise le libellé (NFKD + lowercase + strip ponctuation +
   collapse whitespace).
2. Vérifie si une note du même `type` (inclusion ou synonyme) pour
   le même `code` existe déjà dans OFS ou ANS avec le même libellé
   normalisé.
3. Si oui (**match**) : l'entrée externe est **absorbée**, elle ne
   crée pas de ligne dans le CSV final. Une ligne est loggée dans
   `reports/external_overlaps.csv` :
   - `code`
   - `libelle_externe`
   - `libelle_ofs_ans` (le libellé qui a matché)
   - `source_externe` (ORPHANET, INDEX_CIM10_VOL3, APHP_*)
   - `source_ofs_ans` (CIM-10 ou ANS)
   - `lid_ofs` (si disponible, pour traçabilité)
4. Si non (**pas de match**) : l'entrée externe est **ajoutée** au
   CSV avec :
   - `type` selon la source (synonyme pour Index/AP-HP, synonyme ou
     inclusion pour ORPHANET selon la relation)
   - `source` = le libellé CSV correspondant (cf. CLAUDE.md)
   - `texte` = le libellé externe original (non normalisé)
**Cas particulier — dédup tolérante intra-externes** : un même libellé
peut apparaître dans plusieurs sources externes (par exemple
"Mucoviscidose" dans ORPHANET et dans AP-HP Endocrinologie). On
applique la même règle : la première source rencontrée gagne, les
suivantes sont absorbées et loggées. **Ordre de priorité conventionnel** :
ORPHANET > Index CIM-10 vol3 > AP-HP (par spécialité, ordre
alphabétique). Documenté pour reproductibilité.
 
### Codes orphelins externes

Les codes externes (issus de ORPHANET, Index CIM-10 vol3 ou AP-HP)
sont dits **orphans** quand ils ne figurent pas dans `merged_codes`
(produit par `merge.merge_codes()` selon la politique "ANS prime sur
OFS pour l'existence"). Ces codes ne peuvent pas enrichir le CSV
final — leurs entrées sont loggées dans
`reports/external_orphan_codes.csv` avec une colonne
`categorie_orphan` qui explique la cause.

**4 catégories** (cf diagnostic dans
`docs/sessions/phase2_5_diagnostic.md`) :

1. **`pre_2006_dropped_by_atih`** : code présent dans la table OFS
   MASTER 2006 mais absent du RDF ANS 2025. L'ATIH a retiré ou refondu
   ce code dans la classification CIM-10 FR-PMSI actuelle (ex : A90
   Dengue, A91 Fièvre hémorragique de dengue — refondus vers A92.x).
   **Cas dominant** (~89 % en pratique). Pas un bug — conséquence
   assumée de la politique de fusion.

2. **`truly_absent`** : code absent à la fois d'OFS MASTER et du
   RDF ANS. Probablement une faute de transcription dans la source
   externe (l'Index CIM-10 vol3 date de 2019 et a des approximations)
   ou un code déprécié de longue date. **~11 %** en pratique.

3. **`loader_dropped`** : code présent dans le RDF ANS brut mais
   absent du Parquet `owl_codes` produit par le loader. Détectable
   uniquement si on passe le set des codes RDF en argument à
   `merge_external.merge_external_sources(rdf_codes=...)`. **Filet de
   sécurité — 0 cas observé en pratique**. Si détecté, indique un bug
   du loader OWL à investiguer.

4. **`unknown_pattern`** : filet de sécurité pour des combinaisons de
   présence/absence non couvertes par les 3 catégories ci-dessus.
   Aucun cas en pratique avec le code actuel — réservé pour des
   évolutions futures.

**Schéma** `reports/external_orphan_codes.csv` :

| Colonne | Description |
|---|---|
| `code` | Code CIM-10 |
| `libelle` | Libellé externe (non normalisé) |
| `source_externe` | ORPHANET / INDEX_CIM10_VOL3 / APHP_* |
| `categorie_orphan` | Une des 4 valeurs ci-dessus |

Les codes au format non parseable (`nocode`, intervalles `B65-`,
notations dague `I200+0`) sont filtrés en amont par les **loaders
Phase 1** et n'apparaissent jamais dans ce rapport.
### Format des codes dans les sources externes
 
| Source                | Format brut                          | Conversion nécessaire                              |
|-----------------------|---------------------------------------|----------------------------------------------------|
| ORPHANET              | `Q77.3` (standard avec point)         | aucune                                             |
| Index CIM-10 vol3     | `A000`, `B9688` (compact sans point)  | insertion du point après les 3 premiers caractères |
| AP-HP toutes feuilles | idem Index (compact)                  | idem                                               |
 
**Regex de normalisation** pour les codes compacts :
 
```python
import re
 
def normalize_compact_code(code: str) -> str:
    """Convertit 'A000' en 'A00.0', laisse 'A00' inchangé."""
    if not isinstance(code, str):
        return code
    code = code.strip()
    match = re.match(r"^([A-Z]\d{2})(\d{1,3})$", code)
    if match:
        return f"{match.group(1)}.{match.group(2)}"
    return code  # ex : 'A00', 'B65-', 'nocode' restent tels quels
```
 
### Schéma uniforme des feuilles HECTOR (Index + AP-HP)
 
Les 10 feuilles utiles du fichier HECTOR partagent **strictement** le
même schéma 4 colonnes :
 
| Position | Rôle                                            | Exemple                                          |
|----------|--------------------------------------------------|--------------------------------------------------|
| 1        | libellé / synonyme / entrée d'index             | "Choléra (asiatique) (épidémique) (malin)..."   |
| 2        | étiquette source constante par feuille          | `B` pour l'Index, `DR1` pour dermato, etc.       |
| 3        | code CIM-10 format compact sans point           | `A000`, `B9688`, `nocode`, `B65-`               |
| 4        | drapeau auxiliaire — quasi toujours `nocode`    | `nocode`                                         |
 
Un **loader unifié** paramétré par `(sheet_name, source_label)` est
implémenté dans `loaders/external/aphp_hector.py` (et appelé aussi
pour la feuille "Cim Alphabétique" via `loaders/external/index_cim10.py`
qui en est un wrapper).
 
**Divergence connue** : la feuille "Endocrinologie" porte l'étiquette
`ED1` en colonne 2 (et non `END1`). Le loader doit utiliser le **nom
de la feuille Excel** comme clé canonique, pas l'étiquette en colonne 2.
 
**Doublons internes** : 6 doublons intra-feuilles observés (4 dans
Rhumatologie, 2 dans Dermatologie). Déduplication tolérante à
appliquer après chargement.
 
### Volumétrie estimée
 
| Source                                          | Paires uniques valides |
|--------------------------------------------------|------------------------|
| ORPHANET (relations E + NTBT, codes valides)    | ~7 500                 |
| Index CIM-10 vol3 (codes valides + intervalles) | ~41 500                |
| AP-HP 9 feuilles métier (codes valides)         | ~5 000                 |
| **Total brut avant dédup avec OFS/ANS**         | **~54 000**            |
 
L'estimation du **delta net** après dédup avec le CSV courant ne peut
se faire qu'au build. Pré-mesure conseillée : la fraction d'entrées
absorbées peut être significative (probablement 30-50% pour
l'Index/AP-HP, plus faible pour ORPHANET).


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

Le merger lit `referentials/curation/dagger_curation.csv` pour
attribuer `redundancy_level=subordinate` aux couples curés dans la
table DAGSTAR enrichie (`dagger_asterisk.parquet`). Cette information
n'est plus propagée dans le CSV principal — elle reste exclusivement
dans la table dédiée.

Le merger calcule également les deux flags `is_dagger_in_pair` et
`is_asterisk_in_pair` pour chaque code, sur la base de sa présence
dans DAGSTAR (cf section "Couples dague/astérisque").

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
d'associations (objectif 2 du projet, `dagger_asterisk.parquet`).
Pour le CSV final, l'information de couplage n'est plus matérialisée
sur les lignes individuelles : seuls les flags `is_dagger_in_pair` et
`is_asterisk_in_pair` signalent la participation à des paires. L'ANS
est chargé en parallèle pour permettre un **audit de cohérence** :
les 35 entrées d'écart peuvent être de vraies absences ANS (à
signaler), ou des appariements ANS supplémentaires (à étudier pour
les codes post-2006).

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
- Les flags `is_dagger_in_pair` et `is_asterisk_in_pair` valent
  `False` sauf si une association est présente dans
  `atih-cim10:hasCausality` ou `atih-cim10:hasManifestation` côté
  ANS (et donc dans la table DAGSTAR enrichie).

Loguer ces codes dans `reports/post_2006_codes.csv` pour audit avec
colonnes :
- `code`
- `libelle`
- `n_inclusions`, `n_exclusions`, `n_synonymes`
- `has_dagger_asterisk` (bool — True si le code a au moins une association DAGSTAR, quel que soit le rôle)
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
> - `reports/external_overlaps.csv` : **nouveau**. Logge pour chaque
>   entrée externe absorbée par dédup avec OFS/ANS :
>   - `code` : code CIM-10
>   - `libelle_externe` : libellé tel qu'il apparaît dans la source externe
>   - `libelle_ofs_ans` : libellé OFS/ANS qui a matché
>   - `source_externe` : ORPHANET / INDEX_CIM10_VOL3 / APHP_*
>   - `source_ofs_ans` : CIM-10 / ANS
>   - `lid_ofs` : LID OFS pour traçabilité (si applicable)
>   - `match_type` : exact / atomic_regroupement / real_divergence
>     (réutilise la nomenclature de note_merges.csv pour cohérence)
>
> - `reports/external_orphan_codes.csv` : **nouveau**. Logge les codes
>   cités par les sources externes mais absents d'OFS et d'ANS :
>   - `code`
>   - `libelle`
>   - `source_externe`
>   - `categorie_orphan` : "vraiment_orphan" / "post_2006_ans_only"
>     / "non_parseable"
>
> - `reports/external_sources_summary.csv` : **nouveau**. Bilan
>   statistique du build pour chaque source externe :
>   - Nombre d'entrées brutes lues
>   - Nombre d'entrées valides (code parseable et présent)
>   - Nombre d'entrées absorbées (matches OFS/ANS)
>   - Nombre d'entrées ajoutées au CSV final
>   - Permet de suivre l'impact des sources externes build par build.

Ces rapports sont les yeux du data scientist sur le merge. Ils ne
sont pas optionnels.
