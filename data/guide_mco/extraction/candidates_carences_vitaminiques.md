# Candidates — CARENCES VITAMINIQUES

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/carences_vitaminiques.md`
> (guide chap. V, pp. imprimées 83). Les `L…` y renvoient.

**2 consignes, 2 associations**.

---

## Consignes nouvelles

### GM2026-V-CAR-01 — `condition_emploi`

**Situation** : Carence vitaminique ou avitaminose — exigence documentaire

**Texte** : L'enregistrement dans le RUM-RSS d'un code de carence vitaminique ou d'avitaminose (catégories E50 à E56) nécessite la mention du diagnostic dans le dossier médical, étayée par un dosage biologique témoignant d'une carence, d'un déficit, d'une insuffisance vitaminique ou d'une hypovitaminose.

**Condition** : Diagnostic mentionné au dossier, étayé par un dosage biologique

**Citation** (`carences_vitaminiques.md` L10) :
« L’enregistrement dans le RUM-RSS d’un code de carence vitaminique ou d’avitaminose — catégories E50 à E56 de la CIM–10 — nécessite la mention du diagnostic dans le dossier médical, étayé par un dosage biologique témoignant d’une carence, d’un déficit, d’une insuffisance vitaminique ou d’une hypovitaminose. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `E50-E56` | `regi` | sujet | chaque |  |

### GM2026-V-CAR-02 — `interdiction`

**Situation** : Supplémentation vitaminique systématique du nouveau-né

**Texte** : La supplémentation systématique du nouveau-né en vitamines A, D, E et K ne doit pas donner lieu à l'enregistrement de codes de carence vitaminique ou d'avitaminose.

**Condition** : Supplémentation systématique du nouveau-né, sans carence documentée

**Citation** (`carences_vitaminiques.md` L12) :
« La supplémentation systématique du nouveau-né en vitamines A, D, E et K ne doit pas donner lieu à l’enregistrement de codes de carence vitaminique ou d’avitaminose. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `E50-E56` | `interdit` | sujet | chaque | supplémentation systématique du nouveau-né (vitamines A, D, E, K), sans carence documentée |

