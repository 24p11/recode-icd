# recode-icd

> Toolkit Python pour exploiter les référentiels électroniques de la CIM-10
> (formats OFS suisse et OWL/ANS) en vue d'enrichir des prompts destinés à
> la génération de textes médicaux annotés par LLM.

## Consignes de session Claude Code

À chaque session non triviale :
1. Lire les documents de référence pertinents avant d'agir
   (docs/source_mapping.md, docs/sources/, etc.)
2. Pour les changements de design : proposer un plan détaillé et
   attendre validation avant d'implémenter.
3. Lors d'un signalement d'erreur par l'utilisateur, ne pas proposer
   de correction avant d'avoir : (a) reformulé l'observation, (b)
   localisé le code concerné, (c) tracé l'origine des données
   observées, (d) formulé des hypothèses de cause avec moyens de
   vérification. La correction vient seulement après validation
   explicite de la cause.
4. Avant de conclure une session : produire un récap des diffs
   significatifs (file by file, avec explication).
5. À la fin d'une grosse session : produire un récap dans
   docs/sessions/YYYY-MM-DD_<sujet>.md.
6. **N'annoncer un comportement comme acquis que s'il est testé sur un
   cas qui l'exerce.** Leçon du chantier guide-mco : « le script
   reproduit la version relue » a été annoncé sur la foi d'un article
   sans puce, alors que le correctif portait sur les puces. Un test qui
   passe sur un cas qu'il ne touche pas ne prouve rien.
7. **En cas de blocage : déclarer, puis constater — ne pas itérer sur
   des diffs.** Enchaîner des correctifs cosmétiques jusqu'à ce qu'un
   diff se vide coûte cher et converge mal. Poser d'abord toutes les
   déclarations nécessaires, produire, puis regarder le résultat une
   fois.
8. **Un clone (ou worktree) par session — jamais deux sessions dans le
   même arbre de travail.** Règle actée le 2026-09-03 après incident :
   un `git commit -a` d'une session a embarqué le travail non committé
   d'une autre, sur la mauvaise branche. Le clone principal
   (`recode-icd`) appartient au chantier fiches ; tout chantier
   parallèle travaille dans son worktree (`git worktree add`, ex.
   `../recode-icd-serie1` pour le chantier B guide MCO). Corollaires :
   committer par chemins explicites plutôt que `-a`, vérifier la
   branche courante avant tout commit, et un conflit sur un parquet de
   recommandations se résout par rebuild (`build guide-mco` puis
   rebuild des fiches), jamais à la main.

## Objectifs métier

1. **Fichier maître `inclusions_exclusions_synonymes.csv`** (9 colonnes) :
    `code`, `libelle`, `type` ∈ {inclusion, exclusion, synonyme, note},
    `source`, `texte`, `source_level`, `inherited_from_code`,
    `is_dagger_in_pair`, `is_asterisk_in_pair`.
    Regroupe toutes les informations textuelles associées à un code
    CIM-10, avec propagation des notes des niveaux supérieurs (chapitre,
    bloc, catégorie) vers les codes feuilles. La propagation est rendue
    visible via les colonnes `source_level` et `inherited_from_code` pour
    permettre le filtrage et la lecture humaine. Les deux flags booléens
    `is_dagger_in_pair` / `is_asterisk_in_pair` signalent la
    participation à des paires dague/astérisque ; le détail des paires
    vit dans le livrable séparé (cf objectif 2).
2. **Table des associations dague (†) / astérisque (*)** comme livrable
   séparé (`dagger_asterisk.parquet`). Source unique pour l'information
   détaillée des paires (codes appariés, niveaux d'association, redundancy_level,
   formulations cliniques). Préserve les 6 valeurs du champ `daget`
   F/G/H/S/T/U. Le CSV principal ne porte que les deux flags
   `is_dagger_in_pair` / `is_asterisk_in_pair` qui renvoient vers cette
   table pour le détail.
3. **API stable** pour enrichir des prompts CIM-10 (réutilisable par
   recode-scenario notamment).

## Stack technique

- Python ≥ 3.13 (aligné sur `smt2parquet`)
- Gestion des paquets : **uv**
- DataFrames : **polars**
- Stockage intermédiaire : **Parquet** (via pyarrow)
- Modèles de données : **pydantic v2**
- Validation : **pandera**
- Tests : **pytest** avec marqueurs `unit`, `regression`, `integration`
- Lint/format : **ruff**
- Type-check : **mypy**
- CLI : **typer**

## Commandes courantes

```bash
uv sync                                  # installer
uv run pytest                            # tous les tests
uv run pytest -m unit                    # unitaires seuls
uv run pytest -m regression              # régression seule
uv run recode-icd build atih             # kit ATIH → atih_codes.parquet
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/recode_icd
uv run pre-commit install                # hooks git
```

## Structure du projet

```
src/recode_icd/

├── loaders/
│   ├── ofs.py             # base relationnelle OFS suisse (2006)
│   ├── owl.py             # surcharge locale de smt2parquet (CIM-10 ANS)
│   ├── atih.py            # kit de nomenclature ATIH (statut MCO, règles positionnelles)
│   └── external/          # sources tierces de synonymes/inclusions
│       ├── __init__.py
│       ├── index_cim10.py # feuille "Cim Alphabétique" du HECTOR (Index vol3 officiel)
│       ├── aphp_hector.py # 9 feuilles AP-HP métier (loader unifié paramétré)
│       └── orphanet.py    # XML ORPHANET (relations E + NTBT)
├── notations.py           # table de notation unique (compacte ↔ pointée ↔ maître)
├── couverture.py          # résolveur des consommateurs : toute écriture → fiche ou raison (D0)
├── model.py               # entités pydantic canoniques
├── merge.py               # fusion OFS ⊕ OWL avec politique de résolution
├── propagation.py         # propagation bloc/catégorie → code (nested set)
├── relations/
│   ├── dagger_asterisk.py # table d'associations dague/astérisque (objectif 2)
│   └── sibling_exclusions.py
├── exporters/
│   └── flat_csv.py        # le fichier 9 colonnes
├── registry.py            # ReferentialRegistry (inspiré de recode-scenario)
└── cli/                   # CLI typer
referentials/
├── raw/                   # fichiers sources (gitignored si volumineux)
├── processed/             # Parquets dérivés (committés)
└── curation/              # curation manuelle : dagger_curation.csv, chapter_policy.yaml,
                           # notations_codes.yaml (table de notation unique)
tests/
├── unit/
├── regression/            # golden-files sur 10 codes témoins
├── integration/
└── fixtures/
scripts/
├── prepare_referentials.py
└── explore/               # notebooks d'exploration ad-hoc
docs/
├── owl_extension.md       # quelles propriétés on ajoute à smt2parquet
├── source_mapping.md      # mapping canonique OFS ↔ OWL/ANS (RÉFÉRENCE ABSOLUE)
├── sources/
│   └── ofs_schema.md      # schéma détaillé de la base OFS
└── architecture.md
data/
├── CIM_APHP_2019/                              # Excel HECTOR (Index CIM-10 + thésaurus AP-HP)
│   └── Dictionnaire_Hector_MAJ062019.xlsx
├── Orphanet_Nomenclature_Pack_FR_2025/         # ORPHANET 2025
│   ├── ORPHA_ICD10_mapping_fr_2025.xml
│   └── ORPHA_ICD10_mapping_en_2020.xsd
├── CIM_ATIH_2025/                              # kit de nomenclature ATIH (cim.pdf = format)
│   └── LIBCIM10MULTI.TXT                       # 42 897 codes, Type MCO/HAD 0-4
└── guide_mco/                                  # guide méthodologique MCO
    ├── guide_methodo_mco_2026_version_provisoire.pdf
    ├── extraits_bruts/                         # pdftotext -layout intact
    ├── extraits/                               # transcriptions curées + suppressions.yaml
    ├── extraction/                             # candidates (trace de curation)
    ├── hors_perimetre.md                       # couches 1 et 2, divergences guide/CIM
    └── *_curated.csv                           # SOURCE DE VÉRITÉ du build
```


## Dépendances externes clés

- **Documents de référence obligatoires.** Avant toute modification du
  code de fusion, des loaders ou de l'exporter, Claude Code DOIT lire :
  - `docs/source_mapping.md` : mapping canonique OFS ↔ OWL/ANS.
    Toute décision sur la sémantique d'un champ se prend selon ce document.
  - `docs/sources/ofs_schema.md` : schéma détaillé de la base OFS.

  Si une situation rencontrée n'est pas couverte par ces documents,
  demander à l'utilisateur avant d'inventer un comportement.

- **`smt2parquet`** (https://github.com/dridk/smt2parquet) — utilisé en
  module pour convertir RDF→Parquet via le modèle *nested set*. **Surcharge
  par wrapper local** dans `loaders/owl.py` : on importe
  `smt2parquet.core` (`load_graph`, `dataframe_from_sparql`,
  `build_nested_set`, `write_parquet_with_metadata`) tel quel et on redéfinit
  les requêtes SPARQL `ATTRS_QUERY` / `EDGES_QUERY` localement pour récupérer
  les propriétés non extraites en amont par `smt2parquet/cim10.py` :
  `xkos:exclusionNote`, `skos:definition`, `skos:scopeNote`, `skos:note`,
  `atih-cim10:hasCausality`, `atih-cim10:hasManifestation`,
  `atih-cim10:exclusion`. Détails et requêtes dans `docs/owl_extension.md`.

  **Attention** : `smt2parquet/cim10.py` déduplique les synonymes via
  `.unique()` polars (égalité stricte de chaîne), ce qui laisse passer
  des doublons "presque identiques" (casse, ponctuation, ligature æ).
  La déduplication tolérante finale est de la responsabilité de
  `merge.py` / `flat_csv.py`. Détails dans `docs/source_mapping.md`
  section "Déduplication des synonymes".

- Référence d'inspiration architecturale : **`Stef500/recode-scenario`**
  pour le pattern `ReferentialRegistry` (accès paresseux, validé Pandera,
  caché aux Parquets et YAML).

## Modèle de données canonique

Tout passe par 4 entités pydantic :

- **`Code`** : code CIM-10 avec hiérarchie (chapitre / bloc / catégorie /
  sous-catégorie), bornes `left`/`right` nested set, et le `path`.
- **`Note`** : avec `type: NoteType` ∈ {INCLUSION, EXCLUSION,
  INDIRECT_EXCLUSION, COMMENT, CODING_HINT}, `source: NoteSource` ∈
  {OFS, OWL_ANS, SYNTHESIZED_SIBLING, ...}, et `inherited_from: Code |
  None` (renseigné si la note vient d'un bloc ou d'une catégorie parente
  par propagation).
- **`Synonym`** : libellé alternatif avec `source: SynonymSource`
  ∈ {OWL_ANS, INDEX_CIM10_VOL3, ORPHANET, AP_HP, ...}.
- **`DaggerAsteriskPair`** : couple `(dagger_code, asterisk_code)` avec
  son contexte d'association (`daget` ∈ {F, G, H, S, T, U} et flag
  `plus`).

Toute donnée exportée porte une colonne `source` — **jamais d'agrégation
silencieuse**.

### Cas particulier des notes synthétisées (`SYNTHESIZED_SIBLING`)

Pour les notes générées automatiquement (exclusions des codes frères
.8) :
- `source = SYNTHESIZED_SIBLING` (libellé CSV : `CIM-10 frères`)
- `inherited_from = None` (la note est conceptuellement attachée
  directement au code .8, pas héritée d'un parent)
- Une colonne dédiée dans l'export final indique le code frère cible

C'est différent de la propagation hiérarchique : la note synthétisée
naît au niveau du code .8 lui-même, ce n'est pas un héritage d'un
bloc ou d'une catégorie.

## Domain pitfalls — à NE PAS confondre

1. **Inclusion ≠ synonyme**. Une inclusion est une affection *rangée dans*
   la catégorie ; un synonyme est un autre nom *pour la même* affection.
   OFS distingue les deux ; OWL/ANS souvent pas (les deux se retrouvent
   dans `xkos:inclusionNote` indifféremment). C'est précisément ce que
   notre fusion doit reconstruire en s'appuyant sur OFS.
2. **Note d'exclusion ≠ négation**. Une exclusion dit "cette affection
   appartient à un AUTRE code, voir XX.Y", pas "cette affection n'existe
   pas". Toujours conserver le code de redirection si présent.
3. **Propagation bloc → code obligatoire**. Les notes au niveau bloc
   s'appliquent à TOUS les codes du bloc, sauf override explicite plus bas.
   Cette propagation est tracée dans le CSV final via 
   deux colonnes :
   - `source_level` ∈ {chapter, block, category, code} : indique le niveau 
   d'origine de la note
   - `inherited_from_code` : le code parent (chapter, bloc, catégorie) si 
   la note est propagée, vide si attachée directement au code feuille
 
   Les sources externes (ORPHANET, Index CIM-10 vol3, AP-HP) ne propagent 
   pas : leurs entrées ont toujours `source_level=code` et 
   `inherited_from_code` vide. Idem pour les descripteurs/synonymes OFS et 
   ANS qui sont attachés directement au code feuille.
 
4. **Dague (†) / astérisque (*)**. Le code dague est primaire (maladie
   initiale, étiologie), l'astérisque est la manifestation. Ne **JAMAIS**
   inverser. Voir section "Couples dague/astérisque" pour la politique
   de représentation dans le CSV.
5. **CIM-10 OMS vs CIM-10 FR-PMSI**. La FR-PMSI a des extensions ATIH
   absentes de l'OMS. La version cible doit être explicite dans les
   métadonnées Parquet et dans les exports CSV.
6. **Codes .8 vs .9** : `.8` = "autres" (information ajoutée), `.9` =
   "sans précision" (équivalent au titre de catégorie, pas d'information
   ajoutée). Pour C00-C75, `.8` a une sémantique spécifique (lésion à
   localisations contiguës).
7. **Priorité des chapitres "groupes spéciaux"**. Chapitres I, II, XV–XXI
   ont la priorité sur les chapitres "par appareil" en cas de doute de
   classement. Ne jamais "régulariser" en mettant un code par appareil
   alors qu'un groupe spécial s'applique.
8. **Atomicité OFS vs blocs ANS** (limitation connue). L'ANS livre les
   notes multi-éléments comme un seul bloc textuel avec puces, là où
   OFS atomise. Pour les codes pré-2006, OFS prime et fournit
   l'atomisation. Pour les codes post-2006, on accepte les blocs ANS
   tels quels — pas de parsing automatique. Détails dans
   `docs/source_mapping.md` section "Limitation connue : atomisation
   ANS".
9. **Conventions ANS non standard et normalisation au loader**. ANS
   utilise nativement des crochets `[D22.-]` pour les codes redirigés
   alors que la convention CIM-10 OMS standard utilise des parenthèses
   `(D22.-)`. **Ces codes de redirection ne sont pas un choix
   typographique arbitraire** : ils correspondent sémantiquement aux
   associations dague/astérisque. **Politique recode-icd** : le loader
   OWL/ANS normalise ces crochets en parenthèses au chargement pour
   s'aligner sur la convention OMS standard. Le CSV et la table DAGSTAR
   enrichie contiennent donc les codes de redirection entre parenthèses,
   pas entre crochets. Le texte ANS brut (crochets) reste préservé dans
   le RDF source pour audit. ANS utilise aussi `nævus` avec ligature æ ;
   cet artefact reste dans le CSV (non normalisé). Détails dans
   `docs/source_mapping.md` section "Conventions d'export ANS".
10. **Déduplication stricte vs tolérante**. Le `.unique()` de polars
    (utilisé en amont par smt2parquet) ne suffit pas pour les
    synonymes : il laisse passer les variantes de casse, ponctuation,
    ligature. La déduplication finale doit utiliser la normalisation
    tolérante (NFKD + lowercase + ponctuation + whitespace).

## Politique de fusion OFS ⊕ OWL

Politique par champ, à respecter :

| Champ                    | Source primaire    | Fallback   |
|--------------------------|--------------------|------------|
| `libelle` du code        | OWL_ANS            | OFS        |
| Existence du code        | OWL_ANS            | —          |
| Inclusions typées        | OFS                | OWL_ANS    |
| Exclusions typées        | OFS                | OWL_ANS    |
| Notes éditoriales        | OFS                | OWL_ANS    |
| Associations †/*         | OFS + audit ANS    | OWL_ANS    |
| Synonymes                | OFS                | OWL_ANS    |

Tout désaccord OFS ↔ OWL sur le libellé doit être loggué dans
`reports/merge_conflicts.csv` à chaque build.

Pour les associations †/*, OFS (`DAGSTAR.txt`, 1352 entrées) est la
source primaire pour le CSV de sortie. OWL/ANS
(`atih-cim10:hasCausality` + `atih-cim10:hasManifestation`, 1317
relations dans `terminologie-cim-10-2025-01-01.rdf`) est chargé en
parallèle pour permettre un **audit de cohérence**. Tout désaccord
est loggué dans `reports/dagger_asterisk_conflicts.csv`.

Pour les notes typées, le merger doit produire un champ `match_type`
dans `note_merges.csv` qui distingue : `exact_match`,
`atomic_regroupement`, `real_divergence`, `ofs_only`, `ans_only`.
Détails dans `docs/source_mapping.md` section "Règle de réconciliation".

## Couples dague/astérisque

Politique synthétique (détails dans `docs/source_mapping.md` section
"Couples dague/astérisque : politique de représentation") :

- **Le CSV principal ne porte pas l'information détaillée des paires.**
  Il expose seulement deux flags booléens au niveau du code :
  `is_dagger_in_pair` (True si le code apparaît dans DAGSTAR avec
  daget ∈ {S, T, U}) et `is_asterisk_in_pair` (True si daget ∈ {F, G, H}).
- **Pas d'expansion par paire** : chaque note d'un code apparaît une
  seule fois dans le CSV, indépendamment du nombre de paires
  dague/astérisque auxquelles ce code participe.
- **Le détail des paires** (code apparié, niveau, descripteur clinique,
  redundancy_level) vit exclusivement dans `dagger_asterisk.parquet`,
  livrable séparé conçu pour les consommateurs en aval (notamment
  `recode-scenario` pour l'analyse de scénarios cliniques).
- **La curation manuelle** (`dagger_curation.csv`) reste utilisée pour
  attribuer `redundancy_level=subordinate` aux paires dans la table
  DAGSTAR enrichie. Cette information n'est plus propagée dans le CSV
  principal.

**Filtrage des synonymes redondants** : la règle de filtrage des
descripteurs côté dague (15,8% de doublons exacts mesurés
empiriquement sur DESCR) reste appliquée par le merger,
indépendamment de la politique d'expansion.

## Notes synthétisées (codes "autres" en .8)

En plus des notes extraites des sources, on **synthétise** des notes
d'exclusion pour les codes en `.8` ("Autres ...") :

- **Règle** : pour tout code `XYZ.8`, on ajoute une note d'exclusion qui
  liste les codes frères `XYZ.0`, `XYZ.1`, ..., `XYZ.7` (les codes de la
  même catégorie à 3 caractères qui ne sont ni `.8` ni `.9`), avec leurs
  libellés.
- **Pourquoi** : aider le LLM à comprendre que `XYZ.8` couvre les affections
  *résiduelles* — celles qui n'ont pas leur propre sous-catégorie spécifique.
  Sans cette information, le LLM risque de générer un compte-rendu décrivant
  une affection qui aurait dû être codée sous `XYZ.0` ou autre, ce qui
  corrompt le dataset annoté.
- **NoteSource** : `SYNTHESIZED_SIBLING` (jamais confondre avec une note
  réelle). **Libellé dans le CSV exporté** : `CIM-10 frères` (mapping
  Python ↔ CSV géré par `exporters/flat_csv.py`).
- **NoteType** : `EXCLUSION`.
- **`inherited_from`** : `None` (la note est attachée directement au
  code .8, pas héritée).
- **Granularité d'export** : **une ligne CSV par code frère**, pas une
  ligne agrégée. Le code frère et son libellé apparaissent dans la
  colonne `texte` au format `<libellé du frère> (<code du frère>)`.
  Symétrique avec l'export des exclusions OFS.
- **Exclusion explicite** : les codes `.9` ne sont JAMAIS inclus comme
  frères. Par définition `.9` n'apporte pas d'information ajoutée
  (équivalent au titre catégorie), donc l'exclure n'a pas de sens.
  Règle : siblings = codes du même parent catégorie, sauf `.8` ET `.9`.

Cas limites à gérer explicitement dans `relations/sibling_exclusions.py` :

1. Catégorie qui n'a que `.8` et `.9` (rien à exclure → pas de note
   synthétisée).
2. Catégorie où `.8` est absent (rien à faire).
3. Catégories à structure non-standard (par exemple les chapitres XIX/XX
   avec leurs caractères additionnels). On se restreint pour l'instant aux
   catégories à structure `.0-.9`.
4. **Cas particulier des C00-C75** : la sous-catégorie `.8` a une sémantique
   différente ("lésion à localisations contiguës"). Pour ces codes, **ne
   pas synthétiser** d'exclusion frère — on log un skip dans le rapport.

   ## Sources externes (ORPHANET, Index CIM-10 vol3, AP-HP, CepiDc)
 
En complément d'OFS et OWL/ANS, le projet intègre quatre familles de
sources externes pour enrichir les synonymes et inclusions :
 
1. **ORPHANET** (`data/Orphanet_Nomenclature_Pack_FR_2025/`) — XML
   officiel des maladies rares avec mapping vers CIM-10. Mise à jour
   2025. Politique d'intégration différenciée selon la relation :
   - Relation `E` (Exact) → `type=synonyme`
   - Relation `NTBT` (Narrower Term, Broader Term) → `type=inclusion`
     (l'ORPHA décrit une affection plus spécifique rangée sous le code CIM-10)
   - Relations `BTNT`, `ND` → **ignorées** (l'ORPHA est plus large
     que le code CIM-10, ou la relation n'est pas définie)
2. **Index CIM-10 vol3** (feuille "Cim Alphabétique" du fichier HECTOR) —
   index alphabétique officiel volume 3 de la CIM-10. Quasi figé
   depuis 1996. Tous les libellés sont importés comme `type=synonyme`
   par défaut.
3. **Thésaurus métiers AP-HP** (9 feuilles distinctes du fichier
   HECTOR) — dictionnaires construits par sociétés savantes (SRLF,
   SPILF) ou groupes d'experts AP-HP (DIM NESTOR, services métiers).
   Tous importés comme `type=synonyme` par défaut.
4. **CepiDc 2015** (`data/CIM_CEPIDC_2015/CepiDc_Dictionnaire2015.csv`) —
   dictionnaire de formulations cliniques *vie réelle* rédigées par
   des médecins sur les certificats de décès. Source maintenue par le
   CepiDc (Centre d'épidémiologie sur les causes médicales de décès).
   Style très télégraphique (médiane 26 chars, 3 mots), 147 340
   formulations sur 6 291 codes uniques. Tous les libellés importés
   comme `type=synonyme`. **Placé en dernier** dans `_EXTERNAL_ORDER`
   pour que la dédup tolérante préserve les libellés plus riches
   d'ORPHANET / AP-HP / Index quand il y a chevauchement. Génère un
   rapport spécifique `reports/cepidc_ignored.csv` avec format
   `(code_cepidc, n_formulations_perdues, exemples_formulations)`
   listant les codes CepiDc absents du référentiel `merged_codes`.
   Libellé CSV : **`CepiDc 2015`** (avec espace ; le millésime est
   conservé, c'est un instantané daté).
   Chargement via l'option CLI dédiée :

   ```bash
   uv run recode-icd build external \
     --cepidc-csv data/CIM_CEPIDC_2015/CepiDc_Dictionnaire2015.csv
   ```

   L'option a ce chemin pour **défaut** : `build external` sans
   argument charge donc CepiDc si le fichier est présent. Si le
   fichier est introuvable, un avertissement est émis sur stderr et le
   build se poursuit **sans** CepiDc (et sans écrire
   `cepidc_ignored.csv`) — asymétrie assumée avec `--orphanet-xml` et
   `--hector-xlsx`, qui eux échouent.

   Apport net : **121 127 lignes** ajoutées au CSV (146 948 chargées,
   1 658 absorbées par la dédup tolérante, 6 928 orphelines, 17 235 sur
   des codes non terminaux). L'apport est **quasi disjoint** des
   sources Index / AP-HP : 99,5 % des formulations CepiDc n'y ont
   aucun équivalent (99,2 % vs toutes les sources externes, 98,9 % en
   incluant OFS/ANS).
**Cas particulier piège ORPHANET** : le XML ORPHANET contient deux
propriétés au nom similaire mais à la sémantique différente :
- `DisorderMappingRelation/Name` : porte le sigle E/NTBT/BTNT/ND
  (relation sémantique entre ORPHA et CIM-10)
- `DisorderMappingICDRelation/Name` : porte "Code attribué / Code
  spécifique / Terme d'inclusion / Terme index" (axe orthogonal)
**Le loader ORPHANET doit lire `DisorderMappingRelation/Name`** pour
identifier les relations. C'est cette propriété qui distingue E de
NTBT, pas l'autre. (Le code legacy `prep_data_icd_models.ipynb`
lisait la mauvaise propriété — à corriger).
 
### Politique de fusion avec OFS/ANS
 
**Principe** : OFS reste la source autoritaire. Les sources externes
**enrichissent** uniquement les codes qui n'ont pas déjà l'information.
 
**Règle de dédup** : pour chaque entrée externe `(code, libellé)`, on
applique la normalisation tolérante (NFKD + lowercase + ponctuation)
et on vérifie si le libellé normalisé existe déjà dans OFS ou ANS
pour ce code :
 
- **Match trouvé** : l'entrée externe est **absorbée**, elle ne crée
  pas de ligne dans le CSV final. La trace de cette absorption est
  loggée dans `reports/external_overlaps.csv` (voir Reporting).
- **Pas de match** : l'entrée externe est ajoutée au CSV avec son
  `source` propre.
Cette politique garantit qu'aucune information de la classification
officielle n'est noyée dans des duplications partielles, tout en
préservant la traçabilité via le rapport.
 
### Codes orphelins externes
 
Certains codes apparaissent dans les sources externes mais sont
absents d'OFS et d'OWL/ANS. Trois cas :
 
- **Codes post-2006** (présents en ANS uniquement) : intégrés
  normalement, le code est créé via OWL/ANS comme documenté.
- **Codes vraiment orphelins** (absents des deux) : 5 cas observés
  dans AP-HP, 0 dans ORPHANET. Loggués dans `reports/external_orphan_codes.csv`
  pour audit, mais leurs synonymes/inclusions sont **ignorés** (pas
  de code à enrichir).
- **Codes au format compact non parseable** (ex : `B65-`, `nocode`) :
  - `nocode` (3756 occurrences dans l'Index) : **ignorés**, ce sont
    des renvois "voir X" sans code direct.
  - Intervalles ouverts (`B65-`, `R89-`) : **normalisés** en code
    racine (`B65`, `R89`) et validés contre OFS. Si le code racine
    existe, l'entrée est intégrée.
  - Notations dague exotiques (`I200+0`) : **ignorées**, cas isolés.
### Schéma uniforme du loader AP-HP / Index
 
Les 10 feuilles utiles du fichier HECTOR (Index + 9 spécialités) ont
**toutes le même schéma 4 colonnes** :
 
| Position | Rôle                                            |
|----------|--------------------------------------------------|
| 1        | libellé / synonyme                              |
| 2        | étiquette source constante par feuille          |
| 3        | code CIM-10 format compact sans point           |
| 4        | drapeau auxiliaire (quasi toujours `nocode`)    |
 
Un **loader unifié** paramétré par `(sheet_name, source_label)`
suffit, pas besoin de 10 loaders distincts. Le module
`loaders/external/aphp_hector.py` exporte une fonction
`load_aphp_hector(xlsx_path)` qui retourne un DataFrame consolidé
avec une colonne `source` correctement attribuée selon la feuille
d'origine.
 
**Conversion de format** : les codes sont stockés compacts (`A000`).
La normalisation vers le format standard (`A00.0`) se fait via
`^([A-Z]\d{2})(\d{1,3})$` avec insertion du point après les 3
premiers caractères. Les codes à 3 caractères (`A00`) sont conservés
tels quels.
 
**Divergence d'étiquettes** : la feuille "Endocrinologie" porte
l'étiquette `ED1` en colonne B (et non `END1`). Le loader utilise le
**nom de la feuille Excel** comme clé canonique, pas l'étiquette en
colonne B (plus robuste).



## Codes post-2006 (présents en ANS, absents d'OFS)

Pour les ~2300 codes ajoutés à la classification après le gel OFS
(novembre 2006) :

- Le code est créé dans le merge avec `source=ANS`.
- Toutes ses notes (inclusions, exclusions, synonymes) ont
  `source=ANS`.
- **Les notes multi-éléments restent sous forme de blocs textuels**
  (pas de parsing automatique, cf domain pitfall #8).
- Les artefacts structurels ANS (puces, indentation, ligatures comme
  æ) sont préservés tels quels dans le CSV. Les codes de redirection
  ANS (notés `[D22.-]` dans le RDF source) sont normalisés en
  parenthèses `(D22.-)` par le loader (cf pitfall #9).
- Les flags `is_dagger_in_pair` et `is_asterisk_in_pair` valent
  `False` sauf si une association est présente dans
  `atih-cim10:hasCausality` ou `atih-cim10:hasManifestation` côté ANS
  (et donc dans la table DAGSTAR enrichie).

Ces codes sont loggués dans `reports/post_2006_codes.csv` pour audit.

**Codes témoins de référence** : `U07.13` (« Autres examens et mises en
observation en lien avec l'épidémie COVID-19 ») et `A92.5` (maladie à
virus Zika).

> **Pitfall — ne pas prendre `U07.1` comme témoin CSV.** `U07.1`
> (COVID-19) reste le code post-2006 emblématique, mais il porte les
> sous-divisions ATIH `U07.10`..`U07.15` et il est **type 3 (père
> interdit) au kit ATIH** : non codable, donc hors du CSV, dont le
> périmètre est « feuilles + codes intermédiaires codables »
> (`codes_du_csv`, D2). Tout test de régression qui le vise sur le CSV se
> skippe silencieusement.
> Les témoins ci-dessus sont de vraies feuilles ; `U07.13` hérite en
> prime des redirections `(B34.2)`, `(B97.2)`, `(U04.9)` propagées
> depuis `U07.1`, ce qui préserve la valeur du test. L'absence de
> `U07.1` est verrouillée par un test dédié
> (`test_u07_1_absent_du_csv`). Le backlog
> `inclure_codes_intermediaires.md` a été appliqué le 2026-09-05 pour
> les seuls codes **codables** (800) : `U07.1` reste absent, à raison.
> `U07.1` reste en revanche
> parfaitement valide dans les tests unitaires sur données
> synthétiques.

## `chapter_policy` — composition de la section Formulations des fiches

> **Invariant absolu.** Ces règles gouvernent l'**assemblage des fiches**,
> rien d'autre. Le CSV maître, les Parquets et la colonne `texte` ne sont
> **jamais** modifiés : la forme source reste la seule référence
> auditable. Garantie par `test_le_csv_nest_pas_modifie`.

**Finalité — c'est elle qui départage toute ambiguïté.** La section
Formulations sert à (1) refléter le langage réellement employé par les
médecins dans les CRH, et (2) ne **jamais** élargir ni brouiller le
périmètre du code. Quand le comportement mesuré et une consigne écrite
divergent, c'est cette finalité qui fait foi — et le bon réflexe reste
de poser la question.

Toute la configuration vit dans
`referentials/curation/chapter_policy.yaml`. **Aucune règle n'est en
dur dans le code** : `policy.py` lit le YAML, `cards.py` l'applique.
Justification métier et calibration chiffrée dans
`docs/analyses/2026-08-09_qualite_sources_par_chapitre.md`.

### Les trois règles

- **R1 — filtrage par plage de codes × famille de sources.** Chapitres
  XIX (lésions), XX (causes externes) et XXI (facteurs Z) excluent
  toutes les sources externes ; chapitre XVIII (symptômes) conserve les
  sources réelles mais interdit la génération LLM. Les deux flags
  `sources_externes` et `generation_llm` sont **indépendants**.
- **R2 — plafonnement par famille.** 10 sur les fiches feuilles, 20 sur
  les fiches catégories, plus un plafond global de 50 sur les
  catégories. Deux valeurs distinctes et c'est délibéré : une feuille
  tire d'un seul code, une catégorie agrège toutes ses feuilles.
- **R3 — normalisation des entrées de l'Index vol3.** Transformation de
  **rendu** (`normalize_index.py`), appliquée à l'assemblage. Sur
  36 627 entrées : 11 638 retenues, 24 989 écartées.

R1/R2/R3 gouvernent la **seule** section Formulations. La section
« Consignes de codage » des fiches (cf. « Rendu dans les fiches »,
section guide MCO) n'y est **pas** soumise — contrat `(code, ctx)` sans
`rng` ni `outils`, et `test_section_hors_chapter_policy` l'affirme.

### Profils de bibliothèque (chantier couverture ATIH, D4)

Clé `profils:` du même YAML — premier axe réel du backlog « profils de
fiches par usage » : le **statut MCO** du code. `generation` (défaut de
`cards build`, `outputs/cards_library`) ne construit que les codes
codables en MCO (`merged.codable_mco`, kit ATIH joint) ; `controle`
(`cards build --profil controle`, `outputs/cards_library_controle`)
construit tout, avec la ligne de statut. **Un `_index.csv` par
bibliothèque** (autoportance). Pas d'héritage entre profils : une
valeur par clé. Invariant dual, testé (`test_couverture_invariants.py`) :
**aucun père interdit, code supprimé ou inconnu du kit dans la
bibliothèque de génération** — on n'en retire rien du CSV maître ni du
nested set, on ne les construit pas dans ce profil. Sans kit joint, le
profil `generation` échoue bruyamment plutôt que de « filtrer » sur
rien. Les fiches catégories (3-car) ne sont pas profilées : une
catégorie n'est pas un code à tirer.

### Résolution par REMPLACEMENT, pas par fusion

L'ordre est **bloc > chapitre > défaut**, et la règle la plus spécifique
**remplace intégralement** la moins spécifique — elle n'hérite **pas**
de ses champs absents. Une entrée de bloc doit donc **redéclarer** tout
ce qu'elle veut conserver du chapitre. C'est le seul choix qui permette
de *ré-admettre* une source au niveau d'un bloc. L'oublier rouvre des
sources en silence. Verrouillé par `test_remplacement_et_non_fusion`.

### Pitfalls

1. **Trois lexiques, trois périmètres différents.** Les fusionner « par
   simplification » casse une garantie différente à chaque fois :

   | Lexique | Périmètre | Pourquoi |
   |---|---|---|
   | **Rections** (`du X`, `de la X`) | Index **inclus** | La syntaxe interne des entrées est du français naturel : elle témoigne du genre. |
   | **Casse** (mots vus en minuscule) | Index **exclu** | L'Index capitalise toute tête d'entrée par convention — il ne peut pas dire si un mot est un nom commun. |
   | **Juxtaposition** (dominance adjectivale) | CepiDc **exclu** ; virgules et parenthèses = **frontières dures** | CepiDc est télégraphique (pas d'articles) : tout nom y paraît adjectival. Sans frontières, l'Index se compte lui-même et se contamine. |

   Mesuré : sans exclure CepiDc, « cerveau » ressort adjectival (ratio
   0,46) et « hypoplasie du cerveau » serait cassé.

2. **Exclure des fiches ≠ exclure du pipeline de données.** R1 et R3
   retirent des entrées de la *section Formulations*. Ces mêmes entrées
   restent intégralement dans le CSV maître, avec leur `source`. Ne
   jamais « propager la cohérence » en les retirant en amont.

3. **La relecture de forme ne contrôle pas le périmètre.** Une entrée
   peut être parfaitement bien formée et désigner autre chose que le
   code : « Oculopathie (à), syphilitique (tardive) **nca** » normalisée
   en « oculopathie syphilitique » se lit très bien — et enseigne un
   périmètre faux, puisque `nca` désigne le *résidu non classé
   ailleurs*. C'est pourquoi les abréviations et méta-termes en tête ou
   en queue provoquent une **exclusion, jamais une amputation**. Ce sont
   deux validations distinctes ; ne jamais conclure de l'une à l'autre.

### Commandes

```bash
uv run recode-icd build lexicons          # les trois lexiques (déterministe)
uv run recode-icd cards build             # profil generation (codables MCO) → outputs/cards_library
uv run recode-icd cards build --profil controle   # tous les codes → outputs/cards_library_controle
uv run recode-icd cards build-categories
uv run python scripts/explore/relectures/export_relecture_index.py --graine 4242
```

`VERSION_REGLE` dans le script de relecture doit être **incrémentée à
chaque changement de comportement du normalisateur**, sinon les
relectures de deux versions se mélangent silencieusement.

## Recommandations du guide méthodologique MCO

> Livrable séparé — `referentials/processed/recommendations.parquet` +
> `recommendation_codes.parquet` — sur le patron de
> `dagger_asterisk.parquet`. **Le CSV maître n'est pas modifié** : les
> consignes de codage ne sont pas une source de synonymes ou
> d'inclusions, c'est une famille d'information nouvelle.
>
> Modèle, catalogue des rôles et doctrine d'extraction :
> `docs/analyses/2026-08-09_conception_base_recommandations_guide_methodo.md`
> (RÉFÉRENCE — à lire avant toute modification de `recommendations/`).

Cible du procédé : sortie machine tracée à partir du PDF, relecture humaine obligatoire pour validation et corrections, gel par empreinte. La relecture est une étape structurelle, pas transitoire : l'outillage sert à la diriger (intégrité des mots prouvée, orphelines listées, écarts déclarés), jamais à la supprimer. Toute proposition d'heuristique visant à éviter une relecture doit être refusée au profit d'une déclaration dans curation.yaml

### Deux tables, dix rôles

`recommendations` porte la consigne (une ligne), `recommendation_codes`
ses cibles (N lignes). **La sémantique positionnelle vit dans
l'association, jamais dans le texte seul.** Chaque association déclare
aussi sa **portée** : `chaque` (défaut — la consigne régit chaque code
de l'expression) ou `ensemble` (l'expression est le domaine d'un choix
— jamais résolue vers les feuilles, cf. pitfall 7).

Les dix rôles se rangent en trois familles :
`DP`/`DR`/`DAS` (position prescrite) ·
`interdit` / `interdit_DP` / `interdit_DR` / `interdit_DAS` /
`interdit_association` (emploi ou position proscrits) ·
`regi` / `contexte` (ni l'un ni l'autre).

### Rendu dans les fiches (chantier du 2026-09-03)

Les fiches feuilles portent une section `## Consignes de codage (guide
méthodologique <millésime>)`, insérée entre « À ne pas décrire » et
« Formulations » (le normatif reste groupé avant le lexical). Sélection
et forme dans `recode_icd/recommendations/rendu.py`, branchement par
`cards._section_consignes` ; prototype validé et démonstrations dans
`scripts/explore/rendu_recommandations_fiches.ipynb` (qui importe
`src/`). Règles : filtre `centralite=sujet`, exclusion de `contexte`
avant dédup, dédup par `rec_id` (`sujet` prime sur `exemple`, puis le
plus spécifique), tri `cle_de_tri`, préfixe `[rec_id]`, exemples en
bloc cité `>` (« À titre d'exemple dans le guide : »), règles de
chapitre regroupées en fin de section avec leur `situation` entre
parenthèses. **Hors chapter_policy** (cf. section chapter_policy).
Sans les deux parquets, les fiches se construisent sans la section et
`BuildSummary` porte un avertissement. Fiches catégories : pas de
section (feuilles seules dans `recommendation_codes`). Huit témoins de
régression dans `tests/regression/test_cards_consignes.py`.

### Pitfalls

1. **L'extraction LLM ne rentre JAMAIS dans le pipeline.** Le build ne
   lit que `data/guide_mco/*_curated.csv`, validés humainement ligne à
   ligne — patron `dagger_curation.csv`. `data/guide_mco/extraction/`
   est une **trace de curation**, pas une entrée. Une seule porte
   d'entrée vers les tables curées : la validation ligne à ligne.

2. **`interdit` ≠ `interdit_DP`/`interdit_DR`/`interdit_DAS`.** Le
   premier proscrit le code ; les trois autres ne proscrivent qu'une
   **position**. Les confondre ferait disparaître des codes légitimes :
   `Z43.–` ne doit pas être en DAS en sus d'un acte CCAM, mais reste le
   DP légitime d'une fermeture de stomie.

3. **`regi` ≠ `contexte`.** `regi` = la consigne **régit l'emploi** du
   code (le prescrit, le conditionne ou le décrit) sans lui assigner de
   position. `contexte` = le code **délimite la situation**, la consigne
   ne régit pas son emploi. Un rendu qui veut « les consignes qui
   parlent de ce code » filtre sur `regi` et les positions, jamais sur
   `contexte`.

4. **La spécificité vient de l'expression, pas du référentiel.**
   `merged.type` ne vaut que `chapter|block|category` : `Z86.70` y est
   typé `category` exactement comme `I69`. Le tri code > catégorie >
   plage > chapitre se dérive de `code_expr` telle qu'écrite dans la
   table curée.

5. **Doctrine d'extraction** : on n'associe une expression que si la
   consigne **régit son emploi ou le positionne**. Les mentions de
   passage restent dans le `texte`. Une consigne de chapitre qui régit
   vraiment doit, elle, descendre sur toutes ses feuilles — c'est la
   nature du lien qui décide, pas son coût.

6. **Une expression non parsable ou non résolue va au RAPPORT, jamais
   au silence.** Une consigne avalée est indétectable en aval : rien
   dans la fiche ne signale son absence.

7. **La résolution suppose la portée « pour tout ».** Les prescriptions
   dont l'expression est un **domaine de choix** (« il existe ») doivent
   être déclarées `portee=ensemble` à la curation — jamais résolues vers
   les feuilles, jamais restreintes par interprétation à une liste de
   codes que le guide n'a pas écrite. Critère de partage : **qui fait le
   choix entre les membres de l'expression ?** L'état du patient (chaque
   membre est régi quand il est le diagnostic) → `chaque`. Un élément
   extérieur à l'expression (le motif de séjour, la situation) →
   `ensemble`. Les interdictions sont des « pour tout » par nature.
   Paire d'exemples : AVC-01 (« un code I60.– à I63.– pour un AVC
   constitué ») est `chaque` ; AVC-14 (« le DP appartient au chapitre
   XXI ») est `ensemble` — avant la bascule, cette seule association
   faisait descendre l'article AVC sur les 750 feuilles du chapitre XXI
   (fiche de Z23.0 comprise). L'association `ensemble` part au rapport
   de build, et le pandera de la table résolue verrouille l'invariant.

8. **La curation est fidèle à la notation du guide, la résolution
   traduit — jamais l'inverse** (arbitrage n° 12, cas O04). Quelques
   catégories sont encodées par le référentiel avec 4e et 5e caractères
   **inversés** : « O04.90 » du guide est la feuille `O04.-0.9`. La
   table curée écrit ce que le guide écrit ; la traduction est
   déclarée dans `referentials/curation/notations_codes.yaml` (lue par
   `notations.py`, passée au parseur par le build),
   limitée aux catégories à encodage inversé, chaque entrée testée dans
   les deux sens. Toute forme hors table reste non parsable, au
   rapport ; les traductions sont tracées dans
   `guide_mco_expressions_traduites.csv`. Ne jamais « corriger » une
   expression curée vers la forme du référentiel pour faire passer un
   build : déclarer la catégorie dans la table, ou laisser l'expression
   au rapport.

### Substrat : brut → curé → validé → figé

On ne devine pas, on déclare — voir la cible du procédé en tête de section. Un curé n'existe qu'en vert (test d'intégrité) et n'est figé qu'après relecture humaine, avec relecteur et date dans curation.yaml.

| Répertoire | Contenu |
|---|---|
| `data/guide_mco/extraits_bruts/` | sortie `pdftotext -layout` intacte (commande + version de poppler en tête) — artefact régénérable |
| `data/guide_mco/extraits/` | transcription **curée**, relue, validée, figée — substrat d'ancrage du chantier B |

La curation est un **reformatage sans réécriture**. Autorisé : recoller
les lignes coupées, reconstruire les tableaux, replier les notes de bas
de page à leur point d'appel (`[^57: texte]`), baliser articles et
sections. **Interdit : paraphrase, condensation, réordonnancement du
corps, correction du texte du guide.** Les erreurs de l'original se
signalent en marge — en commentaire HTML — elles ne se réparent pas.

`recode_icd.recommendations.transcription` rend la règle vérifiable, sur
quatre déclarations de `data/guide_mco/extraits/curation.yaml` :
`bornes` (lignes couvertes, l'extraction se faisant en pages entières),
`suppressions_mecaniques` (artefacts de pagination),
`suppressions_editoriales` (renvois de couche 2, avec motif) et
`restitutions` (contenu du PDF absent du brut, avec sa page).

> ⚠ **PITFALL — le brut est lossy, et les contrôles machine ne le
> couvrent pas.** `pdftotext` a rendu quatre lignes vides là où le PDF
> porte le tableau du §4.1 de l'article dénutrition : douze seuils
> chiffrés, perdus, parce que le tableau est incorporé en **image**.
>
> Le test d'intégrité garantit la fidélité **à l'extrait**, jamais la
> complétude vis-à-vis du **PDF**. Un curé peut être vert et amputé d'un
> tableau entier. **Seule la relecture humaine du PDF détecte ce contenu
> perdu** — et c'est une des raisons d'être de la couche curée. Même
> limite pour les plages de citation : une citation peut retomber
> exactement à sa ligne dans un extrait incomplet.
>
> Corollaire : une **restitution** n'est vérifiable par aucune machine,
> puisque son contenu n'est nulle part dans l'extrait. Elle porte donc sa
> `page_pdf`, et la contre-lecture est visuelle.

> ⚠ **PITFALL DE PROCÉDÉ — l'ancrage des notes.** Un mécanisme de
> dérivation positionnelle (colonne de l'exposant hissé dans la sortie
> `pdftotext`) a été construit puis **retiré après quatre itérations** :
> sa sophistication croissait plus vite que son rendement face à la
> déclaration manuelle, qui coûte ≈ 2 min par note. Il violait de plus
> le principe de la relecture structurelle — l'outillage dirige la
> relecture, il ne la remplace pas.
>
> **Toute proposition de le réintroduire doit d'abord battre ce coût.**
> Dix-neuf notes déclarées à la main valent moins d'une heure ; aucune
> des quatre itérations n'a tenu dans ce budget.

> ⚠ **PITFALL — un contrôle différentiel est aveugle aux défauts de son
> propre code.** Le test d'intégrité compare deux artefacts dérivés du
> MÊME dépouillement. Si ce dépouillement est fautif, il l'est des deux
> côtés à la fois : le contrôle reste vert en comparant des jetons
> corrompus.
>
> Vécu le 2026-08-31 : `_depouille` amputait les codes CIM dont les
> chiffres coïncident avec un numéro de note déclaré — `Z29` → `Z`,
> `Z51.30` → `Z51.` — sur un chapitre qui numérote ses notes de 23 à 48
> et cite `Z29`, `Z33`, `Z37`, `Z40`, `Z51.30`. Trois curés verts, et
> des données fausses.
>
> **Les pièges connus se testent par invariant ABSOLU, jamais par
> comparaison** : « un code CIM n'est jamais dépouillé » s'affirme sur
> une entrée choisie, pas sur l'égalité de deux sorties. Tout piège
> identifié dans ce chantier doit recevoir son test d'invariant.

**Conventions de forme d'un curé** (fixées à la relecture du chapitre
XXI, 2026-09-02) : `###` pour les titres de catégorie, blocs cités `>`
avec puces `>-` pour les exemples du guide, `**…**` pour les
paragraphes que le PDF met en gras, puces `-` pour les listes. Les
équivalences de balisage — `>`, `**`, `–`, `•`, `*`, filets de tableau
— sont déclarées dans `transcription.py` et ne comptent pas dans le
flux de mots.

> **Backlog** : le rendu des exemples en blocs cités est une convention
> de transcription, pas encore une décision de rendu de fiche. Quand les
> consignes seront injectées dans les prompts, il faudra décider si un
> exemple du guide entre dans la fiche, et sous quelle forme — cf.
> `docs/backlog/profils_fiches_par_usage.md`.

> ⚠ **Ne jamais élargir `curation.yaml` pour faire passer un test.**
> Un curé qui a perdu un paragraphe doit échouer bruyamment ; un curé
> qui invente une phrase aussi. C'est l'unique raison d'être du fichier.

**Circuit par article** : produire le curé (test vert) → relecture et
validation humaine, les tableaux surtout → commit et gel → l'extraction
des candidates s'ancre dessus.

**Le pilote n'est pas réancré** : ses citations sont validées contre les
bruts, on ne recale rien.

### Commandes

```bash
./scripts/extraire_guide_mco.sh                      # bruts (poppler requis)
uv run recode-icd build guide-mco                    # les deux Parquet + rapport
uv run pytest -k transcription                       # intégrité des curés
uv run python scripts/rendre_candidates_guide_mco.py # fiches de relecture (générées)
```

## Kit ATIH : statut MCO des codes (chantier couverture ATIH)

> Référence : `docs/source_mapping.md` section « Kit de nomenclature
> ATIH » ; mesure et propositions dans
> `docs/analyses/2026-09-05_couverture_atih_phase{1,2}_*.md`.

Le kit `data/CIM_ATIH_2025/LIBCIM10MULTI.TXT` est **la** source de
l'autorisation de codage en MCO. `build atih` → `atih_codes.parquet`
(source de vérité : `type_mco`, `statut_mco`, `codable_mco`,
`interdit_dp/dr/das` dérivés par construction, `supprime`) ; `build
merged --atih` joint `type_mco` / `statut_mco` / `codable_mco` à
`merged_codes` ; chaque fiche porte « Statut MCO (kit ATIH 2025) : … »
sous son titre et les `_index.csv` les colonnes `type_mco` /
`statut_mco`. Le CSV maître n'est pas modifié.

**Codable en MCO = type ≠ 3 et non supprimé.**

### Pitfalls

1. **Le type 3 n'est pas une interdiction clinique.** C'est un père
   (`A00`, `U07.1`, `W00` — dont les enfants sont codables) ou un code
   supprimé (`*** SUaa ***`, décodé en `supprime` + millésime, jamais
   réécrit). `U07.1` est type 3 : le témoin post-2006 des tests est
   `U07.13`, pas lui.
2. **Un code du maître inconnu du kit est `inconnu_atih`, pas null.**
   Ce n'est pas une absence d'information : le code n'est pas codable en
   MCO (1 618 localisations du chapitre XIII, `N06.9`). Null ne veut dire
   qu'une chose — le kit n'a pas été joint (`build merged` sans
   `atih_codes.parquet`).
3. **Trois écritures d'un même code, une seule table.** Compacte
   (`O0490`), pointée (`O04.90`), maître (`O04.-0.9`) : la traduction
   vit dans `referentials/curation/notations_codes.yaml` lue par
   `recode_icd.notations`, deux familles inversées (O04, M62.8) et neuf
   catégories à `+` ponctué. Ne jamais insérer un point « à la main » ;
   `S37.8-0` (nœud) ≠ `S37.80` (feuille).

### Résolveur officiel des consommateurs (D0)

`recode_icd.couverture.resoudre_code(code, ctx)` — et la CLI
`recode-icd resoudre CODE…` — accepte **toute écriture** (compacte
`O0490`, pointée `O04.90`, maître `O04.-0.9`) et répond soit la fiche,
soit la **raison motivée** de l'absence : `intermediaire` (avec ses
feuilles qui ont une fiche), `sans_ligne`, `pere_interdit` (avec ses
enfants), `supprime`, `tronc_chapitre_xx` (avec le tronc),
`absent_du_maitre` (avec l'ancêtre), `inconnu_atih`, `inconnu`,
`notation_invalide`. Une fiche sur un code non codable est rendue
`fiche` avec `codable_mco=False` et un avertissement. **Aucun
traitement aval ne joint plus « à la main » sur le code** : il passe
par le résolveur, et journalise ses réponses négatives (`--journal`,
JSONL) — c'est la mesure d'usage qui priorise la suite.

### Commandes

```bash
uv run recode-icd build atih          # kit → atih_codes.parquet + reports/atih_kit_summary.csv
uv run recode-icd build merged        # joint le statut (option --atih, défaut : le parquet)
uv run recode-icd resoudre O0490 M000 W0004 --journal outputs/usage/resolutions.jsonl
uv run recode-icd resoudre A18.1 --json
```

## Mapping sources internes ↔ libellés CSV

Le modèle Python utilise des enums UPPERCASE pour les sources. Le CSV
exporté utilise des libellés français lisibles. Le mapping vit dans
`exporters/flat_csv.py` :


| `NoteSource` (Python)    | `source` (CSV)              |
|--------------------------|------------------------------|
| `OFS`                    | `CIM-10`                    |
| `OWL_ANS`                | `ANS`                       |
| `SYNTHESIZED_SIBLING`    | `CIM-10 frères`             |
| `INDEX_CIM10_VOL3`       | `CIM-10 index`              |
| `ORPHANET`               | `ORPHANET`                  |
| `APHP_DERMATOLOGIE`      | `AP-HP Dermatologie`        |
| `APHP_ENDOCRINOLOGIE`    | `AP-HP Endocrinologie`      |
| `APHP_GRONES`            | `AP-HP GRONES`              |
| `APHP_METABOLISME`       | `AP-HP Troubles métaboliques` |
| `APHP_NEPHROLOGIE`       | `AP-HP Néphrologie`         |
| `APHP_OPHTALMOLOGIE`     | `AP-HP Ophtalmologie`       |
| `APHP_RHUMATOLOGIE`      | `AP-HP Rhumatologie`        |
| `APHP_GERMES`            | `AP-HP Germes (SPILF)`      |
| `APHP_SRLF`              | `AP-HP SRLF`                |
| `CEPIDC_2015`            | `CepiDc 2015`               |

Toute nouvelle source ajoutée passe par les DEUX endroits : l'enum
Python et le mapping d'export. Test de régression vérifie qu'il n'y a
pas d'enum sans libellé CSV correspondant.

> **Note sur les sources AP-HP** : chaque feuille métier de HECTOR a sa
> propre valeur d'enum. Cela permet au consommateur de filtrer
> facilement par préfixe : `df.filter(pl.col("source").str.starts_with("AP-HP"))`
> récupère toutes les spécialités. La feuille "Cim Alphabétique" du
> même fichier HECTOR n'est PAS un thésaurus AP-HP mais l'index
> alphabétique officiel CIM-10 vol3 — elle utilise donc l'enum
> `INDEX_CIM10_VOL3` distinct.

## Conventions de code

- Toutes les fonctions de fusion et de propagation sont **pures** et
  **déterministes** (mêmes entrées → byte-equivalent en sortie).
- Les loaders renvoient des DataFrames polars **validés par pandera**.
- La source de toute information est tracée par une colonne `source` ;
  jamais d'agrégation silencieuse.
- Les tests de régression utilisent une dizaine de codes témoins fixés
  dans `tests/fixtures/sample_codes.yaml`. Liste obligatoire :
  - Un code avec dague/astérisque (par ex `A18.1`)
  - Un code avec exclusions multiples (ex : `I78.1` et ses 11 nævus)
  - Un code en chapitre XX
  - Un code en chapitre XXI
  - Un code dans C00-C75 avec sous-catégorie `.8` (par ex `C50.8`)
  - **`U07.13`** (COVID-19) et **`A92.5`** (Zika) comme codes post-2006
    — vraies feuilles, contrairement à `U07.1` (cf pitfall § Codes
    post-2006)
  - Un code astérisque **non pointé** (`L62.8`, plus `N16.8` comme
    témoin riche) — pas `L62` lui-même, qui est un nœud intermédiaire
  - Un couple typique pour tester `redundancy_level=subordinate` dans
    la table DAGSTAR enrichie (par ex `A17.8` / `G05.0`)
- Un code avec un synonyme ORPHANET en relation E (par ex `D59.5`  pour "Hémoglobinurie paroxystique nocturne")
> - Un code avec une inclusion ORPHANET en relation NTBT (à
>   identifier au build, par exemple un code D70 avec une variante
>   de neutropénie)
> - Un code couvert simultanément par OFS, Index CIM-10 vol3 et une
>   spécialité AP-HP (pour tester la dédup tolérante inter-sources)
> - Un code avec note propagée depuis un niveau supérieur (par exemple un 
>   code dans le bloc A00-A09 qui hérite d'une note attachée au bloc), 
>   pour tester `source_level` et `inherited_from_code` non vides.
  
## Workflow Claude Code recommandé

- Avant toute modification non-triviale : `/plan` puis validation du plan
  par moi (l'utilisateur) avant implémentation.
- Lancer `uv run pytest -m unit` après chaque modification logique
  significative.
- Pour les explorations OWL/OFS, créer un script ou notebook dans
  `scripts/explore/` plutôt que de polluer `src/`.
- **Tout notebook ou script d'exploration dans `scripts/explore/` doit
  commencer par** :

  ```python
  from recode_icd.utils.loaders_dev import load_exploration_context
  ctx = load_exploration_context()
  ```

  Ne PAS dupliquer la logique de chargement des tables OFS, du Parquet
  ANS, des artefacts du pipeline ou des rapports. Si une source utile
  manque dans `ExplorationContext`, étendre `loaders_dev.py` plutôt que
  de coder un loader ad-hoc dans le notebook.

  `loaders_dev` est **dev only** — ne JAMAIS l'importer depuis
  `src/recode_icd/loaders/`, `merge.py`, `propagation.py`,
  `exporters/`, ou `cli/`.

  `loaders_dev.py` ne contient QUE des fonctions de chargement, jamais
  de calcul ou de transformation métier. Toute logique métier reste
  dans `src/recode_icd/`.

- Les notes d'inclusion/exclusion contiennent souvent des libellés
  médicaux exotiques (latinismes, abréviations) — **ne jamais "normaliser"
  silencieusement** un texte, toujours préserver le texte source.

