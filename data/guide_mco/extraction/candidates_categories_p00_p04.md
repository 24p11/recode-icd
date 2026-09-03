# Candidates — EMPLOI DES CATÉGORIES P00 À P04 DE LA CIM–10

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/categories_p00_p04.md`
> (guide chap. V, pp. imprimées 92). Les `L…` y renvoient.

**1 consignes, 2 associations**.

---

## Consignes nouvelles

### GM2026-V-P00-01 — `condition_emploi`

**Situation** : Codes P00-P04 — extension aux soins supplémentaires du nouveau-né

**Texte** : La note d'inclusion du groupe P00-P04 restreint ces codes aux affections maternelles précisées comme cause de mortalité ou de morbidité du fœtus ou du nouveau-né ; cette contrainte empêchait d'expliquer certaines consommations de ressources. Il faut donc étendre l'utilisation des codes P00-P04 aux circonstances dans lesquelles les états mentionnés ont été cause de soins supplémentaires au nouveau-né, ces soins étant considérés à priori dispensés dès lors que la mère a présenté une des affections répertoriées. Il est ainsi licite de mentionner systématiquement P03.4 dans le dossier de tout nouveau-né extrait par césarienne.

**Condition** : États maternels cause de soins supplémentaires au nouveau-né (présumés si affection répertoriée)

**Citation** (`categories_p00_p04.md` L10-16) :
« En conséquence, il faut étendre l’utilisation des codes P00–P04 aux circonstances dans lesquelles les états mentionnés ont été cause de soins supplémentaires au nouveau-né, et considérer à priori que ces soins ont été dispensés dès lors que la mère a présenté une des affections répertoriées dans les rubriques du groupe P00–P04. […] Il est donc licite de mentionner systématiquement le code P03.4 dans le dossier de tout nouveau-né extrait par césarienne. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `P00-P04` | `regi` | sujet | chaque | état maternel cause de soins supplémentaires au nouveau-né (présumés si affection répertoriée) |
| `P03.4` | `regi` | sujet | chaque | nouveau-né extrait par césarienne — mention systématique licite |

