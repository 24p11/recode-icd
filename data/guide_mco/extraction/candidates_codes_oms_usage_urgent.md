# Candidates — CODES OMS RÉSERVÉS A UN USAGE URGENT

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/codes_oms_usage_urgent.md`
> (guide chap. V, pp. imprimées 84). Les `L…` y renvoient.

**2 consignes, 3 associations**.

---

## Consignes nouvelles

### GM2026-V-OMS-01 — `condition_emploi`

**Situation** : Codes U00-U49 — réserve OMS pour usage urgent

**Texte** : Les codes U00-U49 sont utilisés par l'OMS pour une attribution provisoire à de nouvelles maladies d'étiologie incertaine. Les 10 codes d'attente des catégories U07 doivent être disponibles dans tous les systèmes électroniques à tout moment et utilisés, sans délai, selon les instructions de l'OMS adaptées au PMSI et publiées sur le site de l'ATIH.

**Condition** : Selon les instructions de l'OMS adaptées au PMSI (site ATIH)

**Citation** (`codes_oms_usage_urgent.md` L10) :
« Les codes U00-U49 sont utilisés par l’OMS pour une attribution provisoire à de nouvelles maladies d’étiologie incertaine. […] l’OMS a retenu 10 codes d’attente dans les catégories U07. Ces catégories et sous-catégories doivent être disponibles dans tous les systèmes électroniques à tout moment et utilisées, sans délai, selon les instructions de l’OMS adaptées au PMSI et publiées sur le site de l’ATIH. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `U00-U49` | `regi` | sujet | chaque |  |
| `U07` | `regi` | sujet | chaque |  |

### GM2026-V-OMS-02 — `interdiction`

**Situation** : Codes d'attente U07 — proscription hors consignes OMS

**Texte** : Les codes d'attente (libellé « Usage urgent de U07 ») sont intégrés à la liste des codes utilisables dans les recueils PMSI, mais en l'absence de consignes spécifiques données par l'OMS leur utilisation est proscrite et conduit à un groupage en erreur. Depuis 2020, les consignes OMS pour les codes en lien avec la crise sanitaire permettent d'utiliser ces codes spécifiques sans groupage en erreur.

**Condition** : Absence de consignes spécifiques données par l'OMS

**Citation** (`codes_oms_usage_urgent.md` L10) :
« Ces codes, dont le libellé d’attente est Usage urgent de U07 sont intégrés à la liste des codes utilisables dans les recueils PMSI. Cependant, en l’absence de consignes spécifiques données par l’OMS, leur utilisation est proscrite et conduit à un groupage en erreur. En 2020, les consignes OMS données pour les codes en lien avec la crise sanitaire permettent d’utiliser ces codes spécifiques, sans groupage en erreur. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `U07` | `interdit` | sujet | chaque | absence de consignes spécifiques données par l'OMS |

