# Besoins de `codeur` — analyse d'ouverture et options de conception (2026-10-18)

> Chantier de conception (prompt RF du 2026-10-18, archivé dans
> `docs/sessions/2026-10-18_prompt_chantier_codeur.md`). Objet :
> confronter les besoins de `codeur` (24p11/codeur, outil de codage
> assisté) à l'état de recode-icd, MESURER, proposer des options —
> **rien n'est mis en œuvre ni tranché ici**. Mesures reproductibles :
> `scripts/explore/mesure_besoins_codeur.py`.

## 1. Constat d'ouverture : deux prémisses du prompt à corriger

**a) La plupart des « troncatures » citées sont codables.** Contre le
kit ATIH 2025 (notre source d'autorisation gravée, « codable = type ≠ 3
et non supprimé ») :

| Code du prompt | Statut kit 2025 | Le code complet cité |
|---|---|---|
| `Z992` | **codable** (type 0) | `Z992+0` codable |
| `K861` | **codable** | `K861+8` codable |
| `J961` | **codable** | `J961+0` codable |
| `M142`, `M146` | **codables** | `M1427`, `M1467` codables |
| `E11` | père interdit (type 3) | — |
| `R521` | père interdit (type 3) | `R5210` codable |

4 des 6 exemples « mettraient le RUM en erreur » selon le prompt — le
kit dit le contraire. **49 codes codables ont des extensions « + »
elles-mêmes codables** (Z992, J961, C169, F03…). Conséquence de
conception majeure : la boucle de correction a DEUX régimes, à traiter
différemment —

- **correction obligatoire** : le code proposé est non codable (père
  interdit, supprimé, inconnu) → liste de remplacement ;
- **affinage optionnel** : le code proposé est codable mais moins
  précis qu'un descendant disponible → proposition d'affinage ; le
  code tronqué reste VALIDE au RUM. Imposer la profondeur maximale est
  une politique DIM possible, pas une contrainte du kit — à déclarer
  côté `codeur` si voulue.

Le résolveur (`recode-icd resoudre`) fait déjà exactement ce partage
(`fiche` / `pere_interdit` avec enfants / `intermediaire` avec
feuilles / `supprime` / `inconnu_atih`), toute écriture acceptée.

**b) L'extension « ni » n'existe pas au kit 2025.** `E11ni` : aucun
`code_atih` ne contient « ni » (0/42 897) ; 360 codes portent une
extension « + ». À vérifier côté `codeur` d'où vient cette forme
(ancien millésime ? convention FG ?) — telle quelle, elle ne se
résoudra jamais.

**c) Le canal.** Un `outputs/cards_library.zip` non suivi traîne dans
le clone : des fiches sont passées à `codeur` à la main, hors paquet
versionné — exactement ce que le besoin n° 1 veut abolir. Le CONTRAT
inscrit déjà le canal officiel ; `codeur` doit y entrer comme
consommateur déclaré.

## 2. État vs besoins (les 7 attentes du prompt)

| # | Besoin `codeur` | Existe | Manque |
|---|---|---|---|
| 1 | Index complet, tous codes, codable, forme sans point | `atih_codes.parquet` : 42 897 codes, `code_atih` (**la forme `codeur` exacte** : `Z992+0`), `codable_mco`, `interdit_dp/dr/das`, libellés, millésime — joint à 100 % des 15 282 fiches | pas dans la livraison ; pas de lien code → fichier de fiche ; pas de `format_version` |
| 2 | Fiches « utiles ou vides » | colonnes `has_*` de l'index | les sections notes (Définition/Description/Notes CIM-10) ne sont PAS tracées à l'index ; pas de critère déclaré |
| 3 | Fiches de navigation des nœuds non codables | `build_node_note_card` (blocs/chapitres, 43 fiches) ; le résolveur liste les descendants avec fiche | pas de fiche pour les 1 857 nœuds intermédiaires ; pas de « critère qui départage » |
| 4 | Catégories longues par axe | tables de composition (chap. XX) ; **modificateurs ClaML chargés** (les axes officiels : « le 5ᵉ caractère précise… ») | pas exploités pour la navigation |
| 5 | Explication des extensions PMSI | libellés ATIH par extension (`Z992+0` = HÉMODIALYSE) | pas de préambule ; pas de sémantique transversale des « + » (elle n'existe pas — le sens est par code) |
| 6 | Budget de taille par fiche | `nb_chars` à l'index | pas de plafond ; pas de profil « revue » compact |
| 7 | Export des formulations | tout est dans le CSV maître (12 col.) + pipeline de rendu (R1/R3/registre archaïque) | pas d'export dédié dans la livraison |

## 3. Mesures (2026-10-18, kit ATIH 2025, bibliothèque post-notes)

- **Listes de correction** (descendants codables par nœud non
  codable) : 1 857 nœuds cibles ; **médiane 6, p90 10, p99 77,
  max 126** (F01/F02 — démences ×5ᵉ caractère ; puis chapitre M :
  M62 118, M25/M79 108…). Dans 90 % des cas une liste plate de ≤ 10
  suffit.
- **Codables par catégorie 3 car.** : 1 844 catégories, médiane 6,
  **77 catégories > 20 codables, 44 > 50**. Les longues sont
  concentrées sur F0x (démences) et le chapitre M (localisations) —
  précisément là où les **modificateurs ClaML** portent l'axe officiel.
- **Fiches « vides »** : 33/15 282 ont tous les `has_*` à faux ; après
  croisement avec les notes rendues, **3 vraiment vides** (`C25.9+0`,
  `C25.9+8`, `X59`). Le problème est marginal — mais l'index ne permet
  pas de le voir seul (sections notes non tracées).
- **Taille des fiches** : médiane 1 863 chars ≈ **580 tokens** ; p90
  ≈ 1 170 ; p99 ≈ 2 370 ; max 3 090 (V93.8). **15 fiches ≈ 8 700
  tokens à la médiane, 17 600 au p90** — le cas d'usage « revue d'un
  dossier » tient déjà dans un appel.
- **Formulations** : 172 049 lignes (CepiDc 128 492, Index 39 262,
  AP-HP ~4 300) couvrant **9 266 codes** (61 % des fiches).

## 4. Options de conception (compromis, sans trancher)

### P1 — L'index complet : un livrable `codes.csv` distinct

**Option A (recommandée)** : nouveau livrable dans le paquet —
`codes.csv`, une ligne par code du kit (42 897) : `code_atih` (forme
`codeur`), `code` (pointée), `libelle`, `codable_mco`, `statut_mco`,
`interdit_dp/dr/das`, `fichier` (chemin de la fiche si elle existe,
sinon vide), `millesime_kit`, `format_version`. L'index des FICHES
(`index.csv`) reste ce qu'il est — le contrat n'est pas rompu, les
deux objets ont des sémantiques différentes (codes du référentiel vs
fiches construites). **Option B** : élargir `index.csv` à tous les
codes — rompt la sémantique « l'index énumère les fiches », bump de
`format_version`, migration fictomed/Stream. Coût > bénéfice.

### P2 — Fiches utiles ou vides : marquer, ne pas supprimer

Critère proposé, déclaré au contrat : *informative = au moins une
section au-delà du titre, de la position et du statut*. Implémentation
légère : colonnes `has_definition`/`has_description`/`has_notes_cim`
ajoutées à l'index (manque constaté) + colonne dérivée
`fiche_informative`. Avec 3 fiches réellement vides, supprimer des
fichiers ne rapporte rien et compliquerait le contrat (« l'index fait
foi » resterait vrai, mais un code codable sans fichier serait un
nouveau cas pour tous les consommateurs). **À trancher : marquage
seul (recommandé) vs fiche absente.**

### P3 — Fiches de navigation : généraliser les fiches de nœud

`build_node_note_card` existe (blocs/chapitres). Généralisation aux
1 857 nœuds intermédiaires non codables + les 49 pères codables à
extensions : titre, statut (« père interdit — non codable »), **liste
compacte des codables descendants** (`code_atih` + libellé court
ATIH), et **le critère qui départage**, par ordre de disponibilité :

1. le **texte du modificateur ClaML** quand le nœud en relève (« Les
   subdivisions suivantes… cinquième caractère… ») — officiel, déjà
   chargé (`loaders/claml_notes`), couvre F0x, E1x, M (localisations),
   S/T ;
2. à défaut, un axe **dérivé des libellés** (préfixe commun retiré,
   suffixe discriminant exposé : `Z992+0` HÉMODIALYSE / `+1` DIALYSE
   PÉRITONÉALE…) — c'est mécanique et auditable ;
3. à défaut, liste plate (90 % des nœuds font ≤ 10 lignes).

Relecture RF sur un échantillon dirigé (les 44 catégories > 50 + un
tirage). Destination : la bibliothèque des catégories (elles y sont
chez elles) + exposées dans `codes.csv` (`fichier` du nœud).

### P4 — Catégories longues : l'axe plutôt que la page

Pour les 44 catégories > 50 : regrouper la liste par l'axe du
modificateur (4ᵉ puis 5ᵉ caractère — « type de démence » × « avec/sans
symptômes », « localisation ») plutôt qu'une liste plate de 126.
**Compromis** : si l'axe officiel manque, un regroupement dérivé des
libellés peut être faux — le marquer comme dérivé, relecture RF.
Alternative minimale : liste plate plafonnée + renvoi au résolveur
(simple, mais reporte le problème sur `codeur`).

### P5 — Extensions PMSI : un préambule généré + le sens par code

Il n'existe PAS de sémantique transversale des « + » (le sens est
porté par le libellé de chaque extension). Proposition : un
`PREAMBULE_EXTENSIONS.md` généré du kit (ce qu'est une extension, la
forme `codeur`, « ni » n'existe pas au kit 2025, les 360 codes
concernés) + dans chaque fiche de navigation, le tableau des
extensions avec leurs libellés — c'est là que le LLM apprend quelle
information chercher.

### P6 — Budget de taille : mesurer d'abord, profiler ensuite

Les mesures disent que la revue (≤ 15 fiches) tient déjà (~9-18 k
tokens). Options si RF veut un plafond : (a) rien (chiffres à
l'appui) ; (b) plafond déclaré au contrat (`nb_chars` max, les
dépassements au rapport) ; (c) **profil « revue »** (backlog
`profils_fiches_par_usage.md` : titre + périmètre + à-ne-pas-décrire +
consignes, sans formulations) — c'est le levier le plus fort, mais
c'est un profil de plus à maintenir.

### P7 — Export des formulations : `formulations.csv` au paquet

Trivial et sans risque : `code_atih`, `formulation` (forme RENDUE,
post R1/R3/registre archaïque — le lexique vivant), `source`. Question
à trancher : **avant ou après le plafond R2** — pour la recherche par
mots-clés, AVANT (tout le vivier, 172 k lignes) est plus utile ; les
fiches restent plafonnées.

### Transversal

`codeur` entre au CONTRAT.md comme consommateur ; l'archive de
livraison embarque `codes.csv`, `formulations.csv`, le préambule et
les fiches de navigation **de la même livraison** (même commit, même
millésime — déjà garanti par le nommage).

## 5. Points à trancher par RF

1. La **contradiction Z992** : affinage optionnel vs correction
   obligatoire — et si `codeur` veut imposer la profondeur maximale,
   c'est une politique à déclarer (où : `codeur` ou recode-icd ?).
2. P2 : marquage `fiche_informative` seul, ou fiche absente ?
3. P3 : périmètre des fiches de navigation (1 857 nœuds + 49 pères
   codables ?) et circuit de relecture de l'axe discriminant.
4. P7 : formulations avant ou après plafond R2.
5. P6 : rien / plafond / profil revue.
6. L'énigme « ni » : à instruire côté `codeur`.

## 6. Esquisse de brief (après arbitrages)

Phase 1 (livrables plats, sans relecture) : `codes.csv` +
`formulations.csv` + préambule extensions + colonnes `has_*` notes à
l'index + `codeur` au CONTRAT. Phase 2 (relecture RF structurelle) :
fiches de navigation avec critère discriminant (échantillon dirigé →
verdicts → généralisation), axes des 44 catégories longues. Phase 3 :
profil « revue » si tranché. Tests témoins : Z992 (père codable),
R521 (père interdit), F01 (axe modificateur), une catégorie à axe
dérivé, budget 15 fiches.
