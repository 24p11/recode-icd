# Candidates — ACCOUCHEMENT IMPROMPTU OU À DOMICILE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/accouchement_impromptu.md`
> (guide chap. V, pp. imprimées 81). Les `L…` y renvoient.

**3 consignes, 3 associations**.

---

## Consignes nouvelles

### GM2026-V-ACC-01 — `regle_position`

**Situation** : Séjour faisant suite à un accouchement impromptu hors établissement

**Texte** : Un séjour faisant suite à un accouchement impromptu survenu avant l'arrivée de la mère dans un établissement de santé (au domicile, pendant le trajet vers la maternité), que l'accouchement ait eu lieu ou non en présence du SMUR, est codé DP Z39.00, DA Z37.– ; aucun acte d'accouchement n'est codé.

**Condition** : Accouchement survenu avant l'arrivée dans l'établissement

**Citation** (`accouchement_impromptu.md` L10-14) :
« Un séjour faisant suite à un accouchement impromptu survenu avant l’arrivée de la mère dans un établissement de santé […] est codé comme suit : […] DP : Z39.00 ; […] DA : Z37.– ; […] pas d’acte d’accouchement. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z37` | `DAS` | sujet | chaque |  |
| `Z39.00` | `DP` | sujet | chaque |  |

### GM2026-V-ACC-02 — `definition`

**Situation** : Accouchement à domicile choisi — pas de séjour hospitalier

**Texte** : L'accouchement à domicile résultant du choix de la mère ne donne pas lieu à la production d'un RSS, faute de séjour hospitalier, ni pour la mère ni pour le nouveau-né, y compris si celui-ci est né sans vie.

**Condition** : Accouchement à domicile par choix, sans complication hospitalisée

**Citation** (`accouchement_impromptu.md` L16) :
« L’accouchement à domicile, résultant du choix de la mère, ne donne pas lieu à la production d’un RSS puisqu’il n’existe pas de séjour hospitalier, ni pour la mère ni pour le nouveau-né. — Y compris si celui-ci est né sans vie (voir pages 70 et 92). »

*Aucune association.* Le guide ne nomme ici aucun code : en attribuer supposerait de **choisir** des cibles que le texte ne donne pas.

### GM2026-V-ACC-03 — `regle_position`

**Situation** : Accouchement à domicile — hospitalisation pour complication

**Texte** : En cas de complication après un accouchement à domicile : si elle concerne la mère, son séjour est un séjour du postpartum et non d'accouchement, le DP déterminé conformément à sa définition ; le nouveau-né sans problème de santé propre pris en charge est alors aussi en séjour du postpartum, son DP est codé Z76.2. Si la complication concerne l'enfant, un RSS est produit pour lui, le DP déterminé conformément à sa définition.

**Condition** : Complication après un accouchement à domicile

**Citation** (`accouchement_impromptu.md` L16-19) :
« Une hospitalisation ne surviendrait qu’en cas de complication : — si la complication concerne la mère, son séjour est un séjour du postpartum, non d’accouchement ; le DP est déterminé conformément à sa définition […] le séjour de celui-ci est aussi un séjour du postpartum, son DP est codé Z76.2 […] — si la complication concerne l’enfant, un RSS est produit pour lui ; le DP est déterminé conformément à sa définition et au guide des situations cliniques. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z76.2` | `DP` | sujet | chaque | nouveau-né sans problème de santé propre, mère hospitalisée pour complication |

