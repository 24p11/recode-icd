# Audit post-Phase 2 — sources externes

> Généré par `scripts/explore/2026-05-26_post_phase2_audit.py`.

## Synthèse

- **Ophtalmologie** : 162 absorptions, concentration 85 % sur chapitre VII — verdict : *alignement_naturel*.
- **Richesse lexicale** : 15978 codes uniques, médiane 10 notes/code, p95=30, max=2478 (code `A52.7` à 2478 notes). 90 codes > 100 notes.
- **Orphelins** : 265 cas — 0 post-2006 (attendu), 265 vrais orphelins (à inspecter).

## Recommandation

**À investiguer avant Phase 3.** Points bloquants : code(s) à charge anormale (max=2478), trop de vrais orphelins (265).

---

## Section 1 — Anomalie d'absorption ophtalmologique

**162 entrées absorbées** sur 444 chargées (36,5 %). Distribution par chapitre CIM-10 :

| chapitre | nb absorptions | % |
|---|---:|---:|
| VII | 137 | 84.6 % |
| XVII | 21 | 13.0 % |
| XIX | 3 | 1.9 % |
| IV | 1 | 0.6 % |

**20 exemples d'absorptions** (échantillon stratifié sur l'ordre code) :

| code | libellé AP-HP Ophtalmo | libellé OFS/ANS qui a matché | type externe | type OFS/ANS | divergence |
|---|---|---|---|---|---|
| E70.3 | Albinisme oculaire | Albinisme oculaire | synonyme | synonyme | · |
| H02.5 | Atrophie de la paupière | Atrophie de la paupière | synonyme | synonyme | · |
| H04.5 | Dacryolithe | Dacryolithe | synonyme | synonyme | · |
| H05.2 | Oedème de l'orbite | oedème de l'orbite | synonyme | synonyme | · |
| H16.0 | Ulcère de la cornée avec hypopyon | Ulcère de (la) cornée avec hypopyon | synonyme | synonyme | · |
| H16.1 | Kératite stellaire | Kératite stellaire | synonyme | synonyme | · |
| H16.2 | Kératoconjonctivite SAI | Kératoconjonctivite SAI | synonyme | synonyme | · |
| H18.8 | Hypoesthésie de la cornée | Hypoesthésie de la cornée | synonyme | synonyme | · |
| H20.0 | Uvéite antérieure aiguë, subaiguë ou à répétition | Uvéite antérieure aigüe, subaigüe ou à répétition | synonyme | synonyme | · |
| H25.0 | Cataracte sénile polaire sous-capsulaire (antérieure)(postér | cataracte sénile polaire sous-capsulaire (antérieure) (posté | synonyme | synonyme | · |
| H30.1 | Rétinochoroïdite disséminée | Rétinochoroïdite disséminée | synonyme | synonyme | · |
| H31.1 | Atrophie de la choroïde | Atrophie de la choroïde | synonyme | synonyme | · |
| H33.3 | Trou rond de la rétine sans décollement | Trou rond de la rétine, sans décollement | synonyme | synonyme | · |
| H44.1 | Ophtalmie sympathique | Ophtalmie sympathique | synonyme | inclusion | ✓ |
| H48.1 | Névrite rétrobulbaire au cours de syphilis tardive | Névrite rétrobulbaire au cours de syphilis tardive | synonyme | synonyme | · |
| H50.4 | Syndrome de monofixation | Syndrome de monofixation | synonyme | synonyme | · |
| H53.0 | Amblyopie avec strabisme | Amblyopie avec strabisme | synonyme | synonyme | · |
| H55 | Nystagmus de défaut d'usage | Nystagmus (de) défaut d'usage | synonyme | synonyme | · |
| Q13.0 | Colobome de l'iris | Colobome de l'iris | synonyme | synonyme | · |
| Q14.0 | Opacité congénitale du corps vitré | Opacité congénitale du corps vitré
 | synonyme | inclusion | ✓ |

**Conclusion** : alignement naturel — 85 % des absorptions tombent sur le chapitre VII (Maladies de l'œil). Le thésaurus AP-HP Ophtalmologie reprend l'éditorialisation OMS française quasi verbatim, d'où le taux élevé.

---

## Section 2 — Distribution du nombre de notes par code

CSV final : **214675 lignes** réparties sur **15978 codes uniques**. Moyenne 13.4 notes/code.

**Quantiles** (notes par code) :

| min | p25 | médiane | p75 | p90 | p95 | p99 | max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6 | 10 | 15 | 23 | 30 | 69 | 2478 |

**Histogramme log₁₀** (codes par tranche de nb de notes) :
```
      1–9     : ██████████████████████████████████████ (7618 codes, 47.7 %)
     10–99    : █████████████████████████████████████████ (8267 codes, 51.7 %)
    100–999   :  (90 codes, 0.6 %)
   1000–9999  :  (3 codes, 0.0 %)
```

**90 codes ont > 100 notes** (ces codes méritent une inspection ad-hoc).

**Top 20 des codes les plus chargés** :

| # | code | libellé | n notes | breakdown type | top 3 sources |
|---:|---|---|---:|---|---|
| 1 | A52.7 | Autres formes tardives de syphilis symptomatique | 2478 | synonyme=2380, exclusion=70, inclusion=28 | CIM-10 index=2100, CIM-10=252, ANS=84 |
| 2 | Q87.8 | Autres syndromes congénitaux malformatifs précisés, non classés ailleu | 1215 | inclusion=1185, synonyme=23, exclusion=7 | ORPHANET=1184, CIM-10 index=11, CIM-10 frères=6 |
| 3 | A52.1 | Syphilis nerveuse symptomatique | 1199 | synonyme=1111, exclusion=66, inclusion=22 | CIM-10 index=1012, CIM-10=121, ANS=66 |
| 4 | A18.1 | Tuberculose de l'appareil génito-urinaire | 954 | synonyme=873, exclusion=54, inclusion=27 | CIM-10 index=792, CIM-10=99, ANS=36 |
| 5 | A52.0 | Syphilis cardiovasculaire | 710 | synonyme=640, exclusion=50, inclusion=20 | CIM-10 index=600, CIM-10=70, ANS=40 |
| 6 | A18.0 | Tuberculose des os et des articulations | 640 | synonyme=595, exclusion=30, inclusion=15 | CIM-10 index=545, CIM-10=75, ANS=20 |
| 7 | A18.8 | Tuberculose d'autres organes précisés | 602 | synonyme=476, exclusion=98, inclusion=28 | CIM-10 index=427, CIM-10=77, CIM-10 frères=56 |
| 8 | E74.0 | Thésaurismose glycogénique | 580 | inclusion=430, synonyme=124, exclusion=26 | ORPHANET=434, CIM-10 index=68, CIM-10=40 |
| 9 | M32.1 | Lupus érythémateux disséminé avec atteinte d'organes et d'appareils | 520 | synonyme=424, inclusion=64, exclusion=32 | CIM-10 index=336, CIM-10=72, AP-HP Rhumatologie=48 |
| 10 | A54.8 | Autres infections gonococciques | 448 | synonyme=320, exclusion=112, inclusion=16 | CIM-10 index=224, CIM-10=104, CIM-10 frères=56 |
| 11 | Q82.8 | Autres malformations congénitales précisées de la peau | 433 | inclusion=308, synonyme=111, exclusion=14 | ORPHANET=307, CIM-10 index=60, AP-HP Dermatologie=44 |
| 12 | Q93.5 | Autres délétions partielles d'un chromosome | 419 | inclusion=416, synonyme=2, exclusion=1 | ORPHANET=415, ANS=3, CIM-10 index=1 |
| 13 | A51.4 | Autres formes de syphilis secondaire | 384 | synonyme=342, exclusion=30, inclusion=12 | CIM-10 index=300, CIM-10=54, ANS=24 |
| 14 | G71.0 | Dystrophie musculaire | 379 | inclusion=308, synonyme=63, exclusion=8 | ORPHANET=308, CIM-10 index=48, CIM-10=15 |
| 15 | Q87.0 | Syndromes congénitaux malformatifs atteignant principalement l'aspect  | 365 | inclusion=325, synonyme=39, exclusion=1 | ORPHANET=324, CIM-10 index=25, CIM-10=9 |
| 16 | E77.8 | Autres anomalies du métabolisme des glycoprotéines | 345 | inclusion=327, exclusion=10, synonyme=8 | ORPHANET=330, CIM-10=6, AP-HP Troubles métaboliques=4 |
| 17 | E88.8 | Autres anomalies métaboliques précisées | 295 | inclusion=236, synonyme=45, exclusion=14 | ORPHANET=235, AP-HP Troubles métaboliques=30, CIM-10 index=9 |
| 18 | D86.8 | Sarcoïdose de localisations autres et associées | 294 | synonyme=210, exclusion=54, inclusion=30 | CIM-10 index=138, CIM-10=72, ANS=30 |
| 19 | G60.0 | Neuropathie héréditaire motrice et sensorielle | 275 | inclusion=246, synonyme=24, exclusion=5 | ORPHANET=245, CIM-10 index=18, CIM-10=9 |
| 20 | Q92.3 | Trisomie partielle mineure | 261 | inclusion=255, exclusion=3, synonyme=3 | ORPHANET=253, ANS=4, CIM-10=3 |

---

## Section 3 — Codes orphelins externes

**265 entrées** au code absent de `merged_codes`.

**Distribution par catégorie** :

| catégorie | n | % |
|---|---:|---:|
| vraiment_orphan | 265 | 100.0 % |

**Distribution par source** :

| source | n |
|---|---:|
| INDEX_CIM10_VOL3 | 229 |
| APHP_DERMATOLOGIE | 16 |
| APHP_RHUMATOLOGIE | 8 |
| APHP_NEPHROLOGIE | 7 |
| APHP_GRONES | 2 |
| APHP_OPHTALMOLOGIE | 1 |
| APHP_SRLF | 1 |
| APHP_GERMES | 1 |

**10 exemples — `vraiment_orphan`** :

| code | libellé | source |
|---|---|---|
| A90 | Dengue (classique) | INDEX_CIM10_VOL3 |
| A90 | Fièvre (de) (des) (due à), aden (voir aussi fièvre, dengue) | INDEX_CIM10_VOL3 |
| A90 | Fièvre (de) (des) (due à), dengue | INDEX_CIM10_VOL3 |
| A90 | Fièvre (de) (des) (due à), rouge (voir aussi fièvre, dengue) | INDEX_CIM10_VOL3 |
| A90 | Fièvre (Dengue) | APHP_DERMATOLOGIE |
| A91 | Dengue (classique), fièvre hémorragique | INDEX_CIM10_VOL3 |
| A91 | Fièvre (de) (des) (due à), dengue, hémorragique | INDEX_CIM10_VOL3 |
| A91 | Fièvre (de) (des) (due à), hémorragique (transmise par des a | INDEX_CIM10_VOL3 |
| A91 | Fièvre (de) (des) (due à), hémorragique (transmise par des a | INDEX_CIM10_VOL3 |
| A91 | Fièvre (de) (des) (due à), hémorragique (transmise par des a | INDEX_CIM10_VOL3 |

**Conclusion** : **à investiguer** — la majorité sont des vrais orphelins (codes inexistants).
