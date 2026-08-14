# Candidates — MALNUTRITION, DÉNUTRITION

> **Statut : à valider ligne à ligne. Rien ici n'est dans les tables curées.**
>
> Source : `data/guide_mco/extraits/malnutrition_denutrition.txt`
> (chap. V, pp. imprimées 109-114). Les `L…` renvoient à ce fichier.

L'article a une structure très régulière : trois tranches d'âge
(< 18 ans, 18–70 ans, ≥ 70 ans), chacune avec ses critères
phénotypiques et étiologiques, ses seuils de sévérité, et **la même
consigne de codage répétée trois fois**.

J'ai choisi de **ne pas fusionner les trois consignes de codage**, alors
que leur texte est identique : leurs *conditions* diffèrent (les
critères ne sont pas les mêmes selon l'âge), et fusionner obligerait à
mettre les trois jeux de critères dans une seule condition en texte
libre. Trois lignes, trois conditions — dites-moi si vous préférez une
seule.

---

## §A — Consignes de codage par tranche d'âge

### GM2026-V-DEN-01 — `regle_position`
**Situation** : Dénutrition de l'enfant (< 18 ans) — choix du code selon la sévérité
**Texte** : Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision ; une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée.
**Condition** : Patient de moins de 18 ans ; diagnostic de dénutrition posé (au moins 1 critère phénotypique ET 1 critère étiologique)
**Citation** (L118-121) : « 1.3 Consigne — Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision, une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `contexte` | `sujet` | dénutrition sévère |
| `E44.0` | `contexte` | `sujet` | dénutrition modérée |

### GM2026-V-DEN-02 — `regle_position`
**Situation** : Dénutrition de l'adulte (≥ 18 et < 70 ans) — choix du code selon la sévérité
**Texte** : Une dénutrition sévère se code E43 ; une dénutrition modérée se code E44.0.
**Condition** : Patient de 18 à moins de 70 ans ; diagnostic de dénutrition posé
**Citation** (L176-179) : « 2.3 Consigne — Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision, une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `contexte` | `sujet` | dénutrition sévère |
| `E44.0` | `contexte` | `sujet` | dénutrition modérée |

### GM2026-V-DEN-03 — `regle_position`
**Situation** : Dénutrition de la personne âgée (≥ 70 ans) — choix du code selon la sévérité
**Texte** : Une dénutrition sévère se code E43 ; une dénutrition modérée se code E44.0.
**Condition** : Patient de 70 ans et plus ; diagnostic de dénutrition posé
**Citation** (L237-239) : « 3.3. Consigne — Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision, une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `contexte` | `sujet` | dénutrition sévère |
| `E44.0` | `contexte` | `sujet` | dénutrition modérée |

---

## §B — Consignes générales d'emploi

### GM2026-V-DEN-04 — `condition_emploi`
**Situation** : Emploi des codes E40 à E46 — exigence documentaire
**Texte** : L'emploi des codes E40 à E46 doit se fonder sur les critères HAS et nécessite que le dossier comporte la mention de dénutrition. Cette mention peut être indiquée par un clinicien ou par un diététicien.
**Condition** : Mention de dénutrition présente au dossier
**Citation** (L244-246) : « L'emploi des codes E40 à E46 doit se fonder sur ces critères et nécessite que le dossier comporte la mention de dénutrition. Cette mention peut être indiquée par un clinicien ou par un diététicien. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E40-E46` | `contexte` | `sujet` | |

> **Consigne de forte valeur pour la génération** : elle dit que le CRH
> doit porter le mot « dénutrition », pas seulement des chiffres.

### GM2026-V-DEN-05 — `condition_emploi`
**Situation** : Emploi des codes E40, E41, E42 en France
**Texte** : L'emploi des catégories E40 Kwashiorkor, E41 Marasme nutritionnel et E42 Kwashiorkor avec marasme ne peut être qu'exceptionnel en France.
**Condition** : —
**Citation** (L64-65, note 57) : « Les codes E40, E41 et E42 ne peuvent connaître qu'un emploi exceptionnel en France. » — repris (L272-273, note 62) : « Pour mémoire l'emploi des catégories E40, E41 et E42 ne peut être qu'exceptionnel en France. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E40-E42` | `contexte` | `sujet` | |

> **Très utile en génération** : sans elle, rien n'empêche un générateur
> de produire des kwashiorkors à la chaîne. C'est le pendant nutritionnel
> du problème ORPHANET (biais de fréquence) déjà rencontré au chantier
> `chapter_policy`.

### GM2026-V-DEN-06 — `condition_emploi`
**Situation** : Détermination du niveau de sévérité
**Texte** : Le code est déterminé en fonction des critères correspondant aux définitions HAS retrouvés au dossier, sans que le niveau de sévérité doive nécessairement être mentionné dans le dossier — bien qu'il soit recommandé qu'il le soit.
**Condition** : —
**Citation** (L250-253) : « Le code CIM10 est déterminé en fonction des critères correspondant aux définitions publiées par la HAS et retrouvés au dossier, sans que le niveau de sévérité ne doive nécessairement être mentionné dans le dossier. Il est toutefois recommandé que ce niveau soit explicitement mentionné. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `contexte` | `sujet` | |
| `E44.0` | `contexte` | `sujet` | |

### GM2026-V-DEN-07 — `regle_association`
**Situation** : Coexistence de critères de sévérité différents
**Texte** : Lors de l'observation simultanée d'un seul critère de dénutrition sévère et d'un ou plusieurs critères de dénutrition modérée, il est recommandé de poser un diagnostic de dénutrition sévère.
**Condition** : Coexistence d'un critère sévère et de critères modérés
**Citation** (L172-174) : « Lors de l'observation simultanée d'un seul critère de dénutrition sévère et d'un ou plusieurs critères de dénutrition modérée, il est recommandé de poser un diagnostic de dénutrition sévère. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `contexte` | `sujet` | le sévère prime |
| `E44.0` | `interdit` | `sujet` | écarté au profit de E43 |

> **Point à trancher.** Le texte du guide place cette phrase dans la
> section « adulte 18–70 ans » uniquement (L172-174), alors qu'elle
> énonce un principe qui vaudrait manifestement pour les trois tranches.
> **Je ne l'ai pas généralisée** : ce serait ajouter une portée que le
> texte ne donne pas. Si vous jugez qu'elle est générale, il faut le
> décider explicitement et le noter dans `localisation`.

### GM2026-V-DEN-08 — `definition`
**Situation** : Périmètre du terme « malnutrition » dans la CIM-10
**Texte** : La CIM–10 range sous le terme générique de malnutrition un groupe d'affections résultant d'une carence d'apport ou d'une désassimilation protéinoénergétique : on doit donc l'entendre au sens restreint de **dénutrition**. Le groupe est E40–E46, auquel s'ajoute O25 Malnutrition au cours de la grossesse.
**Condition** : —
**Citation** (L40-43) : « Elle range sous le terme générique de malnutrition un groupe d'affections résultant d'une carence d'apport ou d'une désassimilation protéinoénergétique : on doit donc l'entendre dans le sens restreint de dénutrition. » — et (L66-67, note 58) : « Auxquels s'ajoute O25 Malnutrition au cours de la grossesse. » — et (L68-70, note 59) : « Cet anglicisme désigne de fait tout trouble lié à un déséquilibre alimentaire, aussi bien en défaut qu'en excès. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E40-E46` | `contexte` | `sujet` | |
| `O25` | `contexte` | `sujet` | pendant la grossesse |

---

## §C — Une divergence entre le guide et la CIM-10, à arbitrer

**Le guide énumère `E44.1 Malnutrition protéinoénergétique légère`
(L39-40) mais ne lui donne jamais de consigne de codage.** Les trois
sections « Consigne » ne connaissent que deux niveaux — sévère (E43) et
modérée (E44.0). La HAS elle-même ne définit que ces deux niveaux.

Je **n'ai créé aucune consigne pour E44.1** : le guide n'en donne pas,
et en inventer une serait exactement le genre d'ajout que la finalité
« ne jamais élargir ni brouiller le périmètre » interdit. Mais le
silence est peut-être signifiant : si E44.1 n'a pas de critère, faut-il
une consigne disant qu'il n'a pas d'emploi en pratique ? **Le texte ne
le dit pas** — je ne le tranche pas.

---

## §D — Les critères diagnostiques : à admettre ou non ?

L'article consacre l'essentiel de ses six pages aux **critères
diagnostiques** (IMC, perte de poids, albuminémie, sarcopénie, réduction
des apports). Ce sont des définitions cliniques, pas des consignes de
position.

**Je ne les ai pas versées en candidates**, et je m'arrête pour vous
demander. L'argument dans les deux sens :

- **Pour** : ce sont exactement les faits qu'un CRH doit contenir pour
  qu'un E43 soit justifié. Sans eux, la fiche E43 enseigne le code mais
  pas ce qui l'atteste, et un générateur produira des dénutritions sans
  chiffres. Même raisonnement que pour `GM2026-V-D62-03`.
- **Contre** : la base est conçue comme une base de *consignes de
  codage*. Y verser des seuils biologiques change sa nature, et le
  volume est important (six jeux : 3 tranches d'âge × 2 sévérités, plus
  les critères étiologiques communs).

Si vous les voulez, je propose **six `definition`** —
`GM2026-V-DEN-10` à `GM2026-V-DEN-15` — une par (tranche d'âge,
sévérité), citations L91-97, L104-112, L146-153, L159-165, L209-214,
L228-233, plus une septième pour les critères étiologiques communs
(L80-89). **Cette décision doit être prise en même temps que celle sur
`GM2026-V-D62-03`** : c'est la même question.

---

## Rien à signaler côté enums

Les huit rôles et les cinq types ont suffi pour cet article. Le rôle
`contexte` y est très employé, ce qui rejoint la remarque du fichier
AVC : beaucoup de consignes régissent un code sans lui assigner de
position.
