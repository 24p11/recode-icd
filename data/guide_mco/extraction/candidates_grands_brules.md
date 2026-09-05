# Candidates — TRAITEMENT DES GRANDS BRULÉS

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/grands_brules.md`
> (guide chap. V, pp. imprimées 119). Les `L…` y renvoient.

**1 consignes, 1 associations**.

---

## Consignes nouvelles

### GM2026-V-BRU-01 — `condition_emploi`

**Situation** : Grands brûlés — causes des brûlures avec le chapitre XX

**Texte** : Le titulaire de l'autorisation de traitement des grands brûlés participe aux actions de prévention et recueille les données sur les causes des brûlures (art. R.6123-117 CSP) : une attention particulière est portée au codage des causes des brûlures avec le chapitre XX, en particulier au moyen du logiciel DAtIM lors de la transmission vers e-PMSI.

**Condition** : Prise en charge de grands brûlés

**Citation** (`grands_brules.md` L10) :
« une attention particulière sera portée au codage des causes des brulures avec le chapitre XX de la CIM–10, en particulier au moyen du logiciel de dépistage des atypies de l’information médicale (DAtIM) lors de la transmission des données vers la plateforme e- PMSI. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `XX` | `regi` | sujet | **ensemble** — Domaine du choix de la cause : la consigne appelle à soigner le codage des causes de brûlures, elle ne régit pas chaque code du chapitre XX (précédent AVC-14) | causes des brûlures |

