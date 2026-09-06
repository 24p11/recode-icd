# Chantier couverture ATIH — paliers 1 et 2 (2026-09-05 → 2026-09-06)

**Branche** `feat/couverture-atih` · **Paliers mergés dans `main`** :
palier 1 (`a9f43f9`, D1 + D0), palier 2 (D4 → D2 → D3 → invariants).
**Suite** : 834 tests verts. **Reste** : D5 (chapitre XX), palier 3.

Objectif du chantier : l'invariant absolu « tout code autorisé MCO a une
fiche » et son dual « aucun non-codable dans la bibliothèque de
génération ». Mesure préalable (phase 1, validée RF) :
`docs/analyses/2026-09-05_couverture_atih_phase1.md` ; propositions et
arbitrages : `docs/analyses/2026-09-05_couverture_atih_phase2_architecture.md`.

## Ce qui est en place

| Décision | Livrable | Chiffres |
|---|---|---|
| **D1-c** table de notation unique | `referentials/curation/notations_codes.yaml`, `recode_icd/notations.py` | deux familles inversées (O04, **M62.8** — découverte en phase 1), neuf catégories à `+` ponctué ; compacte → maître → compacte identité sur les 42 897 codes du kit, maître → compacte → maître identité sur tout le nested set |
| **D1-a** le kit devient une donnée | `loaders/atih.py`, `atih_codes.parquet`, `build atih`, colonnes `type_mco`/`statut_mco`/`codable_mco` de `merged`, ligne « Statut MCO » sous chaque titre de fiche, colonnes d'index | 42 897 codes, 40 419 codables, 401 supprimés ; sept statuts, `inconnu_atih` ≠ null |
| **D0** résolveur | `couverture.resoudre_code`, `recode-icd resoudre` (`--json`, `--journal`) | dix statuts motivés, repli (descendants, ancêtre, tronc) ; journal JSONL des négatives = mesure d'usage |
| **D4** profils | `profils:` de `chapter_policy.yaml`, `cards build --profil`, un `_index.csv` par bibliothèque | `generation` 15 071 fiches, `controle` 16 986, catégories 2 054 |
| **D2** héritage | `exporters.flat_csv.codes_du_csv` (feuilles + intermédiaires codables), partagé avec `merge_external` | CSV 321 097 → 338 623 lignes, 16 058 → 16 927 codes ; ~11 500 entrées externes récupérées |
| **D3** existence : OWL_ANS, fallback ATIH | `build owl --atih`, `source_existence`, `reports/atih_only_codes.csv` ; `build_cards_library` construit CSV ∪ codables | 72 codes injectés, 59 codables sans ligne dotés d'une fiche |
| **Invariants** | `tests/regression/test_couverture_invariants.py` | I1 : 15 071 / 15 071 ; I2 : 0 non-codable en génération |

## À souligner

### Deux backlogs historiques clos, avec les chiffres mesurés

- **`inclure_codes_intermediaires.md`** (différé le 2026-05-25, « 2 893
  codes catégorie absents du CSV, dont 916 codables en pratique ») : la
  mesure ATIH ramène le vrai périmètre à **800 codes intermédiaires
  codables** (dont 110 qui sont le seul niveau codable de leur branche
  — `M16.0` par exemple, l'ATIH ne connaissant pas nos `M16.0x`) ; les
  **1 846** autres nœuds sont des pères interdits (type 3) qui ne se
  codent pas. Le témoin du backlog, `U07.1`, est lui-même type 3 : ce
  n'est pas un code autorisé, ses feuilles `U07.10..15` le sont. Appliqué
  par D2, sous la forme « feuilles + codables », pas l'option B.
- **`codes_cites_sans_fiche.md`** (« 23 codes visés par des consignes
  sans fiche ») : **17** sont codables et vides de toute source — ils ont
  une fiche depuis D3 (titre, position, statut, consignes) ; **6**
  (`Z37.00/01/20/21/50/51`) sont **inconnus du kit ATIH** : non codables
  en MCO, sans fiche dans aucune bibliothèque, et le résolveur le dit
  (`inconnu_atih`). La question « comportement voulu le jour où un
  consommateur les demande » a sa réponse : une raison motivée, pas une
  fiche.

### La réconciliation des 50 orphelins OFS type D

Le rapport `orphan_type_d_codes.csv` listait depuis le chantier du
2026-06-06 **90 codes type D de MASTER (OFS) absents du RDF ANS**
(`M11.90`, `M13.00`, `M62.80`…), sans traitement. En injectant les 72
codes codables du kit ATIH absents de l'ANS, D3 en a **retrouvé 50** :
`M11.9x`, `M13.0/9x`, `M83.0x/1x`, `M62.8x` — des localisations du
chapitre XIII que l'ANS a perdues mais que l'OFS et l'ATIH connaissent
tous deux. Ils sont désormais au nested set avec le libellé du kit,
rapprochés d'OFS (`has_ofs_match=True`, notes OFS fusionnées), et
l'écart de libellé ATIH ↔ OFS est tracé dans `merge_conflicts.csv`. Le
rapport d'orphelins tombe à 40 ; les 22 autres injectés (`I70.x0/x1`,
`J96.1xx`, `M45+x`) sont des extensions ATIH postérieures à l'OFS.

### Effets de bord mesurés, tous explicables

- guide MCO : 20 282 → 20 345 couples (consigne, code) — les consignes
  atteignent les injectés (ATH-01 sur `I70.x1`) ;
- `post_2006_codes.csv` ne compte plus que l'ANS (les injectés ont leur
  rapport) ;
- durée de génération ≈ 40 ms/fiche (lecture du statut par code) :
  618 s pour `generation`, 791 s pour `controle`.

## Décisions d'implémentation consignées

1. Sept statuts MCO ; `inconnu_atih` est une information (code du
   maître absent du kit : non codable) ; un `null` ne veut dire que
   « kit non joint ».
2. Une fiche sur un code non codable est rendue `fiche` avec
   `codable_mco=False` (bibliothèque `controle`) ; en `generation`,
   D4 a retiré ces codes, le résolveur répond la raison.
3. Pas de dépendance circulaire kit → maître : `atih_codes` ne dépend
   pas de `merged`.
4. Pas de ligne au CSV pour les codes injectés : trace au rapport et
   colonne `source_existence` de l'index (réversible).
5. Les artefacts sont régénérés une fois par palier, dans un commit
   `build(...)` séparé des commits de code.

## Dette et backlogs ouverts

- `docs/backlog/curation_applied_ligne_dupliquee.md` (nouveau) :
  `build flat-csv` annexe une ligne au rapport à chaque exécution.
- `docs/backlog/taille_csv_maitre.md` : le CSV (55,9 Mo) dépasse le
  seuil recommandé de GitHub — traité dans la future revue
  d'architecture par la formalisation des deux couches, pas en vol.
- Section « Subdivisions codables » des fiches (fiche propre, D2-P) :
  au backlog pour le vérificateur.

## Fichiers touchés (par commit)

`7894281` notations · `ac9042c` loader ATIH · `991dd39` merged/fiches/index · `33c829d` résolveur · `c37b9a0` docs · `4a35d67` profils · `d6dd267` périmètre CSV · `f7c33f7` injection · `5f9bbea` résolveur (descendants) + témoins · `9419ef7` artefacts.
