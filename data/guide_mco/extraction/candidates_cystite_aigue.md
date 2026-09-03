# Candidates — CYSTITE AIGÜE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/cystite_aigue.md`
> (guide chap. V, pp. imprimées 88). Les `L…` y renvoient.

**1 consignes, 2 associations**.

---

## Consignes nouvelles

### GM2026-V-CYS-01 — `condition_emploi`

**Situation** : Cystite aigüe — N30.0 documenté ou N39.0 par défaut

**Texte** : Le diagnostic de cystite aigüe est posé devant l'association de signes fonctionnels (pollakiurie, douleurs mictionnelles…) et d'une pyurie constatée à la bandelette urinaire, ou d'une pyurie avec bactériurie à l'étude cytobactériologique. La mention de cystite (aigüe), d'infection vésicale (aigüe) ou d'infection urinaire basse dans le dossier, appuyée sur ces arguments, permet d'utiliser N30.0 Cystite aigüe. Quand ces éléments manquent, ou devant la présence isolée de germes dans l'uroculture (bactériurie), on code N39.0 Infection des voies urinaires, siège non précisé.

**Condition** : —

**Citation** (`cystite_aigue.md` L10-16) :
« Le diagnostic de cystite aigüe est posé devant l’association : […] de signes fonctionnels de type pollakiurie, douleurs mictionnelles... ; […] et d’une pyurie constatée avec une bandelette urinaire, ou d’une pyurie avec bactériurie en cas d’étude cytobactériologique urinaire. […] La mention de cystite (aigüe), d’infection vésicale (aigüe) ou d’infection urinaire basse dans le dossier, appuyée sur ces arguments, permet d’utiliser le code N30.0 Cystite aigüe pour mentionner cette affection. Quand ces éléments manquent ou devant la présence isolée de germes dans l’uroculture (bactériurie), on code N39.0 Infection des voies urinaires, siège non précisé. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `N30.0` | `regi` | sujet | chaque | signes fonctionnels + pyurie (± bactériurie) et mention au dossier |
| `N39.0` | `regi` | sujet | chaque | arguments de cystite manquants, ou bactériurie isolée |

