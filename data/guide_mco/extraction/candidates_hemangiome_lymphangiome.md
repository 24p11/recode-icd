# Candidates — HÉMANGIOME ET LYMPHANGIOME

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/hemangiome_lymphangiome.md`
> (guide chap. V, pp. imprimées 104). Les `L…` y renvoient.

**1 consignes, 3 associations**.

---

## Consignes nouvelles

### GM2026-V-HEM-01 — `condition_emploi`

**Situation** : Hémangiome et lymphangiome — D18 superficiel, tumeur bénigne d'organe sinon

**Texte** : Hémangiomes et lymphangiomes échappent au classement topographique du chapitre II : l'OMS les distingue d'après leur nature. En France, la catégorie D18 est employée pour les seuls hémangiomes et lymphangiomes superficiels (limités aux téguments) ; lorsque ces tumeurs atteignent un organe profond, on enregistre le code de tumeur bénigne de l'organe (ex. : hémangiome du côlon droit, D12.2 et non D18.0).

**Condition** : Lésion superficielle limitée aux téguments (pour D18)

**Citation** (`hemangiome_lymphangiome.md` L10) :
« En France, la consigne est d'employer la catégorie D18 pour les seuls hémangiomes et lymphangiomes superficiels (limités aux téguments), mais d’enregistrer le code de tumeur bénigne de l'organe lorsque ces tumeurs atteignent un organe profond. Par exemple, un hémangiome du côlon droit doit être codé D12.2 et non D18.0. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `D12.2` | `regi` | **exemple** | chaque |  |
| `D18` | `regi` | sujet | chaque | hémangiome ou lymphangiome superficiel (téguments) |
| `D18.0` | `regi` | **exemple** | chaque |  |

