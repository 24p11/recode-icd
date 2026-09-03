# Candidates — ENFANTS NÉS SANS VIE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/enfants_nes_sans_vie.md`
> (guide chap. V, pp. imprimées 92-93). Les `L…` y renvoient.

**4 consignes, 1 associations**.

---

## Consignes nouvelles

### GM2026-V-ENF-01 — `definition`

**Situation** : Enfant né sans vie ou produit d'IMG — seuils de production du RUM

**Texte** : Les enfants nés sans vie (« mort-nés ») et les produits d'interruption de grossesse pour motif médical (IMG) donnent lieu à la production d'un RUM à partir de vingt-deux semaines révolues d'aménorrhée ou d'un poids d'au moins cinq-cents grammes. Référence : note technique en annexe 2 de l'instruction N° DREES/BES/DGS/SP1/DGOS/R3/2021/148 du 21 juin 2021.

**Condition** : —

**Citation** (`enfants_nes_sans_vie.md` L10-12) :
« Les enfants nés sans vie et les produits d’interruption de grossesse pour motif médical (IMG) donnent lieu à la production d’un résumé d’unité médicale (RUM) […] à partir de vingt- deux semaines révolues d’aménorrhée ou d’un poids d’au moins cinq-cents grammes. »

*Aucune association.* Le guide ne nomme ici aucun code : en attribuer supposerait de **choisir** des cibles que le texte ne donne pas.

### GM2026-V-ENF-02 — `regle_position`

**Situation** : Enfant né sans vie — DP = P95, à l'exclusion de tout autre

**Texte** : Le diagnostic principal du RUM d'un enfant né sans vie emploie le code P95, à l'exclusion de tout autre, y compris, par convention, si la cause du décès est connue. Le RUM-RSS enregistre l'âge gestationnel et la cause de la mort ; les codes des actes éventuels, en particulier l'autopsie, sont saisis dans le RUM.

**Condition** : —

**Citation** (`enfants_nes_sans_vie.md` L14) :
« L’enregistrement du diagnostic principal doit employer le code P95 de la CIM–10, à l’exclusion de tout autre, y compris, par convention, si la cause du décès est connue. Le RUM-RSS enregistre l’âge gestationnel (se reporter au chapitre I), la cause de la mort. Les codes des actes éventuels, en particulier celui d’autopsie, sont saisis dans le RUM. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `P95` | `DP` | sujet | chaque | enfant né sans vie |

### GM2026-V-ENF-03 — `definition`

**Situation** : Autopsie d'un enfant né sans vie ou d'un fœtus — RUM porteur de l'acte

**Texte** : L'acte d'autopsie réalisé sur un enfant né sans vie ou sur un fœtus est codé dans le RUM de l'enfant lorsqu'il en est produit (à partir de vingt-deux semaines révolues d'aménorrhée ou d'un poids d'au moins cinq-cents grammes), et dans le RUM de la mère lorsqu'il ne doit pas être produit de RUM (issue de grossesse avant ces seuils).

**Condition** : —

**Citation** (`enfants_nes_sans_vie.md` L16-19) :
« Lorsqu’un acte d’autopsie est réalisé sur un enfant né sans vie ou sur un fœtus, l’acte est codé : […] dans le RUM de l’enfant lorsqu’il en est produit […] dans le RUM de la mère s’il ne doit pas être produire de RUM, c’est-à-dire pour une issue de grossesse avant vingt-deux semaines révolues d’aménorrhée et d’un poids de moins de cinq-cents grammes. »

*Aucune association.* Le guide ne nomme ici aucun code : en attribuer supposerait de **choisir** des cibles que le texte ne donne pas.

### GM2026-V-ENF-04 — `definition`

**Situation** : Mort-né hors établissement — production du RSS

**Texte** : En cas de naissance d'un enfant mort-né hors d'un établissement de santé (domicile, maison de naissance), un RSS est produit si la mère est hospitalisée. Un RSS est produit lorsque la naissance est assurée par un SMUR, quel que soit son établissement d'implantation.

**Condition** : —

**Citation** (`enfants_nes_sans_vie.md` L23) :
« En cas de naissance d’un enfant mort-né hors d’un établissement de santé (domicile ou maison de naissance) un RSS devra être produit si la mère est hospitalisée. Un RSS est produit lor sque la naissance est assurée par un service mobile d’urgence et de réanimation, quel que soit son établissement d’implantation. »

*Aucune association.* Le guide ne nomme ici aucun code : en attribuer supposerait de **choisir** des cibles que le texte ne donne pas.

