# Candidates — EFFETS NOCIFS DES MÉDICAMENTS

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/effets_nocifs_medicaments.md`
> (guide chap. V, pp. imprimées 90-91). Les `L…` y renvoient.

**4 consignes, 10 associations**.

---

## Consignes nouvelles

### GM2026-V-EFN-01 — `regle_position`

**Situation** : Intoxication médicamenteuse accidentelle ou volontaire — T36-T50 + chapitre XX en DA

**Texte** : Les intoxications médicamenteuses accidentelles et volontaires (auto-infligées, intentionnelles, auto-induites) se codent avec les catégories T36 à T50. La distinction entre circonstances accidentelles et volontaires est assurée par des codes du chapitre XX saisis en diagnostic associé : catégories X40 à X44 pour les accidentelles, X60 à X64 pour les volontaires.

**Condition** : —

**Citation** (`effets_nocifs_medicaments.md` L14) :
« Le codage des intoxications médicamenteuses accidentelles et volontaires (la CIM–10 emploie pour les secondes les qualificatifs auto-infligées, intentionnelles et auto-induites) doit utiliser les catégories T36 à T50. La distinction entre les circonstances accidentelles et volontaires est assurée par des codes du chapitre XX : catégories X40 à X44 pour les premières, X60 à X64 pour les secondes, saisis en tant que diagnostic associé (DA). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `T36-T50` | `regi` | sujet | chaque | intoxication accidentelle ou volontaire |
| `X40-X44` | `DAS` | sujet | chaque | intoxication accidentelle |
| `X60-X64` | `DAS` | sujet | chaque | intoxication volontaire |

### GM2026-V-EFN-02 — `regle_position`

**Situation** : Intoxication — le code T en DP, jamais le symptôme

**Texte** : Coder en DP le symptôme engendré par une intoxication médicamenteuse (ex. les troubles de la conscience de la catégorie R40) au lieu de son code « T » est erroné : le symptôme n'a pas à être choisi pour DP alors que sa cause, l'intoxication, est identifiée (règle D1), et le GHM Troubles de la conscience et comas d'origine non traumatique correspond à des affections de cause ignorée. Pour une intoxication volontaire par psychotrope sédatif ou hypnotique à l'origine de troubles de la conscience, le code exact est celui de l'intoxication par le produit (catégorie T42) ; le coma et les autres complications éventuelles sont enregistrés comme DA. Cette règle s'applique de manière générale aux complications des intoxications médicamenteuses accidentelles et volontaires.

**Condition** : —

**Citation** (`effets_nocifs_medicaments.md` L16-20) :
« Le codage du symptôme ou du syndrome engendré par une intoxication médicamenteuse au lieu d’employer son code « T » a souvent pour origine une confusion […] le symptôme R40.– n’a pas à être choisi pour DP alors que sa cause, l’intoxication, est identifiée (règle D1) […] le code exact est celui de l’intoxication par le produit (catégorie T42). Le coma ou d’autres complications éventuelles doivent être enregistrées comme DA. […] elle doit être appliquée de manière générale aux complications des intoxications médicamenteuses accidentelles et volontaires. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `R40` | `interdit_DP` | sujet | chaque | cause identifiée : intoxication médicamenteuse |
| `T42` | `regi` | **exemple** | chaque |  |

### GM2026-V-EFN-03 — `regle_position`

**Situation** : Effet indésirable en usage thérapeutique — nature de l'effet + Y40-Y59

**Texte** : L'effet indésirable d'une « substance appropriée administrée correctement » se code selon la nature de l'effet — jamais avec les codes du groupe T36-T50 — associé à un code du chapitre XX (catégories Y40-Y59). Enregistrer qu'un effet est secondaire à un traitement médicamenteux n'est possible qu'en employant le chapitre XX.

**Condition** : Substance appropriée administrée correctement

**Citation** (`effets_nocifs_medicaments.md` L24-30) :
« l’effet indésirable d’une « substance appropriée administrée correctement » doit être codé selon la nature de l’effet. Le codage des effets indésirables des médicaments n’utilise donc pas les codes du groupe T36–T50. Il associe au code de la nature de l’effet un code du chapitre XX de la CIM–10 (catégories Y40–Y59). […] Pour un effet donné, enregistrer qu’il est secondaire à un traitement médicamenteux n’est possible qu’en employant le chapitre XX de la CIM–10. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `K29.1` | `regi` | **exemple** | chaque |  |
| `R00.1` | `regi` | **exemple** | chaque |  |
| `T36-T50` | `interdit` | sujet | chaque | effet indésirable d'une substance appropriée administrée correctement |
| `Y40-Y59` | `regi` | sujet | chaque |  |

### GM2026-V-EFN-04 — `condition_emploi`

**Situation** : « Surdosage » avec prescription respectée — effet indésirable, pas intoxication

**Texte** : Par « substance appropriée administrée correctement » on entend le respect de la prescription, notamment de la posologie. Les cas que le langage courant appelle « surdosage » alors que la prescription a été respectée (hémorragie sous anticoagulant avec INR au-dessus de la valeur souhaitée, complication avec concentration sanguine supra-thérapeutique — digoxinémie, lithémie…) sont des effets indésirables : leur codage n'utilise pas les codes du groupe T36-T50.

**Condition** : Prescription médicamenteuse respectée

**Citation** (`effets_nocifs_medicaments.md` L32) :
« Par « substance appropriée administrée correctement » on entend le respect de la prescription médicamenteuse, notamment de la posologie. […] De tels cas, lorsque la prescription a été respectée, doivent être classés comme des effets indésirables et leur codage ne doit pas utiliser les codes du groupe T36–T50. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `T36-T50` | `interdit` | sujet | chaque | « surdosage » avec prescription respectée |

