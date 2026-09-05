# Candidates — TUMEURS À ÉVOLUTION IMPRÉVISIBLE OU INCONNUE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/tumeurs_evolution_imprevisible.md`
> (guide chap. V, pp. imprimées 119-120). Les `L…` y renvoient.

**2 consignes, 4 associations**.

---

## Consignes nouvelles

### GM2026-V-TUM-01 — `condition_emploi`

**Situation** : Tumeur à évolution imprévisible — diagnostic histologique positif

**Texte** : Le classement des tumeurs suit leur comportement évolutif (malignes C00-C97, in situ D00-D09, bénignes D10-D36, à évolution imprévisible ou inconnue D37-D48). Une tumeur à évolution imprévisible a des caractéristiques déterminées : son classement est un diagnostic positif reposant sur un examen histologique, qui sous-entend l'élimination des comportements malin, in situ et bénin, et l'identification d'un comportement évolutif différent. Le classement de la CIM-10 se respecte dans les deux sens : un polyadénome colique reste une tumeur bénigne (D12.6), un polype de vessie est à évolution imprévisible (D41.4). Le codage nécessite que le dossier — en particulier le compte rendu anatomopathologique — soit conforme à ce diagnostic.

**Condition** : Examen histologique conforme au diagnostic

**Citation** (`tumeurs_evolution_imprevisible.md` L10-12) :
« Une tumeur à évolution imprévisible possède des caractéristiques déterminées et son classement comme telle est un diagnostic positif qui repose sur un examen histologique. […] Le codage d’une tumeur comme étant à évolution imprévisible nécessite que les informations contenues dans le dossier médical, en particulier dans le compte rendu de l’examen anatomopathologique, soient conformes à ce diagnostic. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `D12.6` | `regi` | **exemple** | chaque |  |
| `D37-D48` | `regi` | sujet | chaque | diagnostic histologique positif d'évolution imprévisible |
| `D41.4` | `regi` | **exemple** | chaque |  |

### GM2026-V-TUM-02 — `definition`

**Situation** : Tumeur d'évolution inconnue — définition

**Texte** : Une tumeur d'évolution inconnue est une tumeur pour laquelle on ne dispose pas d'information sur le comportement évolutif (ni malin, ni in situ, ni bénin, ni imprévisible) : en pratique, une tumeur sans examen histologique, ou dont l'examen n'est pas contributif, et sur le comportement de laquelle le médecin ne peut pas se prononcer.

**Condition** : —

**Citation** (`tumeurs_evolution_imprevisible.md` L16) :
« une tumeur d’évolution inconnue est une tumeur pour laquelle on ne dispose pas d’information sur son comportement évolutif […] la qualification de tumeur d’évolution inconnue concerne donc une tumeur pour laquelle on ne dispose pas d’examen histologique, ou dont l’examen histologique n’est pas contributif, et sur le comportement de laquelle le médecin ne peut pas se prononcer. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `D37-D48` | `regi` | sujet | chaque | comportement évolutif inconnu |

