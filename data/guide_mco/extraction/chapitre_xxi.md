# Candidates — EMPLOI DES CODES DU CHAPITRE XXI DE LA CIM-10

> **Statut : à valider ligne à ligne. Rien ici n'est dans les tables curées.**
>
> Source : `data/guide_mco/extraits/chapitre_xxi.txt` (chap. V,
> pp. imprimées 93-103). Les `L…` renvoient à ce fichier.

C'est de loin le plus dense des quatre articles : **onze pages, une
cinquantaine de consignes**, organisées par groupes de catégories Z.
J'ai suivi l'ordre du guide.

**Trois remarques avant la liste**, parce qu'elles conditionnent la
lecture :

1. **Un rôle manque, et il manque souvent.** Cinq consignes de cet
   article interdisent l'emploi d'un code **en position de diagnostic
   associé** (redondance avec un acte CCAM). Les huit rôles connaissent
   `interdit_DP` et `interdit_DR`, mais **pas `interdit_DAS`**. Détail
   au §Extensions d'enum en fin de fichier — c'est le point le plus
   important de ce fichier.
2. **La consigne de niveau chapitre existe bien** (XXI-01) : c'est elle
   qui atteindra les 750 fiches du chapitre XXI, et c'est elle que le
   test de rendu attend sur « un Z quelconque non cité par le guide ».
3. **Beaucoup de rôles `contexte`** — même remarque que pour l'AVC :
   le guide régit très souvent un code sans lui assigner de position.

---

## §A — Règle générale du chapitre

### GM2026-V-XXI-01 — `definition`
**Situation** : Emploi général des codes du chapitre XXI
**Texte** : Les codes du chapitre XXI (« codes Z ») peuvent, et souvent doivent, être utilisés dans le RUM comme diagnostic principal, relié ou associé.
**Condition** : —
**Citation** (L39-42) : « Les codes du chapitre XXI Facteurs influant sur l'état de santé et motifs de recours aux services de santé ("codes Z") peuvent, et souvent doivent, être utilisés dans le résumé d'unité médicale (RUM) comme diagnostic principal (DP), relié (DR) ou associé (DA). »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `XXI` | `contexte` | `sujet` | |

---

## §B — Z00 à Z13 : examens, suspicions, dépistages

### GM2026-V-XXI-02 — `condition_emploi`
**Situation** : Z00–Z02 — motifs relevant de l'activité externe
**Texte** : Les catégories Z00 à Z02 répertorient des motifs de recours qui relèvent, sauf exception, de l'activité externe ; les patients concernés ne se plaignent de rien et aucun diagnostic n'est rapporté.
**Citation** (L54-62) : « Catégories Z00–Z02 — Elles répertorient des motifs de recours qui relèvent, sauf exception, de l'activité externe. […] Les patients concernés ne se plaignent de rien et aucun diagnostic n'est rapporté (sinon c'est la symptomatologie ou le diagnostic qu'on coderait). »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z00-Z02` | `contexte` | `sujet` | |

### GM2026-V-XXI-03 — `condition_emploi`
**Situation** : Z03 — suspicions non confirmées
**Texte** : Les cas où l'emploi de Z03 s'impose sont rares : lorsqu'une symptomatologie est présente, on préfère son code (le plus souvent du chapitre XVIII) toutes les fois qu'il est plus précis. Z03.6 reste adapté à une suspicion d'absorption de produit toxique reposant sur une crainte de l'entourage, finalement infirmée.
**Condition** : Absence de symptomatologie codable plus précise
**Citation** (L86-95) : « La règle générale est : le meilleur code est le plus précis par rapport à l'information à coder. Lorsqu'une symptomatologie est présente, on préfèrera son code (le plus souvent présent dans le chapitre XVIII de la CIM–10) à un code Z toutes les fois qu'il est plus précis. Les cas dans lesquels l'emploi de la catégorie Z03 s'impose sont rares. […] En revanche, Z03.6 […] peut être le code le plus adapté à une suspicion d'absorption de produit toxique […] lorsqu'elle repose sur une crainte de l'entourage mais qu'elle est finalement infirmée. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z03` | `contexte` | `sujet` | |
| `Z03.6` | `DP` | `sujet` | suspicion de produit toxique infirmée |
| `XVIII` | `contexte` | `sujet` | à préférer si plus précis |

> ⚠ **`XVIII` en `contexte` fait descendre cette consigne sur les
> ~800 fiches du chapitre XVIII.** C'est fidèle au texte mais bruyant.
> Alternative : ne pas associer `XVIII` du tout, la mention restant dans
> le `texte`. **À trancher** — c'est le premier cas où la résolution
> jusqu'aux feuilles coûte cher.

### GM2026-V-XXI-04 — `condition_emploi`
**Situation** : Z04.0 — alcool et substances pharmacologiques
**Texte** : Z04.0 est employé lorsque la présence dans le sang d'alcool ou de substances pharmacologiques n'est **pas** confirmée ; si elle l'est, on fait appel à la catégorie R78.
**Condition** : Présence non confirmée
**Citation** (L99-101) : « de la présence dans le sang d'alcool ou de substances pharmacologiques ; le code Z04.0 est employé lorsque leur présence n'est pas confirmée, sinon on ferait appel à la catégorie R78. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z04.0` | `contexte` | `sujet` | |
| `R78` | `contexte` | `sujet` | si présence confirmée |

### GM2026-V-XXI-05 — `condition_emploi`
**Situation** : Z04.1 à Z04.3 — suspicion de lésion secondaire
**Texte** : L'emploi de Z04.1 à Z04.3 est réservé aux situations dans lesquelles aucune lésion n'est finalement diagnostiquée.
**Condition** : Aucune lésion finalement diagnostiquée
**Citation** (L102-105) : « d'une lésion susceptible de se manifester secondairement par rapport au traumatisme responsable : codes Z04.1 à Z04.3 ; leur emploi est réservé aux situations dans lesquelles aucune lésion n'est finalement diagnostiquée (sinon c'est elle qu'on coderait) »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z04.1-Z04.3` | `contexte` | `sujet` | |

### GM2026-V-XXI-06 — `condition_emploi`
**Situation** : Z04.4 à Z04.6 — problèmes médicolégaux
**Texte** : Z04.4 et Z04.5 peuvent être utilisés autant pour les coupables que pour les victimes ; on les emploie lorsqu'aucun état morbide n'est mis en évidence.
**Condition** : Aucun état morbide mis en évidence
**Citation** (L106-110) : « d'autres problèmes médicolégaux : Z04.4, Z04.5, Z04.6 ; les codes Z04.4 et Z04.5 peuvent être utilisés autant pour les coupables que pour les victimes : on les emploie lorsque aucun état morbide (lésion traumatique, trouble mental…) n'est mis en évidence, sinon c'est lui qu'on coderait […]. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z04.4-Z04.6` | `contexte` | `sujet` | |

### GM2026-V-XXI-07 — `regle_position`
**Situation** : Z04.800, Z04.801, Z04.802 — codes imposés en DP
**Texte** : Z04.800 (électroencéphalogramme de longue durée) et Z04.801 (enregistrement polygraphique) sont les codes **imposés** pour le DP de ces séjours ; Z04.802 code les bilans préopératoires ou préinterventionnels. Leur emploi s'impose comme DP qu'une affection ait été diagnostiquée ou non au terme du séjour.
**Condition** : —
**Citation** (L116-126) : « Z04.800 est le code imposé pour le DP des séjours motivés par l'enregistrement d'un électroencéphalogramme de longue durée ; Z04.801 est le code imposé pour le DP des séjours motivés par un enregistrement polygraphique ; Z04.802 est le code des examens et mises en observation pour bilan préopératoire ou préinterventionnel ; Z04.880 […]. L'emploi de Z04.800, Z04.801 ou Z04.802 s'impose comme DP du RUM, qu'une affection ait été diagnostiquée ou non au terme du séjour […]. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z04.800` | `DP` | `sujet` | EEG de longue durée |
| `Z04.801` | `DP` | `sujet` | enregistrement polygraphique |
| `Z04.802` | `DP` | `sujet` | bilan préopératoire ou préinterventionnel |
| `Z04.880` | `contexte` | `sujet` | autres investigations |

### GM2026-V-XXI-08 — `interdiction`
**Situation** : Z04.8 — devenu inutilisable depuis ses extensions
**Texte** : Depuis la création de ses extensions (version 11 des GHM), Z04.8 est devenu imprécis et n'est plus utilisable comme DP, DR ni DA ; l'emploi des extensions est obligatoire.
**Condition** : —
**Citation** (L133-136, note 25) : « Elles ont été créées pour la version 11 des GHM (2009). Leur emploi est obligatoire. En effet, Z04.8, devenu imprécis du fait de leur création, n'est plus utilisable comme DP, DR et DA à compter de la version 11 des GHM. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z04.8` | `interdit` | `sujet` | |

### GM2026-V-XXI-09 — `interdiction`
**Situation** : Z04.9 — information trop imprécise
**Texte** : Z04.9 correspond à une information trop imprécise pour être acceptable.
**Citation** (L128) : « Z04.9 correspond à une information trop imprécise pour être acceptable. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z04.9` | `interdit` | `sujet` | |

### GM2026-V-XXI-10 — `interdiction`
**Situation** : Z03 ou Z04 en DP — pas de diagnostic relié
**Texte** : Lorsqu'un code des catégories Z03 ou Z04 est en position de DP, sauf cas particulier, il ne justifie pas de diagnostic relié.
**Condition** : Sauf cas particulier
**Citation** (L130-131) : « Lorsqu'un code des catégories Z03 ou Z04 est en position de DP, sauf cas particulier, il ne justifie pas de diagnostic relié (DR). »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z03` | `interdit_DR` | `sujet` | quand en DP |
| `Z04` | `interdit_DR` | `sujet` | quand en DP |

> **Emploi type de `interdit_DR`** : le code reste parfaitement
> légitime en DP, c'est la position DR *du séjour* qui est proscrite.

### GM2026-V-XXI-11 — `regle_position`
**Situation** : Z08 ou Z09 en DP — maladie surveillée en DR
**Texte** : Lorsqu'un code des catégories Z08 ou Z09 est en position de DP, le code de la maladie surveillée doit figurer en position de DR chaque fois qu'elle respecte sa définition. Ces codes sont typiquement des codes de surveillance négative.
**Condition** : La maladie surveillée respecte la définition du DR
**Citation** (L154-156) : « Lorsqu'un code des catégories Z08 ou Z09 est en position de DP, le code de la maladie surveillée doit figurer en position de DR chaque fois qu'elle respecte sa définition […]. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z08` | `DP` | `sujet` | |
| `Z09` | `DP` | `sujet` | |

### GM2026-V-XXI-12 — `definition`
**Situation** : Z08.2 et Z09.2 — sens du mot « chimiothérapie »
**Texte** : Le mot « chimiothérapie » n'a pas dans la CIM–10 le sens implicite de « chimiothérapie antitumorale » qu'il a dans le langage courant : il a son sens premier de « traitement par des moyens chimiques ». Seule Z08 concerne les tumeurs malignes.
**Citation** (L148-153) : « Z08.2 et Z09.2 : l'intitulé de ces deux sous-catégories contient le mot "chimiothérapie" alors que seule Z08 concerne les tumeurs malignes ; on rappelle en effet que le mot chimiothérapie n'a pas dans la CIM–10 le sens implicite de "chimiothérapie antitumorale" qui est le sien dans le langage courant ; il a son sens premier de "traitement par des moyens chimiques". »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z08.2` | `contexte` | `sujet` | |
| `Z09.2` | `contexte` | `sujet` | |

### GM2026-V-XXI-13 — `interdiction`
**Situation** : Z10 — sans emploi en MCO
**Texte** : La catégorie Z10 n'a pas d'emploi dans le champ d'activité couvert par le PMSI en MCO : elle ne comprend que des motifs de consultation externe.
**Citation** (L158-161) : « Catégorie Z10 – Examen général de routine d'une sous-population définie — Elle n'a pas d'emploi dans le champ d'activité couvert par le PMSI en MCO car elle ne comprend que des motifs de consultation externe dont certains ne concernent pas les établissements d'hospitalisation. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z10` | `interdit` | `sujet` | |

### GM2026-V-XXI-14 — `interdiction`
**Situation** : Z11 à Z13 — le dépistage n'est pas l'exploration d'un problème personnel
**Texte** : Les codes Z11 à Z13 ne doivent pas être employés pour des patients présentant un problème de santé personnel. Il est erroné de coder comme un dépistage une situation d'examens motivés par un antécédent personnel ou familial, ou par une symptomatologie quelconque : c'est le motif des explorations qui doit être codé.
**Condition** : Patient présentant un problème de santé personnel
**Citation** (L163-176) : « Le mot dépistage a dans la CIM–10 le sens de "recherche de certaines affections inapparentes par des examens effectués systématiquement dans des collectivités" […]. Les codes des catégories Z11 à Z13 ne doivent donc pas être employés pour des patients présentant un problème de santé personnel. Il est erroné de coder comme un dépistage une situation d'examens diagnostiques motivés par un antécédent personnel ou familial […] ou par une symptomatologie quelconque […]. Dans ce cas c'est le motif des explorations qui doit être codé […]. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z11-Z13` | `interdit` | `sujet` | si problème de santé personnel |

### GM2026-V-XXI-15 — `regle_position`
**Situation** : Z13.51 — dépistage de la surdité néonatale permanente
**Texte** : Z13.51 doit être systématiquement codé en DAS lorsqu'un dépistage de la surdité néonatale permanente (test et éventuel retest) est réalisé par OEAA ou PEAA lors d'un séjour de nouveau-né.
**Condition** : Dépistage réalisé par OEAA ou PEAA lors d'un séjour de nouveau-né
**Citation** (L177-184) : « Pour le dépistage précoce de la surdité néonatale permanente (SPN) réalisé lors des séjours de nouveau-nés, le code Z13.51 Examen spécial de dépistage des affections des oreilles doit être systématiquement codé en DAS lorsqu'un dépistage (test et éventuel retest) de la surdité néonatale permanente est réalisé, selon les recommandations de la HAS, par oto-émissions acoustiques automatisées (OEAA) ou par potentiels évoqués auditifs automatisés (PEAA). »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z13.51` | `DAS` | `sujet` | |

> **Exception explicite à XXI-14** dans le même article : Z13.51 est un
> dépistage systématique au sens strict. Les deux consignes coexistent
> sans se contredire — l'une exclut le dépistage de complaisance,
> l'autre impose le dépistage réel.

---

## §C — Z20 à Z29 : risque lié à des maladies transmissibles

### GM2026-V-XXI-16 — `condition_emploi`
**Situation** : Z20 — contact avec une maladie transmissible non confirmée
**Texte** : Z20 permet de coder l'absence d'une maladie infectieuse initialement crainte du fait d'un contact ou de toute autre exposition ; si la maladie était confirmée, c'est elle qu'on coderait.
**Condition** : Maladie infectieuse non confirmée
**Citation** (L187-213) : « Catégorie Z20 : elle permet de coder l'absence d'une maladie infectieuse initialement crainte du fait du contact du patient avec une personne infectée ou de tout autre mode d'exposition à un agent infectieux […] ; en effet, si la maladie infectieuse était confirmée, c'est elle qu'on coderait. […] Le code est ici Z20.1. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z20` | `contexte` | `sujet` | |
| `I` | `interdit` | `sujet` | la maladie crainte n'est pas codée |
| `XVIII` | `interdit` | `sujet` | aucun symptôme |
| `Z20.1` | `DP` | **`exemple`** | exemple du guide |

> ⚠ **Les deux `interdit` de chapitre entier (`I`, `XVIII`) descendraient
> sur ~1900 et ~800 fiches.** Le texte les énonce bien, mais dans un
> **exemple** (« cet enfant n'est pas tuberculeux : on ne code donc pas
> cette maladie »), pas comme une règle générale. **Je recommande de ne
> pas les associer** et de laisser la mention dans le `texte`. À votre
> arbitrage — c'est le deuxième cas de bruit potentiel massif.

### GM2026-V-XXI-17 — `condition_emploi`
**Situation** : Z21 — séropositivité VIH isolée
**Texte** : Z21 code la séropositivité isolée au VIH. Si la séropositivité s'associe à l'un des états classés dans les catégories B20 à B24, c'est un code de celles-ci qu'on emploie, non Z21.
**Condition** : Séropositivité isolée
**Citation** (L215-217) : « Z21 est le code de la séropositivité isolée au virus de l'immunodéficience humaine (VIH). Si la séropositivité s'associe à l'un des états classés dans les catégories B20 à B24 du chapitre I de la CIM–10, c'est un code de celles-ci qu'on emploie, non Z21. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z21` | `contexte` | `sujet` | |
| `B20-B24` | `interdit_association` | `sujet` | exclut Z21 |

### GM2026-V-XXI-18 — `definition`
**Situation** : Z22 — colonisations et portages sains
**Texte** : La catégorie Z22, dans la suite logique de Z21, est la catégorie des colonisations (« portages sains »).
**Citation** (L219-220) : « La catégorie Z22, dans la suite logique de Z21, est la catégorie des colonisations (" portages sains ") : bactéries… »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z22` | `contexte` | `sujet` | |

### GM2026-V-XXI-19 — `condition_emploi`
**Situation** : Z29.0 — isolement thérapeutique, non social
**Texte** : Z29.0 n'est pas destiné au classement des situations d'isolement social, qui se codent avec Z60 ; il code l'isolement dans un but thérapeutique. Son emploi est autorisé dans toutes les situations où un patient est isolé pour être mis à l'abri de l'entourage ou pour l'en protéger, malgré le classement de Z29 dans un groupe consacré aux maladies infectieuses.
**Citation** (L222-231) : « la sous-catégorie Z29.0 Isolement n'est pas destinée au classement des situations d'isolement social qui doivent être codées avec la catégorie Z60 ; le code Z29.0 est destiné au codage de l'isolement dans un but thérapeutique […]. Bien que la catégorie Z29 soit classée dans un groupe (Z20–Z29) qui concerne les maladies infectieuses, l'absence d'un autre code d'isolement dans le chapitre XXI conduit à autoriser l'emploi de Z29.0 dans toutes les situations où un patient est isolé […]. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z29.0` | `contexte` | `sujet` | |
| `Z60` | `contexte` | `sujet` | isolement social |

### GM2026-V-XXI-20 — `condition_emploi`
**Situation** : Z29.1 et Z29.2 — immunothérapie et chimiothérapie prophylactiques
**Texte** : Z29.1 ou Z29.2 peuvent être utilisés lors des séjours motivés par l'administration d'une immunothérapie ou d'une chimiothérapie prophylactique, quel qu'en soit le motif, à condition que le caractère prophylactique soit établi.
**Condition** : Caractère prophylactique établi
**Citation** (L232-235) : « Z29.1 ou Z29.2 peuvent être utilisés lors des séjours motivés par l'administration d'une immunothérapie ou d'une chimiothérapie prophylactique, quel qu'en soit le motif (infectieux, tumoral…), mais à condition que le caractère prophylactique (préventif) soit établi. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z29.1` | `contexte` | `sujet` | |
| `Z29.2` | `contexte` | `sujet` | |

### GM2026-V-XXI-21 — `condition_emploi`
**Situation** : Z20 à Z29 — catégories utilisables en MCO et droit au DR
**Texte** : Parmi les catégories Z20 à Z29, seules Z20, Z21, Z22 et Z29 sont en pratique susceptibles d'être utilisées pour le codage des RUM. Si un code de ces rubriques est en DP, seuls ceux de la catégorie Z29 sont susceptibles de justifier un DR.
**Citation** (L237-241) : « Dans le champ actuel du PMSI en MCO, parmi les catégories Z20 à Z29, seules Z20, Z21, Z22 et Z29 sont, en pratique, susceptibles d'être utilisées pour le codage des RUM. Si un code de ces rubriques est en position de diagnostic principal (DP) d'un RUM, seuls ceux de la catégorie Z29 sont susceptibles de justifier un DR, à condition que l'affection concernée respecte sa définition […]. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z20` | `interdit_DR` | `sujet` | quand en DP |
| `Z21` | `interdit_DR` | `sujet` | quand en DP |
| `Z22` | `interdit_DR` | `sujet` | quand en DP |
| `Z29` | `contexte` | `sujet` | seule à justifier un DR |

> **Point à trancher.** « seules Z20, Z21, Z22 et Z29 sont *en pratique*
> susceptibles d'être utilisées » interdit-il les autres (Z23–Z28) ? Le
> guide dit « en pratique », pas « ne doivent pas ». **Je n'ai pas créé
> d'`interdit` sur Z23-Z28** : ce serait durcir le texte.

---

## §D — Z30 à Z39 : reproduction

### GM2026-V-XXI-22 — `regle_position`
**Situation** : Z33 — grossesse normale chez une femme hospitalisée pour un autre motif
**Texte** : Z33 permet d'enregistrer la grossesse comme diagnostic associé lorsqu'une femme enceinte est hospitalisée pour un motif sans rapport avec elle et qu'elle se déroule normalement.
**Condition** : Motif d'hospitalisation sans rapport avec la grossesse ; grossesse normale
**Citation** (L245-249) : « La catégorie Z33 permet, dans le cas d'une femme enceinte hospitalisée pour un motif sans rapport avec sa grossesse, d'enregistrer celle-ci comme diagnostic associé lorsqu'elle se déroule normalement. Exemple : traumatisme de la jambe chez une femme enceinte ; DP : la lésion de la jambe ; diagnostic associé : Z33. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z33` | `DAS` | `sujet` | |

### GM2026-V-XXI-23 — `condition_emploi`
**Situation** : Z34 et Z35 — surveillance de grossesse
**Texte** : Z34 comprend la surveillance des grossesses normales, Z35 celle de **toutes** les autres — l'intitulé « à haut risque » ne doit pas être lu de manière rigide. Dans les hospitalisations de l'antepartum, la mention d'un code Z35.– est indispensable à l'orientation correcte du RSS dans les GHM de l'antepartum.
**Citation** (L251-259) : « Catégories Z34 et Z35 : Z34 comprend la surveillance systématique de la grossesse normale […]. L'intitulé de la catégorie Z35 Surveillance d'une grossesse à haut risque ne doit pas être lu de manière rigide. […] Z34 pour les grossesses normales et Z35 pour les autres, c'est-à-dire pour toutes les non normales (à risque, "haut" ou non). Dans le cas des hospitalisations de l'antepartum, la mention d'un code Z35.– est indispensable à l'orientation correcte du résumé de sortie standardisé (RSS) dans les groupes homogènes de malades (GHM) de l'antepartum. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z34` | `contexte` | `sujet` | grossesse normale |
| `Z35.–` | `contexte` | `sujet` | toute grossesse non normale |

### GM2026-V-XXI-24 — `regle_position`
**Situation** : Z37 — résultat de l'accouchement
**Texte** : La mention d'un code de la catégorie Z37 comme diagnostic associé est indispensable au classement du RSS dans un GHM d'accouchement ; un code de cette catégorie doit être enregistré dans les RSS de tous les séjours comportant un accouchement.
**Citation** (L263-267) : « Catégorie Z37 : la mention d'un de ses codes comme diagnostic associé est indispensable au classement du RSS dans un GHM d'accouchement. Un code de cette catégorie doit être enregistré dans les RSS de tous les séjours comportant un accouchement. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z37` | `DAS` | `sujet` | |

### GM2026-V-XXI-25 — `regle_position`
**Situation** : Z38.0 — nouveau-né en bonne santé en maternité
**Texte** : Z38.0 est le code du DP du RUM du nouveau-né dont le séjour se déroule en maternité auprès de sa mère ; dans cette situation il ne justifie aucun diagnostic relié. Lorsque le DP du séjour d'un nouveau-né est un problème de santé, son code doit être d'abord cherché dans le chapitre XVI.
**Citation** (L269-276) : « Z38.0 Enfant unique né à l'hôpital est le code le plus fréquemment utilisé comme diagnostic principal (DP) des résumés de séjour des nouveau-nés […]. Z38.0 est le code du DP du RUM du nouveau-né dont le séjour se déroule en maternité auprès de sa mère. Dans cette situation il ne justifie aucun diagnostic relié. Lorsque le diagnostic principal du séjour d'un nouveau-né est un problème de santé, son code doit être d'abord cherché dans le chapitre XVI de la CIM–10 (puis, à défaut, dans un autre chapitre). »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z38.0` | `DP` | `sujet` | |
| `Z38.0` | `interdit_DR` | `sujet` | quand en DP |

> **Deux lignes pour un même code, et c'est voulu** : `DP` dit où il va,
> `interdit_DR` dit ce qu'il interdit. Une seule ligne ne peut pas
> porter les deux.

### GM2026-V-XXI-26 — `regle_position`
**Situation** : Z39 — soins et examens du postpartum
**Texte** : Un code Z39 est toujours requis pour les séjours du postpartum ; il ne doit pas être enregistré d'acte d'accouchement dans le RUM, et un code de la catégorie Z37 doit être saisi en diagnostic associé.
**Citation** (L278-282) : « Catégorie Z39 Soins et examens du postpartum : Ce code est toujours requis pour les séjours du postpartum. — il ne doit pas être enregistré d'acte d'accouchement dans le RUM ; — un code de la catégorie Z37 Résultat de l'accouchement doit être saisi en position de diagnostic associé. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z39` | `DP` | `sujet` | |
| `Z37` | `DAS` | `sujet` | |

### GM2026-V-XXI-27 — `regle_position`
**Situation** : Transfert pour soins du postpartum (E1 → E2)
**Texte** : Lorsqu'après un accouchement dans un établissement E1 une mère est transférée avec son enfant dans un établissement E2 pour les soins du postpartum (soins standard, pas de complication, nouveau-né normal), le DP du RUM de la mère est codé Z39.08 et celui du nouveau-né Z76.2.
**Condition** : Soins standard, pas de complication, nouveau-né normal
**Citation** (L291-297) : « Lorsqu'après accouchement dans un établissement de santé E1, une mère est transférée avec son enfant dans un établissement de santé E2 pour les soins du postpartum (soins standard, pas de complication, nouveau-né normal), dans E2 : le DP du RUM de la mère est codé Z39.08 […] ; le DP du RUM du nouveau-né est codé Z76.2 […]. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z39.08` | `DP` | `sujet` | mère |
| `Z76.2` | `DP` | `sujet` | nouveau-né |

---

## §E — Z40 à Z54 : actes et soins spécifiques

### GM2026-V-XXI-28 — `regle_position`
**Situation** : Z40 — actes prophylactiques et thérapeutiques pour tumeur maligne
**Texte** : Z40.0 (opération prophylactique pour facteur de risque de tumeur maligne) a reçu des extensions signalant l'organe opéré. L'emploi des codes Z40 concerne aussi les interventions à but thérapeutique ou prophylactique portant sur d'autres localisations : ainsi une ovariectomie de castration pour cancer du sein hormonosensible se code Z40.01 en DP.
**Citation** (L305-311) : « Dans le cadre des actes opératoires prophylactiques pour facteur de risque de tumeur maligne, des extensions, permettant de signaler l'organe opéré, ont été ajoutées au code "Z40.0 = opération prophylactique pour facteur de risque de tumeur maligne". L'utilisation des codes Z40 concerne également les interventions réalisées à but thérapeutique ou prophylactique, dans le cadre de la prise en charge de tumeurs malignes portant sur d'autres localisations. Ainsi, dans le cadre du traitement d'un cancer du sein hormonosensible, une ovariectomie pour castration doit être codée avec le code Z40.01 en DP. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z40.01` | `DP` | `sujet` | ovariectomie de castration |
| `Z40` | `contexte` | `sujet` | |

### GM2026-V-XXI-29 — `regle_position`
**Situation** : Z41 — chirurgie esthétique et interventions de confort
**Texte** : Lorsqu'il s'agit de chirurgie esthétique, le DP doit **toujours** être codé Z41.0 ou Z41.1, à l'exclusion de tout autre code ; le défaut corrigé peut être codé en DR. Z41.80 code les interventions dites de confort.
**Citation** (L336-341) : « lorsqu'il s'agit de chirurgie esthétique le DP doit toujours être codé Z41.0 ou Z41.1, à l'exclusion de tout autre code ; le défaut corrigé peut être codé en position de diagnostic relié (DR). » — et (L324-330) : « La catégorie Z41 comprend les soins "sans raison médicale" […]. Elle est notamment destinée au codage du DP des séjours pour chirurgie esthétique (Z41.0, Z41.1) et pour intervention dite de confort (Z41.80). »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z41.0` | `DP` | `sujet` | chirurgie esthétique |
| `Z41.1` | `DP` | `sujet` | chirurgie esthétique |
| `Z41.80` | `DP` | `sujet` | intervention de confort |

### GM2026-V-XXI-30 — `regle_position`
**Situation** : Z42 — chirurgie plastique non esthétique
**Texte** : Pour une chirurgie plastique non esthétique, de réparation d'une lésion congénitale ou acquise prise en charge par l'assurance maladie, le DP est codé avec un autre code de la CIM–10 — un code des chapitres I à XIX ou un code de la catégorie Z42 — le meilleur code étant le plus précis. Avec un DP codé Z42.–, le motif de l'intervention peut être mentionné en DR.
**Citation** (L342-348) : « lorsqu'il s'agit de chirurgie plastique non esthétique, de réparation d'une lésion congénitale ou acquise, prise en charge par l'assurance maladie obligatoire, le DP doit être codé avec un autre code de la CIM–10 ; il peut s'agir d'un code des chapitres I à XIX ou d'un code de la catégorie Z42 […]. Avec un DP codé Z42.– le motif de l'intervention peut être mentionné en position de DR s'il respecte sa définition. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z42.–` | `DP` | `sujet` | |
| `J34.2` | `DP` | **`exemple`** | rhinoplastie pour déviation de cloison |
| `L91.0` | `DP` | **`exemple`** | exérèse de cicatrice chéloïde |
| `Z42.1` | `DP` | **`exemple`** | prothèse mammaire après mastectomie |
| `Z41.1` | `DP` | **`exemple`** | prothèse mammaire à visée esthétique |

**Citation des exemples** (L350-356) : « – mise en place de prothèses internes pour augmentation du volume mammaire à visée esthétique : Z41.1 ; – mise en place d'une prothèse mammaire interne après mastectomie : Z42.1 ; – rhinoplastie à visée esthétique : Z41.1 ; – rhinoplastie pour déviation de la cloison nasale : J34.2 ; – exérèse d'une cicatrice chéloïde : L91.0. »

### GM2026-V-XXI-31 — `definition`
**Situation** : Z43 — soins de stomie ponctuels, opposés à Z93
**Texte** : Z43 est une rubrique de soins de stomie ponctuels, incluant la fermeture de la stomie. Elle exclut les soins habituels effectuables à domicile, qui se codent avec Z93, et les complications comprises dans J95.0, K91.4 et N99.5.
**Citation** (L364-370) : « La catégorie Z43 est une rubrique de soins de stomie. Elle comprend des soins médicaux ponctuels […] incluant la fermeture de la stomie. […] La catégorie Z43 exclut les soins habituels tels qu'effectués ou effectuables à domicile (soins quotidiens d'hygiène, changements de poche ou de canule de trachéostomie) qui se codent avec la catégorie Z93 (voir plus loin). Elle exclut aussi les complications comprises dans les rubriques J95.0, K91.4 et N99.5. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z43` | `contexte` | `sujet` | |
| `Z93` | `interdit_association` | `sujet` | soins habituels à domicile |
| `J95.0` | `interdit_association` | `sujet` | complication |
| `K91.4` | `interdit_association` | `sujet` | complication |
| `N99.5` | `interdit_association` | `sujet` | complication |

> **Cas de recouvrement attendu avec les exclusions CIM-10** : ces trois
> renvois figurent très probablement déjà comme exclusions OFS/ANS sous
> Z43. Le rapport `guide_mco_recouvrement_potentiel.csv` devrait les
> signaler — c'est exactement l'usage prévu.

### GM2026-V-XXI-32 — `regle_position`
**Situation** : Z45.0 — implantation d'un stimulateur ou défibrillateur cardiaque
**Texte** : Par convention, le DP d'un séjour pour l'implantation d'un stimulateur ou d'un défibrillateur cardiaque est la cardiopathie qui la justifie, et non Z45.0.
**Citation** (L388-389) : « Par convention, le diagnostic principal d'un séjour pour l'implantation d'un stimulateur ou d'un défibrillateur cardiaque est la cardiopathie qui la justifie, et non Z45.0. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z45.0` | `interdit_DP` | `sujet` | |

> **Emploi type de `interdit_DP`** : Z45.0 reste employable, mais jamais
> comme DP de ce séjour.

### GM2026-V-XXI-33 — `regle_position`
**Situation** : Z49.0 — confection d'une fistule de dialyse
**Texte** : Le DP des séjours pour mise en place d'une fistule de dialyse rénale est codé Z49.0 et non Z45.2. La catégorie Z49, malgré le mot « surveillance » de son intitulé, comprend les prises en charge pour actes de préparation à la dialyse rénale.
**Citation** (L394-396) : « Le DP des séjours pour mise en place d'une fistule de dialyse rénale est codé Z49.0 et non Z45.2 […]. » — et (L434-438) : « La catégorie Z49, malgré la présence du mot "surveillance" dans son intitulé, comprend les prises en charge pour des actes de préparation à la dialyse rénale ; Z49.0 comprend ainsi la mise en place des fistules et cathéters de dialyse. En effet, en raison de la spécificité de cette catégorie et de son rôle dans la classification des GHM, il faut coder Z49.0 (et non Z45.2) le DP des séjours pour la confection d'une fistule. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z49.0` | `DP` | `sujet` | |
| `Z45.2` | `interdit_DP` | `sujet` | confection de fistule |

### GM2026-V-XXI-34 — `regle_position`
**Situation** : Z45.84 — mise en place d'un stimulateur du système nerveux central
**Texte** : Le DP des hospitalisations pour la mise en place d'un stimulateur du système nerveux central (cérébral ou médullaire) doit être codé Z45.84.
**Citation** (L398-401) : « Le DP des hospitalisations pour la mise en place d'un stimulateur du système nerveux central (cérébral ou médullaire) doit être codé Z45.84 Ajustement et entretien d'une prothèse interne du système nerveux central. Il s'agit en effet, en général, de séjours programmés spécifiquement réservés à l'acte médicotechnique de pose du stimulateur. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z45.84` | `DP` | `sujet` | |

### GM2026-V-XXI-35 — `interdiction` ⚠ **rôle manquant**
**Situation** : Z43 ou Z45 en DA redondant avec un acte CCAM
**Texte** : Lorsqu'un code des catégories Z43 ou Z45 correspond à une prise en charge pour laquelle un code d'acte existe dans la CCAM, la saisie dans le même RUM du code Z43.– ou Z45.– en position de diagnostic associé, en sus de celui de l'acte, est redondante et n'est pas justifiée.
**Condition** : Un code d'acte CCAM existe pour la prise en charge
**Citation** (L405-410) : « Lorsqu'un code des catégories Z43 ou Z45 de la CIM–10 correspond à une prise en charge pour laquelle un code d'acte existe dans la CCAM, la saisie dans le même RUM du code Z43.– ou Z45.– en position de diagnostic associé (DA) en sus de celui de l'acte est redondante et n'est pas justifiée. Un tel emploi de "codes Z" serait incorrect au regard de la CIM–10. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z43.–` | **`interdit_DAS`** *(rôle à créer)* | `sujet` | acte CCAM présent |
| `Z45.–` | **`interdit_DAS`** *(rôle à créer)* | `sujet` | acte CCAM présent |

### GM2026-V-XXI-36 — `regle_position`
**Situation** : Z47.0 — ablation de matériel d'ostéosynthèse
**Texte** : Z47.0 doit être utilisé pour coder le DP des séjours pour ablation de matériel d'ostéosynthèse. Au terme de ces séjours, il ne faut pas coder à nouveau la lésion osseuse initiale guérie ou consolidée, ni comme DP, ni comme DR, ni comme diagnostic associé. Z47.0 code aussi le DP des séjours pour retrait d'un espaceur et repose de prothèse définitive.
**Citation** (L418-427) : « Z47.0 doit notamment être utilisé pour coder le DP des séjours pour ablation de matériel d'ostéosynthèse ; il ne faut pas, au terme de ces séjours, coder à nouveau la lésion osseuse initiale guérie ou consolidée, ni comme DP, ni comme DR, ni comme diagnostic associé ; elle ne peut éventuellement être qu'une donnée à visée documentaire. Le DP des séjours pour retrait de prothèse temporaire de type espaceur (spacer), mise en place suite à une infection, et repose de prothèse définitive se code Z47.0 […]. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z47.0` | `DP` | `sujet` | |

> **La seconde moitié de la consigne n'a pas de cible codable.** « la
> lésion osseuse initiale guérie » désigne un code qui dépend du cas ;
> le guide ne le nomme pas. L'interdiction reste dans le `texte` de la
> consigne, sans association — comme pour `GM2026-V-AVC-18`.

### GM2026-V-XXI-37 — `definition`
**Situation** : Z48 — soins postinterventionnels immédiats
**Texte** : Z48 peut être employée pour les soins postinterventionnels immédiats : surveillance postopératoire et surveillance faisant suite à un acte médicotechnique (endoscopie, endovasculaire, imagerie interventionnelle).
**Citation** (L429-432) : « La catégorie Z48 peut être employée pour les soins postinterventionnels immédiats. Par soins postinterventionnels on entend notamment la surveillance postopératoire et celle qui fait suite à un acte médicotechnique tel qu'une intervention par voie endoscopique ou endovasculaire et l'imagerie interventionnelle. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z48` | `contexte` | `sujet` | |

### GM2026-V-XXI-38 — `regle_position`
**Situation** : Z51 — séjours pour actes thérapeutiques
**Texte** : Tous les séjours pour chimiothérapie, radiothérapie, transfusion sanguine, aphérèse sanguine ou oxygénothérapie hyperbare, qu'il s'agisse de séances ou d'hospitalisation complète, doivent comporter en DP le code ad hoc de la catégorie Z51. Z51.1 code le DP des séjours pour chimiothérapie pour tumeur ; Z51.2 les autres chimiothérapies ; Z51.30 la transfusion sanguine ; Z51.31 l'aphérèse.
**Citation** (L475-478) : « Tous les séjours pour chimiothérapie, radiothérapie, transfusion sanguine, aphérèse sanguine, oxygénothérapie hyperbare, qu'il s'agisse de séances ou d'hospitalisation complète, doivent comporter en position de DP le code ad hoc de la catégorie Z51 de la CIM–10. » — et (L455) : « Z51.1 code le DP des séjours pour chimiothérapie pour tumeur. » — et (L460-463) : « Z51.2 est employé pour les autres séjours pour "chimiothérapie", dès lors que l'affection traitée n'est pas une tumeur. » — et (L469-470) : « Z51.30 est le code du DP des séjours pour transfusion sanguine ; Z51.31 est le code du DP des séjours pour aphérèse sanguine. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z51` | `DP` | `sujet` | |
| `Z51.1` | `DP` | `sujet` | chimiothérapie pour tumeur |
| `Z51.2` | `DP` | `sujet` | chimiothérapie non antitumorale |
| `Z51.30` | `DP` | `sujet` | transfusion sanguine |
| `Z51.31` | `DP` | `sujet` | aphérèse sanguine |

### GM2026-V-XXI-39 — `regle_position` ⭐ **témoin Z51.5**
**Situation** : Z51 en DP — la maladie traitée en diagnostic relié
**Texte** : Lorsqu'un code Z51.0–, Z51.1, Z51.2, Z51.3–, Z51.5 ou Z51.8– est en position de DP, la maladie traitée est enregistrée comme diagnostic relié chaque fois qu'elle respecte sa définition, ce qui est le plus souvent le cas.
**Condition** : La maladie traitée respecte la définition du DR
**Citation** (L480-482) : « Lorsqu'un code Z51.0–, Z51.1, Z51.2, Z51.3–, Z51.5 ou Z51.8– est en position de DP, la maladie traitée est enregistrée comme diagnostic relié chaque fois qu'elle respecte sa définition, ce qui est le plus souvent le cas […]. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z51.0` | `DP` | `sujet` | |
| `Z51.1` | `DP` | `sujet` | |
| `Z51.2` | `DP` | `sujet` | |
| `Z51.3` | `DP` | `sujet` | |
| `Z51.5` | `DP` | `sujet` | |
| `Z51.8` | `DP` | `sujet` | |

> **Recoupe `GM2026-V-AVC-06`** (« DP = Z51.5 ; l'AVC en DR »), qui en
> est le cas particulier appliqué à l'AVC. Les deux doivent coexister :
> la fiche Z51.5 recevra la règle générale, la fiche de l'AVC la règle
> particulière. C'est le tri par spécificité qui les ordonnera.

### GM2026-V-XXI-40 — `interdiction` ⚠ **rôle manquant**
**Situation** : Z51 en DA redondant avec un acte CCAM
**Texte** : Lorsqu'un code de la catégorie Z51 correspond à une prise en charge pour laquelle un code d'acte existe dans la CCAM, la saisie du code Z51.– en diagnostic associé en sus de celui de l'acte est redondante et n'est pas justifiée. Z51.00 et Z51.01 font exception : lorsqu'un acte d'irradiation est effectué au cours d'une hospitalisation pour un autre motif, Z51.01 figure dans le même RUM que l'acte.
**Condition** : Un code d'acte CCAM existe ; hors Z51.00 et Z51.01
**Citation** (L484-493) : « Lorsqu'un code de la catégorie Z51 de la CIM–10 correspond à une prise en charge pour laquelle un code d'acte existe dans la CCAM, la saisie dans le même RUM du code Z51.– en position de diagnostic associé (DA) en sus de celui de l'acte est redondante et n'est pas justifiée. […] Z51.00 Séance de préparation à une irradiation et Z51.01 Séance d'irradiation font exception. Lorsqu'un acte d'irradiation est effectué au cours d'une hospitalisation pour un autre motif (un autre DP), Z51.01 figure dans le même RUM que l'acte. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z51.–` | **`interdit_DAS`** *(rôle à créer)* | `sujet` | acte CCAM présent |
| `Z51.00` | `contexte` | `sujet` | exception |
| `Z51.01` | `DAS` | `sujet` | exception : irradiation au cours d'un autre séjour |

### GM2026-V-XXI-41 — `regle_position`
**Situation** : Z52 — prélèvement d'organes ou de tissus
**Texte** : Les codes de la catégorie Z52 sont utilisés pour le codage du DP du RSS produit pour un sujet admis aux fins de prélèvements d'organes ou de tissus. Z52.80 Donneuse d'ovocytes est employé comme DP du séjour pour prélèvement d'ovocytes, et comme diagnostic associé en cas de partage (egg sharing).
**Citation** (L517-525) : « Les codes de la catégorie Z52 sont utilisés pour le codage du diagnostic principal du RSS produit pour un sujet admis aux fins de prélèvements d'organes ou de tissus. Le code étendu national Z52.80 Donneuse d'ovocytes a été créé pour être utilisé depuis 2012 dans deux circonstances : comme diagnostic principal du séjour pour prélèvement d'ovocytes ; comme diagnostic associé du séjour de prélèvement d'ovocytes en cas de partage (egg sharing). »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z52` | `DP` | `sujet` | |
| `Z52.80` | `DP` | `sujet` | prélèvement d'ovocytes |
| `Z52.80` | `DAS` | `sujet` | egg sharing |

### GM2026-V-XXI-42 — `condition_emploi`
**Situation** : Z53 — soins prévus non prodigués
**Texte** : Z53 permet le codage des circonstances dans lesquelles les soins prévus à l'admission ne sont pas prodigués ; le mot « acte » de l'intitulé doit être lu au sens étendu de « prestation de soins », « prise en charge ».
**Citation** (L527-532) : « La catégorie Z53 permet le codage des circonstances dans lesquelles les soins prévus à l'admission ne sont pas prodigués ; le mot acte de l'intitulé doit être lu avec l'acception étendue de "prestation de soins", "prise en charge". Exemples : – refus d'une transfusion sanguine pour motif de conviction : Z53.1 ; – sortie contre avis médical ou par fuite : Z53.2. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z53` | `contexte` | `sujet` | |
| `Z53.1` | `contexte` | **`exemple`** | refus pour motif de conviction |
| `Z53.2` | `contexte` | **`exemple`** | sortie contre avis médical |

---

## §F — Z55 à Z76 : conditions socio-économiques et autres motifs

### GM2026-V-XXI-43 — `regle_position`
**Situation** : Z65.1 — personne détenue
**Texte** : Z65.1 Emprisonnement ou autre incarcération doit être enregistré en position de diagnostic associé lorsque les soins ont été dispensés à une personne détenue.
**Citation** (L552-553) : « Z65.1 Emprisonnement ou autre incarcération doit être enregistré en position de diagnostic associé lorsque les soins ont été dispensés à une personne détenue. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z65.1` | `DAS` | `sujet` | |

### GM2026-V-XXI-44 — `condition_emploi`
**Situation** : Z74.2 — défaillance de l'aide à domicile
**Texte** : Z74.2 est employé lorsqu'une personne qui ne peut vivre à son domicile qu'avec une aide doit être hospitalisée, ou maintenue en hospitalisation, du fait de l'absence ou de la défaillance de celle-ci.
**Citation** (L555-562) : « Z74.2 Besoin d'assistance à domicile, aucun autre membre du foyer n'étant capable d'assurer les soins est employé lorsqu'une personne qui ne peut vivre à son domicile qu'avec une aide, doit être hospitalisée ou maintenue en hospitalisation du fait de l'absence ou de la défaillance de celle-ci. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z74.2` | `contexte` | `sujet` | |

### GM2026-V-XXI-45 — `condition_emploi`
**Situation** : Z75.1 — attente d'admission ailleurs
**Texte** : Z75.1 ne doit être employé que si le séjour ou la prolongation de l'hospitalisation est motivé par la seule attente de l'unité ou de l'établissement adéquat, et non par un événement morbide.
**Condition** : Séjour motivé par la seule attente
**Citation** (L564-566) : « Z75.1 Sujet attendant d'être admis ailleurs, dans un établissement adéquat ne doit être employé que si le séjour ou la prolongation de l'hospitalisation est motivé par la seule attente de l'unité ou de l'établissement adéquat, non par un évènement morbide. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z75.1` | `contexte` | `sujet` | |

### GM2026-V-XXI-46 — `definition`
**Situation** : Z75.80 — sens du mot « acte »
**Texte** : Dans l'intitulé de Z75.80, le mot « acte » ne doit pas être limité à la notion d'acte médicotechnique : il doit être compris au sens large de « prestation de soins », « prise en charge ».
**Citation** (L575-577) : « Dans l'intitulé de Z75.80 Sujet adressé dans un autre établissement, pour réalisation d'un acte, le sens du mot "acte" ne doit pas être limité à la notion d'acte médicotechnique. Il doit être compris avec le sens large de "prestation de soins", "prise en charge". »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z75.80` | `contexte` | `sujet` | |

### GM2026-V-XXI-47 — `regle_position`
**Situation** : Z76.800 — infection ostéoarticulaire complexe
**Texte** : Z76.800 doit être enregistré comme DA dès lors que le patient a fait l'objet d'une réunion de concertation pluridisciplinaire visée par un centre interrégional de référence ayant confirmé le caractère complexe de l'IOA. Même si une seule RCP a été réalisée, Z76.800 doit être saisi dans les RUM de **tous les séjours ultérieurs** motivés par la prise en charge de l'IOA.
**Condition** : RCP visée par un centre interrégional de référence
**Citation** (L585-591) : « Afin d'identifier les patients atteint d'une infections ostéoarticulaires (IOA) complexe, Z76.800 […] doit être enregistré comme DA dès lors que le patient a fait l'objet d'une réunion de concertation pluridisciplinaire visée par un centre interrégional de référence ayant confirmé le caractère complexe de l'IOA. Même si une seule RCP a été réalisée, Z76.800 doit être saisi dans les RUM de tous les séjours ultérieurs du patient motivés par la prise en charge de l'IOA. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z76.800` | `DAS` | `sujet` | |

### GM2026-V-XXI-48 — `regle_position`
**Situation** : Z76.850 — nouveau-né recevant du lait d'un lactarium
**Texte** : Z76.850 doit être enregistré comme DA dans le RUM du séjour des nouveau-nés recevant du lait d'un lactarium.
**Citation** (L593-594) : « Pour identifier les nouveau-nés recevant du lait d'un lactarium, Z76.850 Enfant recevant du lait provenant d'un lactarium doit être enregistré comme DA dans le RUM de leur séjour. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z76.850` | `DAS` | `sujet` | |

---

## §G — Z80 à Z99 : antécédents, greffes, prothèses, dépendance

### GM2026-V-XXI-49 — `interdiction`
**Situation** : Z80 à Z92 — un DP d'antécédent ne justifie jamais de DR
**Texte** : Les codes des catégories Z80 à Z92 peuvent notamment être utilisés pour le codage du DP dans des situations diagnostiques. Un DP d'antécédent personnel ou familial de maladie ne justifie **jamais** de diagnostic relié.
**Citation** (L597-604) : « Catégories Z80 à Z92 – Antécédents personnels et familiaux — Les codes de ces catégories peuvent notamment être utilisés pour le codage du DP dans des situations de diagnostique au sens du guide des situations cliniques […]. Exemple : patient ayant un antécédent familial de cancer colique, hospitalisé pour coloscopie, où la coloscopie ne retrouve aucune lésion : le DP est Z80.00. Un DP d'antécédent personnel ou familial de maladie ne justifie jamais de diagnostic relié. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z80-Z92` | `interdit_DR` | `sujet` | quand en DP |
| `Z80.00` | `DP` | **`exemple`** | antécédent familial de cancer colique |

> **Le « jamais » est explicite** — contrairement à XXI-10, qui réserve
> un « sauf cas particulier ». La distinction est dans le texte, elle
> doit être dans la `condition`.

### GM2026-V-XXI-50 — `condition_emploi`
**Situation** : Z92.1 et Z92.2 — traitements pris antérieurement
**Texte** : Ces codes peuvent être employés lorsqu'un recours aux soins est motivé par la prise d'un médicament prescrit antérieurement, que la prise soit poursuivie (« utilisation actuelle ») ou qu'elle ait cessé au moment du recours — l'acception du mot « antécédent » étant large dans la CIM–10.
**Citation** (L606-613) : « Z92.1 et Z92.2 : la complexité apparente de leur intitulé est due à l'acception étymologique large du mot "antécédent" qui est celle de la CIM–10. Ces codes peuvent être employés lorsqu'un recours aux soins est motivé par la prise d'un médicament prescrit antérieurement, que la prise soit poursuivie ("utilisation actuelle") ou qu'elle ait cessé au moment du recours. Exemple : patient porteur d'une valve cardiaque prothétique, prenant un antivitamine K (AVK) au long cours, hospitalisé pour extractions dentaires : le DP est l'affection dentaire, la prise de l'AVK (Z92.1) est un DAS […]. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z92.1` | `DAS` | `sujet` | |
| `Z92.2` | `DAS` | `sujet` | |

### GM2026-V-XXI-51 — `definition`
**Situation** : Z93 — soins habituels de stomie, opposés à Z43
**Texte** : Z93 est employée pour le codage des soins de stomie habituels, tels qu'effectués ou effectuables à domicile (soins quotidiens d'hygiène, changements de poche, changements de canule de trachéostomie). Elle s'oppose à Z43.
**Citation** (L614-618) : « La catégorie Z93 est une rubrique relative aux stomies. On l'emploie pour le codage des soins habituels tels qu'effectués ou effectuables à domicile (soins quotidiens d'hygiène, changements de poche, changements de canule de trachéostomie). Elle s'oppose à la catégorie Z43 : se reporter supra à la présentation de celle-ci. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z93` | `contexte` | `sujet` | |
| `Z43` | `interdit_association` | `sujet` | soins ponctuels |

### GM2026-V-XXI-52 — `regle_position`
**Situation** : Z94 et Z95 — surveillance négative de greffes et prothèses
**Texte** : Z94 et Z95 sont employées pour coder le DP des situations de surveillance négative des porteurs d'organe ou de tissu greffé (Z94), de pontage coronaire, de prothèse endoartérielle, de prothèse valvulaire cardiaque et autres implants cardiaques et vasculaires (Z95).
**Condition** : Surveillance négative (aucune anomalie constatée)
**Citation** (L620-640) : « Les catégories Z94 et Z95 sont employées pour coder le DP des situations de surveillance négative des porteurs d'organe ou de tissu greffé (Z94), de pontage coronaire et de prothèse endoartérielle (stent), de prothèse valvulaire cardiaque et "autres implants et greffes et cardiaques et vasculaires". Exemples : – patient porteur d'un cœur transplanté […] aucune anomalie n'est constatée ; le DP du séjour est codé Z94.1 ; – patient porteur d'un pontage coronaire hospitalisé pour bilan de surveillance ; aucune anomalie n'est constatée : le DP du séjour est codé Z95.1. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z94` | `DP` | `sujet` | |
| `Z95` | `DP` | `sujet` | |
| `Z94.1` | `DP` | **`exemple`** | cœur transplanté |
| `Z95.1` | `DP` | **`exemple`** | pontage coronaire |
| `T86.2` | `contexte` | **`exemple`** | un rejet se code T86.2 (note 47) |

### GM2026-V-XXI-53 — `condition_emploi`
**Situation** : Z96 et Z97 — présence d'implants et prothèses
**Texte** : Z96 et Z97 permettent le codage de la présence de divers implants, prothèses et appareils. Leur emploi n'est admissible qu'en l'absence de complication.
**Condition** : Absence de complication
**Citation** (L642-645) : « Les catégories Z96 et Z97 permettent le codage de la présence de divers implants, prothèses et appareils. Leur emploi n'est admissible qu'en l'absence de complication. En cas de soins nécessités par une complication, se reporter plus haut dans ce chapitre au point traitant des complications des actes médicaux et chirurgicaux. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z96` | `contexte` | `sujet` | |
| `Z97` | `contexte` | `sujet` | |

### GM2026-V-XXI-54 — `interdiction` ⚠ **rôle manquant**
**Situation** : Z93, Z95 ou Z96 en DA redondant avec un acte CCAM
**Texte** : Lorsqu'un code des catégories Z93, Z95 ou Z96 correspond à une prise en charge pour laquelle un code d'acte existe dans la CCAM, la saisie du code Z93.–, Z95.– ou Z96.– en diagnostic associé en sus de celui de l'acte est redondante et n'est pas justifiée.
**Condition** : Un code d'acte CCAM existe pour la prise en charge
**Citation** (L647-662) : « Lorsqu'un code des catégories Z93, Z95 ou Z96 de la CIM–10 correspond à une prise en charge pour laquelle un code d'acte existe dans la CCAM, la saisie dans le même RUM du code Z93.–, Z95.– ou Z96.– en position de diagnostic associé (DA) en sus de celui de l'acte est redondante et n'est pas justifiée. Un tel emploi de "codes Z" serait incorrect au regard de la CIM–10. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z93.–` | **`interdit_DAS`** *(rôle à créer)* | `sujet` | acte CCAM présent |
| `Z95.–` | **`interdit_DAS`** *(rôle à créer)* | `sujet` | acte CCAM présent |
| `Z96.–` | **`interdit_DAS`** *(rôle à créer)* | `sujet` | acte CCAM présent |

### GM2026-V-XXI-55 — `condition_emploi`
**Situation** : Z99 — dépendance chronique, non phase aigüe
**Texte** : Est dépendante envers une machine une personne atteinte d'une affection chronique dont la survie est subordonnée à l'utilisation régulière et durable de ce matériel. Les codes Z99 ne doivent pas être employés pour mentionner l'utilisation d'un tel matériel en phase aigüe.
**Condition** : Affection chronique ; pas d'emploi en phase aigüe
**Citation** (L664-674) : « Est dépendante envers une machine ou un appareil une personne atteinte d'une affection chronique dont la survie est subordonnée à l'utilisation régulière et durable de ce matériel. C'est en ce sens que doit être comprise l'utilisation des codes de la catégorie Z99. Ils ne doivent pas être employés pour mentionner l'utilisation d'un matériel de ce type en phase aigüe : par exemple, Z99.0 Dépendance envers un aspirateur ou Z99.1 Dépendance envers un respirateur ne doivent pas servir à mentionner l'utilisation de ces matériels chez un patient sous ventilation mécanique pour insuffisance respiratoire aigüe, Z99.2 Dépendance envers une dialyse rénale ne peut pas être employé pour les séjours des patients dialysés pour insuffisance rénale aigüe. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z99` | `interdit` | `sujet` | en phase aigüe |
| `Z99.0` | `interdit` | **`exemple`** | ventilation en insuffisance respiratoire aigüe |
| `Z99.1` | `interdit` | **`exemple`** | idem |
| `Z99.2` | `interdit` | **`exemple`** | dialyse pour insuffisance rénale aigüe |

---

## Extensions d'enum — la demande principale de ce fichier

### `interdit_DAS` — nécessaire

**Cinq consignes** (XXI-35, XXI-40, XXI-54, plus la seconde moitié de
XXI-36 et une partie de XXI-49) interdisent une position de **diagnostic
associé**. Les huit rôles connaissent `interdit_DP` et `interdit_DR`
mais pas `interdit_DAS`.

Les trois façons de s'en passer sont toutes fausses :

- **`interdit`** dirait que Z43.– ne doit pas être employé du tout —
  or il reste le DP légitime d'un séjour de fermeture de stomie
  (XXI-31). Un générateur qui lirait ça n'écrirait plus jamais de
  colostomie ;
- **`interdit_association`** dit « pas avec cette autre cible de la
  consigne » — ici il n'y a pas d'autre cible CIM-10, l'autre terme est
  un **acte CCAM**, qui n'est pas dans le référentiel ;
- **laisser dans le `texte` sans association** perdrait précisément
  l'information positionnelle, qui est ce que le modèle existe pour
  porter (§2 de la note : « la sémantique positionnelle vit dans
  l'association, pas dans le texte seul »).

**Ma recommandation : ajouter `interdit_DAS`**, ce qui porte le
catalogue à neuf modalités et rend la triade complète et symétrique
(`interdit_DP` / `interdit_DR` / `interdit_DAS`). L'ajout touche
`schemas.py`, le §4.2 de la note et le CLAUDE.md.

### `regi` — à arbitrer (rappel du fichier AVC)

Très nombreuses consignes de cet article régissent un code sans lui
assigner de position (`Z22 est la catégorie des colonisations`,
`Z53 permet le codage de…`). J'ai mis `contexte` partout, alors que sa
définition dit « situe la consigne **sans être ce qu'elle prescrit** ».
Sur cet article, `contexte` est le rôle le plus fréquent, ce qui est le
signe qu'il fait deux métiers. Même arbitrage que dans
`avc_complements.md`.

### Rien à signaler côté `type`

Les cinq types ont suffi.
