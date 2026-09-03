# Candidates — INSUFFISANCE RESPIRATOIRE DE L’ADULTE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/insuffisance_respiratoire_adulte.md`
> (guide chap. V, pp. imprimées 106). Les `L…` y renvoient.

**2 consignes, 2 associations**.

---

## Consignes nouvelles

### GM2026-V-IRA-01 — `condition_emploi`

**Situation** : Insuffisance respiratoire aigüe — critères d'emploi de J96.0

**Texte** : L'utilisation du code J96.0 Insuffisance respiratoire aigüe nécessite que le dossier comporte la mention d'une insuffisance ou d'une décompensation respiratoire aigüe, ou d'une détresse respiratoire, et la constatation au cours du séjour d'une SaO2 inférieure à 90 % ou d'une PaO2 inférieure à 60 mm de mercure en air ambiant. Le critère gazométrique ne s'impose pas en cas de ventilation artificielle.

**Condition** : Mention au dossier + critère gazométrique (sauf ventilation artificielle)

**Citation** (`insuffisance_respiratoire_adulte.md` L10-13) :
« L’utilisation du code J96.0 Insuffisance respiratoire aigüe nécessite : […] que le dossier comporte la mention d’une insuffisance ou d’une décompensation respiratoire aigüe, ou d’une détresse respiratoire ; […] et la constatation au cours du séjour d’une saturation artérielle en oxygène (SaO 2) inférieure à 90 % ou d’une pression partielle dans le sang artériel (PaO2) inférieure à 60 mm de mercure en air ambiant. Le critère gazométrique ne s’impose pas en cas de ventilation artificielle. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `J96.0` | `regi` | sujet | chaque |  |

### GM2026-V-IRA-02 — `condition_emploi`

**Situation** : Insuffisance respiratoire chronique — critères d'emploi de J96.1

**Texte** : L'utilisation du code J96.1 Insuffisance respiratoire chronique nécessite que le dossier mentionne l'existence d'une insuffisance respiratoire chronique ou d'une affection respiratoire chronique, et d'une PaO2 inférieure à 60 mm de mercure en air ambiant de manière prolongée.

**Condition** : Mention au dossier + PaO2 < 60 mmHg en air ambiant de manière prolongée

**Citation** (`insuffisance_respiratoire_adulte.md` L15) :
« L’utilisation du code J96.1 Insuffisance respiratoire chronique nécessite que le dossier mentionne l’existence d’une insuffisance respiratoire chronique, ou d’une affection respiratoire chronique, et d’une PaO2 inférieure à 60 mm de mercure en air ambiant de manière prolongé. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `J96.1` | `regi` | sujet | chaque |  |

