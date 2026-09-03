# Candidates — INTERRUPTION DE LA GROSSESSE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/interruption_grossesse.md`
> (guide chap. V, pp. imprimées 106-109). Les `L…` y renvoient.

**9 consignes, 21 associations**.

---

## Consignes nouvelles

### GM2026-V-ITG-01 — `definition`

**Situation** : Interruption de la grossesse — IVG et IMG

**Texte** : Par « interruption de la grossesse » on entend d'une part l'interruption volontaire (IVG, articles L.2212-1 et suivants du CSP), d'autre part l'interruption pour motif médical (IMG, dite aussi interruption thérapeutique, articles L.2213-1 et suivants du CSP).

**Condition** : —

**Citation** (`interruption_grossesse.md` L10-13) :
« Par « interruption de la grossesse » on entend : […] d’une part l’interruption volontaire (IVG) : articles L.2212-1 et suivants, R.2212-1 et suivants du code de la santé publique (CSP) ; […] d’autre part l’interruption pour motif médical (IMG) […] : articles L.2213-1 et suivants, R.2213-1 et suivants du CSP. »

*Aucune association.* Le guide ne nomme ici aucun code : en attribuer supposerait de **choisir** des cibles que le texte ne donne pas.

### GM2026-V-ITG-02 — `regle_position`

**Situation** : IVG non compliquée — DP parmi trois codes

**Texte** : Le codage des IVG non compliquées repose sur la présence en DP de l'un des trois codes : O04.90 (IVG dans le cadre légal, complet ou sans précision, sans complication), O07.4 (échec d'une tentative d'avortement médical sans complication) ou O07.9 (échec d'une tentative d'avortement, autres et sans précision, sans complication). Z64.0 ne sera plus recherché pour l'orientation dans la racine 14Z08Z. L'acte est JNJD002 ou JNJP001 (JNJD002 reste codé pour une technique chirurgicale entre 14 et 16 SA, il permet l'orientation dans les forfaits ad hoc). La date des dernières règles est enregistrée.

**Condition** : IVG non compliquée

**Citation** (`interruption_grossesse.md` L19-29) :
« Le codage des IVG non compliquées repose sur la présence en DP de l’un des 3 codes suivants : […] O04.90, interruption volontaire de grossesse (IVG dans le cadre légal), complet ou sans précision, sans complication […] O07.4 Echec d’une tentative d’avortement médical sans complication […] O07.9 Echec d’une tentative d’avortement, autres et sans précision, sans complication […] Le code Z640 Difficultés liées à une grossesse non désirée ne sera plus recherché pour l’orientation dans la racine 14Z08Z. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `O04.90` | `DP` | sujet | chaque | IVG non compliquée |
| `O07.4` | `DP` | sujet | chaque | IVG non compliquée |
| `O07.9` | `DP` | sujet | chaque | IVG non compliquée |
| `Z64.0` | `regi` | sujet | chaque | plus recherché pour l'orientation 14Z08Z |

### GM2026-V-ITG-03 — `definition`

**Situation** : IVG médicamenteuse — RUM unique, dates conventionnelles

**Texte** : Dans le cas de l'IVG médicamenteuse, un RUM unique est produit ; il mentionne par convention des dates d'entrée et de sortie égales à la date de la consultation de délivrance du médicament abortif, que la prise en charge ait été limitée à cette consultation ou qu'elle ait compris l'ensemble des étapes (délivrance, prise de prostaglandine et surveillance de l'expulsion, consultation de contrôle).

**Condition** : IVG médicamenteuse

**Citation** (`interruption_grossesse.md` L31) :
« Dans le cas de l’IVG médicamenteuse, on rappelle qu’un résumé d’unité médicale (RUM) unique doit être produit. Il doit mentionner par convention des dates d’entrée et de sortie égales à la date de la consultation de délivrance du médicament abortif »

*Aucune association.* Le guide ne nomme ici aucun code : en attribuer supposerait de **choisir** des cibles que le texte ne donne pas.

### GM2026-V-ITG-04 — `regle_position`

**Situation** : IVG — complication au cours du séjour même

**Texte** : Une complication survenant au cours du séjour même de l'IVG est codée par le quatrième caractère du code O04.– ; le cas échéant, un code de la catégorie O08 en position de diagnostic associé peut identifier la nature de la complication. La date des dernières règles est enregistrée.

**Condition** : Complication au cours du séjour de l'IVG

**Citation** (`interruption_grossesse.md` L35) :
« 1°) Lorsqu’une complication survient au cours du séjour même de l’IVG, celle-ci est codée par le quatrième caractère du code O04.–. Le cas échéant, un code de la catégorie O08 Complications consécutives à un avortement, une grossesse extra-utérine et molaire en position de diagnostic associé peut identifier la nature de la complication »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `O04` | `regi` | sujet | chaque | complication codée par le quatrième caractère |
| `O08` | `DAS` | sujet | chaque | identification de la nature de la complication |

### GM2026-V-ITG-05 — `regle_position`

**Situation** : IVG — réhospitalisation pour complication

**Texte** : Lorsqu'une complication donne lieu à une réhospitalisation après le séjour d'IVG : avortement incomplet avec rétention simple non compliquée → DP O04.4 (acte JNMD001, date des dernières règles) ; avortement incomplet avec rétention compliquée, ou autre complication → DP dans la catégorie O08, actes du traitement de la complication enregistrés.

**Condition** : Réhospitalisation après le séjour d'IVG

**Citation** (`interruption_grossesse.md` L37-40) :
« 2°) Lorsqu’une complication donne lieu à une réhospitalisation après le séjour d’IVG, deux cas doivent être distingués : […] le DP est codé O04.4 Avortement médical incomplet, sans complication, […] le DP est un code de la catégorie O08 Complications consécutives à un avortement, une grossesse extra-utérine et molaire ; »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `O04.4` | `DP` | sujet | chaque | avortement incomplet, rétention simple non compliquée |
| `O08` | `DP` | sujet | chaque | rétention compliquée ou autre complication |

### GM2026-V-ITG-06 — `regle_position`

**Situation** : Échec d'IVG — DP dans O07

**Texte** : On parle d'échec d'IVG devant le constat d'une poursuite de la grossesse, généralement après une IVG médicamenteuse ; il conduit à pratiquer une IVG instrumentale. Le DP est un code de la catégorie O07 Échec d'une tentative d'avortement, l'acte est JNJD002, la date des dernières règles est enregistrée.

**Condition** : Poursuite de la grossesse après IVG

**Citation** (`interruption_grossesse.md` L44-48) :
« On parle d'échec d’IVG devant le constat d’une poursuite de la grossesse. […] le DP est un code de la catégorie O07 Échec d'une tentative d'avortement ; »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `O07` | `DP` | sujet | chaque | échec d'IVG (poursuite de la grossesse) |

### GM2026-V-ITG-07 — `regle_position`

**Situation** : IMG avant 22 SA — avortement

**Texte** : L'IMG avant vingt-deux semaines révolues d'aménorrhée se code comme un avortement : DP O04.–1, O04.–2 ou O04.–3 (selon la cause : embryonnaire/fœtale, maternelle, ou association de causes). En DA, le motif de l'IMG : le code ad hoc du chapitre XV s'il y est classé (en particulier la catégorie O35, dont la note d'inclusion ne s'oppose pas à la mention conjointe à un code d'avortement) ou un code des catégories O98 ou O99, précisé si besoin par un code des chapitres I à XVII et XIX. Acte d'interruption de grossesse et date des dernières règles enregistrés.

**Condition** : IMG avant 22 semaines d'aménorrhée révolues

**Citation** (`interruption_grossesse.md` L56-60) :
« On code un avortement : DP O04.-1 ; ou O04.-2 ou O04.-3 […] DA : on enregistre le motif de l’IMG ; selon qu’il est classé dans le chapitre XV de la CIM–10 ou dans un autre chapitre, on choisit le code ad hoc du chapitre XV (en particulier dans la catégorie O35 (Soins maternels pour anomalies et lésions fœtales, connues ou présumées) […] ou un code des catégories O98 ou O99, précisé si besoin par un code des chapitres I à XVII et XIX »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `O04.-1` | `DP` | sujet | chaque | cause embryonnaire ou fœtale |
| `O04.-2` | `DP` | sujet | chaque | cause maternelle |
| `O04.-3` | `DP` | sujet | chaque | association de causes |
| `O35` | `DAS` | sujet | chaque | motif de l'IMG classé au chapitre XV |
| `O98` | `DAS` | sujet | chaque | motif de l'IMG hors chapitre XV |
| `O99` | `DAS` | sujet | chaque | motif de l'IMG hors chapitre XV |

### GM2026-V-ITG-08 — `regle_position`

**Situation** : IMG à partir de 22 SA — accouchement

**Texte** : L'IMG à partir de vingt-deux semaines révolues d'aménorrhée est un accouchement. Cause fœtale : DP dans la catégorie O35 ; DA par convention un code étendu de la catégorie Z37 (en général Z37.11 Naissance unique, enfant mort-né, à la suite d'une IMG) ; acte d'accouchement ; âge gestationnel et date des dernières règles. Cause maternelle : DP au code ad hoc du chapitre XV ou dans O98/O99, pas de DR ; DA Z37 (en général Z37.11), précision par un code des chapitres I à XVII et XIX si besoin ; acte d'accouchement ; âge gestationnel et date des dernières règles.

**Condition** : IMG à partir de 22 semaines d'aménorrhée révolues

**Citation** (`interruption_grossesse.md` L62-78) :
« C’est un accouchement. Le codage diffère selon que le motif de l’interruption est fœtal ou maternel. […] Si la cause est une anomalie fœtale : […] DP : un code de la catégorie O35 ; […] DA : on enregistre par convention un code étendu de la catégorie Z37 Résultat de l’accouchement […] Si la cause de l’interruption est maternelle : […] on choisit le code ad hoc du chapitre XV ou un code des catégories O98 ou O99 ; pas de DR ; »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `O35` | `DP` | sujet | chaque | IMG ≥ 22 SA, cause fœtale |
| `O98` | `DP` | sujet | chaque | IMG ≥ 22 SA, cause maternelle hors chapitre XV |
| `O99` | `DP` | sujet | chaque | IMG ≥ 22 SA, cause maternelle hors chapitre XV |
| `Z37` | `DAS` | sujet | chaque | par convention, code étendu (résultat de l'accouchement) |
| `Z37.11` | `regi` | **exemple** | chaque |  |

### GM2026-V-ITG-09 — `regle_position`

**Situation** : Produits d'IMG ≥ 22 SA ou 500 g — RUM, DP P95

**Texte** : Les produits d'IMG à partir de vingt-deux semaines révolues d'aménorrhée ou d'un poids d'au moins cinq-cents grammes donnent lieu à la production d'un RUM par convention ; le DP est codé P95.–.

**Condition** : Produit d'IMG ≥ 22 SA ou ≥ 500 g

**Citation** (`interruption_grossesse.md` L80) :
« Les produits d’IMG à partir de vingt-deux semaines révolues d’aménorrhée ou d’un poids d’au moins cinq-cents grammes donnent lieu à la production d’un RUM par convention, le DP est codé P95. –. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `P95` | `DP` | sujet | chaque | produit d'IMG ≥ 22 SA ou ≥ 500 g |

