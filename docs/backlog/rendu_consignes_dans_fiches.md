# Backlog — Rendu des consignes du guide MCO dans les fiches (chantier fiches)

> Statut : **partiellement traité**. Ouvert le 2026-09-02 à la clôture
> du chantier A ; le chantier fiches du 2026-09-03
> (`feat/cards-recommandations`) a implémenté l'insertion dans
> `cards.py`, l'affichage de la `situation` sur les règles de chapitre
> et le rendu des `exemple` en bloc cité. Restent ouverts le plafond
> par fiche et les conditions par code (ci-dessous).

## ✅ Traité le 2026-09-03 — situation, exemples, insertion

- **Insertion de la section dans `cards.py`** : section « Consignes de
  codage » entre « À ne pas décrire » et « Formulations »,
  implémentation dans `recode_icd/recommendations/rendu.py`, prototype
  du notebook remplacé (il importe désormais `src/`).
- **`situation` affichée** entre parenthèses sur les règles générales
  de chapitre — le cas d'école Z23.0/GM2026-V-XXI-01 est un témoin de
  régression. (GM2026-V-AVC-14, l'autre cas d'école, est depuis
  l'amendement `portee` une association `ensemble` jamais résolue.)
  La situation des consignes **non**-chapitre n'est pas rendue — à
  rouvrir si la relecture des fiches en montre le besoin.
- **Rendu des `centralite = exemple`** : bloc cité `>` introduit par
  « À titre d'exemple dans le guide : », entre les consignes sujet et
  les règles générales. À la dédup, `sujet` prime sur `exemple`
  (témoin Z20.1). Témoin « exemple seul » : F01.000.

## Points restant ouverts

- **Plafond de consignes par fiche** — mécanisme analogue à R2 de la
  `chapter_policy` (note de conception §4.3). E43 rend aujourd'hui
  12 consignes, c'est le haut de la distribution observée ; aucun
  plafonnement tant que la relecture n'en montre pas la nécessité.
- **Rendu des conditions par code** — la colonne `condition` de
  l'association, plus fine que celle de la consigne (ex. AVC-06 :
  `I60-I64` « phase initiale » vs `I69` « phase séquellaire »).
- **Fiches catégories** — `recommendation_codes` ne porte que des
  feuilles ; `build_category_card` ne rend pas de section Consignes.
  À trancher avec les profils de fiches
  (`docs/backlog/profils_fiches_par_usage.md`).

Les règles déjà actées par le prototype (filtre `sujet`, exclusion de
`contexte`, tri par spécificité via `cle_de_tri`, regroupement des
règles de chapitre, préfixe `[rec_id]`, déduplication au niveau le plus
spécifique) sont la base de départ du chantier, pas des questions
ouvertes.
