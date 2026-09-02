# Backlog — Rendu des consignes du guide MCO dans les fiches (chantier fiches)

> Statut : **à instruire**. Ouvert le 2026-09-02, à la clôture du
> chantier A, sur validation des six démonstrations du prototype
> `scripts/explore/rendu_recommandations_fiches.ipynb`. Ce backlog
> regroupe ce que le prototype a volontairement laissé au chantier
> fiches (celui qui touchera `cards.py`).

## Afficher la colonne `situation` avec les consignes rendues

**Au moins pour les règles de niveau chapitre.** La `situation` borne
le texte de la consigne et transforme une règle apparemment hors sujet
en information de non-application.

Cas d'école, constaté sur la démonstration Z23.0 : GM2026-V-AVC-14
(« s'il n'est pas découvert d'affection nouvelle, le DP appartient au
chapitre XXI ») descend sur toutes les fiches Z, dont la vaccination
anticholérique. Rendue nue, la règle semble hors sujet ; rendue avec sa
situation (« AVC — séjour de surveillance à distance »), elle dit au
lecteur — et au générateur — précisément quand elle ne s'applique pas.
La curation `XXI / DP / sujet` est conforme à la doctrine ; c'est un
raffinement de **rendu**, pas de base.

## Autres points laissés au chantier fiches par le prototype

- **Insertion de la section dans `cards.py`** — le prototype ne touche
  pas aux fiches ; le jour venu, son implémentation est remplacée, pas
  doublée.
- **Plafond de consignes par fiche** — mécanisme analogue à R2 de la
  `chapter_policy` (note de conception §4.3).
- **Rendu des `centralite = exemple`** — exclues par défaut ; se
  tranche avec la question du rendu des exemples du guide (blocs cités
  `>` des curés, convention de transcription et pas encore décision de
  rendu — cf. CLAUDE.md et `docs/backlog/profils_fiches_par_usage.md`).
- **Rendu des conditions par code** — la colonne `condition` de
  l'association, plus fine que celle de la consigne (ex. AVC-06 :
  `I60-I64` « phase initiale » vs `I69` « phase séquellaire »).

Les règles déjà actées par le prototype (filtre `sujet`, exclusion de
`contexte`, tri par spécificité via `cle_de_tri`, regroupement des
règles de chapitre, préfixe `[rec_id]`, déduplication au niveau le plus
spécifique) sont la base de départ du chantier, pas des questions
ouvertes.
