# Candidates — PRÉCARITÉ

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/precarite.md`
> (guide chap. V, pp. imprimées 114-115). Les `L…` y renvoient.

**12 consignes, 22 associations**.

---

## Consignes nouvelles

### GM2026-V-PRE-01 — `regle_position`

**Situation** : Codes de précarité — emploi en DAS

**Texte** : Pour décrire les situations de précarité susceptibles d'avoir un impact sur la prise en charge, des consignes d'emploi de codes existants et des extensions nationales ont été créées en 2015. Ces codes peuvent être utilisés en position de diagnostic associé dès lors qu'ils en respectent la définition, notamment en termes d'accroissement de la charge en soins, ou lorsque les conditions socioéconomiques ont justifié une prise en charge particulière (situations mentionnées au dossier médical, notamment suite à l'intervention d'une assistante sociale).

**Condition** : Définition respectée : accroissement de la charge en soins ou prise en charge particulière justifiée

**Citation** (`precarite.md` L10-14) :
« Ces codes peuvent être utilisés en position de diagnostic associé dès lors qu’ils en respectent la définition notamment en termes d’accroissement de la charge en soins ou lorsque les conditions socioéconomiques ont justifié une prise en charge particulière »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z55.00` | `DAS` | sujet | chaque | définition du code respectée |
| `Z55.1` | `DAS` | sujet | chaque | définition du code respectée |
| `Z59.0` | `DAS` | sujet | chaque | définition du code respectée |
| `Z59.10` | `DAS` | sujet | chaque | définition du code respectée |
| `Z59.11` | `DAS` | sujet | chaque | définition du code respectée |
| `Z59.12` | `DAS` | sujet | chaque | définition du code respectée |
| `Z59.13` | `DAS` | sujet | chaque | définition du code respectée |
| `Z59.50` | `DAS` | sujet | chaque | définition du code respectée |
| `Z59.62` | `DAS` | sujet | chaque | définition du code respectée |
| `Z60.20` | `DAS` | sujet | chaque | définition du code respectée |
| `Z60.30` | `DAS` | sujet | chaque | définition du code respectée |

### GM2026-V-PRE-02 — `definition`

**Situation** : Précarité — définition de Z55.00 (Analphabétisme et illettrisme)

**Texte** : Z55.00 Analphabétisme et illettrisme : Incapacité, d'origine non médicale, à lire un texte simple en le comprenant, à utiliser et à communiquer une information écrite dans la vie courante. Réservé aux personnes de plus de 15 ans ; ne concerne que la langue d'usage du patient.

**Condition** : —

**Citation** (`precarite.md` L16) :
« Z55.00 Analphabétisme et illettrisme, concerne les personnes qui présentent une incapacité, d’origine non médicale, à lire un texte simple en le comprenant, à utiliser et à communiquer une information écrite dans la vie courante. Ce code est réservé aux personnes de plus de 15 ans et ne concerne que la langue d’usage du patient. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z55.00` | `regi` | sujet | chaque |  |

### GM2026-V-PRE-03 — `definition`

**Situation** : Précarité — définition de Z55.1 (Scolarité inexistante ou inaccessible)

**Texte** : Z55.1 Scolarité inexistante ou inaccessible : Enfants de moins de 17 ans ne suivant, au moment de l'admission, aucun processus d'instruction (filière scolaire en établissement ou à distance, enseignement par tiers…), pour des raisons autres que médicales. L'absentéisme chronique (enfant inscrit mais non présent) est également codé ainsi.

**Condition** : —

**Citation** (`precarite.md` L18) :
« Z55.1 Scolarité inexistante ou inaccessible, concerne les enfants de moins de 17 ans ne suivant, au moment de l’admission, aucun processus d’instruction […] L’absentéisme chronique (enfant inscrit mais non présent) est également codé ainsi. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z55.1` | `regi` | sujet | chaque |  |

### GM2026-V-PRE-04 — `definition`

**Situation** : Précarité — définition de Z59.0 (Sans abri)

**Texte** : Z59.0 Sans abri : Personne vivant dans la rue au moment de l'admission, ou hébergée dans un centre d'hébergement d'urgence ou un centre d'hébergement et de réinsertion sociale (CHRS).

**Condition** : —

**Citation** (`precarite.md` L20) :
« Z59.0 Sans abri, s’utilise pour une personne vivant dans la rue au moment de l’admission, ou hébergée dans un centre d’hébergement d’urgence, ou dans un centre d’hébergement et de réinsertion sociale (CHRS). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z59.0` | `regi` | sujet | chaque |  |

### GM2026-V-PRE-05 — `definition`

**Situation** : Précarité — définition de Z59.10 (Logement insalubre ou impropre à l'habitation)

**Texte** : Z59.10 Logement insalubre ou impropre à l'habitation : Logements présentant un danger pour la santé des occupants, hébergements dans des lieux non destinés à l'habitation, squats.

**Condition** : —

**Citation** (`precarite.md` L24) :
« Z59.10 Logement insalubre ou impropre à l’habitation, correspond aux logements présentant un danger pour la santé de ses occupants, aux hébergements dans des lieux non destinés à l’habitation ou aux squats. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z59.10` | `regi` | sujet | chaque |  |

### GM2026-V-PRE-06 — `definition`

**Situation** : Précarité — définition de Z59.11 (Logement sans confort)

**Texte** : Z59.11 Logement sans confort : Logements sans confort sanitaire (absence d'eau courante, d'installation sanitaire ou de WC intérieurs) ; logements sans chauffage, à chauffage sommaire ou sans électricité.

**Condition** : —

**Citation** (`precarite.md` L26) :
« Z59.11 Logement sans confort, correspond aux logements sans confort sanitaire, c’est-à-dire lorsqu’un des éléments suivants est absent : eau courante, installation sanitaire, WC intérieurs. Les logements sans chauffage ou avec un moyen de chauffage sommaire, ou sans électricité relèvent également de ce code. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z59.11` | `regi` | sujet | chaque |  |

### GM2026-V-PRE-07 — `definition`

**Situation** : Précarité — définition de Z59.12 (Logement inadéquat du fait de l'état de santé)

**Texte** : Z59.12 Logement inadéquat du fait de l'état de santé : Logement devenu inadéquat du fait de l'état de santé de la personne à la sortie de l'hôpital.

**Condition** : —

**Citation** (`precarite.md` L28) :
« Z59.12 Logement inadéquat du fait de l’état de santé de la personne, concerne un logement devenu inadéquat du fait de l’état de santé de la personne à la sortie de l’hôpital. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z59.12` | `regi` | sujet | chaque |  |

### GM2026-V-PRE-08 — `definition`

**Situation** : Précarité — définition de Z59.13 (Logement en habitat temporaire ou de fortune)

**Texte** : Z59.13 Logement en habitat temporaire ou de fortune : Hébergements tels que hôtel, mobil-home, caravane, camping ou cabane.

**Condition** : —

**Citation** (`precarite.md` L30) :
« Enfin, Z59.13 Logement en habitat temporaire ou de fortune, est à utiliser pour des hébergements tels que hôtel, mobil- home, caravane, camping ou cabane. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z59.13` | `regi` | sujet | chaque |  |

### GM2026-V-PRE-09 — `definition`

**Situation** : Précarité — définition de Z59.50 (Absence totale de revenu, d'aide et de prestations financières)

**Texte** : Z59.50 Absence totale de revenu, d'aide et de prestations financières : Absence totale de revenu (salaires, activité commerciale, prestations financières dont minima sociaux…) ou personnes n'ayant que la mendicité comme source de revenu — la mendicité ne se code pas ici si elle n'est pas l'unique source de revenu.

**Condition** : —

**Citation** (`precarite.md` L32) :
« Z59.50 Absence totale de revenu, d’aide et de prestations financières, correspond à une absence totale de revenu […] La mendicité n’est pas à coder ici si elle ne constitue pas l’unique source de revenu. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z59.50` | `regi` | sujet | chaque |  |

### GM2026-V-PRE-10 — `definition`

**Situation** : Précarité — définition de Z59.62 (Bénéficiaires de minima sociaux)

**Texte** : Z59.62 Bénéficiaires de minima sociaux : Personnes percevant des allocations soumises à conditions de ressources : RSA, ASS, ATA, AER, AAH, ASPA, ASI.

**Condition** : —

**Citation** (`precarite.md` L34) :
« Z59.62 Bénéficiaires de minima sociaux, concernent les personnes qui perçoivent des allocations soumises à conditions de ressources telles que le revenu de solidarité active (RSA), l’allocation de solidarité spécifique (ASS) »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z59.62` | `regi` | sujet | chaque |  |

### GM2026-V-PRE-11 — `definition`

**Situation** : Précarité — définition de Z60.20 (Personne vivant seule à son domicile)

**Texte** : Z60.20 Personne vivant seule à son domicile : Personnes vivant seules à leur domicile, quel que soit leur sentiment de solitude ou d'isolement ; ne concerne pas les personnes vivant en établissement collectif.

**Condition** : —

**Citation** (`precarite.md` L36) :
« Z60.20 Personne vivant seule à son domicile, concerne les personnes vivant seules à leur domicile, quel que soit leur sentiment de solitude ou d’isolement. Ce code ne concerne pas les personnes vivant en établissement collectif. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z60.20` | `regi` | sujet | chaque |  |

### GM2026-V-PRE-12 — `definition`

**Situation** : Précarité — définition de Z60.30 (Difficultés liées à la langue)

**Texte** : Z60.30 Difficultés liées à la langue : S'emploie lorsque le recours à un interprète (un tiers) est nécessaire pour la prise en charge du patient.

**Condition** : —

**Citation** (`precarite.md` L38) :
« Z60.30 Difficultés liées à la langue, s’emploie lorsque le recours à un interprète (un tiers) est nécessaire pour la prise en charge du patient. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z60.30` | `regi` | sujet | chaque |  |

