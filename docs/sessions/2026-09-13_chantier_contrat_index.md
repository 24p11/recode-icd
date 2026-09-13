# Chantier « contrat d'index » — récap (2026-09-13)

**Branche** `feat/contrat-index` (depuis `main`, en parallèle du
chantier notes OFS — arbres jamais partagés, chantier committé et
poussé avant bascule). **Décisions pré-arbitrées avec RF**, appliquées
sans STOP intermédiaire ; merge sur accord explicite. Prompt archivé :
`2026-09-13_prompt_chantier_contrat_index.md`.

## Historique confirmé contre le git log (avec une nuance)

- `_index.csv` existe depuis le **2026-06-07** (`2edf6c5`) — antérieur
  à D4. Ce que D4 a décidé (`4a35d67` du 2026-09-05, mergé le
  2026-09-06 dans `4fcbd2b`), c'est **un index PAR bibliothèque**
  (autoportance) : `cards_library_controle/_index.csv` naît au palier 2
  (`9419ef7`, 06/09).
- Les **1 709 fiches hors index** : résidus pré-profils, confirmé —
  piège attrapé à la livraison du 2026-09-12 (`5c73a22`, archive
  construite depuis l'index par `preparer_livraison.py`).

## Ce qui est en place

| Décision | Implémentation |
|---|---|
| CONTRAT.md | source canonique `docs/livraison/CONTRAT.md`, copié par le build à la racine des trois bibliothèques, embarqué dans le paquet de livraison |
| Nom canonique | `cards._ecrit_index` écrit `index.csv` (canonique : `filepath → fichier`, + `format_version`) ET `_index.csv` (schéma historique, déprécié, un cycle) |
| Noyau garanti | `code, fichier, statut_mco, format_version` — présent dans les trois index (feuilles, contrôle, catégories) ; `FORMAT_VERSION = "1"` dans `cards.py` |
| L'index fait foi | `cards._nettoie_residus` : un build COMPLET supprime les `.md` hors index (CONTRAT.md épargné) et rapporte le compte (`BuildSummary.n_residus_nettoyes`, affiché par la CLI) ; un build partiel (`--limit`/`--chapter`) ne nettoie jamais |
| Consommateur interne | le résolveur (`couverture.charge_contexte`) lit `index.csv`/`fichier`, repli `_index.csv`/`filepath` pendant la transition ; tests d'invariants migrés vers le canonique |
| Canal officiel | `preparer_livraison.py` lit le canonique, embarque `index.csv` + `_index.csv` (transition) + `CONTRAT.md` ; `LIVRAISON.md` et le guide d'usage renvoient au contrat |
| Consommateurs | fictomed (CHU Brest), Stream (AP-HP) — listés dans CONTRAT.md avec la sémantique `tronc_composition` |

## Tests

`tests/unit/test_contrat_index.py` (5) : canonique + copie dépréciée
identiques au renommage près, `format_version` constante ; nettoyage
épargne CONTRAT.md ; **un build partiel ne rase rien** (résidu témoin
survivant) ; le contrat documente chaque décision (grep des termes) ;
le résolveur lit les deux schémas. `.gitignore` : `index.csv` committé
pour les trois bibliothèques (règle catégories dédupliquée au passage).

## Nettoyage effectif au premier build sous contrat

Rebuild des trois bibliothèques : les résidus pré-profils ont été
supprimés par le build lui-même (compte au récapitulatif CLI) — le
répertoire et l'index sont désormais alignés, et le restent.

## Calendrier de transition

- **Cycle en cours** : double écriture, consommateurs migrent vers
  `index.csv` (fictomed et Stream notifiés à la prochaine livraison via
  LIVRAISON.md/CONTRAT.md).
- **Cycle suivant** : retrait de `_index.csv` (écriture, .gitignore,
  repli du résolveur) — à ouvrir comme micro-chantier.

Merge dans `main` sur accord explicite de RF.
