# Statistiques du CSV maître

> Rapport déterministe généré par `recode_icd.reports.csv_stats.generate_csv_stats` (commande `recode-icd build stats`). Aucune observation interprétative — uniquement des chiffres bruts.

- **Généré le** : 2026-05-28
- **Lignes totales** : 214675
- **Codes uniques** : 15978
- **Moyenne notes/code** : 13.4

## Distribution par source

| source | lignes | % |
|---|---:|---:|
| CIM-10 | 77729 | 36.2 % |
| ANS | 64340 | 30.0 % |
| CIM-10 index | 44305 | 20.6 % |
| ORPHANET | 18410 | 8.6 % |
| CIM-10 frères | 5359 | 2.5 % |
| AP-HP Dermatologie | 1667 | 0.8 % |
| AP-HP Rhumatologie | 836 | 0.4 % |
| AP-HP Néphrologie | 691 | 0.3 % |
| AP-HP Ophtalmologie | 371 | 0.2 % |
| AP-HP Endocrinologie | 358 | 0.2 % |
| AP-HP Troubles métaboliques | 235 | 0.1 % |
| AP-HP Germes (SPILF) | 199 | 0.1 % |
| AP-HP GRONES | 125 | 0.1 % |
| AP-HP SRLF | 50 | 0.0 % |

## Distribution par type

| type | lignes | % |
|---|---:|---:|
| exclusion | 92944 | 43.3 % |
| synonyme | 75521 | 35.2 % |
| inclusion | 46210 | 21.5 % |

## Croisé source × type

| source | total | synonyme | inclusion | exclusion |
|---|---:|---:|---:|---:|
| CIM-10 | 77729 | 9422 (12.1 %) | 14224 (18.3 %) | 54083 (69.6 %) |
| ANS | 64340 | 15867 (24.7 %) | 14971 (23.3 %) | 33502 (52.1 %) |
| CIM-10 index | 44305 | 44305 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| ORPHANET | 18410 | 1395 (7.6 %) | 17015 (92.4 %) | 0 (0.0 %) |
| CIM-10 frères | 5359 | 0 (0.0 %) | 0 (0.0 %) | 5359 (100.0 %) |
| AP-HP Dermatologie | 1667 | 1667 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Rhumatologie | 836 | 836 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Néphrologie | 691 | 691 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Ophtalmologie | 371 | 371 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Endocrinologie | 358 | 358 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Troubles métaboliques | 235 | 235 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Germes (SPILF) | 199 | 199 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP GRONES | 125 | 125 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP SRLF | 50 | 50 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |

## Distribution par source_level

| source_level | lignes | % |
|---|---:|---:|
| code | 109885 | 51.2 % |
| block | 45453 | 21.2 % |
| category | 43291 | 20.2 % |
| chapter | 16046 | 7.5 % |

## Quantiles du nombre de notes par code

| min | p25 | médiane | p75 | p90 | p95 | p99 | max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6 | 10 | 15 | 23 | 30 | 69 | 2478 |

## Codes dépassant 100 notes

90 code(s) concerné(s).

| code | libellé | notes |
|---|---|---:|
| A52.7 | Autres formes tardives de syphilis symptomatique | 2478 |
| Q87.8 | Autres syndromes congénitaux malformatifs précisés, non classés ailleurs | 1215 |
| A52.1 | Syphilis nerveuse symptomatique | 1199 |
| A18.1 | Tuberculose de l'appareil génito-urinaire | 954 |
| A52.0 | Syphilis cardiovasculaire | 710 |
| A18.0 | Tuberculose des os et des articulations | 640 |
| A18.8 | Tuberculose d'autres organes précisés | 602 |
| E74.0 | Thésaurismose glycogénique | 580 |
| M32.1 | Lupus érythémateux disséminé avec atteinte d'organes et d'appareils | 520 |
| A54.8 | Autres infections gonococciques | 448 |
| Q82.8 | Autres malformations congénitales précisées de la peau | 433 |
| Q93.5 | Autres délétions partielles d'un chromosome | 419 |
| A51.4 | Autres formes de syphilis secondaire | 384 |
| G71.0 | Dystrophie musculaire | 379 |
| Q87.0 | Syndromes congénitaux malformatifs atteignant principalement l'aspect de la face | 365 |
| E77.8 | Autres anomalies du métabolisme des glycoprotéines | 345 |
| E88.8 | Autres anomalies métaboliques précisées | 295 |
| D86.8 | Sarcoïdose de localisations autres et associées | 294 |
| G60.0 | Neuropathie héréditaire motrice et sensorielle | 275 |
| Q92.3 | Trisomie partielle mineure | 261 |
| G11.4 | Paraplégie spastique héréditaire | 245 |
| Q87.1 | Syndromes congénitaux malformatifs associés principalement à une petite taille | 237 |
| E75.2 | Autres sphingolipidoses | 228 |
| A18.5 | Tuberculose de l'œil | 204 |
| G05.1 | Encéphalite, myélite et encéphalomyélite au cours d'infections virales classées ailleurs | 204 |
| G01 | Méningite au cours d'affections bactériennes classées ailleurs | 192 |
| Q04.3 | Autres anomalies localisées du développement de l'encéphale | 185 |
| A50.4 | Syphilis congénitale nerveuse tardive [neurosyphilis juvénile] | 177 |
| H35.5 | Dystrophie rétinienne héréditaire | 174 |
| Q87.2 | Syndromes congénitaux malformatifs impliquant principalement les membres | 173 |
| M35.0 | Syndrome de Gougerot–Sjögren | 172 |
| G63.3 | Polynévrite au cours d'autres maladies endocriniennes et métaboliques  | 170 |
| A54.2 | Pelvipéritonite gonococcique et autres infections génito-urinaires gonococciques | 162 |
| E72.0 | Anomalies du transport des acides aminés | 162 |
| G63.0 | Polynévrite au cours de maladies infectieuses et parasitaires classées ailleurs | 162 |
| I64 | Accident vasculaire cérébral, non précisé comme étant hémorragique ou par infarctus | 161 |
| G71.2 | Myopathies congénitales | 154 |
| Q78.8 | Autres ostéo-chondro-dysplasies précisées | 153 |
| E71.3 | Anomalie du métabolisme des acides gras | 151 |
| D84.8 | Autres déficits immunitaires précisés | 150 |
| E71.1 | Autres anomalies du métabolisme des acides aminés à chaine ramifiée | 146 |
| A36.8 | Autres formes de diphtérie | 145 |
| Q99.8 | Autres anomalies précisées des chromosomes | 145 |
| A50.5 | Autres formes tardives de syphilis congénitale, symptomatique | 144 |
| G11.1 | Ataxie cérébelleuse à début précoce | 138 |
| B00.5 | Affections oculaires dues au virus de l'herpès | 136 |
| A39.8 | Autres infections à méningocoques | 135 |
| G12.2 | Maladies du neurone moteur | 134 |
| M36.3 | Arthropathie au cours d'autres maladies du sang classées ailleurs  | 132 |
| H13.1 | Conjonctivite au cours de maladies infectieuses et parasitaires classées ailleurs | 130 |
| H18.5 | Dystrophies cornéennes héréditaires | 129 |
| A18.3 | Tuberculose de l'intestin, du péritoine et des ganglions mésentériques | 128 |
| E10.4 | Diabète sucré de type 1 - " Avec complications neurologiques " | 128 |
| E13.4 | Autres diabètes sucrés précisés - " Avec complications neurologiques " | 128 |
| E53.8 | Autres avitaminoses précisées du groupe B | 128 |
| G40.3 | Épilepsie et syndromes épileptiques généralisés idiopathiques | 128 |
| D89.1 | Cryoglobulinémie | 126 |
| B02.3 | Zona ophtalmique | 125 |
| E23.0 | Hypopituitarisme | 125 |
| E14.4 | Diabète sucré, sans précision - " Avec complications neurologiques " | 124 |
| Q79.6 | Syndrome d'Ehlers–Danlos | 122 |
| G31.8 | Autres affections dégénératives précisées du système nerveux | 121 |
| H19.2 | Kératite et kératoconjonctivite au cours d'autres maladies infectieuses et parasitaires classées ailleurs | 120 |
| D81.8 | Autres déficits immunitaires combinés | 118 |
| E76.2 | Autres mucopolysaccharidoses | 118 |
| P03.1 | Fœtus et nouveau-né affectés par d'autres présentations et positions vicieuses du fœtus et disproportions fœtopelviennes au cours du travail et de l'accouchement | 118 |
| E70.3 | Albinisme | 117 |
| G02.0 | Méningite au cours d'infections virales classées ailleurs | 117 |
| A54.4 | Infection gonococcique du système ostéoarticulaire et des muscles | 116 |
| A60.0 | Infection des organes génitaux et de l'appareil génito-urinaire par le virus de l'herpès | 116 |
| T85.8 | Autres complications de prothèses, implants et greffes internes, non classées ailleurs | 116 |
| C56 | Tumeur maligne de l'ovaire | 114 |
| N50.8 | Autres affections précisées des organes génitaux de l'homme | 114 |
| B26.8 | Oreillons avec autres complications | 112 |
| E12.4 | Diabète sucré de malnutrition - " Avec complications neurologiques " | 112 |
| E72.8 | Autres anomalies précisées du métabolisme des acides aminés | 112 |
| G60.8 | Autres neuropathies héréditaires et idiopathiques | 112 |
| M36.1 | Arthropathie au cours de maladies tumorales classées ailleurs | 112 |
| N08.0 | Glomérulopathie au cours de maladies infectieuses et parasitaires classées ailleurs | 112 |
| G11.8 | Autres ataxies héréditaires | 111 |
| Q68.8 | Autres anomalies morphologiques congénitales ostéoarticulaires et des muscles précisées | 109 |
| Q77.7 | Dysplasie spondyloépiphysaire | 109 |
| Q82.4 | Dysplasie ectodermique (anhidrotique) | 109 |
| A01.0 | Fièvre typhoïde | 108 |
| N16.1 | Maladie rénale tubulo-interstitielle au cours de maladies tumorales | 108 |
| O65.5 | Dystocie due à une anomalie des organes pelviens de la mère | 108 |
| G40.4 | Autres épilepsies et syndromes épileptiques généralisés | 107 |
| Q04.8 | Autres malformations congénitales précisées de l'encéphale | 106 |
| Q74.0 | Autres malformations congénitales d'un (des) membre(s) supérieur(s), y compris la ceinture scapulaire | 103 |
| M45 | Spondylarthrite ankylosante | 102 |
