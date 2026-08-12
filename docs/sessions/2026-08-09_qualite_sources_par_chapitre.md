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

---

# Second tour — arbitrages appliqués et notebook refondu

Arbitrages rendus après lecture du premier rapport. Quatre décisions, plus une
demande sur la forme du livrable.

## 9. R2 fixé à 20

Le balayage a été étendu à 30, ce qui éclaire le coude : entre 5 et 20 les
métriques d'équilibre sont **plates** (part CepiDc médiane 0,455 → 0,488,
41 → 54 catégories au-delà de 80 %) alors que le volume conservé **triple**
(6 794 → 22 395). À 30 en revanche le bénéfice se **dégrade** nettement
(médiane 0,60, 77 catégories). 20 est donc le dernier palier avant
dégradation, à volume maximal.

| Plafond/source | Rendues | Perdues | Part CepiDc médiane | Catégories > 80 % |
|---|---|---|---|---|
| aucun (actuel) | 30 400 | 0 | 0,70 | 226 |
| 5 | 6 794 | 23 606 | 0,455 | 41 |
| 10 (convention feuilles) | 12 566 | 17 834 | 0,476 | 47 |
| **20 — retenu** | **22 395** | **8 005** | **0,488** | **54** |
| 30 | 27 365 | 3 035 | 0,600 | 77 |

**Deux plafonds distincts coexistent** — 10 sur les feuilles, 20 sur les
catégories — et le document justifie l'écart plutôt que de le masquer : les
viviers ne sont pas comparables (une fiche feuille tire d'un seul code, une
fiche catégorie agrège toutes ses feuilles ; C79 en compte 3 007). Le YAML de
`chapter_policy` devra donc porter **deux clés distinctes**, pas une constante
partagée.

## 10. Sous-règle ANS retirée

Actée : la sous-règle « filtrer les renvois ANS de la section Formulations »
est retirée de R1, sans objet. Les « États mentionnés en … » restent dans
« Périmètre clinique du code », où un renvoi de plages est une information
légitime — il dit quelles affections le code recouvre. Le document porte la
décision datée sous le constat n° 3.

## 11. R3 — nouvelle règle transversale

L'angle mort sur l'Index devient une règle à part entière : **le critère
d'exclusion est le format de l'entrée, pas son chapitre**. R1 est allégée en
conséquence — elle ne porte plus l'exclusion Index de XIX/XXI et se concentre
sur les sources externes métier, le bloc T36-T50 et le flag LLM.

Effet de l'allègement : R1 écarte **31 441** formulations au lieu de 37 071, et
seulement **713 codes** perdent leur section Formulations au lieu de 2 219 —
l'Index restant en place, la plupart des codes de XIX/XXI conservent une entrée.

### Détecteur instrumenté, non figé

Trois motifs (`voir`, parenthèses grammaticales, virgules multiples) plus une
variante stricte (toute virgule, parenthèse ou « voir »). Validation contre
**30 entrées Index tirées à graine fixe et relues une à une**, critère : *un
clinicien écrirait-il cette chaîne telle quelle ?* Verdict : 28 chemins
d'index, 2 entrées utilisables (« Trachéomalacie », « Dysbarisme »).

| Détecteur | VP | FN | FP | VN | Index écarté | Index gardé |
|---|---|---|---|---|---|---|
| 3 motifs | 27 | 1 | 0 | 2 | 31 203 (85,2 %) | 5 424 |
| strict | 28 | 0 | 0 | 2 | 35 434 (96,7 %) | 1 193 |

Aucun faux positif des deux côtés. Le seul faux négatif des trois motifs est
« Quatrième, maladie (non sexuellement transmissible) » : une seule virgule et
une parenthèse qui n'est pas un connecteur grammatical.

**Le choix de variante reste ouvert**, et une **troisième voie** est apparue :
4 231 entrées séparent les deux détecteurs, du type « Rectite (à), amibienne »
— contenu bon, formatage d'index. Les **normaliser** plutôt que les écarter
récupérerait une information réelle. Hors périmètre d'un détecteur, à
instruire séparément.

> Les étiquettes de relecture sont celles d'**une seule lecture**. Le tirage
> étant reproductible (`seed=1234`), une seconde relecture porte sur exactement
> les mêmes entrées.

## 12. Backlog — taille du CSV maître

[`docs/backlog/taille_csv_maitre.md`](../backlog/taille_csv_maitre.md) :
53,15 Mo, seuil GitHub 50, limite dure 100. Trois options pesées — Git LFS
(quotas et dépendance au clone), dé-versionnement du CSV reconstructible
(mais c'est le livrable principal, et les tests de régression le lisent),
publication en artefact de release (piste intermédiaire). À trancher **avant**
l'intégration des synonymes LLM, dont le volume sera du même ordre que CepiDc.

Coût moins visible signalé : le fichier étant réécrit intégralement à chaque
build, chaque régénération ajoute ~53 Mo à l'historique git.

## 13. Le notebook, refondu en support didactique

L'ancienne version était un script linéaire avec de simples cellules de titre —
elle ne répondait pas à la demande. Refonte :

- **50 cellules markdown pour 34 de code.** Chaque étape et chaque décision de
  modélisation est expliquée.
- **Fonctions courtes, nommées, dans des cellules dédiées**, séparées de leurs
  cellules d'appel : `echantillon(plage, famille, type_note, n, graine)`,
  `applique_r1`, `applique_r2(df, plafond, graine)`, `calibre(df, plafonds)`,
  `politique_pour`, `marque_motifs_index`, `confusion`. Toutes paramétrables,
  avec une invitation explicite à rejouer avec d'autres arguments.
- **Aucun tableau collé en dur** : tout est reproduit par exécution.
- **Les trois pièges documentés comme encadrés pédagogiques** (« ⚠ Piège »),
  avec ce qu'ils ont produit comme résultat faux : drapeau `IGNORECASE` perdu
  au passage vers polars (0 détection au lieu de 204), catégorie lue dans le
  `path` sur blocs imbriqués (C00-C75 compté comme une catégorie de 13 978
  formulations), troncature alphabétique au lieu d'un tirage (médiane 0,50 au
  lieu de 0,76).

Le `.py` reste la source de vérité (diffable, lintable, exécutable) ; le
`.ipynb` est régénéré. Pour que cela soit possible, le convertisseur a gagné
le marqueur **`# %% [markdown]`** (format percent, compatible jupytext) : son
corps commenté devient une vraie cellule markdown.

Notebook exécuté de bout en bout sur `main` à jour : **0 erreur**, toutes les
cellules exécutées.

## 14. État git

| Commit | Objet |
|---|---|
| `2fef41f` | extra `notebook` + convertisseur paramétrable |
| `4e1a807` | document de trace, notebook corrigé et exécuté |
| `9cb2675` | cellules markdown dans le convertisseur, B018 toléré dans `scripts/explore` |
| `774b5cb` | R1 allégée, R2 = 20, R3, backlog CSV, notebook refondu |

Vérifications finales : **366 tests verts**, `ruff check` propre sur `src/`,
`tests/` et les deux scripts touchés, `ruff format --check` propre, `mypy`
propre. Toujours **rien dans `src/`** hormis l'extension de chargement — R1,
R2 et R3 restent du prototype.

---

# Troisième tour — instruction de la normalisation (2026-08-12)

Les trois commits du second tour ont été poussés. Reste l'instruction de la
« troisième voie » ouverte par la section (e) avant de figer R3.

## 15. Typologie de l'Index

Classement des 36 627 entrées par forme :

| Forme | Avec connecteur de liaison | Sans | Total |
|---|---|---|---|
| 3+ segments | 10 635 | 3 277 | **13 912** |
| 2 segments | 7 097 | 3 830 | **10 927** |
| renvoi (« voir ») | 7 607 | 1 888 | **9 495** |
| 1 segment | 403 | 1 890 | **2 293** |

Les formes courtes — celles que le normalisateur peut traiter — pèsent
**13 220 entrées, soit 36,1 %**. La répartition varie fortement par chapitre :
XVIII est le plus propre (24 % de formes à 1 segment), XV le plus dégradé
(0,7 %, avec 1 975 entrées à 3+ segments sur 2 772).

## 16. Le normalisateur prototype

Périmètre étroit et assumé : **formes à 1-2 segments, sans renvoi**. Trois
opérations déterministes, **sans LLM** — retrait des connecteurs parenthésés
de liaison (ceux dont le contenu entier est un mot outil ; les parenthèses
*qualifiantes* comme `(chronique)` sont conservées), recollement
`segment + qualifiant`, minuscule initiale. Aucun réordonnancement au-delà du
recollement. Les formes à 3+ segments et tous les renvois restent écartés.

## 17. Relecture manuelle de 50 normalisations

Tirage reproductible (`seed=99`), relu entrée par entrée :

| Étiquette | Effectif |
|---|---|
| `correcte` — utilisable telle quelle | **11** (22 %) |
| `degradee` — artefact résiduel, sens non ambigu | **33** (66 %) |
| `fautive` — sens changé ou chaîne inintelligible | **6** (12 %) |

**Le résultat le plus utile n'est pas le score mais la structure des
erreurs** : les deux causes sont détectables par motif, donc corrigeables sans
LLM.

1. **Parenthèses qualifiantes résiduelles** — quasi-totalité des `degradee`,
   et **6 695 normalisations concernées, soit 50,6 %**. Le normalisateur ne
   retire que les connecteurs de liaison, laissant « abcès (embolique)
   (infectieux) (multiple) (pyogène) (septique) sous-dural ».
2. **Inversions d'éponymes et énumérations de synonymes** — totalité des
   `fautive`. Le second segment y est une *tête*, pas un qualifiant :
   « Lipschütz, ulcère de » recollé dans l'ordre donne « lipschütz ulcère de ».
   Le motif `, (syndrome|maladie|ulcère|…) de` en détecte **490, soit 3,7 %**.

## 18. Bilan comparé et traçabilité

| Politique | Gardées | Écartées | Dont réécrites |
|---|---|---|---|
| Détecteur 3 motifs (exclusion seule) | 5 424 | 31 203 | — |
| Détecteur strict (exclusion seule) | 1 193 | 35 434 | — |
| **R3 révisée** | **13 220** | 23 407 | 11 331 |

La R3 révisée récupère **13 220 entrées** là où les détecteurs purement
exclusifs n'en gardaient que 5 424 et 1 193.

**Traçabilité** — documentée dans le notebook (encadré dédié) et dans le
document de trace (§6 bis et §7, mention datée du 2026-08-12) : la
normalisation est une **transformation de rendu**, appliquée par `cards.py` à
l'assemblage de la fiche. Le CSV maître n'est jamais modifié, la colonne
`texte` conserve la forme source de l'Index vol3, qui reste la seule chose
auditable. C'est la condition pour rester conforme au principe « jamais
d'agrégation silencieuse » : normaliser en amont rendrait le libellé officiel
irrécupérable.

C'est aussi le seul mécanisme des trois règles qui *réécrit* du texte plutôt
que d'en écarter — d'où l'insistance sur ce point.

## 19. R3 reste non figée — trois décisions

1. **Étendre le retrait aux parenthèses qualifiantes ?** Levier n°1, il touche
   la moitié des normalisations. Il fait perdre de l'information
   (`(chronique)`, `(aigu)`) mais produit des formulations réellement
   utilisables.
2. **Inversions d'éponymes** : les exclure (motif détectable, ~4 %) ou les
   **inverser** explicitement, le second segment étant la tête ?
3. **Seuil d'acceptation** des `degradee`, pour une section dont le rôle est
   d'élargir le rappel et non de fournir un libellé officiel.

## 20. État git

| Commit | Objet |
|---|---|
| `032b440` | typologie, normalisateur, relecture des 50, traçabilité |

Le notebook compte désormais **67 cellules markdown pour 44 de code**,
exécuté de bout en bout sans erreur. Vérifications : 366 tests verts, `ruff`
et `mypy` propres. Toujours **rien dans `src/`**.

**Un commit local non poussé** (`032b440`).

---

# Quatrième tour — normalisateur v2 (2026-08-12)

Les trois décisions attendues ont été prises et implémentées. **Le seuil
d'acceptation n'est pas atteint** : R3 reste non figée, mais le chemin pour
l'atteindre est désormais entièrement cartographié.

## 21. Les trois décisions appliquées

**Retrait complet des parenthèses qualifiantes.** La justification de fond est
maintenant documentée dans le notebook et le document de trace : les
conventions du **volume 3 de la CIM-10** posent que les termes parenthésés
sont des **modificateurs non essentiels**, dont la présence ou l'absence ne
change pas l'affectation du code. Les retirer restitue le terme dans sa forme
minimale affectante — c'est l'application de la sémantique officielle de
l'index, pas une approximation. Parenthèses résiduelles : **6 695 → 47**.

**Inversion des éponymes**, bornée au motif « second segment se terminant par
`de` / `d'` / `du` / `des` », avec gestion de l'élision
(« Eberth, maladie d' » → « maladie d'Eberth », sans espace). **490 entrées**
inversées ; tout autre motif reste écarté.

**Minuscule initiale épargnant les noms propres.** Le discriminant retenu est
le corpus lui-même : on ne minusculise que si le premier mot est attesté en
minuscule **ailleurs dans le CSV, hors Index**. La justification est
structurelle — l'Index capitalise *toute* tête d'entrée par convention
éditoriale, il ne peut donc pas témoigner de la casse naturelle d'un terme,
alors que CepiDc, AP-HP, OFS et ANS sont du texte médical courant. Vérifié :
`Borrelia`, `Stellantchasmus`, `Lipschütz`, `Eberth` préservés ; `rectite`,
`dysurie` minusculisés.

## 22. Échantillon de 100 — le seuil n'est pas atteint

Tirage `seed=2025`, distinct du premier. Lecture préliminaire, à confirmer :

| Étiquette | v1 (50) | **v2 (100)** | Seuil | Verdict |
|---|---|---|---|---|
| `correcte` | 22 % | **57 %** | — | — |
| `degradee` | 66 % | **40 %** | ≤ 10 % | **non atteint** |
| `fautive` | 12 % | **3 %** | 0 | **non atteint** |

Progrès net — les correctes passent de 22 % à 57 % — mais les deux seuils
sont manqués.

## 23. Diagnostic : les deux écarts sont traitables

**Les 3 fautives relèvent d'un même manque.** Le second segment est la tête du
terme mais **sans préposition finale**, donc hors du motif d'inversion :
« Autosome, site fragile » et « Xxxx, syndrome » (caryotype 48,XXXX) appellent
exactement l'inversion appliquée aux éponymes. La troisième,
« Nca, bien portant », a pour premier segment une **abréviation d'index**
(`nca`) et n'est pas un terme. Conformément à la consigne « corrigée par motif
ou versée aux exclusions » : élargir l'inversion aux seconds segments réduits
à un substantif de tête nu, et exclure les entrées dont le premier segment est
une abréviation d'index.

**Les 40 % de dégradées ont une cause unique.** C'est la **préposition de
liaison manquante** : « Hypoplasie (de), cerveau » rend « hypoplasie cerveau »
là où le français demande « hypoplasie du cerveau ».

C'est le point le plus intéressant du tour, parce qu'il révèle une limite du
raisonnement qui a fondé la décision 1. Le retrait complet est juste pour les
modificateurs *qualifiants* — ils sont bien non essentiels au sens du volume 3.
Mais les connecteurs *de liaison* ne sont pas des modificateurs : ce sont des
**marqueurs de rection grammaticale**, et le `(de)` retiré indiquait
précisément la liaison à employer. **L'information nécessaire était dans la
source, et le retrait uniforme l'a détruite.**

Les **consommer comme joint** plutôt que les supprimer traiterait la
quasi-totalité des dégradées :

```
« Hypoplasie (de), cerveau »    → « hypoplasie du cerveau »
« Perforation (de), estomac »   → « perforation de l'estomac »
« Carence (en), phénylalanine » → « carence en phénylalanine »
```

Contraction (`de` + `le` → `du`) et élision (`de` + voyelle → `de l'`) sont
déterministes en français. Non appliqué ici, la décision du jour étant le
retrait complet — **c'est le correctif à instruire au prochain tour**.

## 24. Bilan global révisé

| Politique | Conservées telles quelles | Normalisées | Écartées |
|---|---|---|---|
| Détecteur 3 motifs (exclusion seule) | 5 424 | 0 | 31 203 |
| Détecteur strict (exclusion seule) | 1 193 | 0 | 35 434 |
| R3 v1 (connecteurs de liaison seuls) | 1 889 | 11 331 | 23 407 |
| **R3 v2** | 725 | **12 495** | 23 407 |

Le périmètre écarté est **identique entre v1 et v2** (23 407 : les renvois et
les formes à 3+ segments). Les deux corrections portent sur la **qualité** des
13 220 entrées récupérées, pas sur leur nombre. Le détail par chapitre est
dans le notebook (cellule « Bilan global révisé, par chapitre »).

## 25. État git

| Commit | Objet |
|---|---|
| `f508d34` | normalisateur v2, échantillon de 100, diagnostic |

Notebook : **77 cellules markdown pour 51 de code**, exécuté de bout en bout
sans erreur. Vérifications : 366 tests verts, `ruff` et `mypy` propres.
Toujours **rien dans `src/`**.

---

# Cinquième tour — normalisateur v3, zéro fautive atteint (2026-08-12)

## 26. L'amendement de fond

Mon diagnostic sur les connecteurs a été retenu et la décision 1 amendée. La
distinction qui manquait : **les connecteurs de liaison ne sont pas des
modificateurs, ce sont des marqueurs de rection**. Le volume 3 qualifie de non
essentiels les termes parenthésés *qualifiants* — ceux-là se retirent
toujours, la justification tient. Mais `(de)`, `(à)`, `(en)` indiquent comment
le terme se construit, et **le retrait détruisait une information présente
dans la source**.

Le v3 les consomme comme joint, avec contraction et élision.

## 27. D'où vient le genre, et un bénéfice inattendu

`de + le → du` suppose de connaître le genre, que la source ne donne pas. Je
l'ai tiré du **corpus** : relevé des rections attestées (`du cerveau` 73 fois,
`de la rate` 19, `de l'estomac` 79), forme majoritaire retenue.

Le même mécanisme a rendu un second service, que je n'avais pas anticipé :
**un adjectif n'est jamais précédé d'un article**. L'absence d'attestation
vaut donc signal qu'il ne faut *pas* insérer de joint — c'est ce qui évite
« rectite à l'amibienne » et « abcès de sous-dural », sans avoir à identifier
les adjectifs.

> **Piège trouvé à la mise en œuvre**, et coûteux : un motif d'attestation en
> `\s+` ne voit **jamais** les élisions, puisque « de l'estomac » ne comporte
> pas d'espace après le joint. Le lexique était silencieusement amputé de
> toute une famille de rections. Deux motifs distincts sont nécessaires.

## 28. Les trois correctifs des fautives

1. **Inversion élargie** aux seconds segments réduits à un substantif de tête
   nu, sur liste blanche courte (`syndrome`, `maladie`, `site fragile`).
2. **Exclusion** des entrées à premier segment abréviation d'index
   (`nca`, `sai`).
3. **Garde-fou sur les groupes nominaux complets** : un second segment portant
   déjà sa rection (« syndrome du choc toxique ») ne reçoit pas de joint
   externe.

L'asymétrie demandée est respectée : tout cas douteux est **écarté, jamais
normalisé**. Coût assumé, 732 entrées de moins qu'en v2.

## 29. Le seuil « zéro fautive » est atteint

Tirage `seed=777`, distinct des deux précédents. Lecture préliminaire :

| Étiquette | v1 (50) | v2 (100) | **v3 (100)** | Seuil | Verdict |
|---|---|---|---|---|---|
| `correcte` | 22 % | 57 % | **80 %** | — | — |
| `degradee` | 66 % | 40 % | **20 %** | ≤ 10 % | non atteint |
| `fautive` | 12 % | 3 % | **0** | 0 | **atteint** |

**Les 20 % de dégradées ont une cause unique** : le joint non inséré faute de
rection attestée, pour des noms rares ou techniques absents des sources hors
Index — `psoas`, `colibacille`, `béryllium`, `streptocoques`, `colostomie`,
`albumine`, `cuir chevelu`, `tuteur urinaire` — plus un reliquat `nca` en fin
d'entrée.

Deux leviers pour le tour suivant :

1. **Admettre l'Index dans le lexique de rections.** Légitime : « du psoas »
   y est fiable même si la capitalisation de l'Index ne l'est pas. **À ne pas
   confondre avec le vocabulaire de casse**, qui doit rester hors Index pour
   la raison structurelle déjà posée.
2. **Retirer les abréviations d'index en fin d'entrée**, et pas seulement en
   tête.

## 30. Contrôle de vraisemblance des joints

| Joint | du | de la | de l' | des | par | au | à l' | en | pour | avec | à la | aux |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Occurrences | 1 061 | 766 | 541 | 200 | 36 | 29 | 21 | 16 | 12 | 11 | 9 | 1 |

Répartition attendue en français médical. Un excès de `de l'` aurait signalé
une élision à l'aveugle ; un excès de `de` nu, un lexique trop pauvre.

## 31. Bilan global v3 et état git

| Politique | Conservées | Normalisées | Écartées |
|---|---|---|---|
| Détecteur 3 motifs (exclusion seule) | 5 424 | 0 | 31 203 |
| R3 v2 | 725 | 12 495 | 23 407 |
| **R3 v3** | 724 | **11 764** | 24 139 |

| Commit | Objet |
|---|---|
| `8af9fd6` | normalisateur v3, échantillon de 100, distribution des joints |

Notebook : **89 cellules markdown pour 59 de code**, exécuté sans erreur.
366 tests verts, `ruff` et `mypy` propres. Toujours **rien dans `src/`**.
