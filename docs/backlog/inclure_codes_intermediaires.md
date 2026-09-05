# Backlog — Inclure les codes intermédiaires dans le CSV final

> Statut : **appliqué le 2026-09-05** (chantier couverture ATIH, D2) —
> mais **pas l'option B** décrite ci-dessous : le périmètre du CSV est
> désormais « feuilles ∪ codes intermédiaires **codables en MCO** »
> (kit ATIH), soit 800 codes de plus, et non les 2 893 codes catégorie.
> Les 1 846 autres nœuds sont des pères interdits (type 3) qui ne se
> codent pas — `U07.1` en fait partie : le témoin de ce backlog n'était
> pas un code autorisé, ses feuilles `U07.10..15` le sont. Cf
> `docs/analyses/2026-09-05_couverture_atih_phase1.md` §5 et
> `docs/source_mapping.md` § « Périmètre du CSV maître ».
> Décision RF initiale du 2026-05-25 : différé, codes terminaux
> uniquement.
> Diagnostic complet : voir [../sessions/2026-05-25_phase3_dagger_asterisk.md](../sessions/2026-05-25_phase3_dagger_asterisk.md)
> §4 et la session de migration du 2026-05-25.

## Contexte rapide

Le filtre [_leaf_codes()](../../src/recode_icd/exporters/flat_csv.py)
(`flat_csv.py:62-65`) restreint le CSV final aux codes dont
`right - left == 1` (feuilles strictes au sens nested set).

Conséquence : **2 893 codes `type == category` OWL sont absents du
CSV final**, dont :

- 1 603 codes 3-caractères classiques (A00, A01, ...) ayant des
  sous-catégories ;
- **916 codes 4-caractères XYZ.X codables en pratique** (U07.1
  COVID-19, C16.9 Tumeur maligne de l'estomac SAI, B18.0 Hépatite
  chronique B avec delta, ...) — devenus nœuds intermédiaires parce
  qu'ils portent des sous-divisions ATIH XYZ.XX ;
- 126 codes 5-caractères + 4 codes 6-caractères avec sous-enfants.

Ces codes sont les "victimes" structurelles : leurs descendants sont
bien présents dans le CSV (ex : U07.10..U07.15), mais le parent
codable l'est pas.

## Prompt prêt à l'emploi pour implémenter l'option B

À coller dans une nouvelle session Claude Code quand la décision sera
prise d'élargir le périmètre du CSV.

```text
On veut élargir le périmètre du CSV maître
`referentials/processed/inclusions_exclusions_synonymes.csv` pour
inclure TOUS les codes `type == category` de la classification OWL,
pas seulement les feuilles strictes du nested set.

Contexte du bug pré-existant (diagnostic complet dans
docs/backlog/inclure_codes_intermediaires.md et docs/sessions/
2026-05-25_phase3_dagger_asterisk.md §4) :

- `src/recode_icd/exporters/flat_csv.py:62-65` définit `_leaf_codes()`
  avec le filtre `(type == "category") & (right - left == 1)`.
- Ce filtre exclut 2 893 codes catégorie OWL du CSV final, dont
  916 codes 4-caractères codables en pratique (U07.1 COVID-19,
  C16.9, B18.0, etc.) qui ont des sous-divisions ATIH 5-caractères.

Tâche : modifier `_leaf_codes()` pour qu'il garde TOUS les codes
`type == "category"`, indépendamment de la valeur de `right - left`.

Critères d'acceptation :

1. Code modifié : `_leaf_codes()` retourne `merged.filter(
   pl.col("type") == "category").select(...)`.
2. Tests existants restent verts (`uv run pytest`). Si certains tests
   font une hypothèse implicite "feuille stricte" qui devient fausse,
   les ajuster avec un commentaire `# élargi à toutes les categories
   (cf docs/backlog/inclure_codes_intermediaires.md)`.
3. Le test
   `tests/regression/test_flat_csv_witnesses.py::test_u07_1_has_no_dagger_asterisk_columns_filled`
   ne doit plus skip — U07.1 doit être présent dans le CSV avec
   `dagger_code` et `asterisk_code` à NULL et `redundancy_level=none`.
4. Ajouter un test de régression qui vérifie la présence d'un
   échantillon de codes 4-caractères auparavant manquants : au
   minimum U07.1, C16.9, B18.0.
5. Régénérer le CSV via `uv run recode-icd build flat-csv` et
   vérifier la nouvelle volumétrie. Volumétrie attendue (estimée
   à la session de diagnostic) : passage d'environ 147 428 lignes à
   un volume plus élevé (à mesurer), avec ~2 893 codes
   supplémentaires injectant chacun leurs notes propagées.
6. Mettre à jour `docs/source_mapping.md` si une section décrit la
   restriction "feuilles strictes" (vérifier en cherchant "leaf"
   ou "feuille" dans le doc). Ajouter une note expliquant que le
   CSV inclut désormais TOUS les codes catégorie, indépendamment de
   leur position dans l'arbre.
7. Marquer cette tâche comme faite dans
   `docs/backlog/inclure_codes_intermediaires.md` (changer le statut
   "différé" → "appliqué le YYYY-MM-DD").
8. Produire un récap de session dans
   `docs/sessions/YYYY-MM-DD_<sujet>.md` (cf CLAUDE.md §5).

Points d'attention :

- La propagation bloc→catégorie→sous-catégorie continue de fonctionner
  comme avant ; les codes intermédiaires hériteront donc des notes de
  leurs parents en plus des leurs.
- Vérifier l'impact sur le filtrage des descripteurs doublons
  (`_filter_redundant_dagger_synonyms`) — pas d'impact attendu car
  ce filtre n'agit que sur les codes liés à une paire dague/astérisque.
- Vérifier l'impact sur l'expansion dague/astérisque
  (`_attach_dagger_asterisk_columns`) — pas d'impact attendu non plus
  car les codes intermédiaires sans paire émettent une ligne avec
  `dagger_code=NULL, asterisk_code=NULL`.
- Les rapports `reports/curation_applied.csv`,
  `reports/dagger_asterisk_summary.csv` doivent être régénérés et
  les compteurs aval (`dagger_lines_marked_redundant`,
  `synonyms_filtered_as_duplicates`) vérifiés cohérents avec la
  nouvelle volumétrie.

Avant de commencer : suivre la consigne CLAUDE.md §1-2 — relire les
documents de référence (docs/source_mapping.md, ce fichier de
backlog, le récap 2026-05-25) puis proposer un plan détaillé avant
toute modification.
```

## Notes complémentaires

- L'option D évoquée à la session de diagnostic (filtrer sur "code
  avec point", c-à-d XYZ.X et XYZ.XX) reste envisageable comme
  alternative à B si on veut exclure les catégories 3-caractères
  pures (A00, A01) qui n'apportent que leur titre. Le prompt
  ci-dessus correspond à B (inclusion exhaustive) ; pour D, remplacer
  le filtre par
  `(pl.col("type") == "category") & pl.col("code").str.contains(r"\.")`.
- L'option C (s'appuyer sur le champ `valid` de la table MASTER OFS)
  exigerait un travail supplémentaire pour les codes post-2006 absents
  d'OFS — la politique de fallback ANS devient alors structurante.
