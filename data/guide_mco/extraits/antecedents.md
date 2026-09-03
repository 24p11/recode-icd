<!-- Transcription curée — ANTÉCÉDENTS
     Premier jet produit par scripts/curer_guide_mco.py, À RELIRE.
     Brut : extraits_bruts/antecedents.txt, lignes 27-84.
     Curation déclarée : extraits/curation.yaml.
     Le test garantit qu'aucun mot n'a bougé ; il ne dit rien des
     tableaux, de l'ancrage des notes, ni de ce que pdftotext a perdu. -->

## ANTÉCÉDENTS

Une affection constituant un antécédent personnel — une maladie ancienne guérie — ne doit pas être enregistrée dans le résumé d’unité médicale (RUM) avec le code qu’on utiliserait si elle était présente (« active »), c’est-à-dire qu’elle ne doit pas être codée avec les chapitres I à XIX de la CIM–10 (sinon éventuellement comme une donnée à visée documentaire). La même règle s’impose dans le cas d’un antécédent familial, c’est-à-dire d’une affection dont le patient n’est personnellement pas atteint. Un antécédent personnel ou familial, au sens d’une affection dont le patient n’est plus ou n’est pas atteint au moment du séjour objet du RUM, doit être codé avec le chapitre XXI (« codes Z »).

On trouve dans le chapitre XXI de la CIM–10 des catégories (Z80 à Z99) destinées au codage des antécédents.

Les affections qui entrainent habituellement des séquelles font partie des exclusions de ces catégories.

> Exemples :
> - Z86.1 Antécédents personnels de maladies infectieuses et parasitaires exclut les séquelles de maladies infectieuses et parasitaires ;
> - Z86.7 Antécédents personnels de maladies de l’appareil circulatoire exclut l’infarctus ancien, les séquelles de maladies cérébrovasculaires et le syndrome postinfarctus. [^6: Z86.7 a des extensions, créées pour la version 11 des GHM (2009) : Z86.70 et Z86.71. Leur emploi est obligatoire (voir le Manuel des groupes homogènes de malades).]

Le problème que pose l’utilisation des catégories d’antécédents en général, et d’antécédents personnels en particulier, est celui de la définition du mot « antécédent ». On retient la suivante : une affection ancienne qui n’existe plus et qui n’est pas cause de troubles résiduels [^7: Sinon on parlerait de séquelles, non d’antécédents (voir le point 2 de ce chapitre).] au moment de l’hospitalisation concernée par le recueil d’informations.

Le problème concerne notamment les antécédents personnels de tumeur maligne : à partir de quand un cancer peut-il être considéré comme un antécédent ?

Le choix entre « cancer » et « antécédent de cancer » est d’abord une question médicale, il ne dépend pas du codeur au vu d’une information telle que « cancer datant de 3 ans » ou « cancer datant de 10 ans ». [^8: On s’est longtemps fondé sur un délai de cinq ans. Cette référence est de tradition purement orale, elle n’a jamais figuré dans aucun document officiel. Elle est médicalement erronée puisque la durée à partir de laquelle une rémission autorise à parler d’antécédent de cancer varie, en fonction notamment de l’organe atteint et du type histologique. Il ne faut plus se référer au délai de cinq ans.] Si un clinicien estime qu’un cancer « extirpé chirurgicalement dans sa totalité » est devenu un antécédent, il faut le coder avec la catégorie Z85 de la CIM– 10. S’il considère au contraire qu’il est trop tôt pour parler d’antécédent, il faut l’enregistrer au moyen du code adapté du chapitre II de la CIM–10.

Ainsi, il n’appartient pas au médecin responsable de l’information médicale ni au codeur de trancher entre cancer et antécédent de cancer. Ce diagnostic est de la compétence du médecin qui dispense les soins au patient.
