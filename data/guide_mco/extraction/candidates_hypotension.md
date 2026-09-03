# Candidates — HYPOTENSION ET BAISSE DE LA TENSION ARTÉRIELLE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/hypotension.md`
> (guide chap. V, pp. imprimées 104). Les `L…` y renvoient.

**2 consignes, 5 associations**.

---

## Consignes nouvelles

### GM2026-V-HYP-01 — `condition_emploi`

**Situation** : Baisse tensionnelle non spécifique — R03.1

**Texte** : Une baisse de la pression intraartérielle qui est un signe d'accompagnement de diverses maladies ou une découverte fortuite isolée, sans diagnostic de maladie hypotensive chronique, est qualifiée de « non spécifique » : elle se code R03.1 Constatation d'une baisse non spécifique de la tension artérielle, selon la logique du chapitre XVIII et par analogie avec la note du R03.0.

**Condition** : Pas de diagnostic formel d'hypotension (signe d'accompagnement ou découverte fortuite isolée)

**Citation** (`hypotension.md` L12) :
« Dans les deux circonstances, cette chute tensionnelle est qualifiée par la CIM–10 de « non spécifique » : elle doit alors être codée R03.1 Constatation d’une baisse non spécifique de la tension artérielle. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `R03.1` | `regi` | sujet | chaque |  |

### GM2026-V-HYP-02 — `condition_emploi`

**Situation** : Maladie hypotensive chronique — I95.0, I95.1, I95.8

**Texte** : L'hypotension artérielle idiopathique ou orthostatique est une maladie chronique invalidante, au diagnostic fondé sur la constatation répétée d'une baisse des pressions diastolique et systolique mesurées dans des conditions rigoureuses. I95.0, I95.1 et I95.8 ne s'emploient que devant un diagnostic établi de maladie hypotensive chronique — sauf intégration dans un ensemble de troubles neurovégétatifs et neurologiques constituant le syndrome de Shy et Drager (G23.8). La même argumentation distingue la maladie hypertensive (I10) de l'élévation « non spécifique » (R03.0).

**Condition** : Diagnostic établi de maladie hypotensive chronique

**Citation** (`hypotension.md` L14) :
« Les codes I95.0, I95.1 et I95.8 ne doivent être employés que devant un diagnostic établi de maladie hypotensive chronique (sauf si elle s’intègre dans un ensemble de troubles neurovégétatifs et neurologiques, constituant alors le syndrome de Shy et Drager, code G23.8). La même argumentation conduit à distinguer la maladie hypertensive (I10) et l’élévation « non spécifique » de la pression intraartérielle (R03.0). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `G23.8` | `regi` | sujet | chaque | hypotension intégrée à un syndrome de Shy et Drager |
| `I95.0` | `regi` | sujet | chaque | diagnostic établi de maladie hypotensive chronique |
| `I95.1` | `regi` | sujet | chaque | diagnostic établi de maladie hypotensive chronique |
| `I95.8` | `regi` | sujet | chaque | diagnostic établi de maladie hypotensive chronique |

