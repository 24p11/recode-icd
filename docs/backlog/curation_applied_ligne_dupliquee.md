# Backlog — `reports/curation_applied.csv` reçoit une ligne dupliquée à chaque build

> Statut : **à corriger**, hors chantier. Relevé le 2026-09-05 pendant
> le chantier couverture ATIH (palier 1), en relançant la chaîne aval
> pour vérifier le déterminisme.

## Le constat

`recode-icd build flat-csv` **ajoute** à `reports/curation_applied.csv`
une ligne `flat_csv,synonyms_filtered_as_duplicates,54` à chaque
exécution au lieu de la remplacer : le fichier committé en porte déjà
quatre exemplaires (lots successifs du chantier B). Le rapport n'est
donc pas déterministe — il dépend du nombre de builds — alors que
toute fonction de build du projet doit l'être (CLAUDE.md, conventions
de code).

La valeur (54) est stable ; seul le nombre de lignes dérive. Aucun
consommateur connu ne lit cette ligne.

## À faire

1. Dans l'exporter (`exporters/flat_csv.py` ou le CLI `build flat-csv`),
   réécrire la section `flat_csv` du rapport au lieu de l'annexer —
   même patron que les autres dimensions du fichier (`curation`,
   `coherence`), écrites d'un bloc par `build dagger-asterisk`.
2. Nettoyer les doublons présents dans le fichier committé.
3. Test : deux builds successifs produisent un rapport byte-identique.

Précédent : le projet a déjà été mordu par des artefacts non
déterministes (`recommendations/build.py`, docstring de module).
