# Nouveautés des fiches — livraison du 2026-09-14

> À l'attention des consommateurs de la bibliothèque de fiches CIM-10
> (fictomed — CHU Brest, Stream — AP-HP). Version livrée : commit
> `33d89c0`, kit ATIH 2025, `format_version` **1 — inchangée** : le
> noyau garanti de l'index (`code`, `fichier`, `statut_mco`,
> `format_version`) n'a pas bougé.

## Trois sections nouvelles sur les fiches

Les notes officielles de la CIM-10 (OMS/ANS 2025, complétées par la
base OFS 2006) entrent dans les fiches, validées ligne à ligne par
relecture médicale. Trois sections peuvent apparaître :

**1. `## Définition (CIM-10)`** — la définition officielle du code,
entre le Périmètre clinique et les consignes. Exemple (E43,
malnutrition grave) :

> Perte de poids importante (émaciation) chez l'enfant ou l'adulte, ou
> absence de gain pondéral chez l'enfant, aboutissant à un poids
> inférieur d'au moins trois écarts types à la valeur moyenne de la
> population de référence […]

**2. `## Description clinique (OMS)`** — les descriptions cliniques du
glossaire officiel (chapitre F en tête). Exemple (F20.0) :

> La schizophrénie paranoïde se caractérise essentiellement par la
> présence d'idées délirantes relativement stables, souvent de
> persécution […]

**3. `## Notes de la CIM-10`** — les règles d'emploi substantielles de
la classification, après les consignes du guide méthodologique (les
deux proviennent de référentiels différents et ne sont jamais
fondues). Une note héritée d'un bloc porte sa provenance. Exemple
(I21.08) :

> \- Pour la morbidité, le laps de temps dont il est fait mention en
> I21-I22 et I24-I25 est l'intervalle entre le début de l'épisode
> ischémique et l'admission pour soins. […] *(note du bloc I20-I25)*

Le boilerplate OMS sans substance (« utiliser, au besoin, un code
supplémentaire… ») a été écarté du rendu sur relecture — pas de bruit
nouveau dans vos prompts.

## Bibliothèque des catégories : 43 fiches de nœud nouvelles

L'index de la bibliothèque des catégories passe de **2 054 à 2 097
lignes** : des fiches de BLOC (`I20-I25`, `D00-D09`…) et de CHAPITRE
(`X`…) portent désormais les notes attachées à ces niveaux. Leurs
codes ne sont pas des catégories 3 caractères — si vous filtrez par
forme de code, ces lignes sont nouvelles ; le noyau garanti et les
colonnes existantes sont inchangés.

## Rappels du contrat (CONTRAT.md, embarqué dans l'archive)

- **L'index fait foi** : consommez `index.csv`, jamais un parcours du
  répertoire. `_index.csv` est déprécié — **dernier cycle de double
  écriture, retrait à la prochaine livraison** : migrez vers
  `index.csv` (colonne `fichier`) dès maintenant.
- Le canal officiel reste le **paquet de livraison versionné** (nommé
  commit + millésime kit), jamais le répertoire `outputs/` du dépôt.
- Retours et codes non résolus : joignez le journal du résolveur
  (`recode-icd resoudre … --journal`).
