# Statistiques du CSV maître

> Rapport déterministe généré par `recode_icd.reports.csv_stats.generate_csv_stats` (commande `recode-icd build stats`). Aucune observation interprétative — uniquement des chiffres bruts.

- **Généré le** : 2026-09-05
- **Lignes totales** : 338623
- **Codes uniques** : 16927
- **Moyenne notes/code** : 20.0

## Distribution par source

| source | lignes | % |
|---|---:|---:|
| CepiDc 2015 | 128492 | 37.9 % |
| CIM-10 | 77676 | 22.9 % |
| ANS | 65086 | 19.2 % |
| CIM-10 index | 39262 | 11.6 % |
| ORPHANET | 18410 | 5.4 % |
| CIM-10 frères | 5402 | 1.6 % |
| AP-HP Dermatologie | 1587 | 0.5 % |
| AP-HP Rhumatologie | 986 | 0.3 % |
| AP-HP Néphrologie | 590 | 0.2 % |
| AP-HP Ophtalmologie | 281 | 0.1 % |
| AP-HP Endocrinologie | 265 | 0.1 % |
| AP-HP Troubles métaboliques | 221 | 0.1 % |
| AP-HP Germes (SPILF) | 193 | 0.1 % |
| AP-HP GRONES | 126 | 0.0 % |
| AP-HP SRLF | 46 | 0.0 % |

## Distribution par type

| type | lignes | % |
|---|---:|---:|
| synonyme | 187430 | 55.4 % |
| exclusion | 95438 | 28.2 % |
| inclusion | 55755 | 16.5 % |

## Croisé source × type

| source | total | synonyme | inclusion | exclusion |
|---|---:|---:|---:|---:|
| CepiDc 2015 | 128492 | 128492 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| CIM-10 | 77676 | 7532 (9.7 %) | 14404 (18.5 %) | 55740 (71.8 %) |
| ANS | 65086 | 6441 (9.9 %) | 24349 (37.4 %) | 34296 (52.7 %) |
| CIM-10 index | 39262 | 39262 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| ORPHANET | 18410 | 1408 (7.6 %) | 17002 (92.4 %) | 0 (0.0 %) |
| CIM-10 frères | 5402 | 0 (0.0 %) | 0 (0.0 %) | 5402 (100.0 %) |
| AP-HP Dermatologie | 1587 | 1587 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Rhumatologie | 986 | 986 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Néphrologie | 590 | 590 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Ophtalmologie | 281 | 281 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Endocrinologie | 265 | 265 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Troubles métaboliques | 221 | 221 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP Germes (SPILF) | 193 | 193 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP GRONES | 126 | 126 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |
| AP-HP SRLF | 46 | 46 (100.0 %) | 0 (0.0 %) | 0 (0.0 %) |

## Distribution par source_level

| source_level | lignes | % |
|---|---:|---:|
| code | 231304 | 68.3 % |
| block | 46004 | 13.6 % |
| category | 44885 | 13.3 % |
| chapter | 16430 | 4.9 % |

## Quantiles du nombre de notes par code

| min | p25 | médiane | p75 | p90 | p95 | p99 | max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 7 | 11 | 19 | 36 | 60 | 174 | 1269 |

## Codes dépassant 100 notes

416 code(s) concerné(s).

| code | libellé | notes |
|---|---|---:|
| Q87.8 | Autres syndromes congénitaux malformatifs précisés, non classés ailleurs | 1269 |
| C79.8 | Tumeur maligne secondaire d'autres sièges précisés | 1235 |
| S06.2 | Lésion traumatique cérébrale diffuse | 1067 |
| C85.9 | Lymphome non hodgkinien, non précisé | 1015 |
| C34.9 | Tumeur maligne de bronche ou du poumon, sans précision | 881 |
| Z92.4 | Antécédents personnels d'intervention chirurgicale importante, non classée ailleurs | 865 |
| Z92.2 | Antécédents personnels d'utilisation (actuelle) à long terme d'autres médicaments | 834 |
| Y83.1 | Intervention chirurgicale avec implantation d'une prothèse interne | 778 |
| I25.1 | Cardiopathie artérioscléreuse | 708 |
| I77.9 | Atteinte des artères et artérioles, sans précision | 708 |
| C79.5 | Tumeur maligne secondaire des os et de la moelle osseuse | 665 |
| I67.8 | Autres maladies cérébrovasculaires précisées | 662 |
| R02 | Gangrène, non classée ailleurs | 600 |
| I97.8 | Autres troubles de l'appareil circulatoire après un acte à visée diagnostique et thérapeutique, non classés ailleurs | 595 |
| I74.3 | Embolie et thrombose des artères des membres inférieurs | 582 |
| L89.9 | Ulcère de décubitus et zone de pression, sans précision | 558 |
| T82.8 | Autres complications précisées de prothèses, implants et greffes cardiaques et vasculaires | 504 |
| T81.4 | Infection après un acte à visée diagnostique et thérapeutique, non classée ailleurs | 466 |
| Q82.8 | Autres malformations congénitales précisées de la peau | 460 |
| Q93.5 | Autres délétions partielles d'un chromosome | 456 |
| C80.9 | Tumeur maligne de siège primitif non précisé | 455 |
| Y83.2 | Intervention chirurgicale avec anastomose, pontage ou greffe | 455 |
| C34.1 | Tumeur maligne du lobe supérieur, bronches ou poumon | 453 |
| C83.3 | Lymphome diffus à grandes cellules B | 449 |
| I99 | Troubles autres et non précisés de l'appareil circulatoire | 441 |
| G71.0 | Dystrophie musculaire | 429 |
| X44 | Intoxication accidentelle par des médicaments et substances biologiques et exposition à ces produits, autres et sans précision | 427 |
| C44.3 | Tumeur maligne de la peau de la face, parties autres et non précisées | 426 |
| Y83.8 | Autres interventions chirurgicales | 420 |
| X61 | Auto-intoxication par des antiépileptiques, sédatifs, hypnotiques, antiparkinsoniens et psychotropes et exposition à ces produits, non classés ailleurs | 418 |
| X64 | Auto-intoxication par des médicaments et substances biologiques et exposition à ces produits, autres et sans précision | 418 |
| T88.9 | Complication de soins chirurgicaux et médicaux, sans précision | 411 |
| Q87.0 | Syndromes congénitaux malformatifs atteignant principalement l'aspect de la face | 403 |
| L97 | Ulcère du membre inférieur, non classé ailleurs | 395 |
| K56.6 | Occlusions intestinales, autres et sans précision | 388 |
| G31.9 | Affection dégénérative du système nerveux, sans précision | 386 |
| T85.7 | Infection et réaction inflammatoire dues à d'autres prothèses, implants et greffes internes | 383 |
| G93.8 | Autres affections précisées du cerveau | 382 |
| M89.9 | Maladie osseuse, sans précision | 379 |
| T66 | Effets de rayonnements, sans précision | 371 |
| Z95.2 | Présence de prothèse d'une valvule cardiaque | 365 |
| T82.7 | Infection et réaction inflammatoire dues à d'autres prothèses, implants et greffes cardiaques et vasculaires | 362 |
| C71.8 | Tumeur maligne à localisations contiguës de l'encéphale | 358 |
| I77.6 | Artérite, sans précision | 357 |
| Y83.6 | Ablation d'un autre organe (partielle) (totale) | 354 |
| I97.1 | Autres troubles fonctionnels après chirurgie cardiaque | 353 |
| E77.8 | Autres anomalies du métabolisme des glycoprotéines | 350 |
| J18.9 | Pneumopathie, sans précision | 350 |
| W79 | Inhalation et ingestion d'aliments provoquant une obstruction des voies respiratoires | 350 |
| E88.8 | Autres anomalies métaboliques précisées | 346 |
| C79.3 | Tumeur maligne secondaire du cerveau et des méninges cérébrales | 345 |
| I25.8 | Autres formes de cardiopathie ischémique chronique | 339 |
| R09.2 | Arrêt respiratoire | 336 |
| C71.0 | Tumeur maligne du cerveau, sauf lobes et ventricules | 323 |
| T81.0 | Hémorragie et hématome compliquant un acte à visée diagnostique et thérapeutique, non classés ailleurs | 320 |
| I50.09 | Insuffisance cardiaque congestive, avec fraction d'éjection ventriculaire gauche [FEVG] non précisée | 318 |
| Z96.6 | Présence d'implants d'articulations orthopédiques | 317 |
| D48.7 | Tumeur à évolution imprévisible et inconnue d'autres sièges précisés | 316 |
| X41 | Intoxication accidentelle par des antiépileptiques, sédatifs, hypnotiques, antiparkinsoniens et psychotropes et exposition à ces produits, non classés ailleurs | 316 |
| I77.2 | Rupture d'une artère | 308 |
| C34.3 | Tumeur maligne du lobe inférieur, bronches ou poumon | 303 |
| E74.0 | Thésaurismose glycogénique | 302 |
| D43.0 | Tumeur à évolution imprévisible ou inconnue de l'encéphale, supratentoriel | 300 |
| G60.0 | Neuropathie héréditaire motrice et sensorielle | 300 |
| Z90.4 | Absence acquise d'autres parties de l'appareil digestif | 299 |
| I33.0 | Endocardite infectieuse aigüe et subaigüe | 294 |
| T17.9 | Corps étranger dans les voies respiratoires, partie non précisée | 294 |
| C79.9 | Tumeur maligne secondaire de siège non précisé | 291 |
| C78.0 | Tumeur maligne secondaire du poumon | 290 |
| J95.8 | Autres troubles respiratoires après un acte à visée diagnostique et thérapeutique, non classés ailleurs | 290 |
| I74.9 | Embolie et thrombose d'artères non précisées | 288 |
| E75.2 | Autres sphingolipidoses | 285 |
| G31.8 | Autres affections dégénératives précisées du système nerveux | 285 |
| I50.9 | Insuffisance cardiaque, sans précision | 285 |
| R68.8 | Autres symptômes et signes généraux précisés | 281 |
| D18.0 | Hémangiome, tout siège | 279 |
| C56 | Tumeur maligne de l'ovaire | 277 |
| J20.9 | Bronchite aigüe, sans précision | 276 |
| M86.9 | Ostéomyélite, sans précision | 276 |
| K65.0 | Péritonite aigüe | 275 |
| C41.0 | Tumeur maligne des os du crâne et de la face | 274 |
| J98.0 | Affections des bronches, non classées ailleurs | 273 |
| K91.8 | Autres atteintes de l'appareil digestif après un acte à visée diagnostique et thérapeutique, non classées ailleurs | 270 |
| T81.2 | Perforation et déchirure accidentelles au cours d'un acte à visée diagnostique et thérapeutique, non classées ailleurs | 268 |
| Q87.1 | Syndromes congénitaux malformatifs associés principalement à une petite taille | 267 |
| Q92.3 | Trisomie partielle mineure | 265 |
| C71.9 | Tumeur maligne de l'encéphale, sans précision | 264 |
| R41.8 | Symptômes et signes relatifs aux fonctions cognitives et à la conscience, autres et non précisés | 264 |
| B90.9 | Séquelles de tuberculose des voies respiratoires et sans précision | 260 |
| C49.9 | Tumeur maligne du tissu conjonctif et des autres tissus mous, sans précision | 260 |
| I80.3 | Phlébite et thrombophlébite des membres inférieurs, sans précision | 260 |
| C78.8 | Tumeur maligne secondaire des organes digestifs, autres et non précisés | 257 |
| I49.9 | Arythmie cardiaque, sans précision | 257 |
| C49.2 | Tumeur maligne du tissu conjonctif et des autres tissus mous du membre inférieur, y compris la hanche | 254 |
| C64 | Tumeur maligne du rein, à l'exception du bassinet | 254 |
| G11.4 | Paraplégie spastique héréditaire | 254 |
| G93.9 | Affection du cerveau, sans précision | 252 |
| A41.9 | Sepsis, sans précision | 250 |
| M84.4 | Fracture pathologique, non classée ailleurs | 247 |
| Q04.3 | Autres anomalies localisées du développement de l'encéphale | 245 |
| C76.0 | Tumeur maligne de siège mal défini de la tête, de la face et du cou | 244 |
| C85.1 | Lymphomes à cellules B, sans précision | 242 |
| I67.9 | Maladie cérébrovasculaire, sans précision | 240 |
| T82.0 | Complication mécanique d'une prothèse valvulaire cardiaque | 240 |
| F03 | Démence, sans précision | 238 |
| F10.2 | Troubles mentaux et du comportement liés à l'utilisation d'alcool - " Syndrome de dépendance " | 237 |
| A41.5 | Sepsis à d'autres microorganismes Gram négatif | 236 |
| R57.9 | Choc, sans précision | 234 |
| I80.2 | Phlébite et thrombophlébite d'autres vaisseaux profonds des membres inférieurs | 232 |
| C90.0 | Myélome multiple | 231 |
| I51.9 | Cardiopathie, sans précision | 231 |
| T81.8 | Autres complications d'un acte à visée diagnostique et thérapeutique, non classées ailleurs | 229 |
| I49.8 | Autres arythmies cardiaques précisées | 228 |
| I77.8 | Autres atteintes précisées des artères et artérioles | 226 |
| J18.1 | Pneumopathie lobaire, sans précision | 225 |
| T84.5 | Infection et réaction inflammatoire dues à une prothèse articulaire interne | 225 |
| I51.6 | Maladie cardiovasculaire, sans précision | 224 |
| X69 | Auto-intoxication par des produits chimiques et substances nocives et exposition à ces produits, autres et sans précision | 224 |
| K63.9 | Maladie de l'intestin, sans précision | 223 |
| J18.0 | Bronchopneumopathie, sans précision | 219 |
| N28.8 | Autres affections précisées du rein et de l'uretère | 219 |
| T85.8 | Autres complications de prothèses, implants et greffes internes, non classées ailleurs | 218 |
| I67.2 | Athérosclérose cérébrale | 217 |
| K76.8 | Autres maladies précisées du foie | 217 |
| C50.9 | Tumeur maligne du sein, sans précision | 216 |
| C92.0 | Leucémie myéloblastique aigüe [LAM] | 210 |
| G98 | Autres affections du système nerveux, non classées ailleurs | 210 |
| X49 | Intoxication accidentelle par des produits chimiques et substances nocives et exposition à ces produits, autres et sans précision | 208 |
| T82.3 | Complication mécanique d'autres greffes vasculaires | 206 |
| J98.8 | Autres troubles respiratoires précisés | 205 |
| I38 | Endocardite, valvule non précisée | 203 |
| T81.1 | Choc pendant ou après un acte à visée diagnostique et thérapeutique, non classé ailleurs | 203 |
| K74.6 | Cirrhoses du foie, autres et sans précision | 202 |
| Z98.8 | Autres états postchirurgicaux précisés | 201 |
| I65.2 | Occlusion et sténose de l'artère carotide | 200 |
| K31.8 | Autres maladies précisées de l'estomac et du duodénum | 199 |
| G71.2 | Myopathies congénitales | 197 |
| K92.9 | Maladie du système digestif, sans précision | 196 |
| Q87.2 | Syndromes congénitaux malformatifs impliquant principalement les membres | 196 |
| G40.3 | Épilepsie et syndromes épileptiques généralisés idiopathiques | 194 |
| J15.6 | Pneumopathie due à d'autres bactéries à Gram négatif | 194 |
| T90.5 | Séquelles de lésion traumatique intracrânienne | 193 |
| Z96.8 | Présence d'autres implants fonctionnels précisés | 193 |
| C44.9 | Tumeur maligne de la peau, sans précision | 192 |
| S06.5 | Hémorragie sousdurale traumatique | 192 |
| L98.4 | Ulcérations chroniques de la peau, non classées ailleurs | 191 |
| R57.2 | Choc septique | 191 |
| Q99.8 | Autres anomalies précisées des chromosomes | 187 |
| Y60.0 | Coupure, piqûre, perforation ou hémorragie accidentelles au cours d'une intervention chirurgicale | 187 |
| J69.0 | Pneumopathie due à des aliments et des vomissements | 186 |
| F45.3 | Dysfonctionnement neurovégétatif somatoforme | 184 |
| C78.7 | Tumeur maligne secondaire du foie et des voies biliaires intrahépatiques | 182 |
| F99 | Trouble mental, sans autre indication | 182 |
| H35.5 | Dystrophie rétinienne héréditaire | 182 |
| C49.0 | Tumeur maligne du tissu conjonctif et des autres tissus mous de la tête, de la face et du cou | 181 |
| A49.8 | Autres infections bactériennes, siège non précisé | 180 |
| W78 | Inhalation du contenu de l'estomac | 180 |
| Y83.9 | Intervention chirurgicale, sans précision | 180 |
| G93.5 | Compression du cerveau | 179 |
| I80.1 | Phlébite et thrombophlébite de la veine fémorale | 179 |
| K70.3 | Cirrhose alcoolique du foie | 179 |
| L08.9 | Infection localisée de la peau et du tissu cellulaire souscutané, sans précision | 179 |
| A52.7 | Autres formes tardives de syphilis symptomatique | 178 |
| C78.3 | Tumeur maligne secondaire des organes respiratoires, autres et non précisés | 178 |
| Y84.8 | Autres actes médicaux | 177 |
| C67.9 | Tumeur maligne de la vessie, sans précision | 176 |
| G93.1 | Lésion cérébrale anoxique, non classée ailleurs | 176 |
| D84.8 | Autres déficits immunitaires précisés | 175 |
| J39.2 | Autres maladies du pharynx | 174 |
| S14.1 | Lésions traumatiques de la moelle cervicale, autres et non précisées | 174 |
| R91 | Résultats anormaux d'imagerie diagnostique du poumon | 173 |
| C79.4 | Tumeur maligne secondaire de parties du système nerveux, autres et non précisées | 172 |
| D32.0 | Tumeur bénigne des méninges cérébrales | 172 |
| J20.8 | Bronchite aigüe due à d'autres microorganismes précisés | 172 |
| A09.0 | Gastroentérites et colites d’origine infectieuse, autres et non précisées | 170 |
| C16.9 | Tumeur maligne de l'estomac, sans précision | 169 |
| D38.1 | Tumeur à évolution imprévisible ou inconnue de la trachée, des bronches et du poumon | 169 |
| C77.2 | Tumeur maligne secondaire et non précisée des ganglions lymphatiques intraabdominaux | 168 |
| J39.8 | Autres maladies des voies respiratoires supérieures précisées | 168 |
| J84.1 | Autres affections pulmonaires interstitielles avec fibrose | 168 |
| E71.3 | Anomalie du métabolisme des acides gras | 167 |
| J38.7 | Autres maladies du larynx | 166 |
| L02.2 | Abcès cutané, furoncle et anthrax du tronc | 166 |
| Z99.1 | Dépendance envers un respirateur | 166 |
| D48.5 | Tumeur à évolution imprévisible et inconnue de la peau | 165 |
| J81 | Œdème pulmonaire | 165 |
| J90 | Épanchement pleural, non classé ailleurs | 165 |
| C77.0 | Tumeur maligne secondaire et non précisée des ganglions lymphatiques de la tête, de la face et du cou | 164 |
| L02.4 | Abcès cutané, furoncle et anthrax d'un membre | 163 |
| Q78.8 | Autres ostéo-chondro-dysplasies précisées | 163 |
| G11.1 | Ataxie cérébelleuse à début précoce | 161 |
| K55.9 | Trouble vasculaire de l'intestin, sans précision | 161 |
| T88.8 | Autres complications précisées de soins médicaux et chirurgicaux, non classées ailleurs | 161 |
| T85.6 | Complication mécanique d'autres prothèses, implants et greffes internes précisés | 160 |
| C78.6 | Tumeur maligne secondaire du rétropéritoine et du péritoine | 159 |
| C84.4 | Lymphome périphérique à cellules T, non classé ailleurs | 159 |
| K92.2 | Hémorragie gastro-intestinale, sans précision | 159 |
| I71.0 | Dissection de l'aorte [toute localisation] | 158 |
| A18.0 | Tuberculose des os et des articulations | 157 |
| W23 | Compression, écrasement ou blocage dans des objets ou entre des objets | 157 |
| C76.3 | Tumeur maligne de siège mal défini du pelvis | 156 |
| E88.9 | Anomalie métabolique, sans précision | 156 |
| D37.7 | Tumeur à évolution imprévisible ou inconnue d'autres organes digestifs | 155 |
| K83.1 | Obstruction des voies biliaires | 155 |
| T88.7 | Effet indésirable d'un médicament, sans précision | 155 |
| X42 | Intoxication accidentelle par des narcotiques et psychodysleptiques [hallucinogènes] et exposition à ces produits, non classés ailleurs | 155 |
| W80 | Inhalation et ingestion d'autres objets provoquant une obstruction des voies respiratoires | 154 |
| E85.4 | Amylose limitée à un ou plusieurs organes | 153 |
| I62.0 | Hémorragie sousdurale non traumatique | 153 |
| J22 | Infection aigüe des voies respiratoires inférieures, sans précision | 153 |
| Y14 | Intoxication par des médicaments et substances biologiques, autres et sans précision et exposition à ces produits, intention non déterminée | 153 |
| C77.1 | Tumeur maligne secondaire et non précisée des ganglions lymphatiques intrathoraciques | 151 |
| D37.0 | Tumeur à évolution imprévisible ou inconnue de la lèvre, de la cavité buccale et du pharynx | 151 |
| R19.0 | Tuméfaction et masse intraabdominales et pelviennes | 151 |
| C34.0 | Tumeur maligne de la bronche souche | 150 |
| E71.1 | Autres anomalies du métabolisme des acides aminés à chaine ramifiée | 150 |
| E23.0 | Hypopituitarisme | 149 |
| N32.8 | Autres affections précisées de la vessie | 149 |
| C20 | Tumeur maligne du rectum | 148 |
| L03.1 | Phlegmon d'autres parties d'un membre | 148 |
| L98.8 | Autres affections précisées de la peau et du tissu cellulaire souscutané | 148 |
| W20 | Heurt causé par le lancement ou la chute (d'un)(d') objet(s) | 148 |
| X45 | Intoxication accidentelle par l'alcool et exposition à l'alcool | 148 |
| Y44.2 | Effets indésirables des anticoagulants au cours de leur usage thérapeutique | 148 |
| C44.5 | Tumeur maligne de la peau du tronc | 147 |
| P03.1 | Fœtus et nouveau-né affectés par d'autres présentations et positions vicieuses du fœtus et disproportions fœtopelviennes au cours du travail et de l'accouchement | 147 |
| X50 | Surmenage et mouvements épuisants ou répétés | 147 |
| N39.0 | Infection des voies urinaires, siège non précisé | 146 |
| S06.8 | Autres lésions traumatiques intracrâniennes | 146 |
| C44.2 | Tumeur maligne de la peau de l'oreille et du conduit auditif externe | 144 |
| J86.0 | Pyothorax avec fistule | 144 |
| C49.1 | Tumeur maligne du tissu conjonctif et des autres tissus mous du membre supérieur, y compris l'épaule | 143 |
| I35.9 | Atteinte de la valvule aortique, sans précision | 142 |
| P00.8 | Fœtus et nouveau-né affectés par d'autres affections maternelles | 142 |
| Q24.8 | Autres malformations cardiaques congénitales précisées | 142 |
| Z98.0 | Dérivation et anastomose intestinales | 142 |
| Z99.8 | Dépendance envers d'autres machines et appareils auxiliaires | 142 |
| C26.8 | Tumeur maligne à localisations contiguës de l'appareil digestif | 141 |
| I82.8 | Embolie et thrombose d'autres veines précisées | 141 |
| N50.8 | Autres affections précisées des organes génitaux de l'homme | 141 |
| D47.2 | Gammapathie monoclonale de signification indéterminée [GMSI] | 140 |
| T17.8 | Corps étranger de localisations autres et multiples dans les voies respiratoires | 140 |
| Y60.6 | Coupure, piqûre, perforation ou hémorragie accidentelles au cours d'une aspiration, d'une ponction et d'un autre cathétérisme | 140 |
| Y83.5 | Amputation de membre(s) | 140 |
| D48.0 | Tumeur à évolution imprévisible et inconnue des os et du cartilage articulaire | 139 |
| G40.4 | Autres épilepsies et syndromes épileptiques généralisés | 139 |
| J95.0 | Fonctionnement défectueux d'une trachéotomie | 139 |
| P03.8 | Fœtus et nouveau-né affectés par d'autres complications précisées du travail et de l'accouchement | 139 |
| C44.7 | Tumeur maligne de la peau du membre inférieur, y compris la hanche | 138 |
| J44.9 | Maladie pulmonaire obstructive chronique, sans précision | 138 |
| K55.1 | Troubles vasculaires chroniques de l'intestin | 138 |
| T87.4 | Infection d'un moignon d'amputation | 138 |
| X70 | Lésion auto-infligée par pendaison, strangulation et suffocation | 138 |
| C83.0 | Lymphome à petites cellules B | 137 |
| G12.2 | Maladies du neurone moteur | 137 |
| G80.9 | Paralysie cérébrale, sans précision | 137 |
| Y11 | Intoxication par des antiépileptiques, sédatifs, hypnotiques, antiparkinsoniens et psychotropes et exposition à ces produits, non classés ailleurs, intention non déterminée | 136 |
| C39.8 | Tumeur maligne à localisations contiguës des organes respiratoires et intrathoraciques | 135 |
| M80.9 | Ostéoporose avec fracture pathologique, sans précision | 135 |
| M89.5 | Ostéolyse | 135 |
| Y65.8 | Autres accidents et complications précisés au cours d'actes médicaux et chirurgicaux | 135 |
| B18.2 | Hépatite virale chronique C | 134 |
| D48.1 | Tumeur à évolution imprévisible et inconnue du tissu conjonctif et des autres tissus mous | 134 |
| Z90.2 | Absence acquise [de partie] de poumon | 134 |
| C76.1 | Tumeur maligne de siège mal défini du thorax | 133 |
| I25.9 | Cardiopathie ischémique chronique, sans précision | 133 |
| I80.8 | Phlébite et thrombophlébite d'autres localisations | 133 |
| J96.99 | Insuffisance respiratoire, sans précision - " Type non précisé " | 133 |
| A18.1 | Tuberculose de l'appareil génito-urinaire | 132 |
| G62.9 | Polynévrite, sans précision | 132 |
| G93.4 | Encéphalopathie, sans précision | 132 |
| J15.2 | Pneumopathie due à des staphylocoques | 132 |
| K92.8 | Autres maladies précisées du système digestif | 132 |
| R06.8 | Anomalies de la respiration, autres et non précisées | 131 |
| H18.5 | Dystrophies cornéennes héréditaires | 130 |
| I26.9 | Embolie pulmonaire, sans mention de cœur pulmonaire aigu | 130 |
| I51.7 | Cardiomégalie | 130 |
| J13 | Pneumonie due à Streptococcus pneumoniae | 130 |
| K63.2 | Fistule de l'intestin | 130 |
| K83.0 | Angiocholite [cholangite] | 130 |
| Z51.5 | Soins palliatifs | 130 |
| Z90.0 | Absence acquise d'une partie de la tête et du cou | 130 |
| C14.8 | Tumeur maligne à localisations contiguës de la lèvre, de la cavité buccale et du pharynx | 129 |
| C25.9 | Tumeur maligne du pancréas, sans précision | 129 |
| Q79.6 | Syndrome d'Ehlers–Danlos | 129 |
| X78 | Lésion auto-infligée par utilisation d'objet tranchant | 129 |
| C22.9 | Tumeur maligne du foie, sans précision | 128 |
| G60.8 | Autres neuropathies héréditaires et idiopathiques | 128 |
| B49 | Mycose, sans précision | 127 |
| I72.8 | Anévrisme et dissection d'autres artères précisées | 127 |
| I82.9 | Embolie et thrombose d'une veine non précisée | 127 |
| R04.8 | Hémorragie d'autres parties des voies respiratoires | 127 |
| Z90.8 | Absence acquise d'autres organes | 127 |
| C79.2 | Tumeur maligne secondaire de la peau | 126 |
| E87.8 | Autres déséquilibres hydroélectrolytiques, non classés ailleurs | 126 |
| G11.8 | Autres ataxies héréditaires | 126 |
| N19 | Défaillance rénale, sans précision | 126 |
| R98 | Décès sans témoin | 126 |
| X80 | Lésion auto-infligée par saut dans le vide | 126 |
| E76.2 | Autres mucopolysaccharidoses | 125 |
| I73.9 | Maladie vasculaire périphérique, sans précision | 125 |
| I71.3 | Anévrisme aortique abdominal, rompu | 124 |
| J44.8 | Autres maladies pulmonaires obstructives chroniques précisées | 124 |
| K86.8 | Autres maladies précisées du pancréas | 124 |
| M00.9 | Arthrite à bactéries pyogènes, sans précision | 124 |
| X68 | Auto-intoxication par des pesticides et exposition à ces produits | 124 |
| A52.1 | Syphilis nerveuse symptomatique | 123 |
| D81.8 | Autres déficits immunitaires combinés | 123 |
| E46 | Malnutrition protéinoénergétique, sans précision | 123 |
| E70.3 | Albinisme | 123 |
| G04.9 | Encéphalite, myélite et encéphalomyélite, sans précision | 123 |
| G90.9 | Affection du système nerveux autonome, sans précision | 122 |
| I08.0 | Atteintes des valvules mitrale et aortique | 122 |
| K62.8 | Autres maladies précisées de l'anus et du rectum | 122 |
| S06.9 | Lésion traumatique intracrânienne, sans précision | 122 |
| I51.3 | Thrombose intracardiaque, non classée ailleurs | 121 |
| K22.8 | Autres maladies précisées de l'œsophage | 121 |
| C18.9 | Tumeur maligne du côlon, sans précision | 120 |
| C26.9 | Tumeur maligne de sièges mal définis de l'appareil digestif | 120 |
| I67.1 | Anévrisme cérébral, non rompu | 120 |
| S36.8 | Lésion traumatique d'autres organes intraabdominaux | 120 |
| C44.4 | Tumeur maligne de la peau du cuir chevelu et du cou | 119 |
| C68.9 | Tumeur maligne d'un organe urinaire, sans précision | 119 |
| C73 | Tumeur maligne de la thyroïde | 119 |
| D61.9 | Aplasie médullaire, sans précision | 119 |
| I05.9 | Maladie de la valvule mitrale, sans précision | 119 |
| O99.4 | Maladies de l'appareil circulatoire compliquant la grossesse, l'accouchement et la puerpéralité | 118 |
| T45.1 | Intoxication par médicaments antitumoraux et immunosuppresseurs | 118 |
| T84.0 | Complication mécanique d'une prothèse articulaire interne | 118 |
| E72.8 | Autres anomalies précisées du métabolisme des acides aminés | 117 |
| I10 | Hypertension essentielle (primitive) | 117 |
| T14.5 | Lésion traumatique de vaisseau(x) sanguin(s) d'une partie du corps non précisée | 117 |
| J86.9 | Pyothorax sans fistule | 116 |
| L02.9 | Abcès cutané, furoncle et anthrax, sans précision | 116 |
| Q74.0 | Autres malformations congénitales d'un (des) membre(s) supérieur(s), y compris la ceinture scapulaire | 116 |
| Z82.4 | Antécédents familiaux de cardiopathies ischémiques et autres maladies de l'appareil circulatoire | 116 |
| Z92.1 | Antécédents personnels d'utilisation (actuelle) à long terme d'anticoagulants | 116 |
| F22.0 | Trouble délirant | 115 |
| I74.0 | Embolie et thrombose de l'aorte abdominale | 115 |
| K80.5 | Calcul des canaux biliaires sans angiocholite ni cholécystite | 115 |
| S36.1 | Lésion traumatique du foie et de la vésicule biliaire | 115 |
| Z95.0 | Présence de dispositifs électroniques cardiaques | 115 |
| A18.8 | Tuberculose d'autres organes précisés | 114 |
| C43.5 | Mélanome malin du tronc | 114 |
| J98.5 | Maladies du médiastin, non classées ailleurs | 114 |
| L03.3 | Phlegmon du tronc | 114 |
| Q21.2 | Communication auriculoventriculaire | 114 |
| S09.9 | Lésion traumatique de la tête, sans précision | 114 |
| G95.1 | Myélopathies vasculaires | 113 |
| I74.2 | Embolie et thrombose des artères des membres supérieurs | 113 |
| Q04.8 | Autres malformations congénitales précisées de l'encéphale | 113 |
| Z53.2 | Acte non effectué par décision du sujet pour des raisons autres et non précisées | 113 |
| C18.6 | Tumeur maligne du côlon descendant | 112 |
| L89.2 | Ulcère de décubitus de stade III | 112 |
| C18.2 | Tumeur maligne du côlon ascendant | 111 |
| C22.0 | Carcinome hépatocellulaire | 111 |
| D75.9 | Maladie du sang et des organes hématopoïétiques, sans précision | 111 |
| I72.4 | Anévrisme et dissection des artères du membre inférieur | 111 |
| O65.5 | Dystocie due à une anomalie des organes pelviens de la mère | 111 |
| Q77.7 | Dysplasie spondyloépiphysaire | 111 |
| Q82.4 | Dysplasie ectodermique (anhidrotique) | 111 |
| R55 | Syncope et collapsus | 111 |
| G12.1 | Autres amyotrophies spinales héréditaires | 110 |
| Q76.4 | Autres malformations congénitales du rachis, non associées à une scoliose | 110 |
| T84.9 | Complication d'une prothèse, d'un implant et d'une greffe orthopédiques internes, sans précision | 110 |
| C80.0 | Tumeur maligne de siège primitif non précisé, ainsi décrit | 109 |
| D70 | Agranulocytose | 109 |
| E72.1 | Anomalies du métabolisme des acides aminés soufrés | 109 |
| F32.9 | Épisode dépressif, sans précision | 109 |
| G06.0 | Abcès et granulome intracrâniens | 109 |
| Q68.8 | Autres anomalies morphologiques congénitales ostéoarticulaires et des muscles précisées | 109 |
| Z90.7 | Absence acquise d'organe(s) génital(aux) | 109 |
| G71.3 | Myopathie mitochondriale, non classée ailleurs | 108 |
| I77.1 | Sténose d'une artère | 108 |
| K83.8 | Autres maladies précisées des voies biliaires | 108 |
| T84.8 | Autres complications de prothèses, implants et greffes orthopédiques internes | 108 |
| X62 | Auto-intoxication par des narcotiques et psychodysleptiques [hallucinogènes] et exposition à ces produits, non classés ailleurs | 108 |
| C41.2 | Tumeur maligne du rachis | 107 |
| K22.2 | Obstruction de l'œsophage | 107 |
| T17.5 | Corps étranger dans les bronches | 107 |
| T29.3 | Brulures de parties multiples du corps, au moins une brulure du troisième degré mentionnée | 107 |
| C41.1 | Tumeur maligne de la mandibule | 106 |
| C76.2 | Tumeur maligne de siège mal défini de l'abdomen | 106 |
| G40.9 | Épilepsie, sans précision | 106 |
| I83.9 | Varices des membres inférieurs sans ulcère ni inflammation | 106 |
| E83.1 | Anomalies du métabolisme du fer | 105 |
| N10 | Néphrite tubulo-interstitielle aigüe | 105 |
| T82.1 | Complication mécanique d'un appareil cardiaque électronique | 105 |
| T98.3 | Séquelles de complications de soins chirurgicaux et médicaux, non classées ailleurs | 105 |
| C90.3 | Plasmocytome solitaire | 104 |
| F43.2 | Troubles de l'adaptation | 104 |
| I69.8 | Séquelles de maladies cérébrovasculaires, autres et non précisées | 104 |
| I74.8 | Embolie et thrombose d'autres artères | 104 |
| J15.9 | Pneumopathie bactérienne, sans précision | 104 |
| S25.0 | Lésion traumatique de l'aorte thoracique | 104 |
| C44.6 | Tumeur maligne de la peau du membre supérieur, y compris l'épaule | 103 |
| D68.2 | Carence héréditaire en autres facteurs de coagulation | 103 |
| G09 | Séquelles d'affections inflammatoires du système nerveux central | 103 |
| I89.8 | Autres atteintes non infectieuses précisées des vaisseaux et des ganglions lymphatiques | 103 |
| N13.9 | Uropathie obstructive et par reflux, sans précision | 103 |
| R09.0 | Asphyxie | 103 |
| B37.8 | Autres localisations de candidose | 102 |
| C38.3 | Tumeur maligne du médiastin, partie non précisée | 102 |
| J38.0 | Paralysie des cordes vocales et du larynx | 102 |
| J43.9 | Emphysème pulmonaire, sans précision | 102 |
| K81.0 | Cholécystite aigüe | 102 |
| Q74.2 | Autres malformations congénitales d'un (des) membre(s) inférieur(s), y compris la ceinture pelvienne | 102 |
| S27.3 | Autres lésions traumatiques du poumon | 102 |
| Z95.1 | Présence d'un pontage aortocoronaire | 102 |
| D84.9 | Déficit immunitaire, sans précision | 101 |
| G30.9 | Maladie d'Alzheimer, sans précision | 101 |
| G71.1 | Affections myotoniques | 101 |
| Q87.3 | Syndromes congénitaux malformatifs comprenant un gigantisme du nouveau-né | 101 |
| W17 | Autre chute d'un niveau à un autre | 101 |
| Y60.4 | Coupure, piqûre, perforation ou hémorragie accidentelles au cours d'une endoscopie | 101 |
| Z86.4 | Antécédents personnels d'abus de substances psychoactives | 101 |
