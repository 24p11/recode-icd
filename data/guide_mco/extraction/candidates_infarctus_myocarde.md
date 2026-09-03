# Candidates — INFARCTUS DU MYOCARDE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/infarctus_myocarde.md`
> (guide chap. V, pp. imprimées 105). Les `L…` y renvoient.

**1 consignes, 10 associations**.

---

## Consignes nouvelles

### GM2026-V-IDM-01 — `condition_emploi`

**Situation** : Infarctus du myocarde — prise en charge initiale vs « autres »

**Texte** : Les codes de prise en charge dite « initiale » de l'infarctus du myocarde sont réservés aux situations de première prise en charge thérapeutique selon les règles de l'art cardiologiques. L'emploi des extensions de prise en charge dites « autres » (I21.08, I21.18, I21.28, I21.38, I21.48, I21.98, I22.08, I22.18, I22.88, I22.98) s'impose notamment : pour un séjour après mutation ou transfert depuis une unité de soins intensifs ; pour l'unité inadéquate en cas d'erreur d'orientation corrigée par mutation ou transfert le jour même ou le lendemain (l'unité qui assure la prise en charge cardiologique utilise, elle, un code de prise en charge initiale).

**Condition** : Prise en charge autre que la première prise en charge thérapeutique

**Citation** (`infarctus_myocarde.md` L10-18) :
« Les codes de prise en charge dite « initiale » de l’infarctus du myocarde sont réservés aux situations de première prise en charge thérapeutique de l’infarctus selon les règles de l’art cardiologiques. En conséquence, l’emploi des extensions correspondant aux prises en charge dites « autres » (I21.08, I21.18, I21.28, I21.38, I21.48, I21.98, I22.08, I22.18, I22.88 et I22.98) s’impose par exemple dans les cas suivants : […] séjour après mutation ou transfert depuis une unité de soins intensifs ; […] erreur d’orientation : hospitalisation initiale dans une unité inadéquate suivie d’une mutation ou d’un transfert le jour même ou le lendemain dans une unité cardiologique. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I21.08` | `regi` | sujet | chaque | prise en charge autre que la première prise en charge thérapeutique |
| `I21.18` | `regi` | sujet | chaque | prise en charge autre que la première prise en charge thérapeutique |
| `I21.28` | `regi` | sujet | chaque | prise en charge autre que la première prise en charge thérapeutique |
| `I21.38` | `regi` | sujet | chaque | prise en charge autre que la première prise en charge thérapeutique |
| `I21.48` | `regi` | sujet | chaque | prise en charge autre que la première prise en charge thérapeutique |
| `I21.98` | `regi` | sujet | chaque | prise en charge autre que la première prise en charge thérapeutique |
| `I22.08` | `regi` | sujet | chaque | prise en charge autre que la première prise en charge thérapeutique |
| `I22.18` | `regi` | sujet | chaque | prise en charge autre que la première prise en charge thérapeutique |
| `I22.88` | `regi` | sujet | chaque | prise en charge autre que la première prise en charge thérapeutique |
| `I22.98` | `regi` | sujet | chaque | prise en charge autre que la première prise en charge thérapeutique |

