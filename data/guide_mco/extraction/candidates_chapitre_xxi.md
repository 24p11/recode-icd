# Candidates — EMPLOI DES CODES DU CHAPITRE XXI DE LA CIM-10

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits_bruts/chapitre_xxi.txt`
> (guide chap. V, pp. imprimées 93-103). Les `L…` y renvoient.

**55 consignes, 115 associations**.

---

## Consignes nouvelles

### GM2026-V-XXI-01 — `definition`

**Situation** : Emploi général des codes du chapitre XXI

**Texte** : Les codes du chapitre XXI (« codes Z ») peuvent, et souvent doivent, être utilisés dans le RUM comme diagnostic principal, relié ou associé.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L39-42) :
« Les codes du chapitre XXI Facteurs influant sur l’état de santé et motifs de recours aux services de santé ("codes Z") peuvent, et souvent doivent, être utilisés dans le résumé d’unité médicale (RUM) comme diagnostic principal (DP), relié (DR) ou associé (DA). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `XXI` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-02 — `condition_emploi`

**Situation** : Z00–Z02 — motifs relevant de l'activité externe

**Texte** : Les catégories Z00 à Z02 répertorient des motifs de recours qui relèvent, sauf exception, de l'activité externe ; les patients concernés ne se plaignent de rien et aucun diagnostic n'est rapporté.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L54-62) :
« Elles répertorient des motifs de recours qui relèvent, sauf exception, de l’activité externe. […] Les patients concernés ne se plaignent de rien et aucun diagnostic n’est rapporté (sinon c’est la symptomatologie ou le diagnostic qu’on coderait). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z00-Z02` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-03 — `condition_emploi`

**Situation** : Z03 — suspicions non confirmées

**Texte** : Les cas où l'emploi de Z03 s'impose sont rares : lorsqu'une symptomatologie est présente, on préfère son code (le plus souvent du chapitre XVIII) toutes les fois qu'il est plus précis. Z03.6 reste adapté à une suspicion d'absorption de produit toxique reposant sur une crainte de l'entourage, finalement infirmée.

**Condition** : Absence de symptomatologie codable plus précise

**Citation** (`chapitre_xxi.txt` L86-95) :
« La règle générale est : le meilleur code est le plus précis par rapport à l’information à coder. Lorsqu’une symptomatologie est présente, on préfèrera son code (le plus souvent présent dans le chapitre XVIII de la CIM–10) à un code Z toutes les fois qu’il est plus précis. Les cas dans lesquels l’emploi de la catégorie Z03 s’impose sont rares. […] En revanche, Z03.6 […] peut être le code le plus adapté à une suspicion d’absorption de produit toxique […] lorsqu’elle repose sur une crainte de l’entourage mais qu’elle est finalement infirmée. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z03` | `regi` | sujet | chaque |  |
| `Z03.6` | `DP` | sujet | chaque | suspicion de produit toxique infirmée |

### GM2026-V-XXI-04 — `condition_emploi`

**Situation** : Z04.0 — alcool et substances pharmacologiques

**Texte** : Z04.0 est employé lorsque la présence dans le sang d'alcool ou de substances pharmacologiques n'est pas confirmée ; si elle l'est, on fait appel à la catégorie R78.

**Condition** : Présence non confirmée

**Citation** (`chapitre_xxi.txt` L99-101) :
« de la présence dans le sang d’alcool ou de substances pharmacologiques ; le code Z04.0 est employé lorsque leur présence n’est pas confirmée, sinon on ferait appel à la catégorie R78. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `R78` | `regi` | sujet | chaque | si présence confirmée |
| `Z04.0` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-05 — `condition_emploi`

**Situation** : Z04.1 à Z04.3 — suspicion de lésion secondaire

**Texte** : L'emploi de Z04.1 à Z04.3 est réservé aux situations dans lesquelles aucune lésion n'est finalement diagnostiquée.

**Condition** : Aucune lésion finalement diagnostiquée

**Citation** (`chapitre_xxi.txt` L102-105) :
« d’une lésion susceptible de se manifester secondairement par rapport au traumatisme responsable : codes Z04.1 à Z04.3 ; leur emploi est réservé aux situations dans lesquelles aucune lésion n’est finalement diagnostiquée (sinon c’est elle qu’on coderait) »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z04.1-Z04.3` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-06 — `condition_emploi`

**Situation** : Z04.4 à Z04.6 — problèmes médicolégaux

**Texte** : Z04.4 et Z04.5 peuvent être utilisés autant pour les coupables que pour les victimes ; on les emploie lorsqu'aucun état morbide n'est mis en évidence.

**Condition** : Aucun état morbide mis en évidence

**Citation** (`chapitre_xxi.txt` L106-110) :
« d’autres problèmes médicolégaux : Z04.4, Z04.5, Z04.6 ; les codes Z04.4 et Z04.5 peuvent être utilisés autant pour les coupables que pour les victimes : on les emploie lorsque aucun état morbide (lésion traumatique, trouble mental…) n’est mis en évidence, sinon c’est lui qu’on coderait. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z04.4-Z04.6` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-07 — `regle_position`

**Situation** : Z04.800, Z04.801, Z04.802 — codes imposés en DP

**Texte** : Z04.800 (électroencéphalogramme de longue durée) et Z04.801 (enregistrement polygraphique) sont les codes imposés pour le DP de ces séjours ; Z04.802 code les bilans préopératoires ou préinterventionnels. Leur emploi s'impose comme DP qu'une affection ait été diagnostiquée ou non au terme du séjour.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L116-126) :
« Z04.800 est le code imposé pour le DP des séjours motivés par l’enregistrement d’un électroencéphalogramme de longue durée ; Z04.801 est le code imposé pour le DP des séjours motivés par un enregistrement polygraphique ; Z04.802 est le code des examens et mises en observation pour bilan préopératoire ou préinterventionnel ; Z04.880 […]. L’emploi de Z04.800, Z04.801 ou Z04.802 s’impose comme DP du RUM, qu’une affection ait été diagnostiquée ou non au terme du séjour. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z04.800` | `DP` | sujet | chaque | EEG de longue durée |
| `Z04.801` | `DP` | sujet | chaque | enregistrement polygraphique |
| `Z04.802` | `DP` | sujet | chaque | bilan préopératoire ou préinterventionnel |
| `Z04.880` | `regi` | sujet | chaque | autres investigations |

### GM2026-V-XXI-08 — `interdiction`

**Situation** : Z04.8 — devenu inutilisable depuis ses extensions

**Texte** : Depuis la création de ses extensions (version 11 des GHM), Z04.8 est devenu imprécis et n'est plus utilisable comme DP, DR ni DA ; l'emploi des extensions est obligatoire.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L133-136 (note 25)) :
« Elles ont été créées pour la version 11 des GHM (2009). Leur emploi est obligatoire. En effet, Z04.8, devenu imprécis du fait de leur création, n’est plus utilisable comme DP, DR et DA à compter de la version 11 des GHM. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z04.8` | `interdit` | sujet | chaque |  |

### GM2026-V-XXI-09 — `interdiction`

**Situation** : Z04.9 — information trop imprécise

**Texte** : Z04.9 correspond à une information trop imprécise pour être acceptable.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L128) :
« Z04.9 correspond à une information trop imprécise pour être acceptable. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z04.9` | `interdit` | sujet | chaque |  |

### GM2026-V-XXI-10 — `interdiction`

**Situation** : Z03 ou Z04 en DP — pas de diagnostic relié

**Texte** : Lorsqu'un code des catégories Z03 ou Z04 est en position de DP, sauf cas particulier, il ne justifie pas de diagnostic relié.

**Condition** : Sauf cas particulier

**Citation** (`chapitre_xxi.txt` L130-131) :
« Lorsqu’un code des catégories Z03 ou Z04 est en position de DP, sauf cas particulier, il ne justifie pas de diagnostic relié (DR). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z03` | `interdit_DR` | sujet | chaque | quand en DP |
| `Z04` | `interdit_DR` | sujet | chaque | quand en DP |

### GM2026-V-XXI-11 — `regle_position`

**Situation** : Z08 ou Z09 en DP — maladie surveillée en DR

**Texte** : Lorsqu'un code des catégories Z08 ou Z09 est en position de DP, le code de la maladie surveillée doit figurer en position de DR chaque fois qu'elle respecte sa définition. Ces codes sont typiquement des codes de surveillance négative.

**Condition** : La maladie surveillée respecte la définition du DR

**Citation** (`chapitre_xxi.txt` L154-156) :
« Lorsqu’un code des catégories Z08 ou Z09 est en position de DP, le code de la maladie surveillée doit figurer en position de DR chaque fois qu’elle respecte sa définition. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z08` | `DP` | sujet | chaque |  |
| `Z09` | `DP` | sujet | chaque |  |

### GM2026-V-XXI-12 — `definition`

**Situation** : Z08.2 et Z09.2 — sens du mot « chimiothérapie »

**Texte** : Le mot « chimiothérapie » n'a pas dans la CIM–10 le sens implicite de « chimiothérapie antitumorale » qu'il a dans le langage courant : il a son sens premier de « traitement par des moyens chimiques ». Seule Z08 concerne les tumeurs malignes.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L148-153) :
« Z08.2 et Z09.2 : l’intitulé de ces deux sous-catégories contient le mot "chimiothérapie" alors que seule Z08 concerne les tumeurs malignes ; on rappelle en effet que le mot chimiothérapie n’a pas dans la CIM–10 le sens implicite de "chimiothérapie antitumorale" qui est le sien dans le langage courant ; il a son sens premier de "traitement par des moyens chimiques". »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z08.2` | `regi` | sujet | chaque |  |
| `Z09.2` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-13 — `interdiction`

**Situation** : Z10 — sans emploi en MCO

**Texte** : La catégorie Z10 n'a pas d'emploi dans le champ d'activité couvert par le PMSI en MCO : elle ne comprend que des motifs de consultation externe.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L158-161) :
« Elle n’a pas d’emploi dans le champ d’activité couvert par le PMSI en MCO car elle ne comprend que des motifs de consultation externe dont certains ne concernent pas les établissements d’hospitalisation. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z10` | `interdit` | sujet | chaque |  |

### GM2026-V-XXI-14 — `interdiction`

**Situation** : Z11 à Z13 — le dépistage n'est pas l'exploration d'un problème personnel

**Texte** : Les codes Z11 à Z13 ne doivent pas être employés pour des patients présentant un problème de santé personnel. Il est erroné de coder comme un dépistage une situation d'examens motivés par un antécédent personnel ou familial, ou par une symptomatologie quelconque : c'est le motif des explorations qui doit être codé.

**Condition** : Patient présentant un problème de santé personnel

**Citation** (`chapitre_xxi.txt` L163-176) :
« Les codes des catégories Z11 à Z13 ne doivent donc pas être employés pour des patients présentant un problème de santé personnel. Il est erroné de coder comme un dépistage une situation d’examens diagnostiques motivés par un antécédent personnel ou familial […] ou par une symptomatologie quelconque […]. Dans ce cas c’est le motif des explorations qui doit être codé. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z11-Z13` | `interdit` | sujet | chaque | si problème de santé personnel |

### GM2026-V-XXI-15 — `regle_position`

**Situation** : Z13.51 — dépistage de la surdité néonatale permanente

**Texte** : Z13.51 doit être systématiquement codé en DAS lorsqu'un dépistage de la surdité néonatale permanente (test et éventuel retest) est réalisé par OEAA ou PEAA lors d'un séjour de nouveau-né.

**Condition** : Dépistage réalisé par OEAA ou PEAA lors d'un séjour de nouveau-né

**Citation** (`chapitre_xxi.txt` L177-184) :
« le code Z13.51 Examen spécial de dépistage des affections des oreilles doit être systématiquement codé en DAS lorsqu’un dépistage (test et éventuel retest) de la surdité néonatale permanente est réalisé, selon les recommandations de la HAS, par oto-émissions acoustiques automatisées (OEAA) ou par potentiels évoqués auditifs automatisés (PEAA). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z13.51` | `DAS` | sujet | chaque |  |

### GM2026-V-XXI-16 — `condition_emploi`

**Situation** : Z20 — contact avec une maladie transmissible non confirmée

**Texte** : Z20 permet de coder l'absence d'une maladie infectieuse initialement crainte du fait d'un contact ou de toute autre exposition ; si la maladie était confirmée, c'est elle qu'on coderait. L'exemple du guide précise qu'en l'absence de symptôme il n'y a pas lieu d'employer un code du chapitre XVIII, ni de coder la maladie crainte avec le chapitre I.

**Condition** : Maladie infectieuse non confirmée

**Citation** (`chapitre_xxi.txt` L187-213) :
« elle permet de coder l’absence d’une maladie infectieuse initialement crainte du fait du contact du patient avec une personne infectée ou de tout autre mode d’exposition à un agent infectieux […] ; en effet, si la maladie infectieuse était confirmée, c’est elle qu’on coderait. […] cet enfant n’est pas tuberculeux : on ne code donc pas cette maladie (elle ne doit pas être codée avec le chapitre I de la CIM–10) ; il ne présente aucun symptôme […] : il n’y a donc pas lieu d’utiliser un code du chapitre XVIII. Le code est ici Z20.1. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z20` | `regi` | sujet | chaque |  |
| `Z20.1` | `DP` | **exemple** | chaque |  |

### GM2026-V-XXI-17 — `condition_emploi`

**Situation** : Z21 — séropositivité VIH isolée

**Texte** : Z21 code la séropositivité isolée au VIH. Si la séropositivité s'associe à l'un des états classés dans les catégories B20 à B24, c'est un code de celles-ci qu'on emploie, non Z21.

**Condition** : Séropositivité isolée

**Citation** (`chapitre_xxi.txt` L215-217) :
« Z21 est le code de la séropositivité isolée au virus de l’immunodéficience humaine (VIH). Si la séropositivité s’associe à l’un des états classés dans les catégories B20 à B24 du chapitre I de la CIM–10, c’est un code de celles-ci qu’on emploie, non Z21. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `B20-B24` | `interdit_association` | sujet | chaque | exclut Z21 |
| `Z21` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-18 — `definition`

**Situation** : Z22 — colonisations et portages sains

**Texte** : La catégorie Z22, dans la suite logique de Z21, est la catégorie des colonisations (« portages sains »).

**Condition** : —

**Citation** (`chapitre_xxi.txt` L219-220) :
« La catégorie Z22, dans la suite logique de Z21, est la catégorie des colonisations (" portages sains ") : bactéries… »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z22` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-19 — `condition_emploi`

**Situation** : Z29.0 — isolement thérapeutique, non social

**Texte** : Z29.0 n'est pas destiné au classement des situations d'isolement social, qui se codent avec Z60 ; il code l'isolement dans un but thérapeutique. Son emploi est autorisé dans toutes les situations où un patient est isolé pour être mis à l'abri de l'entourage ou pour l'en protéger.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L222-231) :
« la sous-catégorie Z29.0 Isolement n’est pas destinée au classement des situations d’isolement social qui doivent être codées avec la catégorie Z60 ; le code Z29.0 est destiné au codage de l’isolement dans un but thérapeutique […]. Bien que la catégorie Z29 soit classée dans un groupe (Z20–Z29) qui concerne les maladies infectieuses, l’absence d’un autre code d’isolement dans le chapitre XXI conduit à autoriser l’emploi de Z29.0 dans toutes les situations où un patient est isolé. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z29.0` | `regi` | sujet | chaque |  |
| `Z60` | `regi` | sujet | chaque | isolement social |

### GM2026-V-XXI-20 — `condition_emploi`

**Situation** : Z29.1 et Z29.2 — immunothérapie et chimiothérapie prophylactiques

**Texte** : Z29.1 ou Z29.2 peuvent être utilisés lors des séjours motivés par l'administration d'une immunothérapie ou d'une chimiothérapie prophylactique, quel qu'en soit le motif, à condition que le caractère prophylactique soit établi.

**Condition** : Caractère prophylactique établi

**Citation** (`chapitre_xxi.txt` L232-235) :
« Z29.1 ou Z29.2 peuvent être utilisés lors des séjours motivés par l’administration d’une immunothérapie ou d’une chimiothérapie prophylactique, quel qu’en soit le motif (infectieux, tumoral…), mais à condition que le caractère prophylactique (préventif) soit établi. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z29.1` | `regi` | sujet | chaque |  |
| `Z29.2` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-21 — `condition_emploi`

**Situation** : Z20 à Z29 — catégories utilisables en MCO et droit au DR

**Texte** : Parmi les catégories Z20 à Z29, seules Z20, Z21, Z22 et Z29 sont en pratique susceptibles d'être utilisées pour le codage des RUM. Si un code de ces rubriques est en DP, seuls ceux de la catégorie Z29 sont susceptibles de justifier un DR.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L237-241) :
« Dans le champ actuel du PMSI en MCO, parmi les catégories Z20 à Z29, seules Z20, Z21, Z22 et Z29 sont, en pratique, susceptibles d’être utilisées pour le codage des RUM. Si un code de ces rubriques est en position de diagnostic principal (DP) d’un RUM, seuls ceux de la catégorie Z29 sont susceptibles de justifier un DR, à condition que l’affection concernée respecte sa définition. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z20` | `interdit_DR` | sujet | chaque | quand en DP |
| `Z21` | `interdit_DR` | sujet | chaque | quand en DP |
| `Z22` | `interdit_DR` | sujet | chaque | quand en DP |
| `Z29` | `regi` | sujet | chaque | seule à justifier un DR |

### GM2026-V-XXI-22 — `regle_position`

**Situation** : Z33 — grossesse normale chez une femme hospitalisée pour un autre motif

**Texte** : Z33 permet d'enregistrer la grossesse comme diagnostic associé lorsqu'une femme enceinte est hospitalisée pour un motif sans rapport avec elle et qu'elle se déroule normalement.

**Condition** : Motif d'hospitalisation sans rapport avec la grossesse ; grossesse normale

**Citation** (`chapitre_xxi.txt` L245-249) :
« La catégorie Z33 permet, dans le cas d’une femme enceinte hospitalisée pour un motif sans rapport avec sa grossesse, d’enregistrer celle-ci comme diagnostic associé lorsqu’elle se déroule normalement. Exemple : traumatisme de la jambe chez une femme enceinte ; DP : la lésion de la jambe ; diagnostic associé : Z33. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z33` | `DAS` | sujet | chaque |  |

### GM2026-V-XXI-23 — `condition_emploi`

**Situation** : Z34 et Z35 — surveillance de grossesse

**Texte** : Z34 comprend la surveillance des grossesses normales, Z35 celle de toutes les autres — l'intitulé « à haut risque » ne doit pas être lu de manière rigide. Dans les hospitalisations de l'antepartum, la mention d'un code Z35.– est indispensable à l'orientation correcte du RSS dans les GHM de l'antepartum.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L251-259) :
« Z34 comprend la surveillance systématique de la grossesse normale […]. L’intitulé de la catégorie Z35 Surveillance d’une grossesse à haut risque ne doit pas être lu de manière rigide. […] Z34 pour les grossesses normales et Z35 pour les autres, c’est-à-dire pour toutes les non normales (à risque, "haut" ou non). Dans le cas des hospitalisations de l’antepartum, la mention d’un code Z35.– est indispensable à l’orientation correcte du résumé de sortie standardisé (RSS) dans les groupes homogènes de malades (GHM) de l’antepartum. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z34` | `regi` | sujet | chaque | grossesse normale |
| `Z35.–` | `regi` | sujet | chaque | toute grossesse non normale |

### GM2026-V-XXI-24 — `regle_position`

**Situation** : Z37 — résultat de l'accouchement

**Texte** : La mention d'un code de la catégorie Z37 comme diagnostic associé est indispensable au classement du RSS dans un GHM d'accouchement ; un code de cette catégorie doit être enregistré dans les RSS de tous les séjours comportant un accouchement.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L263-267) :
« la mention d’un de ses codes comme diagnostic associé est indispensable au classement du RSS dans un GHM d’accouchement. Un code de cette catégorie doit être enregistré dans les RSS de tous les séjours comportant un accouchement. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z37` | `DAS` | sujet | chaque |  |

### GM2026-V-XXI-25 — `regle_position`

**Situation** : Z38.0 — nouveau-né en bonne santé en maternité

**Texte** : Z38.0 est le code du DP du RUM du nouveau-né dont le séjour se déroule en maternité auprès de sa mère ; dans cette situation il ne justifie aucun diagnostic relié. Lorsque le DP du séjour d'un nouveau-né est un problème de santé, son code doit être d'abord cherché dans le chapitre XVI.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L269-276) :
« Z38.0 est le code du DP du RUM du nouveau-né dont le séjour se déroule en maternité auprès de sa mère. Dans cette situation il ne justifie aucun diagnostic relié. Lorsque le diagnostic principal du séjour d’un nouveau-né est un problème de santé, son code doit être d’abord cherché dans le chapitre XVI de la CIM–10 (puis, à défaut, dans un autre chapitre). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z38.0` | `DP` | sujet | chaque |  |
| `Z38.0` | `interdit_DR` | sujet | chaque | quand en DP |

### GM2026-V-XXI-26 — `regle_position`

**Situation** : Z39 — soins et examens du postpartum

**Texte** : Un code Z39 est toujours requis pour les séjours du postpartum ; il ne doit pas être enregistré d'acte d'accouchement dans le RUM, et un code de la catégorie Z37 doit être saisi en diagnostic associé.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L278-282) :
« Ce code est toujours requis pour les séjours du postpartum. — il ne doit pas être enregistré d’acte d’accouchement dans le RUM ; — un code de la catégorie Z37 Résultat de l’accouchement doit être saisi en position de diagnostic associé. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z37` | `DAS` | sujet | chaque |  |
| `Z39` | `DP` | sujet | chaque |  |

### GM2026-V-XXI-27 — `regle_position`

**Situation** : Transfert pour soins du postpartum (E1 vers E2)

**Texte** : Lorsqu'après un accouchement dans un établissement E1 une mère est transférée avec son enfant dans un établissement E2 pour les soins du postpartum, le DP du RUM de la mère est codé Z39.08 et celui du nouveau-né Z76.2.

**Condition** : Soins standard, pas de complication, nouveau-né normal

**Citation** (`chapitre_xxi.txt` L291-297) :
« Lorsqu’après accouchement dans un établissement de santé E1, une mère est transférée avec son enfant dans un établissement de santé E2 pour les soins du postpartum (soins standard, pas de complication, nouveau-né normal), dans E2 : le DP du RUM de la mère est codé Z39.08 […] ; le DP du RUM du nouveau-né est codé Z76.2. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z39.08` | `DP` | sujet | chaque | mère |
| `Z76.2` | `DP` | sujet | chaque | nouveau-né |

### GM2026-V-XXI-28 — `regle_position`

**Situation** : Z40 — actes prophylactiques et thérapeutiques pour tumeur maligne

**Texte** : Z40.0 a reçu des extensions signalant l'organe opéré. L'emploi des codes Z40 concerne aussi les interventions à but thérapeutique ou prophylactique portant sur d'autres localisations : une ovariectomie de castration pour cancer du sein hormonosensible se code Z40.01 en DP.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L305-311) :
« des extensions, permettant de signaler l’organe opéré, ont été ajoutées au code "Z40.0 = opération prophylactique pour facteur de risque de tumeur maligne". L’utilisation des codes Z40 concerne également les interventions réalisées à but thérapeutique ou prophylactique, dans le cadre de la prise en charge de tumeurs malignes portant sur d’autres localisations. Ainsi, dans le cadre du traitement d’un cancer du sein hormonosensible, une ovariectomie pour castration doit être codée avec le code Z40.01 en DP. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z40` | `regi` | sujet | chaque |  |
| `Z40.01` | `DP` | sujet | chaque | ovariectomie de castration |

### GM2026-V-XXI-29 — `regle_position`

**Situation** : Z41 — chirurgie esthétique et interventions de confort

**Texte** : Lorsqu'il s'agit de chirurgie esthétique, le DP doit toujours être codé Z41.0 ou Z41.1, à l'exclusion de tout autre code ; le défaut corrigé peut être codé en DR. Z41.80 code les interventions dites de confort.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L324-341) :
« lorsqu’il s’agit de chirurgie esthétique le DP doit toujours être codé Z41.0 ou Z41.1, à l’exclusion de tout autre code ; le défaut corrigé peut être codé en position de diagnostic relié (DR). — La catégorie Z41 comprend les soins "sans raison médicale" […]. Elle est notamment destinée au codage du DP des séjours pour chirurgie esthétique (Z41.0, Z41.1) et pour intervention dite de confort (Z41.80). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z41.0` | `DP` | sujet | chaque | chirurgie esthétique |
| `Z41.1` | `DP` | sujet | chaque | chirurgie esthétique |
| `Z41.80` | `DP` | sujet | chaque | intervention de confort |

### GM2026-V-XXI-30 — `regle_position`

**Situation** : Z42 — chirurgie plastique non esthétique

**Texte** : Pour une chirurgie plastique non esthétique, de réparation d'une lésion congénitale ou acquise prise en charge par l'assurance maladie, le DP est codé avec un autre code de la CIM–10 — un code des chapitres I à XIX ou un code de la catégorie Z42 — le meilleur code étant le plus précis. Avec un DP codé Z42.–, le motif de l'intervention peut être mentionné en DR.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L342-356) :
« lorsqu’il s’agit de chirurgie plastique non esthétique, de réparation d’une lésion congénitale ou acquise, prise en charge par l’assurance maladie obligatoire, le DP doit être codé avec un autre code de la CIM–10 ; il peut s’agir d’un code des chapitres I à XIX ou d’un code de la catégorie Z42 […]. Avec un DP codé Z42.– le motif de l’intervention peut être mentionné en position de DR s’il respecte sa définition. Exemples : – mise en place de prothèses internes pour augmentation du volume mammaire à visée esthétique : Z41.1 ; – mise en place d’une prothèse mammaire interne après mastectomie : Z42.1 ; – rhinoplastie à visée esthétique : Z41.1 ; – rhinoplastie pour déviation de la cloison nasale : J34.2 ; – exérèse d’une cicatrice chéloïde : L91.0. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `J34.2` | `DP` | **exemple** | chaque | rhinoplastie pour déviation de cloison |
| `L91.0` | `DP` | **exemple** | chaque | exérèse de cicatrice chéloïde |
| `Z41.1` | `DP` | **exemple** | chaque | prothèse mammaire à visée esthétique |
| `Z42.1` | `DP` | **exemple** | chaque | prothèse mammaire après mastectomie |
| `Z42.–` | `DP` | sujet | chaque |  |

### GM2026-V-XXI-31 — `definition`

**Situation** : Z43 — soins de stomie ponctuels, opposés à Z93

**Texte** : Z43 est une rubrique de soins de stomie ponctuels, incluant la fermeture de la stomie. Elle exclut les soins habituels effectuables à domicile, qui se codent avec Z93, et les complications comprises dans J95.0, K91.4 et N99.5.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L364-370) :
« La catégorie Z43 est une rubrique de soins de stomie. Elle comprend des soins médicaux ponctuels […] incluant la fermeture de la stomie. […] La catégorie Z43 exclut les soins habituels tels qu’effectués ou effectuables à domicile (soins quotidiens d’hygiène, changements de poche ou de canule de trachéostomie) qui se codent avec la catégorie Z93 (voir plus loin). Elle exclut aussi les complications comprises dans les rubriques J95.0, K91.4 et N99.5. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `J95.0` | `interdit_association` | sujet | chaque | complication |
| `K91.4` | `interdit_association` | sujet | chaque | complication |
| `N99.5` | `interdit_association` | sujet | chaque | complication |
| `Z43` | `regi` | sujet | chaque |  |
| `Z93` | `interdit_association` | sujet | chaque | soins habituels à domicile |

### GM2026-V-XXI-32 — `regle_position`

**Situation** : Z45.0 — implantation d'un stimulateur ou défibrillateur cardiaque

**Texte** : Par convention, le DP d'un séjour pour l'implantation d'un stimulateur ou d'un défibrillateur cardiaque est la cardiopathie qui la justifie, et non Z45.0.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L388-389) :
« Par convention, le diagnostic principal d’un séjour pour l’implantation d’un stimulateur ou d’un défibrillateur cardiaque est la cardiopathie qui la justifie, et non Z45.0. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z45.0` | `interdit_DP` | sujet | chaque |  |

### GM2026-V-XXI-33 — `regle_position`

**Situation** : Z49.0 — confection d'une fistule de dialyse

**Texte** : Le DP des séjours pour mise en place d'une fistule de dialyse rénale est codé Z49.0 et non Z45.2. La catégorie Z49, malgré le mot « surveillance » de son intitulé, comprend les prises en charge pour actes de préparation à la dialyse rénale.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L394-396 et L434-438) :
« Le DP des séjours pour mise en place d’une fistule de dialyse rénale est codé Z49.0 et non Z45.2. — La catégorie Z49, malgré la présence du mot "surveillance" dans son intitulé, comprend les prises en charge pour des actes de préparation à la dialyse rénale ; Z49.0 comprend ainsi la mise en place des fistules et cathéters de dialyse. […] il faut coder Z49.0 (et non Z45.2) le DP des séjours pour la confection d’une fistule. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z45.2` | `interdit_DP` | sujet | chaque | confection de fistule |
| `Z49.0` | `DP` | sujet | chaque |  |

### GM2026-V-XXI-34 — `regle_position`

**Situation** : Z45.84 — mise en place d'un stimulateur du système nerveux central

**Texte** : Le DP des hospitalisations pour la mise en place d'un stimulateur du système nerveux central (cérébral ou médullaire) doit être codé Z45.84.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L398-401) :
« Le DP des hospitalisations pour la mise en place d’un stimulateur du système nerveux central (cérébral ou médullaire) doit être codé Z45.84 Ajustement et entretien d’une prothèse interne du système nerveux central. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z45.84` | `DP` | sujet | chaque |  |

### GM2026-V-XXI-35 — `interdiction`

**Situation** : Z43 ou Z45 en DA redondant avec un acte CCAM

**Texte** : Lorsqu'un code des catégories Z43 ou Z45 correspond à une prise en charge pour laquelle un code d'acte existe dans la CCAM, la saisie dans le même RUM du code Z43.– ou Z45.– en position de diagnostic associé, en sus de celui de l'acte, est redondante et n'est pas justifiée.

**Condition** : Un code d'acte CCAM existe pour la prise en charge

**Citation** (`chapitre_xxi.txt` L405-410) :
« Lorsqu’un code des catégories Z43 ou Z45 de la CIM–10 correspond à une prise en charge pour laquelle un code d’acte existe dans la CCAM, la saisie dans le même RUM du code Z43.– ou Z45.– en position de diagnostic associé (DA) en sus de celui de l’acte est redondante et n’est pas justifiée. Un tel emploi de "codes Z" serait incorrect au regard de la CIM–10. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z43.–` | `interdit_DAS` | sujet | chaque | acte CCAM présent |
| `Z45.–` | `interdit_DAS` | sujet | chaque | acte CCAM présent |

### GM2026-V-XXI-36 — `regle_position`

**Situation** : Z47.0 — ablation de matériel d'ostéosynthèse

**Texte** : Z47.0 doit être utilisé pour coder le DP des séjours pour ablation de matériel d'ostéosynthèse. Au terme de ces séjours, il ne faut pas coder à nouveau la lésion osseuse initiale guérie ou consolidée, ni comme DP, ni comme DR, ni comme diagnostic associé. Z47.0 code aussi le DP des séjours pour retrait d'un espaceur et repose de prothèse définitive.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L418-427) :
« Z47.0 doit notamment être utilisé pour coder le DP des séjours pour ablation de matériel d’ostéosynthèse ; il ne faut pas, au terme de ces séjours, coder à nouveau la lésion osseuse initiale guérie ou consolidée, ni comme DP, ni comme DR, ni comme diagnostic associé ; elle ne peut éventuellement être qu’une donnée à visée documentaire. Le DP des séjours pour retrait de prothèse temporaire de type espaceur (spacer), mise en place suite à une infection, et repose de prothèse définitive se code Z47.0. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z47.0` | `DP` | sujet | chaque |  |

### GM2026-V-XXI-37 — `definition`

**Situation** : Z48 — soins postinterventionnels immédiats

**Texte** : Z48 peut être employée pour les soins postinterventionnels immédiats : surveillance postopératoire et surveillance faisant suite à un acte médicotechnique (endoscopie, endovasculaire, imagerie interventionnelle).

**Condition** : —

**Citation** (`chapitre_xxi.txt` L429-432) :
« La catégorie Z48 peut être employée pour les soins postinterventionnels immédiats. Par soins postinterventionnels on entend notamment la surveillance postopératoire et celle qui fait suite à un acte médicotechnique tel qu’une intervention par voie endoscopique ou endovasculaire et l’imagerie interventionnelle. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z48` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-38 — `regle_position`

**Situation** : Z51 — séjours pour actes thérapeutiques

**Texte** : Tous les séjours pour chimiothérapie, radiothérapie, transfusion sanguine, aphérèse sanguine ou oxygénothérapie hyperbare, qu'il s'agisse de séances ou d'hospitalisation complète, doivent comporter en DP le code ad hoc de la catégorie Z51. Z51.1 code le DP des séjours pour chimiothérapie pour tumeur ; Z51.2 les autres chimiothérapies ; Z51.30 la transfusion sanguine ; Z51.31 l'aphérèse.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L455, L460-463, L469-470, L475-478) :
« Tous les séjours pour chimiothérapie, radiothérapie, transfusion sanguine, aphérèse sanguine, oxygénothérapie hyperbare, qu’il s’agisse de séances ou d’hospitalisation complète, doivent comporter en position de DP le code ad hoc de la catégorie Z51 de la CIM–10. — Z51.1 code le DP des séjours pour chimiothérapie pour tumeur. — Z51.2 est employé pour les autres séjours pour "chimiothérapie", dès lors que l’affection traitée n’est pas une tumeur. — Z51.30 est le code du DP des séjours pour transfusion sanguine ; Z51.31 est le code du DP des séjours pour aphérèse sanguine. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z51` | `DP` | sujet | chaque |  |
| `Z51.1` | `DP` | sujet | chaque | chimiothérapie pour tumeur |
| `Z51.2` | `DP` | sujet | chaque | chimiothérapie non antitumorale |
| `Z51.30` | `DP` | sujet | chaque | transfusion sanguine |
| `Z51.31` | `DP` | sujet | chaque | aphérèse sanguine |

### GM2026-V-XXI-39 — `regle_position`

**Situation** : Z51 en DP — la maladie traitée en diagnostic relié

**Texte** : Lorsqu'un code Z51.0–, Z51.1, Z51.2, Z51.3–, Z51.5 ou Z51.8– est en position de DP, la maladie traitée est enregistrée comme diagnostic relié chaque fois qu'elle respecte sa définition, ce qui est le plus souvent le cas.

**Condition** : La maladie traitée respecte la définition du DR

**Citation** (`chapitre_xxi.txt` L480-482) :
« Lorsqu’un code Z51.0–, Z51.1, Z51.2, Z51.3–, Z51.5 ou Z51.8– est en position de DP, la maladie traitée est enregistrée comme diagnostic relié chaque fois qu’elle respecte sa définition, ce qui est le plus souvent le cas. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z51.0` | `DP` | sujet | chaque |  |
| `Z51.1` | `DP` | sujet | chaque |  |
| `Z51.2` | `DP` | sujet | chaque |  |
| `Z51.3` | `DP` | sujet | chaque |  |
| `Z51.5` | `DP` | sujet | chaque |  |
| `Z51.8` | `DP` | sujet | chaque |  |

### GM2026-V-XXI-40 — `interdiction`

**Situation** : Z51 en DA redondant avec un acte CCAM

**Texte** : Lorsqu'un code de la catégorie Z51 correspond à une prise en charge pour laquelle un code d'acte existe dans la CCAM, la saisie du code Z51.– en diagnostic associé en sus de celui de l'acte est redondante et n'est pas justifiée. Z51.00 et Z51.01 font exception : lorsqu'un acte d'irradiation est effectué au cours d'une hospitalisation pour un autre motif, Z51.01 figure dans le même RUM que l'acte.

**Condition** : Un code d'acte CCAM existe ; hors Z51.00 et Z51.01

**Citation** (`chapitre_xxi.txt` L484-493) :
« Lorsqu’un code de la catégorie Z51 de la CIM–10 correspond à une prise en charge pour laquelle un code d’acte existe dans la CCAM, la saisie dans le même RUM du code Z51.– en position de diagnostic associé (DA) en sus de celui de l’acte est redondante et n’est pas justifiée. […] Z51.00 Séance de préparation à une irradiation et Z51.01 Séance d’irradiation font exception. Lorsqu’un acte d’irradiation est effectué au cours d’une hospitalisation pour un autre motif (un autre DP), Z51.01 figure dans le même RUM que l’acte. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z51.00` | `regi` | sujet | chaque | exception |
| `Z51.01` | `DAS` | sujet | chaque | exception : irradiation au cours d'un autre séjour |
| `Z51.–` | `interdit_DAS` | sujet | chaque | acte CCAM présent |

### GM2026-V-XXI-41 — `regle_position`

**Situation** : Z52 — prélèvement d'organes ou de tissus

**Texte** : Les codes de la catégorie Z52 sont utilisés pour le codage du DP du RSS produit pour un sujet admis aux fins de prélèvements d'organes ou de tissus. Z52.80 Donneuse d'ovocytes est employé comme DP du séjour pour prélèvement d'ovocytes, et comme diagnostic associé en cas de partage (egg sharing).

**Condition** : —

**Citation** (`chapitre_xxi.txt` L517-525) :
« Les codes de la catégorie Z52 sont utilisés pour le codage du diagnostic principal du RSS produit pour un sujet admis aux fins de prélèvements d’organes ou de tissus. Le code étendu national Z52.80 Donneuse d’ovocytes a été créé pour être utilisé depuis 2012 dans deux circonstances : comme diagnostic principal du séjour pour prélèvement d’ovocytes ; comme diagnostic associé du séjour de prélèvement d’ovocytes en cas de partage (egg sharing). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z52` | `DP` | sujet | chaque |  |
| `Z52.80` | `DAS` | sujet | chaque | egg sharing |
| `Z52.80` | `DP` | sujet | chaque | prélèvement d'ovocytes |

### GM2026-V-XXI-42 — `condition_emploi`

**Situation** : Z53 — soins prévus non prodigués

**Texte** : Z53 permet le codage des circonstances dans lesquelles les soins prévus à l'admission ne sont pas prodigués ; le mot « acte » de l'intitulé doit être lu au sens étendu de « prestation de soins », « prise en charge ».

**Condition** : —

**Citation** (`chapitre_xxi.txt` L527-532) :
« La catégorie Z53 permet le codage des circonstances dans lesquelles les soins prévus à l’admission ne sont pas prodigués ; le mot acte de l’intitulé doit être lu avec l’acception étendue de "prestation de soins", "prise en charge". Exemples : – refus d’une transfusion sanguine pour motif de conviction : Z53.1 ; – sortie contre avis médical ou par fuite : Z53.2. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z53` | `regi` | sujet | chaque |  |
| `Z53.1` | `regi` | **exemple** | chaque | refus pour motif de conviction |
| `Z53.2` | `regi` | **exemple** | chaque | sortie contre avis médical |

### GM2026-V-XXI-43 — `regle_position`

**Situation** : Z65.1 — personne détenue

**Texte** : Z65.1 Emprisonnement ou autre incarcération doit être enregistré en position de diagnostic associé lorsque les soins ont été dispensés à une personne détenue.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L552-553) :
« Z65.1 Emprisonnement ou autre incarcération doit être enregistré en position de diagnostic associé lorsque les soins ont été dispensés à une personne détenue. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z65.1` | `DAS` | sujet | chaque |  |

### GM2026-V-XXI-44 — `condition_emploi`

**Situation** : Z74.2 — défaillance de l'aide à domicile

**Texte** : Z74.2 est employé lorsqu'une personne qui ne peut vivre à son domicile qu'avec une aide doit être hospitalisée, ou maintenue en hospitalisation, du fait de l'absence ou de la défaillance de celle-ci.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L555-562) :
« Z74.2 Besoin d’assistance à domicile, aucun autre membre du foyer n’étant capable d’assurer les soins est employé lorsqu’une personne qui ne peut vivre à son domicile qu’avec une aide, doit être hospitalisée ou maintenue en hospitalisation du fait de l’absence ou de la défaillance de celle-ci. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z74.2` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-45 — `condition_emploi`

**Situation** : Z75.1 — attente d'admission ailleurs

**Texte** : Z75.1 ne doit être employé que si le séjour ou la prolongation de l'hospitalisation est motivé par la seule attente de l'unité ou de l'établissement adéquat, et non par un événement morbide.

**Condition** : Séjour motivé par la seule attente

**Citation** (`chapitre_xxi.txt` L564-566) :
« Z75.1 Sujet attendant d’être admis ailleurs, dans un établissement adéquat ne doit être employé que si le séjour ou la prolongation de l’hospitalisation est motivé par la seule attente de l’unité ou de l’établissement adéquat, non par un évènement morbide. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z75.1` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-46 — `definition`

**Situation** : Z75.80 — sens du mot « acte »

**Texte** : Dans l'intitulé de Z75.80, le mot « acte » ne doit pas être limité à la notion d'acte médicotechnique : il doit être compris au sens large de « prestation de soins », « prise en charge ».

**Condition** : —

**Citation** (`chapitre_xxi.txt` L575-577) :
« Dans l’intitulé de Z75.80 Sujet adressé dans un autre établissement, pour réalisation d’un acte, le sens du mot "acte" ne doit pas être limité à la notion d’acte médicotechnique. Il doit être compris avec le sens large de "prestation de soins", "prise en charge". »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z75.80` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-47 — `regle_position`

**Situation** : Z76.800 — infection ostéoarticulaire complexe

**Texte** : Z76.800 doit être enregistré comme DA dès lors que le patient a fait l'objet d'une réunion de concertation pluridisciplinaire visée par un centre interrégional de référence ayant confirmé le caractère complexe de l'IOA. Même si une seule RCP a été réalisée, Z76.800 doit être saisi dans les RUM de tous les séjours ultérieurs motivés par la prise en charge de l'IOA.

**Condition** : RCP visée par un centre interrégional de référence

**Citation** (`chapitre_xxi.txt` L585-591) :
« Z76.800 Sujet ayant recours aux services de santé après une réunion de concertation pluridisciplinaire [RCP] ayant établi la complexité d’une infection ostéoarticulaire doit être enregistré comme DA dès lors que le patient a fait l’objet d’une réunion de concertation pluridisciplinaire visée par un centre interrégional de référence ayant confirmé le caractère complexe de l’IOA. Même si une seule RCP a été réalisée, Z76.800 doit être saisi dans les RUM de tous les séjours ultérieurs du patient motivés par la prise en charge de l’IOA. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z76.800` | `DAS` | sujet | chaque |  |

### GM2026-V-XXI-48 — `regle_position`

**Situation** : Z76.850 — nouveau-né recevant du lait d'un lactarium

**Texte** : Z76.850 doit être enregistré comme DA dans le RUM du séjour des nouveau-nés recevant du lait d'un lactarium.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L593-594) :
« Pour identifier les nouveau-nés recevant du lait d’un lactarium, Z76.850 Enfant recevant du lait provenant d’un lactarium doit être enregistré comme DA dans le RUM de leur séjour. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z76.850` | `DAS` | sujet | chaque |  |

### GM2026-V-XXI-49 — `interdiction`

**Situation** : Z80 à Z92 — un DP d'antécédent ne justifie jamais de DR

**Texte** : Les codes des catégories Z80 à Z92 peuvent notamment être utilisés pour le codage du DP dans des situations diagnostiques. Un DP d'antécédent personnel ou familial de maladie ne justifie jamais de diagnostic relié.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L597-604) :
« Les codes de ces catégories peuvent notamment être utilisés pour le codage du DP dans des situations de diagnostique au sens du guide des situations cliniques […]. Exemple : patient ayant un antécédent familial de cancer colique, hospitalisé pour coloscopie, où la coloscopie ne retrouve aucune lésion : le DP est Z80.00. Un DP d’antécédent personnel ou familial de maladie ne justifie jamais de diagnostic relié. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z80-Z92` | `interdit_DR` | sujet | chaque | quand en DP |
| `Z80.00` | `DP` | **exemple** | chaque | antécédent familial de cancer colique |

### GM2026-V-XXI-50 — `condition_emploi`

**Situation** : Z92.1 et Z92.2 — traitements pris antérieurement

**Texte** : Ces codes peuvent être employés lorsqu'un recours aux soins est motivé par la prise d'un médicament prescrit antérieurement, que la prise soit poursuivie (« utilisation actuelle ») ou qu'elle ait cessé au moment du recours — l'acception du mot « antécédent » étant large dans la CIM–10.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L606-613) :
« Z92.1 et Z92.2 : la complexité apparente de leur intitulé est due à l’acception étymologique large du mot "antécédent" qui est celle de la CIM–10. Ces codes peuvent être employés lorsqu’un recours aux soins est motivé par la prise d’un médicament prescrit antérieurement, que la prise soit poursuivie ("utilisation actuelle") ou qu’elle ait cessé au moment du recours. Exemple : patient porteur d’une valve cardiaque prothétique, prenant un antivitamine K (AVK) au long cours, hospitalisé pour extractions dentaires : le DP est l’affection dentaire, la prise de l’AVK (Z92.1) est un DAS. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z92.1` | `DAS` | sujet | chaque |  |
| `Z92.2` | `DAS` | sujet | chaque |  |

### GM2026-V-XXI-51 — `definition`

**Situation** : Z93 — soins habituels de stomie, opposés à Z43

**Texte** : Z93 est employée pour le codage des soins de stomie habituels, tels qu'effectués ou effectuables à domicile (soins quotidiens d'hygiène, changements de poche, changements de canule de trachéostomie). Elle s'oppose à Z43.

**Condition** : —

**Citation** (`chapitre_xxi.txt` L614-618) :
« La catégorie Z93 est une rubrique relative aux stomies. On l’emploie pour le codage des soins habituels tels qu’effectués ou effectuables à domicile (soins quotidiens d’hygiène, changements de poche, changements de canule de trachéostomie). Elle s’oppose à la catégorie Z43. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z43` | `interdit_association` | sujet | chaque | soins ponctuels |
| `Z93` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-52 — `regle_position`

**Situation** : Z94 et Z95 — surveillance négative de greffes et prothèses

**Texte** : Z94 et Z95 sont employées pour coder le DP des situations de surveillance négative des porteurs d'organe ou de tissu greffé (Z94), de pontage coronaire, de prothèse endoartérielle, de prothèse valvulaire cardiaque et autres implants cardiaques et vasculaires (Z95).

**Condition** : Surveillance négative (aucune anomalie constatée)

**Citation** (`chapitre_xxi.txt` L620-640 et L692-693 (note 47)) :
« Les catégories Z94 et Z95 sont employées pour coder le DP des situations de surveillance négative des porteurs d’organe ou de tissu greffé (Z94), de pontage coronaire et de prothèse endoartérielle (stent), de prothèse valvulaire cardiaque et "autres implants et greffes et cardiaques et vasculaires". Exemples : – patient porteur d’un cœur transplanté […] aucune anomalie n’est constatée ; le DP du séjour est codé Z94.1 ; – patient porteur d’un pontage coronaire hospitalisé pour bilan de surveillance ; aucune anomalie n’est constatée : le DP du séjour est codé Z95.1. — Un rejet, en revanche, doit être codé T86.2. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `T86.2` | `regi` | **exemple** | chaque | un rejet se code T86.2 |
| `Z94` | `DP` | sujet | chaque |  |
| `Z94.1` | `DP` | **exemple** | chaque | cœur transplanté |
| `Z95` | `DP` | sujet | chaque |  |
| `Z95.1` | `DP` | **exemple** | chaque | pontage coronaire |

### GM2026-V-XXI-53 — `condition_emploi`

**Situation** : Z96 et Z97 — présence d'implants et prothèses

**Texte** : Z96 et Z97 permettent le codage de la présence de divers implants, prothèses et appareils. Leur emploi n'est admissible qu'en l'absence de complication.

**Condition** : Absence de complication

**Citation** (`chapitre_xxi.txt` L642-645) :
« Les catégories Z96 et Z97 permettent le codage de la présence de divers implants, prothèses et appareils. Leur emploi n’est admissible qu’en l’absence de complication. En cas de soins nécessités par une complication, se reporter plus haut dans ce chapitre au point traitant des complications des actes médicaux et chirurgicaux. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z96` | `regi` | sujet | chaque |  |
| `Z97` | `regi` | sujet | chaque |  |

### GM2026-V-XXI-54 — `interdiction`

**Situation** : Z93, Z95 ou Z96 en DA redondant avec un acte CCAM

**Texte** : Lorsqu'un code des catégories Z93, Z95 ou Z96 correspond à une prise en charge pour laquelle un code d'acte existe dans la CCAM, la saisie du code Z93.–, Z95.– ou Z96.– en diagnostic associé en sus de celui de l'acte est redondante et n'est pas justifiée.

**Condition** : Un code d'acte CCAM existe pour la prise en charge

**Citation** (`chapitre_xxi.txt` L647-662) :
« Lorsqu’un code des catégories Z93, Z95 ou Z96 de la CIM–10 correspond à une prise en charge pour laquelle un code d’acte existe dans la CCAM, la saisie dans le même RUM du code Z93.–, Z95.– ou Z96.– en position de diagnostic associé (DA) en sus de celui de l’acte est redondante et n’est pas justifiée. Un tel emploi de "codes Z" serait incorrect au regard de la CIM–10. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z93.–` | `interdit_DAS` | sujet | chaque | acte CCAM présent |
| `Z95.–` | `interdit_DAS` | sujet | chaque | acte CCAM présent |
| `Z96.–` | `interdit_DAS` | sujet | chaque | acte CCAM présent |

### GM2026-V-XXI-55 — `condition_emploi`

**Situation** : Z99 — dépendance chronique, non phase aigüe

**Texte** : Est dépendante envers une machine une personne atteinte d'une affection chronique dont la survie est subordonnée à l'utilisation régulière et durable de ce matériel. Les codes Z99 ne doivent pas être employés pour mentionner l'utilisation d'un tel matériel en phase aigüe.

**Condition** : Affection chronique ; pas d'emploi en phase aigüe

**Citation** (`chapitre_xxi.txt` L664-674) :
« Est dépendante envers une machine ou un appareil une personne atteinte d’une affection chronique dont la survie est subordonnée à l’utilisation régulière et durable de ce matériel. C’est en ce sens que doit être comprise l’utilisation des codes de la catégorie Z99. Ils ne doivent pas être employés pour mentionner l’utilisation d’un matériel de ce type en phase aigüe : par exemple, Z99.0 Dépendance envers un aspirateur ou Z99.1 Dépendance envers un respirateur ne doivent pas servir à mentionner l’utilisation de ces matériels chez un patient sous ventilation mécanique pour insuffisance respiratoire aigüe, Z99.2 Dépendance envers une dialyse rénale ne peut pas être employé pour les séjours des patients dialysés pour insuffisance rénale aigüe. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z99` | `interdit` | sujet | chaque | en phase aigüe |
| `Z99.0` | `interdit` | **exemple** | chaque | ventilation en insuffisance respiratoire aigüe |
| `Z99.1` | `interdit` | **exemple** | chaque | ventilation en insuffisance respiratoire aigüe |
| `Z99.2` | `interdit` | **exemple** | chaque | dialyse pour insuffisance rénale aigüe |

