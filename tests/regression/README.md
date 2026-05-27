# Tests de régression

Tests basés sur des **codes témoins** de la classification CIM-10.
Vérifient empiriquement que le pipeline complet (OFS + ANS + dague/
astérisque + sources externes) produit le résultat attendu sur des
codes spécifiquement choisis.

Tous les tests portent le marqueur pytest `regression`. Ils
dépendent des artefacts produits par le pipeline (`build merged`,
`build flat-csv`, `build external`) — ils sont automatiquement
**skip** si ces artefacts sont absents.

Lancement :
```bash
uv run pytest -m regression
```

## Codes témoins

Liste centrale : [`tests/fixtures/sample_codes.yaml`](../fixtures/sample_codes.yaml).
Cette section regroupe les codes par cas de validation, avec le
fichier de test associé.

### Phase 1 — pipeline OFS + ANS (tests historiques)

| Code | Témoin de | Tests |
|---|---|---|
| `A00.0` | Catégorie historique, divergence libellé OFS↔OWL | [`test_flat_csv_witnesses.py`](test_flat_csv_witnesses.py) |
| `F02.00` | Dague/astérisque OWL via triple direct | `test_flat_csv_witnesses.py` |
| `F66.2` | `skos:definition` OWL (cas rare) | `test_flat_csv_witnesses.py` |
| `I41.1` | Dague/astérisque OWL via reification `owl:Axiom` | `test_flat_csv_witnesses.py` |
| `J45.8` | Sous-catégorie .8 avec synthèse exclusion frères | `test_flat_csv_witnesses.py` |
| `C50.8` | Sous-catégorie .8 dans C00-C75 (SKIP synthèse) | `test_flat_csv_witnesses.py` |
| `K70.3` | Exclusions OFS multiples chapitre XI | `test_flat_csv_witnesses.py` |
| `V03.1` | Chapitre XX (causes externes) — structure 5-char | `test_flat_csv_witnesses.py` |
| `Z00.0` | Chapitre XXI (non-maladie) | `test_flat_csv_witnesses.py` |
| `T81.0` | Chapitre XIX — exclusions héritées du bloc | `test_flat_csv_witnesses.py` |

### Phase 2 — dague/astérisque (curation)

| Code | Témoin de | Tests |
|---|---|---|
| `A17.8` / `G05.0` | Couple subordinate via curation | [`test_dagger_asterisk_witnesses.py`](test_dagger_asterisk_witnesses.py) |
| `A18.1` / `N33.0` | Couple subordinate (canonique) | `test_dagger_asterisk_witnesses.py` |
| `E10.2` / `N08.3` | Couple independent (canonique) | `test_dagger_asterisk_witnesses.py` |
| `U07.1` | Code post-2006 sans dague/astérisque | `test_dagger_asterisk_witnesses.py` |

### Phase 3 — sources externes (nouveaux témoins)

11 codes témoins répartis en 6 catégories de validation.

| Code | Catégorie | Témoin de |
|---|---|---|
| `E84.8` | A. ORPHANET E | Synonyme ORPHANET sur une sous-catégorie de Mucoviscidose (E84 non-leaf, exclu) |
| `D59.5` | A. ORPHANET E | Maladie rare avec plusieurs synonymes ORPHANET (HPN) |
| `Q87.8` | B. ORPHANET NTBT | Code-fourre-tout dominé par les inclusions ORPHANET (>1000) |
| `E74.0` | B. ORPHANET NTBT | Inclusions ORPHANET (sous-classification glycogénoses) |
| `A52.7` | C. Index CIM-10 vol3 | Cas extrême : >2000 synonymes Index (syphilis tardive) |
| `I10` | C. Index CIM-10 vol3 | Code standard avec synonymes Index (sanity) |
| `H22.0` | D. AP-HP | Entrées AP-HP Ophtalmologie non absorbées (~25) |
| `N08.5` | D. AP-HP | Entrées AP-HP Néphrologie non absorbées (~15) |
| `A18.1` | E. Coexistence | Dague/astérisque + entrées externes coexistent |
| `U07.10` | E. Coexistence | Code post-2006 — aucune source externe |
| `A90` | F. Orphan | Retiré par l'ATIH 2025, classé `pre_2006_dropped_by_atih` |

Tests : [`test_external_sources_witnesses.py`](test_external_sources_witnesses.py).

#### Tests de cohérence globale (en complément des 11 témoins)

| Test | Vérifie |
|---|---|
| `test_external_sources_never_fill_dagger_columns_for_non_paired_codes` | Aucune entrée externe sur un code hors paire ne remplit `dagger_code`/`asterisk_code`. |
| `test_external_entries_inherit_subordinate_redundancy` | Les entrées externes sur A18.1 (dague subordinate) héritent bien de `redundancy_level=subordinate`. |
| `test_csv_final_schema_unchanged` | Le CSV final a toujours exactement 9 colonnes. |

### Phase 2.5b — catégorisation orphan (refonte)

Voir [`test_external_sources_witnesses.py::test_a90_classified_as_pre_2006_dropped_by_atih`](test_external_sources_witnesses.py) qui valide la nouvelle catégorie `pre_2006_dropped_by_atih`. Les 4 catégories complètes (`pre_2006_dropped_by_atih`, `truly_absent`, `loader_dropped`, `unknown_pattern`) sont aussi testées dans [`tests/integration/test_external_merge.py`](../integration/test_external_merge.py).

## Style des assertions

**À FAIRE** :
- Fourchettes (`n > 500`, `100 ≤ n ≤ 3000`) plutôt que valeurs exactes.
- Présence d'au moins une entrée d'une source attendue.
- Type correct (synonyme / inclusion / exclusion).
- Pour les codes dague/astérisque : `dagger_code`/`asterisk_code`/`redundancy_level`/`is_redundant_dagger` cohérents.

**À ÉVITER** :
- Tests sur des valeurs exactes (genre "exactement 2 478 entrées") — la volumétrie peut bouger légèrement à chaque rebuild si les sources évoluent.
- Tests sur des libellés exacts (sauf pour les libellés systématiques OFS qui sont stables).

## Fixtures partagées

[`conftest.py`](conftest.py) expose 3 fixtures `scope="module"` :

- `csv_final_df` : CSV maître post-Phase 2 (~215 000 lignes).
- `orphan_report_df` : `reports/external_orphan_codes.csv`.
- `overlaps_report_df` : `reports/external_overlaps.csv`.

Les tests qui nécessitent une de ces fixtures sont **automatiquement skip** si l'artefact n'est pas présent (CI sans données).
