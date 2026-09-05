# Candidates — SUICIDES ET TENTATIVES DE SUICIDE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/suicides_tentatives.md`
> (guide chap. V, pp. imprimées 119). Les `L…` y renvoient.

**1 consignes, 2 associations**.

---

## Consignes nouvelles

### GM2026-V-SUI-01 — `regle_position`

**Situation** : Suicide ou tentative — DP chapitre XIX, X60-X84 en DA

**Texte** : Les RUM des séjours dont le suicide ou la tentative de suicide est le motif mentionnent un DP codé avec le chapitre XIX (lésions traumatiques, empoisonnements). En DA : les éventuelles complications (définition du DAS) ainsi qu'un code du groupe X60-X84 du chapitre XX pour le caractère auto-infligé des lésions et le ou les moyens utilisés. Pour les tentatives médicamenteuses, voir l'article EFFETS NOCIFS DES MÉDICAMENTS.

**Condition** : Séjour dont le suicide ou la tentative est le motif

**Citation** (`suicides_tentatives.md` L12) :
« Les RUM produits pour les séjours dont suicide ou tentative de suicide sont le motif, mentionnent un diagnostic principal codé avec le chapitre XIX de la CIM–10 Lésions traumatiques, empoisonnements et certaines autres conséquences de cause externe. On enregistre en tant que diagnostics associés (DA) les éventuelles complications […] ainsi qu’un code du groupe X60–X84 du chapitre XX […] pour enregistrer le caractère auto-infligé des lésions et le ou les moyens utilisés. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `X60-X84` | `DAS` | sujet | chaque | caractère auto-infligé et moyens utilisés |
| `XIX` | `DP` | sujet | **ensemble** — Domaine du choix du DP : le motif de séjour (suicide/tentative) est extérieur à l'expression — la consigne ne régit pas chaque code du chapitre XIX (précédent AVC-14) |  |

