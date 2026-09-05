# Couverture ATIH — phase 2 : propositions d'architecture (2026-09-05)

**Branche** `feat/couverture-atih` · **Statut** : propositions soumises,
rien d'implémenté. Une section par décision, dans l'ordre de priorité
fixé par RF ; chaque option porte son chiffrage (fichiers, ordre de
grandeur de code et de tests, effet sur les livrables, risques) et une
recommandation. Les chiffres viennent de la phase 1
(`2026-09-05_couverture_atih_phase1.md`) et de mesures complémentaires
faites pour ce document (contenu disponible par code, structure du
chapitre XX).

Invariant cible, posé en fin de chantier seulement : **« tout code
autorisé MCO a une fiche »** — sur les 15 071 codes hors chapitre XX,
et sur le chapitre XX au sens de la composition retenue en D5.

Dépendances entre décisions : D1 fournit la colonne dont D2, D4 et D5
ont besoin (le statut MCO de chaque code) ; D2 et D3 modifient la liste
des codes construits ; D4 et D5 ne touchent qu'au rendu. Ordre de
réalisation proposé : **D1 → D4 (marquage) → D2 (110 puis 800) → D3 →
D5**.

---

## D1 — Le kit ATIH devient une donnée des livrables

**Besoin.** Le Type MCO/HAD (et le profil SMR) comme métadonnée de
chaque fiche et colonne des parquets : filtre de génération (un code
type 3 ou supprimé ne se tire jamais) et source systématique de règles
positionnelles pour le vérificateur (type 1/2 → jamais DP ni DR, type 4
→ jamais DP), complémentaire des consignes du guide.

**Ce que le kit apporte, par code** (42 897) : `type_mco` 0-4, profil
SMR (3 drapeaux O/N : manifestation morbide principale, affection
étiologique, DAS), `type_psy` 0/1/3, libellé court, libellé long, et un
marqueur de suppression dans le libellé (`*** SUaa ***`, 401 codes, tous
type 3). Le kit ne porte ni hiérarchie ni millésime explicite : le
millésime se déclare (constante `2025`, comme `2026-provisoire` pour le
guide).

### Option D1-a — Parquet dédié `atih_codes.parquet` + jointures (recommandée)

- **Loader de production** `loaders/atih.py` (le loader dev de la phase
  1, promu, avec la table de notation — cf. D1-c) ; schéma pandera
  `AtihCodesSchema` : `code` (écriture du maître), `code_atih` (compact),
  `type_mco`, `smr_mmp`, `smr_ae`, `smr_das`, `type_psy`, `supprime`
  (bool + millésime SU), `libelle_court`, `libelle_long`, `millesime`.
  Codes sans écriture au maître (chapitre XX, 72 absents) : `code` =
  écriture naïve, colonne `au_maitre=False`.
- **Dérivation des règles positionnelles**, dans le même parquet, par
  construction depuis le type : `interdit_dp`, `interdit_dr`,
  `interdit_das`, `codable_mco` (= type ≠ 3 et non supprimé). Une seule
  source de vérité pour le vérificateur et recode-scenario, sans passer
  par le modèle des consignes.
- **Jointure dans `merged_codes.parquet`** : colonnes `type_mco`,
  `codable_mco` (nullable : inconnu de l'ATIH → null, ce qui EST une
  information — cf. D4). `MergedCodesSchema` est `strict` : +2 champs,
  +1 test de schéma.
- **Fiches** : une ligne de métadonnées sous le titre — `Statut MCO
  (ATIH 2025) : codable, pas de restriction` / `interdit en DP et DR
  (cause externe)` / `non codable en MCO (père)` / `supprimé en 2009` /
  `inconnu du kit ATIH` — et deux colonnes dans `_index.csv`
  (`type_mco`, `statut_mco`). Le CSV maître (9 colonnes) **n'est pas
  modifié** : le statut n'est pas une note.
- **Métadonnées Parquet** : `atih_kit_version` dans le dict écrit par
  `write_parquet_with_metadata` (pitfall n° 5 : la version cible
  explicite).
- **CLI** : `build atih` (kit → parquet) et option `--atih` de `build
  merged`.

Chiffrage : `loaders/atih.py` ~150 lignes + `schemas.py` +30 ; `merge.py`
+40 (jointure) ; `cards.py` +40 (ligne de statut, index) ; `cli/build.py`
+40 ; ~25 tests (loader sur fixture synthétique, schéma, 3 témoins de
statut — un type 0, un type 2 du chapitre XX, un supprimé —, métadonnées,
déterminisme) ; docs : `source_mapping.md` (nouvelle section « Kit ATIH »,
politique de fusion : *statut MCO — source ATIH, pas de fallback*),
CLAUDE.md (structure + pitfall « le type 3 n'est pas une interdiction
clinique, c'est un père ou un code supprimé »). Build : +1 s. Aucune
fiche ne change de contenu clinique ; 16 058 fiches gagnent une ligne.

### Option D1-b — Les règles positionnelles comme consignes synthétiques

Cinq consignes `ATIH2025-MCO-T1..T4` (+ « supprimé ») dans
`recommendations.parquet`, associations = tous les codes du type (26 536
pour le type 2), rendues sur les fiches par la section « Consignes de
codage ».

Chiffrage : `RecommendationsSchema.rec_id` (`^GM\d{4}-…`) et le
catalogue des rôles à élargir ; +40 000 lignes dans
`recommendation_codes.parquet` (×3) ; **une ligne de plus sur 28 000
fiches de génération** — c'est du bruit là où la note d'évaluation du
2026-08-09 dit que les interdictions amorcent ce qu'elles interdisent.
Écartée pour le rendu ; reste possible **plus tard, pour le seul
vérificateur**, en lisant `atih_codes.parquet` via la même interface
que les consignes (rôles `interdit_DP`/`interdit_DR` existent déjà).

### Option D1-c — La table de notation unique (transversale, incluse dans D1-a)

La clé de correspondance de la phase 1 devient
`referentials/curation/notations_guide.yaml` élargi — renommé
`notations_codes.yaml` — avec **deux familles inversées déclarées**
(`O04` : `O04.-<5e>.<4e>` ; `M62.8` : `M62.8-<6e><5e>`) et les neuf
catégories à `+` ponctué, lue par `recommendations/notations.py` (déjà
en place, à généraliser : la traduction guide ↔ référentiel et ATIH ↔
référentiel sont la même fonction, `O0490` du kit et `O04.90` du guide
ne différant que par le point). Testée dans les deux sens sur le kit
entier (42 897 codes → identité) et sur le maître (injectivité) : ce
sont les assertions du script, promues en tests de régression.

Chiffrage : `notations.py` +80 lignes (famille M62.8, `+` ponctué, sens
ATIH), YAML +20, 8 tests, `test_guide_mco_notations.py` inchangé (les
dorés ITG restent verts). Bénéfice : le parseur du chantier B, le
loader ATIH et le futur vérificateur partagent **une** table — aucune
règle de notation en dur nulle part (arbitrage 12 étendu).

**Recommandation D1 : a + c.** Le parquet dédié est la source de
vérité ; la colonne de `merged` et la ligne de fiche en sont des vues.

---

## D2 — Les 110 « seul niveau codable », puis les 800 intermédiaires

**Contenu disponible par code** (mesuré) :

| | 800 intermédiaires autorisés | dont 110 seul niveau codable |
|---|---|---|
| lignes **propres** OFS/ANS (`propagated_notes`, non héritées) | 644 sur 374 codes (364 excl., 268 incl., 12 éditoriales) | 71 sur 53 codes |
| synonymes propres (`merged.synonymes`) | 258 codes | 42 codes |
| définitions ANS | 109 codes | 0 |
| **aucun contenu propre** | **404 codes** | **57 codes** |
| lignes **héritées** déjà calculées par la propagation | 4 758 sur 796 codes | 607 sur 109 codes |
| entrées **externes aujourd'hui rejetées** (« non terminal ») : Index vol3 / CepiDc / AP-HP rhumato / ORPHANET | 2 700 (584 codes) / 7 876 (345) / 374 (242) / 426 (84) | 324 (93) / 383 (33) / 104 (62) / 51 (8) |
| feuilles descendantes | 6 052 | 1 052 |

Deux lectures des 110 : pour `M16.0` (coxarthrose post-traumatique
bilatérale), les feuilles `M16.0x` sont les localisations OFS de 5e
position, **que l'ATIH ne code pas** — le code MCO est `M16.0` et sa
fiche est aujourd'hui éclatée en dix fiches non codables. Pour
`Z37.0/2/5`, l'ATIH s'arrête aussi au niveau supérieur mais nos
subdivisions `Z37.x0/x1` sont vides de toute source. Dans les deux cas
la fiche du niveau codable manque.

### Option D2-H — Fiche par héritage : élargir le périmètre du CSV aux codes codables

`_leaf_codes()` retient les feuilles strictes ; il retiendrait **les
feuilles ∪ les nœuds `codable_mco`** (D1). Effets mécaniques :

- le code reçoit ses lignes propres + les lignes héritées (déjà dans
  `propagated_notes`) ; `source_level`/`inherited_from_code` restent
  exacts ;
- `merge_external` cesse de rejeter les entrées sur ces codes : ~11 500
  formulations (Index, CepiDc, AP-HP, ORPHANET) entrent au CSV sous
  leur source, dédup tolérante inchangée ;
- la fiche se construit par le chemin standard (Périmètre, À ne pas
  décrire, Consignes — déjà résolues sur ces codes par le nested set,
  Formulations) ; aucune synthèse des descendants.

Chiffrage : `flat_csv.py` +15, `merge_external.py` +20
(`entries_dropped_non_terminal` → « non terminal non codable » seulement),
`cards.py` 0 (itère sur les codes du CSV), 12 tests (témoins `M16.0`,
`F00.0`, `Z37.0`, `C25.9`, `U07.1` — qui reste **absent**, type 3 —,
volumétrie), `source_mapping.md` (§ périmètre du CSV : « feuilles et
codes codables MCO »), backlog `inclure_codes_intermediaires.md` clos
avec la réponse chiffrée. CSV : +~17 000 lignes (5 400 propres/héritées
+ 11 500 externes) ; **+800 fiches** ; les trois `skip` historiques de
`U07.1` restent des skips (le témoin est type 3). Build fiches : +16 s.
Risque : une fiche `M00.0` porte le périmètre de dix localisations sans
les nommer — acceptable pour la génération (le clinicien écrit « arthrite
à pneumocoque du genou », le code de localisation est un raffinement),
insuffisant pour le vérificateur (D2-P le complète).

### Option D2-P — Fiche propre : héritage + synthèse des descendants

D2-H plus une section **« Subdivisions codables »** (ou « Localisations »
quand les feuilles sont des 5e positions du chapitre XIII — la section
existe déjà pour les codes type D) listant les feuilles avec libellé,
sur le patron des exclusions frères synthétisées (`SYNTHESIZED_SIBLING`
: source dédiée, `inherited_from` vide, une ligne par feuille). Pas
d'union des synonymes des feuilles : elle brouillerait le périmètre
(finalité de `chapter_policy`).

Chiffrage : `relations/sibling_exclusions.py` +60 (générateur
« subdivisions », même cas limites), `NoteSource.SYNTHESIZED_SUBDIVISION`
+ libellé CSV `CIM-10 subdivisions`, `cards.py` +30, 10 tests. CSV :
+6 052 lignes. Pour les 404 codes sans contenu propre, la fiche n'est
alors **pas** un titre nu : position + héritage + subdivisions +
consignes.

**Recommandation D2 : H d'abord (les 110, puis les 800 — même code,
deux témoins), P ensuite** si le vérificateur en a besoin. H seul règle
l'invariant ; P est un enrichissement de rendu.

---

## D3 — Les 59 feuilles sans ligne et les 72 extensions absentes

**Deux situations distinctes.** Les 59 existent dans le nested set (ANS)
avec un libellé, sans aucune ligne ; les 72 n'existent nulle part au
maître (extensions ATIH postérieures ou étrangères à l'export ANS 2025).

### Option D3-a — Le kit ATIH comme source de codes et de libellés (recommandée)

- **Les 59** : `build_cards_library` itère sur `codes du CSV ∪ codes
  codables du nested set` (D1) ; `build_card` sait déjà construire une
  fiche sans ligne au CSV (chemin `_section_*_from_ans`, celui de
  `U07.1`) : titre, position, consignes résolues (les 16 résistances
  `U82/U83+x` reçoivent RAM-01..05, les `Z37.xx` leurs consignes du
  chapitre XXI), À ne pas décrire hérité. Les 59 fiches existent dès
  D1 + ce changement, **sans toucher au CSV** (un code sans note n'a pas
  de ligne : c'est le contrat du CSV, on ne l'invente pas).
- **Les 72** : injection dans le nested set au chargement OWL
  (`loaders/owl.py` construit l'arbre depuis des arêtes ; on ajoute les
  arêtes `ancêtre_maitre → code` avec le libellé long ATIH et
  `source=ATIH`), avant `build_nested_set` — le code devient un code
  comme un autre : propagation (il hérite des notes de son ancêtre :
  `I70.00` reçoit celles de `I70.0`), résolution des consignes
  (ATH-01 atteint `I70.x1`), CSV, fiche. Trace : `reports/atih_only_codes.csv`
  (patron `post_2006_codes.csv`) ; politique de fusion : *existence du
  code — OWL_ANS, **fallback ATIH*** (tableau du CLAUDE.md, une ligne).
  Le libellé ATIH remplace un libellé absent, jamais un libellé ANS.

Chiffrage : `owl.py` +40 (arêtes supplémentaires, tri déterministe),
`merge.py` +20 (colonne `code_source` ∈ {OWL_ANS, ATIH}), `cards.py`
+20 (liste des codes construits), `schemas.py` +5, 14 tests (les 72 sont
dans `merged` avec le bon parent ; `I70.01` hérite de `I70.0` ; un code
ATIH n'écrase jamais un code ANS ; les 59 ont une fiche ; `U82.2+0` porte
RAM-01), `source_mapping.md` +1 section. Nested set : left/right de
tous les nœuds recalculés — sans conséquence (aucun test ne fige un
intervalle) ; parquets régénérés. Fiches : +131.

### Option D3-b — Libellé ATIH comme ligne du CSV (`type=synonyme, source=ATIH 2025`)

Une ligne par code pour que le CSV « voie » le code. Chiffrage faible
(loader externe sur le patron CepiDc, +1 `NoteSource`, +1 libellé CSV,
8 tests), mais **faux sur le fond** : un libellé officiel n'est pas un
synonyme, et les 72 resteraient hors du nested set (pas de propagation,
pas de consignes). Écartée seule ; compatible avec D3-a si on veut
tracer *dans le CSV* que le libellé vient du kit (ligne `type=note`,
libellé CSV `ATIH 2025`) — à décider avec la politique de fusion.

**Recommandation D3 : a**, RAM en tête (les 16 codes de résistance sont
des feuilles sans ligne : disponibles dès D1, avant les 72).

---

## D4 — 299 fiches sur codes interdits/supprimés, 1 618 sur-fines du chapitre XIII

Rien ne se retire du CSV maître ni du nested set : les 1 612
localisations sont des codes OMS légitimes (chantier 2026-06-06), les
209 catégories du chapitre XX sont les troncs de D5, et un code
supprimé garde sa valeur d'audit (un CRH ancien peut le porter).

### Option D4-a — Marquage seul

D1 suffit : `statut_mco` dans `_index.csv` et ligne de statut sur la
fiche. Le consommateur filtre. Chiffrage : 0 au-delà de D1. Risque : un
tirage de génération qui ignore la colonne tire `W00` ou `M07.20`.

### Option D4-b — Exclusion par profil (recommandée)

Le backlog `profils_fiches_par_usage.md` demande où vit un profil ;
l'autorisation MCO en est le premier axe concret et le plus simple :
une clé `profils:` dans `chapter_policy.yaml` —

```yaml
profils:
  generation:            # défaut de `cards build`
    codes: codables_mco  # type ≠ 3, non supprimé, connu du kit
  controle:
    codes: tous
```

— résolue par `policy.py` (pas d'héritage entre profils : une valeur
par clé, le piège du remplacement/fusion ne se pose pas), appliquée par
`build_cards_library` comme filtre de la liste des codes, et
`cards build --profil controle` pour l'autre bibliothèque. Les 1 618
sur-fines et les 299 interdites sortent de la bibliothèque de
génération (16 058 → **14 141 + les fiches de D2/D3**) et restent dans
la bibliothèque de contrôle avec leur ligne de statut.

Chiffrage : `policy.py` +40, `cards.py` +25, `cli/cards.py` +10, YAML
+8, 10 tests (le profil génération ne contient aucun code type 3 ni
supprimé — **c'est le second invariant absolu du chantier**, dual du
premier ; le profil contrôle contient tout ; `W00` est dans l'un et pas
dans l'autre), backlog profils : premier axe traité, les autres
(ORPHANET, exclusions, R3) restent ouverts. Les deux bibliothèques
partagent le même `_index.csv` enrichi ou en ont un chacune (choix de
consommation à faire avec les data scientists).

### Option D4-c — Retrait

Écartée : détruit de l'information auditable et casse les témoins de
régression du chapitre XIII.

**Recommandation D4 : b** (a en est le sous-produit).

---

## D5 — Chapitre XX : périmètre séparé

**Structure du kit, mesurée.** 373 catégories, 27 097 codes. Deux
tables **constantes sur tout le chapitre** :

| Position | Table | Valeurs |
|---|---|---|
| lieu | 0 domicile · 1 établissement collectif · 2 école et lieu public · 3 lieu de sport · 4 rue ou route · 5 zone de commerce · 6 local industriel et chantier · 7 exploitation agricole · 8 autres lieux précisés · 9 lieu sans précision | 10 |
| activité | 0 sport · 1 jeu et loisirs · 2 travail à des fins lucratives · 3 autres formes de travail · 4 repos, sommeil, repas, activités essentielles · 8 autres activités précisées · 9 non précisée | 7 |

Trois patrons de composition, déterminés par la catégorie :

| Patron | Catégories | Forme | Codes |
|---|---|---|---|
| lieu + activité | 303 (W00-Y34 hors 4e OMS) | `W00` + lieu + [activité] | `W000`, `W0004` |
| 4e OMS + activité | V01-V99, Y40-Y84 (53 + ~100) | `V01.0` + [activité] | `V010`, `V0104` |
| 4e OMS + lieu + activité | 6 (`W26`, `X34`, `X47`, `X67`, `X88`, `Y17`) | `W26.0` + [lieu] + [activité], ou `W26.0` + `+` + activité (sans lieu) | `W2600`, `W26004`, `W260+4` |

Le type MCO est **2 pour tous** (jamais DP/DR) — une seule règle
positionnelle pour 27 097 codes.

### Option D5-a — 25 348 fiches

Chiffrage : +500 s de build, +150 Mo de markdown, 25 348 fiches dont le
texte clinique serait identique à celui du tronc à une locution près
(« , domicile, en pratiquant un sport »). Écartée : coût sans
information.

### Option D5-b — Fiche de tronc + règle de composition (recommandée)

- Une table dérivée **déterministe** depuis le kit :
  `chapitre_xx_composition.parquet` (tronc, patron, positions, valeurs
  admises, libellé de chaque valeur), validée pandera, construite par
  `build atih` — jamais écrite à la main.
- Les fiches des **troncs** (les 3 309 codes à 4 caractères de patron
  « 4e OMS », les 373 catégories de patron « lieu ») portent une section
  **« Composition MCO (ATIH 2025) »** : « ce code se complète en MCO
  d'un lieu (4e caractère, table) et, facultativement, d'une activité
  (5e) ; jamais en DP ni DR ». Les 209 catégories 3-car de type 3 (D4)
  deviennent des **troncs de composition** : marquées « non codable
  seul, se complète du lieu », pas « interdit ».
- L'invariant s'énonce : *un code autorisé du chapitre XX est couvert
  si son tronc a une fiche et si sa composition est dans la table* —
  testé sur les 25 348 (couverture 100 % par construction), avec un
  test de régression sur la stabilité des deux tables (10 et 7 valeurs,
  libellés figés).
- Le générateur tire le tronc et compose ; le vérificateur décompose le
  code d'un RUM en tronc + positions et contrôle chaque partie contre
  la table.

Chiffrage : `loaders/atih.py` +80 (dérivation des patrons, détection
des exceptions : `X49` porte des 6-car sans forme à `+`, à traiter comme
patron 3 sans variante), `cards.py` +40 (section), `schemas.py` +20,
14 tests, docs (`csv_usage_guide.md` : section chapitre XX pour les
consommateurs). Fiches : +0 ; la section apparaît sur ~3 700 troncs.

### Option D5-c — Fiches au niveau lieu (3 309 codes à 4 caractères) + composition de l'activité

Intermédiaire : couvre les codes les plus fréquents en RUM (le lieu est
obligatoire, l'activité rare) au prix de 3 309 fiches quasi identiques.
Non recommandée tant que D5-b n'a pas été essayée par les consommateurs.

**Recommandation D5 : b.** Décision de périmètre à acter séparément,
après D1-D4 ; elle ne bloque pas l'invariant hors chapitre XX.

---

## Récapitulatif

| Décision | Recommandation | Code + tests (ordre de grandeur) | Livrables |
|---|---|---|---|
| D1 | parquet `atih_codes` + colonne `merged` + ligne de fiche + table de notation unique | ~350 lignes, ~35 tests | +1 parquet, `merged` +2 colonnes, `_index` +2 colonnes |
| D2 | H (110 puis 800), P plus tard | ~100 lignes, 12 tests (H) | CSV +17 000 lignes, +800 fiches |
| D3 | a (RAM en tête) | ~110 lignes, 14 tests | +131 fiches, +1 rapport |
| D4 | b — profil `generation` = codables seulement | ~85 lignes, 10 tests | bibliothèque génération 16 058 → ~15 070 |
| D5 | b — tronc + composition | ~150 lignes, 14 tests | +1 parquet, section sur ~3 700 troncs |

Au terme de D1-D4 : **15 071 codes autorisés hors chapitre XX, 15 071
fiches** ; l'invariant « tout code autorisé MCO a une fiche » peut être
posé en test de régression, avec son dual « la bibliothèque de génération
ne contient aucun code non codable ». Après D5, l'invariant s'étend au
chapitre XX par composition.

Ce qui reste hors chantier : le diff de millésime du kit (le kit est
annuel comme le guide — même backlog que `diff_millesime_guide_mco.md`),
et l'usage des profils SMR/PSY (portés par le parquet, sans consommateur
aujourd'hui).
