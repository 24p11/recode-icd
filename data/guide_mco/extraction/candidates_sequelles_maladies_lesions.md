# Candidates — SÉQUELLES DE MALADIES ET DE LÉSIONS TRAUMATIQUES

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/sequelles_maladies_lesions.md`
> (guide chap. V, pp. imprimées 117-119). Les `L…` y renvoient.

**4 consignes, 20 associations**.

---

## Consignes nouvelles

### GM2026-V-SEQ-01 — `definition`

**Situation** : Séquelles — définition et compétence du clinicien

**Texte** : La CIM-10 définit les séquelles comme des « états pathologiques stables, conséquences d'affections qui ne sont plus en phase active » ; on décrit la nature de la séquelle de manière exhaustive et on en donne l'origine. La notion de séquelle doit être retenue et codée chaque fois qu'elle est explicitement mentionnée : il n'appartient ni au médecin responsable de l'information médicale ni au codeur de trancher entre maladie présente et état séquellaire — c'est la compétence du médecin qui a dispensé les soins.

**Condition** : —

**Citation** (`sequelles_maladies_lesions.md` L10-20) :
« La CIM–10 définit les séquelles comme des « états pathologiques stables, conséquences d'affections qui ne sont plus en phase active » […] La notion de séquelle doit être retenue et codée chaque fois qu’elle est explicitement mentionnée. Il n’appartient pas au médecin responsable de l’information médicale ni au codeur de trancher entre le codage d’une maladie présente ou d’un état séquellaire. Ce diagnostic est de la compétence du médecin qui a dispensé les soins au patient. »

*Aucune association.* Le guide ne nomme ici aucun code : en attribuer supposerait de **choisir** des cibles que le texte ne donne pas.

### GM2026-V-SEQ-02 — `regle_position`

**Situation** : Séquelles — nature en premier, code « Séquelles de… » associé

**Texte** : Pour le codage d'une séquelle, on donne la priorité au code qui correspond à sa nature (le code retenu pour l'affection principale désigne la nature des séquelles elles-mêmes) ; on peut y ajouter le code « Séquelles de… » des catégories dédiées (B90-B94, E64.–, E68, G09, I69.–, O97, T90-T98, Y85-Y89, auxquelles s'ajoute O94). Le code de séquelle est un diagnostic associé ; depuis le 1er mars 2013 il peut aussi être enregistré en diagnostic relié lorsqu'il en respecte la définition.

**Condition** : —

**Citation** (`sequelles_maladies_lesions.md` L16-27) :
« Le code retenu pour " affection principale " doit être celui qui désigne la nature des séquelles elles-mêmes, auquel on peut ajouter le code " Séquelles de…" [...]. » […] Pour le codage d’une séquelle, conformément à la consigne de la CIM–10, on donne la priorité au code qui correspond à sa nature. Le code de séquelle est un diagnostic associé (se reporter au point 2 du chapitre précédent). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `B90-B94` | `DAS` | sujet | chaque |  |
| `B90.1` | `regi` | **exemple** | chaque |  |
| `B91` | `regi` | **exemple** | chaque |  |
| `E64` | `DAS` | sujet | chaque |  |
| `E68` | `DAS` | sujet | chaque |  |
| `G09` | `DAS` | sujet | chaque |  |
| `G83.1` | `regi` | **exemple** | chaque |  |
| `I69` | `DAS` | sujet | chaque |  |
| `I69.3` | `regi` | **exemple** | chaque |  |
| `N97.1` | `regi` | **exemple** | chaque |  |
| `O94` | `DAS` | sujet | chaque |  |
| `O97` | `DAS` | sujet | chaque |  |
| `T90-T98` | `DAS` | sujet | chaque |  |

### GM2026-V-SEQ-03 — `condition_emploi`

**Situation** : Séquelles — le délai d'un an ne compte pas

**Texte** : Le délai « d'un an ou plus après le début de la maladie » cité dans les notes de certaines rubriques (G09, I69, T90-T98, Y85-Y89, O94) ne doit pas être pris en compte : il concerne les règles de codage de la mortalité (cas où il n'est pas identifié d'autre cause au décès).

**Condition** : —

**Citation** (`sequelles_maladies_lesions.md` L18) :
« Un délai « d’un an ou plus après le début de la maladie » est cité dans les notes propres à certaines rubriques (G09, I69, T90-T98, Y85-Y89, O94). Il n’y a pas lieu d’en tenir compte. Il concerne les règles de codage de la mortalité »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `G09` | `regi` | sujet | chaque |  |
| `I69` | `regi` | sujet | chaque |  |
| `O94` | `regi` | sujet | chaque |  |
| `T90-T98` | `regi` | sujet | chaque |  |
| `Y85-Y89` | `regi` | sujet | chaque |  |

### GM2026-V-SEQ-04 — `regle_position`

**Situation** : Séquelles — circonstances d'origine Y85-Y89 en DAS

**Texte** : Les catégories Y85-Y89 (chapitre XX) codent les circonstances d'origine des séquelles : il est recommandé de les utiliser, en position de diagnostic associé, chaque fois qu'on dispose de l'information nécessaire (les codes du chapitre XX ne s'utilisent jamais en DP ou DR).

**Condition** : Information sur les circonstances disponible

**Citation** (`sequelles_maladies_lesions.md` L29-31) :
« Les catégories Y85–Y89 (chapitre XX de la CIM–10) permettent de coder des circonstances d’origine des séquelles. Il est recommandé de les utiliser, en position de diagnostic associé […] chaque fois qu’on dispose de l’information nécessaire. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `T90.5` | `regi` | **exemple** | chaque |  |
| `Y85-Y89` | `DAS` | sujet | chaque | information sur les circonstances disponible |

