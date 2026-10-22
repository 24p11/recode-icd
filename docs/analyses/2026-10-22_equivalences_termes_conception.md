# Dictionnaire d'équivalences entre mots — analyse d'ouverture (2026-10-22)

> Chantier de conception (brief RF du 2026-10-22, archivé dans
> `docs/sessions/2026-10-22_prompt_chantier_equivalences.md`). Objet :
> un dictionnaire de correspondances entre MOTS (abréviations,
> variantes), indépendant des codes, pour élargir la recherche de
> `codeur` — options pour les points 1, 2 et 4, **rien n'est mis en
> œuvre ni tranché ici**. Mesures reproductibles :
> `scripts/explore/mesure_equivalences_termes.py`.

## 1. État vs besoin : rien d'équivalent n'existe, trois acquis servent

| Acquis | Ce qu'il apporte | Ce qu'il n'est pas |
|---|---|---|
| Le vivier des 172 049 formulations (109 987 livrées) | **la mine** d'auto-extraction : abréviations réelles (CepiDc = langage de certificat) et expansions co-occurrentes par code | des équivalences entre mots — ce sont des formulations PAR CODE |
| Les patrons de curation (dagger_curation.csv, registre_formulations.yaml, notes_cim_curated.csv) | le circuit éprouvé : candidats calculés → relecture ligne à ligne → table curée = source de vérité → export versionné | — |
| Le CONTRAT et la livraison versionnée | le canal : un export de plus, additif, `format_version` intacte | — |

Le chantier « synonymes LLM » du backlog (fiches à compléter) est un
objet DIFFÉRENT — des formulations par code — mais complémentaire : le
même circuit de relecture servira les deux, et les équivalences
amélioreront la recherche sans gonfler les fiches. Les trois lexiques
R3 (rections/casse/juxtaposition) sont de l'outillage grammatical de
normalisation, pas des équivalences — rien à réutiliser directement.

## 2. Mesures (vivier des formulations, 2026-10-22)

- **828 abréviations distinctes** (tokens tout-majuscules 2-6 lettres,
  hors SAI/NCA), dont **776 dans CepiDc** — le langage réel. Tête :
  AVP (523 occ.), MI (450), LMNH, MIG/MID, IV, ORL, SARM, IDM, AVC,
  HTA (77 occ., 27 codes)…
- **623 paires (abréviation ↔ expansion) auto-extraites** par
  co-occurrence sur le même code avec l'heuristique des initiales —
  qualité visiblement bonne (PTH ↔ prothèse totale hanche, PAC ↔
  pontage aorto-coronaire, CIV, HSD, RVM…), **rappel limité** : HTA,
  IDM, AVC échappent à l'heuristique (initiales intra-mot :
  HyperTension Artérielle). L'auto-extraction amorce, elle ne suffit
  pas.
- **3 418 familles morphologiques** à plusieurs formes dans le
  vocabulaire (19 652 mots ≥ 6 lettres) : tumeur/tumeurs,
  fracture/fracturaire… Les fautes réelles y sont déjà (pulmonare,
  pulmoniare — CepiDc), ce qui sert la recherche par trigrammes de
  `codeur`, pas le dictionnaire.
- **Hors de portée mécanique, à déclarer** : les variantes savantes
  (rein↔rénal, cœur↔cardiaque, foie↔hépatique), les ambiguïtés (IRC,
  IC, PR, MI…), et les fréquences en CRH réels (corpus hors dépôt —
  la vraie mesure d'usage sera le journal de recherche de `codeur`).

**Pièges mesurés, à graver dans le futur chantier :**

1. les chiffres romains (II, III : 271 occ.) et les codes (BK, LSD)
   passent le filtre « tout-majuscules » — l'auto-extraction propose,
   l'humain tranche ;
2. la **latéralité est une famille compositionnelle** (MIG/MID,
   MSG/MSD, LSD/LSG/LID/LIG : membre/lobe + G/D) — la traiter par
   lignes individuelles multiplierait les entrées ; une règle déclarée
   (suffixe G/D) est une option, des lignes explicites en sont une
   autre (plus simple, ~20 lignes) ;
3. le **radical ne vaut pas équivalence** : « cardia » (anatomie) ≠
   « cardiaque » ; aucun stemming automatique ne doit entrer dans le
   dictionnaire sans relecture.

## 3. Options de conception

### P1 — Le format : une table curée, un export livré

**Source de vérité** (option A, recommandée — patron
`dagger_curation.csv`) : `referentials/curation/equivalences_termes.csv`,
une ligne par équivalence orientée :

| Colonne | Contenu |
|---|---|
| `terme` | forme PLIÉE (minuscules, sans accent — la forme que `codeur` compare déjà) |
| `equivalent` | idem, expressions multi-mots admises |
| `type` | `abreviation` \| `variante_morphologique` \| `variante_savante` \| `synonyme` |
| `sens` | `bidirectionnel` \| `vers_equivalent` (FA → fibrillation auriculaire, jamais l'inverse) |
| `source` | `formulations` (auto-extraction) \| `manuel` \| `llm` \| `usage_codeur` |
| `statut` | `propose` \| `relu` — **seules les lignes `relu` sont livrées** |
| `commentaire` | une ligne (l'ambiguïté levée, la spécialité…) |

**Export livré** : `equivalences.csv` dans le paquet (lignes `relu` +
`version_livraison`), généré par `preparer_livraison.py` comme
`codes.csv` — additif, `format_version` inchangée, section au CONTRAT.
Les candidats `propose` vivent dans la table curée (ou un fichier de
candidats séparé, cf. P4) mais ne sortent JAMAIS dans la livraison.
Option B (YAML façon registre) : lisible mais inadapté au volume
(centaines → milliers de lignes) et à l'import de candidats.

### P2 — Les ambiguïtés : la multiplicité EST la déclaration

**Option A (recommandée)** : plusieurs lignes pour un même `terme`
(IRC → insuffisance rénale chronique ; IRC → insuffisance respiratoire
chronique), et `codeur` élargit en OU sur tous les équivalents — pour
une RECHERCHE, le rappel prime, le classement fait le tri ; le
commentaire documente l'ambiguïté. La colonne `contexte` (spécialité)
n'est PAS créée en v1 : aucun consommateur ne saurait l'exploiter
aujourd'hui — on l'ajoutera si l'usage le réclame (colonne additive).
**Option B** : `contexte` dès la v1 — coût de curation immédiat pour un
bénéfice hypothétique.

### P4 — Le circuit : recode-icd seule source, `codeur` propose

```
journaux codeur (recherche → code choisi ; recherches sans résultat)
        │  export de candidats (CSV, trace — JAMAIS une entrée du build)
        ▼
data/equivalences/candidats_codeur_<date>.csv
        │  relecture RF ligne à ligne (le circuit éprouvé)
        ▼
referentials/curation/equivalences_termes.csv   (statut: propose → relu)
        │  build/livraison
        ▼
equivalences.csv livré  →  consommé par codeur (et les autres)
```

- **recode-icd est la seule source de vérité** ; la table de `codeur`
  est un cache de la livraison + ses candidats locaux.
- **À trancher — le statut des candidats locaux côté `codeur`** :
  (a) *strict* : un candidat est inactif tant qu'il n'est pas revenu
  par une livraison (cohérence totale, latence d'un cycle) ;
  (b) *optimiste* : `codeur` applique ses candidats en attendant la
  relecture (réactivité pour les testeurs, divergence temporaire, et
  un candidat rejeté doit être désactivé à la livraison suivante).
  La règle « jamais deux dictionnaires qui divergent » plaide pour
  (a) ; l'usage par 100 testeurs peut plaider pour (b) borné (candidats
  marqués localement comme non validés).
- Le même export sert la boucle de correction et, plus tard, les
  candidats de prompt — un seul dictionnaire, plusieurs usages (même
  doctrine que formulations : deux usages, deux coupes seulement si
  nécessaire).

### P5 (amorce) et P3 (sources), en découlant

Amorce proposée, dans l'ordre du rendement mesuré : les **623 paires
auto-extraites** (source `formulations`, statut `propose`) + une liste
LLM des **abréviations MCO courantes** (viser les 828 du vivier en
priorité par fréquence — toujours relues, l'extraction LLM reste une
trace) + les **variantes savantes** manuelles (liste courte à
construire, rein/cœur/foie/poumon…). Couverture mesurable : % des 828
abréviations du vivier ayant une expansion `relu` ; les manques réels
viendront des journaux de `codeur` (recherches sans résultat). Les
terminologies ouvertes : à instruire séparément (licences), rien n'en
dépend pour la v1.

## 4. Points à trancher par RF

1. P1 : table curée CSV unique (A) vs YAML (B) ; formes pliées
   confirmées ?
2. P2 : multiplicité sans `contexte` en v1 (A) ?
3. P4 : candidats locaux de `codeur` — strict (a) ou optimiste
   borné (b) ?
4. Latéralité (MIG/MID…) : lignes explicites ou règle compositionnelle
   déclarée ?
5. L'amorce : seuil de fréquence pour la passe LLM (top 100 ? 300 ?),
   et qui relit (volumétrie de relecture : 623 + la passe LLM).

## 5. Esquisse de brief (après arbitrages)

Phase 1 : table curée + auto-extraction v1 (candidats `propose`) +
passe LLM d'amorce → **STOP relecture RF** (verdicts ligne à ligne sur
les `propose`) → export `equivalences.csv` au paquet + CONTRAT + guide.
Témoins : HTA bidirectionnel, FA `vers_equivalent` (jamais « fa »
intra-mot), IRC à deux équivalents, tumeur↔tumoral, « cardia » ABSENT
(contre-témoin stemming), seules les `relu` sortent. Phase 2 : format
d'import des candidats `codeur` + première boucle de remontée.
