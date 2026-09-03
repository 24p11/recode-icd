# Candidates — COMPLICATIONS DES ACTES MÉDICAUX ET CHIRURGICAUX

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/complications_actes.md`
> (guide chap. V, pp. imprimées 84-88). Les `L…` y renvoient.

**6 consignes, 49 associations**.

---

## Consignes nouvelles

### GM2026-V-COMP-01 — `condition_emploi`

**Situation** : Complication d'un acte — règle générale de choix du code

**Texte** : Une complication d'un acte diagnostique ou thérapeutique est codée de la façon la plus précise, la nature de la complication étant prioritaire : (1) avec un code du groupe T80-T88 lorsque le code le plus précis pour la complication appartient à ce groupe ; (2) sinon avec un code d'une catégorie « Atteintes [troubles] [affections] de l'appareil […] après un acte à visée […] » lorsque la nature de la complication figure dans l'intitulé (ce qui exclut les sous-catégories .8 et .9) ; (3) dans les autres cas avec un code « habituel » de la CIM-10. Les codes T80-T88 ne sont employés que lorsqu'ils apportent le plus de précision, c'est-à-dire lorsque la CIM-10 n'offre pas par ailleurs de possibilité de codage plus précis selon la nature de la complication.

**Condition** : —

**Citation** (`complications_actes.md` L20-36) :
« Une complication d’un acte diagnostique ou thérapeutique doit être codée dans le respect de la règle générale, c’est-à-dire de la façon la plus précise au regard de l’information. […] on préfère toujours un codage privilégiant la nature de la complication. […] avec un code du groupe T80–T88 lorsque le code le plus précis pour la complication appartient à ce groupe ; […] sinon avec un code d’une catégorie « Atteintes [troubles] [affections] de l’appareil [...] après un acte à visée [...] » lorsque la nature de la complication figure dans l’intitulé, ce qui exclut les sous-catégories .8 et .9 ; […] dans les autres cas avec un code « habituel » de la CIM–10. […] Les codes du groupe T80–T88 doivent être employés lorsqu’ils apportent le plus de précision »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `T80-T88` | `regi` | sujet | chaque |  |
| `T82.1` | `regi` | **exemple** | chaque |  |
| `T84.0` | `regi` | **exemple** | chaque |  |
| `T86.1` | `regi` | **exemple** | chaque |  |
| `T87.3` | `regi` | **exemple** | chaque |  |

### GM2026-V-COMP-02 — `regle_association`

**Situation** : Complication codée avec un code « habituel » — complément T80-T88 en DAS

**Texte** : Lorsqu'un codage précis selon la nature de la complication conduit à l'enregistrer avec un code « habituel » (autre code des chapitres I à XIX), il doit être complété par le code du groupe T80-T88 correspondant, enregistré comme diagnostic associé, quelle que soit son imprécision et y compris s'il n'est pas autorisé comme DP. Le code « T » à choisir est celui que l'index alphabétique (volume 3) indique pour la complication. Ce codage complémentaire ne s'applique qu'aux codes « habituels » : il ne concerne ni les codes « T » ni les catégories « Atteintes […] après un acte à visée […] ».

**Condition** : Complication codée avec un code « habituel »

**Citation** (`complications_actes.md` L87-114) :
« Lorsqu’un codage précis selon la nature de la complication conduit à l’enregistrer avec un code « habituel », il doit être complété par un code du groupe T80–T88, quelle que soit l’imprécision de celui-ci, y compris s’il s’agit d’un code non autorisé comme DP […] lorsque l’index alphabétique (volume 3) de la CIM–10 indique pour la complication un code du groupe T80–T88, c’est lui qui doit compléter le code « habituel ». […] Ce codage complémentaire en tant que diagnostic associé ne s’applique qu’aux codes « habituels ». »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `A41.2` | `regi` | **exemple** | chaque |  |
| `I21` | `regi` | **exemple** | chaque |  |
| `I33.0` | `regi` | **exemple** | chaque |  |
| `I74.3` | `regi` | **exemple** | chaque |  |
| `I80.8` | `regi` | **exemple** | chaque |  |
| `J18.9` | `regi` | **exemple** | chaque |  |
| `K25.3` | `regi` | **exemple** | chaque |  |
| `K65.0` | `regi` | **exemple** | chaque |  |
| `L02.2` | `regi` | **exemple** | chaque |  |
| `M00` | `regi` | **exemple** | chaque |  |
| `M86` | `regi` | **exemple** | chaque |  |
| `S27.01` | `regi` | **exemple** | chaque |  |
| `S66` | `regi` | **exemple** | chaque |  |
| `T80-T88` | `DAS` | sujet | chaque | complication codée avec un code « habituel » |

### GM2026-V-COMP-03 — `regle_position`

**Situation** : Complication d'un acte — circonstances iatrogéniques en DAS (chapitre XX)

**Texte** : Quel que soit le code de la complication (groupe T80-T88, catégorie « Atteintes […] après un acte à visée […] » ou code « habituel »), les circonstances iatrogéniques sont enregistrées au moyen d'un code du chapitre XX en position de diagnostic associé : Y83-Y84 pour les réactions anormales ou complications ultérieures sans mention d'accident (aléa médical) ; Y60-Y69 (accidents au cours d'actes) et Y70-Y82 (appareils médicaux associés à des accidents) lorsque les circonstances sont différentes ; Y88 lorsque la complication est une séquelle d'un acte antérieur ; Y95 Facteurs nosocomiaux, en tant que de besoin, pour les actes effectués en établissement d'hospitalisation.

**Condition** : —

**Citation** (`complications_actes.md` L118-149) :
« Quel que soit le code de la complication […] les circonstances iatrogéniques doivent être enregistrées au moyen d’un code du chapitre XX en position de diagnostic associé. […] Les codes « Y » donnés ici à titre d’exemple appartiennent au groupe Y83–Y84 […] Lorsque les circonstances de la complication sont différentes, on dispose des codes des groupes Y60–Y69 Accidents et complications au cours d’actes médicaux et chirurgicaux et Y70–Y82 Appareils médicaux associés à des accidents au cours d’actes diagnostiques et thérapeutiques. […] Lorsque la complication est une séquelle d’un acte antérieur, le codage […] est complété avec la catégorie Y88. […] S’agissant de complications dues à des actes effectués dans des établissements d’hospitalisation, le codage doit être complété en tant que de besoin par le code Y95 Facteurs nosocomiaux. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Y60-Y69` | `DAS` | sujet | chaque | accident au cours de l'acte |
| `Y70-Y82` | `DAS` | sujet | chaque | appareil médical associé à un accident |
| `Y83-Y84` | `DAS` | sujet | chaque | réaction anormale ou complication ultérieure sans mention d'accident (aléa) |
| `Y88` | `DAS` | sujet | chaque | complication séquelle d'un acte antérieur |
| `Y95` | `DAS` | sujet | chaque | acte effectué en établissement d'hospitalisation, en tant que de besoin |

### GM2026-V-COMP-04 — `interdiction`

**Situation** : Codes T80-T88 imprécis — non autorisés en DP

**Texte** : Plusieurs sous-catégories du groupe T80-T88 sont très imprécises : l'emploi de T80.2, T81.2, T81.4, T88.0, T88.1, T88.7 (auxquels s'ajoutent T81.3, T85.5, T86.0 et T86.8, devenus imprécis du fait de leur subdivision) ainsi que de toutes les subdivisions .8 et .9 du groupe (hors celles de la catégorie T86) n'est pas autorisé pour le codage du diagnostic principal.

**Condition** : —

**Citation** (`complications_actes.md` L46) :
« En revanche, plusieurs sous-catégories sont très imprécises. L’emploi de certaines n’est pas autorisé pour le codage du diagnostic principal (DP) : T80.2, T81.2, T81.4, T88.0, T88.1, T88.7 […] et toutes les subdivisions .8 et .9 hors celles de la catégorie T86. […] Auxquels s’ajoutent T81.3, T85.5, T86.0 et T86.8, devenus imprécis du fait de leur subdivision. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `T80.2` | `interdit_DP` | sujet | chaque |  |
| `T81.2` | `interdit_DP` | sujet | chaque |  |
| `T81.3` | `interdit_DP` | sujet | chaque |  |
| `T81.4` | `interdit_DP` | sujet | chaque |  |
| `T85.5` | `interdit_DP` | sujet | chaque |  |
| `T86.0` | `interdit_DP` | sujet | chaque |  |
| `T86.8` | `interdit_DP` | sujet | chaque |  |
| `T88.0` | `interdit_DP` | sujet | chaque |  |
| `T88.1` | `interdit_DP` | sujet | chaque |  |
| `T88.7` | `interdit_DP` | sujet | chaque |  |

### GM2026-V-COMP-05 — `condition_emploi`

**Situation** : Catégories « Atteintes de l'appareil […] après un acte » — sous-catégories .8 et .9

**Texte** : Les sous-catégories des catégories « Atteintes [troubles] [affections] de l'appareil […] après un acte à visée […] » contiennent habituellement une manifestation précise et son étiologie (ex. I97.2, J95.1) ; on en rapproche les codes dont le libellé implique que l'affection est toujours consécutive à un acte (ex. K43.1, K43.5). Leurs sous-catégories .9 ne sont pas autorisées comme DP, et une information orientant vers l'une d'elles doit faire rechercher davantage de précision ; les sous-catégories .8 (ex. I97.8, J95.8, K91.8) sont imprécises : il faut leur préférer les codes « habituels » de la CIM-10.

**Condition** : —

**Citation** (`complications_actes.md` L50-62) :
« Les sous-catégories contiennent habituellement une manifestation précise et son étiologie. […] Les sous-catégories codées .9 ne sont pas autorisées comme DP et une information orientant vers l’une d’elles doit faire rechercher davantage de précision. […] Les sous-catégories codées .8 telles que I97.8 […] sont imprécises. Aux sous- catégories .8 il faut préférer les codes « habituels » de la CIM–10. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I97.2` | `regi` | **exemple** | chaque |  |
| `I97.8` | `regi` | **exemple** | chaque |  |
| `J95.1` | `regi` | **exemple** | chaque |  |
| `J95.8` | `regi` | **exemple** | chaque |  |
| `K43.1` | `regi` | **exemple** | chaque |  |
| `K43.5` | `regi` | **exemple** | chaque |  |
| `K91.8` | `regi` | **exemple** | chaque |  |

### GM2026-V-COMP-06 — `condition_emploi`

**Situation** : Complications d'actes obstétricales — chapitre XV

**Texte** : On rapproche des catégories « Atteintes […] après un acte » les complications d'actes classées dans le chapitre XV (quatrièmes caractères des catégories O03 à O06 et O08 pour les grossesses terminées par un avortement, catégories O29, O74…). Leur emploi s'impose pour le dossier de la mère pendant la grossesse, le travail, l'accouchement et la puerpéralité (ex. O35.7, O75.4, O86.0, O90.0 à O90.2).

**Condition** : Dossier de la mère (grossesse, travail, accouchement, puerpéralité)

**Citation** (`complications_actes.md` L56) :
« On en rapproche les complications d’actes classées dans le chapitre XV de la CIM–10 Grossesse, accouchement et puerpéralité : quatrièmes caractères des catégories O03–O06 et O08 pour les grossesses terminées par un avortement, catégories O29, O74... Leur emploi s’impose pour le dossier de la mère pendant la grossesse, le travail, l’accouchement et la puerpéralité. Par exemple, O35.7, O75.4, O86.0 et O90.0 à O90.2. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `O03-O06` | `regi` | sujet | chaque | grossesse terminée par un avortement, quatrième caractère |
| `O08` | `regi` | sujet | chaque | grossesse terminée par un avortement |
| `O29` | `regi` | sujet | chaque |  |
| `O35.7` | `regi` | **exemple** | chaque |  |
| `O74` | `regi` | sujet | chaque |  |
| `O75.4` | `regi` | **exemple** | chaque |  |
| `O86.0` | `regi` | **exemple** | chaque |  |
| `O90.0-O90.2` | `regi` | **exemple** | chaque |  |

