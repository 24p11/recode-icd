# Candidates — ŒDÈME PULMONAIRE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/oedeme_pulmonaire.md`
> (guide chap. V, pp. imprimées 114). Les `L…` y renvoient.

**1 consignes, 3 associations**.

---

## Consignes nouvelles

### GM2026-V-OED-01 — `condition_emploi`

**Situation** : Œdème pulmonaire — I50.1, J60-J70 ou J81 selon l'origine

**Texte** : « Œdème pulmonaire », « œdème aigu pulmonaire », « OAP » correspondent habituellement à une insuffisance ventriculaire gauche : tout œdème pulmonaire d'origine cardiaque se code I50.1 (chapitre IX). Les œdèmes pulmonaires dus à des agents externes sont classés en J60-J70. Les autres formes se codent J81 Œdème pulmonaire — par exemple l'œdème de surcharge observé au cours de l'insuffisance rénale.

**Condition** : —

**Citation** (`oedeme_pulmonaire.md` L10-12) :
« Dans ce cas, leur code est I50.1 Insuffisance ventriculaire gauche. […] On doit donc coder I50.1 tout œdème pulmonaire dont l’origine est cardiaque. […] Les œdèmes pulmonaires dus à des agents externes sont classés en J60–J70. Les autres formes d’œdème pulmonaire se codent en J81 Œdème pulmonaire. C’est le cas par exemple de l’œdème pulmonaire de surcharge observé au cours de l’insuffisance rénale. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I50.1` | `regi` | sujet | chaque | œdème pulmonaire d'origine cardiaque |
| `J60-J70` | `regi` | sujet | chaque | œdème pulmonaire dû à des agents externes |
| `J81` | `regi` | sujet | chaque | autres formes (ex. surcharge de l'insuffisance rénale) |

