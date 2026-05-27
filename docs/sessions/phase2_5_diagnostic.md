# Diagnostic Phase 2.5 — orphans externes

> Généré par `scripts/explore/2026-05-27_phase2_5_diagnostic.py`.

## Synthèse

- **75 codes orphans uniques** analysés (265 entrées brutes dans `reports/external_orphan_codes.csv`, déduplication par code).
- **0/75** (0 %) dans le RDF ANS 2025.
- **67/75** (89 %) dans OFS MASTER 2006.
- **Cause dominante** : H4 — la politique « ANS prime sur OFS pour l'existence du code » (documentée dans `source_mapping.md`) laisse 67/75 codes OFS-only hors de `merged_codes`. **Pas un bug**, mais une conséquence de la politique. La CIM-10 FR-PMSI 2025 a refondu ces codes.
- **8/75** vrais codes morts (absents de tout) — bruit des sources externes (Index CIM-10 vol3 2019).
- **0/75** dûs à un défaut de loader → H1 (corruption du loader OWL) **INFIRMÉE**.
- **Catégorie `post_2006_ans_only` confirmée inutilisable** (0 cas, refonte proposée).


## Recommandation

**Pas de correction de loader.** Le diagnostic appelle deux décisions distinctes :
1. **Politique d'existence des codes** : statu quo (option A — par défaut, recommandé sauf besoin métier explicite) ou repêchage des codes OFS-only (option B/C — modifie la politique documentée).
2. **Refonte de la catégorisation orphan** : indépendante, recommandée (~30 min) pour rendre `reports/external_orphan_codes.csv` actionnable. Cf section 4.

---

## Section 1 — Matrice de présence des 75 codes orphans

**Synthèse présence** :

| source | présents | absents |
|---|---:|---:|
| RDF ANS brut | 0 | 75 |
| OFS MASTER table brute | 67 | 8 |
| `owl_codes.parquet` (sortie loader) | 0 | 75 |
| `ofs_codes.parquet` (sortie loader) | 63 | 12 |

**Patterns de présence** (4 colonnes : RDF | OFS_master | OWL_Parquet | OFS_Parquet) :

| pattern | n codes | interprétation |
|---|---:|---|
| `✗✓✗✓` | 63 | OFS-only — retiré par l'ATIH dans ANS 2025 (politique merger) |
| `✗✗✗✗` | 8 | absent de toutes les sources — vrai code mort |
| `✗✓✗✗` | 4 | OFS-only mais loader OFS l'a filtré (rare) |

**Types observés dans OFS MASTER pour les orphans (qui y sont présents)** :

| type OFS | n |
|---|---:|
| `S` | 61 |
| `D` | 3 |
| `K` | 3 |

**15 codes emblématiques** (mix de patterns) :

| code | RDF | type RDF | OFS_M | type OFS_M | OWL_pq | type OWL_pq | OFS_pq |
|---|:-:|---|:-:|---|:-:|---|:-:|
| `A90` | ✗ | · | ✓ | K | ✗ | · | ✓ |
| `A91` | ✗ | · | ✓ | K | ✗ | · | ✓ |
| `B23.4` | ✗ | · | ✗ | · | ✗ | · | ✗ |
| `B59` | ✗ | · | ✓ | K | ✗ | · | ✓ |
| `B75.2` | ✗ | · | ✗ | · | ✗ | · | ✗ |
| `C83.2` | ✗ | · | ✓ | S | ✗ | · | ✓ |
| `C83.4` | ✗ | · | ✓ | S | ✗ | · | ✓ |

---

## Section 2 — Validation des hypothèses

**H1 — loader OWL filtre incorrectement des codes présents dans le RDF** : 
**INFIRMÉE**. Aucun code orphan n'est dans le RDF ANS sans être dans `owl_codes.parquet`. Le loader OWL n'a aucune responsabilité dans ce problème.


**H2 — variation de format de code (avec/sans point, casse, caractère invisible)** : 
**non pertinente**. Les codes observés (A90, A91, C83.2, ...) ont des formats standards à 3 ou 5 caractères ; pas d'artefact détecté. Si le code existait sous une autre forme dans le RDF, on l'aurait trouvé par la recherche de tous les `A9*` (voir trace).


**H3 — codes vraiment absents partout (vrais codes morts)** : 
**partiellement confirmée** : 8/75 codes (11 %) sont absents de TOUTES les sources (RDF ANS, OFS MASTER). Probablement des fautes de transcription dans l'Index CIM-10 vol3 de 2019 ou des codes déprécés depuis longtemps.


**H4 (NOUVELLE) — politique du merger « ANS prime sur OFS pour l'existence »** : 
**CONFIRMÉE COMME CAUSE DOMINANTE**. 67/75 codes (89 %) sont dans OFS MASTER mais absents du RDF ANS 2025. La politique de `merge.merge_codes()` (documentée dans `docs/source_mapping.md`) exige qu'un code existe en ANS pour figurer dans `merged_codes`. Conséquence : les codes CIM-10 OMS 2006 qui ont été retirés ou refondus par l'ATIH dans la version FR-PMSI 2025 disparaissent du référentiel.


**Exemple concret** : A90/A91 (Dengue, Fièvre hémorragique de dengue) sont absents du RDF ANS 2025 ; la classification FR a refondu les fièvres tropicales dans A92-A99 et probablement déplacé la dengue dans A92.x ou B-codes ATIH. Mais l'Index CIM-10 vol3 (édition 2019) référence encore A90/A91 → orphans.


**Bilan diagnostic** :

- Cause dominante : **H4** (politique merger, 67/75).
- Cause secondaire : **H3** (vrais codes morts, 8/75).
- H1 et H2 : non pertinentes ici.
- **Aucune correction de loader nécessaire**. La question est produit/politique : faut-il étendre `merged_codes` aux codes OFS-only pour préserver une couverture rétro-compatible ?

---

## Section 3 — Tracé pas-à-pas pour 3 codes témoins

### `A90`

- **RDF ANS brut** : absent
- **OFS MASTER brut** : présent — type = `K`
- **`owl_codes.parquet`** : absent (cohérent — pas dans RDF source)
- **`ofs_codes.parquet`** : présent — type = `category`
- **`merged_codes`** : absent (puisque l'Index CIM-10 l'a classé orphan)

  → Le code est en OFS mais pas en ANS. Cas dégénéré OFS-only.


### `A91`

- **RDF ANS brut** : absent
- **OFS MASTER brut** : présent — type = `K`
- **`owl_codes.parquet`** : absent (cohérent — pas dans RDF source)
- **`ofs_codes.parquet`** : présent — type = `category`
- **`merged_codes`** : absent (puisque l'Index CIM-10 l'a classé orphan)

  → Le code est en OFS mais pas en ANS. Cas dégénéré OFS-only.


### `R75` : pas dans la liste des orphans (skip)

---

## Section 4 — Refonte de la catégorisation orphan

**Constat (confirmé par le diagnostic ci-dessus)** : la catégorie `post_2006_ans_only` est **inutilisable**. Pourquoi : un code post-2006 présent dans ANS appartient nécessairement à `merged_codes` (le merger l'a créé via OWL/ANS), donc il n'apparaît jamais comme orphan. Le critère discriminant n'a pas de population à filtrer.


**Sémantique utile à capturer** (causes réellement observées) :

- **`pre_2006_dropped_by_atih`** : code présent en OFS 2006 mais absent du RDF ANS 2025 (l'ATIH l'a retiré/refondu dans la classification FR-PMSI). C'est la cause **dominante**. Décision produit : faut-il étendre `merged_codes` pour préserver ces codes ?

- **`truly_absent`** : code absent de TOUTES les sources (RDF ANS ET OFS MASTER). Probablement une faute de transcription dans la source externe (l'Index CIM-10 vol3 date de 2019 et a des approximations).

- **`loader_dropped`** (théoriquement possible, 0 cas observé) : code dans le RDF mais perdu par le loader. À garder par défense future.


**Nouveau schéma proposé** (spec, à implémenter en Phase 2.5b) :

```python
categorie_orphan ∈ {
    "pre_2006_dropped_by_atih",  # OFS oui, ANS non — politique
    "truly_absent",              # ni OFS ni ANS — bruit source externe
    "loader_dropped",            # RDF oui, owl_codes.parquet non
    "unknown_pattern",           # combinaison inattendue (filet de sécurité)
}
```

**Bénéfice** : chaque catégorie pointe vers une action concrète. Plus de catégorie ambiguë comme `post_2006_ans_only`.

---

## Section 5 — Recommandations de correction (input phase 2.5b)

**Aucune correction de loader nécessaire.** Le diagnostic montre que les 75 codes orphans sont :
- **67** (89 %) présents en OFS 2006 mais retirés de la classification ANS 2025 par l'ATIH (politique merger : ANS prime sur OFS pour l'existence).
- **8** (11 %) absents de toutes les sources (vrais codes morts dans l'Index CIM-10 vol3).
- **0** dûs à un défaut de loader.


**Décision à prendre (produit, pas technique)** :

1. **Option A — Statu quo** : accepter que les codes OFS-only ne soient pas dans `merged_codes`. Cohérent avec la politique CIM-10 FR-PMSI actuelle (l'ATIH a refondu pour de bonnes raisons). Le CSV final reflète la classification française vivante. **Conséquence** : ~75 entrées externes resteront orphan, loggées mais non intégrées. Pas de modification de code.

2. **Option B — Repêchage OFS-only** : étendre `merge.merge_codes()` pour créer des entrées `merged_codes` à partir des codes OFS-only (~67 codes à réintégrer). Modifie la politique documentée dans `source_mapping.md`. **Conséquence** : ces codes obsolètes apparaissent dans le CSV avec leur libellé OFS et leurs notes OFS uniquement. Volumétrie supplémentaire estimée : ~2010 lignes CSV (sur la base de la médiane 30 notes/code observée en audit Phase 2).

3. **Option C — Compromis** : repêcher uniquement les codes 3-car (`type=K` OFS) qui ne sont pas couverts par une refonte ANS — pas les sous-catégories `S`. Volumétrie supplémentaire plus faible.


**Cible de correction (si option B ou C choisie)** :

- `src/recode_icd/merge.py` : nouvelle branche dans `merge_codes()` qui injecte les codes OFS-only avec `source=OFS` pour le libellé.

- `src/recode_icd/merge_external.py` : refonte de `_classify_codes` pour distinguer `pre_2006_dropped_by_atih` vs `truly_absent` vs `loader_dropped` (cf section 4).

- `docs/source_mapping.md` : mise à jour de la politique "Existence du code" dans le tableau §"Politique de fusion".


**Refonte catégorisation orphan (indépendante des options ci-dessus)** :

Quelle que soit l'option retenue, la catégorisation actuelle est défaillante. La refonte proposée en section 4 doit être faite — complexité ~30 min (modif `_classify_codes` + tests d'intégration).

---

## Annexe — Plan phase 2.5b (correction)

Cette annexe propose deux chantiers indépendants. Le premier est léger et recommandé sans discussion. Le second est une décision produit à valider.


### Chantier 1 — Refonte catégorisation orphan (recommandé)

**Complexité : faible (~45 min)**.


**Étapes** :

1. Modifier `merge_external._classify_codes` pour produire les 3-4 catégories proposées en section 4 (`pre_2006_dropped_by_atih`, `truly_absent`, `loader_dropped`, `unknown_pattern`). Nécessite de passer le DataFrame `ofs_codes` (et éventuellement le RDF) à la fonction.

2. Mettre à jour les tests d'intégration Phase 2 (`tests/integration/test_external_merge.py`) pour les nouvelles catégories — en particulier `test_orphan_codes_logged_not_added` qui vérifie `vraiment_orphan`.

3. Mettre à jour `docs/source_mapping.md` §"Codes orphelins externes" avec le nouveau schéma.

4. `build external` + vérifier `reports/external_orphan_codes.csv` actionnable.


**Risques** : négligeables. Aucun impact sur le CSV final.


### Chantier 2 — Politique d'existence des codes (décision produit)

**Décision à valider** : option A/B/C. Volume OFS-only significatif (67).


**Si option B (repêchage OFS-only) choisi** :

**Complexité : modérée (~2h)**.

1. Modifier `merge.merge_codes()` pour ajouter une branche qui injecte les codes OFS-only avec leurs colonnes propagées depuis OFS (libellé, inclusions, exclusions, synonymes). Le `source` du code est `OFS`, le `type` est dérivé du `type` OFS (`K`→category, `S`→category, `G`→block, `C`→chapter).

2. Adapter `MergedCodesSchema` si nécessaire (probablement pas, le schéma est déjà permissif).

3. Mettre à jour `docs/source_mapping.md` §"Politique de fusion" ligne "Existence du code" : maintenant `OWL_ANS ∪ OFS` au lieu de `OWL_ANS uniquement`.

4. Tests : ajouter régression `test_merge_includes_ofs_only_codes` avec témoins A90, A91, C83.2 (5-10 codes). Vérifier que ~67 codes apparaissent dans `merged_codes` après le merge.

5. Rebuild complet + audit : valider que les entrées Index CIM-10 sur ces codes (67 codes × N entrées chacun) rejoignent le CSV final au lieu d'être loggées orphans. Volume CSV supplémentaire estimé : +2010 à +6700 lignes.


**Risques chantier 2** :
- **Conflit de politique** : la spec `source_mapping.md` énonce explicitement « Priorité = ANS (à jour) puis OFS » pour l'existence. Modifier ça doit être documenté comme un revirement assumé.
- **Cohérence en aval** : `flat_csv.py` filtre sur `leaves` (codes nested-set avec right-left==1). Les codes OFS-only n'ont pas de place dans l'arbre nested-set ANS — il faudra leur attribuer un left/right cohérent ou les exclure du filtre leaves. Question non-triviale.
- **Risque d'incohérence sémantique** : ces codes ont été retirés par l'ATIH pour une raison (refonte clinique). Les réintégrer va à l'encontre de la classification FR-PMSI utilisée en pratique.
