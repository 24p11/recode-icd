# Qualité des sources de synonymes par chapitre CIM-10

**Date** : 2026-08-09
**Statut** : analyse close ; règles **R1** (allégée) et **R2 = 20** arrêtées,
**R3** énoncée avec son détecteur instrumenté mais **variante non figée** ;
implémentation renvoyée au chantier `chapter_policy`
**Notebook reproductible** : [`scripts/explore/qualite_sources_par_chapitre.ipynb`](../../scripts/explore/qualite_sources_par_chapitre.ipynb)
(source `.py` du même nom — modifier le `.py`, pas le notebook)

Ce document est la **trace de référence** que la future section
`chapter_policy` du CLAUDE.md citera. Il fige les constats et la justification
métier des règles ; le notebook les rejoue et en mesure l'effet sur le CSV
courant.

---

## 1. Question posée

Les fiches descriptives injectent, dans la section « Formulations cliniques
alternatives », des libellés issus de quatre familles de sources externes.
Toutes ne se valent pas selon le chapitre CIM-10 : certains chapitres n'ont
pas besoin de formulations alternatives du tout, et certaines sources y
produisent des entrées activement nuisibles.

L'enjeu est la qualité du corpus annoté en aval : une formulation imprécise
brouille le périmètre du code et corrompt le dataset d'entraînement.

## 2. Méthode et statut des chiffres

**Deux jeux de chiffres coexistent volontairement dans ce document.**

- Les **chiffres de référence** ci-dessous portent sur le CSV maître
  **pré-merge CepiDc** (199 970 lignes) et sur le dictionnaire CepiDc brut
  (~147 000 lignes). Ils sont **figés, datés du 2026-08-09**, et ne sont pas
  réécrits.
- Le **notebook tourne sur le CSV courant** (321 097 lignes, post-merge et
  post-dédup tolérante). Sa cellule (a) affiche explicitement l'écart avec les
  chiffres figés plutôt que de les remplacer.

Vérification faite au 2026-08-09 : sur les sept valeurs de référence
recalculables (AP-HP et Index par chapitre), **l'écart est nul** — le merge
CepiDc n'a pas touché ces sources. Les volumes CepiDc, eux, diffèrent
mécaniquement : le dictionnaire brut compte ~147 000 entrées, dont 121 127
seulement entrent au CSV après dédup tolérante, filtrage des codes orphelins
et des codes non terminaux.

## 3. Constats

### 3.1 Les sources externes métier sont marginales sur XVIII–XXI

Synonymes AP-HP : **112** sur R00-R99, **235** sur S00-T98, **49** sur V01-Y98,
**39** sur Z00-Z99. ORPHANET y est quasi nul (15 entrées sur tout le chapitre
XIX, 0 sur XX et XXI).

Conséquence : les exclure de ces chapitres coûte très peu.

### 3.2 Index CIM-10 vol3 — un problème de format, pas de légitimité

Les volumes sont importants (**3 935** synonymes sur S00-T98, **1 695** sur
Z00-Z99, **0** sur V01-Y98), mais le format dominant est le **chemin d'index
alphabétique inversé avec renvois**, illisible comme formulation de compte
rendu :

> S65.0 — « Traumatisme(s) (de) (voir aussi le type précisé de traumatisme),
> artère, cubitale (niveau avant-bras), poignet et main »

> S35.2 — « Traumatisme(s) (de) (voir aussi le type précisé de traumatisme),
> artère, mésentérique (inférieure) »

La qualité reste **mélangée** : sur les Z, on trouve aussi bien
« Difficulté(s) de(s), liées à, divorce dans la famille » (chemin d'index) que
« Séropositivité au vih » (formulation naturelle parfaitement utilisable).
L'exclusion par chapitre est donc un compromis, pas une vérité — voir
le §8.1 : ce constat a finalement donné la règle R3 (§6).

### 3.3 Renvois ANS « États mentionnés en … »

Le RDF ANS contient des renvois de la forme « États mentionnés en C15-C26 »,
qui ne décrivent rien : ce sont des pointeurs vers une plage de codes. **559
lignes** dans le CSV, dont **249 inclusions** et 185 synonymes.

> **Amendement du 2026-08-09, acté — la sous-règle est retirée.**
> L'analyse initiale plaçait ces renvois dans la section Formulations et
> concluait « à filtrer de la section Formulations ». **C'est inexact** : ANS
> ne fait pas partie des sources de cette section
> (`cards.FORMULATION_SOURCES_EXCLUDED`), et les 185 synonymes ANS porteurs du
> motif **n'apparaissent nulle part dans les fiches** — contrôlé sur N13.6,
> dont la fiche ne contient pas la chaîne. Ce sont les *inclusions* ANS qui
> remontent, dans la section **« Périmètre clinique du code »**. Exemple,
> fiche Z85.00 :
>
> ```
> ## Périmètre clinique du code
> Inclusions héritées de la catégorie Z85.0 :
> - États mentionnés en C15- C26
> Au niveau du code :
> - États mentionnés en C15–C21
> ```
>
> **Décision (RF, 2026-08-09)** : la sous-règle est **retirée de R1, sans
> objet**. Là où ces renvois atterrissent effectivement — le périmètre
> clinique — un renvoi de plages de codes est une **information légitime** :
> il dit au lecteur quelles affections le code recouvre. Rien n'est donc
> filtré ; les « États mentionnés en … » restent en place.

### 3.4 CepiDc — qualité fortement dépendante du chapitre

**Excellent sur les chapitres diagnostiques.** Le dictionnaire est constitué
de formulations rédigées par des médecins, en registre télégraphique proche
du compte rendu réel :

| Chapitre | Exemples CepiDc |
|---|---|
| X (respiratoire) | « broncho-pneumopathie inhalation », « pneumopathie commune lobaire inférieure », « séquelles pleurésie purulente » |
| II (tumeurs) | « lymphoplasmocytome médullaire IgM », « adénocarcinome mucineux sinus ethmoïdal », « métastase temporale » |

Taux de motifs parasites : **0,2 %** sur le chapitre II, **0,4 %** sur XVIII,
**0,5 %** sur X et XI — négligeable.

**Dangereux hors contexte diagnostique.** Le certificat de décès enregistre
la cause, pas le diagnostic codé : sur les intoxications médicamenteuses et
les causes externes, cela produit des noms de médicaments nus et des mentions
de prise ou de traitement, inutilisables comme formulation de CRH :

| Code | Formulation CepiDc |
|---|---|
| T46.0 | « Gutron » |
| T43.5 | « Droleptan » |
| T38.5 | « THS » |
| T42.4 | « prise Havlane » |
| T50.7 | « sous Vectarion » |
| T45.6 | « traitement Actilyse » |
| T45.1 | « intoxication Azathioprine » |

Taux de motifs parasites par chapitre (CSV courant) : **XXI 13,7 %**,
**XX 8,6 %**, XV 3,6 %, XIII 3,1 %, **XIX 2,3 %**.

> Écart avec les chiffres de référence, qui étaient calculés **par lettre**
> sur le dictionnaire brut (Z 10,7 %, Y 12,4 %, X 9,2 %, T 2,7 %) et non par
> chapitre. Les ordres de grandeur et le classement sont conservés ; XXI est
> mesuré un peu plus haut (13,7 % contre 10,7 %) parce que le chapitre
> agrège tous les Z et que la dédup a retiré des entrées propres.

**Nuance essentielle sur l'heuristique.** Le motif « mot unique capitalisé »
n'est parasite que pour les noms de médicaments. Ailleurs il capture des
acronymes et des éponymes qui sont d'**excellents** synonymes :

> RCIU (P05.9), CIVD (O67.0), OMI (R60.0), LAM4 (C92.5), Hashimoto (E06.3),
> Addison (E27.1), Merkelome (C44.9), Pancoast-Tobias (C34.1),
> Schinzel-Giedion (Q87.0)

C'est la raison décisive de préférer **une politique par chapitre et par bloc
à une curation textuelle générale** du CepiDc : aucune heuristique textuelle
ne sépare « Gutron » de « Hashimoto ».

### 3.5 Déséquilibre des fiches catégories

Les fiches feuilles plafonnent l'Index et CepiDc à 10 entrées chacun
(`INDEX_SAMPLE_SIZE`) mais laissent AP-HP libre. Les fiches catégories, elles,
n'ont **aucun plafond par source** — seulement un plafond global de 50
(`CATEGORY_FORMULATIONS_MAX`). CepiDc apportant 121 127 des 161 607
formulations candidates (75 %), il domine mécaniquement.

Mesure sur les **737 catégories dont le vivier dépasse 50** : part médiane de
CepiDc dans la fiche rendue **76 %**, et **321 catégories au-dessus de 80 %**.
Cas extrêmes : C00-C75 (96 % de CepiDc), C76-C80 (99 %), C81-C96 (92 %).

## 4. Règle R1 — filtrage par plage de codes × source

S'applique **à l'assemblage des fiches uniquement**. Le CSV maître et les
Parquets restent complets, chapitres exclus compris.

| Plage | Sources externes (AP-HP, ORPHANET, CepiDc, LLM) | Génération LLM |
|---|---|---|
| **XVIII** (R00-R99) | **Conservées** | **Non** |
| **XIX** (S00-T98) | **Exclues** | Non |
| **XX** (V01-Y98) | **Exclues** | Non |
| **XXI** (Z00-Z99) | **Exclues** | Non |
| **T36-T50** (bloc) | Exclues — CepiDc en toutes circonstances | Non |
| Tous les autres | Conservées | Oui |

> **R1 ne porte plus l'exclusion de l'Index CIM-10 vol3.** La version initiale
> l'excluait de XIX et XXI ; la mesure du §8.1 a montré que le problème de
> l'Index est son **format**, présent partout et davantage sur des chapitres
> non exclus. Ce critère est désormais porté par la règle **R3**,
> transversale. R1 se concentre sur les sources externes métier.

> **La sous-règle sur les renvois ANS a été retirée** (cf. amendement §3.3) :
> elle visait une section qu'ANS n'alimente pas, et là où ces renvois
> atterrissent réellement ils sont légitimes.

**Justifications métier.** Les Z sont des codes de circonstance
administrative ou de prise en charge, sans terme médical substituable. Les
V-Y se codent sur les circonstances décrites, pas sur un terme. Les S-T sont
combinatoires par site et nature de lésion : leurs libellés officiels sont
déjà la langue du CRH. Le chapitre XVIII est traité à part parce que les
codes R ont de vraies variantes d'usage courant (« mal de tête » pour R51,
« essoufflement » pour R06.0) — on conserve donc les sources réelles, mais on
interdit la génération LLM, dont les variantes risqueraient d'élargir
indûment le périmètre de codes déjà peu spécifiques.

Le bloc **T36-T50** porte une règle propre parce qu'il se comporte plus comme
des diagnostics classiques que comme des lésions par site : il pourrait
légitimement être exempté un jour de la politique du chapitre XIX. Mais
CepiDc doit y rester exclu quoi qu'il arrive, pour la raison du §3.4.

> **Piège de résolution — à trancher dans le YAML de `chapter_policy`.** Le
> prototype implémente « la règle la plus spécifique **remplace** la moins
> spécifique » (bloc > chapitre > défaut), et non une union. C'est le seul
> choix qui permette de *ré-admettre* une source au niveau bloc — le cas
> prévu pour T36-T50. En contrepartie, une entrée de bloc doit
> **redéclarer** les exclusions du chapitre qu'elle veut conserver ; l'oublier
> ouvre silencieusement des sources. La CIM-10 imbrique jusqu'à trois niveaux
> de bloc (C50.8 vit sous « C00-C97 / C00-C75 / C50-C50 »), et la résolution
> doit donc les tester du plus interne au plus large.

### Effet mesuré de R1 (CSV courant, R1 allégée)

Formulations candidates : **161 607 → 130 166**, soit **31 441 écartées**.

| Chapitre | Famille | Écartées |
|---|---|---|
| XX | CepiDc | 12 956 |
| XIX | CepiDc | 10 869 |
| XXI | CepiDc | 7 293 |
| XIX | AP-HP | 235 |
| XX | AP-HP | 49 |
| XXI | AP-HP | 39 |

**713 codes** perdent entièrement leur section Formulations, sur 8 629 codes
qui en avaient une. C'est nettement moins que dans la version initiale de R1
(2 219 codes) : l'Index restant en place sur XIX et XXI, la plupart de ces
codes y conservent au moins une entrée — celles que R3 laissera passer.

## 5. Règle R2 — plafond par source des fiches catégories

Étendre aux fiches catégories le plafonnement par source des fiches feuilles.
Le prototype plafonne par **famille** de sources (les neuf feuilles AP-HP
comptant pour une) plutôt que par libellé : la question posée est la
domination d'un *type* d'apport.

### Calibration — **décision : R2 = 20**

Mesure sur les **608 catégories** dont le vivier dépasse encore 50 après R1,
composition de la fiche réellement rendue (donc après le plafond global de 50) :

| Plafond/source | Formulations rendues | Formulations perdues | Part CepiDc médiane | Catégories > 80 % |
|---|---|---|---|---|
| aucun (actuel) | 30 400 | 0 | 0,70 | 226 |
| 5 | 6 794 | 23 606 | 0,455 | 41 |
| 10 (convention feuilles) | 12 566 | 17 834 | 0,476 | 47 |
| 15 | 17 823 | 12 577 | 0,484 | 51 |
| **20 — retenu** | **22 395** | **8 005** | **0,488** | **54** |
| 30 | 27 365 | 3 035 | 0,600 | 77 |

**Lecture du coude.** L'essentiel du bénéfice vient du simple fait d'avoir un
plafond : les catégories au-delà de 80 % s'effondrent de 226 à 41-54, et la
part médiane passe de 0,70 à ~0,48. Entre 5 et 20 les métriques d'équilibre ne
bougent presque plus (0,455 → 0,488 ; 41 → 54 catégories) alors que le volume
conservé **triple** (6 794 → 22 395). Au-delà, à 30, le bénéfice se dégrade
franchement (médiane 0,60, 77 catégories au-delà de 80 %).

**20 est donc le dernier palier avant dégradation, à volume maximal.** Retenir
10 aurait coûté 9 829 formulations de plus pour seulement 7 catégories de moins
au-dessus de 80 %.

### Deux plafonds distincts, et pourquoi c'est justifié

La convention n'est volontairement pas unique : **10 sur les fiches feuilles,
20 sur les fiches catégories**. Les viviers ne sont pas comparables. Une fiche
feuille tire d'un **seul code** ; une fiche catégorie **agrège toutes ses
feuilles**, avec un vivier d'un ordre de grandeur supérieur — 3 007
formulations pour C79, contre quelques dizaines pour un code isolé. Appliquer
10 aux deux niveaux serait beaucoup plus mordant sur les catégories, pour un
gain d'équilibre marginal que le tableau ci-dessus chiffre précisément.

L'écart est donc documenté, pas subi. Il devra être explicité dans le YAML de
`chapter_policy` (deux clés distinctes, pas une constante partagée).

### Exemple d'effet (plafond 20)

| Catégorie | Avant | Après |
|---|---|---|
| C79 | 3 007 formulations — CepiDc 2 977, AP-HP 21, Index 9 | 49 — CepiDc 20, AP-HP 20, Index 9 |
| C34 | 1 876 — CepiDc 1 870, Index 6 | 26 — CepiDc 20, Index 6 |
| I77 | 1 709 — CepiDc 1 654, Index 45, AP-HP 10 | 50 — CepiDc 20, Index 20, AP-HP 10 |

## 6. Règle R3 — exclure l'Index sur son format, pas sur son chapitre

**Énoncé.** Une entrée de l'Index CIM-10 vol3 est écartée de la section
Formulations si son **texte** a la forme d'un chemin d'index inversé, quel que
soit son chapitre. Ce critère remplace l'exclusion par chapitre que portait
R1.

**Pourquoi.** Le format « chemin d'index » n'a rien de spécifique à XIX et
XXI ; il domine partout, et davantage sur des chapitres qui n'étaient pas
exclus (cf §8.1). Exclure par chapitre traitait le symptôme là où il était
visible, en jetant au passage les bonnes entrées de XIX/XXI et en laissant
passer les mauvaises ailleurs.

### Détecteur instrumenté

Trois motifs, testés séparément puis combinés :

| Motif | Ce qu'il attrape |
|---|---|
| `voir` | renvois « voir aussi », « - voir » |
| `parentheses_index` | parenthèses grammaticales `(de)`, `(à)`, `(acquise)`, `(dues à)`… |
| `virgules_multiples` | structure inversée à deux virgules ou plus |

Une variante **stricte** a également été mesurée : écarter toute entrée
comportant une virgule, une parenthèse ou un « voir » — autrement dit ne
garder que les entrées d'un seul tenant.

### Validation sur relecture manuelle

Trente entrées Index tirées à graine fixe (`seed=1234`) ont été **relues une à
une**, avec pour critère : *un clinicien écrirait-il cette chaîne telle quelle
dans un compte rendu ?* Verdict : **28 chemins d'index, 2 entrées
directement utilisables** (« Trachéomalacie » J39.8, « Dysbarisme » T70.3).

| Détecteur | VP | FN | FP | VN | Rappel | Précision | Index écarté | Index gardé |
|---|---|---|---|---|---|---|---|---|
| 3 motifs | 27 | 1 | 0 | 2 | 0,964 | 1,000 | 31 203 (85,2 %) | 5 424 |
| strict | 28 | 0 | 0 | 2 | 1,000 | 1,000 | 35 434 (96,7 %) | 1 193 |

Aucun faux positif pour l'un comme pour l'autre. Le seul faux négatif du
détecteur à trois motifs est *« Quatrième, maladie (non sexuellement
transmissible) »* (B08.8) : une seule virgule, et une parenthèse qui n'est pas
un connecteur grammatical.

> **Étiquettes à revalider.** Elles résultent d'**une seule relecture**. Le
> tirage étant reproductible, une seconde lecture peut porter sur exactement
> les mêmes entrées — cellule « Échantillon relu à la main » du notebook.

### La zone grise, et une troisième voie

**4 231 entrées** séparent les deux variantes : celles que les trois motifs
gardent et que la variante stricte écarte. Elles ressemblent à *« Rectite (à),
amibienne »* — le **contenu** est bon (« rectite amibienne »), seul le
**formatage** est de l'index.

Cela ouvre une option qui n'est ni « garder » ni « écarter » :
**normaliser** ces entrées — retirer les parenthèses grammaticales, remettre
les segments dans l'ordre. Elle récupérerait une information réelle, au prix
d'un travail de réécriture. À instruire séparément ; hors du périmètre d'un
détecteur.

**Le détecteur n'est pas encore figé** : le choix entre les deux variantes (ou
l'ouverture de la troisième voie) se fait après lecture des sorties du
notebook.

## 7. Ce que ces règles ne font pas

Elles ne touchent **ni le CSV maître, ni les Parquets, ni les rapports**.
Toute l'information reste ingérée et traçable ; seul l'assemblage des fiches
filtre. C'est un point à ne pas confondre — cf. le pitfall à inscrire au
CLAUDE.md.

## 8. Angles morts

### 8.1 Le format « chemin d'index » n'est pas propre à XIX et XXI — devenu R3

Constat qui a **motivé la création de R3** (§6) et l'allègement de R1. La
prévalence du format « chemin d'index » domine partout, et davantage sur des
chapitres qui n'étaient pas exclus :

| Chapitre | Entrées Index | Part détectée (3 motifs) | Part détectée (strict) |
|---|---|---|---|
| **XV** (grossesse) | 2 772 | **94,8 %** | 99,6 % |
| XIV (génito-urinaire) | 2 220 | 90,9 % | 97,1 % |
| XIX | 3 935 | 90,7 % | 99,2 % |
| **XVI** (périnatal) | 1 485 | 90,4 % | 99,6 % |
| X (respiratoire) | 1 324 | 87,8 % | 98,3 % |
| IX (circulatoire) | 1 872 | 87,2 % | 97,9 % |
| II (tumeurs) | 1 483 | 87,1 % | 100,0 % |
| I | 4 699 | 86,6 % | 97,4 % |
| XXI | 1 695 | 86,4 % | 97,4 % |
| … | | | |
| XVIII (symptômes) | 1 062 | 64,1 % | 83,3 % |

XVIII est le seul chapitre nettement en dessous — cohérent avec le fait que
les codes R ont de vraies variantes d'usage courant, et que c'est le chapitre
où l'on conserve toutes les sources réelles.

Ce point est **traité**, il n'est plus un angle mort. Ce qui reste ouvert est
le choix de la variante du détecteur (cf §6).

### 8.2 Autres blocs candidats à une politique spéciale

Au-delà de T36-T50 : **O00-O99** (grossesse — logique d'épisode plutôt que de
diagnostic, et 90 % de chemins d'index côté Index), **P00-P96** (période
périnatale, même profil), et les **codes U** du chapitre XXII (usage
provisoire, 7 formulations CepiDc seulement).

### 8.3 ORPHANET n'alimente pas encore la section Formulations

Son exclusion dans R1 est aujourd'hui sans effet mesurable
(`cards.FORMULATION_SOURCES_EXCLUDED`). La règle prépare le cas où la section
s'ouvrirait à cette source.

### 8.4 L'apport des fiches lui-même est en question

Une évaluation manuelle par médecins DIM (cf.
[`2026-08-09_evaluation_fiches_et_contexte_llm.md`](2026-08-09_evaluation_fiches_et_contexte_llm.md))
ne montre **pas d'apport mesurable** des fiches dans les prompts de génération
de CRH. Cela ne périme pas ce travail — améliorer la qualité des formulations
est une condition nécessaire — mais cela recentre l'enjeu : la piste « fiche
réduite aux formulations seules » y figure parmi les conditions à tester, ce
qui rend le contenu de cette section d'autant plus déterminant.
