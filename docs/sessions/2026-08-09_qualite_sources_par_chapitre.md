# Qualité des sources par chapitre — trace, notebook et règles R1/R2 (volet B)

**Date** : 2026-08-09
**Type** : analyse reproductible + prototypage de règles, aucune implémentation en `src/`
**Statut** : terminé — notebook exécuté de bout en bout, 366 tests verts, rien poussé
**Livrables** : [`docs/analyses/2026-08-09_qualite_sources_par_chapitre.md`](../analyses/2026-08-09_qualite_sources_par_chapitre.md),
[`scripts/explore/qualite_sources_par_chapitre.ipynb`](../../scripts/explore/qualite_sources_par_chapitre.ipynb)

Le volet A de la journée (clôture du chantier 1 et push) est consigné dans
[`2026-08-09_merge_cepidc.md`](2026-08-09_merge_cepidc.md).

---

## 1. Résultat en une ligne

L'analyse de qualité des sources est figée dans un document de trace, rejouée
par un notebook qui tourne de bout en bout sur `main`, et les règles R1/R2 y
sont prototypées et mesurées. **Toutes les conclusions qualitatives de
l'analyse initiale se reproduisent**, une seule a dû être amendée — et un
angle mort sérieux est apparu.

## 2. Extension de `loaders_dev`

Une seule, minimale. `_load_external_frames()` appelait
`load_external_frames(orphanet_xml, hector_xlsx)` avec deux arguments :
**CepiDc était silencieusement absent de `ctx.external`** depuis son
intégration. Le troisième argument est passé, avec la même garde d'existence
non fatale que `recode-icd build external`. `ctx.external` expose désormais
les douze sources (146 948 lignes CepiDc incluses).

Aucune logique métier n'a été ajoutée au module : la dérivation
code → chapitre / bloc / catégorie vit dans le notebook.

## 3. Le notebook

`scripts/explore/qualite_sources_par_chapitre.py` est la **source de vérité**
(diffable, lintable, exécutable directement) ; le `.ipynb` en est le rendu
régénéré. 24 cellules de code, 49 cellules au total, exécution complète sans
erreur, graines fixées partout.

Sections : (a) volumétrie et écarts avec les chiffres pré-merge,
(b) échantillonneur paramétré rejouant les trois inspections,
(c) détecteur de motifs parasites et ses faux positifs, (d) prototype R1/R2
avec mesure d'effet et calibration, (e) angles morts.

En tête du fichier, l'avertissement demandé : **quand `chapter_policy` sera
implémenté dans `src/`, la section (d) devra importer l'implémentation réelle
au lieu du prototype**, faute de quoi les deux divergeront en silence.

### Outillage rendu fonctionnel au passage

`_convert_to_ipynb.py` était committé **sans sa dépendance** — `nbformat`
n'était dans aucun extra du projet — et codé en dur sur le notebook de mai
2026. Il ne pouvait donc convertir ni ce notebook-ci, ni aucun autre. Ajout
d'un extra `notebook` (nbformat, nbconvert, ipykernel) et généralisation du
convertisseur, qui prend maintenant le script en argument et dérive son
en-tête du docstring de module.

## 4. Trois défauts de modélisation corrigés

La version intermédiaire du notebook, emportée par le commit `4e60f76`,
contenait trois erreurs que la confrontation aux chiffres de référence a
révélées. Elles méritent d'être consignées : les deux dernières produisaient
des résultats *plausibles mais faux*.

1. **Drapeau regex perdu.** `re.compile(..., flags=re.IGNORECASE)` puis
   passage de `.pattern` à polars : le drapeau Python ne traverse pas, et le
   motif `états? mentionn` ne matchait pas « **É**tats mentionnés ». Résultat
   affiché : 0 renvoi ANS détecté, au lieu de 204. Corrigé par un drapeau
   `(?i)` **inline**.
2. **Catégorie lue dans le `path`.** Prendre le segment d'indice 2 donne la
   catégorie sur la plupart des chapitres, mais un **sous-bloc** sur ceux qui
   imbriquent les blocs — C50.8 vit sous `II/C00-C97/C00-C75/C50-C50/C50/C50.8`.
   La mesure comptait donc « C00-C75 » comme une catégorie de 13 978
   formulations. Corrigé en dérivant la catégorie du code lui-même (partie
   avant le point), ce que fait `cards.py`. La résolution de bloc teste
   désormais **tous** les niveaux, du plus interne au plus large.
3. **Troncature alphabétique au lieu d'un tirage.** `cards.py` tronque à 50
   avec `rng.sample`, un tirage uniforme qui **préserve en espérance la
   composition par source**. Modéliser cela par une tête de liste triée
   biaise la composition (elle privilégie les premières feuilles) et faisait
   mesurer une part CepiDc médiane de 0,50 au lieu de 0,76. Corrigé par un
   ordre pseudo-aléatoire à graine fixe (hash), déterministe et non biaisé.

**Validation croisée après correction** : les mesures reproduisent
exactement le chantier 1 — 737 catégories dont le vivier dépasse 50, part
CepiDc médiane 0,76, 321 catégories au-dessus de 80 % (chantier 1 : 737 /
76,4 % / 325). Sans cette confrontation, les trois défauts seraient passés.

## 5. Chiffres — ce qui tient, ce qui bouge

Politique retenue et appliquée : le document de trace fige les chiffres
pré-merge datés ; le notebook tourne sur le CSV courant et signale les écarts.

**Écart nul** sur les sept valeurs de référence recalculables (AP-HP et Index
par chapitre : 112/235/49/39 et 3 935/0/1 695). Le merge CepiDc n'a pas touché
ces sources.

**Écart méthodologique signalé, non réécrit** sur les taux de motifs
parasites : la référence les calculait **par lettre** sur le dictionnaire brut
(Z 10,7 %, Y 12,4 %, X 9,2 %, T 2,7 %), le notebook les calcule **par
chapitre** sur le CSV post-dédup (XXI 13,7 %, XX 8,6 %, XIX 2,3 %). Ordres de
grandeur et classement conservés.

### Un amendement qualitatif — signalé comme convenu

Le constat n° 3 affirmait : « ANS sur les Z : renvois *États mentionnés en
K70–K87* — à filtrer de la **section Formulations** ». **La section est
erronée.** ANS ne fait pas partie des sources de la section Formulations
(`cards.FORMULATION_SOURCES_EXCLUDED`), et les 185 synonymes ANS porteurs du
motif **n'apparaissent nulle part dans les fiches** — contrôlé sur N13.6.
Ce sont les *inclusions* ANS qui remontent, dans **« Périmètre clinique du
code »** (vérifié sur la fiche Z85.00).

Le fond du constat tient — 204 lignes concernées, dont 176 sur le chapitre XXI
— seule la cible de la règle change. Le document de trace porte l'amendement
avec sa mention datée, et R1 vise la bonne section.

## 6. Effet mesuré des règles

**R1** écarte 37 071 des 161 607 formulations candidates (161 607 → 124 536),
et vide entièrement la section Formulations de **2 219 codes** sur les 8 629
qui en avaient une (1 089 en XIX, 575 en XXI, 555 en XX). Le retrait des
renvois ANS retire 204 inclusions.

Coût honnête consigné dans le document : quelques entrées correctes partent
avec le reste — S52.50 perd son unique formulation, « Fracture traumatique
fermée de l'extrémité distale du radius », parfaitement lisible.

**R2 — calibration** sur les 590 catégories dont le vivier dépasse encore 50
après R1, composition de la fiche réellement rendue :

| Plafond/source | Rendues | Perdues | Part CepiDc médiane | Catégories > 80 % |
|---|---|---|---|---|
| aucun (actuel) | 29 500 | 0 | 0,72 | 226 |
| 5 | 6 704 | 22 796 | 0,455 | 41 |
| 10 (convention feuilles) | 12 386 | 17 114 | 0,476 | 47 |
| 15 | 17 553 | 11 947 | 0,484 | 51 |
| **20** | 22 035 | **7 465** | 0,488 | 54 |

**Le coude est à 20, pas à 10.** L'essentiel du bénéfice vient d'avoir un
plafond quelconque : les catégories au-dessus de 80 % s'effondrent de 226 à
41-54 et la médiane de 0,72 à ~0,48. Entre 5 et 20 les métriques d'équilibre
ne bougent quasiment plus, alors que le volume conservé triple. Retenir 10
pour l'unité de convention coûte 9 649 formulations de plus que 20, pour
7 catégories de moins au-dessus de 80 %.

Recommandation portée au document : **20**, en documentant l'écart avec le
plafond des fiches feuilles plutôt qu'en le masquant. Décision à trancher au
chantier `chapter_policy`.

## 7. L'angle mort le plus sérieux

R1 n'exclut l'Index CIM-10 vol3 que sur XIX et XXI, au motif de son format
« chemin d'index ». La mesure de prévalence de ce format montre qu'il **domine
presque partout, et davantage sur des chapitres non exclus** :

| Chapitre | Part du format « chemin d'index » |
|---|---|
| XV (grossesse) | **90,2 %** |
| XVI (périnatal) | **84,8 %** |
| XIX *(exclu par R1)* | 78,3 % |
| II (tumeurs) | 77,7 % |
| XXI *(exclu par R1)* | 72,7 % |
| XVIII (symptômes) | 38,1 % |

Le critère pertinent est donc vraisemblablement **le format de l'entrée, pas
le chapitre**. Une règle transversale traiterait la cause et récupérerait au
passage les 22 % de bonnes entrées Index de XIX. R1 reste un premier pas
défendable, mais il traite le symptôme là où il est visible.

Autres angles morts consignés : blocs O00-O99 et P00-P96 candidats à une
politique propre ; ORPHANET dont l'exclusion est aujourd'hui sans effet ; et
le fait que l'apport même des fiches est remis en question par l'évaluation
manuelle (`docs/analyses/2026-08-09_evaluation_fiches_et_contexte_llm.md`).

## 8. Diffs et état git

| Commit | Objet |
|---|---|
| `4e60f76` *(le tien)* | a emporté une version intermédiaire du notebook et l'extension `loaders_dev` |
| `2fef41f` | extra `notebook` + convertisseur paramétrable |
| `4e1a807` | document de trace, notebook corrigé et exécuté |

Vérifications : **366 tests verts**, `ruff check` propre sur `src/`, `tests/`
et les scripts modifiés, `ruff format --check` propre, `mypy` propre.

Rien n'a été implémenté dans `src/` hormis l'extension de chargement — R1 et
R2 restent du prototype, conformément au périmètre.

**Deux commits locaux non poussés** (`2fef41f`, `4e1a807`).
