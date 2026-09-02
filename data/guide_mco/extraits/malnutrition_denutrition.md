<!-- ============================================================
     COMMENT RELIRE CE FICHIER

     Le test d'intégrité garantit qu'aucun mot n'a été ajouté, perdu ni
     déplacé par rapport à l'extrait brut. Il ne dit RIEN sur ce qui
     vous revient :

       1. Le tableau du §4.1 est une RESTITUTION — il est absent du
          brut, pdftotext l'a perdu (il est en image dans le PDF).
          Aucune machine ne peut le vérifier : à contrôler à l'œil
          contre le PDF, page 121 (imprimée 113).
       2. Les six notes repliées `[^n: …]` sont-elles raccrochées au
          bon appel ?
       3. Les titres et les listes rendent-ils la structure du PDF ?

     VOUS POUVEZ ÉDITER CE FICHIER DIRECTEMENT. Après édition :

         uv run pytest -k transcription -q

     - vert  : votre correction est du reformatage — c'est votre
               domaine, rien à déclarer ;
     - rouge : le message dit quels mots ont changé. Soit c'est un
               écart involontaire, soit c'est un choix éditorial qui
               doit être déclaré dans extraits/curation.yaml — dans ce
               second cas, signalez-le plutôt que de modifier le YAML.

     Pour une remarque, un doute, une erreur du guide à signaler :
     écrivez-la en commentaire HTML comme celui-ci. Le test l'ignore,
     je la reprends.
     ============================================================ -->

<!-- Transcription curée — MALNUTRITION, DÉNUTRITION
     Guide méthodologique MCO 2026 (version provisoire), chap. V, pp. imprimées 109-114.
     Brut : extraits_bruts/malnutrition_denutrition.txt, lignes 35-305.
     Curation déclarée : extraits/curation.yaml.
     Note 64 (URL des courbes CRESS) est hors des bornes de l'article : son appel
     « CRESS64 » reste dans le texte, la note n'est pas transcrite. -->

## MALNUTRITION, DÉNUTRITION

La CIM–10 classe les états de malnutrition dans le groupe E40–E46 : E40 Kwashiorkor, E41 Marasme nutritionnel ; E42 Kwashiorkor avec marasme [^57: Les codes E40, E41 et E42 ne peuvent connaître qu’un emploi exceptionnel en France.] ; E43 Malnutrition protéinoénergétique grave, sans précision ;E44.0 Malnutritionprotéinoénergétique modérée ; E44.1 Malnutrition protéinoénergétique légère ; E46 Malnutrition sans précision58. [^58: Auxquels s’ajoute O25 Malnutrition au cours de la grossesse.] Elle range sous le terme générique de malnutrition59 [^59: Cet anglicisme désigne de fait tout trouble lié à un déséquilibre alimentaire, aussi bien en défaut qu’en excès.] un groupe d’affections résultant d’une carence d’apport ou d’une désassimilation protéinoénergétique : on doit donc l’entendre dans le sens restreint de dénutrition.

La HAS publie en novembre 2019 et mis à jour en 2021 des recommandations de bonne pratique pour le diagnostic de la dénutrition de l’enfant et de l’adulte. Ce document a été élaboré en collaboration avec la Fédération française de nutrition (FFN)60. [^60: Diagnostic de la dénutrition de l’enfant et de l’adulte - novembre 2019.] Pour les patients de moins de 70 ans, le diagnostic de la dénutrition nécessite la présence d’au moins 1 critère phénotypique et 1 critère étiologique. Ce diagnostic est un préalable obligatoire avant de juger de sa sévérité. Il repose exclusivement sur des critères non biologiques. Ces critères sont exposés ci-dessous :

### 1. Le diagnostic de la dénutrition chez les patients âgés de moins de 18 ans

Les critères phénotypiques sont les suivants :
- perte de poids ≥ 5 % en 1 mois ou ≥ 10 % en 6 mois ou ≥ 10 % par rapport au poids habituel avant le début de la maladie ;
- IMC < courbe IOTF 18,5 ;
- stagnation pondérale aboutissant à un poids situé 2 couloirs en dessous du couloir habituel de l’enfant (courbe de poids) ;
- réduction de la masse et/ou de la fonction musculaires (lorsque les normes et/ou les outils sont disponibles)

Les critères étiologiques sont les suivants :
- réduction de la prise alimentaire ≥ 50 % pendant plus d’1 semaine, ou toute réduction des apports pendant plus de 2 semaines par rapport :
  * à la consommation alimentaire habituelle quantifiée,
  * ou aux besoins protéino-énergétiques estimés ;
- absorption réduite (malabsorption/maldigestion) ;
- situation d’agression (hypercatabolisme protéique avec ou sans syndrome inflammatoire):
   * pathologie aiguë ou
   * pathologie chronique évolutive ou
   * pathologie maligne évolutive

#### 1.1 Les critères de dénutrition modérée chez les patients âgés de moins de 18 ans

- courbe IOTF 17 < IMC < courbe IOTF 18,5 ;
- perte de poids ≥ 5 % et ≤ 10 % en 1 mois ou ≥ 10 % et ≤ 15 % en 6 mois par rapport au poids habituel avant le début de la maladie ;
- stagnation pondérale aboutissant à un poids situé entre 2 et 3 couloirs en dessous du couloir habituel.

L’observation d’un seul critère de dénutrition modérée suffit pour poser le diagnostic de dénutrition modérée dès lors que la dénutrition est présente ( 1 caractère phénotypique + 1 caractère étiologique).

#### 1.2 Les critères de dénutrition sévère chez les patients âgés de moins de 18 ans

-  IMC ≤ courbe IOTF 17 ;
-  perte de poids > 10 % en 1 mois ou > 15 % en 6 mois par rapport au poids habituel avant le début de la maladie ;
-  stagnation pondérale aboutissant à un poids situé au moins 3 couloirs (représentant 3 écart-types) en dessous du couloir habituel ;
- infléchissement statural (avec perte d’au moins un couloir par rapport à la taille habituelle).

L’observation d’un seul critère de dénutrition sévère suffit à qualifier la dénutrition de sévère dès lors que la dénutrition est présente (1 caractère étiologique + 1 caractère phénotypique).

#### 1.3 Consigne

Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision, une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée.

### 2. Le diagnostic de la dénutrition chez l’adulte (≥ 18 ans et < 70 ans)

Les critères phénotypiques sont les suivants :
-  perte de poids ≥ 5 % en 1 mois ou ≥ 10 % en 6 mois ou ≥ 10 % par rapport au poids habituel avant le début de la maladie ;
- IMC < 18,5 kg/m2 ;
- réduction quantifiée de la masse et/ou de la fonction musculaires.

Les critères étiologiques sont les suivants :
- réduction de la prise alimentaire ≥ 50 % pendant plus d’1 semaine, ou toute réduction des apports pendant plus de 2 semaines par rapport :
   * à la consommation alimentaire habituelle quantifiée,
   * ou aux besoins protéino-énergétiques estimés ;
- absorption réduite (malabsorption/maldigestion) ;
- situation d’agression (hypercatabolisme protéique avec ou sans syndrome inflammatoire)
   *  pathologie aiguë ou
   * pathologie chronique évolutive ou
   * pathologie maligne évolutive.

#### 2.1 Les critères de dénutrition modérée chez l’adulte (≥ 18 ans et < 70 ans)

- 17 < IMC < 18,5 kg/m2 ;
- perte de poids ≥ 5 % en 1 mois ou ≥ 10 % en 6 mois ou ≥ 10 % par rapport au poids habituel avant le début de la maladie ;
- mesure de l’albuminémie par immunonéphélémétrie ou immunoturbidimétrie >30 g/L et < 35 g/L. Les seuils d’albuminémie sont à prendre en compte quel que soit l’état inflammatoire.

L’observation d’un seul critère de dénutrition modérée suffit à qualifier la dénutrition de modérée dès lors que la dénutrition est présente (1 caractère étiologique + 1 caractère phénotypique).

#### 2.2 Les critères de dénutrition sévère chez l’adulte (≥ 18 ans et < 70 ans)

- IMC ≤ 17 kg/m2 ;
- perte de poids ≥ 10 % en 1 mois ou ≥ 15 % en 6 mois ou ≥ 15 % par rapport au poids habituel avant le début de la maladie ;
- mesure de l’albuminémie par immunonéphélémétrie ou immunoturbidimétrie ≤ 30g/L. Les seuils d’albuminémie sont à prendre en compte quel que soit l’état inflammatoire.

L’observation d’un seul critère de dénutrition sévère suffit à qualifier la dénutrition de sévère dès lors que la dénutrition est présente (1 caractère étiologique + 1 caractère phénotypique).

Lors de l’observation simultanée d’un seul critère de dénutrition sévère et d’un ou plusieurs critères de dénutrition modérée, il est recommandé de poser un diagnostic de dénutrition sévère.

#### 2.3 Consigne

Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision, une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée.x

### 3. Le diagnostic de la dénutrition chez la personne âgée de 70 ans et plus

Le diagnostic repose sur la recommandation de bonnes pratiques de la HAS élaborée en collaboration avec la Fédération française de nutrition intitulée "Diagnostic de la dénutrition chez la personne de 70 ans et plus".

Pour les patients de 70 ans et plus, le diagnostic de la dénutrition nécessite la présence d’au moins 1 critère phénotypique et 1 critère étiologique. Ce diagnostic est un préalable obligatoire avant de juger de sa sévérité. Il repose exclusivement sur des critères non biologiques. Ces critères sont résumés ci-dessous.

Les critères phénotypiques sont les suivants (1 seul critère suffit) :
- perte de poids ≥ 5 % en 1 mois ou ≥ 10 % en 6 mois ou ≥ 10 % par rapport au poids habituel avant le début de la maladie ;
- IMC < 22 kg/m2 [^61: Ce critère ne concerne pas la personne âgée de 70 ans et plus en situation d’obésité.];
- sarcopénie confirmée par une réduction quantifiée de la force et de la masse musculaire.

Les critères étiologiques sont les suivants (1 seul critère suffit) :
- réduction de la prise alimentaire ≥ 50 % pendant plus d’1 semaine, ou toute réduction des apports pendant plus de 2 semaines par rapport à la consommation alimentaire habituelle ou aux besoins protéino-énergétiques ;
- absorption réduite (malabsorption/maldigestion) ;
- situation d’agression (avec ou sans syndrome inflammatoire) : pathologie aiguë ou pathologie chronique évolutive ou pathologie maligne évolutive.

#### 3.1 Les critères de dénutrition modérée chez les patients âgés de 70 ans et plus

- 20 ≤ IMC < 22 ;
- perte de poids ≥ 5 % et < 10 % en 1 mois ou ≥ 10 % et < 15 % en 6 mois ou ≥ 10 % et < 15 % par rapport au poids habituel avant le début de la maladie ;
- mesure de l’albuminémie par immunonéphélémétrie ou immunoturbidimétrie > 30 g/L.

L’observation d’un seul critère de dénutrition modérée suffit pour poser le diagnostic de dénutrition modérée dès lors que la dénutrition est présente (1 caractère phénotypique + 1 caractère étiologique).

#### 3.2. Les critères de dénutrition sévère chez les patients âgés de 70 ans et plus

- IMC < 20 kg/m2 ;
- Perte de poids ≥ 10 % en 1 mois ou ≥ 15 % en 6 mois ou ≥ 15 % par rapport au poids habituel avant le début de la maladie ;
- mesure de l’albuminémie par immunonéphélémétrie ou immunoturbidimétrie ≤ 30 g/L.

L’observation d’un seul critère de dénutrition sévère suffit à qualifier la dénutrition de sévère dès lors que la dénutrition est présente (1 caractère étiologique + 1 caractère phénotypique).

#### 3.3. Consigne

Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision, une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée.

### 4. Consignes générales

L’emploi des codes E40 à E46 doit se fonder sur ces critères et nécessite que le dossier comporte [^62: Pour mémoire l’emploi des catégories E40, E41 et E42 ne peut être qu’exceptionnel en France.] la mention de dénutrition . Cette mention peut être indiquée par un clinicien ou par un diététicien. Il est recommandé d’intégrer les valeurs du poids et de la taille et de l’IMC dans le dossier médical partagé (DMP).

Le code CIM10 est déterminé en fonction des critères correspondant aux définitions publiées par la HAS et retrouvés au dossier, sans que le niveau de sévérité ne doive nécessairement être mentionné dans le dossier. Il est toutefois recommandé que ce niveau soit explicitement mentionné.

#### 4.1 Outil d’évaluation de la masse et/ou de la fonction musculaire

| Méthodes de mesure | Hommes | Femmes |
|---|---|---|
| Force de préhension (dynamomètre) en kg | < 26 | < 16 |
| Vitesse de marche (m/s) | < 0,8 | < 0,8 |
| Indice de surface musculaire en L3 en cm²/m² (scanner, IRM) | 52,4 | 38,5 |
| Indice de masse musculaire en kg/m² (impédancemétrie) | 7,0 | 5,7 |
| Indice de masse non grasse (impédancemétrie) en kg/m² | < 17 | < 15 |
| Masse musculaire appendiculaire (DEXA) en kg/m² | 7,23 | 5,67 |

<!-- DÉFAUT DU GUIDE, signalé et NON réparé (RF, contre-lecture du PDF p. imprimée 113).

     Trois lignes de ce tableau donnent un seuil SANS comparateur, là où
     les trois autres portent « < » :

       - indice de surface musculaire en L3 : « 52,4 » / « 38,5 »
       - indice de masse musculaire (impédancemétrie) : « 7,0 » / « 5,7 »
       - masse musculaire appendiculaire (DEXA) : « 7,23 » / « 5,67 »

     La direction de comparaison est donc indéterminée sur ces trois
     méthodes. La transcription reproduit l'asymétrie telle quelle : la
     corriger ferait dire au guide ce qu'il ne dit pas, et c'est
     précisément ce que la base doit pouvoir attester.

     Consigné dans data/guide_mco/hors_perimetre.md, section
     « Divergences et défauts du guide constatés ». Si la version
     définitive corrige ce point, le diff de millésime le montrera. -->

L’utilisation d’une seule de ces méthodes suffit

#### 4.2 Critère « albuminémie »

D’après la « Fiche-outil-diagnostic » HAS63 les seuils d’albuminémie sont à prendre en compte quel que soit l’état inflammatoire.

#### 4.3 Critère « MNA »

Ce dépistage peut être formalisé par un questionnaire tel que le Mini Nutritional Assessment.

#### 4.4 Courbes IOTF (IMC) et courbe de poids chez l’enfant

Les courbes disponibles sur le site de la CRESS64 .

#### 4.5 Courbe de poids chez l’enfant : définition du couloir habituel

Le couloir habituel est le couloir habituel de croissance pondérale de l’enfant ou de référence pour des pathologies spécifiques (trisomie 21, myopathie, etc.).

#### 4.6 Critère « stagnation pondérale aboutissant à un poids situé entre 2 et 3 couloirs en dessous du couloir habituel » pour la dénutrition modérée chez l’enfant

Pour le critère de la définition HAS, il faut comprendre 2 couloirs en dessous du couloir habituel, et jusqu’à la limite du 3ème couloir

#### 4.7 Critère « stagnation pondérale aboutissant à un poids situé au moins 3 couloirs en dessous du couloir habituel » pour la dénutrition sévère chez l’enfant

Pour le critère de la définition HAS « poids situé au moins « 3 couloirs (représentant 3 écart- types) » il faut comprendre 3 couloirs en percentiles.
