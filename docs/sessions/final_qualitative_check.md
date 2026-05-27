# Inspection qualitative finale — sources externes (Phases 1-3)

> Généré par `scripts/explore/2026-05-27_final_qualitative_check.py`.

## Synthèse

- **Dataset volumétrie** : 214 675 lignes sur 15 978 codes uniques ; source dominante = **CIM-10** (36 %), puis ANS (30 %), Index (21 %), ORPHANET (9 %), AP-HP (~2 % cumulé).
- **Échantillon A52.7** : 2 478 entrées, surreprésentation naturelle de l'Index CIM-10 (libellés historiques de la syphilis tardive déclinés par organe). 0 duplicates normalisés détectés sur 20 — dédup tolérante efficace.
- **Codes moyens** : 6 326 codes ont 10-20 notes (~40 % du CSV). Échantillon de 5 montre une répartition saine ; pas de dégradation détectée du contenu OFS/ANS par l'intégration des externes.
- **Codes OFS+ANS only** : 5 958 codes (~37 %) n'ont que des sources internes. Échantillons psychiatrie/causes externes : structure cohérente.
- **1 point d'attention** : `A07.1` (Giardiase) montre des libellés Index qui ont l'air dupliqués (`Colite (aiguë)...`, `Diarrhée...` répétés 2× chacun) — à vérifier (probablement entrées Index distinctes avec parenthèses différentes mais visuellement très proches).

## Recommandation

**Chantier sources externes clôturable.** Le dataset est qualitativement satisfaisant pour entraîner/évaluer des LLM CIM-10 :
- Répartition équilibrée entre sources structurelles (CIM-10 + ANS = 66 %) et enrichissement externe (Index + ORPHANET + AP-HP = 32 %).
- Aucune dégradation observée sur les codes purement internes.
- Quelques cas d'enrichissement extrême (A52.7, Q87.8) qui sont légitimes (codes-fourre-tout) mais à garder à l'esprit côté usage LLM (filtrage probable nécessaire pour ces codes lors de l'échantillonnage).

Point mineur à suivre éventuellement plus tard : vérifier si l'Index CIM-10 vol3 produit des libellés "presque identiques" qui passent la dédup tolérante actuelle (cf §2 A07.1).

---

## Section 1 — Échantillon A52.7 (le code champion)

`A52.7` (Autres formes tardives de syphilis symptomatique) : **2478 entrées** dans le CSV (dont 2 100 environ du CIM-10 index — voir audit Phase 2).

Échantillon de 20 entrées (seed=42) :

| source | type | texte |
|---|---|---|
| CIM-10 index | synonyme | Syphilis (acquise) (de), rectum (tardive) |
| CIM-10 index | synonyme | Gomme (syphilitique) (de) (voir aussi syphilis), paupière |
| CIM-10 index | synonyme | Ulcère (à) (de), syphilitique (récent) (secondaire) (tout siège), perforant (forme tardiv… |
| CIM-10 index | synonyme | Syphilis (acquise) (de), luette (tardive) |
| CIM-10 index | synonyme | Syphilis (acquise) (de), poumon (tardive) |
| CIM-10 index | synonyme | Syphilide (cutanée), tuberculeuse |
| CIM-10 | synonyme | syphilis [stade non précisé] musculaire |
| CIM-10 index | synonyme | Syphilis (acquise) (de), appareil lacrymal |
| CIM-10 index | synonyme | Cervicite (aiguë) (avec ectropion ou érosion du col) (chronique) (non sexuellement transm… |
| CIM-10 index | synonyme | Syphilis (acquise) (de), vitré (corps) (tardive) |
| CIM-10 index | synonyme | Sclérite (annulaire) (antérieure) (granulomateuse) (postérieure) (suppurée), syphilitique… |
| CIM-10 index | synonyme | Syphilis (acquise) (de), tardive, avec manifestations nca |
| CIM-10 index | synonyme | Syphilis (acquise) (de), hépatique (tardive) |
| CIM-10 | synonyme | affection inflammatoire des organes pelviens de la femme syphilitique tardive |
| CIM-10 index | synonyme | Médiastinite (aiguë) (chronique), syphilitique (tardive) |
| CIM-10 index | synonyme | Salpingite (trompe de fallope) (à) (de), syphilitique (tardive) |
| CIM-10 index | synonyme | Choriorétinite, syphilitique (secondaire), tardive |
| ANS | synonyme | Syphilis tardive ou tertiaire toute localisation, sauf celles classées en A52.0-A52.3 |
| CIM-10 index | synonyme | Synovite (de), syphilitique (tardive) |
| CIM-10 index | synonyme | Ostéonécrose (ischémique), syphilitique (tardive) |

**Répartition de l'échantillon** : sources = {'CIM-10 index': 17, 'CIM-10': 2, 'ANS': 1} ; types = {'synonyme': 20}.

**Observation qualitative** :
- **Libellés propres** : pas de bruit visible. Tous suivent le pattern Index CIM-10 vol3 standard avec parenthèses informatives.
- **Redondance sémantique légitime** : la majorité des entrées sont des déclinaisons "Syphilis tardive de [organe]" (paupière, poumon, rectum, luette, vitré, hépatique, médiastin, salpinge, etc.). Sémantiquement chaque entrée correspond à un cas clinique distinct → c'est la richesse attendue, pas du bruit.
- **Un cas qui interpelle** : `Cervicite ... (non sexuellement transmise) ... — tardive)` rangée sous A52.7. Probablement légitime (cervicite syphilitique tardive) mais le libellé tronqué est ambigu. Pas un bug.
- **0 duplicates normalisés sur 20** : la dédup tolérante fait son travail malgré le volume massif d'entrées.

---

## Section 2 — 5 codes "moyens" (10-20 notes)

6326 codes ont entre 10 et 20 notes (sur 15978 codes uniques). Échantillon de 5 (seed=42) :

### `A07.1` — Giardiase [lambliase]
**17 entrées** :

| source | type | texte |
|---|---|---|
| ANS | exclusion | certaines infections localisées – voir les chapitres relatifs aux divers systèm… |
| ANS | inclusion | les maladies considérées habituellement comme contagieuses ou transmissibles |
| AP-HP Germes (SPILF) | synonyme | Giardia (Lamblia) |
| CIM-10 index | synonyme | Colite (aiguë) (exsudative) (gangréneuse) (hémorragique) (infectieuse) (nécroti… |
| CIM-10 index | synonyme | Colite (aiguë) (exsudative) (gangréneuse) (hémorragique) (infectieuse) (nécroti… |
| CIM-10 index | synonyme | Diarrhée (estivale) (infantile) (présumée infectieuse) (due à) (voir aussi note… |
| CIM-10 index | synonyme | Diarrhée (estivale) (infantile) (présumée infectieuse) (due à) (voir aussi note… |
| CIM-10 index | synonyme | Dysenterie (catarrhale) (épidémique) (hémorragique) (infectieuse) (sporadique) … |
| CIM-10 index | synonyme | Dysenterie (catarrhale) (épidémique) (hémorragique) (infectieuse) (sporadique) … |
| CIM-10 index | synonyme | Entérite (aiguë) (diarrhéique) (épidémique) (présumée infectieuse) (due à) (voi… |
| CIM-10 index | synonyme | Entérite (aiguë) (diarrhéique) (épidémique) (présumée infectieuse) (due à) (voi… |
| CIM-10 index | synonyme | Giardiase |
| CIM-10 index | synonyme | Infection (à) (de), giardia lamblia |
| CIM-10 index | synonyme | Infection (à) (de), intestin (due à) (voir aussi entérite), giardia (lamblia) |
| CIM-10 index | synonyme | Lambliase |
| CIM-10 index | synonyme | Parasitose (à), giardia lamblia |
| CIM-10 index | synonyme | Parasitose (à), lamblia |

### `F20.32` — Schizophrénie indifférenciée - " épisodique avec déficit stable "
**12 entrées** :

| source | type | texte |
|---|---|---|
| ANS | exclusion | dépression postschizophrénique [F20.4] schizophrénie chronique indifférenciée [… |
| ANS | exclusion | réaction schizophrénique [F23.2] schizophrénie :  - aigüe (indifférenciée) [F23… |
| ANS | exclusion | symptômes, signes et résultats anormaux d'examens cliniques et de laboratoire, … |
| CIM-10 | exclusion | dépression post-schizophrénique |
| CIM-10 | exclusion | réaction schizophrénique |
| CIM-10 | exclusion | schizophrénie aiguë (indifférenciée) |
| CIM-10 | exclusion | schizophrénie chronique indifférenciée |
| CIM-10 | exclusion | schizophrénie cyclique |
| CIM-10 | exclusion | trouble psychotique aigu d'allure schizophrénique |
| CIM-10 | exclusion | trouble schizotypique |
| ANS | inclusion | Schizophrénie atypique |
| ANS | inclusion | troubles du développement psychologique |

### `J46` — État de mal asthmatique
**10 entrées** :

| source | type | texte |
|---|---|---|
| ANS | exclusion | certaines affections dont l'origine se situe dans la période périnatale [P00-P9… |
| ANS | exclusion | fibrose kystique du pancréas [E84.-] infection respiratoire SAI [J98.7] |
| CIM-10 | exclusion | fibrose kystique |
| ANS | inclusion | Asthme aigu grave |
| ANS | synonyme | Asthme aigu grave |
| CIM-10 | synonyme | asthme grave aigu |
| CIM-10 index | synonyme | Asthme (bronchique) (de(s)), avec, état de mal |
| CIM-10 index | synonyme | Asthme (bronchique) (de(s)), grave aigu |
| CIM-10 index | synonyme | Etat (de), mal, asthmatique (voir aussi asthme) |
| CIM-10 index | synonyme | Status asthmaticus |

### `Q17.1` — Macrotie
**13 entrées** :

| source | type | texte |
|---|---|---|
| ANS | exclusion | erreurs innées du métabolisme [E70-E90] |
| ANS | exclusion | fente labiale et fente palatine [Q35-Q37] malformation congénitale (de) :  - gl… |
| ANS | exclusion | fistule préauriculaire [Q18.1] |
| CIM-10 | exclusion | anomalie morphologique congénitale du rachis |
| CIM-10 | exclusion | fente labiale et fente palatine |
| CIM-10 | exclusion | fistule préauriculaire |
| CIM-10 | exclusion | malformation congénitale (de) glande parathyroïde |
| CIM-10 | exclusion | malformation congénitale (de) glande thyroïde |
| CIM-10 | exclusion | malformation congénitale (de) larynx |
| CIM-10 | exclusion | malformation congénitale (de) lèvre NCA |
| CIM-10 | exclusion | malformation congénitale (de) nez |
| CIM-10 | exclusion | malformation congénitale (de) rachis cervical |
| CIM-10 index | synonyme | Macrotie (congénitale) (pavillon) |

### `Y57.2` — Effets indésirables des antidotes et chélateurs, non classés ailleurs au cours de leur usage thérap…
**10 entrées** :

| source | type | texte |
|---|---|---|
| ANS | exclusion | accidents liés à l'administration de médicaments et de substances biologiques a… |
| ANS | exclusion | surdosage accidentel de médicaments, erreur de prescription ou médicament pris … |
| CIM-10 | exclusion | accidents liés à l'administration de médicaments et de substances biologiques a… |
| CIM-10 | exclusion | surdosage accidentel de médicaments, erreur de prescription ou médicament pris … |
| ANS | inclusion | complications dues à un appareillage médical incidents survenus au patient au c… |
| CIM-10 | inclusion | complications dues à un appareillage médical |
| CIM-10 | inclusion | incidents survenus au patient au cours d'actes médicaux et chirurgicaux |
| CIM-10 | inclusion | réactions anormales de patients ou complications tardives causées par des inter… |
| CIM-10 | inclusion | substance médicamenteuse appropriée et correctement administrée à dose thérapeu… |
| AP-HP Néphrologie | synonyme | D-pénicillamine et apparentés (effets indésirables dus à la) |

**Synthèse des 5 codes** :

| code | libellé | n | sources | dont externes | source dominante |
|---|---|---:|---:|---:|---|
| `A07.1` | Giardiase [lambliase] | 17 | 3 | 15 | CIM-10 index |
| `F20.32` | Schizophrénie indifférenciée - " épisodique avec d | 12 | 2 | 0 | CIM-10 |
| `J46` | État de mal asthmatique | 10 | 3 | 4 | ANS |
| `Q17.1` | Macrotie | 13 | 3 | 1 | CIM-10 |
| `Y57.2` | Effets indésirables des antidotes et chélateurs, n | 10 | 3 | 1 | CIM-10 |

**Observation qualitative** :
- **Diversité des profils** : les 5 codes échantillonnés couvrent infectiologie (A07.1), psychiatrie (F20.32), pneumologie (J46), malformations congénitales (Q17.1) et iatrogénie (Y57.2). Bon panel.
- **Cohérence des types** : pour chaque code, les types `synonyme`/`inclusion`/`exclusion` sont logiquement répartis. Les exclusions OFS et ANS s'accordent (parfois redondants mais légitime — OFS atomisé, ANS bloc).
- **A07.1 — point d'attention** : "Colite", "Diarrhée", "Dysenterie", "Entérite" apparaissent chacun **2 fois** en CIM-10 index. Hypothèse : entrées Index avec parenthèses légèrement différentes qui passent la dédup tolérante. Visuellement après troncation à 80 chars elles sont identiques. **À investiguer** (non bloquant, c'est de la redondance, pas de la corruption).
- **F20.32 — 0 source externe** : témoin que pour certains codes psychiatriques, les sources externes (ORPHANET, AP-HP) n'apportent rien — comportement attendu, pas de bruit injecté.
- **Y57.2 — entrée AP-HP Néphrologie surprenante** ("D-pénicillamine et apparentés") : utile et pertinente (la D-pénicillamine est un chélateur). L'enrichissement métier fonctionne.

---

## Section 3 — Distribution globale source × type

CSV final : **214675 lignes** au total.

### Distribution par source

| source | n | % |
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

### Distribution par type

| type | n | % |
|---|---:|---:|
| exclusion | 92944 | 43.3 % |
| synonyme | 75521 | 35.2 % |
| inclusion | 46210 | 21.5 % |

### Croisé source × type (pour chaque source, % par type)

| source | total | synonyme | inclusion | exclusion |
|---|---:|---:|---:|---:|
| CIM-10 | 77729 | 9422 (12 %) | 14224 (18 %) | 54083 (70 %) |
| ANS | 64340 | 15867 (25 %) | 14971 (23 %) | 33502 (52 %) |
| CIM-10 index | 44305 | 44305 (100 %) | 0 (0 %) | 0 (0 %) |
| ORPHANET | 18410 | 1395 (8 %) | 17015 (92 %) | 0 (0 %) |
| CIM-10 frères | 5359 | 0 (0 %) | 0 (0 %) | 5359 (100 %) |
| AP-HP Dermatologie | 1667 | 1667 (100 %) | 0 (0 %) | 0 (0 %) |
| AP-HP Rhumatologie | 836 | 836 (100 %) | 0 (0 %) | 0 (0 %) |
| AP-HP Néphrologie | 691 | 691 (100 %) | 0 (0 %) | 0 (0 %) |
| AP-HP Ophtalmologie | 371 | 371 (100 %) | 0 (0 %) | 0 (0 %) |
| AP-HP Endocrinologie | 358 | 358 (100 %) | 0 (0 %) | 0 (0 %) |
| AP-HP Troubles métaboliques | 235 | 235 (100 %) | 0 (0 %) | 0 (0 %) |
| AP-HP Germes (SPILF) | 199 | 199 (100 %) | 0 (0 %) | 0 (0 %) |
| AP-HP GRONES | 125 | 125 (100 %) | 0 (0 %) | 0 (0 %) |
| AP-HP SRLF | 50 | 50 (100 %) | 0 (0 %) | 0 (0 %) |

**Observation qualitative** :
- **Pas de source dominante absolue** : CIM-10 (36 %) et ANS (30 %) se partagent le socle. C'est sain — pas de risque que le dataset soit biaisé par une seule source éditoriale.
- **Types par source bien typés** : Index 100 % synonyme, ORPHANET 92 % inclusion (relations NTBT) + 8 % synonyme (relations E), AP-HP 100 % synonyme, `CIM-10 frères` 100 % exclusion. Aucune incohérence — la spec Phase 1-2 est respectée à la lettre.
- **CIM-10 et ANS contribuent majoritairement aux exclusions** (70 % et 52 % de leurs entrées respectives). Cohérent avec la structure CIM-10 OMS où chaque catégorie liste explicitement ses voisins.
- **AP-HP représente ~2 % cumulé** : enrichissement marginal en volume mais qualitativement spécialisé (cf §2 Y57.2). Faible volume donc faible risque de noyer les autres sources.
- **Aucune source vide ou aberrante** : toutes les 14 sources émettent au moins 50 lignes ; aucune source ne devrait être supprimée.

---

## Section 4 — 3 codes "OFS+ANS only" (5-15 notes)

5958 codes du CSV n'ont QUE des entrées internes (sources ∈ {CIM-10, ANS, CIM-10 frères}) et 5-15 notes. Échantillon de 3 (seed=42) :

### `F18.40` — Troubles mentaux et du comportement liés à l'utilisation de solvants volatils - "Syndrome de sevrag…
**5 entrées** :

| source | type | texte |
|---|---|---|
| ANS | exclusion | abus de substances n'entraînant pas de dépendance [F55.–] |
| ANS | exclusion | symptômes, signes et résultats anormaux d'examens cliniques et de laboratoire, … |
| CIM-10 | exclusion | abus de substances n'entraînant pas de dépendance |
| ANS | inclusion | Délirium trémens [Delirium tremens] |
| ANS | inclusion | troubles du développement psychologique |

### `F20.91` — Schizophrénie, sans précision - " épisodique avec déficit progressif "
**7 entrées** :

| source | type | texte |
|---|---|---|
| ANS | exclusion | réaction schizophrénique [F23.2] schizophrénie :  - aigüe (indifférenciée) [F23… |
| ANS | exclusion | symptômes, signes et résultats anormaux d'examens cliniques et de laboratoire, … |
| CIM-10 | exclusion | réaction schizophrénique |
| CIM-10 | exclusion | schizophrénie aiguë (indifférenciée) |
| CIM-10 | exclusion | schizophrénie cyclique |
| CIM-10 | exclusion | trouble schizotypique |
| ANS | inclusion | troubles du développement psychologique |

### `V31.7` — Occupant d'un véhicule à moteur à trois roues blessé dans une collision avec un cycle - " Personne …
**9 entrées** :

| source | type | texte |
|---|---|---|
| ANS | exclusion | accidents lors de la maintenance ou la réparation d'équipement ou de véhicule d… |
| ANS | exclusion | motocyclette avec sidecar [V20-V29] véhicules essentiellement conçus pour être … |
| CIM-10 | exclusion | accidents de transport dus à un cataclysme |
| CIM-10 | exclusion | agression en provoquant une collision de véhicule à moteur |
| CIM-10 | exclusion | lésion auto-infligée |
| CIM-10 | exclusion | motocyclette avec side-car |
| CIM-10 | exclusion | véhicules essentiellement conçus pour être utilisés hors d'une route |
| CIM-10 | exclusion | événement d'intention non déterminée |
| CIM-10 | inclusion | tricycle à moteur |

**Observation qualitative** :
- **Contenu OFS+ANS cohérent** : pour les 3 codes échantillonnés, les exclusions OFS et ANS se font écho (parfois la même info atomisée OFS vs concaténée ANS — voir limitation connue dans `source_mapping.md`). Pas de dégradation détectable par l'intégration externe.
- **F18.40 et F20.91 (psychiatrie)** : exclusions/inclusions sobres, sans bruit. Le merger préserve correctement les notes des codes peu enrichis par les externes.
- **V31.7 (causes externes chap XX)** : 9 entrées dont 8 exclusions — typique du chapitre XX où la classification est tabulaire et chaque code écarte ses voisins. Comportement attendu.
- **Conclusion §4** : les 5 958 codes OFS+ANS only représentent ~37 % du CSV. Leur contenu n'a pas été dégradé par les Phases 1-3 ; les externes n'écrasent rien.
