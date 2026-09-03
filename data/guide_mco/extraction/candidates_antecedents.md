# Candidates — ANTÉCÉDENTS

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/antecedents.md`
> (guide chap. V, pp. imprimées 82-83). Les `L…` y renvoient.

**5 consignes, 29 associations**.

---

## Consignes nouvelles

### GM2026-V-ANT-01 — `interdiction`

**Situation** : Antécédent personnel ou familial — principe de codage

**Texte** : Une affection constituant un antécédent personnel (maladie ancienne guérie) ou familial (affection dont le patient n'est personnellement pas atteint) ne doit pas être enregistrée dans le RUM avec le code qu'on utiliserait si elle était présente : pas de code des chapitres I à XIX (sinon éventuellement comme donnée à visée documentaire). Elle doit être codée avec le chapitre XXI (« codes Z »).

**Condition** : L'affection est un antécédent : le patient n'est plus ou n'est pas atteint au moment du séjour

**Citation** (`antecedents.md` L10) :
« Une affection constituant un antécédent personnel […] ne doit pas être enregistrée dans le résumé d’unité médicale (RUM) avec le code qu’on utiliserait si elle était présente (« active »), c’est-à-dire qu’elle ne doit pas être codée avec les chapitres I à XIX de la CIM–10 (sinon éventuellement comme une donnée à visée documentaire). La même règle s’impose dans le cas d’un antécédent familial […] Un antécédent personnel ou familial […] doit être codé avec le chapitre XXI (« codes Z »). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `I` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `II` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `III` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `IV` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `IX` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `V` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `VI` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `VII` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `VIII` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `X` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `XI` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `XII` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `XIII` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `XIV` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `XIX` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `XV` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `XVI` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `XVII` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `XVIII` | `interdit` | sujet | chaque | l'affection est un antécédent (guérie / patient non atteint) |
| `XXI` | `regi` | sujet | **ensemble** — Domaine du choix : le code Z est choisi selon la nature de l'antécédent, et l'essentiel du chapitre XXI ne code pas d'antécédents — précédent AVC-14 (fiche de Z23.0) |  |

### GM2026-V-ANT-02 — `condition_emploi`

**Situation** : Catégories d'antécédents Z80-Z99 — affections à séquelles exclues

**Texte** : Les catégories Z80 à Z99 du chapitre XXI sont destinées au codage des antécédents. Les affections qui entraînent habituellement des séquelles font partie de leurs exclusions (ex. : Z86.1 exclut les séquelles de maladies infectieuses et parasitaires ; Z86.7 exclut l'infarctus ancien, les séquelles de maladies cérébrovasculaires et le syndrome postinfarctus).

**Condition** : —

**Citation** (`antecedents.md` L12-18) :
« On trouve dans le chapitre XXI de la CIM–10 des catégories (Z80 à Z99) destinées au codage des antécédents. […] Les affections qui entrainent habituellement des séquelles font partie des exclusions de ces catégories. […] Z86.1 Antécédents personnels de maladies infectieuses et parasitaires exclut les séquelles de maladies infectieuses et parasitaires ; […] Z86.7 Antécédents personnels de maladies de l’appareil circulatoire exclut l’infarctus ancien, les séquelles de maladies cérébrovasculaires et le syndrome postinfarctus. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z80-Z99` | `regi` | sujet | chaque |  |
| `Z86.1` | `regi` | **exemple** | chaque |  |
| `Z86.7` | `regi` | **exemple** | chaque |  |

### GM2026-V-ANT-03 — `condition_emploi`

**Situation** : Z86.7 — emploi obligatoire des extensions Z86.70 et Z86.71

**Texte** : Z86.7 a des extensions créées pour la version 11 des GHM (2009) : Z86.70 et Z86.71. Leur emploi est obligatoire.

**Condition** : —

**Citation** (`antecedents.md` L18) :
« Z86.7 a des extensions, créées pour la version 11 des GHM (2009) : Z86.70 et Z86.71. Leur emploi est obligatoire (voir le Manuel des groupes homogènes de malades). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z86.7` | `regi` | sujet | chaque |  |
| `Z86.70` | `regi` | sujet | chaque |  |
| `Z86.71` | `regi` | sujet | chaque |  |

### GM2026-V-ANT-04 — `definition`

**Situation** : Définition de l'antécédent

**Texte** : Un antécédent est une affection ancienne qui n'existe plus et qui n'est pas cause de troubles résiduels au moment de l'hospitalisation concernée par le recueil d'informations (sinon on parlerait de séquelles, non d'antécédents). Cette définition conditionne l'emploi des catégories d'antécédents.

**Condition** : —

**Citation** (`antecedents.md` L20) :
« On retient la suivante : une affection ancienne qui n’existe plus et qui n’est pas cause de troubles résiduels […] au moment de l’hospitalisation concernée par le recueil d’informations. […] Sinon on parlerait de séquelles, non d’antécédents (voir le point 2 de ce chapitre). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `Z80-Z99` | `regi` | sujet | chaque |  |

### GM2026-V-ANT-05 — `condition_emploi`

**Situation** : Antécédent personnel de tumeur maligne — cancer ou antécédent de cancer

**Texte** : Le choix entre « cancer » et « antécédent de cancer » est une question médicale : il ne dépend pas du codeur et il n'appartient ni au médecin responsable de l'information médicale ni au codeur de trancher — c'est la compétence du médecin qui dispense les soins. Le délai traditionnel de cinq ans, de tradition purement orale, est médicalement erroné et ne doit plus servir de référence. Cancer devenu antécédent : catégorie Z85 ; cancer encore actif : code adapté du chapitre II.

**Condition** : —

**Citation** (`antecedents.md` L22-26) :
« Le choix entre « cancer » et « antécédent de cancer » est d’abord une question médicale, il ne dépend pas du codeur […] Il ne faut plus se référer au délai de cinq ans. […] Si un clinicien estime qu’un cancer « extirpé chirurgicalement dans sa totalité » est devenu un antécédent, il faut le coder avec la catégorie Z85 de la CIM– 10. S’il considère au contraire qu’il est trop tôt pour parler d’antécédent, il faut l’enregistrer au moyen du code adapté du chapitre II de la CIM–10. […] Ainsi, il n’appartient pas au médecin responsable de l’information médicale ni au codeur de trancher entre cancer et antécédent de cancer. Ce diagnostic est de la compétence du médecin qui dispense les soins au patient. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `II` | `regi` | sujet | **ensemble** — « code adapté du chapitre II » : domaine du choix ; l'alternative cancer/antécédent ne régit pas chaque membre du chapitre II (tumeurs bénignes, in situ, à évolution imprévisible non concernées) | cancer encore actif |
| `Z85` | `regi` | sujet | chaque | cancer considéré comme un antécédent par le clinicien |

