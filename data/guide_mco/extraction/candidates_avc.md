# Candidates — ACCIDENTS VASCULAIRES CÉRÉBRAUX

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits_bruts/avc.txt`
> (guide chap. V, pp. imprimées 78-81). Les `L…` y renvoient.

**14 consignes, 31 associations** (+ 3 associations manquantes de consignes déjà versées).

---

## Associations manquantes de consignes déjà versées

Ces consignes sont dans `recommendations_curated.csv` mais sans
aucune association : le §5 de la note n'en donnait pas. Elles
ressortent au rapport de build sous
`guide_mco_recommandations_sans_code.csv`.

### GM2026-V-AVC-02

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I60-I63` | `interdit_association` | sujet | chaque | un code plus précis existe |
| `I64` | `regi` | sujet | chaque |  |

### GM2026-V-AVC-04

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I60-I64` | `DP` | sujet | chaque | récidive confirmée par l'imagerie |

---

## Consignes nouvelles

### GM2026-V-AVC-07 — `regle_association`

**Situation** : AVC — association d'un AIT et d'un AVC constitué

**Texte** : Un code d'AIT (G45.–) et un code d'AVC constitué (I60–I64) ne peuvent être associés que s'il s'agit de deux épisodes distincts au cours du même séjour.

**Condition** : Deux épisodes distincts au cours du même séjour

**Citation** (`avc.txt` L123-124) :
« Un code d’AIT (G45.–) et un code d’AVC constitué (I60–I64) ne peuvent être associés que s’il s’agit de deux épisodes distincts au cours du même séjour. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `G45` | `interdit_association` | sujet | chaque | sauf deux épisodes distincts |
| `I60-I64` | `interdit_association` | sujet | chaque | sauf deux épisodes distincts |

### GM2026-V-AVC-08 — `regle_position`

**Situation** : AVC à la phase aigüe — manifestations cliniques

**Texte** : Les manifestations cliniques de l'AVC sont codées comme diagnostics associés significatifs si elles en respectent la définition, le plus précisément possible et en employant les extensions ATIH prévues (hémiplégie G81.0–, aphasie et dysphasie R47.0–).

**Condition** : Respect de la définition du DAS

**Citation** (`avc.txt` L126-129) :
« Les manifestations cliniques de l’AVC sont codées comme diagnostics associés significatifs (DAS) si elles en respectent la définition. Il importe de les coder le plus précisément possible et d’employer les extensions prévues pour certains codes (hémiplégie, dysphasie et aphasie : se reporter au point 2 supra). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `G81` | `DAS` | sujet | chaque |  |
| `I60-I64` | `contexte` | sujet | chaque |  |
| `R47` | `DAS` | sujet | chaque |  |

### GM2026-V-AVC-09 — `interdiction`

**Situation** : AVC — syndromes des artères cérébrales G46.0 à G46.2

**Texte** : G46.0, G46.1 et G46.2 sont réservés aux syndromes neurologiques résultant d'une insuffisance circulatoire sans infarctus : ils ne peuvent pas être associés à un code d'infarctus cérébral. Cette association reste possible pour G46.3 à G46.8.

**Condition** : —

**Citation** (`avc.txt` L76-81) :
« la CIM–10 réserve les codes G46.0 à G46.2 […] à l’enregistrement de syndromes neurologiques résultant d’une insuffisance circulatoire sans infarctus […]. Ainsi, G46.0, G46.1 et G46.2 ne peuvent pas être associés à un code d’infarctus cérébral, alors que cette association est possible pour les codes G46.3 à G46.8. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `G46.0-G46.2` | `interdit_association` | sujet | chaque |  |
| `G46.3-G46.8` | `regi` | sujet | chaque | association autorisée |
| `I63` | `contexte` | sujet | chaque |  |

### GM2026-V-AVC-10 — `regle_position`

**Situation** : AVC — codage des séquelles

**Texte** : Le codage des séquelles donne la priorité aux manifestations cliniques observées, auxquelles on associe un code de la catégorie I69 Séquelles de maladies cérébrovasculaires.

**Condition** : —

**Citation** (`avc.txt` L89-92) :
« Leur codage donne la priorité aux manifestations cliniques observées, auxquelles on associe un code de la catégorie I69 Séquelles de maladies cérébrovasculaires. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I69` | `regi` | sujet | chaque | associé à la manifestation |

### GM2026-V-AVC-11 — `condition_emploi`

**Situation** : AVC — antécédent sans séquelle

**Texte** : Z86.70 exclut par construction la notion de séquelle ; il doit être employé dès que l'AVC est considéré comme ancien et qu'il ne persiste aucune séquelle fonctionnelle.

**Condition** : AVC ancien, aucune séquelle fonctionnelle persistante

**Citation** (`avc.txt` L94-97) :
« Par construction de la CIM–10, la notion d’antécédent d’AVC, codée Z86.70, exclut celle de séquelle. Le code Z86.70 Antécédents personnels de maladies cérébrovasculaires doit être employé dès que l’AVC est considéré comme ancien et qu’il ne persiste aucune séquelle fonctionnelle. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I69` | `interdit_association` | sujet | chaque | incompatible avec l'antécédent |
| `Z86.70` | `regi` | sujet | chaque |  |

### GM2026-V-AVC-12 — `regle_position`

**Situation** : AVC — séjour pour poursuite des soins dans une autre unité ou un autre établissement

**Texte** : En cas de transfert dans un autre établissement de MCO, l'AVC peut être codé comme DP dans l'établissement d'accueil dès lors qu'il continue d'être le sujet des soins.

**Condition** : L'AVC continue d'être le sujet des soins

**Citation** (`avc.txt` L152-155) :
« en cas de transfert dans un autre établissement de MCO après sortie d’unité neurovasculaire, l’AVC peut être codé comme DP dans l’autre établissement dès lors qu’il continue d’être le sujet des soins (situation clinique de traitement unique partagé […]). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I60-I64` | `DP` | sujet | chaque |  |

### GM2026-V-AVC-13 — `regle_position`

**Situation** : AVC — séjour pour aggravation ou complication (séjour distinct de la prise en charge initiale)

**Texte** : La manifestation ou la complication prise en charge est codée comme DP ; un code de séquelle d'AVC (I69) est placé en DAS.

**Condition** : Séjour distinct de celui de la prise en charge initiale

**Citation** (`avc.txt` L157-166) :
« La manifestation ou la complication prise en charge est codée comme DP. Les exemples les plus fréquents sont les troubles de la marche ou l’aggravation de la spasticité (catégorie R26 […]), le syndrome dépressif (catégorie F32 […]), l’épilepsie (catégories G40 […] et G41 […]), la démence vasculaire (catégorie F01 […]). Un code de séquelle d’AVC (I69) est placé en DAS. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `F01` | `DP` | **exemple** | chaque |  |
| `F32` | `DP` | **exemple** | chaque |  |
| `G40` | `DP` | **exemple** | chaque |  |
| `G41` | `DP` | **exemple** | chaque |  |
| `I69` | `DAS` | sujet | chaque |  |
| `R26` | `DP` | **exemple** | chaque |  |

### GM2026-V-AVC-14 — `regle_position`

**Situation** : AVC — surveillance au long cours avec séquelles, sans affection nouvelle

**Texte** : S'il n'est pas découvert d'affection nouvelle, le DP appartient au chapitre XXI ; un code de séquelle d'AVC (I69) est placé en DR et les manifestations séquellaires éventuelles sont codées comme DAS.

**Condition** : Aucune affection nouvelle découverte ; séquelles présentes

**Citation** (`avc.txt` L176-180) :
« S’il n’est pas découvert d’affection nouvelle le code du DP appartient au chapitre XXI de la CIM-10 […]. Un code de séquelle d’AVC (I69) est placé en DR et les manifestations séquellaires éventuelles sont codées comme DAS si elles en respectent la définition. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I69` | `DR` | sujet | chaque |  |
| `XXI` | `DP` | sujet | chaque |  |

### GM2026-V-AVC-15 — `regle_position`

**Situation** : AVC — surveillance dite positive (affection nouvelle liée à l'AVC)

**Texte** : Si une affection nouvelle liée à l'AVC — complication de celui-ci ou de son traitement — est découverte, cette affection est le DP ; les manifestations séquellaires respectant la définition d'un DAS, complétées par un code de séquelle I69.–, sont enregistrées en position de diagnostics associés.

**Condition** : Découverte d'une affection nouvelle liée à l'AVC

**Citation** (`avc.txt` L185-189) :
« Si une affection nouvelle liée à l’AVC, c’est-à-dire une complication de celui-ci ou de son traitement, est découverte (surveillance dite positive), cette affection est le DP. Les éventuelles manifestations séquellaires respectant la définition d’un DAS, complétées par un code de séquelle I69.–, sont enregistrées en position de diagnostics associés. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I69.–` | `DAS` | sujet | chaque |  |

### GM2026-V-AVC-16 — `regle_position`

**Situation** : AVC — séjour pour répit de la famille ou des aidants

**Texte** : Le DP est codé Z74.2 Besoin d'assistance à domicile ou Z75.5 Prise en charge pendant les vacances ; un code de séquelle de maladie cérébrovasculaire (I69.–) est saisi en position de DAS.

**Condition** : —

**Citation** (`avc.txt` L199-202) :
« Séjour pour répit de la famille ou des aidants : le DP est codé Z74.2 […] ou Z75.5 Prise en charge pendant les vacances. Un code de séquelle de maladie cérébrovasculaire (I69.–) est saisi en position de DAS. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I69.–` | `DAS` | sujet | chaque |  |
| `Z74.2` | `DP` | sujet | chaque |  |
| `Z75.5` | `DP` | sujet | chaque |  |

### GM2026-V-AVC-17 — `condition_emploi`

**Situation** : AVC — codage de l'étiologie

**Texte** : L'étiologie ne peut être codée comme diagnostic associé que si elle en respecte la définition. Les étiologies sont classées dans des rubriques diverses de la CIM–10.

**Condition** : Respect de la définition du diagnostic associé

**Citation** (`avc.txt` L143-144 et L85-87) :
« L’étiologie ne peut être codée comme diagnostic associé que si elle en respecte la définition. — Les étiologies des AVC sont classées dans des rubriques diverses de la CIM–10 ; par exemple la fibrillation auriculaire (I48), les malformations congénitales vasculaires cérébrales (Q28.–), l’athérosclérose cérébrale (I67.2), l’encéphalopathie hypertensive (I67.4), etc. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I48` | `DAS` | **exemple** | chaque |  |
| `I67.2` | `DAS` | **exemple** | chaque |  |
| `I67.4` | `DAS` | **exemple** | chaque |  |
| `Q28.–` | `DAS` | **exemple** | chaque |  |

### GM2026-V-AVC-18 — `condition_emploi`

**Situation** : AVC — codage des complications

**Texte** : Les complications sont codées comme DAS si elles en respectent la définition (par exemple inhalation, épilepsie, escarre, démence vasculaire).

**Condition** : Respect de la définition du DAS

**Citation** (`avc.txt` L146-147) :
« Les complications sont codées comme DAS si elles en respectent la définition, par exemple, inhalation, épilepsie, escarre, démence vasculaire… »

*Aucune association.* Le guide ne nomme ici aucun code : en attribuer supposerait de **choisir** des cibles que le texte ne donne pas.

### GM2026-V-AVC-19 — `definition`

**Situation** : AVC constitué à la phase aigüe — périmètre des catégories

**Texte** : Le codage des AVC constitués fait appel, à la phase aigüe, aux catégories I60 à I63, qui excluent les lésions traumatiques. I60 inclut la rupture d'anévrisme d'artère cérébrale ; I62 inclut l'hémorragie sous-durale et extradurale ; I63 couvre les AVC ischémiques (embolie, thrombose, bas débit).

**Condition** : —

**Citation** (`avc.txt` L28-39) :
« Le codage des AVC constitués fait appel, à la phase aigüe, aux catégories I60 à I63 qui excluent les lésions traumatiques. […] I60 Hémorragie sous-arachnoïdienne ; cette catégorie inclut la rupture d’anévrisme d’artère cérébrale ; […] I62 […] cette catégorie inclut l’hémorragie sous-durale et extradurale. Les AVC par infarctus cérébral ou AVC ischémiques — embolie, thrombose, bas débit — sont codés avec la catégorie I63 Infarctus cérébral. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I60-I63` | `regi` | sujet | chaque |  |

### GM2026-V-AVC-20 — `definition`

**Situation** : AVC — extensions ATIH des manifestations (hémiplégie, aphasie)

**Texte** : G81.0 et R47.0 ont été subdivisés par l'ATIH en 2007 pour distinguer les symptômes selon leur moment d'apparition et leur évolution : G81.00, G81.01, G81.08 ; R47.00, R47.01, R47.02, R47.03. Les mêmes codes servent pour les parésies et les paralysies.

**Condition** : —

**Citation** (`avc.txt` L50-62) :
« À l’initiative de la Société française neurovasculaire, ces deux catégories ont fait l’objet d’extensions par l’ATIH en 2007 afin de distinguer les symptômes selon leur moment d’apparition et leur évolution : G81.0 Hémiplégie flasque est subdivisé en : G81.00 […], G81.01 […] et G81.08 […] ; on emploie les mêmes codes pour les parésies et les paralysies […] ; R47.0 Dysphasie et aphasie est subdivisé en : R47.00 […], R47.01 […], R47.02 […], R47.03 Dysphasie. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `G81.0` | `regi` | sujet | chaque |  |
| `R47.0` | `regi` | sujet | chaque |  |

