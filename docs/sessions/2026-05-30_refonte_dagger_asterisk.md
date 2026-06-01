# Refonte de la politique dague/astérisque

**Date** : 2026-05-30
**Type** : refonte structurelle du pipeline (suite à retours d'usage)
**Statut** : décisions actées et documentées, implémentation à faire

---

## 1. Contexte et déclencheurs

Cette session fait suite à des retours d'usage du CSV
`inclusions_exclusions_synonymes.csv` qui ont révélé trois problèmes
distincts dans le pipeline existant. Le présent récap couvre
exclusivement la refonte du **problème 1** (duplication des notes par
paire dague/astérisque). Les autres problèmes sont mentionnés à la fin
pour la mémoire du projet.

### Les trois problèmes observés à l'usage

**Problème 1 — Duplication des notes par paire dague/astérisque**

Sur A01.0 (fièvre typhoïde), la note d'inclusion "Infection due à
Salmonella typhi" apparaît **3 fois** dans le CSV. Investigation : A01.0
participe à 3 paires dague/astérisque (avec G01, I39, J17.0), et chaque
note du code est dupliquée par paire.

Cas plus extrême : G01 (méningite au cours d'affections bactériennes
classées ailleurs) participe à 12 paires dague/astérisque côté
astérisque + 1 cas non pointé. Toutes ses notes sont dupliquées par 12.
Sur 192 lignes du CSV pour ce code, environ 176 sont redondantes.

**Problème 2 — Notes ANS étiquetées synonyme alors qu'elles sont des inclusions**

Exemples remontés :
- D21.6 "Tronc" — note de localisation anatomique étiquetée comme
  synonyme alors que c'est une précision de localisation
- M01.08 "Arthrite méningococcique [A39.8]" — formulation typique d'une
  inclusion ANS (avec code dague entre crochets) étiquetée comme
  synonyme

Cause sous-jacente probable : l'ANS ne distingue pas clairement
inclusions et synonymes via ses propriétés RDF, et le loader OWL
étiquette par défaut. **Non traité dans cette session** — voir section
"Chantiers identifiés".

**Problème 3 — Navigation OFS brut impossible**

`inspect_code()` ne permettait pas de voir les tables OFS brutes sous le
code. **Traité en amont** dans une session de "Day 2" : ajout d'un mode
`verbose=True` qui expose les tables brutes (BLOC 2bis) et le traçage
inter-étapes du pipeline (BLOC 5). Cet outil a été essentiel pour le
diagnostic du problème 1.

---

## 2. Diagnostic du bug d'expansion (problème 1)

### Premières investigations via `inspect_code(verbose=True)`

L'extension de `inspect_code` a permis d'observer concrètement le bug.
Sur A01.0, le traçage du pipeline montre :

```
Étape                    | Nb lignes
RDF ANS brut (triples)   | (non chargé)
ofs_codes.parquet        | 1
owl_codes.parquet        | 1
merged_codes.parquet     | 1
propagated_notes.parquet | 36
flat_csv (CSV final)     | 108
```

Le saut significatif est `propagated_notes` (36 lignes) → `flat_csv` (108
lignes), avec un facteur **×3** qui correspond exactement au nombre de
paires dague/astérisque de A01.0 (3 paires).

Le traçage d'un texte spécifique le confirme :

```
"Infection due à Salmonella typhi"
  owl_codes=1 | merged_codes=1 | propagated_notes=1 | flat_csv=3
```

La note transite par toutes les étapes en une seule occurrence, puis se
trouve dupliquée par 3 au moment de l'export CSV.

### Localisation du code fautif

L'expansion est faite par la fonction `_attach_dagger_asterisk_columns`
dans `src/recode_icd/exporters/flat_csv.py`. Cette fonction réalise une
**jointure cartésienne** entre :

- Les notes propagées du code (toute note : inclusion, exclusion,
  synonyme, propagation hiérarchique, source externe)
- Les paires dague/astérisque dont le code fait partie (via la table
  DAGSTAR enrichie)

L'intention initiale était de remplir les colonnes `dagger_code` et
`asterisk_code` du CSV : pour chaque paire impliquant le code, on
crée une ligne avec ces colonnes renseignées.

Le problème : cette logique applique l'expansion à **toutes** les notes
du code, alors que sémantiquement, seules certaines notes décrivent
spécifiquement une combinaison dague/astérisque. La majorité des notes
(libellé systématique, inclusions générales, synonymes externes,
exclusions héritées) ne concernent pas la combinaison — elles sont
duplciquées sans raison.

---

## 3. Investigation de la mécanique DAGSTAR

### Question soulevée

L'observation initiale était : "certains descripteurs OFS, comme
'méningite leptospirose' pour G01, semblent matérialiser une combinaison
dague/astérisque". Mais comment cette correspondance est-elle
formellement encodée dans le schéma OFS ?

### Réponse trouvée via le PDF officiel OFS

Le document `Version_V2B004_update_.pdf` (mise à jour officielle OFS
pour la grippe aviaire J09 en 2006) documente la mécanique relationnelle
DAGSTAR. Extrait clé (section 7) :

> 7.1 Table LIBELLE add new **descriptor libelle** for SID 3936 with **LID 70603**
> 7.2 Table DAGSTAR add new link for **SID 3936 LID 70603** to SID 19551 DAGET H

Pour créer une nouvelle paire dague/astérisque entre I41.1 et J09,
l'OFS :
1. **Crée d'abord un nouveau descripteur** dans la table LIBELLE (LID 70603)
2. **Puis crée la ligne DAGSTAR** qui pointe à la fois vers le SID du
   code et vers le LID du descripteur

Conclusion : **chaque ligne DAGSTAR est un triplet structuré**
`(SID, LID, assoc, daget, plus)` où le LID pointe vers un libellé
spécifique qui matérialise la combinaison.

### Confirmation empirique

Vérification sur G01 (SID=2910) + A27 (SID=160, leptospirose) :

```python
ctx.ofs["dagstar"].filter(
    (pl.col("SID") == 2910) & (pl.col("assoc") == 160)
)
# → SID=2910 | LID=15301 | assoc=160 | daget=H | plus=1

ctx.ofs["libelle"].filter(pl.col("LID") == 15301)
# → LID=15301 : "méningite (au cours de) leptospirose"
```

La paire G01+A27 est bien matérialisée par le descripteur "méningite
(au cours de) leptospirose" (LID 15301).

### Investigations empiriques sur les 1352 lignes DAGSTAR

Trois investigations Python ont précisé la mécanique :

**Investigation 1 — Couverture des LID DAGSTAR par les autres tables**

```
LID DAGSTAR présents dans LIBELLE  : 1125 / 1126 (99,9%)
LID DAGSTAR présents dans DESCR    : 656 / 1126 (58%)
LID DAGSTAR présents dans INCLUDE  : 8 / 1126
LID DAGSTAR présents dans EXCLUDE  : 0 / 1126

LID DAGSTAR couverts par au moins UNE table : 1125 / 1126
LID DAGSTAR non couverts (orphans)          : 1 (LID 13911)
```

**Conclusion** : DAGSTAR référence des LID qui sont quasi-tous déjà
présents dans LIBELLE (et souvent dans DESCR). DAGSTAR n'apporte pas
de contenu textuel nouveau.

**Investigation 2 — Source LIBELLE des LID DAGSTAR**

```
Distribution du champ source :
  D (descripteur)        : 718
  S (libellé systématique) : 625
  I (inclusion)          : 8
  null                   : 1
```

Constat majeur : **environ 50% des LID DAGSTAR sont des libellés
systématiques** (source=S), pas des descripteurs. Pour ces 625 cas, le
LID référencé est le libellé systématique du code lui-même, qui n'ajoute
pas de sémantique nouvelle.

**Investigation 3 — Position du LID dans DAGSTAR**

```
Position du LID par rapport aux SID :
  lid_cote_SID    : 1351 (99,9%)
  lid_introuvable : 1 (LID 13911)
```

Le LID est **systématiquement** rattaché au SID principal de la ligne
DAGSTAR, jamais au `assoc`. La structure est asymétrique : la paire est
représentée d'un seul côté.

### Découverte de la partition stricte daget × source

Le croisement des investigations a révélé une partition parfaite :

| daget | Côté | Type de LID | n |
|-------|------|-------------|---|
| F | astérisque | libellé systématique | 269 |
| G | astérisque | libellé systématique | 263 |
| H | astérisque | **descripteur dédié** | 440 |
| S | dague | libellé systématique | 37 |
| T | dague | libellé systématique | 56 |
| U | dague | **descripteur dédié** | 278 |

**Aucun chevauchement.** Le champ `daget` détermine entièrement le type
de LID :
- H et U sont les niveaux "riches" : descripteur clinique spécifique de
  la combinaison
- F, G, S, T sont les niveaux "pauvres" : libellé systématique sans
  contenu nouveau

### Investigation approfondie des 625 LID source=S

Sur les LID systématiques (source=S, 458 LID uniques pour 625 lignes
DAGSTAR), on a constaté :
- Distribution par `daget` : F (269), G (263), T (56), S (37)
- Distribution par type de code : type=S (534), type=K (91)
- Distribution par level : level 4 (452), level 5 (93), level 3 (80)

**Observation marquante** : certains LID systématiques sont référencés
par un grand nombre de paires DAGSTAR. Exemples :
- G63.3 ("polynévrite au cours d'autres maladies classées ailleurs") :
  **34 paires**
- M82.1 ("ostéoporose au cours de maladies endocriniennes") : 18 paires
- M36.3 ("arthropathie au cours d'autres maladies systémiques") : 11 paires

Ce sont des codes astérisque "fourre-tout" qui s'utilisent avec de
nombreux dagues étiologiques. Dans le CSV actuel, leur libellé
systématique est dupliqué autant de fois qu'il y a de paires.

### Découverte du cas `assoc=0`

Pour les daget F et S (non pointés), `assoc=0` est fréquent. Cela
signifie "pas de code apparié fixe". Exemples : L62 "maladies des ongles
au cours d'autres maladies classées ailleurs" (daget=F, assoc=0) — c'est
un code astérisque générique qui s'utilise avec n'importe quel dague
étiologique.

---

## 4. Reformulation du modèle DAGSTAR

Avec les investigations, on peut maintenant reformuler proprement la
sémantique de DAGSTAR :

### Structure d'une ligne DAGSTAR

```
(SID, LID, assoc, daget, plus)
```

- `SID` : code principal de la ligne
- `LID` : pointeur vers un libellé de la table LIBELLE (systématique si
  source=S, descripteur si source=D)
- `assoc` : code apparié (0 si pas de code fixe — cas non pointés F/S)
- `daget` : niveau et rôle (F/G/H astérisque, S/T/U dague)
- `plus` : flag dont le sens exact reste à clarifier

### Trois catégories de lignes DAGSTAR

**Catégorie A — Paires "pointées" avec descripteur dédié (daget H/U, 718 lignes)**

Le LID est un descripteur clinique spécifique de la combinaison
(ex : "méningite leptospirose" pour G01+A27). Le `assoc` pointe vers un
vrai code apparié. **Information sémantique riche.**

**Catégorie B — Paires "pointées" sans descripteur dédié (daget G/T, 319 lignes)**

Le LID est le libellé systématique du code. Le `assoc` pointe vers un
vrai code apparié. **Information de couplage utile mais sans formulation
clinique dédiée.**

**Catégorie C — Codes "non pointés" (daget F/S, 306 lignes)**

Le LID est le libellé systématique du code. `assoc=0` : pas de code
apparié fixe. **Le code est de nature dague/astérisque générique, sans
paire précise.**

---

## 5. Pivot conceptuel

### Le constat initial

Stéphane a observé : "L'information de couplage dague/astérisque est par
nature une **propriété du scénario clinique**, pas d'un code isolé."

Cette reformulation a recadré la réflexion : si on encode l'info de
paire au niveau du code (dans le CSV), on duplique inutilement parce
que la même information de paire apparaît sur les deux codes (chaque
note de A01.0 répétée pour signaler la paire avec G01, et chaque note
de G01 répétée pour signaler la paire avec A01.0).

### Approche alternative proposée

Au lieu de "DAGSTAR pilote la génération du CSV" (jointure cartésienne
notes × paires), on inverse : "DAGSTAR est une source d'enrichissement
optionnel". Le CSV est construit à partir des libellés / descripteurs /
inclusions utiles, et DAGSTAR n'ajoute qu'une information minimale au
niveau du code.

### Cohérence avec les objectifs initiaux

Rappel des objectifs initiaux du projet : "construire un CSV qui apporte
de l'information complémentaire au modèle afin de mieux comprendre les
maladies couvertes par le code".

Les associations dague/astérisque sont un **plus** dans ce cadre, pas un
fondement. Pour les cas où le LID DAGSTAR est un libellé systématique
(catégories B et C), DAGSTAR n'apporte rien au CSV. Pour les cas où
c'est un descripteur dédié (catégorie A), le descripteur est déjà dans
le CSV via la table DESCR (étiqueté `synonyme`).

**Conclusion** : DAGSTAR n'enrichit pas sémantiquement le CSV au-delà
de ce que LIBELLE/DESCR/INCLUDE apportent déjà. L'information de
couplage doit migrer ailleurs.

### Séparation des responsabilités

- **CSV principal `inclusions_exclusions_synonymes.csv`** : répond à
  "que sait-on sur ce code ?" (libellé, inclusions, exclusions,
  synonymes, propagations). Pas d'info détaillée des paires.
- **Table `dagger_asterisk.parquet`** : source unique pour le détail
  des paires (codes appariés, niveaux, descripteurs cliniques,
  redundancy_level). Utilisable par les consommateurs en aval
  (notamment `recode-scenario` pour l'analyse de scénarios cliniques).
- **L'analyseur de scénario** (futur, dans `recode-scenario`) :
  répond à "comment coder ce scénario clinique ?" en consultant le
  CSV et la table DAGSTAR.

---

## 6. Décisions de design

### Décision 1 — Suppression de l'expansion par paire

**Acté** : la fonction `_attach_dagger_asterisk_columns` est supprimée
du pipeline. Chaque note d'un code apparaît une seule fois dans le CSV,
indépendamment du nombre de paires dague/astérisque auxquelles ce code
participe.

**Impact volumétrique attendu** :
- A01.0 : 108 lignes → environ 36 lignes
- G01 : 192 lignes → environ 16 lignes
- CSV global : ~215 000 lignes → estimation 150-180k (à mesurer
  empiriquement au build)

### Décision 2 — Schéma du CSV : passage de 11 à 9 colonnes

**Colonnes supprimées** :
- `dagger_code`
- `asterisk_code`
- `redundancy_level`
- `is_redundant_dagger`

**Colonnes ajoutées** :
- `is_dagger_in_pair` (bool)
- `is_asterisk_in_pair` (bool)

**Sémantique finale des flags** :
- `is_dagger_in_pair = True` si le code apparaît dans DAGSTAR avec
  daget ∈ {S, T, U} (rôle de dague, peu importe que la paire soit
  pointée ou non)
- `is_asterisk_in_pair = True` si le code apparaît dans DAGSTAR avec
  daget ∈ {F, G, H} (rôle d'astérisque)
- Les deux peuvent être True simultanément (cas rare où le code joue
  les deux rôles)

**Note sur le choix de la sémantique large** : on avait initialement
envisagé d'exclure les cas non pointés (daget F/S) des flags, par
analogie avec la politique précédente qui les excluait du CSV. Mais
dans la nouvelle approche (flags booléens et non plus expansion par
paire), cette exclusion n'a plus de sens — un code générique L62 ou
G94 participe bien à la mécanique dague/astérisque, le signal est
utile au consommateur.

### Décision 3 — Conservation de la table DAGSTAR enrichie

**Acté** : `dagger_asterisk.parquet` reste un livrable du pipeline
`recode-icd`. Il continue à porter :
- Une ligne par paire unique avec codes et libellés des deux côtés
- `levels_present` : sous-ensemble de {F, G, H, S, T, U}
- `combination_labels` : formulations cliniques observées
- `redundancy_level` : alimenté par la curation manuelle
- `source_lids` : LID OFS contribuant à l'association

**Usage prévu** : consommation par `recode-scenario` (et autres
consommateurs futurs) pour l'analyse de scénarios cliniques.

### Décision 4 — Conservation de la curation manuelle

**Acté** : `dagger_curation.csv` continue d'exister et d'être consommé
par le merger. La règle `redundancy_level=subordinate` est désormais
appliquée **uniquement à la table DAGSTAR enrichie**, pas au CSV
principal. Les 163 paires curées restent pertinentes.

### Décision 5 — Méthode de conduite du chantier

**Acté** : doc d'abord, code ensuite (comme tous les chantiers
précédents). Patches appliqués dans l'ordre :
1. `docs/source_mapping.md` — référence absolue de construction
2. `docs/csv_usage_guide.md` — guide consommateur
3. `CLAUDE.md` — doc projet pour Claude Code
4. Le présent récap de session
5. Plus tard : chantier d'implémentation

---

## 7. Patches de documentation appliqués

### Patch 1 — `docs/source_mapping.md`

**10 remplacements appliqués** :

1. Ajustement de la ligne dague/astérisque dans la table de
   correspondance maître (mention "table dédiée hors CSV principal")
2. Refonte complète de la section "Couples dague/astérisque" :
   - Ajout de la colonne "Type de LID référencé" dans la table des
     niveaux daget
   - Nouvelle sous-section "Mécanique relationnelle dans DAGSTAR"
   - Nouvelle sous-section "Politique de représentation dans le CSV
     final" avec justification
   - Sous-section "Pas d'expansion par paire dans le CSV"
3. Refonte de la table "Schéma final du CSV principal" (passage à 9
   colonnes)
4. Mise à jour de la phase 3 du séquencement (suppression des mentions
   des colonnes obsolètes)
5. Actualisation de la sous-section "Dague/astérisque — audit de
   cohérence"
6. Actualisation de la sous-section "Codes post-2006" (flags
   `is_dagger_in_pair` / `is_asterisk_in_pair`)
7. Clarification de la section "Merger" (curation appliquée à la table
   DAGSTAR enrichie uniquement)
8. Précision sur `has_dagger_asterisk` dans le rapport
   `post_2006_codes.csv`
9. Mise à jour de la sous-section "Consommation par le merger" du
   fichier de curation
10. Actualisation de la description du rapport `curation_applied.csv`

### Patch 2 — `docs/csv_usage_guide.md`

**5 remplacements appliqués** :

1. Date de dernière révision : 2026-05-28 → 2026-05-30 (refonte
   dague/astérisque)
2. Section 2 (schéma) : 11 → 9 colonnes, refonte de la table
3. Section 5 (couples dague/astérisque) : refonte complète en 3
   sous-sections (flags / table DAGSTAR enrichie / justification du
   pivot)
4. Section 6 : ajustement du titre "colonnes 10-11" → "colonnes 6-7"
5. Section 8 : reformulation de la recommandation sur les couples
   subordinate (renvoi vers `dagger_asterisk.parquet`)

### Patch 3 — `CLAUDE.md`

**6 remplacements appliqués** :

1. Section "Objectifs métier" (point 1) : passage à 9 colonnes, liste
   des colonnes mise à jour
2. Section "Objectifs métier" (point 2) : reformulation pour clarifier
   que `dagger_asterisk.parquet` est la source unique pour le détail
   des paires
3. Section "Structure du projet" : commentaire sur `flat_csv.py` (11 →
   9 colonnes)
4. Section "Couples dague/astérisque" : refonte de la synthèse
5. Section "Codes post-2006" : actualisation de la mention sur les
   associations dague/astérisque
6. Section "Conventions de code" : précision sur le code témoin
   A17.8/G05.0

---

## 8. Plan d'implémentation (à venir)

L'implémentation se fera dans une session dédiée. Liste des chantiers
identifiés :

### Code du pipeline

- **`src/recode_icd/exporters/flat_csv.py`** :
  - Suppression de la fonction `_attach_dagger_asterisk_columns`
  - Ajout du calcul de `is_dagger_in_pair` et `is_asterisk_in_pair`
    via jointure simple avec la table DAGSTAR

- **`src/recode_icd/loaders/schemas.py`** (ou équivalent) :
  - Mise à jour de `FlatCsvSchema` : passage à 9 colonnes
  - Suppression des champs obsolètes
  - Ajout des deux flags booléens

- **`src/recode_icd/merge.py`** :
  - Vérifier que la curation `dagger_curation.csv` est désormais
    consommée uniquement pour la table DAGSTAR enrichie
  - Plus de propagation de `is_redundant_dagger` dans le CSV principal

- **`src/recode_icd/relations/dagger_asterisk.py`** :
  - Inchangé probablement (la table enrichie reste produite comme avant)
  - À vérifier qu'aucune dépendance n'a été cassée

### Tests

- **Tests de régression touchant les colonnes supprimées** : à adapter
- **Nouveaux tests** sur les flags `is_dagger_in_pair` et
  `is_asterisk_in_pair` (codes témoins : A01.0, G01, A18.1, N33.0,
  E10.2)
- **Test de non-régression volumétrique** : vérifier que la suppression
  de l'expansion ne fait pas chuter la volumétrie au-delà de ce qui
  est attendu (le CSV ne doit pas perdre de notes, juste arrêter de les
  dupliquer)

### Régénération

- Régénérer `inclusions_exclusions_synonymes.csv`
- Régénérer `reports/csv_stats.md` via `recode-icd build stats`
- Vérifier que `reports/curation_applied.csv` est correct (cf
  modifications de la doc)

### Codes témoins à valider après implémentation

| Code | Attendu après refonte |
|------|----------------------|
| A01.0 | ~36 lignes (au lieu de 108), `is_dagger_in_pair=True`, `is_asterisk_in_pair=False` |
| G01 | ~16 lignes (au lieu de 192), `is_dagger_in_pair=False`, `is_asterisk_in_pair=True` |
| A18.1 | `is_dagger_in_pair=True`, `is_asterisk_in_pair=False` |
| N33.0 | `is_dagger_in_pair=False`, `is_asterisk_in_pair=True` |
| E10.2 | `is_dagger_in_pair=True`, `is_asterisk_in_pair=False` |
| U07.1 | `is_dagger_in_pair=False`, `is_asterisk_in_pair=False` (code post-2006 sans paire DAGSTAR) |
| A52.7 | Reste un code-fourre-tout (mais sans duplication par paire) |

---

## 9. Chantiers identifiés pour les prochaines sessions

### Chantier 2 — Problème 2 : notes ANS étiquetées synonyme à tort

**Symptômes observés** (rappel) :
- D21.6 "Tronc" — note de localisation anatomique étiquetée comme
  synonyme alors que c'est une précision de localisation
- M01.08 "Arthrite méningococcique [A39.8]" — formulation typique d'une
  inclusion ANS (avec code dague entre crochets) étiquetée comme
  synonyme

**Hypothèse de cause** : l'ANS ne distingue pas inclusions et synonymes
via ses propriétés RDF (`xkos:inclusionNote` peut contenir les deux
types de contenu). Notre loader OWL/ANS étiquette par défaut tout
`xkos:inclusionNote` comme `INCLUSION`, mais inversement, certains
contenus dans d'autres propriétés (comme `skos:altLabel`) peuvent être
des inclusions implicites avec code entre crochets.

**Pistes d'investigation pour la prochaine session** :

1. **Diagnostic empirique** :
   - Combien de lignes ANS sont actuellement étiquetées `synonyme` dans
     le CSV ?
   - Combien d'entre elles contiennent un code entre crochets (signal
     fort d'inclusion ANS) ?
   - Combien correspondent à des notes anatomiques (D21.6 "Tronc",
     etc.) ?
   - Y a-t-il des patterns systématiques (par chapitre, par bloc) ?

2. **Inspection du loader OWL/ANS** (`src/recode_icd/loaders/owl.py`) :
   - Quel mapping est appliqué exactement à `xkos:inclusionNote`,
     `skos:altLabel`, `xkos:exclusionNote` ?
   - Pour les codes problématiques (D21.6, M01.08), retracer d'où vient
     l'étiquette `synonyme`

3. **Heuristiques possibles pour réétiqueter** :
   - Présence de code entre crochets `[X##.#]` → inclusion (forte
     signal)
   - Structure préfixée (`au cours de`, `dû à`, etc.) → potentielle
     inclusion
   - Localisation anatomique pure (mots clés `tronc`, `membre`,
     `région`) → potentiellement à reclasser

4. **Décision de politique** :
   - Réétiqueter automatiquement via heuristique
   - Filtrer ces entrées du CSV
   - Laisser tel quel et documenter le piège
   - Combinaison (par exemple : heuristique forte pour les codes entre
     crochets, et tolérance pour le reste)

**Indépendance fonctionnelle** : le chantier 2 ne dépend pas du
chantier 1. Il peut être traité avant ou après l'implémentation de la
refonte dague/astérisque. Recommandation : finir l'implémentation du
chantier 1 d'abord pour éviter d'empiler deux refontes en parallèle.

### Autres pistes ouvertes

- **Sens du champ `plus`** (DAGSTAR) : n'a pas été élucidé dans cette
  session. Apparaît principalement à 0, parfois à 1. Pourrait porter
  une information sémantique (cas particuliers, anomalies) à
  investiguer si le besoin se présente.

- **LID 13911 orphelin** : un seul LID DAGSTAR n'est référencé dans
  aucune autre table (LIBELLE, DESCR, INCLUDE, EXCLUDE). À investiguer
  si pertinent — probablement un cas particulier sans impact pratique.

---

## 10. Codes témoins et fichiers de référence

### Codes témoins ajoutés ou consolidés

| Code | Rôle |
|------|------|
| A01.0 | Cas de duplication ×3 (3 paires dague/astérisque) — fil rouge du diagnostic |
| G01 | Cas extrême de duplication ×12 (12 paires côté astérisque) |
| A18.1 | Couple subordinate avec N33.0 (10 paires DAGSTAR, fil rouge du walkthrough) |
| A17.0 | Couple subordinate tuberculose-méningite |
| A27 | Code dague pour la paire-test G01+A27 |
| A52.7 | Code-fourre-tout (~2478 notes), test de non-régression volumétrique |
| L62 | Code astérisque non pointé (daget=F, assoc=0) |
| G63.3 | Cas de LID systématique référencé par 34 paires |
| D21.6 | Cas problème synonyme/inclusion (problème 2, non traité) |
| M01.08 | Cas problème synonyme/inclusion avec code entre crochets (problème 2, non traité) |
| U07.1 | Code post-2006 (COVID), pas de paire DAGSTAR attendue |

### Fichiers de référence du projet impactés

| Fichier | Statut après cette session |
|---------|---------------------------|
| `docs/source_mapping.md` | Patché (10 remplacements) |
| `docs/csv_usage_guide.md` | Patché (5 remplacements) |
| `CLAUDE.md` | Patché (6 remplacements) |
| `docs/sessions/2026-05-30_refonte_dagger_asterisk.md` | Créé (le présent fichier) |
| `src/recode_icd/exporters/flat_csv.py` | À modifier (chantier d'implémentation) |
| `src/recode_icd/loaders/schemas.py` | À modifier (chantier d'implémentation) |
| `src/recode_icd/merge.py` | À vérifier / ajuster |
| `referentials/processed/dagger_asterisk.parquet` | Inchangé (reste un livrable) |
| `referentials/curation/dagger_curation.csv` | Inchangé (reste consommé par le merger) |
| `inclusions_exclusions_synonymes.csv` | À régénérer après implémentation |
| `reports/csv_stats.md` | À régénérer après implémentation |

---

## 11. Méthodologie : ce qui a bien fonctionné

Ce récap se termine par quelques observations méthodologiques pour les
sessions futures :

- **Le mode `verbose=True` de `inspect_code()`** s'est révélé central
  pour le diagnostic. L'ajout du BLOC 2bis (tables brutes) et du BLOC 5
  (traçage inter-étapes) a permis de localiser précisément le bug
  d'expansion. Sans cet outil, le diagnostic aurait pris beaucoup plus
  de temps.

- **L'investigation empirique avant la décision** : les trois
  investigations Python sur DAGSTAR (couverture, distribution source,
  position du LID) ont quantifié le problème et révélé la partition
  stricte daget × source. Cette partition n'aurait pas été identifiée
  par simple lecture du PDF officiel.

- **Le PDF officiel OFS** (`Version_V2B004_update_.pdf`) a été décisif
  pour comprendre la mécanique relationnelle DAGSTAR-LIBELLE. La doc
  officielle reste la meilleure source quand le schéma relationnel
  n'est pas évident.

- **Le pivot conceptuel "propriété du scénario, pas du code"** a
  débloqué la décision. Avant ce pivot, on cherchait à corriger
  localement le bug d'expansion ; après, on a vu qu'il fallait
  questionner la place même de l'information dans le CSV.

- **La méthode "doc d'abord, code ensuite"** continue de prouver sa
  valeur. Forcer la rédaction des patches de doc avant l'implémentation
  oblige à expliciter les décisions et révèle souvent des incohérences
  ou des manques. C'est aussi ce qui rend les sessions de Claude Code
  reproductibles.

- **La discussion préliminaire avant la rédaction** : pour le récap
  comme pour les patches, prendre le temps de questionner et reformuler
  ensemble avant de produire le document final a permis d'éviter
  plusieurs erreurs (par exemple : la définition initiale trop
  restrictive des flags qui excluait les non pointés, corrigée après
  challenge).
