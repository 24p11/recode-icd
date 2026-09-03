# Candidates — CHUTES A REPETITION

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/chutes_a_repetition.md`
> (guide chap. V, pp. imprimées 83). Les `L…` y renvoient.

**3 consignes, 3 associations**.

---

## Consignes nouvelles

### GM2026-V-CHU-01 — `condition_emploi`

**Situation** : Chutes à répétition — définition et emploi réservé de R29.6

**Texte** : Le codage des chutes à répétition (R29.6) est réservé aux situations correspondant à la définition : chutes à répétition en raison du grand âge ou d'autres problèmes de santé mal définis. La chute est le fait de se retrouver involontairement sur le sol ou dans une position de niveau inférieur par rapport à sa position de départ ; le caractère répétitif est acquis à partir d'au moins deux chutes dans l'année qui précède le recueil.

**Condition** : Au moins deux chutes dans l'année précédant le recueil

**Citation** (`chutes_a_repetition.md` L10) :
« Le codage des chutes à répétition (R29.6) est réservé aux situations correspondant à la définition suivante : chutes à répétition en raison du grand âge ou d'autres problèmes de santé mal définis. La chute est définie comme le fait de se retrouver involontairement sur le sol ou dans une position de niveau inférieur par rapport à sa position de départ. Le caractère répétitif des chutes est considéré à partir du moment où la personne a fait au moins deux chutes dans l’année qui précède le recueil d’information. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `R29.6` | `regi` | sujet | chaque |  |

### GM2026-V-CHU-02 — `regle_position`

**Situation** : Chutes à répétition — R29.6 en DP

**Texte** : R29.6 est le DP d'un séjour motivé par la chute au cours duquel aucune lésion (conséquence de la chute) n'est traitée et aucune cause n'est trouvée : chute constatée répétitive, ou bilan de chutes répétitives à la recherche d'une pathologie causale sans que cette cause soit trouvée.

**Condition** : Aucune lésion traitée, aucune cause trouvée

**Citation** (`chutes_a_repetition.md` L14-16) :
« La chute à répétition est le DP d’un séjour motivé par la chute, séjour au cours duquel aucune lésion (conséquence de la chute) n’est traitée et aucune cause n’est trouvée. […] d’une chute constatée répétitive (au moins deux chutes dans l’année), le DP est la chute R29.6 ; […] d’un bilan de chutes répétitives à la recherche d’une pathologie causale et sans que cette cause soit trouvée, le DP est la chute R29.6 ; »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `R29.6` | `DP` | sujet | chaque | séjour motivé par la chute, aucune lésion traitée, aucune cause trouvée |

### GM2026-V-CHU-03 — `regle_position`

**Situation** : Chutes à répétition — R29.6 en DAS

**Texte** : La chute à répétition peut être un DAS (elle marque une fragilité du patient) quand elle n'est pas le DP : lorsqu'elle est à l'origine d'une lésion, la lésion étant le DP du séjour, et seulement si aucune causalité n'est retrouvée, le DAS est la chute R29.6.

**Condition** : Lésion en DP, aucune causalité retrouvée

**Citation** (`chutes_a_repetition.md` L18-19) :
« La notion de chute à répétition peut être un DAS car elle marque une fragilité du patient dans les cas pour lesquels elle ne sera pas le DP : […] Dans les cas où la chute à répétition est à l’origine de lésion, la lésion étant le DP du séjour, et seulement si aucune causalité n’est retrouvée, le DAS est la chute R29.6. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `R29.6` | `DAS` | sujet | chaque | lésion consécutive à la chute en DP, aucune causalité retrouvée |

