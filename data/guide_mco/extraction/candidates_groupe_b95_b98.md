# Candidates — EMPLOI DES CODES DU GROUPE B95–B98 CIM–10

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/groupe_b95_b98.md`
> (guide chap. V, pp. imprimées 91). Les `L…` y renvoient.

**2 consignes, 8 associations**.

---

## Consignes nouvelles

### GM2026-V-B95-01 — `condition_emploi`

**Situation** : Codes B95-B98 — DAS uniquement, infection présente

**Texte** : Les codes B95-B98 ne doivent être utilisés qu'en position de diagnostic associé, conformément à leur intitulé : ils sont réservés aux cas dans lesquels une infection est présente, classée dans un chapitre distinct du chapitre I. La rubrique de l'infection s'accompagne souvent de la note « Utiliser, au besoin, un code supplémentaire (B95-B98) pour identifier l'agent infectieux ».

**Condition** : Infection présente, classée hors chapitre I

**Citation** (`groupe_b95_b98.md` L10-18) :
« Ces codes ne doivent être utilisés qu’en position de diagnostic associé. Leur usage doit être conforme à leur intitulé. Ils sont donc réservés aux cas dans lesquels une infection est présente, infection classée dans un chapitre distinct du chapitre I (CIM–10, vol. 2, § 4.4.4). La rubrique de l’infection s’accompagne souvent d’une note signalant la possibilité d’association : « Utiliser, au besoin, un code supplémentaire (B95–B98) pour identifier l’agent infectieux ». »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `B95-B98` | `DAS` | sujet | chaque | infection présente, classée hors chapitre I |
| `I33.0` | `regi` | **exemple** | chaque |  |
| `J32.0` | `regi` | **exemple** | chaque |  |
| `L02` | `regi` | **exemple** | chaque |  |
| `M86` | `regi` | **exemple** | chaque |  |
| `N10` | `regi` | **exemple** | chaque |  |
| `R18` | `regi` | **exemple** | chaque |  |

### GM2026-V-B95-02 — `condition_emploi`

**Situation** : Colonisation sans infection — Z22

**Texte** : En l'absence d'infection, une colonisation (« portage sain ») doit être codée avec la catégorie Z22.

**Condition** : Absence d'infection

**Citation** (`groupe_b95_b98.md` L20) :
« En l’absence d’infection, une colonisation (« portage sain ») doit être codée avec la catégorie Z22. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z22` | `regi` | sujet | chaque | colonisation sans infection |

