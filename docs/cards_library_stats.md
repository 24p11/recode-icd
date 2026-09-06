# Bibliothèque de fiches CIM-10 — Statistiques de référence

> Document de référence sur le contenu de `outputs/cards_library/`,
> généré par `recode-icd cards build`. Dernière mise à jour :
> 2026-09-05 (chantier couverture ATIH, palier 2 — profils, codes
> intermédiaires codables, codes injectés depuis le kit ATIH).

## État au 2026-09-05 — deux bibliothèques feuilles, par profil

| Bibliothèque | Profil | Fiches | Dont consignes | Durée |
|---|---|---|---|---|
| `outputs/cards_library/` | `generation` — codables MCO seulement | **15 071** | 3 490 | 618 s |
| `outputs/cards_library_controle/` | `controle` — tous les codes | **16 986** | 3 525 | 791 s |
| `outputs/cards_library_categories/` | (non profilée) | 2 054 | — | 125 s |

**15 071 = le nombre de codes autorisés MCO hors chapitre XX** (kit
ATIH 2025) : l'invariant « tout code autorisé hors chapitre XX a une
fiche » est vert (`tests/regression/test_couverture_invariants.py`),
comme son dual « aucun non-codable dans la bibliothèque de génération ».

Répartition par statut MCO (colonne `statut_mco` des `_index.csv`) :

| `statut_mco` | generation | controle |
|---|---|---|
| `codable` | 13 366 | 13 366 |
| `cause_externe` (chap. XX, jamais DP/DR) | 1 188 | 1 188 |
| `interdit_dp_dr` | 441 | 441 |
| `interdit_dp` | 76 | 76 |
| `inconnu_atih` (localisations chap. XIII…) | — | 1 619 |
| `pere_interdit` | — | 217 |
| `supprime` | — | 79 |

Ce qui a changé depuis le 2026-06-08 (16 058 fiches, un seul profil) :

- **D2** — 800 codes intermédiaires codables entrent au CSV maître et
  ont une fiche par héritage (`M00.0`, `F00.0`, `M16.0`…) ;
- **D3** — 59 codes codables sans aucune ligne au CSV ont une fiche
  (titre, position, statut, consignes) ; 72 codes du kit ATIH absents
  de l'ANS sont injectés dans le nested set (`source_existence=ATIH`
  dans l'index) ;
- **D4** — les 1 915 codes non codables (pères interdits, supprimés,
  inconnus du kit) sortent du profil `generation` et restent dans
  `controle` ;
- chaque fiche porte une ligne « Statut MCO (kit ATIH 2025) » sous son
  titre (D1). Durée de génération ≈ 40 ms/fiche (lecture du statut par
  code).

Les sections ci-dessous décrivent la bibliothèque telle qu'elle était
avant ce chantier ; les mesures de couverture des sections restent
indicatives.


---

## Vue d'ensemble

| Mesure | Avant CepiDc (2026-06-06) | Après CepiDc (2026-06-08) |
|---|---|---|
| Codes feuilles | 15 978 | 16 058 |
| Sous-dossiers (chapitres romains) | 22 (I à XXII) | 22 (I à XXII) |
| Temps de génération | 110 s (~6,9 ms/fiche) | 286 s (~17,8 ms/fiche) |
| Erreurs lors de la génération | 0 | 0 |
| Volume markdown total | 22,6 Mo | 24,2 Mo |
| Taille médiane d'une fiche | 1 398 caractères | 1 463 caractères |
| Taille maximale d'une fiche | 4 785 caractères | 5 254 caractères |

La bibliothèque est régénérée à la demande. Elle n'est pas versionnée
(cf. `.gitignore`), seul `_index.csv` est conservé comme inventaire.

L'intégration CepiDc ajoute +80 codes (codes désormais couverts par
au moins une entrée), +7 % de volume markdown, +5 % en taille
médiane. La durée de génération a triplé : surcoût venant de la
section « Formulations cliniques alternatives » qui parcourt plus
d'entrées par code à filtrer/échantillonner.

## Distribution par chapitre

Top 5 chapitres en volume :

| Chapitre | Description | n | % |
|---|---|---|---|
| XIII | Musculo-squelettique | 4 866 | 30,3 % |
| XIX | Traumatismes | 1 444 | 9,0 % |
| XX | Causes externes | 1 350 | 8,4 % |
| V | Troubles mentaux | 1 060 | 6,6 % |
| I | Maladies infectieuses | 793 | 4,9 % |

Le chapitre XIII pèse à lui seul près d'un tiers du volume total,
conséquence de la combinatoire des 5e positions anatomiques (10
positions × ~500 sous-catégories).

Les 5 plus gros chapitres représentent ~60 % du volume total.

## Présence des sections

Section conditionnellement présente selon le code :

| Section | n (avant) | % (avant) | n (après) | % (après) |
|---|---|---|---|---|
| Position dans la classification | 15 978 | 100 % | 16 058 | 100 % |
| À ne pas décrire | 15 593 | 97,6 % | ~15 593 | ~97 % |
| Périmètre clinique | 10 436 | 65,3 % | ~10 436 | ~65 % |
| Formulations cliniques alternatives | 7 523 | 47,1 % | 8 629 | 53,7 % |
| Localisations anatomiques | 2 280 | 14,3 % | 2 280 | 14,2 % |

L'intégration CepiDc fait passer la couverture de la section
« Formulations cliniques alternatives » de 47,1 % à 53,7 % des fiches
(+1 106 codes nouvellement couverts), sans impact sur les autres
sections.

## Apport CepiDc — top 10 codes les plus enrichis (volume avant échantillonnage)

| Code | Libellé | n formulations CepiDc |
|---|---|---|
| C79.8 | Tumeur maligne secondaire d'autres sièges précisés | 1 226 |
| C85.9 | Lymphome non hodgkinien, non précisé | 999 |
| C34.9 | Tumeur maligne de bronche ou du poumon, sans précision | 873 |
| Z92.4 | Antécédents personnels d'intervention chirurgicale importante | 854 |
| Z92.2 | Antécédents personnels d'utilisation (actuelle) à long terme | 825 |
| Y83.1 | Intervention chirurgicale avec implantation d'une prothèse | 770 |
| I77.9 | Atteinte des artères et artérioles, sans précision | 697 |
| I25.1 | Cardiopathie artérioscléreuse | 682 |
| C79.5 | Tumeur maligne secondaire des os et de la moelle osseuse | 649 |
| I67.8 | Autres maladies cérébrovasculaires précisées | 602 |

Ces volumes sont mesurés **avant** l'échantillonnage `INDEX_SAMPLE_SIZE
= 10` appliqué côté fiches feuilles (cf [cards.py:_section_formulations](../src/recode_icd/cards.py)).
La fiche feuille n'affiche jamais plus de 10 entrées CepiDc, mais le
CSV contient toutes les entrées.

## Apport CepiDc — codes ignorés

124 codes CepiDc sont absents du `merged_codes` recode-icd (codes
pré-2006 supprimés par l'ATIH). Détails dans
[`reports/cepidc_ignored.csv`](../reports/cepidc_ignored.csv) avec le
nombre de formulations perdues par code et des exemples. Top du
rapport : R58.09 (528 formulations), I63.59 (477), I21.99 (411), etc.

## Bibliothèque catégories (`outputs/cards_library_categories/`)

Générée par `recode-icd cards build-categories` (75 s).

| Mesure | Valeur |
|---|---|
| Catégories | 2 054 |
| Volume markdown total | 7,0 Mo |
| Taille médiane d'une fiche | 3 265 caractères |
| Taille maximale d'une fiche | 16 173 caractères |
| Plafond formulations cliniques | `CATEGORY_FORMULATIONS_MAX = 50` |

**Notes sur les sections** :
- "Localisations anatomiques" : 2 280 codes correspond exactement
  aux codes type=D, depth=5 du chapitre XIII ayant des inclusions
  atomiques (les ex-altLabel retypés par le chantier 2026-06-06).
- "À ne pas décrire" est universel grâce à la propagation
  hiérarchique des exclusions depuis le chapitre, le bloc et la
  catégorie. Les 2,4 % sans cette section sont des cas particuliers
  (probablement des codes avec un chapitre sans exclusion globale,
  à investiguer si pertinent).
- "Périmètre clinique" inclut depuis 2026-06-06 les inclusions
  héritées des niveaux supérieurs (chapter, block, category).

## Métriques pour budget LLM

Estimations approximatives pour anticiper le coût d'un prompt
contenant plusieurs fiches :

| Métrique | Valeur |
|---|---|
| Fiche médiane | ~1 400 caractères ≈ 350 tokens |
| Fiche maximale | ~4 800 caractères ≈ 1 200 tokens |
| Scénario typique (3-5 codes) | ~1 000-2 000 tokens |
| Scénario riche (10 codes) | ~3 500-5 000 tokens |

À comparer avec la fenêtre contextuelle du modèle LLM cible.

## Structure des fichiers

```
outputs/cards_library/
├── _index.csv  (inventaire versionné)
├── I/   (793 fiches)
├── II/  (...)
├── ...
├── XIII/ (4 866 fiches — plus gros chapitre)
├── ...
└── XXII/ (33 fiches U)
```

## Schéma de `_index.csv`

| Colonne | Type | Description |
|---|---|---|
| `code` | str | Code CIM-10 (ex. `A18.1`) |
| `chapter` | str | Chapitre en notation romaine |
| `filepath` | str | Chemin relatif depuis `outputs/cards_library/` |
| `libelle` | str | Libellé du code |
| `has_perimetre` | bool | Section "Périmètre clinique du code" présente |
| `has_localisations` | bool | Section "Localisations anatomiques" présente |
| `has_exclusions` | bool | Section "À ne pas décrire" présente |
| `has_formulations` | bool | Section "Formulations cliniques alternatives" présente |
| `nb_chars` | int | Nombre de caractères de la fiche |

## Comment régénérer

```bash
# Génération complète
uv run recode-icd cards build

# Filtrage par chapitre
uv run recode-icd cards build --chapter XIII

# Limitation pour test rapide
uv run recode-icd cards build --limit 100

# Wrapper standalone équivalent
uv run python scripts/build_cards_library.py
```

Le notebook
`scripts/explore/2026-06-06_build_cards_library.ipynb` permet une
exploration interactive (inventaire, mesures de performance,
spot-check sur des fiches au hasard).

## Lien avec les chantiers

Cette bibliothèque est le résultat final du **chantier 1** (construction
des données et fiches), qui a couvert :

- Refonte dague/astérisque
- Normalisation crochets ANS → parenthèses
- Prototype de fiche v2 (révision section "À ne pas décrire")
- Retypage `skos:altLabel` → inclusion pour codes type=D chapitre XIII
- Section "Localisations anatomiques" conditionnelle
- Inclusions héritées + harmonisation de l'ordre des sous-sections
- Refactorisation `build_card` dans `src/recode_icd/cards.py`
- Génération massive de la bibliothèque

La bibliothèque est utilisée comme matériau d'entrée pour le
**chantier 2** (construction du prompt LLM pour génération de
comptes-rendus médicaux).
