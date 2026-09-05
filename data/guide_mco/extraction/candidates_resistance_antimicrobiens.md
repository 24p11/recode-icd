# Candidates — RÉSISTANCE AUX ANTIMICROBIENS

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/resistance_antimicrobiens.md`
> (guide chap. V, pp. imprimées 115-116). Les `L…` y renvoient.

**5 consignes, 11 associations**.

---

## Consignes nouvelles

### GM2026-V-RAM-01 — `definition`

**Situation** : Résistances aux antimicrobiens — catégories U82, U83, U84

**Texte** : La description des résistances aux antibiotiques (OMS 2013, PMSI 2014) repose sur trois catégories : U82 Résistance aux antibiotiques bétalactamines, U83 Résistance aux autres antibiotiques, U84 Résistance aux autres antimicrobiens. Les codes ont été enrichis en 2015 par l'ATIH d'un caractère en 6e position (U82 et U83) indiquant si la résistance concerne un germe responsable d'une infection en cours ou un portage sain ; pour les codes à 4 caractères, le signe « + » est noté en 5e position.

**Condition** : —

**Citation** (`resistance_antimicrobiens.md` L10) :
« Elle repose sur trois catégories U82 Résistance aux antibiotiques bétalactamines [bétalactames], U83 Résistance aux autres antibiotiques et U84 Résistance aux autres antimicrobiens. Les codes de résistance aux antibiotiques ont été enrichis en 2015 par l’ATIH avec notamment l’ajout d’un caractère supplémentaire en 6e position […] pour les catégories U82 et U83 »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `U82` | `regi` | sujet | chaque |  |
| `U83` | `regi` | sujet | chaque |  |
| `U84` | `regi` | sujet | chaque |  |

### GM2026-V-RAM-02 — `condition_emploi`

**Situation** : Résistances — deux conditions d'emploi

**Texte** : Dans le recueil PMSI, l'emploi des codes des catégories U82 à U84 doit respecter deux conditions : la résistance est mentionnée dans le compte rendu du laboratoire de bactériologie, et elle entraîne une modification du schéma thérapeutique habituel ou la mise en œuvre de mesures d'isolement spécifiques (mesures d'hygiène d'isolement septique selon le mode de transmission, distinctes des précautions standard).

**Condition** : Mention au CR de bactériologie + modification thérapeutique ou isolement spécifique

**Citation** (`resistance_antimicrobiens.md` L12-15) :
« Dans le cadre du recueil PMSI, l’emploi des codes de ces catégories doit respecter deux conditions : […] la résistance doit être mentionnée dans le compte rendu du laboratoire de bactériologie ; […] la résistance doit entrainer une modification du schéma thérapeutique habituel, ou la mise en œuvre de mesures d’isolement spécifiques »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `U82-U84` | `regi` | sujet | chaque |  |

### GM2026-V-RAM-03 — `interdiction`

**Situation** : Résistance naturelle — ne se code pas

**Texte** : Les situations de résistance naturelle — liée à la nature du germe en termes de genre ou d'espèce — ne se codent pas.

**Condition** : Résistance naturelle du germe

**Citation** (`resistance_antimicrobiens.md` L19) :
« les situations de résistance naturelle, c'est-à-dire les situations où la résistance est liée à la nature du germe en termes de genre ou d’espèce, ne se codent pas ; »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `U82-U84` | `interdit` | sujet | chaque | résistance naturelle (genre ou espèce du germe) |

### GM2026-V-RAM-04 — `condition_emploi`

**Situation** : Portage sain d'un germe résistant avec mesures — U82/U83

**Texte** : Les situations de portage sain d'un germe présentant une résistance et faisant l'objet, du fait de cette résistance, de mesures telles que l'isolement ou l'utilisation de matériels ou d'un chariot de soins spécifiques autorisent l'emploi des codes des catégories U82 et U83.

**Condition** : Portage sain avec mesures liées à la résistance

**Citation** (`resistance_antimicrobiens.md` L20) :
« les situations de portage sain de germe présentant une résistance et faisant l’objet, du fait de cette résistance, de mesures telles que l’isolement, l’utilisation de matériels ou d’un chariot de soins spécifiques autorisent l’emploi des codes des catégories U82 et U83. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `U82` | `regi` | sujet | chaque | portage sain avec mesures liées à la résistance |
| `U83` | `regi` | sujet | chaque | portage sain avec mesures liées à la résistance |

### GM2026-V-RAM-05 — `condition_emploi`

**Situation** : Bactérie multirésistante — mention BMR obligatoire pour U83.71–

**Texte** : La mention de la résistance est indispensable (résistance à un antibiotique ou multirésistance). La notion de bactérie multirésistante [BMR] ne concerne que certains germes et résistances précisés par les laboratoires et les CCLIN : le terme doit figurer dans le dossier — la seule présence de plusieurs résistances sans mention de bactérie ou germe multirésistant n'autorise pas le code U83.71–.

**Condition** : Mention explicite de bactérie ou germe multirésistant au dossier

**Citation** (`resistance_antimicrobiens.md` L22) :
« La notion de bactérie multirésistante [BMR] ne concerne que certains germes et certaines résistances bien précisées par les laboratoires de bactériologie et les CCLIN. Ce terme doit figurer dans le dossier, la seule présence de plusieurs résistances sans mention de bactérie ou de germe multirésistant n'autorise pas le code U83.71–. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `J13` | `regi` | **exemple** | chaque |  |
| `U83.71` | `regi` | sujet | chaque | mention BMR au dossier |
| `Z22.3` | `regi` | **exemple** | chaque |  |
| `Z29.0` | `regi` | **exemple** | chaque |  |

