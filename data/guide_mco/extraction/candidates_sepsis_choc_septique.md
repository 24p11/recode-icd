# Candidates — SEPSIS ET CHOC SEPTIQUE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/sepsis_choc_septique.md`
> (guide chap. V, pp. imprimées 116-117). Les `L…` y renvoient.

**4 consignes, 16 associations**.

---

## Consignes nouvelles

### GM2026-V-SEP-01 — `regle_position`

**Situation** : Sepsis — codes « sepsis », fin du R65.1

**Texte** : Depuis le 1er mars 2021 (définition sepsis-3 de 2016), le sepsis ne se code plus par le SRIS d'origine infectieuse avec défaillance d'organe (R65.1) : il est décrit avec les codes portant « sepsis » dans leur libellé, dans les catégories A40-A41, B37.7, les extensions P36.–0 et O85 (ex. A40.0, A41.5). En cas de sepsis, et a fortiori de choc septique, R65.1 ne doit plus être codé. Le diagnostic de sepsis, posé par le clinicien, doit être mentionné au dossier ; la référence au score SOFA est recommandée mais non nécessaire pour le PMSI.

**Condition** : Diagnostic de sepsis posé par le clinicien, mentionné au dossier

**Citation** (`sepsis_choc_septique.md` L12-20) :
« le codage de celui-ci ne se basera plus sur le codage du syndrome de réponse inflammatoire systémique d'origine infectieuse avec défaillance d'organe (R65.1). Il sera décrit avec les codes qui comportent les termes sepsis dans leur libellé, dans les catégories A40- A41, B37.7, P36.-0 et O85 (exemples A40.0 Sepsis à streptocoques, groupe A, A41.5 Sepsis à d'autres microorganismes Gram négatif). […] En cas de sepsis et à fortiori de choc septique, le syndrome de réponse inflammatoire systémique d'origine infectieuse avec défaillance d'organe (R65.1) ne doit plus être codé. […] Le diagnostic de sepsis, posé par le clinicien, doit être mentionné dans le dossier médical du patient. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `A40-A41` | `regi` | sujet | chaque | sepsis diagnostiqué |
| `B37.7` | `regi` | sujet | chaque | sepsis à candida |
| `O85` | `regi` | sujet | chaque | sepsis puerpéral |
| `P36.00` | `regi` | sujet | chaque | sepsis du nouveau-né (extension « sepsis ») |
| `P36.10` | `regi` | sujet | chaque | sepsis du nouveau-né (extension « sepsis ») |
| `P36.20` | `regi` | sujet | chaque | sepsis du nouveau-né (extension « sepsis ») |
| `P36.30` | `regi` | sujet | chaque | sepsis du nouveau-né (extension « sepsis ») |
| `P36.40` | `regi` | sujet | chaque | sepsis du nouveau-né (extension « sepsis ») |
| `P36.50` | `regi` | sujet | chaque | sepsis du nouveau-né (extension « sepsis ») |
| `P36.80` | `regi` | sujet | chaque | sepsis du nouveau-né (extension « sepsis ») |
| `P36.90` | `regi` | sujet | chaque | sepsis du nouveau-né (extension « sepsis ») |
| `R65.1` | `interdit` | sujet | chaque | sepsis ou choc septique (depuis le 1er mars 2021) |

### GM2026-V-SEP-02 — `condition_emploi`

**Situation** : Infection hors sepsis — R65.0 accessible

**Texte** : En cas d'infection hors sepsis, le SRIS d'origine infectieuse sans défaillance d'organe (R65.0) reste accessible au codage lorsqu'il apporte une information supplémentaire sur la sévérité de l'infection (ex. infection urinaire basse).

**Condition** : Infection hors sepsis, information supplémentaire de sévérité

**Citation** (`sepsis_choc_septique.md` L16) :
« En cas d’infection hors sepsis, le syndrome de réponse inflammatoire systémique d'origine infectieuse sans défaillance d'organe (R65.0) reste accessible au codage lorsque qu’il apporte une information supplémentaire sur la sévérité de l’infection. (exemple infection urinaire basse). »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `R65.0` | `regi` | sujet | chaque | infection hors sepsis, information de sévérité |

### GM2026-V-SEP-03 — `regle_position`

**Situation** : Bactériémie isolée — A49 en DP, T80-T88 si iatrogène

**Texte** : Une bactériémie isolée — sans infection d'organe ou porte d'entrée précisée, sans critères de sepsis, et hors complication suivant la pose de prothèses, implants et greffes internes ou cardiaques et vasculaires — ne permet pas de coder l'infection ou le sepsis : un code de la catégorie A49 est utilisé en DP. Pour une bactériémie iatrogène, on code d'abord la complication dans T80-T88 lorsqu'elle est précisée.

**Condition** : Bactériémie isolée sans critères de sepsis

**Citation** (`sepsis_choc_septique.md` L18) :
« Une bactériémie isolée, sans infection d’organe ou porte d’entrée précisée ni critères de sepsis et, en dehors d’une complication suivant la pose de prothèses, d’implants et greffes internes ou cardiaques et vasculaires, ne permet pas de coder l’infection ou le sepsis. Dans ce cas un code de la catégorie A49 sera utilisé en DP. Pour une bactériémie iatrogène, on codera d’abord la complication dans T80-T88 lorsqu’elle est précisée. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `A49` | `DP` | sujet | chaque | bactériémie isolée sans critères de sepsis |
| `T80-T88` | `regi` | sujet | chaque | bactériémie iatrogène, complication précisée |

### GM2026-V-SEP-04 — `regle_association`

**Situation** : Choc septique — définition et R57.2 associé

**Texte** : Le choc septique est un sous-ensemble du sepsis (anomalies circulatoires, cellulaires ou métaboliques augmentant considérablement la mortalité à un mois, 25 à 35 %), défini par la présence, au cours d'un sepsis, d'un besoin de vasopresseurs en continu malgré un remplissage adéquat pour maintenir la PAM > 65 mmHg, et d'une élévation des lactates sériques > 2 mmol/l (18 mg/dl). Lorsque l'infection s'accompagne d'un choc septique ainsi défini, R57.2 Choc septique est associé au code du sepsis. Les actes CCAM de suppléance vitale, remplissage vasculaire et épuration extrarénale sont codés chaque fois qu'ils sont réalisés.

**Condition** : Critères du choc septique réunis au cours d'un sepsis

**Citation** (`sepsis_choc_septique.md` L24-31) :
« Le choc septique est un sous-ensemble du sepsis au cours duquel les anomalies circulatoires et cellulaires ou métaboliques sous-jacentes sont suffisamment profondes pour augmenter considérablement la mortalité […] Lorsque l’infection s’accompagne d’un sepsis avec choc septique comme défini ci-dessus, le code R57.2 Choc septique devra être associé au code du sepsis. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `R57.2` | `regi` | sujet | chaque | choc septique au cours d'un sepsis (associé au code du sepsis) |

