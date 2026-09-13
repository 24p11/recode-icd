# Prompt de commande — chantier « contrat d'index » (archivé)

> Prompt de RF reçu le 2026-09-13 (chantier en parallèle du chantier
> notes OFS), archivé tel quel. Récap :
> `2026-09-13_chantier_contrat_index.md`.

---

Ok chantier en parallèle :

Éléments d'historique à confirmer contre le git log : _index.csv =
décision D4 (profils, 6/09) ; les 1 709 hors index = résidus
pré-profils, piège attrapé à la livraison du 12/09 (archive construite
depuis l'index, script preparer_livraison.py). Décisions pré-arbitrées
avec Rémi pour le contrat : nom canonique index.csv (transition :
double écriture un cycle, _index.csv déprécié) ; noyau garanti code,
fichier, statut_mco, format_version ; l'index fait foi — le build
nettoie son répertoire ou échoue sur résidus ; le canal officiel pour
les consommateurs externes est le paquet de livraison versionné, pas
outputs/ ; documenter la sémantique tronc_composition. Consommateurs
connus à lister : fictomed (CHU Brest), Stream (AP-HP). Le CONTRAT.md
vit à la racine de chaque bibliothèque ET dans le paquet de livraison.
