# Chantier « besoins codeur » — récap (2026-10-18)

**Sur `main`** (consigne n° 9). Prompt, brief de verdicts et recadrage
archivés (`2026-10-18_prompt_chantier_codeur.md`,
`_brief_codeur_verdicts.md`, `_recadrage_phase_b_codeur.md`). Analyse
et mesures : `docs/analyses/2026-10-18_besoins_codeur_conception.md` +
`scripts/explore/mesure_besoins_codeur.py`.

## Conception (validée RF)

Deux prémisses du prompt corrigées contre le kit : 4 des 6
« troncatures » citées sont CODABLES (→ deux régimes : correction
obligatoire / affinage proposé jamais imposé) ; « ni » n'existe pas au
kit. Fiches de navigation, découpage des catégories longues et
échantillon de relecture ANNULÉS au recadrage ; axe discriminant ClaML
au backlog avec déclencheur (`docs/backlog/axe_discriminant_claml.md`).

## Livré (phases A + B, artefacts calculés purs)

| Livrable | Contenu |
|---|---|
| `codes.csv` | 42 897 codes du kit, `code_atih` + forme pointée, `codable_mco`, statuts, millésime + version — seule source de la liste des codes |
| `descendants_codables.csv` | 19 977 couples sur 2 546 nœuds, `noeud_codable` porte le régime ; même logique que le résolveur, invariant testé export == `resoudre_code` |
| `formulations.csv` | 109 987 formulations rendues (R1/R3/registre, SANS plafond R2 — deux usages, deux coupes, même vivier) |
| `extensions_preambule.md` | généré du kit |
| `index.csv` | + `has_definition`, `has_description_clinique`, `has_notes_cim` (informatif, `format_version` = 1) |
| CONTRAT.md / guide | livrables documentés, les deux régimes, `codeur` troisième consommateur |

Réconciliation des nœuds (jamais au silence) : 2 546 = 1 848 non
codables (1 857 mesurés − 8 inconnus du kit − Z37.9, père interdit
sans aucun descendant codable) + 698 codables à descendants plus
précis (intermédiaires D2, dont 49 pères à extensions).

## Trouvaille M142 (remontée aux consommateurs et au générateur)

Le kit ne subdivise pas le 5ᵉ caractère du chapitre XIII : M1427/M1467
sont `inconnu_atih` (non codables). Les « arrondis LLM » du chapitre
XIII étaient ce symptôme — les codes de scénario se tirent de
`codes.csv` (`codable_mco=true`). Témoin inverse verrouillé ; section
dédiée dans la note nouveautés. Notebook de contre-lecture du kit :
`scripts/explore/explore_kit_atih.py`.

## Bilan des sept points du brief

| # | Attente codeur | Sort |
|---|---|---|
| 1 | Index complet, seule source des codes | **Traité (A)** : `codes.csv` |
| 2 | Fiches « utiles ou vides » | **Traité (A)** : colonnes `has_*` (marquage, jamais d'absence) |
| 3 | Navigation des nœuds non codables | **Traité (B, recadré)** : `descendants_codables.csv` + `noeud_codable` |
| 4 | Catégories longues par axe | **Différé avec déclencheur** : `docs/backlog/axe_discriminant_claml.md` |
| 5 | Explication des extensions PMSI | **Traité (A)** : `extensions_preambule.md` (généré du kit) |
| 6 | Budget de taille / profil revue | **Différé avec déclencheur** : `docs/backlog/profils_fiches_par_usage.md` § profil revue |
| 7 | Export des formulations | **Traité (A)** : `formulations.csv` (sans plafond R2) |

Différé transversal : **retrait de `_index.csv`** — déclenché par la
confirmation de bascule des consommateurs connus (CONTRAT reformulé le
2026-10-18, la note nouveautés vaut préavis formel), petit chantier
dédié le moment venu.

**Chantier CLOS le 2026-10-18** (livraison
`recode-icd_fiches_generation_65701d6_atih-2025.tar.gz`).

## Phase C

Archive groupée (profil generation, commit de fin), note
`nouveautes_fiches_2026-10-18.md` cumulative (sections notes, 43
fiches de nœud, exports, colonnes `has_*`, section M142), zip hors
canal retiré du clone. `_index.csv` encore double-écrit : le contrat
promettait son retrait à cette livraison — maintenu une livraison de
plus, signalé aux consommateurs ; **décision de retrait à prendre**
(seul point laissé ouvert). 889 tests verts.
