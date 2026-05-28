# Documentation du projet recode-icd

Index des documents de référence. Chaque document a un rôle précis et un
public cible.

## Documents de référence (à lire avant de modifier le pipeline)

| Document | Rôle | Public |
|----------|------|--------|
| [`source_mapping.md`](source_mapping.md) | **Référence absolue** de la construction : mapping canonique OFS ↔ ANS, politique de fusion par champ, couples dague/astérisque, sources externes, propagation. Toute décision sur la sémantique d'un champ se tranche ici. | Développeurs du pipeline |
| [`csv_usage_guide.md`](csv_usage_guide.md) | Guide d'**exploitation** du CSV final : schéma des 11 colonnes, sémantique des sources, recommandations pour l'usage (prompt engineering). | Consommateurs du CSV |
| [`sources/ofs_schema.md`](sources/ofs_schema.md) | Schéma détaillé de la base OFS suisse (tables, champs, codes source). | Développeurs des loaders OFS |

## Distinction source_mapping vs csv_usage_guide

Ces deux documents sont complémentaires et ne se recouvrent pas :

- **`source_mapping.md`** explique comment le CSV est **construit** (d'où
  viennent les données, comment elles fusionnent, quelles règles
  s'appliquent). C'est la spec technique de production.
- **`csv_usage_guide.md`** explique comment le CSV est **exploité** (que
  contient chaque colonne, comment filtrer, quelles précautions prendre).
  C'est la doc du consommateur, autonome (ne suppose pas de connaître le
  pipeline).

## Journaux de session

Le dossier [`sessions/`](sessions/) contient les récaps de sessions de
travail datés (`YYYY-MM-DD_<sujet>.md`). Chaque session non triviale y
laisse une trace : décisions prises, fichiers modifiés, ce qui reste à
faire. Utile pour reprendre le projet après une pause ou comprendre
l'historique d'une décision.

## Rapports générés (non versionnés dans docs/)

Les rapports produits à chaque build vivent dans `reports/` (à la racine
du projet), pas dans `docs/`. Les principaux :

| Rapport | Contenu |
|---------|---------|
| `reports/csv_stats.md` | Statistiques à jour du CSV final (distributions source, type, source_level, quantiles). Régénéré via `recode-icd build stats`. |
| `reports/external_overlaps.csv` | Entrées externes absorbées par dédup avec OFS/ANS. |
| `reports/external_orphan_codes.csv` | Codes cités par les sources externes mais absents du CSV. |
| `reports/external_sources_summary.csv` | Bilan par source externe (chargé / absorbé / orphan / ajouté). |
| `reports/dagger_asterisk_summary.csv` | Métadonnées des paires dague/astérisque. |
| `reports/curation_applied.csv` | Impact de la curation dague/astérisque appliquée au build. |

## Notebooks

| Notebook | Rôle |
|----------|------|
| `scripts/explore/01_walkthrough_pipeline` | Walkthrough pédagogique du pipeline complet (fil rouge A18.1). Point d'entrée pour découvrir le projet. |
| `scripts/explore/<date>_inspect_code` | Démonstration de la fonction `inspect_code()` (inspection d'un code : toutes sources + résultat final). |

## Conventions

- Les documents de référence (`source_mapping.md`, ce README) sont mis à
  jour AVANT l'implémentation d'un changement structurant, pas après.
- Les statistiques chiffrées vivent dans `reports/` (volatiles,
  régénérées), pas dans les documents de référence (qui ne contiennent que
  des ordres de grandeur datés).
