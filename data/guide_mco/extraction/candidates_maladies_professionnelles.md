# Candidates — MALADIES PROFESSIONNELLES

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/maladies_professionnelles.md`
> (guide chap. V, pp. imprimées 109). Les `L…` y renvoient.

**1 consignes, 1 associations**.

---

## Consignes nouvelles

### GM2026-V-MPR-01 — `regle_position`

**Situation** : Caractère professionnel d'une affection — Y96 en DAS

**Texte** : En plus du codage selon la nature de l'affection (asbestose, silicose, « gale » du ciment, etc.), Y96 Facteurs liés aux conditions de travail signale le caractère professionnel d'une affection. Dès lors que la causalité a été établie, il faut l'enregistrer en position de diagnostic associé — pour tous les problèmes de santé de cause professionnelle, y compris les lésions traumatiques et leurs séquelles.

**Condition** : Causalité professionnelle établie

**Citation** (`maladies_professionnelles.md` L10) :
« la CIM–10 donne la possibilité de signaler le caractère professionnel d’une affection au moyen du code Y96 Facteurs liés aux conditions de travail. Dès lors que la causalité a été établie, il faut l’enregistrer en position de diagnostic associé. Cette consigne vaut pour tous les problèmes de santé de cause professionnelle, y compris les lésions traumatiques et leurs séquelles. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Y96` | `DAS` | sujet | chaque | causalité professionnelle établie |

