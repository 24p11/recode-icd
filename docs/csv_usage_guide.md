# Guide d'usage du CSV `inclusions_exclusions_synonymes.csv`

> Document de référence pour tout consommateur du fichier maître produit
> par le pipeline recode-icd. Décrit le schéma, la sémantique des valeurs,
> et les points de vigilance pour l'exploitation (notamment
> l'enrichissement de prompts LLM).
>
> Ce document est autonome : il ne suppose aucune connaissance du pipeline
> de construction. Pour comprendre comment le CSV est construit, voir
> `docs/source_mapping.md` et le notebook `01_walkthrough_pipeline`.
>
> **Les statistiques chiffrées vivent dans `reports/csv_stats.md`**,
> régénéré à chaque build (elles évoluent quand les sources sont mises à
> jour). Ce guide ne contient que des ordres de grandeur indicatifs,
> datés de leur dernière révision manuelle.
>
> _Dernière révision manuelle : 2026-05-30 (refonte dague/astérisque)._

---

## 1. Vue d'ensemble

Le CSV regroupe, pour chaque code CIM-10, toutes les informations
textuelles associées : libellé systématique, inclusions, exclusions,
synonymes, et notes éditoriales. Ces informations proviennent de
plusieurs sources fusionnées (classification suisse OFS 2006,
classification française ANS à jour, et trois sources externes
d'enrichissement).

**Objectif métier** : enrichir des prompts destinés à faire générer ou
annoter des textes médicaux par un LLM, en lui fournissant le contexte
sémantique complet d'un code CIM-10.

**Volumétrie indicative** : ~215 000 lignes sur ~16 000 codes uniques
(moyenne ~13 lignes par code). Chiffres exacts dans `reports/csv_stats.md`.

**Granularité** : une ligne = une information textuelle (une inclusion,
une exclusion, un synonyme, ou une note) attachée à un code, avec sa
provenance.

---

## 2. Schéma : les 9 colonnes

| # | Colonne | Type | Description |
|---|---------|------|-------------|
| 1 | `code` | str | Code CIM-10 au format standard avec point (ex : `A18.1`) |
| 2 | `libelle` | str | Libellé systématique officiel du code (constant pour toutes les lignes d'un même code) |
| 3 | `type` | str | Nature de l'information : `inclusion`, `exclusion`, `synonyme` |
| 4 | `source` | str | Provenance de l'information (voir énumération §3) |
| 5 | `texte` | str | Le texte de l'information (le libellé de l'inclusion/exclusion/synonyme) |
| 6 | `source_level` | str | Niveau hiérarchique d'origine de la note : `chapter` / `block` / `category` / `code` (voir §6) |
| 7 | `inherited_from_code` | str? | Code parent dont la note est propagée (vide si attachée directement au code) |
| 8 | `is_dagger_in_pair` | bool | `True` si le code participe à au moins une association DAGSTAR comme code dague (voir §5) |
| 9 | `is_asterisk_in_pair` | bool | `True` si le code participe à au moins une association DAGSTAR comme code astérisque (voir §5) |

Note : `type` peut aussi contenir `note` pour les notes éditoriales selon
les versions ; la grande majorité des lignes sont inclusion / exclusion /
synonyme.

**Pour le détail des paires dague/astérisque** (quel code apparié, niveau
d'association, redundancy_level, etc.), consulter le livrable séparé
`dagger_asterisk.parquet`. Le CSV principal ne porte que les deux flags
booléens ci-dessus pour signaler la participation à des paires.

---

## 3. La colonne `source` : énumération et sémantique

Chaque ligne porte une source qui indique d'où vient l'information. Les
sources se répartissent en deux familles.

### Sources structurelles (le socle de la classification)

| `source` | Origine | Rôle |
|----------|---------|------|
| `CIM-10` | OFS suisse 2006 (relationnel) | Source autoritaire pour les inclusions/exclusions typées |
| `ANS` | ANS française à jour (RDF/OWL) | Source autoritaire pour les libellés et l'existence des codes ; couvre les codes post-2006 |
| `CIM-10 frères` | Synthétisé par le pipeline | Exclusions synthétisées pour les codes `.8` (listant les codes frères `.0`-`.7`) |

### Sources externes (enrichissement)

| `source` | Origine | Rôle |
|----------|---------|------|
| `CIM-10 index` | Index alphabétique CIM-10 volume 3 | Synonymes (libellés cliniques historiques, déclinaisons par organe) |
| `ORPHANET` | Nomenclature ORPHANET 2025 | Synonymes (maladies rares, relation E) + inclusions (sous-types, relation NTBT) |
| `AP-HP Dermatologie` | Thésaurus AP-HP | Synonymes spécialisés dermatologie |
| `AP-HP Endocrinologie` | Thésaurus AP-HP | Synonymes spécialisés endocrinologie |
| `AP-HP GRONES` | Thésaurus AP-HP (groupe DIM) | Synonymes |
| `AP-HP Troubles métaboliques` | Thésaurus AP-HP | Synonymes |
| `AP-HP Néphrologie` | Thésaurus AP-HP | Synonymes spécialisés néphrologie |
| `AP-HP Ophtalmologie` | Thésaurus AP-HP | Synonymes spécialisés ophtalmologie |
| `AP-HP Rhumatologie` | Thésaurus AP-HP | Synonymes spécialisés rhumatologie |
| `AP-HP Germes (SPILF)` | Société française de pathologie infectieuse | Synonymes (germes) |
| `AP-HP SRLF` | Société française de réanimation | Synonymes |

Astuce de filtrage : toutes les sources AP-HP commencent par `AP-HP`, donc
`source.startswith("AP-HP")` les capture toutes.

---

## 4. Statistiques

**Les statistiques à jour sont dans `reports/csv_stats.md`** (régénéré à
chaque build via `recode-icd build stats`). On y trouve : distribution par
source, par type, croisé source × type, distribution `source_level`, et
quantiles du nombre de notes par code.

Ordres de grandeur indicatifs (révision 2026-05-28, à titre de repère
seulement — voir le rapport pour les chiffres exacts) :

- Socle structurel (CIM-10 + ANS) : ~66 % des lignes
- Enrichissement externe (Index + ORPHANET + AP-HP) : ~32 %
- Frères synthétisés : ~2,5 %
- Par type : exclusion ~43 %, synonyme ~35 %, inclusion ~22 %
- Propagation : ~49 % des notes héritées d'un niveau supérieur
- Codes-fourre-tout : ~90 codes dépassent 100 notes, record ~2 500

Points structurels stables (peu susceptibles de changer) :

- Index CIM-10 et AP-HP sont 100 % synonymes
- ORPHANET est majoritairement inclusions (relations NTBT) + minoritairement synonymes (relations E)
- CIM-10 frères est 100 % exclusions
- CIM-10 et ANS portent l'essentiel des exclusions

---

## 5. Couples dague / astérisque (colonnes 8-9)

La CIM-10 permet de coder certains diagnostics avec deux codes : un code
**dague** (étiologie, maladie initiale) et un code **astérisque**
(manifestation localisée). Exemple : A18.1 (Tuberculose génito-urinaire)
+ N33.0 (Cystite tuberculeuse).

### Représentation dans le CSV : deux flags booléens

Le CSV principal ne porte pas l'information détaillée des paires
dague/astérisque sur ses lignes. Il expose seulement deux colonnes
booléennes au niveau du code :

- **`is_dagger_in_pair`** : `True` si le code participe à au moins une
  association DAGSTAR comme code dague (rôle d'étiologie).
- **`is_asterisk_in_pair`** : `True` si le code participe à au moins une
  association DAGSTAR comme code astérisque (rôle de manifestation).

Un même code peut avoir les deux flags à `True` simultanément si selon
les paires considérées, il joue les deux rôles.

Ces flags signalent au consommateur que le code participe à la
mécanique dague/astérisque, sans détailler les paires spécifiques.

### Pour obtenir le détail des paires : la table DAGSTAR enrichie

Pour connaître quelles paires précises impliquent un code, avec leur
niveau d'association (`subordinate` / `independent`) et la formulation
clinique de chaque combinaison, consulter le livrable séparé
`referentials/processed/dagger_asterisk.parquet`.

Cette table contient une ligne par paire unique (dague, astérisque) avec :
- Les codes et libellés des deux côtés
- Les niveaux d'association présents
- Le `redundancy_level` issu de la curation manuelle (`subordinate` pour
  les paires où le code dague se "résume" dans la combinaison, typique
  des maladies infectieuses)
- Les libellés cliniques observés pour la combinaison

### Pourquoi cette séparation ?

L'information de couplage dague/astérisque est par nature une **propriété
du scénario clinique** (à exploiter au moment du codage d'un texte
médical), pas une propriété intrinsèque d'un code isolé. La représenter
ligne par ligne dans le CSV créait une duplication massive (jusqu'à ×12
sur certains codes) sans apporter de valeur sémantique au-delà de ce que
les autres colonnes contiennent déjà.

Pour plus de détails sur cette décision, voir `docs/source_mapping.md`
section "Couples dague/astérisque : politique de représentation".

---

## 6. Propagation hiérarchique (colonnes 6-7)

Les notes (inclusions, exclusions, notes éditoriales) peuvent être
attachées à n'importe quel niveau de la hiérarchie CIM-10 (chapitre, bloc,
catégorie, code). Le pipeline les **propage** vers tous les codes feuilles
concernés, et trace cette propagation :

- **`source_level`** : niveau d'origine de la note (`chapter` / `block` / `category` / `code`)
- **`inherited_from_code`** : le code parent dont la note vient (vide si `source_level=code`)

Exemple : une exclusion attachée au bloc A00-A09 apparaît sur tous les
codes du bloc avec `source_level=block` et `inherited_from_code=A00-A09`.

**Conventions** :
- Les sources externes (ORPHANET, Index, AP-HP) ont toujours `source_level=code`, `inherited_from_code` vide
- Les synonymes OFS/ANS sont attachés au code feuille : `source_level=code`
- Seules les inclusions/exclusions/notes OFS et ANS peuvent être propagées

**Usage** : pour maximiser la spécificité, un consommateur peut filtrer
les notes propagées depuis un niveau trop haut (par exemple ignorer
`source_level=chapter` pour ne garder que les notes plus proches du code).

Note : près de la moitié des notes sont propagées (voir `reports/csv_stats.md`).
C'est conforme à la structure CIM-10 où les exclusions sont souvent
définies une fois au niveau du bloc.

---

## 7. Points de vigilance et limitations connues

### Les codes-fourre-tout (volumétrie extrême)

Une centaine de codes ont plus de 100 notes. Les plus extrêmes :
- A52.7 (syphilis tardive) : ~2 500 notes, dont l'essentiel de l'Index CIM-10
- Q87.8 (syndromes malformatifs précisés) : ~1 200 notes, dont l'essentiel d'ORPHANET
- A52.1, A18.1, A52.0, A18.0 : 600-1 200 notes

Ce sont des catégories `.7` / `.8` ("autres formes précisées") qui
absorbent énormément d'entités cliniques. C'est **légitime** (richesse
historique réelle) mais **problématique pour l'usage LLM** : injecter des
milliers de synonymes dans un prompt sature le contexte et dilue le signal.

**Recommandation** : pour ces codes, prévoir un échantillonnage ou un
plafonnement du nombre de notes injectées dans le prompt. Ne pas tout
injecter aveuglément.

### La déduplication tolérante n'attrape pas tout

La dédup utilise une normalisation tolérante (NFKD + minuscules +
ponctuation). Elle élimine les variantes typographiques (casse, accents,
ligatures) mais **pas** les reformulations sémantiques.

Conséquence : deux libellés qui décrivent la même chose mais formulés
différemment ("Choléra asiatique" vs "Choléra dû à V. cholerae") sont
conservés tous les deux. C'est généralement souhaitable (richesse
lexicale), mais ça explique pourquoi le taux d'absorption inter-sources
est faible (~2,5 %).

**Cas limite identifié** (A07.1, Giardiase) : certaines entrées Index avec
des parenthèses légèrement différentes ("Colite (aiguë)..." vs "Colite
(aiguë) (exsudative)...") passent la dédup et apparaissent comme
quasi-doublons. Non bloquant, mais à connaître si on observe des
redondances apparentes.

### Codes absents du CSV

Certains codes CIM-10 historiques (par exemple A90, A91 — Dengue ancienne
classification) ne sont PAS dans le CSV. Raison : ils ont été retirés de
la classification française ANS (refondus vers d'autres catégories par
l'ATIH). Le CSV reflète la classification française vivante, pas
l'historique. Ces codes orphelins sont tracés dans
`reports/external_orphan_codes.csv` avec la catégorie
`pre_2006_dropped_by_atih`.

### Atomicité OFS vs blocs ANS

Pour les codes pré-2006, les notes sont atomisées (une ligne par élément).
Pour les codes post-2006 (présents uniquement en ANS, ex : U07.1 COVID),
les notes multi-éléments peuvent rester sous forme de blocs textuels avec
puces. C'est une limitation acceptée (pas de parsing automatique des blocs
ANS).

---

## 8. Recommandations d'usage pour le prompt engineering

Quelques pistes pour exploiter le CSV dans des prompts LLM :

**Filtrer par type selon l'objectif** :
- Pour aider le LLM à reconnaître un code : injecter les `synonyme` et `inclusion`
- Pour aider le LLM à ne pas confondre des codes proches : injecter les `exclusion`
- Les exclusions sont la richesse sous-exploitée du dataset (~43 % des lignes)

**Gérer les codes-fourre-tout** : plafonner le nombre de notes injectées
pour les codes à forte volumétrie (>50 notes), par échantillonnage ou par
priorité de source.

**Choisir les sources selon le besoin** :
- Variété lexicale grand public : `CIM-10 index`
- Terminologie spécialisée : sources `AP-HP`
- Maladies rares : `ORPHANET`
- Socle officiel : `CIM-10` et `ANS`

**Exploiter la propagation** : pour un code donné, distinguer les notes
qui lui sont propres (`source_level=code`) des notes héritées
(`source_level` block/category/chapter). Les notes propres sont les plus
spécifiques.

**Gérer les couples dague/astérisque** : pour les paires `subordinate`,
consulter `dagger_asterisk.parquet` pour identifier les codes dagues qui
se résument dans la combinaison et envisager de les filtrer côté
consommateur.

---

## 9. Comment régénérer le CSV et les stats

```bash
uv run recode-icd build external               # charge sources externes + dédup
uv run recode-icd build flat-csv --external    # produit le CSV final
uv run recode-icd build stats                  # régénère reports/csv_stats.md
```

Pour inspecter un code spécifique (toutes sources + résultat final) :

```python
from recode_icd.utils.loaders_dev import inspect_code
inspect_code("A18.1")            # code exact
inspect_code("A18")              # préfixe (toute la catégorie)
inspect_code(["A18.1", "N33.0"]) # liste
```

## Résoudre un code vers sa fiche — ne jamais joindre à la main

*Chantier couverture ATIH, D0 (2026-09-05).*

Un code peut s'écrire de trois façons — compacte (kit ATIH, RUM :
`O0490`), pointée (`O04.90`), maître (`O04.-0.9`) — et trois familles
divergent de la règle « point après le 3e caractère » (O04, M62.8, neuf
catégories à `+`). Une jointure naïve sur `code` échoue en silence.
Passer par le résolveur :

```python
from recode_icd.couverture import charge_contexte, resoudre_code

ctx = charge_contexte()                 # atih_codes + merged_codes + _index.csv
r = resoudre_code("O0490", ctx)
r.statut        # "fiche"
r.code          # "O04.-0.9"  (écriture du maître)
r.fiche         # "XV/O04.-0.9.md"
r.codable_mco   # True
```

Réponses négatives, toujours motivées (`r.raison`) et avec un repli :

| `statut` | Repli fourni |
|---|---|
| `intermediaire` (codable, subdivisé, sans fiche propre) | `codes_avec_fiche` : ses feuilles |
| `pere_interdit` (type 3) | `codes_avec_fiche` : ses enfants |
| `tronc_chapitre_xx` (extension lieu/activité) | `ancetre` : le tronc, et sa fiche |
| `absent_du_maitre` (extension ATIH récente) | `ancetre` |
| `sans_ligne`, `supprime`, `inconnu_atih`, `inconnu`, `notation_invalide` | — |

Une fiche sur un code non codable (supprimé, inconnu du kit, père)
est rendue `fiche` avec `codable_mco=False` : filtrer dessus avant tout
tirage de génération. CLI équivalente : `recode-icd resoudre CODE…
[--json] [--journal fichier.jsonl]` — le journal n'enregistre que les
réponses négatives ; **envoyez-le**, il priorise les fiches à produire.

