# Audit des divergences textuelles OFS ↔ ANS

Source : `reports/note_merges.csv` (produit par `merge.find_note_merges`).

Périmètre : **5,425 cas** où `difference_significative=True` (= les textes OFS et ANS restent différents même après normalisation complète : casse, accents, ponctuation interne, NBSP).

Sortie générée par `scripts/explore/_build_text_divergence_review.py` (seed=42). Ré-exécutable pour stabilité des échantillons.

---

## 1. Statistiques globales

### 1.1 Distribution par chapitre CIM-10

Chapitre déduit du premier caractère du code (avec disambiguïsation C/D et H/H pour les chapitres II/III et VII/VIII).

| chapter |      len |
| ----- | -------- |
| XX    |      794 |
| XIX   |      664 |
| II    |      335 |
| V     |      324 |
| XVIII |      324 |
| XI    |      315 |
| XIII  |      294 |
| X     |      259 |
| IX    |      253 |
| IV    |      237 |
| XIV   |      231 |
| I     |      216 |
| XXI   |      211 |
| XII   |      211 |
| XVII  |      197 |
| XV    |      133 |
| VI    |      132 |
| XVI   |      118 |
| III   |       92 |
| VII   |       56 |
| VIII  |       29 |

### 1.2 Distribution par type de note

Le pipeline actuel ne distingue que `inclusion` et `exclusion` (les `note_editorial` OFS ne sont pas matchées avec OWL, donc n'apparaissent jamais dans `note_merges.csv`).

| type      |      len |
| --------- | -------- |
| exclusion |    4,372 |
| inclusion |    1,053 |

### 1.3 Distribution par longueur de divergence

`delta_len = |len(ANS) - len(OFS)|` (différence absolue en nombre de caractères).

| delta_bucket |      len |
| ------ | -------- |
| > 100  |    2,471 |
| 51–100 |    1,113 |
| 6–20   |    1,101 |
| 21–50  |      719 |
| ≤ 5    |       21 |

**Sens du delta** :

- ANS strictement plus long : **5,387** cas (99%)
- OFS strictement plus long : **22** cas (0%)
- Longueurs égales : **16** cas (0%)

---

## 2. Tirage stratifié — 50 cas représentatifs

Échantillonnage déterministe (seed=42).

### 2.1 Cas où ANS est strictement plus long que OFS (10 cas)

*Hypothèse : ANS contient des précisions additionnelles (code source, qualificatifs cliniques modernes, etc.) absentes d'OFS 2006.*

- **I78.1** (exclusion) — `len(OFS)=19` / `len(ANS)=252`
  - OFS : naevus (à) (en) SAI
  - ANS : nævus (à) (en) :
 - SAI [D22.-] 
 - bleu [D22.-] 
 - flammeus [Q82.5] 
 - fraise [Q82.5] 
 - mélanocytes [D22.-] 
 - pigmentaire [D22.-] 
 - pileux [D22.-] 
 - sanguin [Q82.5] 
 - tache de vin [Q82.5]…
- **Y42** (exclusion) — `len(OFS)=20` / `len(ANS)=139`
  - OFS : hormones ocytociques
  - ANS : hormones :
 - ocytociques [Y55.0] 
 - parathyroïdiennes et leurs dérivés [Y54.7] 
minéralocorticoïdes et leurs antagonistes [Y54.0-Y54.1] 

- **I80** (exclusion) — `len(OFS)=25` / `len(ANS)=429`
  - OFS : syndrome post-phlébitique
  - ANS : phlébite et thrombophlébite (de) :
 - compliquant :
  - avortement, grossesse extra-utérine ou molaire [O00-O07]  [O08.7] 
  - grossesse, accouchement et puerpéralité [O22.-]  [O87.-] 
 - intracrânien…
- **S24** (exclusion) — `len(OFS)=37` / `len(ANS)=46`
  - OFS : lésion traumatique du plexus brachial
  - ANS : lésion traumatique du plexus brachial [S14.3]

- **R52** (exclusion) — `len(OFS)=17` / `len(ANS)=476`
  - OFS : douleur (de) dent
  - ANS : céphalée [R51]
colique néphrétique [N23]
douleur (de) :
 - abdominale [R10.-] 
 - articulaire [M25.5] 
 - dent [K08.8] 
 - dos [M54.9] 
 - épaule [M25.5] 
 - gorge [R07.0] 
 - langue [K14.6] 
 - mamma…
- **Q01** (inclusion) — `len(OFS)=21` / `len(ANS)=108`
  - OFS : méningocèle cérébrale
  - ANS : encéphalomyélocèle
hydroencéphalocèle
hydroméningocèle crânienne
méningocèle cérébrale
méningoencéphalocèle

- **Z87.5** (exclusion) — `len(OFS)=111` / `len(ANS)=151`
  - OFS : surveillance d'une grossesse en cours avec des antécédents obstétricaux pathologiques et difficultés à procréer
  - ANS : avortements à répétition [N96]
surveillance d'une grossesse en cours avec des antécédents obstétricaux pathologiques et difficultés à procréer [Z35.-]

- **A21** (inclusion) — `len(OFS)=26` / `len(ANS)=136`
  - OFS : fièvre (de) mouche du daim
  - ANS : fièvre (de) :
 - mouche du daim
 - transmise par le lapin
infection à Francisella tularensis subsp. tularensis [Francisella tularensis]

- **V87** (exclusion) — `len(OFS)=29` / `len(ANS)=66`
  - OFS : collision impliquant cycliste
  - ANS : collision impliquant:
 - cycliste [V10-V19] 
 - piéton [V01-V09] 

- **J42** (exclusion) — `len(OFS)=34` / `len(ANS)=216`
  - OFS : bronchite chronique emphysémateuse
  - ANS : bronchite chronique :
 - asthmatique [J44.-] 
 - avec obstruction des voies respiratoires [J44.-] 
 - emphysémateuse [J44.-] 
 - simple et mucopurulente [J41.-] 
maladie pulmonaire obstructive chroniq…

### 2.2 Cas où OFS est strictement plus long que ANS (10 cas)

*Hypothèse : OFS conserve des notes historiques détaillées que l'ANS a synthétisées ou abrégées.*

- **T29** (inclusion) — `len(OFS)=81` / `len(ANS)=69`
  - OFS : brûlures et corrosions classées dans plus d'une catégorie en (T20-T25), (T26-T28)
  - ANS : brulures et corrosions classées dans plus d'une catégorie en T20-T28

- **I11** (inclusion) — `len(OFS)=87` / `len(ANS)=59`
  - OFS : tout état classé en I50.-, I51.4, I51.5, I51.6, I51.7, I51.8, I51.9 dû à l'hypertension
  - ANS : tout état classé en I50.-, I51.4-I51.9 dû à l'hypertension

- **C82** (inclusion) — `len(OFS)=64` / `len(ANS)=50`
  - OFS : lymphome folliculaire non hodgkinien avec ou sans zones diffuses
  - ANS : lymphome folliculaire avec ou sans zones diffuses

- **P24** (inclusion) — `len(OFS)=49` / `len(ANS)=40`
  - OFS : pneumopathie néonatale résultant d'une aspiration
  - ANS : pneumopathie d'inhalation du nouveau-né

- **F03** (exclusion) — `len(OFS)=54` / `len(ANS)=19`
  - OFS : démence sénile avec delirium ou état confusionnel aigu
  - ANS : sénilité SAI [R54]

- **C93** (inclusion) — `len(OFS)=55` / `len(ANS)=21`
  - OFS : le code morphologique M989 avec code de comportement /3
  - ANS : leucémie monocytoïde

- **P78.3** (exclusion) — `len(OFS)=96` / `len(ANS)=67`
  - OFS : diarrhée néonatale SAI dans les pays où cette affection peut être présumée d'origine infectieuse
  - ANS : diarrhée du nouveau-né :
 - SAI  [A09.9] 
 - infectieuse  [A09.0] 

- **T40** (exclusion) — `len(OFS)=119` / `len(ANS)=42`
  - OFS : pharmacodépendance et troubles mentaux et du comportement apparentés, liés à l'utilisation de substances psycho-actives
  - ANS : intoxication signifiant ébriété [F10-F19]

- **C92** (inclusion) — `len(OFS)=70` / `len(ANS)=42`
  - OFS : les codes morphologiques M986-M988, M9930 avec code de comportement /3
  - ANS : leucémie :
 - granulocytaire
 - myélogène

- **T00-T07** (inclusion) — `len(OFS)=192` / `len(ANS)=150`
  - OFS : lésions traumatiques, selon leur type, d'au moins deux parties du corps classées en (S00-S09), (S10-S19), (S20-S29), (S30-S39), (S40-S49), (S50-S59), (S60-S69), (S70-S79), (S80-S89), (S90-S99)
  - ANS : atteinte bilatérale de membres de la même partie du corps
lésions traumatiques, selon leur type, d'au moins deux parties du corps classées en S00-S99


### 2.3 Cas de longueurs similaires (Δ ≤ 5 caractères, 10 cas)

*Variations de wording sans changement de volume : reformulations, synonymes lexicaux, différences d'orthographe légères, etc.*

- **G05** (inclusion) — `len(OFS)=77` / `len(ANS)=77`
  - OFS : méningo-encéphalite et méningomyélite au cours d'affections classées ailleurs
  - ANS : méningoencéphalite et méningomyélite au cours d'affections classées ailleurs

- **P08** (inclusion) — `len(OFS)=137` / `len(ANS)=137`
  - OFS : les états mentionnés, sans autre précision, comme cause de mortalité, de morbidité ou de soins supplémentaires du foetus ou du nouveau-né
  - ANS : les états mentionnés, sans autre précision, comme cause de mortalité, de morbidité ou de soins supplémentaires du fœtus ou du nouveau-né

- **D17** (inclusion) — `len(OFS)=63` / `len(ANS)=68`
  - OFS : les codes morphologiques M885-M888 avec code de comportement /0
  - ANS : les codes morphologiques M885– à M888– avec code de comportement /0

- **C43** (inclusion) — `len(OFS)=63` / `len(ANS)=68`
  - OFS : les codes morphologiques M872-M879 avec code de comportement /3
  - ANS : les codes morphologiques M872– à M879– avec code de comportement /3

- **K27** (inclusion) — `len(OFS)=26` / `len(ANS)=26`
  - OFS : ulcère gastro-duodénal SAI
  - ANS : ulcère gastroduodénal SAI

- **D18** (inclusion) — `len(OFS)=63` / `len(ANS)=68`
  - OFS : les codes morphologiques M912-M917 avec code de comportement /O
  - ANS : les codes morphologiques M912– à M917– avec code de comportement /0

- **D03** (inclusion) — `len(OFS)=63` / `len(ANS)=68`
  - OFS : les codes morphologiques M872-M879 avec code de comportement /2
  - ANS : les codes morphologiques M872– à M879– avec code de comportement /2

- **Z03** (inclusion) — `len(OFS)=227` / `len(ANS)=227`
  - OFS : personnes ayant certains symptômes ou signes d'un état anormal qui nécessite un examen plus approfondi, mais chez qui après examen et mise en observation, un traitement ou des soins médicaux n'apparai…
  - ANS : personnes ayant certains symptômes ou signes d'un état anormal qui nécessite un examen plus approfondi, mais chez qui un traitement ou des soins médicaux n'apparaissent pas comme nécessaires après exa…
- **A84** (inclusion) — `len(OFS)=51` / `len(ANS)=51`
  - OFS : méningo-encéphalite virale transmise par des tiques
  - ANS : méningoencéphalite virale transmise par des tiques

- **Z90** (inclusion) — `len(OFS)=83` / `len(ANS)=83`
  - OFS : perte d'une partie du corps NCA après intervention chirurgicale ou post-traumatique
  - ANS : perte d'une partie du corps NCA après intervention chirurgicale ou posttraumatique


### 2.4 Cas dans les chapitres cliniques majeurs (II, IX, XIX — 10 cas)

*Chapitres à forte fréquence d'annotation (tumeurs, cardiovasculaire, traumatismes).*

- **I82** (exclusion) — `len(OFS)=45` / `len(ANS)=495`
  - OFS : embolie et thrombose veineuse (de) cérébrales
  - ANS : embolie et thrombose veineuses (de) :
 - cérébrales [I63.6]  [I67.6] 
 - compliquant :
  - avortement, grossesse extra-utérine ou molaire [O00-O07]  [O08.7] 
  - grossesse, accouchement et puerpéralit…
- **T81.1** (exclusion) — `len(OFS)=114` / `len(ANS)=365`
  - OFS : choc anaphylactique dû à effets indésirables d'une substance médicamenteuse appropriée et correctement administrée
  - ANS : choc :
 - anaphylactique :
  - SAI [T78.2] 
  - dû à :
   - effets indésirables d'une substance médicamenteuse appropriée et correctement administrée [T88.6] 
   - sérum [T80.5] 
 - anesthésique [T88.…
- **I46** (exclusion) — `len(OFS)=58` / `len(ANS)=212`
  - OFS : compliquant avortement, grossesse extra-utérine ou molaire
  - ANS : choc cardiogénique [R57.0]
compliquant :
 - acte de chirurgie obstétricale ou acte à visée diagnostique et thérapeutique obstétrical [O75.4] 
 - avortement, grossesse extra-utérine ou molaire [O00-O07…
- **T45.8** (exclusion) — `len(OFS)=16` / `len(ANS)=37`
  - OFS : immunoglobulines
  - ANS : fer [T45.4]
immunoglobulines [T50.9]

- **T88** (exclusion) — `len(OFS)=110` / `len(ANS)=733`
  - OFS : complications précisées classées ailleurs, telles que complications dues à anesthésie au cours de puerpéralité
  - ANS : complications après :
 - acte à visée diagnostique et thérapeutique NCA [T81.-] 
 - injection thérapeutique, perfusion et transfusion [T80.-] 
- complications précisées classées ailleurs, telles que :…
- **D14.0** (exclusion) — `len(OFS)=51` / `len(ANS)=404`
  - OFS : bord postérieur de la cloison nasale et des choanes
  - ANS : bord postérieur de la cloison nasale et des choanes [D10.6]
bulbe olfactif [D33.3]
cartilage de l'oreille [D21.0]
conduit auditif (externe) [D22.2]  [D23.2]
nez :
 - SAI [D36.7] 
 - peau [D22.3]  [D23…
- **I05** (inclusion) — `len(OFS)=89` / `len(ANS)=84`
  - OFS : affections classées en I05.0, I05.2, I05.8, I05.9 précisées ou non d'origine rhumatismale
  - ANS : affections classées en I05.0 et I05.2-I05.9 précisées ou non d'origine rhumatismale

- **I46.1** (exclusion) — `len(OFS)=38` / `len(ANS)=117`
  - OFS : mort subite avec infarctus du myocarde
  - ANS : mort subite :
 - SAI [R96.-] 
 - avec :
  - infarctus du myocarde [I21-I22] 
  - trouble de la conduction [I44-I45] 

- **I82** (exclusion) — `len(OFS)=88` / `len(ANS)=495`
  - OFS : embolie et thrombose veineuse (de) intracrâniennes et intrarachidiennes, pyogènes ou SAI
  - ANS : embolie et thrombose veineuses (de) :
 - cérébrales [I63.6]  [I67.6] 
 - compliquant :
  - avortement, grossesse extra-utérine ou molaire [O00-O07]  [O08.7] 
  - grossesse, accouchement et puerpéralit…
- **T78.4** (exclusion) — `len(OFS)=84` / `len(ANS)=263`
  - OFS : type précisé de réaction allergique, telle que gastro-entérite et colite allergiques
  - ANS : réaction allergique SAI due à une substance médicamenteuse appropriée et correctement administrée [T88.7]
type précisé de réaction allergique, telle que :
 - dermite [L23-L25]  [L27.-] 
 - gastroentér…

### 2.5 Cas tirés au hasard (10 cas)

*Échantillon non-stratifié — contrôle.*

- **J84** (exclusion) — `len(OFS)=110` / `len(ANS)=275`
  - OFS : pneumopathie lymphoïde interstitielle résultant de la maladie due au virus de l'immunodéficience humaine [VIH]
  - ANS : affections pulmonaires interstitielles médicamenteuses [J70.2-J70.4]
emphysème interstitiel [J98.2]
maladies du poumon dues à des agents externes [J60-J70]
pneumopathie lymphoïde interstitielle résult…
- **F18.7** (exclusion) — `len(OFS)=78` / `len(ANS)=233`
  - OFS : syndrome de Korsakov induit par l'alcool ou d'autres substances psycho-actives
  - ANS : état psychotique induit par l'alcool ou d'autres subtances psychoactives [F10-F19 avec le quatrième caractère .5]
syndrome de Korsakov induit par l'alcool ou d'autres substances psychoactives [F10-F19…
- **T20** (inclusion) — `len(OFS)=27` / `len(ANS)=147`
  - OFS : cuir chevelu [toute partie]
  - ANS : cuir chevelu [toute partie]
lèvre
nez (cloison)
œil avec d'autres parties de la face, de la tête et du cou
oreille [toute partie]
région temporale

- **J04** (exclusion) — `len(OFS)=56` / `len(ANS)=97`
  - OFS : laryngite obstructive aiguë [croup] et épiglottite aiguë
  - ANS : laryngisme (striduleux) [J38.5]
laryngite obstructive aigüe [croup] et épiglottite aigüe [J05.-]

- **D14.0** (exclusion) — `len(OFS)=25` / `len(ANS)=404`
  - OFS : conduit auditif (externe)
  - ANS : bord postérieur de la cloison nasale et des choanes [D10.6]
bulbe olfactif [D33.3]
cartilage de l'oreille [D21.0]
conduit auditif (externe) [D22.2]  [D23.2]
nez :
 - SAI [D36.7] 
 - peau [D22.3]  [D23…
- **X45** (inclusion) — `len(OFS)=30` / `len(ANS)=169`
  - OFS : alcool propylique [1-propanol]
  - ANS : alcool :
 - SAI
 - butylique [1-butanol]
 - éthylique [éthanol]
 - isopropylique [2-propanol]
 - méthylique [méthanol]
 - propylique [1-propanol]
fusel [huile de fusel]

- **J38.1** (exclusion) — `len(OFS)=19` / `len(ANS)=28`
  - OFS : polypes adénomateux
  - ANS : polypes adénomateux [D14.1]

- **I26** (exclusion) — `len(OFS)=58` / `len(ANS)=136`
  - OFS : compliquant avortement, grossesse extra-utérine ou molaire
  - ANS : compliquant :
 - avortement, grossesse extra-utérine ou molaire [O00-O07]  [O08.2] 
 - grossesse, accouchement et puerpéralité [O88.-] 

- **S30-S39** (exclusion) — `len(OFS)=50` / `len(ANS)=383`
  - OFS : effets dus à un corps étranger dans anus et rectum
  - ANS : brulures et corrosions [T20-T32]
effets dus à un corps étranger dans :
 - anus et rectum [T18.5] 
 - appareil génito-urinaire [T19.-] 
 - estomac, intestin grêle et côlon [T18.2-T18.4] 
fracture du ra…
- **P39.1** (exclusion) — `len(OFS)=26` / `len(ANS)=35`
  - OFS : conjonctivite gonococcique
  - ANS : conjonctivite gonococcique [A54.3]


---

## 3. Patterns détectés automatiquement

### 3.1 Présence de références à d'autres codes (`[A18.3]`, etc.)

- OFS contient une référence-code : **0** (0%)
- ANS contient une référence-code : **3,723** (69%)

**Lecture** : les notes d'exclusion citent typiquement le code de redirection entre crochets (`[A18.3]`). Si ANS systématise ces références plus que OFS, cela milite pour conserver les versions ANS quand elles sont strictement enrichies.

### 3.2 Inclusion textuelle (substring)

- ANS est un sous-texte d'OFS (ANS ⊂ OFS) : **0** (0%)
- OFS est un sous-texte d'ANS (OFS ⊂ ANS) : **2,693** (50%)

**Lecture** : un texte qui en contient un autre indique souvent que l'une des deux versions a ajouté des qualificatifs (ex. `« asthme »` vs `« asthme allergique extrinsèque »`). Le côté qui contient l'autre est, en première approximation, la version *plus précise*.

### 3.3 Pattern OFS-substring-of-ANS dominant ?

Le ratio `OFS ⊂ ANS` (ANS plus riche) vs `ANS ⊂ OFS` (OFS plus riche) donne un signal direct sur la direction d'enrichissement éditorial. À examiner avant de figer la priorité OFS sur le libellé.

---

## 4. Questions à trancher pour raffiner la politique

1. **Sur les ~2,693 cas où OFS ⊂ ANS** (ANS strictement enrichi par rapport à OFS), faut-il garder OFS (politique actuelle) ou préférer ANS quand on a la garantie qu'il contient au moins l'info OFS ? La règle « OFS prime sur le libellé textuel » peut-elle être conditionnée à `len(OFS) ≥ len(ANS)` ?

2. **Sur les ~3,723 cas où une seule des deux versions porte les références-codes** (`[X##.#]`), faut-il privilégier la version annotée ? Ce sont des métadonnées de redirection qui restent utiles au LLM.

3. **Distinction inclusion vs exclusion** : la politique « OFS prime » s'applique-t-elle uniformément, ou faudrait-il moduler par type de note ? Les exclusions ANS peuvent comporter des codes [A18.3] de redirection à préserver ; les inclusions ANS sont plus souvent des reformulations stylistiques sans valeur clinique ajoutée.

4. **Chapitre XX (causes externes)** : les libellés ANS y sont souvent très différents d'OFS (révisions OMS post-2006 importantes pour les accidents de transport). Faut-il un override par chapitre, par exemple ANS prime pour XX et XXI ?

5. **Logging suffisant ?** Le rapport actuel `note_merges.csv` log les alternatives ANS mais le CSV final n'expose qu'une seule version. Faut-il aussi exporter dans `inclusions_exclusions_synonymes.csv` les variantes ANS — par exemple comme lignes additionnelles avec `source=ANS` — quand `difference_significative=True` ? Le LLM bénéficierait des deux formulations.