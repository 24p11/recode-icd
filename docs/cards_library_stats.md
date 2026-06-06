# Bibliothèque de fiches CIM-10 — Statistiques de référence

> Document de référence sur le contenu de `outputs/cards_library/`,
> généré par `recode-icd cards build`. Dernière mise à jour : 2026-06-06.

---

## Vue d'ensemble

| Mesure | Valeur |
|---|---|
| Codes feuilles | 15 978 |
| Sous-dossiers (chapitres romains) | 22 (I à XXII) |
| Temps de génération | 110 s (~6,9 ms/fiche) |
| Erreurs lors de la génération | 0 |
| Volume markdown total | 22,6 Mo |
| Taille médiane d'une fiche | 1 398 caractères |
| Taille maximale d'une fiche | 4 785 caractères |

La bibliothèque est régénérée à la demande. Elle n'est pas versionnée
(cf. `.gitignore`), seul `_index.csv` est conservé comme inventaire.

## Distribution par chapitre

Top 5 chapitres en volume :

| Chapitre | Description | n | % |
|---|---|---|---|
| XIII | Musculo-squelettique | 4 866 | 30,5 % |
| XIX | Traumatismes | 1 444 | 9,0 % |
| XX | Causes externes | 1 350 | 8,4 % |
| V | Troubles mentaux | 1 060 | 6,6 % |
| I | Maladies infectieuses | 793 | 5,0 % |

Le chapitre XIII pèse à lui seul près d'un tiers du volume total,
conséquence de la combinatoire des 5e positions anatomiques (10
positions × ~500 sous-catégories).

Les 5 plus gros chapitres représentent ~60 % du volume total.

## Présence des sections

Section conditionnellement présente selon le code :

| Section | n | % | Commentaire |
|---|---|---|---|
| Position dans la classification | 15 978 | 100 % | Universel |
| À ne pas décrire | 15 593 | 97,6 % | Quasi-universel (exclusions héritées) |
| Périmètre clinique | 10 436 | 65,3 % | Descripteurs et inclusions héritées |
| Formulations cliniques alternatives | 7 523 | 47,1 % | Entrées Index CIM-10 + AP-HP |
| Localisations anatomiques | 2 280 | 14,3 % | Exclusif aux codes type=D du chapitre XIII |

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
