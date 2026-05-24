# Surcharge OWL — extraction enrichie du RDF CIM-10 ANS

## Pourquoi surcharger ?

`smt2parquet/cim10.py` n'extrait du RDF ANS que cinq prédicats :
`skos:notation`, `rdfs:label`, `dc:type`, `skos:altLabel`,
`xkos:inclusionNote`. Or le fichier
`referentials/raw/CIM_ANS_2026/dat/terminologie-cim-10-2025-01-01.rdf`
expose plusieurs prédicats utiles supplémentaires, dont les notes
d'exclusion et les associations dague/astérisque.

## Inventaire des prédicats du RDF ANS

Compté sur `terminologie-cim-10-2025-01-01.rdf` (édition 2025-01-01,
13 MB) au 2026-05-15 :

| Prédicat                          | Occurrences | Extrait par `smt2parquet/cim10.py` ? |
|-----------------------------------|------------:|--------------------------------------|
| `xkos:inclusionNote`              | 16 246      | ✓ oui                                |
| `skos:altLabel` (synonymes)       | 23 082      | ✓ oui                                |
| `skos:notation` (code)            | (tous)      | ✓ oui                                |
| `rdfs:label` (libellé)            | (tous)      | ✓ oui                                |
| `dc:type` (chapitre/bloc/cat/sub) | (tous)      | ✓ oui                                |
| `xkos:exclusionNote`              |  5 634      | **non** — à ajouter                  |
| `atih-cim10:hasCausality` (†→*)   |  1 317      | **non** — à ajouter                  |
| `atih-cim10:hasManifestation`     | présent     | **non** — à ajouter                  |
| `atih-cim10:exclusion`            | présent     | **non** — à ajouter (à analyser)     |
| `skos:definition`                 |    387      | **non** — à ajouter                  |
| `skos:scopeNote`                  |    374      | **non** — à ajouter                  |

## Stratégie : wrapper local

`src/recode_icd/loaders/owl.py` importe les primitives génériques de
`smt2parquet.core` (parsing RDF, exécution SPARQL, calcul nested set,
écriture Parquet avec métadonnées) et redéfinit les requêtes SPARQL
spécifiques à CIM-10 :

- **`ATTRS_QUERY`** étendu : ajout des clauses `OPTIONAL` pour
  `xkos:exclusionNote`, `skos:definition`, `skos:scopeNote`,
  `atih-cim10:exclusion`.
- **`EDGES_QUERY` ou requête séparée** : extraction des paires
  `(?manifestation atih-cim10:hasCausality ?cause)` pour reconstruire la
  table dague/astérisque (cause = code dague primaire, manifestation =
  code astérisque). Vérification de symétrie avec
  `atih-cim10:hasManifestation`.
- Pas d'héritage : `smt2parquet` n'expose pas de classe abstraite. La
  surcharge se fait par redéfinition des constantes module-level et
  appel direct aux fonctions `core.*`.

## Colonnes du Parquet produit

Le Parquet produit par `loaders/owl.py` doit contenir, en plus des
colonnes standards de `smt2parquet` (`code`, `label`, `type`, `depth`,
`left`, `right`, `path`, `synonymes`, `inclusion_note`) :

- `exclusion_note: list[str]`
- `definition: str | None`
- `scope_note: list[str]`

La table des associations †/* est exportée **séparément** dans
`referentials/processed/dagger_asterisk_owl.parquet` avec colonnes
`(dagger_code, asterisk_code, source="OWL_ANS")`.

## Tests

- Régression sur 5 codes témoins (un avec exclusion, un avec
  dague/astérisque, un avec définition, un avec altLabel multiples, un
  sans propriétés optionnelles) — voir
  `tests/regression/test_owl_loader.py`.
- Vérification que chaque code RDF du fichier est présent dans le
  Parquet de sortie (no silent drop).

## TODO ouvert

- Confirmer la direction sémantique de `atih-cim10:hasCausality` sur un
  échantillon manuel (le dague est-il bien le sujet ou l'objet de la
  propriété ?). Exemple à valider :
  `F02.00 atih-cim10:hasCausality G31.0` → F02.00 est la manifestation
  (démence Pick), G31.0 est la cause (maladie de Pick = dague).
- Évaluer si `atih-cim10:exclusion` apporte une info distincte de
  `xkos:exclusionNote` ou si c'est une duplication.
- PR upstream sur `smt2parquet/cim10.py` pour aligner avec la version
  CCAM (qui extrait déjà `xkos:exclusionNote` et `skos:definition`).
