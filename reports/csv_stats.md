# Statistiques du CSV maître

> Rapport déterministe généré par `recode_icd.reports.csv_stats.generate_csv_stats` (commande `recode-icd build stats`). Aucune observation interprétative — uniquement des chiffres bruts.

- **Généré le** : 2026-05-30
- **Lignes totales** : 199970
- **Codes uniques** : 15978
- **Moyenne notes/code** : 12.5

## Distribution par source

| source | lignes | % |
|---|---:|---:|
| CIM-10 | 74105 | 37.1 % |
| ANS | 62365 | 31.2 % |
| CIM-10 index | 36627 | 18.3 % |
| ORPHANET | 17989 | 9.0 % |
| CIM-10 frères | 5031 | 2.5 % |
| AP-HP Dermatologie | 1551 | 0.8 % |
| AP-HP Rhumatologie | 617 | 0.3 % |
| AP-HP Néphrologie | 565 | 0.3 % |
| AP-HP Ophtalmologie | 281 | 0.1 % |
| AP-HP Endocrinologie | 263 | 0.1 % |
| AP-HP Troubles métaboliques | 221 | 0.1 % |
| AP-HP Germes (SPILF) | 193 | 0.1 % |
| AP-HP GRONES | 117 | 0.1 % |
| AP-HP SRLF | 45 | 0.0 % |

## Distribution par type

| type | lignes | % |
|---|---:|---:|
| exclusion | 90631 | 45.3 % |
| synonyme | 64504 | 32.3 % |
| inclusion | 44835 | 22.4 % |

## Croisé source × type

| source | total | synonyme | inclusion | exclusion |
|---|---:|---:|---:|---:|
| CIM-10 | 74105 | 7123 (9.6 %) | 13868 (18.7 %) | 53114 (71.7 %) |
| ANS | 62365 | 15567 (25.0 %) | 14312 (22.9 %) | 32486 (52.1 %) |
| CIM-10 index | 36627 | 36627 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| ORPHANET | 17989 | 1334 (7.4 %) | 16655 (92.6 %) | 0 (0.0 %) |
| CIM-10 frères | 5031 | 0 (0.0 %) | 0 (0.0 %) | 5031 (100.0 %) |
| AP-HP Dermatologie | 1551 | 1551 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Rhumatologie | 617 | 617 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Néphrologie | 565 | 565 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Ophtalmologie | 281 | 281 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Endocrinologie | 263 | 263 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Troubles métaboliques | 221 | 221 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Germes (SPILF) | 193 | 193 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP GRONES | 117 | 117 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP SRLF | 45 | 45 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |

## Distribution par source_level

| source_level | lignes | % |
|---|---:|---:|
| code | 97624 | 48.8 % |
| block | 44301 | 22.2 % |
| category | 42705 | 21.4 % |
| chapter | 15340 | 7.7 % |

## Quantiles du nombre de notes par code

| min | p25 | médiane | p75 | p90 | p95 | p99 | max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6 | 10 | 15 | 22 | 29 | 58 | 1215 |

## Codes dépassant 100 notes

50 code(s) concerné(s).

| code | libellé | notes |
|---|---|---:|
| Q87.8 | Autres syndromes congénitaux malformatifs précisés, non classés ailleurs | 1215 |
| Q82.8 | Autres malformations congénitales précisées de la peau | 433 |
| Q93.5 | Autres délétions partielles d'un chromosome | 419 |
| G71.0 | Dystrophie musculaire | 379 |
| Q87.0 | Syndromes congénitaux malformatifs atteignant principalement l'aspect de la face | 365 |
| E77.8 | Autres anomalies du métabolisme des glycoprotéines | 345 |
| E88.8 | Autres anomalies métaboliques précisées | 295 |
| E74.0 | Thésaurismose glycogénique | 290 |
| G60.0 | Neuropathie héréditaire motrice et sensorielle | 275 |
| Q92.3 | Trisomie partielle mineure | 261 |
| G11.4 | Paraplégie spastique héréditaire | 245 |
| Q87.1 | Syndromes congénitaux malformatifs associés principalement à une petite taille | 237 |
| E75.2 | Autres sphingolipidoses | 228 |
| Q04.3 | Autres anomalies localisées du développement de l'encéphale | 185 |
| A52.7 | Autres formes tardives de syphilis symptomatique | 177 |
| H35.5 | Dystrophie rétinienne héréditaire | 174 |
| Q87.2 | Syndromes congénitaux malformatifs impliquant principalement les membres | 173 |
| G71.2 | Myopathies congénitales | 154 |
| Q78.8 | Autres ostéo-chondro-dysplasies précisées | 153 |
| E71.3 | Anomalie du métabolisme des acides gras | 151 |
| D84.8 | Autres déficits immunitaires précisés | 150 |
| E71.1 | Autres anomalies du métabolisme des acides aminés à chaine ramifiée | 146 |
| Q99.8 | Autres anomalies précisées des chromosomes | 145 |
| G11.1 | Ataxie cérébelleuse à début précoce | 138 |
| G12.2 | Maladies du neurone moteur | 134 |
| H18.5 | Dystrophies cornéennes héréditaires | 129 |
| A18.0 | Tuberculose des os et des articulations | 128 |
| G40.3 | Épilepsie et syndromes épileptiques généralisés idiopathiques | 128 |
| E23.0 | Hypopituitarisme | 125 |
| Q79.6 | Syndrome d'Ehlers–Danlos | 122 |
| G31.8 | Autres affections dégénératives précisées du système nerveux | 121 |
| D81.8 | Autres déficits immunitaires combinés | 118 |
| E76.2 | Autres mucopolysaccharidoses | 118 |
| P03.1 | Fœtus et nouveau-né affectés par d'autres présentations et positions vicieuses du fœtus et disproportions fœtopelviennes au cours du travail et de l'accouchement | 118 |
| E70.3 | Albinisme | 117 |
| T85.8 | Autres complications de prothèses, implants et greffes internes, non classées ailleurs | 116 |
| C56 | Tumeur maligne de l'ovaire | 114 |
| N50.8 | Autres affections précisées des organes génitaux de l'homme | 114 |
| E72.8 | Autres anomalies précisées du métabolisme des acides aminés | 112 |
| G60.8 | Autres neuropathies héréditaires et idiopathiques | 112 |
| G11.8 | Autres ataxies héréditaires | 111 |
| A52.1 | Syphilis nerveuse symptomatique | 109 |
| Q68.8 | Autres anomalies morphologiques congénitales ostéoarticulaires et des muscles précisées | 109 |
| Q77.7 | Dysplasie spondyloépiphysaire | 109 |
| Q82.4 | Dysplasie ectodermique (anhidrotique) | 109 |
| O65.5 | Dystocie due à une anomalie des organes pelviens de la mère | 108 |
| G40.4 | Autres épilepsies et syndromes épileptiques généralisés | 107 |
| A18.1 | Tuberculose de l'appareil génito-urinaire | 106 |
| Q04.8 | Autres malformations congénitales précisées de l'encéphale | 106 |
| Q74.0 | Autres malformations congénitales d'un (des) membre(s) supérieur(s), y compris la ceinture scapulaire | 103 |
