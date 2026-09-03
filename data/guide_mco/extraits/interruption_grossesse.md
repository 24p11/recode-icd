<!-- Transcription curée — INTERRUPTION DE LA GROSSESSE
     Premier jet produit par scripts/curer_guide_mco.py, À RELIRE.
     Brut : extraits_bruts/interruption_grossesse.txt, lignes 40-192.
     Curation déclarée : extraits/curation.yaml.
     Le test garantit qu'aucun mot n'a bougé ; il ne dit rien des
     tableaux, de l'ancrage des notes, ni de ce que pdftotext a perdu. -->

## INTERRUPTION DE LA GROSSESSE

Par « interruption de la grossesse » on entend :

- d’une part l’interruption volontaire (IVG) : articles L.2212-1 et suivants, R.2212-1 et suivants du code de la santé publique (CSP) ;
- d’autre part l’interruption pour motif médical (IMG) [^50: Dite aussi interruption thérapeutique de grossesse.] : articles L.2213-1 et suivants, R.2213-1 et suivants du CSP.

### 1. Codage de l’IVG

#### 1.1 IVG non compliquée

Le codage des IVG non compliquées repose sur la présence en DP de l’un des 3 codes suivants :

- O04.90, interruption volontaire de grossesse (IVG dans le cadre légal), complet ou sans précision, sans complication
- O07.4 Echec d’une tentative d’avortement médical sans complication
- O07.9 Echec d’une tentative d’avortement, autres et sans précision, sans complication

Le code Z640 Difficultés liées à une grossesse non désirée ne sera plus recherché pour l’orientation dans la racine 14Z08Z.

L’acte enregistré est, selon le cas, JNJD002 Évacuation d'un utérus gravide par aspiration et/ou curetage, au 1er trimestre de la grossesse ou JNJP001 Évacuation d'un utérus gravide par moyen médicamenteux, au 1er trimestre de la grossesse. Même si le libellé de l’acte semble en restreindre l’utilisation au premier trimestre de la grossesse, l’acte JNJD002 Évacuation d’un utérus gravide par aspiration et/ou curetage, au 1er trimestre de la grossesse doit continuer à être codé en cas de technique chirurgicale pour une grossesse de plus de 14SA et de moins de 16SA, car il permet l’orientation des séjours dans les forfaits ad-hoc.

Par ailleurs, la date des dernières règles est enregistrée.

Dans le cas de l’IVG médicamenteuse, on rappelle qu’un résumé d’unité médicale (RUM) unique doit être produit. Il doit mentionner par convention des dates d’entrée et de sortie égales à la date de la consultation de délivrance du médicament abortif, que la prise en charge ait été limitée à la consultation de prise du médicament abortif ou qu’elle ait compris l’ensemble des étapes (consultation de délivrance du médicament abortif, prise de prostaglandine et surveillance de l’expulsion, consultation de contrôle). [^51: Se reporter au point 1.2 du chapitre I.]

#### 1.2 IVG compliquée

1°) Lorsqu’une complication survient au cours du séjour même de l’IVG, celle-ci est codée par le quatrième caractère du code O04.–. Le cas échéant, un code de la catégorie O08 Complications consécutives à un avortement, une grossesse extra-utérine et molaire en position de diagnostic associé peut identifier la nature de la complication (CIM–10, volume 2 p. 123 ou 158 ). [^52: Dans l’ensemble de ce chapitre, les numéros de page renvoient au volume 2 de l’édition imprimée de la Classification statistique internationale des maladies et des problèmes de santé connexes, dixième révision (CIM–10) ; OMS éd. Le premier numéro (ici « 103 ») correspond à l’édition de 1993, le second (« 134 ») à l’édition de 2008.] La date des dernières règles est enregistrée.

2°) Lorsqu’une complication donne lieu à une réhospitalisation après le séjour d’IVG, deux cas doivent être distingués :

- s’il s’agit d’un avortement incomplet, avec rétention simple — non compliquée — de produits de la conception : − le DP est codé O04.4 Avortement médical incomplet, sans complication, − l’acte enregistré est JNMD001 Révision de la cavité de l'utérus après avortement ; − la date des dernières règles est enregistrée ;
- s’il s’agit d’un avortement incomplet avec rétention compliquée de produits de la conception, ou d’une autre complication : – le DP est un code de la catégorie O08 Complications consécutives à un avortement, une grossesse extra-utérine et molaire ; – l’acte ou les actes réalisés pour le traitement de la complication sont enregistrés.

#### 1.3 Échec d’IVG

On parle d'échec d’IVG devant le constat d’une poursuite de la grossesse. Ce cas est généralement observé après une IVG médicamenteuse. Il conduit à pratiquer une IVG instrumentale. Le RUM doit être codé comme suit :

- le DP est un code de la catégorie O07 Échec d'une tentative d'avortement ;
- l’acte enregistré est JNJD002 Évacuation d'un utérus gravide par aspiration et/ou curetage, au 1er trimestre de la grossesse ;
- la date des dernières règles est enregistrée.

### 2. Codage de l’IMG

Il diffère selon la durée de la gestation au moment de l’interruption [^53: Voir  les informations données dans la note technique constituant l’annexe II l’instruction N° DREES/BES/DGS/SP1/DGOS/R3/2021/148 du 21 juin 2021.]. <!-- Un « 51 » isolé de l'original (résidu de numérotation à côté de l'appel 53) est retiré ici comme balisage. -->

#### 2.1 IMG avant vingt-deux semaines révolues d’aménorrhée

On code un avortement : DP O04.-1 ; ou O04.-2 ou O04.-3

- DA : on enregistre le motif de l’IMG ; selon qu’il est classé dans le chapitre XV de la CIM–10 ou dans un autre chapitre, on choisit le code ad hoc du chapitre XV (en particulier dans la catégorie O35 (Soins maternels pour anomalies et lésions fœtales, connues ou présumées) [^54: La note d’inclusion placée sous son titre dans le volume 1 de la CIM–10 ne s’oppose pas à sa mention dans le résumé de sortie, conjointement à un code d’avortement.] ou un code des catégories O98 ou O99, précisé si besoin par un code des chapitres I à XVII et XIX [^55: Voir dans le volume 1 de la CIM–10 les notes figurant en tête des catégories O98 et O99.] ;
- acte d’interruption de grossesse
- date des dernières règles.

#### 2.2 IMG à partir de vingt-deux semaines révolues d’aménorrhée

C’est un accouchement. Le codage diffère selon que le motif de l’interruption est fœtal ou maternel.

Si la cause est une anomalie fœtale :

- DP : un code de la catégorie O35 ;

- DA : on enregistre par convention un code étendu de la catégorie Z37 Résultat de l’accouchement (en général Z37.11 Naissance unique, enfant mort-né, à la suite d’une interruption de la grossesse pour motif médical ) [^56: Code Z37.1 de la CIM–10 étendu pour la circonstance à compter de la version 11c (2011) de la classification des GHM.] ;
- acte d’accouchement ;
- âge gestationnel et date des dernières règles.

Si la cause de l’interruption est maternelle :
- DP : selon que la cause est classée dans le chapitre XV de la CIM–10 ou dans un autre chapitre, on choisit le code ad hoc du chapitre XV ou un code des catégories O98 ou O99 ; pas de DR ;
- DA : on enregistre par convention un code de la catégorie Z37 (en général Z37.11 Naissance unique, enfant mort-né, à la suite d’une interruption de la grossesse pour motif médical) ; si besoin, un code des chapitres I à XVII et XIX précise le DP53 ;
- acte d’accouchement ;
- âge gestationnel et date des dernières règles.

Les produits d’IMG à partir de vingt-deux semaines révolues d’aménorrhée ou d’un poids d’au moins cinq-cents grammes donnent lieu à la production d’un RUM par convention, le DP est codé P95. –.
