# Hors périmètre de la base de recommandations

> Passages relevés pendant l'extraction du pilote (chap. V du guide MCO
> 2026-provisoire) qui relèvent des **couches 1 et 2** du §3 de la note
> de conception, et non de la couche 3 (« consignes spécifiques à des
> codes ou situations »).
>
> **Ils sont consignés, pas jetés.** La couche 1 est destinée au
> préambule commun des prompts de génération — chantier distinct déjà
> identifié — et la couche 2 à la documentation de recode-scenario. Les
> perdre reviendrait à refaire la lecture.

Les `L…` renvoient aux fichiers de `data/guide_mco/extraits_bruts/`.

---

## Couche 1 — Grammaire CIM-10 générale

Destination : **préambule commun des prompts**, pas les fiches.

### Le principe du code le plus précis
> « La règle générale est : le meilleur code est le plus précis par
> rapport à l'information à coder. »
> — `chapitre_xxi.txt` L86-87, repris L176 et L346-347.

C'est **le** principe transversal du guide : il gouverne le choix entre
un code Z et un code de symptôme (XXI-03), entre Z42 et un code des
chapitres I à XIX (XXI-30), et l'emploi de Z03. Il n'a aucune cible de
code : le rattacher à un chapitre serait arbitraire.

### La note liminaire du chapitre XXI (alinéas a et b)
> « Il est recommandé de lire la note figurant à la première page du
> chapitre XXI du volume 1, spécialement les lignes relatives aux deux
> circonstances indiquées pour l'emploi des codes Z (alinéas a et b). »
> — `chapitre_xxi.txt` L43-45 ; les alinéas eux-mêmes sont cités
> L301-304 et L544-550.

Renvoi au volume 1 de la CIM-10. La note liminaire est déjà dans le
référentiel (`scope_notes` du chapitre XXI côté ANS) : la reverser ici
créerait un doublon avec une autre autorité.

### Le sens de « séquelle » dans la CIM-10
> « La CIM–10 définit les séquelles comme des "états pathologiques,
> stables, conséquences d'affections qui ne sont plus en phase active". »
> — `avc.txt` L89-90.

Définition générale. **Sa conséquence pour l'AVC** (priorité aux
manifestations + I69) est retenue en couche 3 sous
`GM2026-V-AVC-10` ; c'est la définition seule qui reste ici.

### Sens de mots dont l'acception CIM-10 diffère du langage courant
Cas limites : chacun est **attaché à des codes précis**, donc **retenu
en couche 3** malgré son caractère lexical —
« chimiothérapie » (XXI-12, Z08.2/Z09.2/Z51.2), « dépistage »
(XXI-14, Z11-Z13), « antécédent » (XXI-50, Z92.1/Z92.2), « acte »
(XXI-42 pour Z53 et XXI-46 pour Z75.80), « malnutrition »
(DEN-08, E40-E46).

**Noté ici pour mémoire** : si le préambule commun devait un jour porter
une rubrique « faux amis lexicaux de la CIM-10 », ces cinq entrées en
sont le noyau, et elles seraient alors **dupliquées** entre le préambule
et les fiches. Décision à prendre au chantier préambule, pas ici.

---

## Couche 2 — Règles générales PMSI, sans référence de code

Destination : **documentation de recode-scenario**, ou rien.

### Renvois à d'autres chapitres du guide
- « Les notions de DP, DR et DA ont été traitées dans le chapitre IV. »
  — `chapitre_xxi.txt` L73-74 (note 23).
- « se reporter au point 2 du chapitre IV » (définition du DR), cité
  cinq fois : L156, L241, L482, et implicitement partout où le guide
  écrit « chaque fois qu'elle respecte sa définition ».
- « se reporter au point 1.2.2.3 du chapitre VI » (traitement unique
  partagé) — `avc.txt` L155.
- « se reporter au chapitre VI situation 1.3.1 » (surveillance négative)
  — `chapitre_xxi.txt` L144-146.

Ces renvois portent la **définition du DR**, qui conditionne une bonne
douzaine de consignes retenues (« … chaque fois qu'elle respecte sa
définition »). La base porte la condition en texte libre ; elle ne porte
pas la définition. **C'est une dépendance assumée, pas un oubli.**

### Conditions de production du RUM et périmètre du recueil
> « On ne saurait en déduire des modalités de recueil de l'information
> qui ne seraient pas conformes aux conditions de production du RUM
> exposées dans le chapitre I ni aux règles de hiérarchisation des
> diagnostics qui font l'objet du chapitre IV. »
> — `chapitre_xxi.txt` L49-52.

### Qui décide, et non comment coder
> « Il n'appartient pas au médecin responsable de l'information médicale
> ni au codeur de trancher entre chirurgie esthétique et autre chirurgie
> plastique, ni de décider si une intervention est de confort ou non.
> Il s'agit d'un choix qui est d'abord de la compétence du médecin qui
> dispense les soins […]. »
> — `chapitre_xxi.txt` L358-362.

Règle d'organisation. Elle ne change aucun code ; elle dit qui tranche.

> « Il importe que le dossier médical soit en accord avec cette règle. »
> — `avc.txt` L115.

> « Il est recommandé d'intégrer les valeurs du poids et de la taille et
> de l'IMC dans le dossier médical partagé (DMP). »
> — `malnutrition_denutrition.txt` L247-248.

Recommandations de tenue de dossier. **Frontière discutable** pour la
dernière : elle est proche de `GM2026-V-DEN-04` (« nécessite que le
dossier comporte la mention de dénutrition »), que j'ai retenue en
couche 3 parce qu'elle **conditionne l'emploi des codes E40-E46**,
alors que celle-ci ne conditionne rien — elle recommande une pratique.
Si vous jugez la distinction trop fine, DEN-04 doit descendre ici avec
elle.

### Définition du champ MCO et des séances
> « Son utilisation pour le codage du DP est une condition d'un
> enregistrement juste des séances au sens du PMSI en MCO, mais l'emploi
> de la catégorie Z51 ne leur est pas réservé. »
> — `chapitre_xxi.txt` L449-453.

La partie *codage* est retenue en `GM2026-V-XXI-38` ; c'est la
définition de la séance qui reste ici.

---

## Divergences guide / CIM-10 constatées

Passages où le guide et la classification ne se recouvrent pas
exactement. **Aucune ligne de recommandation n'en est tirée** : combler
un silence du guide serait exactement l'ajout que la finalité « ne
jamais élargir ni brouiller le périmètre » interdit. On les consigne
pour que le constat survive à la session.

### E44.1 Malnutrition protéinoénergétique légère — énuméré, jamais employé

> « La CIM–10 classe les états de malnutrition dans le groupe E40–E46 :
> E40 Kwashiorkor, E41 Marasme nutritionnel ; E42 Kwashiorkor avec
> marasme ; E43 Malnutrition protéinoénergétique grave, sans précision ;
> E44.0 Malnutrition protéinoénergétique modérée ; **E44.1 Malnutrition
> protéinoénergétique légère** ; E46 Malnutrition sans précision. »
> — `malnutrition_denutrition.txt` L37-40.

Le guide énumère E44.1 dans le groupe, puis **ne lui donne jamais de
consigne**. Ses trois sections « Consigne » (L118-121, L176-179,
L237-239) ne connaissent que deux niveaux : sévère → E43, modérée →
E44.0. Les recommandations HAS sur lesquelles le guide s'appuie ne
définissent elles-mêmes que ces deux niveaux.

**Constat, pas interprétation** : le silence peut vouloir dire que
E44.1 n'a pas d'emploi en pratique, ou seulement que le guide n'a pas
traité le cas. **Le texte ne permet pas de trancher**, et rien n'a été
versé — ni consigne d'emploi, ni interdiction. À reposer à la parution
de la version définitive du guide, en même temps que le diff de
millésime.

---

## Débordements de pages — appartiennent à d'autres articles

L'extraction se fait en **pages entières** (cf. `scripts/extraire_guide_mco.sh`),
donc la dernière page d'un article déborde sur le suivant. Ces passages
ne relèvent pas du pilote et **n'ont pas été extraits** :

| Passage | Fichier | Article réel |
|---|---|---|
| L205-226 | `avc.txt` | ACCOUCHEMENT IMPROMPTU OU À DOMICILE |
| L229-247 | `avc.txt` | ANÉMIE POSTHÉMORRAGIQUE (début — couvert par son propre extrait) |
| L85-104 | `anemie_posthemorragique_d62.txt` | ANTÉCÉDENTS |
| L15-33 | `chapitre_xxi.txt` | ENFANTS NÉS SANS VIE |
| L678-695 | `chapitre_xxi.txt` | ÉTAT GRABATAIRE |
| L15-31 | `malnutrition_denutrition.txt` | LÉSIONS TRAUMATIQUES, MALADIES PROFESSIONNELLES |

> **Deux d'entre eux méritent un chantier B prioritaire.** L'article
> ANTÉCÉDENTS (« une affection constituant un antécédent personnel ne
> doit pas être codée avec les chapitres I à XIX […] doit être codé avec
> le chapitre XXI ») est **l'exemple type de `interdit_DP`/`interdit_DR`
> au niveau chapitre** que le §4.2 de la note cite. Et ÉTAT GRABATAIRE
> (R26.30) porte le cas du « et » du libellé, qui est le cas d'école de
> la couche 1.
