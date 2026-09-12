# Chantier « registre des formulations » — récap (2026-09-07 → 2026-09-09)

**Branche** `feat/registre-formulations` (depuis `main` post-palier 3
couverture ATIH, mergé en préalable sur accord). **Statut : livré, en
attente de l'accord de merge de RF.** Prompt de commande archivé :
`2026-09-07_prompt_chantier_registre_formulations.md`.

Objectif : écarter de la section « Formulations cliniques
alternatives » les formulations de registre archaïque (vocabulaire de
certificat de décès, terminologie désuète) qui dégradent la qualité
des fiches pour la génération. Cas d'école : le nuage « apoplexie »
d'I64.

## Phase 1 — liste candidate (2026-09-07)

`scripts/explore/relectures/export_relecture_registre_formulations.py`
(v1) : 43 sondes lexicales jugées sur la **forme rendue** (ce que le
lecteur de la fiche voit), signal d'isolement en qualificatif, gardes
contextuelles à périmètre par code. **157 candidates** (122 ecarter /
35 garder proposés) ; 103 entrées d'Index à sonde déjà écartées par R3,
non listées. Support xlsx à deux feuilles pour la relecture.

## Verdict RF (2026-09-09, complété le 2026-09-12)

**135 écartées / 22 gardées** au verdict initial, ligne à ligne dans
le xlsx (CSV synchronisé). 15 verdicts ont corrigé les propositions —
dont croup, « paralysie générale » et « lichen scrofulosorum »
écartés.

Deux lignes signalées à RF, tranchées le 2026-09-12 (**bilan final :
136 écartées / 21 gardées**) :

- **F03 « démence précoce » : gardée, décision explicite.** Lecture
  moderne « démence à début précoce », vivante en gériatrie, qui prime
  sur l'origine kraepelinienne probable de la ligne CepiDc.
- **B94.8 « séquelles croup » : écartée** (correction du verdict
  initial). Le mot « croup » est vivant (laryngite pédiatrique, J05.0),
  mais cette formulation-ci est du registre diphtérique de certificat
  de décès. Entrée ajoutée au YAML avec ce motif.

Témoins dorés mis à jour en conséquence : croup écarté partout
(A36.0, J05.0, B94.8), et F03 « démence précoce » gardée / « sénilité
mentale » écartée sur le même code.

## Phase 2 — implémentation

| Volet | Livrable |
|---|---|
| Famille d'exclusion déclarée | `referentials/curation/registre_formulations.yaml` — 135 entrées `(code, source, texte)` forme source exacte, motif, validation RF datée |
| Chargement | `recode_icd/registre_formulations.py` : `load_registre` (via `cards.charge_politique`) ; entrée OFS/ANS refusée bruyamment (`PolicyError`) ; fichier absent → registre inerte |
| Point d'application | `cards._candidates_formulations`, avant R3, sur la forme source — couvre toutes les familles de la section, **LLM comprise** (fixture, patron du flag `generation_llm`) |
| Tests | +10 : unitaires (chargement, refus OFS/ANS, fixture LLM, formulation entière) et témoins (paires écartée/gardée à même sonde — tabès sur A52.1, croup A36.0/B94.8 ; fiche I64 avant/après ; hors-Formulations byte-identique ; ancrage des 135 entrées sur le CSV). **869 verts** (859 en référence post-palier 3) |
| Re-mesure | `scripts/explore/mesure_registre_formulations.py` → `docs/analyses/2026-09-09_registre_formulations_re_mesure.md` + `_fiches_a_completer.csv` |
| Doc | CLAUDE.md : sous-section « Registre des formulations écartées », pitfall 4 « sonde ≠ verdict », commandes |

## Chiffres

133 formulations retirées (post-dédup) de 66 fiches (après le
complément du 2026-09-12). Par source : CepiDc 74, Index 58, AP-HP
Dermatologie 4. Chapitres de tête : V 41, IX 18, VI 16, X 12, XVIII
11, IV 10. **Sections vidées : E00.0, E00.2, H65.9 ; réduites à ≤2 :
E00.1, E00.9, I64 (8→1, reste « accident vasculaire cérébral SAI »),
F44.5, J31.1** — ces 8 fiches sont l'entrée du chantier synonymes LLM
(B94.8 garde 80+ formulations CepiDc, sa section ne bouge pas de
liste).

## Décisions consignées

1. La sonde se juge sur la **forme rendue** ; le filtre s'applique sur
   la **forme source** (avant R3) — deux moments, deux formes, et c'est
   cohérent : on juge ce qui se voit, on identifie ce qui est auditable.
2. Granularité `(code, source, texte)` : une formulation écartée sur un
   code ne l'est pas ailleurs sans verdict.
3. Le registre est né après les bibliothèques : fichier absent =
   filtre inerte (contextes de test minimaux), jamais d'erreur.
4. Les 22 gardées ne sont pas au YAML : la trace de leur validation est
   le support de relecture committé (v1, verdicts inclus).

## Dette et suites

- **Chantier synonymes LLM** : partir de
  `2026-09-09_registre_formulations_fiches_a_completer.csv` (E00 en
  tête — tout son lexique Index était archaïque).
- Si R3 s'assouplit, re-passer les sondes (103 entrées à sonde
  actuellement neutralisées par R3) — `VERSION_REGLE` à incrémenter.
- Bibliothèques `generation`, `controle` et catégories régénérées après
  filtre (commit d'artefacts séparé, `_index.csv`).

Merge dans `main` sur accord explicite de RF.
