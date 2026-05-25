# Inventaire des sources externes de synonymes

> Inventaire en lecture seule produit le 2026-05-25 par
> [scripts/explore/2026-05-25_external_sources_inventory.py](../scripts/explore/2026-05-25_external_sources_inventory.py).
> Artefacts JSON associés :
> [scripts/explore/_inventory_artifacts/](../scripts/explore/_inventory_artifacts/).
>
> Objectif : préparer l'intégration de trois nouvelles sources de
> synonymes au CSV maître
> `referentials/processed/inclusions_exclusions_synonymes.csv`.
> Décision d'implémentation reportée — ce document sert de base à la
> discussion.

## Convention de classification des codes

Pour chaque code CIM-10 extrait des sources externes, on mesure la
membership dans deux référentiels :

| Classe       | Définition                                          |
|--------------|------------------------------------------------------|
| `ofs`        | présent dans la table OFS MASTER (codes pré-2006)   |
| `owl_only`   | absent d'OFS mais présent dans `owl_codes.parquet` (codes ATIH post-2006) |
| `orphan`     | absent des deux — vrai code mort ou faute de frappe |
| `unparseable`| forme inattendue (ex : `nocode`, intervalle `B65-`, notation dague) |

Volumétries de référence : OFS MASTER = 19 155 codes, OWL/ANS =
18 778 codes catégorie + chapitres et blocs.

## Format de code observé

| Source                | Format brut                          | Conversion nécessaire |
|-----------------------|---------------------------------------|------------------------|
| ORPHANET              | `Q77.3` (avec point, standard)        | aucune                 |
| Index CIM-10 (B)      | `A000`, `B9688` (compact, sans point) | insertion du point après les 3 premiers caractères |
| AP-HP toutes feuilles | idem Index (compact)                  | idem                   |

Le script utilise une regex `^([A-Z]\d{2})(\d{1,3})$` pour normaliser
les codes compacts ; les codes à 3 caractères (`A00`) sont conservés
tels quels.

---

## 1. ORPHANET

Fichier : [data/Orphanet_Nomenclature_Pack_FR_2025/ORPHA_ICD10_mapping_fr_2025.xml](../data/Orphanet_Nomenclature_Pack_FR_2025/ORPHA_ICD10_mapping_fr_2025.xml)

Métadonnées XML racine : `ExtractionDate=2025-06-24`, `version=1.3.42`.

### Volumétrie brute

| Mesure                                          | Valeur |
|--------------------------------------------------|--------|
| `Disorder` total                                | 7 534  |
| `ExternalReference` vers `Source=ICD-10`        | 8 333  |
| Autres sources rencontrées dans `Source`        | aucune |

### Distribution `DisorderMappingRelation` (sigle en début du `Name` fr)

| Sigle | Sens                                                                 | Compte |
|-------|----------------------------------------------------------------------|--------|
| `E`   | Exact (le code ORPHA est exactement le code CIM-10)                  | **611** |
| `NTBT`| Narrower term, broader term (ORPHA plus restreint que CIM-10)        | 6 883 |
| `BTNT`| Broader term, narrower term (ORPHA plus large que CIM-10)            | 826   |
| `ND`  | Non déterminé                                                        | 13    |

### Distribution `DisorderMappingICDRelation` (axe orthogonal)

| Sigle              | Compte |
|--------------------|--------|
| `Code attribué`    | 6 626  |
| `Code spécifique`  | 1 068  |
| `Terme d'inclusion`| 452    |
| `Terme index`      | 187    |

> ⚠️ **Piège noté** : le snippet `prep_data_icd_models.ipynb` que tu as
> ouvert lit `DisorderMappingICDRelation/Name`, qui porte "Code
> attribué / spécifique / etc.", PAS le sigle E/NTBT/BTNT/ND. Pour
> identifier les correspondances exactes, c'est
> `DisorderMappingRelation/Name` (sans `ICD`) qu'il faut consulter.

### Focus sur la relation `E` (seul cas exploitable comme synonyme)

| Mesure                                         | Valeur |
|-------------------------------------------------|--------|
| Entrées totales                                | 611    |
| Codes CIM-10 distincts                         | 602    |
| Classification OFS                             | 566    |
| Classification OWL only (post-2006)            | 37     |
| Classification orphan                          | 0      |
| Classification unparseable                     | 8      |

### Exemples de relation `E`

| OrphaCode | Name (court)                                | Synonymes (1er)                 | Code | Class. |
|-----------|---------------------------------------------|----------------------------------|------|--------|
| 447       | Hémoglobinurie paroxystique nocturne        | (voir XML)                      | D59.5 | ofs |
| 856       | NON RARE EN EUROPE : Gilles de la Tourette  | (voir XML)                      | F95.2 | ofs |
| 825       | NON RARE EN EUROPE : Spondylarthrite ankylosante | (voir XML)                  | M45  | ofs |

Détail complet des 10 exemples dans
[scripts/explore/_inventory_artifacts/orphanet.json](../scripts/explore/_inventory_artifacts/orphanet.json) (`relation_E.examples`).

### Notes
- Encodage XML : déclaré `UTF-8`, pas d'artefact constaté.
- Aucune contre-référence vers d'autres terminologies (la source XML
  est restreinte à ICD-10).

---

## 2. Index CIM-10 vol3 (feuille `Cim Alphabétique`)

Fichier : [data/CIM_APHP_2019/Dictionnaire_Hector_MAJ062019.xlsx](../data/CIM_APHP_2019/Dictionnaire_Hector_MAJ062019.xlsx)

### Schéma observé (4 colonnes, identique à toutes les feuilles AP-HP)

| Position | Rôle                                           | Exemple                                          |
|----------|------------------------------------------------|--------------------------------------------------|
| 1        | libellé / synonyme / entrée d'index            | "Choléra (asiatique) (épidémique) (malin)..."   |
| 2        | étiquette source constante par feuille         | `B` pour l'Index, `DR1` pour dermato, etc.       |
| 3        | code CIM-10 **format compact sans point**      | `A000`, `B9688`, ou `nocode`, ou `B65-`         |
| 4        | drapeau auxiliaire — quasi toujours `nocode`   | `nocode`                                         |

### Volumétrie

| Mesure                                              | Valeur |
|------------------------------------------------------|--------|
| Lignes brutes                                       | 45 266 |
| Codes avec point dans la source brute               | 0      |
| Distribution longueur (3/4/5/6 chars compact)       | 4 → 39 722 ; 6 → 3 758 ; 3 → 1 779 ; 5 → 7 |
| Classification `ofs`                                | 41 326 |
| Classification `owl_only`                           | 6      |
| Classification `orphan`                             | 5      |
| Classification `unparseable`                        | 3 929  |
| Doublons internes (code, libellé normalisé)         | 0      |

### Décomposition des `unparseable`

| Pattern brut       | Compte | Sens                                                         |
|--------------------|--------|--------------------------------------------------------------|
| `nocode`           | 3 756  | Renvoi "voir X" sans code direct (redirection intra-index)  |
| `B65-`, `R89-`, ...| ≈ 170  | Intervalle ouvert / racine sans précision (10 patterns observés en top 15) |
| autres             | ≈ 3    | Cas atypiques résiduels (à inspecter au cas par cas)         |

→ **Question de politique** : on garde les `B65-` (en normalisant à
`B65` pour validation) ou on les ignore ? Voir Questions ouvertes.

### 10 exemples (les 10 premières lignes valides)

Voir
[scripts/explore/_inventory_artifacts/aphp_and_index.json](../scripts/explore/_inventory_artifacts/aphp_and_index.json) (`INDEX_CIM10_VOL3.examples`).

| libellé                                                                  | code_raw | code_norm | classe |
|--------------------------------------------------------------------------|----------|-----------|--------|
| Choléra (asiatique) (épidémique) (malin), classique                      | A000     | A00.0     | ofs    |
| Choléra (asiatique) (épidémique) (malin), vibrio cholerae o1, biovar... | A000     | A00.0     | ofs    |
| Choléra (asiatique) (épidémique) (malin), el tor                         | A001     | A00.1     | ofs    |
| ...                                                                       | ...      | ...       | ...    |

### Notes
- Encodage : xlsx natif UTF-8, lecture par `fastexcel` sans incident.
- Aucun doublon intra-feuille — l'index contient des libellés parfois
  proches mais distincts (variantes parenthétiques).

---

## 3. Feuilles AP-HP métiers (9 feuilles, schéma identique)

Toutes les feuilles utiles partagent le **même schéma 4 colonnes** que
l'Index ci-dessus. **Un loader unifié paramétré par nom de feuille +
étiquette source est donc possible**.

### Synthèse volumétrie

| Feuille Excel        | Label                | Brutes | `ofs`  | `owl_only` | `orphan` | `unparseable` | Doublons intra |
|----------------------|----------------------|--------|--------|------------|----------|----------------|----------------|
| Dermatologie         | APHP_DERMATOLOGIE    | 1 834  | 1 823  | 7          | 0        | 4              | 2              |
| Endocrinologie       | APHP_ENDOCRINOLOGIE  | 301    | 297    | 1          | 0        | 3              | 0              |
| GRONES               | APHP_GRONES          | 166    | 139    | 6          | 1        | 20             | 0              |
| Troubles métaboliques| APHP_METABOLISME     | 269    | 268    | 0          | 0        | 1              | 0              |
| Néphrologie          | APHP_NEPHROLOGIE     | 715    | 703    | 7          | 1        | 4              | 0              |
| Ophtalmo             | APHP_OPHTALMOLOGIE   | 444    | 439    | 5          | 0        | 0              | 0              |
| Rhumatologie         | APHP_RHUMATOLOGIE    | 1 042  | 1 035  | 5          | 2        | 0              | 4              |
| Germes               | APHP_GERMES          | 258    | 256    | 0          | 0        | 2              | 0              |
| SRLF                 | APHP_SRLF            | 51     | 46     | 3          | 1        | 1              | 0              |
| **Total**            | —                    | **5 080** | **5 006** | **34**   | **5**    | **35**         | **6**          |

### Divergences à signaler par rapport à l'énoncé

- **Endocrinologie : étiquette `ED1`** dans la 1re colonne, pas
  `END1` comme indiqué dans ton brief. À harmoniser (utiliser le nom
  de feuille comme clé canonique, pas l'étiquette).

### Exemples par feuille (5 par feuille)

Voir
[scripts/explore/_inventory_artifacts/aphp_and_index.json](../scripts/explore/_inventory_artifacts/aphp_and_index.json) — chaque label porte un champ `examples`. Petit aperçu :

**APHP_DERMATOLOGIE** (extraits) :

| libellé                              | code_raw | code_norm | classe |
|--------------------------------------|----------|-----------|--------|
| Tuberculose pulmonaire SAI           | A159     | A15.9     | ofs    |
| Adénite tuberculeuse                 | A182     | A18.2     | ofs    |
| Tuberculose cutanée                  | A184     | A18.4     | ofs    |
| Lupus tuberculeux                    | A184     | A18.4     | ofs    |
| Tuberculide papulo-nécrotique        | A184     | A18.4     | ofs    |

### Cas particulier des `unparseable` GRONES (20 lignes)

19 sur 20 sont des `nocode` (entrées de glossaire type
"Hypoprotéinémie : voir hypoprotidémie"). 1 cas est `I200+0` (notation
dague avec `+0`). À ignorer en bloc, sauf décision contraire.

### Chevauchements inter-feuilles AP-HP métiers

Sur **4 991 paires uniques (code, libellé normalisé)** :

| Nombre de feuilles où la paire apparaît | Nombre de paires |
|------------------------------------------|------------------|
| 1                                        | 4 991            |
| 2                                        | 24               |
| ≥ 3                                      | 0                |

Très faible redondance entre spécialités. Exemples typiques :
`C78.7 / "métastase hépatique"` figure dans Néphrologie et
Rhumatologie ; `B02.9 / "zona SAI"` dans Dermato et Néphrologie.

### Chevauchement Index CIM-10 ↔ AP-HP métiers

164 paires `(code, libellé norm)` AP-HP métier sont déjà présentes
dans l'Index. Sur ~5 000 paires AP-HP métier uniques, c'est ~3 % de
redondance avec l'Index — faible.

---

## 4. Mesures transverses

### Encodage

| Source       | Encodage |
|--------------|----------|
| ORPHANET XML | UTF-8 déclaré, sans BOM |
| AP-HP xlsx   | UTF-8 natif (Office Open XML) ; lecture via `fastexcel`. Un fichier de lock `~$Dictionnaire_Hector_MAJ062019.xlsx` indique qu'Excel est actuellement ouvert sur le fichier — sans impact sur la lecture en mode read-only. |

### Estimation volumétrique consolidée

Paires `(code, libellé normalisé)` uniques après dédup tolérante
(NFKD + lowercase + ponctuation, via `recode_icd._normalize.normalize_for_match`) :

| Source                                          | Paires uniques valides |
|--------------------------------------------------|------------------------|
| ORPHANET (relation `E` uniquement, codes valides) | **1 484**             |
| AP-HP toutes feuilles utiles (Index + 9 métiers, codes valides) | **46 178** |
| Overlap ORPHANET ∩ AP-HP                        | **87**                 |
| **Union nette estimée**                          | **47 575**             |

### Ordre de grandeur attendu pour le CSV final

Le CSV actuel pèse 147 428 lignes. L'ajout des sources externes
représenterait environ **+32 %** (47 575 / 147 428). Tous au type
SYNONYM, sauf décision contraire pour les "Terme d'inclusion"
ORPHANET (cf. Questions ouvertes).

> ⚠️ Cette estimation **suppose une dédup tolérante** avec les
> synonymes OFS/ANS déjà présents. Le calcul exact ne peut se faire
> qu'au moment de l'intégration : on retire les paires
> `(code, libellé norm)` déjà présentes dans le CSV courant. Il
> est très probable qu'une fraction non négligeable des entrées Index
> et AP-HP soit déjà dans le CSV (un libellé d'index pour `A00.0`
> "Choléra classique" est typiquement une inclusion OFS).
> Pré-mesure conseillée avant build : intersection avec les
> synonymes/inclusions actuels du CSV.

### Cohérence des schémas

| Constat                                              | Implication |
|------------------------------------------------------|-------------|
| Les 10 feuilles AP-HP utiles ont **strictement le même schéma 4 colonnes** | Un loader unifié paramétré par `(sheet_name, source_label)` suffit. |
| ORPHANET est dans un format distinct (XML)            | Loader dédié. |

---

## Questions ouvertes

À trancher avant l'implémentation (`src/recode_icd/loaders/external/`).

### Q1 — Granularité de l'enum source AP-HP

CLAUDE.md §"Mapping sources internes ↔ libellés CSV" définit un
**unique** `AP_HP` avec libellé CSV "AP-HP". Ton brief liste **9
sous-étiquettes** (`APHP_DERMATOLOGIE`, ...).

Options :
- **A. Conserver `AP_HP` unique** ; la spécialité n'est pas exposée
  dans le CSV final.
- **B. Étendre l'enum en 9 valeurs** ; le CSV final porte
  `AP-HP dermato`, `AP-HP néphro`, etc.
- **C. Compromis** : enum unique `AP_HP` dans le code, mais on ajoute
  une colonne `source_specialty` au CSV pour préserver la traçabilité
  sans casser le schéma à 9 colonnes (ce serait alors 10).

Mon avis : **B ou C**. La spécialité est une info précieuse pour le
LLM (un synonyme dermato peut être très spécifique) et tu as déjà
nommé les sous-étiquettes. **C** préserve la rétro-compatibilité du
schéma actuel.

### Q2 — Politique sur les relations ORPHANET non-`E`

Le brief ne parle que de synonymes, mais ORPHANET livre aussi 6 883
relations `NTBT` (ORPHA plus restreint que la CIM-10) et 826 `BTNT`.

Options :
- **A. Ignorer NTBT/BTNT** : 611 paires `E` seulement. Simple.
- **B. Importer aussi NTBT comme synonyme** : risqué — le libellé
  ORPHA décrit une affection plus précise que le code CIM-10 cible,
  donc le LLM pourrait produire un texte trop spécifique pour
  justifier le code. Probablement à éviter.
- **C. Importer NTBT/BTNT comme inclusion**, marquée
  `redundancy_level=indirect` ou équivalent : sémantique correcte
  mais demande un nouveau type de note dans le modèle.

Mon avis : **A** pour l'itération 1. **B** ou **C** plus tard si
besoin de plus de couverture.

### Q3 — Index CIM-10 vol3 : traitement des `nocode` et des intervalles `B65-`

3 756 lignes `nocode` (renvois intra-index "voir X") ; ~170 lignes
au format `B65-` (intervalle ou racine).

Options :
- **A. Ignorer les deux** : on perd ~170 entrées potentiellement
  utiles (libellés génériques associables à un code racine).
- **B. Ignorer `nocode`, garder `B65-` normalisé en `B65`** : on
  récupère les ~170 libellés. À tester pour vérifier qu'ils ne sont
  pas déjà dans OFS comme inclusions racine.

Mon avis : **B**.

### Q4 — Notes synthétisées vs synonymes externes : conflit possible ?

Le pipeline produit déjà des notes `SYNTHESIZED_SIBLING` pour les
codes `.8`. Les sources externes pourraient apporter des synonymes
pour ces mêmes codes `.8`. Pas de conflit fonctionnel (sources
différentes, types différents), mais ça mérite d'être validé sur
un cas concret (ex : C50.8) avant le build.

### Q5 — Synonyme vs inclusion : type de note final

CLAUDE.md décrit ces sources comme apportant des `SYNONYM`. Mais
certaines entrées d'index vol3 sont plutôt des **inclusions** (`Eberth,
maladie d'` pour `A01.0` est typiquement une inclusion OFS, pas un
synonyme du libellé systématique).

Options :
- **A. Tout ranger sous `SYNONYM`** : simple, mais perd l'info
  inclusion.
- **B. Heuristique** : si la paire `(code, libellé norm)` matche
  déjà une inclusion OFS/ANS, on l'absorbe comme inclusion (et
  source enrichie : `CIM-10 + CIM-10 index`). Sinon, synonyme. Demande
  un audit pour mesurer combien d'entrées sont concernées avant
  décision.

Mon avis : **A** pour l'itération 1, mesurer pour préparer B
ultérieurement.

### Q6 — `INDEX_CIM10_VOL3` vit dans le même fichier que les AP-HP

L'index n'est PAS un thésaurus AP-HP mais cohabite dans le même
classeur. Implications :
- **Loader** : un seul code de lecture xlsx pour les 10 feuilles
  utiles, mais l'enum source distingue `INDEX_CIM10_VOL3` (cf
  CLAUDE.md déjà prévu) des `APHP_*`.
- **Tests** : si AP-HP 2019 est mis à jour, faut-il vérifier que
  l'Index ne bouge pas ? Probablement non — l'index vol3 est un
  référentiel quasi figé depuis 1996.

### Q7 — Adresses fichiers et politique de versionning

Les fichiers sources vivent dans `data/`, gitignored selon CLAUDE.md
(« fichiers sources, gitignored si volumineux »). Question pratique :
quand on génère un Parquet `external_*.parquet` à partir d'eux, on le
commit ? Le ratio compression vs traçabilité penche probablement
pour oui (fichier final < 10 Mo, utile pour CI/reproducibilité).
