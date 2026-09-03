# Candidates — DIABÈTE DE TYPE 2 TRAITÉ PAR INSULINE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/diabete_type2_insuline.md`
> (guide chap. V, pp. imprimées 89). Les `L…` y renvoient.

**1 consignes, 10 associations**.

---

## Consignes nouvelles

### GM2026-V-DIA-01 — `condition_emploi`

**Situation** : Diabète de type 2 insulinotraité — emploi des extensions E11.–0

**Texte** : Les codes étendus de la catégorie E11 portant le chiffre 0 en cinquième position (E11.00 à E11.90) distinguent le diabète de type 2 insulinotraité (insulinonécessitant, insulinorequérant). Ils sont réservés au diabète de type 2 insulinotraité au long cours et ne doivent pas être employés lorsqu'un évènement ponctuel exige, pendant l'hospitalisation, un bref remplacement du traitement antidiabétique oral par l'insuline (par exemple pour une anesthésie). Leur mention dans un RUM suppose que le patient était déjà traité par insuline à domicile avant l'hospitalisation, ou que le traitement insulinique est poursuivi à domicile après la sortie (mentionné dans l'ordonnance de sortie).

**Condition** : Insulinothérapie au long cours (à domicile avant l'hospitalisation ou poursuivie après la sortie)

**Citation** (`diabete_type2_insuline.md` L10) :
« Les codes étendus correspondant à ces derniers sont ceux possédant le chiffre 0 » en cinquième position du code […] Ces codes sont réservés au diabète de type 2 insulinotraité au long cours. Ils ne doivent pas être employés lorsqu’un évènement ponctuel exige, pendant une hospitalisation, un bref remplacement d’un traitement antidiabétique oral par l’insuline, par exemple pour une anesthésie. La mention d’un code étendu E11.–0 dans un RUM suppose que le patient fût déjà traité par insuline à son domicile avant son hospitalisation ou que le traitement insulinique soit poursuivi à domicile après la sortie (il est alors mentionné dans l’ordonnance de sortie). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `E11.00` | `regi` | sujet | chaque |  |
| `E11.10` | `regi` | sujet | chaque |  |
| `E11.20` | `regi` | sujet | chaque |  |
| `E11.30` | `regi` | sujet | chaque |  |
| `E11.40` | `regi` | sujet | chaque |  |
| `E11.50` | `regi` | sujet | chaque |  |
| `E11.60` | `regi` | sujet | chaque |  |
| `E11.70` | `regi` | sujet | chaque |  |
| `E11.80` | `regi` | sujet | chaque |  |
| `E11.90` | `regi` | sujet | chaque |  |

