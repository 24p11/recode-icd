# Registre des formulations — re-mesure après filtre (2026-09-09)

**Chantier « registre des formulations »**, branche
`feat/registre-formulations`. Verdict ligne à ligne de RF du 2026-09-09
sur 157 candidates (support :
`scripts/explore/relectures/relecture_registre_formulations_v1.{csv,xlsx}`) :
**135 écartées, 22 gardées**. La liste validée vit dans
`referentials/curation/registre_formulations.yaml`, consommée par
l'assemblage des fiches (`cards._candidates_formulations`, avant R3) au
même titre que les règles de la chapter_policy. Le CSV maître est
intouché. Mesure produite par
`scripts/explore/mesure_registre_formulations.py` (le vrai chemin de
code, avec puis sans registre).

## Volumétrie des écartées

Par source : **CepiDc 73**, **Index vol3 58**, **AP-HP Dermatologie 4**
(« Mongolisme », « Trisomie 21 (mongolisme) », « Naevus mongolien »,
« Tache mongolique »). OFS et ANS ne sont jamais filtrés (refus au
chargement, testé).

Par chapitre — l'archaïsme se concentre où on l'attendait : **V : 41**
(le nuage hystérie/F44 et l'hébéphrénie écartée au profit des seules
formes gardées), **IX : 18** (apoplexie d'I64, ramollissements),
**VI : 16** (ramollissement cérébral, sénilité), **X : 12** (catarrhes,
croup), **XVIII : 11** (misère physiologique, consomption, gâtisme),
**IV : 10** (crétinisme, athrepsie), **I : 9** (croup, scrofule,
paralysie générale). Queue : VIII 3, XI 5, XV-XVII 8, II/III 2.

Sur les 135 écartées, **132 formulations disparaissent effectivement**
des sections (post-dédup) de **65 fiches**. Témoins dorés (mêmes sondes,
verdicts opposés — le partage est clinicien, pas lexical) : « maladie
tabès » s'écarte, « tabès syphilitique » se garde (A52.1) ; « croup »
s'écarte (A36.0, J05.0), « séquelles croup » se garde (B94.8).

## Fiches à compléter — l'entrée du chantier synonymes LLM

`2026-09-09_registre_formulations_fiches_a_completer.csv` (même
répertoire) liste les **8 fiches** dont la section Formulations est
vidée ou réduite à ≤ 2 après filtre. Ce sont les trous de couverture
réels : des codes dont le seul lexique alternatif disponible était
archaïque, et où le langage vivant du CRH n'a plus de témoin.

| Code | Fiche | Avant → après |
|---|---|---|
| E00.0 | Syndrome d'insuffisance thyroïdienne congénitale, type neuro. | 1 → **0** |
| E00.2 | — type mixte | 1 → **0** |
| H65.9 | Otite moyenne non suppurée, sans précision | 2 → **0** |
| E00.1 | — type myxoedémateux | 3 → 1 |
| E00.9 | — sans précision | 3 → 1 |
| I64 | AVC, non précisé (le cas d'école du chantier) | 8 → 1 |
| F44.5 | Convulsions dissociatives | 4 → 2 |
| J31.1 | Rhinopharyngite chronique | 3 → 2 |

Lecture : la famille E00 (crétinisme) perd tout son lexique Index —
c'est le candidat le plus net à une génération LLM de formulations
vivantes (« hypothyroïdie congénitale sévère »…). I64 garde
« accident vasculaire cérébral SAI » (AP-HP), exactement l'objectif du
chantier : le nuage apoplexie disparaît, le terme vivant reste.

## Ce que la re-mesure ne couvre pas

Les fiches **catégories** agrègent leurs feuilles : aucune section de
catégorie ne se vide (vérifié par le rebuild). Les 103 entrées d'Index
portant une sonde mais déjà écartées par R3 (renvois, `nca`…)
n'atteignent pas les fiches et ne sont pas au registre — si R3
s'assouplit un jour, la re-passe des sondes est à refaire
(`export_relecture_registre_formulations.py`, `VERSION_REGLE` à
incrémenter).
