# Chapter_policy : synthèse du chantier d'instruction (R1, R2, R3)

*Note de synthèse — 2026-08-12. Récapitule les échanges et itérations ayant
abouti aux trois règles figées, avant leur implémentation dans `src/`.
Documents techniques de référence : le notebook
`scripts/explore/qualite_sources_par_chapitre.ipynb` et
`docs/analyses/2026-08-09_qualite_sources_par_chapitre.md`.*

## 1. Le point de départ

Souhait initial : simplifier les fiches des chapitres XVIII (signes et
symptômes, R), XIX (lésions traumatiques, S-T), XX (causes externes, V-Y)
et XXI (facteurs Z), dont les libellés officiels sont déjà proches du
langage clinique et pour lesquels des synonymes ajoutés risquaient de
brouiller le périmètre des codes.

Deux clarifications de périmètre ont cadré tout le reste :

- la simplification porte sur **les fiches uniquement** — le CSV maître
  reste exhaustif, toutes sources confondues (un malentendu initial dans
  l'autre sens a été corrigé) ;
- le chapitre XVIII est un cas à part : les codes R ont de vraies
  variantes d'usage (« mal de tête » pour R51), on y **garde les sources
  réelles** et on n'exclut que la future génération LLM.

## 2. Ce que l'analyse des données a montré

Plutôt que de trancher sur intuition, une analyse du CSV maître et du
dictionnaire CepiDc brut a été menée (puis consolidée dans le notebook).
Quatre constats structurants :

1. **Les sources externes métier (AP-HP, ORPHANET) sont marginales sur
   XVIII-XXI** — les exclure ne coûte presque rien.
2. **L'Index vol3 a un problème de format, pas de légitimité** : ses
   entrées sont des chemins d'index alphabétique inversé (« Traumatisme(s)
   (de) (voir aussi…), artère, cubitale… »), pas des formulations de CRH.
3. **CepiDc est excellent sur les chapitres diagnostiques** (« poussée
   BPCO », « hernie étranglée ») **mais dangereux sur T36-T50 et X/Y/Z** :
   logique du certificat de décès — noms de médicaments nus
   (« Furosémide » → T50.1), mentions de prise/traitement. Taux de motifs
   parasites : ≤ 1 % sur les chapitres classiques, 9-12 % sur X/Y/Z.
4. **Fausse alerte instructive** : hors de ces chapitres, le motif « mot
   unique » capture des acronymes (GEA, PAVM) et éponymes (Dupuytren) qui
   sont d'excellents synonymes. Conclusion : une politique par
   chapitre/bloc suffit, pas de curation textuelle générale du CepiDc.

À quoi s'est ajouté un constat issu du merge CepiDc (chantier 1) :
les **fiches catégories** étaient écrasées par CepiDc (part médiane 76 %,
325 catégories au-dessus de 80 %), faute de plafond par source là où les
fiches feuilles plafonnent à 10.

## 3. Les trois règles et leur trajectoire

### R1 — Politique par plage de codes × famille de sources

**Forme finale** : sources externes (AP-HP, ORPHANET, CepiDc, futures LLM)
exclues des fiches sur XIX, XX, XXI ; règle de bloc explicite excluant
CepiDc sur T36-T50 ; flag `generation_llm: false` sur XVIII-XXI ; OFS/ANS
jamais filtrés. Résolution bloc > chapitre > défaut, **par remplacement**
(une règle de bloc remplace la règle de chapitre, elle n'en hérite pas).

**Ce qui a changé en cours de route** :
- une sous-règle initiale « filtrer les renvois ANS "États mentionnés
  en…" de la section Formulations » a été **retirée** : vérification
  faite, ANS n'alimente pas cette section — les renvois apparaissent dans
  « Périmètre clinique du code », où ils sont une information légitime ;
- l'exclusion de l'Index sur XIX/XXI, d'abord dans R1, en a été **sortie**
  quand CC a montré que le format « chemin d'index » domine encore plus
  sur des chapitres non exclus (XV : 90 %, XVI : 85 %, contre 78 % sur
  XIX). Le critère pertinent est le format de l'entrée, pas le chapitre —
  d'où la règle transversale R3.

### R2 — Plafonnement par source des fiches catégories

**Forme finale** : plafond par source de **20** pour les fiches catégories
(les feuilles restent à 10), échantillonnage par tirage au sort
reproductible.

**Comment 20 a été choisi** : calibration par balayage (5/10/15/20, étendu
à 30). Résultat : l'essentiel du bénéfice vient d'avoir un plafond tout
court (catégories > 80 % : de 226 à ~41-54 ; médiane de 0,72 à ~0,48) ;
entre 5 et 20 les métriques d'équilibre sont plates alors que le volume
conservé triple ; à 30 le bénéfice se dégrade franchement. 20 est le
dernier palier avant dégradation. L'unité de convention avec le plafond 10
des feuilles a été envisagée puis écartée : elle aurait coûté 9 649
formulations pour un gain de 7 catégories — les viviers sont d'un ordre de
grandeur différent, deux clés YAML distinctes sont justifiées.

### R3 — Normalisation et filtrage par format de l'Index vol3

C'est la règle qui a demandé le plus d'itérations, parce qu'elle est la
seule qui **réécrit du texte** au lieu d'en écarter.

**Étape 1 — détecteurs d'exclusion.** Deux variantes instrumentées et
relues sur échantillon : trois motifs (27 VP / 1 FN / 0 FP) et stricte
(28 / 0 / 0). Problème : elles écartaient respectivement 85 % et 97 % de
l'Index — le remède supprimait quasiment la source.

**Étape 2 — la « troisième voie ».** CC a repéré que 4 231 entrées entre
les deux détecteurs étaient du type « Rectite (à), amibienne » : contenu
bon, seul le *formatage* est de l'index. D'où le basculement : normaliser
les formes courtes (1-2 segments) au lieu de choisir entre deux
amputations. Périmètre normalisable : 13 220 entrées (36 % de l'Index).

**Étape 3 — itérations du normalisateur**, chacune validée par relecture
manuelle d'un échantillon à graine fixée, avec un critère asymétrique :
zéro fautive tolérée (une formulation au sens faux corrompt le corpus),
les dégradées-mais-compréhensibles tolérées jusqu'à ~10-15 % (style
télégraphique, registre qui existe dans les vrais CRH).

| Version | Correctes / Dégradées / Fautives | Ce qui a été corrigé ensuite |
|---|---|---|
| v1 | 11 / 33 / 6 (sur 50) | Retrait **complet** des parenthèses qualifiantes (justification volume 3 : modificateurs non essentiels, sans effet sur l'affectation) ; inversion des éponymes à préposition traînante (« Lipschütz, ulcère de » → « ulcère de Lipschütz ») avec élision ; casse protégée par lexique hors Index |
| v2 | 57 / 40 / 3 (sur 100) | Découverte clé de CC : les connecteurs de liaison « (de) », « (à) » ne sont pas des modificateurs mais des **marqueurs de rection** — les retirer détruisait une information. Décision amendée : les **consommer comme joints** (« Hypoplasie (de), cerveau » → « hypoplasie du cerveau »), avec le genre tiré des rections attestées dans le corpus ; extension de l'inversion aux têtes nues (« Xxxx, syndrome ») ; exclusion des abréviations d'index |
| v3 | 80 / 20 / 0 | Zéro fautive atteint. Cause unique des dégradées : joint non inséré faute de rection attestée. Deux leviers de code (pas de données) : forme nue admise en dernier recours après les contractées, seuil des contractées abaissé à 1 |
| v4 | 85 / 15 / 0 — **figée** | Zéro fautive pour la 2e fois consécutive ; les 15 % restants sans cause corrigeable par motif (têtes sans aucune attestation de rection : aucun motif ne devine le genre de « dactylos ») → règle d'arrêt appliquée |

**Trouvailles à retenir de la série** (documentées comme pitfalls) :
- **dualité des lexiques** : rections construites AVEC l'Index (la syntaxe
  interne de ses entrées est du français naturel), casse SANS l'Index (il
  capitalise toute tête par convention). Fusionner dans un sens
  minusculise « Borrelia », dans l'autre ampute les rections ;
- l'absence d'attestation de rection **protège les adjectifs** sans avoir
  à les identifier (pas d'article attesté → pas de joint → « rectite
  amibienne », jamais « rectite à l'amibienne ») ;
- l'ordre des formes compte : contractée avant nue (« du cuir chevelu »,
  pas « de cuir chevelu ») ;
- asymétrie appliquée partout : au moindre doute sur une tête, l'entrée
  est écartée, jamais normalisée.

**Bilan chiffré final de R3** : sur 36 627 entrées Index, 12 488 retenues
(dont 11 772 réécrites), 24 139 écartées — plus du double du meilleur
détecteur d'exclusion (5 424).

## 4. Principes transversaux tenus sur toute la série

1. **Le CSV maître n'est jamais touché** : les trois règles s'appliquent à
   l'assemblage des fiches ; pour R3, la colonne `texte` garde la forme
   source de l'Index comme seule référence auditable.
2. **Rien dans `src/` pendant l'instruction** : tout a été prototypé dans
   le notebook ; l'implémentation est le chantier qui commence, et le
   notebook basculera alors sur l'implémentation réelle (chiffres
   identiques exigés).
3. **Chaque décision est chiffrée avant d'être prise** : calibration de
   R2, typologie de l'Index, échantillons relus à graine fixée pour R3.
4. **Les relectures humaines deviennent des tests** : les paires
   source→attendu validées manuellement seront les tests dorés de
   l'implémentation.

## 5. Ce que le chantier d'implémentation doit livrer

YAML déclaratif (plages, familles de sources, deux plafonds, résolution
par remplacement), module de normalisation R3 portant la v4 à
l'identique, application dans `cards.py`, tests (dorés R3, non-fuite LLM
par fixture, remplacement bloc/chapitre, dualité des lexiques,
déterminisme), rebuild des 18 000 fiches avec rapport de composition
avant/après et fiches témoins. Prompt détaillé :
`prompt_cc_chantier_chapter_policy.md`.
