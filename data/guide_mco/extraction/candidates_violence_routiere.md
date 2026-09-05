# Candidates — VIOLENCE ROUTIÈRE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/violence_routiere.md`
> (guide chap. V, pp. imprimées 120-121). Les `L…` y renvoient.

**3 consignes, 7 associations**.

---

## Consignes nouvelles

### GM2026-V-VIO-01 — `regle_position`

**Situation** : Accident de la circulation — nature des lésions (chapitre XIX)

**Texte** : Pour tout accident de la circulation routière, la nature des lésions traumatiques est codée en position de diagnostic principal ou de diagnostic associé, dans le respect de leur définition, avec le chapitre XIX.

**Condition** : Accident de la circulation routière

**Citation** (`violence_routiere.md` L10-14) :
« Pour tout accident de la circulation routière […] on enregistre dans le résumé d’unité médicale les informations suivantes. […] Elles sont codées en position de diagnostic principal ou de diagnostic associé dans le respect de leur définition (se reporter au chapitre IV), avec le chapitre XIX de la CIM–10. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `XIX` | `regi` | sujet | **ensemble** — Domaine du choix du code de lésion : le motif (accident de la circulation) est extérieur à l'expression — la consigne ne régit pas chaque code du chapitre XIX (précédent AVC-14) |  |

### GM2026-V-VIO-02 — `regle_position`

**Situation** : Accident de la circulation — circonstances (V01-V89)

**Texte** : Les circonstances des lésions sont codées au moyen du chapitre XX, spécialement de ses catégories V01 à V89. V89.2 (« accident de la circulation sans autre indication ») peut coder la notion d'« accident de la voie publique » sans précision.

**Condition** : Accident de la circulation routière

**Citation** (`violence_routiere.md` L18) :
« Elles sont codées au moyen du chapitre XX, spécialement de ses catégories V01 à V89. V89.2, comprenant « accident de la circulation sans autre indication », peut coder la notion d’« accident de la voie publique » sans précision. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `V01-V89` | `regi` | sujet | chaque | circonstances des lésions |
| `V89.2` | `regi` | sujet | chaque | accident de la voie publique sans précision |

### GM2026-V-VIO-03 — `regle_position`

**Situation** : Accident de la circulation — facteurs favorisants

**Texte** : Les facteurs favorisants présents au moment de l'accident (effet de l'alcool, de drogue ou de médicament…) sont enregistrés, notamment avec la catégorie R78 (présence de drogues et substances dans le sang) ou le groupe F10-F19 (troubles mentaux et du comportement liés aux substances psychoactives). L'enregistrement des effets secondaires des médicaments impose Y40-Y59 ; Y90-Y91 précisent l'importance d'une intoxication alcoolique.

**Condition** : Facteurs favorisants présents au moment de l'accident

**Citation** (`violence_routiere.md` L22) :
« D’éventuels facteurs favorisants présents au moment de l’accident (effet de l’alcool, de drogue ou de médicament…) doivent être enregistrés, notamment avec les codes de la catégorie R78 Présence de drogues et d’autres substances non trouvées normalement dans le sang ou avec ceux du groupe F10–F19 Troubles mentaux et du comportement liés à l’utilisation de substances psychoactives. […] Les catégories Y90–Y91 permettent de préciser l’importance d’une intoxication alcoolique. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `F10-F19` | `regi` | sujet | chaque | facteur favorisant au moment de l'accident |
| `R78` | `regi` | sujet | chaque | facteur favorisant au moment de l'accident |
| `Y40-Y59` | `regi` | sujet | chaque | effet secondaire de médicament |
| `Y90-Y91` | `regi` | sujet | chaque | importance de l'intoxication alcoolique |

