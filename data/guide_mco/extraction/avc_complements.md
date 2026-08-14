# Candidates — ACCIDENTS VASCULAIRES CÉRÉBRAUX (compléments)

> **Statut : à valider ligne à ligne. Rien ici n'est dans les tables curées.**
>
> Source : `data/guide_mco/extraits/avc.txt` (chap. V, pp. imprimées 78-81).
> Les numéros de ligne `L…` renvoient à ce fichier, extrait par
> `pdftotext -layout` — la contre-lecture doit se faire contre lui.
>
> Le §5 de la note de conception a fourni AVC-01 à AVC-06, déjà versées.
> Ce fichier contient **(a)** les deux associations manquantes de AVC-02
> et AVC-04, et **(b)** les consignes que la lecture du texte source
> révèle et que le §5 n'avait pas relevées.

---

## (a) Associations manquantes de consignes déjà versées

AVC-02 et AVC-04 sont dans `recommendations_curated.csv` mais n'ont
aucune ligne dans `recommendation_codes_curated.csv` — le §5 n'en
donnait pas. Elles ressortent au rapport de build sous
`guide_mco_recommandations_sans_code.csv`. Sans ces lignes, les deux
consignes n'atteignent aucune fiche.

### GM2026-V-AVC-02 — associations
| code_expr | role | centralite | condition |
|---|---|---|---|
| `I64` | `condition_emploi`… → voir remarque | `sujet` | |
| `I60-I63` | `interdit_association` | `sujet` | un code plus précis existe |

> **Remarque — pas de rôle pour « c'est ce code que la consigne
> régit ».** La consigne AVC-02 porte *sur* I64 sans lui assigner de
> position. Le rôle le plus proche est `contexte`, mais son sens est
> « situe la consigne sans être ce qu'elle prescrit », ce qui est
> exactement l'inverse. Je propose `contexte` **par défaut** et signale
> le cas au §Extensions d'enum ci-dessous.

**Citation** (L120-121) : « Le code I64 ne doit être employé qu'en
l'absence d'examen de neuro-imagerie et ne doit pas l'être en
association avec un code plus précis. »

### GM2026-V-AVC-04 — associations
| code_expr | role | centralite | condition |
|---|---|---|---|
| `I60-I64` | `DP` | `sujet` | récidive confirmée par l'imagerie |

**Citation** (L168-169) : « Séjour pour récidive d'AVC : une récidive
d'AVC, à la condition qu'elle soit confirmée par l'imagerie, doit être
codée comme un AVC à la phase aigüe. »

---

## (b) Consignes nouvelles

### GM2026-V-AVC-07 — `regle_association`
**Situation** : AVC — association d'un AIT et d'un AVC constitué
**Texte** : Un code d'AIT (G45.–) et un code d'AVC constitué (I60–I64) ne peuvent être associés que s'il s'agit de deux épisodes distincts au cours du même séjour.
**Condition** : Deux épisodes distincts au cours du même séjour
**Citation** (L123-124) : « Un code d'AIT (G45.–) et un code d'AVC constitué (I60–I64) ne peuvent être associés que s'il s'agit de deux épisodes distincts au cours du même séjour. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `G45` | `interdit_association` | `sujet` | sauf deux épisodes distincts |
| `I60-I64` | `interdit_association` | `sujet` | sauf deux épisodes distincts |

### GM2026-V-AVC-08 — `regle_position`
**Situation** : AVC à la phase aigüe — manifestations cliniques
**Texte** : Les manifestations cliniques de l'AVC sont codées comme diagnostics associés significatifs (DAS) si elles en respectent la définition, le plus précisément possible et en employant les extensions ATIH prévues (hémiplégie G81.0–, aphasie et dysphasie R47.0–).
**Condition** : Respect de la définition du DAS
**Citation** (L126-129) : « Les manifestations cliniques de l'AVC sont codées comme diagnostics associés significatifs (DAS) si elles en respectent la définition. Il importe de les coder le plus précisément possible et d'employer les extensions prévues pour certains codes (hémiplégie, dysphasie et aphasie : se reporter au point 2 supra). »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `G81` | `DAS` | `sujet` | |
| `R47` | `DAS` | `sujet` | |
| `I60-I64` | `contexte` | `sujet` | |

### GM2026-V-AVC-09 — `interdiction`
**Situation** : AVC — syndromes des artères cérébrales G46.0 à G46.2
**Texte** : G46.0, G46.1 et G46.2 sont réservés aux syndromes neurologiques résultant d'une insuffisance circulatoire **sans** infarctus : ils ne peuvent pas être associés à un code d'infarctus cérébral. Cette association reste possible pour G46.3 à G46.8.
**Condition** : —
**Citation** (L76-81) : « la CIM–10 réserve les codes G46.0 à G46.2 […] à l'enregistrement de syndromes neurologiques résultant d'une insuffisance circulatoire sans infarctus […]. Ainsi, G46.0, G46.1 et G46.2 ne peuvent pas être associés à un code d'infarctus cérébral, alors que cette association est possible pour les codes G46.3 à G46.8. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `G46.0-G46.2` | `interdit_association` | `sujet` | |
| `I63` | `contexte` | `sujet` | |
| `G46.3-G46.8` | `contexte` | `sujet` | association autorisée |

> **Distincte de AVC-03**, qui porte sur la description de l'artère ou du
> mécanisme et vise I60–I64. Celle-ci porte sur l'infarctus (I63) et
> énonce en creux une **autorisation** pour G46.3–G46.8. Fusionner les
> deux perdrait l'autorisation.

### GM2026-V-AVC-10 — `regle_position`
**Situation** : AVC — codage des séquelles
**Texte** : Le codage des séquelles donne la priorité aux manifestations cliniques observées, auxquelles on associe un code de la catégorie I69 Séquelles de maladies cérébrovasculaires.
**Condition** : —
**Citation** (L89-92) : « La CIM–10 définit les séquelles comme des "états pathologiques, stables, conséquences d'affections qui ne sont plus en phase active". Leur codage donne la priorité aux manifestations cliniques observées, auxquelles on associe un code de la catégorie I69 Séquelles de maladies cérébrovasculaires. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `I69` | `contexte` | `sujet` | associé à la manifestation |

### GM2026-V-AVC-11 — `condition_emploi`
**Situation** : AVC — antécédent sans séquelle
**Texte** : Z86.70 exclut par construction la notion de séquelle ; il doit être employé dès que l'AVC est considéré comme ancien et qu'il ne persiste aucune séquelle fonctionnelle.
**Condition** : AVC ancien, aucune séquelle fonctionnelle persistante
**Citation** (L94-97) : « Par construction de la CIM–10, la notion d'antécédent d'AVC, codée Z86.70, exclut celle de séquelle. Le code Z86.70 Antécédents personnels de maladies cérébrovasculaires doit être employé dès que l'AVC est considéré comme ancien et qu'il ne persiste aucune séquelle fonctionnelle. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z86.70` | `contexte` | `sujet` | |
| `I69` | `interdit_association` | `sujet` | incompatible avec l'antécédent |

### GM2026-V-AVC-12 — `regle_position`
**Situation** : AVC — séjour pour poursuite des soins dans une autre unité ou un autre établissement
**Texte** : En cas de transfert dans un autre établissement de MCO, l'AVC peut être codé comme DP dans l'établissement d'accueil dès lors qu'il continue d'être le sujet des soins.
**Condition** : L'AVC continue d'être le sujet des soins
**Citation** (L152-155) : « en cas de transfert dans un autre établissement de MCO après sortie d'unité neurovasculaire, l'AVC peut être codé comme DP dans l'autre établissement dès lors qu'il continue d'être le sujet des soins (situation clinique de traitement unique partagé […]). »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `I60-I64` | `DP` | `sujet` | |

### GM2026-V-AVC-13 — `regle_position`
**Situation** : AVC — séjour pour aggravation ou complication (séjour distinct de la prise en charge initiale)
**Texte** : La manifestation ou la complication prise en charge est codée comme DP ; un code de séquelle d'AVC (I69) est placé en DAS.
**Condition** : Séjour distinct de celui de la prise en charge initiale
**Citation** (L157-166) : « Séjour pour prise en charge d'une aggravation d'un état neurologique consécutif à un AVC […]. La manifestation ou la complication prise en charge est codée comme DP. Les exemples les plus fréquents sont les troubles de la marche ou l'aggravation de la spasticité (catégorie R26 […]), le syndrome dépressif (catégorie F32 […]), l'épilepsie (catégories G40 […] et G41 […]), la démence vasculaire (catégorie F01 […]). Un code de séquelle d'AVC (I69) est placé en DAS. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `I69` | `DAS` | `sujet` | |
| `R26` | `DP` | **`exemple`** | |
| `F32` | `DP` | **`exemple`** | |
| `G40` | `DP` | **`exemple`** | |
| `G41` | `DP` | **`exemple`** | |
| `F01` | `DP` | **`exemple`** | |

> C'est le cas qui motive `centralite` : **la fiche de F32 n'a pas
> vocation à recevoir la consigne AVC.** Le §5 de la note l'anticipait
> déjà.

### GM2026-V-AVC-14 — `regle_position`
**Situation** : AVC — surveillance au long cours **avec** séquelles, sans affection nouvelle
**Texte** : S'il n'est pas découvert d'affection nouvelle, le DP appartient au chapitre XXI ; un code de séquelle d'AVC (I69) est placé en DR et les manifestations séquellaires éventuelles sont codées comme DAS.
**Condition** : Aucune affection nouvelle découverte ; séquelles présentes
**Citation** (L176-180) : « S'il n'est pas découvert d'affection nouvelle le code du DP appartient au chapitre XXI de la CIM-10 […]. Un code de séquelle d'AVC (I69) est placé en DR et les manifestations séquellaires éventuelles sont codées comme DAS si elles en respectent la définition. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `XXI` | `DP` | `sujet` | |
| `I69` | `DR` | `sujet` | |

> **Complète AVC-05, elle ne la remplace pas.** AVC-05 traite le cas
> *sans* séquelle (DP = Z86.70, pas de DR) ; celle-ci le cas *avec*
> séquelles. Les deux se lisent dans le même paragraphe du guide.

### GM2026-V-AVC-15 — `regle_position`
**Situation** : AVC — surveillance dite positive (affection nouvelle liée à l'AVC)
**Texte** : Si une affection nouvelle liée à l'AVC — complication de celui-ci ou de son traitement — est découverte, cette affection est le DP ; les manifestations séquellaires respectant la définition d'un DAS, complétées par un code de séquelle I69.–, sont enregistrées en position de diagnostics associés.
**Condition** : Découverte d'une affection nouvelle liée à l'AVC
**Citation** (L185-189) : « Si une affection nouvelle liée à l'AVC, c'est-à-dire une complication de celui-ci ou de son traitement, est découverte (surveillance dite positive), cette affection est le DP. Les éventuelles manifestations séquellaires respectant la définition d'un DAS, complétées par un code de séquelle I69.–, sont enregistrées en position de diagnostics associés. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `I69.–` | `DAS` | `sujet` | |

### GM2026-V-AVC-16 — `regle_position`
**Situation** : AVC — séjour pour répit de la famille ou des aidants
**Texte** : Le DP est codé Z74.2 Besoin d'assistance à domicile […] ou Z75.5 Prise en charge pendant les vacances ; un code de séquelle de maladie cérébrovasculaire (I69.–) est saisi en position de DAS.
**Condition** : —
**Citation** (L199-202) : « Séjour pour répit de la famille ou des aidants : le DP est codé Z74.2 […] ou Z75.5 Prise en charge pendant les vacances. Un code de séquelle de maladie cérébrovasculaire (I69.–) est saisi en position de DAS. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `Z74.2` | `DP` | `sujet` | |
| `Z75.5` | `DP` | `sujet` | |
| `I69.–` | `DAS` | `sujet` | |

### GM2026-V-AVC-17 — `condition_emploi`
**Situation** : AVC — codage de l'étiologie
**Texte** : L'étiologie ne peut être codée comme diagnostic associé que si elle en respecte la définition. Les étiologies sont classées dans des rubriques diverses de la CIM–10.
**Condition** : Respect de la définition du diagnostic associé
**Citation** (L143-144) : « L'étiologie ne peut être codée comme diagnostic associé que si elle en respecte la définition. » — et (L85-87) : « Les étiologies des AVC sont classées dans des rubriques diverses de la CIM–10 ; par exemple la fibrillation auriculaire (I48), les malformations congénitales vasculaires cérébrales (Q28.–), l'athérosclérose cérébrale (I67.2), l'encéphalopathie hypertensive (I67.4), etc. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `I48` | `DAS` | **`exemple`** | |
| `Q28.–` | `DAS` | **`exemple`** | |
| `I67.2` | `DAS` | **`exemple`** | |
| `I67.4` | `DAS` | **`exemple`** | |

### GM2026-V-AVC-18 — `condition_emploi`
**Situation** : AVC — codage des complications
**Texte** : Les complications sont codées comme DAS si elles en respectent la définition (par exemple inhalation, épilepsie, escarre, démence vasculaire).
**Condition** : Respect de la définition du DAS
**Citation** (L146-147) : « Les complications sont codées comme DAS si elles en respectent la définition, par exemple, inhalation, épilepsie, escarre, démence vasculaire… »

> **Aucune association proposée** : le guide ne donne ici que des
> libellés en clair, sans code. Les rattacher supposerait de **choisir**
> des codes que le texte ne nomme pas — hors de ce que la curation peut
> attester. Consigne conservée sans cible, ou à écarter : à votre
> arbitrage.

### GM2026-V-AVC-19 — `definition`
**Situation** : AVC constitué à la phase aigüe — périmètre des catégories
**Texte** : Le codage des AVC constitués fait appel, à la phase aigüe, aux catégories I60 à I63, qui **excluent les lésions traumatiques**. I60 inclut la rupture d'anévrisme d'artère cérébrale ; I62 inclut l'hémorragie sous-durale et extradurale ; I63 couvre les AVC ischémiques (embolie, thrombose, bas débit).
**Condition** : —
**Citation** (L28-39) : « Le codage des AVC constitués fait appel, à la phase aigüe, aux catégories I60 à I63 qui excluent les lésions traumatiques. […] I60 Hémorragie sous-arachnoïdienne ; cette catégorie inclut la rupture d'anévrisme d'artère cérébrale ; […] I62 […] cette catégorie inclut l'hémorragie sous-durale et extradurale. Les AVC par infarctus cérébral ou AVC ischémiques — embolie, thrombose, bas débit — sont codés avec la catégorie I63 Infarctus cérébral. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `I60-I63` | `contexte` | `sujet` | |

### GM2026-V-AVC-20 — `definition`
**Situation** : AVC — extensions ATIH des manifestations (hémiplégie, aphasie)
**Texte** : G81.0 et R47.0 ont été subdivisés par l'ATIH en 2007 pour distinguer les symptômes selon leur moment d'apparition et leur évolution : G81.00 (flasque récente, persistante au-delà de 24 h), G81.01 (régressive dans les 24 h), G81.08 ; R47.00, R47.01, R47.02, R47.03. Les mêmes codes servent pour les parésies et les paralysies.
**Condition** : —
**Citation** (L50-62) : « À l'initiative de la Société française neurovasculaire, ces deux catégories ont fait l'objet d'extensions par l'ATIH en 2007 afin de distinguer les symptômes selon leur moment d'apparition et leur évolution : G81.0 Hémiplégie flasque est subdivisé en : G81.00 […], G81.01 […] et G81.08 […] ; on emploie les mêmes codes pour les parésies et les paralysies […] ; R47.0 Dysphasie et aphasie est subdivisé en : R47.00 […], R47.01 […], R47.02 […], R47.03 Dysphasie. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `G81.0` | `contexte` | `sujet` | |
| `R47.0` | `contexte` | `sujet` | |

---

## Extensions d'enum à arbitrer

**1. Rôle « sujet de la consigne, sans position assignée ».** AVC-02
(« I64 n'est employé qu'en l'absence de neuro-imagerie ») régit
l'emploi d'un code sans lui donner de position DP/DR/DAS. `contexte`
est défini comme « situe la consigne **sans être ce qu'elle
prescrit** » — c'est l'inverse. Trois options :

- (a) élargir la définition de `contexte` — mais on perd la distinction
  entre « c'est de ce code qu'on parle » et « ce code n'est là que pour
  situer », qui est utile au rendu ;
- (b) ajouter un rôle `regi` (ou `objet`) — le plus fidèle, et
  `centralite=sujet` ne le remplace pas puisqu'elle répond à une autre
  question (illustration ou non) ;
- (c) laisser `contexte` et documenter l'imprécision.

**Ma recommandation : (b)**, mais l'ajout d'une neuvième modalité se
décide, il ne se glisse pas.

**2. Observation, sans demande d'extension.** Le guide distingue
« le DP **est codé** X » (obligation) de « X **peut** être codé en
DP » (permission). Le modèle écrase les deux sur `DP`. Ce n'est pas
gênant pour la génération de CRH, ça le deviendrait pour
recode-scenario, qui voudrait savoir si une contrainte est dure. À
noter au backlog plutôt qu'à traiter ici.
