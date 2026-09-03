# Candidates — EMPLOI DES CATÉGORIES O80 À O84 DE LA CIM–10

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/categories_o80_o84.md`
> (guide chap. V, pp. imprimées 92). Les `L…` y renvoient.

**1 consignes, 2 associations**.

---

## Consignes nouvelles

### GM2026-V-O80-01 — `interdiction`

**Situation** : Codes O81.0 à O84.9 — plus utilisables en DP

**Texte** : L'emploi des codes O81.0 à O84.9 comme diagnostic principal du RUM est une erreur : depuis la version 11 des GHM (2009), ils ne sont plus utilisables en position de DP. Pour enregistrer un accouchement instrumental, le code du DP doit être choisi parmi les autres codes du chapitre XV (cf. la note en tête du groupe Accouchement O80-O84 au volume 1).

**Condition** : —

**Citation** (`categories_o80_o84.md` L10) :
« Il en résulte en particulier que l'emploi des codes O81.0 à O84.9 comme diagnostic principal (DP) du résumé d’unité médicale est une erreur. Depuis la version 11 des GHM (2009) ils ne sont plus utilisables en position de DP. Pour enregistrer un accouchement instrumental le code du DP doit être choisi parmi les autres codes du chapitre XV. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `O81.0-O84.9` | `interdit_DP` | sujet | chaque |  |
| `XV` | `regi` | sujet | **ensemble** — « parmi les autres codes du chapitre XV » : domaine du choix du DP de remplacement — la consigne ne régit pas chaque code du chapitre XV (précédent AVC-14) | accouchement instrumental — choix du DP |

