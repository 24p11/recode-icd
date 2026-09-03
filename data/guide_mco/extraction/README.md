# Candidates du pilote — registre de curation

> **VERSÉ le 2026-08-17.** Les 85 consignes et 171 associations de ce
> répertoire sont dans `../recommendations_curated.csv` et
> `../recommendation_codes_curated.csv`. Ce qui reste ici est la
> justification — quelle citation soutient quelle ligne — conservée au
> même titre qu'une relecture remplie.
>
> **Ce répertoire est une trace de curation, pas une entrée du
> pipeline.** Le build ne lit que `data/guide_mco/*_curated.csv`. Ce
> qu'on garde ici, c'est la justification : quelle citation soutient
> quelle ligne, et quel arbitrage a été rendu.

## Organisation

| Fichier | Rôle |
|---|---|
| `candidates_recommendations.csv` | **source unique** — les consignes, avec leur citation |
| `candidates_recommendation_codes.csv` | **source unique** — les associations (rôle, centralité) |
| `candidates_<article>.md` | **généré** par `scripts/rendre_candidates_guide_mco.py` |

Les markdown ont d'abord été rédigés à la main, tables de rôles
comprises. C'est le schéma exact qui a produit l'incident ORPHANET du
chantier `chapter_policy` — deux énumérations de la même information,
maintenues séparément, qui divergent sans que personne l'ait décidé. Les
CSV font foi et les markdown sont régénérés.

## Volumétrie

**85 consignes, 171 associations**, sur 169 expressions distinctes —
toutes parsables, toutes résolues contre `merged_codes.parquet`.

| Article | Consignes |
|---|---|
| Chapitre XXI | 55 |
| Malnutrition, dénutrition | 15 |
| AVC (compléments) | 14 |
| Anémie posthémorragique D62 (complément) | 1 |

## Arbitrages rendus (RF, 2026-08-14)

1. **`interdit_DAS` créé.** Cinq consignes du chapitre XXI interdisent
   la position de diagnostic associé (redondance avec un acte CCAM), et
   aucun rôle existant ne convenait : `interdit` dirait le code proscrit
   — or `Z43.–` reste le DP légitime d'une fermeture de stomie ;
   `interdit_association` désigne une autre cible CIM-10, or l'autre
   terme est un acte CCAM, absent du référentiel.
2. **`regi` créé, `contexte` restreint.** `regi` = « la consigne régit
   l'emploi de ce code — elle le prescrit, le conditionne ou le décrit —
   sans lui assigner de position ». `contexte` = « le code délimite la
   situation, la consigne ne régit pas son emploi ». Avant la scission,
   `contexte` faisait les deux métiers et devenait majoritaire.
   Après migration : **62 `regi` contre 2 `contexte`** — l'ampleur du
   déséquilibre confirme après coup que le rôle unique était intenable.
3. **Doctrine d'extraction gravée** : on n'associe une expression que si
   la consigne régit son emploi ou le positionne ; les mentions de
   passage restent dans le `texte`. Appliquée à XXI-03 (chapitre XVIII
   non associé) et XXI-16 (chapitres I et XVIII non associés) — soit
   ~2 700 fiches épargnées pour des mentions dont l'une est dans un
   simple exemple.
4. **Seuils biologiques admis** : `D62-03` et les sept `definition` de
   dénutrition (`DEN-10` à `DEN-16`). Justification : les fiches servent
   la génération **et** la vérification, et les critères sont ce qui
   atteste le code dans un compte rendu. Sans eux, la fiche E43 enseigne
   le code mais pas ce qui le justifie, et un générateur produirait des
   dénutritions sans chiffres.
5. **E44.1** : aucune ligne. Divergence consignée dans
   `../hors_perimetre.md`.
6. **DEN-07 non généralisée** : le guide place la règle « le sévère
   prime » dans la seule section adulte 18-70 ans. La portée reste
   celle du texte, et la restriction est écrite dans la `condition`.
7. **DEN-01/02/03 non fusionnées** : même texte de consigne, mais
   conditions distinctes (les critères diffèrent selon l'âge). Fusionner
   aurait obligé à empiler trois jeux de critères dans une condition
   unique.

8. **Portée `chaque` / `ensemble` créée** (RF, 2026-09-02, après merge
   du pilote — cas AVC-14/Z23.0). La résolution suppose la portée
   « pour tout » : une expression qui n'est que le **domaine d'un
   choix** (« le DP appartient au chapitre XXI ») doit être déclarée
   `portee=ensemble` — jamais résolue vers les feuilles, jamais
   restreinte par interprétation à une liste de codes que le guide n'a
   pas écrite. **Critère de partage, à appliquer dès la grille des
   candidates du chantier B : qui fait le choix entre les membres de
   l'expression ?** L'état du patient (chaque membre est régi quand il
   est le diagnostic) → `chaque` (défaut, colonne vide). Un élément
   extérieur à l'expression (motif de séjour, situation) → `ensemble`,
   avec justification obligatoire. Les interdictions sont des « pour
   tout » par nature. Paire d'exemples : AVC-01 (`chaque`) vs AVC-14
   (`ensemble`). Revue du pilote faite le même jour : AVC-14/XXI seule
   basculée ; AVC-01, AVC-04, AVC-06, AVC-12 (plages de l'affection
   même) et XXI-49 (interdiction) restent `chaque`.

9. **Plage à borne absente du nested set : erreur au rapport, pas de
   résolution élargie** (RF, 2026-09-03, cas OMS-01/`U00-U49`). La
   résolution d'une plage exige l'existence de ses deux bornes ;
   `U00` n'existe pas — le chapitre XXII est clairsemé par conception.
   On n'étend pas la résolution aux plages creuses : mécanisme sans
   valeur actuelle (la consigne atteint les fiches U07 par sa seconde
   association), on réinstruit si un second cas apparaît **avec une
   perte réelle**. L'expression part au rapport
   `guide_mco_expressions_non_resolues.csv`, jamais au silence —
   invariant verrouillé par test de régression.

10. **Attribut `rendu_fiche` (oui|non, défaut oui) au niveau de la
    consigne** (RF, 2026-09-03, cas ANT-01). Les consignes de très
    large portée sont du bruit dans les fiches de **génération** —
    utiles à la base et au futur vérificateur, pas au rédacteur de
    CRH. Critère de bascule : « aide le rédacteur de CRH » (rendue)
    vs « aide seulement le contrôleur » (non rendue). Le niveau
    consigne, et non association, est retenu : le critère porte sur le
    contenu de la consigne, pas sur ses cibles, et une consigne « à
    moitié rendue » serait illisible. `rendu_fiche=non` exige une
    justification datée ; le build liste ces consignes dans
    `guide_mco_consignes_non_rendues.csv` et le rendu des fiches
    filtre dessus. Première bascule : ANT-01.

11. **Un code convoqué pour comparaison ou analogie n'est ni `sujet`
    ni `exemple`** (RF, 2026-09-03, cas HYP-02/I10 et R03.0). « La même
    argumentation conduit à distinguer I10 et R03.0 » compare la
    consigne à un couple voisin : ces codes sont des objets de
    comparaison, pas des instances de ce que la consigne régit —
    mention de passage (précédent XXI-03), l'analogie reste dans le
    `texte`. `centralite=exemple` est réservé aux codes cités comme
    instances de la consigne elle-même.

## Points laissés ouverts

- **`GM2026-V-AVC-18`** (complications codées en DAS) n'a **aucune
  association** : le guide n'y donne que des libellés en clair
  — « inhalation, épilepsie, escarre, démence vasculaire » — sans code.
  Leur en attribuer supposerait de choisir des cibles que le texte ne
  nomme pas. La consigne sera donc listée au rapport de build sous
  `guide_mco_recommandations_sans_code.csv`, et c'est **normal**.
- **Obligation vs permission.** Le guide distingue « le DP **est codé**
  X » de « X **peut** être codé en DP » ; le modèle écrase les deux sur
  `DP`. Sans conséquence pour la génération, gênant pour
  recode-scenario, qui voudrait savoir si une contrainte est dure. À
  verser au backlog, pas à traiter dans ce chantier.
