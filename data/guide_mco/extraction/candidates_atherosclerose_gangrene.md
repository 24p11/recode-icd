# Candidates — ATHEROSCLEROSE AVEC GANGRENE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/atherosclerose_gangrene.md`
> (guide chap. V, pp. imprimées 83). Les `L…` y renvoient.

**1 consignes, 2 associations**.

---

## Consignes nouvelles

### GM2026-V-ATH-01 — `regle_association`

**Situation** : Athérosclérose avec gangrène — I70.21 en DP et codage de la gangrène

**Texte** : I70.21 Athérosclérose des artères distales, avec gangrène comporte intrinsèquement la notion de gangrène : utilisé en DP, il ne devrait pas permettre de codage supplémentaire de la gangrène (note d'exclusion de R02 au volume 1 : « à l'exclusion de gangrène au cours d'athérosclérose (I70.2) »). Toutefois, à titre d'exception, l'emploi de R02 en diagnostic associé lorsque I70.21 est codé en DP est autorisé : c'est actuellement le seul moyen de discriminer les prises en charge avec gangrène lors du groupage en GHM.

**Condition** : —

**Citation** (`atherosclerose_gangrene.md` L10) :
« Le code I70.21 Athérosclérose des artères distales, avec gangrène comporte intrinsèquement la notion de gangrène. […] la note accompagnant le code R02 Gangrène non classée ailleurs dans le volume 1 de la CIM-10 précise que ce code est à utiliser « à l’exclusion de gangrène au cours d’athérosclérose (I70.2). ». Toutefois, à titre d’exception, l’utilisation en diagnostic associé, du code R02 lorsque I70.21 est codé en DP, est autorisée. En effet, porter le code R02 en diagnostic associé est actuellement le seul moyen de discriminer les prises en charge avec gangrène lors du groupage en GHM. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I70.21` | `regi` | sujet | chaque |  |
| `R02` | `DAS` | sujet | chaque | I70.21 codé en DP |

