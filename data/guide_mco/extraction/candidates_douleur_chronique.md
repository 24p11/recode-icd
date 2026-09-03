# Candidates — DOULEUR CHRONIQUE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/douleur_chronique.md`
> (guide chap. V, pp. imprimées 89). Les `L…` y renvoient.

**1 consignes, 1 associations**.

---

## Consignes nouvelles

### GM2026-V-DOU-01 — `condition_emploi`

**Situation** : Douleur chronique — définition HAS et emploi de R52.2

**Texte** : Il y a douleur chronique (syndrome multidimensionnel exprimé par la personne atteinte), quelles que soient sa topographie et son intensité, lorsque la douleur présente plusieurs des caractéristiques suivantes : persistance ou récurrence ; durée au-delà de l'habituel pour la cause initiale présumée (notamment évolution depuis plus de 3 mois) ; réponse insuffisante au traitement ; détérioration significative et progressive des capacités fonctionnelles et relationnelles. L'utilisation du code R52.2 nécessite que le dossier mentionne l'existence d'une douleur chronique dans le cadre de cette définition.

**Condition** : Douleur chronique au sens de la définition HAS, mentionnée au dossier

**Citation** (`douleur_chronique.md` L10-19) :
« il y a douleur chronique, quelles que soient sa topographie et son intensité, lorsque la douleur présente plusieurs des caractéristiques suivantes : […] Persistance ou récurrence ; […] Durée au-delà de ce qui est habituel pour la cause initiale présumée, notamment si la douleur évolue depuis plus de 3 mois ; […] Réponse insuffisante au traitement ; […] Détérioration significative et progressive du fait de la douleur, des capacités fonctionnelles et relationnelles du patient […] L’utilisation du code R52.2 douleur chronique nécessite que le dossier mentionne l’existence d’une douleur chronique dans le cadre de cette définition. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `R52.2` | `regi` | sujet | chaque |  |

