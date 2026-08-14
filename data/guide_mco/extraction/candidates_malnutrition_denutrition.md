# Candidates — MALNUTRITION, DÉNUTRITION

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/malnutrition_denutrition.txt`
> (guide chap. V, pp. imprimées 109-114). Les `L…` y renvoient.

**15 consignes, 21 associations**.

---

## Consignes nouvelles

### GM2026-V-DEN-01 — `regle_position`

**Situation** : Dénutrition de l'enfant (< 18 ans) — choix du code selon la sévérité

**Texte** : Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision ; une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée.

**Condition** : Patient de moins de 18 ans ; diagnostic de dénutrition posé (au moins 1 critère phénotypique ET 1 critère étiologique)

**Citation** (`malnutrition_denutrition.txt` L118-121) :
« 1.3 Consigne — Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision, une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `regi` | sujet | dénutrition sévère |
| `E44.0` | `regi` | sujet | dénutrition modérée |

### GM2026-V-DEN-02 — `regle_position`

**Situation** : Dénutrition de l'adulte (≥ 18 et < 70 ans) — choix du code selon la sévérité

**Texte** : Une dénutrition sévère se code E43 ; une dénutrition modérée se code E44.0.

**Condition** : Patient de 18 à moins de 70 ans ; diagnostic de dénutrition posé

**Citation** (`malnutrition_denutrition.txt` L176-179) :
« 2.3 Consigne — Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision, une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `regi` | sujet | dénutrition sévère |
| `E44.0` | `regi` | sujet | dénutrition modérée |

### GM2026-V-DEN-03 — `regle_position`

**Situation** : Dénutrition de la personne âgée (≥ 70 ans) — choix du code selon la sévérité

**Texte** : Une dénutrition sévère se code E43 ; une dénutrition modérée se code E44.0.

**Condition** : Patient de 70 ans et plus ; diagnostic de dénutrition posé

**Citation** (`malnutrition_denutrition.txt` L237-239) :
« 3.3. Consigne — Une dénutrition sévère se code E43 Malnutrition protéino-énergétique grave, sans précision, une dénutrition modérée se code E44.0 Malnutrition protéino-énergétique modérée. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `regi` | sujet | dénutrition sévère |
| `E44.0` | `regi` | sujet | dénutrition modérée |

### GM2026-V-DEN-04 — `condition_emploi`

**Situation** : Emploi des codes E40 à E46 — exigence documentaire

**Texte** : L'emploi des codes E40 à E46 doit se fonder sur les critères HAS et nécessite que le dossier comporte la mention de dénutrition. Cette mention peut être indiquée par un clinicien ou par un diététicien.

**Condition** : Mention de dénutrition présente au dossier

**Citation** (`malnutrition_denutrition.txt` L244-246) :
« L'emploi des codes E40 à E46 doit se fonder sur ces critères et nécessite que le dossier comporte la mention de dénutrition. Cette mention peut être indiquée par un clinicien ou par un diététicien. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E40-E46` | `regi` | sujet |  |

### GM2026-V-DEN-05 — `condition_emploi`

**Situation** : Emploi des codes E40, E41 et E42 en France

**Texte** : L'emploi des catégories E40 Kwashiorkor, E41 Marasme nutritionnel et E42 Kwashiorkor avec marasme ne peut être qu'exceptionnel en France.

**Condition** : —

**Citation** (`malnutrition_denutrition.txt` L64-65 (note 57) et L272-273 (note 62)) :
« Les codes E40, E41 et E42 ne peuvent connaître qu'un emploi exceptionnel en France. — Pour mémoire l'emploi des catégories E40, E41 et E42 ne peut être qu'exceptionnel en France. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E40-E42` | `regi` | sujet |  |

### GM2026-V-DEN-06 — `condition_emploi`

**Situation** : Détermination du niveau de sévérité

**Texte** : Le code est déterminé en fonction des critères correspondant aux définitions HAS retrouvés au dossier, sans que le niveau de sévérité doive nécessairement être mentionné dans le dossier — bien qu'il soit recommandé qu'il le soit.

**Condition** : —

**Citation** (`malnutrition_denutrition.txt` L250-253) :
« Le code CIM10 est déterminé en fonction des critères correspondant aux définitions publiées par la HAS et retrouvés au dossier, sans que le niveau de sévérité ne doive nécessairement être mentionné dans le dossier. Il est toutefois recommandé que ce niveau soit explicitement mentionné. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `regi` | sujet |  |
| `E44.0` | `regi` | sujet |  |

### GM2026-V-DEN-07 — `regle_association`

**Situation** : Coexistence de critères de sévérité différents (adulte 18-70 ans)

**Texte** : Lors de l'observation simultanée d'un seul critère de dénutrition sévère et d'un ou plusieurs critères de dénutrition modérée, il est recommandé de poser un diagnostic de dénutrition sévère.

**Condition** : Coexistence d'un critère sévère et de critères modérés ; portée limitée à la section « adulte ≥ 18 et < 70 ans » du guide (non généralisée aux trois tranches d'âge, décision RF 2026-08-14)

**Citation** (`malnutrition_denutrition.txt` L172-174) :
« Lors de l'observation simultanée d'un seul critère de dénutrition sévère et d'un ou plusieurs critères de dénutrition modérée, il est recommandé de poser un diagnostic de dénutrition sévère. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `regi` | sujet | le sévère prime |
| `E44.0` | `interdit` | sujet | écarté au profit de E43 |

### GM2026-V-DEN-08 — `definition`

**Situation** : Périmètre du terme « malnutrition » dans la CIM-10

**Texte** : La CIM–10 range sous le terme générique de malnutrition un groupe d'affections résultant d'une carence d'apport ou d'une désassimilation protéinoénergétique : on doit donc l'entendre au sens restreint de dénutrition. Le groupe est E40–E46, auquel s'ajoute O25 Malnutrition au cours de la grossesse.

**Condition** : —

**Citation** (`malnutrition_denutrition.txt` L40-43, L66-67 (note 58), L68-70 (note 59)) :
« Elle range sous le terme générique de malnutrition un groupe d'affections résultant d'une carence d'apport ou d'une désassimilation protéinoénergétique : on doit donc l'entendre dans le sens restreint de dénutrition. — Auxquels s'ajoute O25 Malnutrition au cours de la grossesse. — Cet anglicisme désigne de fait tout trouble lié à un déséquilibre alimentaire, aussi bien en défaut qu'en excès. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E40-E46` | `regi` | sujet |  |
| `O25` | `regi` | sujet | pendant la grossesse |

### GM2026-V-DEN-10 — `definition`

**Situation** : Critères de dénutrition modérée chez l'enfant (< 18 ans)

**Texte** : Dénutrition modérée avant 18 ans : courbe IOTF 17 < IMC < courbe IOTF 18,5 ; perte de poids ≥ 5 % et ≤ 10 % en 1 mois ou ≥ 10 % et ≤ 15 % en 6 mois par rapport au poids habituel avant le début de la maladie ; stagnation pondérale aboutissant à un poids situé entre 2 et 3 couloirs en dessous du couloir habituel. Un seul critère suffit dès lors que la dénutrition est présente.

**Condition** : Patient de moins de 18 ans ; dénutrition déjà établie

**Citation** (`malnutrition_denutrition.txt` L91-101) :
« 1.1 Les critères de dénutrition modérée chez les patients âgés de moins de 18 ans — courbe IOTF 17 < IMC < courbe IOTF 18,5 ; perte de poids ≥ 5 % et ≤ 10 % en 1 mois ou ≥ 10 % et ≤ 15 % en 6 mois par rapport au poids habituel avant le début de la maladie ; stagnation pondérale aboutissant à un poids situé entre 2 et 3 couloirs en dessous du couloir habituel. L'observation d'un seul critère de dénutrition modérée suffit pour poser le diagnostic de dénutrition modérée dès lors que la dénutrition est présente. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E44.0` | `regi` | sujet |  |

### GM2026-V-DEN-11 — `definition`

**Situation** : Critères de dénutrition sévère chez l'enfant (< 18 ans)

**Texte** : Dénutrition sévère avant 18 ans : IMC ≤ courbe IOTF 17 ; perte de poids > 10 % en 1 mois ou > 15 % en 6 mois ; stagnation pondérale aboutissant à un poids situé au moins 3 couloirs en dessous du couloir habituel ; infléchissement statural avec perte d'au moins un couloir. Un seul critère suffit dès lors que la dénutrition est présente.

**Condition** : Patient de moins de 18 ans ; dénutrition déjà établie

**Citation** (`malnutrition_denutrition.txt` L104-115) :
« 1.2 Les critères de dénutrition sévère chez les patients âgés de moins de 18 ans — IMC ≤ courbe IOTF 17 ; perte de poids > 10 % en 1 mois ou > 15 % en 6 mois par rapport au poids habituel avant le début de la maladie ; stagnation pondérale aboutissant à un poids situé au moins 3 couloirs (représentant 3 écart-types) en dessous du couloir habituel ; infléchissement statural (avec perte d'au moins un couloir par rapport à la taille habituelle). L'observation d'un seul critère de dénutrition sévère suffit à qualifier la dénutrition de sévère dès lors que la dénutrition est présente. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `regi` | sujet |  |

### GM2026-V-DEN-12 — `definition`

**Situation** : Critères de dénutrition modérée chez l'adulte (≥ 18 et < 70 ans)

**Texte** : Dénutrition modérée de 18 à 70 ans : 17 < IMC < 18,5 kg/m² ; perte de poids ≥ 5 % en 1 mois ou ≥ 10 % en 6 mois ou ≥ 10 % par rapport au poids habituel ; albuminémie > 30 g/L et < 35 g/L, quel que soit l'état inflammatoire. Un seul critère suffit dès lors que la dénutrition est présente.

**Condition** : Patient de 18 à moins de 70 ans ; dénutrition déjà établie

**Citation** (`malnutrition_denutrition.txt` L146-156) :
« 2.1 Les critères de dénutrition modérée chez l'adulte (≥ 18 ans et < 70 ans) — 17 < IMC < 18,5 kg/m2 ; perte de poids ≥ 5 % en 1 mois ou ≥ 10 % en 6 mois ou ≥ 10 % par rapport au poids habituel avant le début de la maladie ; mesure de l'albuminémie par immunonéphélémétrie ou immunoturbidimétrie >30 g/L et < 35 g/L. Les seuils d'albuminémie sont à prendre en compte quel que soit l'état inflammatoire. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E44.0` | `regi` | sujet |  |

### GM2026-V-DEN-13 — `definition`

**Situation** : Critères de dénutrition sévère chez l'adulte (≥ 18 et < 70 ans)

**Texte** : Dénutrition sévère de 18 à 70 ans : IMC ≤ 17 kg/m² ; perte de poids ≥ 10 % en 1 mois ou ≥ 15 % en 6 mois ou ≥ 15 % par rapport au poids habituel ; albuminémie ≤ 30 g/L, quel que soit l'état inflammatoire. Un seul critère suffit dès lors que la dénutrition est présente.

**Condition** : Patient de 18 à moins de 70 ans ; dénutrition déjà établie

**Citation** (`malnutrition_denutrition.txt` L159-170) :
« 2.2 Les critères de dénutrition sévère chez l'adulte (≥ 18 ans et < 70 ans) — IMC ≤ 17 kg/m2 ; perte de poids ≥ 10 % en 1 mois ou ≥ 15 % en 6 mois ou ≥ 15 % par rapport au poids habituel avant le début de la maladie ; mesure de l'albuminémie par immunonéphélémétrie ou immunoturbidimétrie ≤ 30g/L. Les seuils d'albuminémie sont à prendre en compte quel que soit l'état inflammatoire. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `regi` | sujet |  |

### GM2026-V-DEN-14 — `definition`

**Situation** : Critères de dénutrition modérée chez la personne âgée (≥ 70 ans)

**Texte** : Dénutrition modérée à partir de 70 ans : 20 ≤ IMC < 22 ; perte de poids ≥ 5 % et < 10 % en 1 mois ou ≥ 10 % et < 15 % en 6 mois ou ≥ 10 % et < 15 % par rapport au poids habituel ; albuminémie > 30 g/L. Un seul critère suffit dès lors que la dénutrition est présente.

**Condition** : Patient de 70 ans et plus ; dénutrition déjà établie

**Citation** (`malnutrition_denutrition.txt` L209-217) :
« 3.1 Les critères de dénutrition modérée chez les patients âgés de 70 ans et plus — 20 ≤ IMC < 22 ; perte de poids ≥ 5 % et < 10 % en 1 mois ou ≥ 10 % et < 15 % en 6 mois ou ≥ 10 % et < 15 % par rapport au poids habituel avant le début de la maladie ; mesure de l'albuminémie par immunonéphélémétrie ou immunoturbidimétrie > 30 g/L. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E44.0` | `regi` | sujet |  |

### GM2026-V-DEN-15 — `definition`

**Situation** : Critères de dénutrition sévère chez la personne âgée (≥ 70 ans)

**Texte** : Dénutrition sévère à partir de 70 ans : IMC < 20 kg/m² ; perte de poids ≥ 10 % en 1 mois ou ≥ 15 % en 6 mois ou ≥ 15 % par rapport au poids habituel ; albuminémie ≤ 30 g/L. Un seul critère suffit dès lors que la dénutrition est présente.

**Condition** : Patient de 70 ans et plus ; dénutrition déjà établie

**Citation** (`malnutrition_denutrition.txt` L228-236) :
« 3.2. Les critères de dénutrition sévère chez les patients âgés de 70 ans et plus — IMC < 20 kg/m2 ; Perte de poids ≥ 10 % en 1 mois ou ≥ 15 % en 6 mois ou ≥ 15 % par rapport au poids habituel avant le début de la maladie ; mesure de l'albuminémie par immunonéphélémétrie ou immunoturbidimétrie ≤ 30 g/L. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E43` | `regi` | sujet |  |

### GM2026-V-DEN-16 — `definition`

**Situation** : Diagnostic de dénutrition — critères phénotypiques et étiologiques requis

**Texte** : Le diagnostic de dénutrition nécessite au moins 1 critère phénotypique ET 1 critère étiologique ; il est un préalable obligatoire avant de juger de la sévérité et repose exclusivement sur des critères non biologiques. Les critères étiologiques sont identiques aux trois âges : réduction de la prise alimentaire ≥ 50 % pendant plus d'1 semaine (ou toute réduction pendant plus de 2 semaines) ; absorption réduite (malabsorption, maldigestion) ; situation d'agression (pathologie aiguë, chronique évolutive ou maligne évolutive). Les critères phénotypiques varient avec l'âge — perte de poids, IMC (seuils IOTF avant 18 ans, 18,5 kg/m² de 18 à 70 ans, 22 kg/m² au-delà), réduction de la masse ou de la fonction musculaires, sarcopénie confirmée après 70 ans.

**Condition** : —

**Citation** (`malnutrition_denutrition.txt` L49-52, L57-89, L126-143, L187-205) :
« Pour les patients de moins de 70 ans, le diagnostic de la dénutrition nécessite la présence d'au moins 1 critère phénotypique et 1 critère étiologique. Ce diagnostic est un préalable obligatoire avant de juger de sa sévérité. Il repose exclusivement sur des critères non biologiques. — Les critères étiologiques sont les suivants : réduction de la prise alimentaire ≥ 50 % pendant plus d'1 semaine, ou toute réduction des apports pendant plus de 2 semaines […] ; absorption réduite (malabsorption/maldigestion) ; situation d'agression (hypercatabolisme protéique avec ou sans syndrome inflammatoire) : pathologie aiguë ou pathologie chronique évolutive ou pathologie maligne évolutive. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `E40-E46` | `regi` | sujet |  |

