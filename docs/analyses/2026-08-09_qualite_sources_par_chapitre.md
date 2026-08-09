# Qualité des sources de synonymes par chapitre CIM-10

**Date** : 2026-08-09
**Statut** : analyse close, règles R1/R2 arrêtées, implémentation renvoyée au
chantier `chapter_policy`
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
l'angle mort §7.1, qui s'est révélé plus sérieux que prévu.

### 3.3 Renvois ANS « États mentionnés en … »

Le RDF ANS contient des renvois de la forme « États mentionnés en C15-C26 »,
qui ne décrivent rien : ce sont des pointeurs vers une plage de codes. **559
lignes** dans le CSV, dont **249 inclusions** et 185 synonymes.

> **Amendement du 2026-08-09** — l'analyse initiale plaçait ces renvois dans
> la section Formulations et concluait « à filtrer de la section
> Formulations ». **Vérification faite, c'est inexact** : ANS ne fait pas
> partie des sources de cette section (`cards.FORMULATION_SOURCES_EXCLUDED`),
> et les 185 synonymes ANS porteurs du motif **n'apparaissent nulle part dans
> les fiches** — contrôlé sur N13.6, dont la fiche ne contient pas la chaîne.
> Ce sont les *inclusions* ANS qui remontent, dans la section **« Périmètre
> clinique du code »**. Exemple, fiche Z85.00 :
>
> ```
> ## Périmètre clinique du code
> Inclusions héritées de la catégorie Z85.0 :
> - États mentionnés en C15- C26
> Au niveau du code :
> - États mentionnés en C15–C21
> ```
>
> La règle R1 vise donc la section **Périmètre clinique**, pas Formulations.
> Portée réelle mesurée : **204 inclusions** retirées, dont 176 sur le
> chapitre XXI — ce qui confirme le constat d'origine (« ANS sur les Z »),
> seule la section visée était erronée.

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

| Plage | Section Formulations | Génération LLM |
|---|---|---|
| **XVIII** (R00-R99) | **Oui**, toutes sources réelles | **Non** |
| **XIX** (S00-T98) | **Non** (Index, AP-HP, ORPHANET, CepiDc exclus) | Non |
| **XX** (V01-Y98) | **Non** (AP-HP, ORPHANET, CepiDc exclus ; Index déjà absent) | Non |
| **XXI** (Z00-Z99) | **Non** (Index, AP-HP, ORPHANET, CepiDc exclus) | Non |
| **T36-T50** (bloc) | CepiDc exclu en toutes circonstances | — |
| Tous les autres | Oui | Oui |

Plus, transversalement : **retrait des renvois ANS « États mentionnés en … »
de la section Périmètre clinique** (cf. amendement §3.3).

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

### Effet mesuré de R1 (CSV courant)

Formulations candidates : **161 607 → 124 536**, soit **37 071 écartées**.

| Chapitre | Famille | Écartées |
|---|---|---|
| XX | CepiDc | 12 956 |
| XIX | CepiDc | 10 869 |
| XXI | CepiDc | 7 293 |
| XIX | Index | 3 935 |
| XXI | Index | 1 695 |
| XIX | AP-HP | 235 |
| XX | AP-HP | 49 |
| XXI | AP-HP | 39 |

**2 219 codes** perdent entièrement leur section Formulations (1 089 en XIX,
575 en XXI, 555 en XX), sur 8 629 codes qui en avaient une. C'est l'effet
recherché : ces sections n'apportaient rien.

Coût honnête à connaître : quelques entrées correctes disparaissent avec le
reste. Exemple S52.50, dont l'unique formulation était « Fracture traumatique
fermée de l'extrémité distale du radius » — parfaitement lisible. Le pari est
que le libellé officiel suffit sur ces chapitres.

## 5. Règle R2 — plafond par source des fiches catégories

Étendre aux fiches catégories le plafonnement par source des fiches feuilles.
Le prototype plafonne par **famille** de sources (les neuf feuilles AP-HP
comptant pour une) plutôt que par libellé : la question posée est la
domination d'un *type* d'apport.

### Calibration

Mesure sur les **590 catégories** dont le vivier dépasse encore 50 après R1,
composition de la fiche réellement rendue (donc après le plafond global de 50) :

| Plafond/source | Formulations rendues | Formulations perdues | Part CepiDc médiane | Catégories > 80 % |
|---|---|---|---|---|
| aucun (actuel) | 29 500 | 0 | 0,72 | 226 |
| 5 | 6 704 | 22 796 | 0,455 | 41 |
| **10** (convention feuilles) | 12 386 | 17 114 | 0,476 | 47 |
| 15 | 17 553 | 11 947 | 0,484 | 51 |
| **20** | 22 035 | **7 465** | 0,488 | 54 |

**Lecture du coude.** L'essentiel du bénéfice vient du simple fait d'avoir un
plafond : les catégories au-dessus de 80 % s'effondrent de 226 à 41-54, et la
part médiane passe de 0,72 à ~0,48. Entre 5 et 20, les métriques d'équilibre
ne bougent presque plus (médiane 0,455 → 0,488 ; 41 → 54 catégories) alors que
le volume conservé **triple** (6 704 → 22 035).

**Le coude est donc à 20**, pas à 10. Retenir 10 pour l'unité de convention
avec les fiches feuilles coûte 9 649 formulations de plus que 20, pour
seulement 7 catégories de moins au-dessus de 80 %. Arbitrage à trancher :
convention unique contre diversité. Recommandation : **20**, en documentant
l'écart de convention plutôt qu'en le masquant.

### Exemple d'effet (plafond 10)

| Catégorie | Avant | Après |
|---|---|---|
| C00-C75 | 13 978 formulations, 96 % CepiDc | 30 formulations : Index 10, CepiDc 10, AP-HP 10 |
| C76-C80 | 6 370, 99 % CepiDc | 30 : Index 10, CepiDc 10, AP-HP 10 |
| C81-C96 | 3 974, 92 % CepiDc | 30 : Index 10, CepiDc 10, AP-HP 10 |

## 6. Ce que ces règles ne font pas

Elles ne touchent **ni le CSV maître, ni les Parquets, ni les rapports**.
Toute l'information reste ingérée et traçable ; seul l'assemblage des fiches
filtre. C'est un point à ne pas confondre — cf. le pitfall à inscrire au
CLAUDE.md.

## 7. Angles morts

### 7.1 Le format « chemin d'index » n'est pas propre à XIX et XXI — et c'est sérieux

R1 n'exclut l'Index que sur XIX et XXI. Or la mesure de prévalence du format
« chemin d'index » (heuristique : virgules de subordination en cascade et/ou
renvoi « voir ») montre qu'il domine **presque partout**, et davantage sur des
chapitres non exclus que sur les chapitres exclus :

| Chapitre | Entrées Index | Format chemin | Part |
|---|---|---|---|
| **XV** (grossesse) | 2 772 | 2 500 | **90,2 %** |
| **XVI** (périnatal) | 1 485 | 1 260 | **84,8 %** |
| XIX *(exclu par R1)* | 3 935 | 3 080 | 78,3 % |
| II (tumeurs) | 1 483 | 1 153 | 77,7 % |
| XXI *(exclu par R1)* | 1 695 | 1 232 | 72,7 % |
| IX (circulatoire) | 1 872 | 1 299 | 69,4 % |
| … | | | |
| XVIII (symptômes) | 1 062 | 405 | 38,1 % |

**Conclusion à instruire** : le critère pertinent est probablement **le format
de l'entrée**, pas le chapitre. Une règle transversale « écarter les entrées
Index de forme chemin d'index » traiterait le problème à la racine et
récupérerait au passage les bonnes entrées Index de XIX et XXI (les 22 % de
XIX qui n'ont pas ce format). R1 reste un bon premier pas, mais il traite le
symptôme là où il est le plus visible, pas la cause.

### 7.2 Autres blocs candidats à une politique spéciale

Au-delà de T36-T50 : **O00-O99** (grossesse — logique d'épisode plutôt que de
diagnostic, et 90 % de chemins d'index côté Index), **P00-P96** (période
périnatale, même profil), et les **codes U** du chapitre XXII (usage
provisoire, 7 formulations CepiDc seulement).

### 7.3 ORPHANET n'alimente pas encore la section Formulations

Son exclusion dans R1 est aujourd'hui sans effet mesurable
(`cards.FORMULATION_SOURCES_EXCLUDED`). La règle prépare le cas où la section
s'ouvrirait à cette source.

### 7.4 L'apport des fiches lui-même est en question

Une évaluation manuelle par médecins DIM (cf.
[`2026-08-09_evaluation_fiches_et_contexte_llm.md`](2026-08-09_evaluation_fiches_et_contexte_llm.md))
ne montre **pas d'apport mesurable** des fiches dans les prompts de génération
de CRH. Cela ne périme pas ce travail — améliorer la qualité des formulations
est une condition nécessaire — mais cela recentre l'enjeu : la piste « fiche
réduite aux formulations seules » y figure parmi les conditions à tester, ce
qui rend le contenu de cette section d'autant plus déterminant.
