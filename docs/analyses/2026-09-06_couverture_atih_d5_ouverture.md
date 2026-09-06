# Couverture ATIH — D5, rapport d'ouverture : chapitre XX par composition (2026-09-06)

**Décision RF (2026-09-06)** : option « tronc explicite ». La catégorie
(`W00`…) porte la fiche de tronc, marquée structurellement « non
codable seul — se compose du lieu (4ᵉ) et de l'activité (5ᵉ) », admise
dans la génération par **exception déclarée au profil**. Pas
d'injection des 3 309 codes à 4 caractères : elle matérialiserait le
premier étage de la combinatoire que D5 existe pour éviter, et le
contenu vit déjà sur les catégories.

Trois garde-fous exigés : (1) I2 reformulé sans affaiblissement —
aucun code non codable *présenté comme émissible* dans la génération ;
les troncs sont une classe déclarée (`tronc_composition` à l'index), la
seule admise, tout autre type 3 reste une violation — testé dans les
deux sens ; (2) la fiche de tronc ouvre sur son marquage, avant tout
contenu ; (3) le résolveur valide les codes composés (`W0009` → tronc
`W00` + lieu 0 + activité 9, ou le rejet motivé d'un suffixe invalide).

## Recensement des patrons — mesuré sur le kit (373 catégories, 27 097 codes)

Rôle de chaque position, déterminé par les libellés du kit (le suffixe
d'un code par rapport à son parent est comparé aux tables lieu et
activité) :

| Patron | Catégories | Tronc | Positions | Exemples |
|---|---|---|---|---|
| **lieu + activité** | 201 | catégorie 3-car (type 3) | 4ᵉ = lieu, 5ᵉ = activité (facultative) | `W00`, `W03`…`Y33` : `W000`, `W0004` |
| **OMS + activité** | 102 | code OMS 4-car (type 2, codable, fiche existante) | 5ᵉ = activité | `V01.0` : `V0104` — transports, `Y40`-`Y84` |
| **OMS + lieu + activité**, forme `+` | 6 | code OMS 4-car (codable) | 5ᵉ = lieu, 6ᵉ = activité ; `+` = activité sans lieu | `W26.0` : `W2600`, `W26004`, `W260+4` (`W26`, `X34`, `X47`, `X67`, `X88`, `Y17`) |
| **lieu seul** | 1 | catégorie 3-car | 4ᵉ = lieu | `Y34` |
| **lieu + activité + précision** | 1 | catégorie 3-car | 4ᵉ = lieu, 5ᵉ = activité, 6ᵉ = agent (0 acide fluorhydrique, 1 ciment) | `X49` : 220 codes |
| OMS seul, pas d'extension | 52 | — (les codes OMS 4-car sont codables et ont leur fiche) | — | `X59`, `Y06`, `Y07`, `Y35`… |
| aucune subdivision | 10 | — (la catégorie est codable, type 2, fiche existante) | — | `V98`, `V99`, `X52`, `Y66`, `Y69`, `Y86`, `Y95`-`Y98` |

**Deux tables constantes sur tout le chapitre** (libellé canonique =
majoritaire ; les variantes du kit sont listées au rapport, jamais
corrigées) :

| lieu (10) | activité (7) |
|---|---|
| 0 domicile · 1 établissement collectif · 2 école et lieu public (2 variantes : « école, lieu public », « lieu public ») · 3 lieu de sport · 4 rue ou route · 5 zone de commerce · 6 local industriel et chantier · 7 exploitation agricole · 8 autres lieux précisés · 9 lieu sans précision (variante « sans précision ») | 0 en pratiquant un sport · 1 en participant à un jeu et à des activités de loisirs · 2 en exerçant un travail à des fins lucratives · 3 en exerçant d'autres formes de travail · 4 en se reposant, en dormant, en mangeant ou en participant à d'autres activités essentielles · 8 en participant à d'autres activités précisées · 9 en participant à une activité non précisée |

**Troncs à admettre par exception** : les **207** catégories 3-car des
patrons « lieu + activité », « lieu seul » et « lieu + activité +
précision » (toutes type 3) — chiffre de la dérivation, qui décide le
rôle par valeur et absorbe `X59` (hybride OMS/lieu en 4ᵉ) et `Y34`. Les troncs des patrons « OMS + … » sont
des codes 4-car déjà codables et déjà dans la génération (850 codes
`V01.0`, `W26.0`…) : ils reçoivent la section de composition, pas
d'exception. Les 52 + 10 catégories sans extension ne sont pas des
troncs.

## Architecture retenue

1. **Table dérivée déterministe du kit** (`build atih`) :
   `chapitre_xx_troncs.parquet` (un tronc par ligne : écriture maître,
   compacte, patron, positions, forme `+`, classe `tronc_composition` /
   `tronc_codable`, nombre de codes composés), `chapitre_xx_valeurs.parquet`
   (tables lieu, activité et précisions par tronc, avec libellés) et
   `chapitre_xx_codes.parquet` (les 25 348 codes composés décomposés :
   tronc, lieu, activité, précision, forme `+`). Rapport
   `reports/chapitre_xx_composition.csv` (effectifs par patron,
   variantes de libellé). Vérification à la construction : **chaque code
   du chapitre XX du kit est un tronc, un code OMS sans extension ou un
   code composé** — rien n'est avalé.
2. **Exception de profil** : `profils.generation.exceptions:
   [tronc_composition]` ; `build_cards_library` construit CSV ∪ codables
   ∪ troncs, la génération garde codables ∪ troncs déclarés. Colonne
   `classe_generation` (`emissible` / `tronc_composition`) dans les
   `_index.csv` des deux bibliothèques.
3. **Fiche de tronc** : marquage en première ligne sous le titre, avant
   le statut et tout contenu ; section « Composition MCO (kit ATIH
   2025) » après la position — positions, tables, forme `+`, nombre de
   codes composés. Les troncs codables (`V01.0`) reçoivent la section
   sans le marquage.
4. **I2 reformulé** (`couverture.verifie_generation`) : toute ligne de
   l'index de génération est soit codable, soit un tronc de classe
   `tronc_composition` inscrit dans la table — testé sur l'index réel
   et sur des index synthétiques (un `M07.20`, un faux tronc → violation).
   **I1 étendu** : chaque code composé du chapitre XX est couvert si son
   tronc a une fiche de génération.
5. **Résolveur** : `W0009` → statut `compose` (fiche du tronc + lieu 0
   « domicile » + activité 9 « … non précisée ») ; suffixe invalide →
   `composition_invalide` motivé (`W0005` : activité 5 hors table) ;
   `tronc_chapitre_xx` disparaît au profit de ces deux statuts.

## Chiffrage

| Volet | Code | Tests | Livrables |
|---|---|---|---|
| dérivation (`composition.py`, schémas, `build atih`) | ~250 lignes | 12 (kit synthétique, kit réel : 27 097 couverts, tables constantes) | +3 parquets, +1 rapport |
| profil, index, fiches (`policy.py`, `cards.py`, YAML) | ~120 | 8 | génération 15 071 → **15 278** fiches (+207 troncs), contrôle +207 |
| invariants (`couverture.verifie_generation`, I1 par composition) | ~60 | 6 (deux sens) | — |
| résolveur (`compose`, `composition_invalide`) | ~80 | 10 | statuts, docs DS |
| docs (source_mapping, CLAUDE.md, guide DS, README) | — | — | — |

Build : +2 s (`build atih`), +8 s de fiches. Aucune fiche existante ne
change hors des 1 080 troncs codables qui gagnent une section.

## Mesuré à la dérivation (2026-09-06, après implémentation)

- 1 057 troncs : 207 `tronc_composition` (catégories, type 3) + 850
  `tronc_codable` ; 25 308 codes composés ; **200 codes de type 3 en
  branches mortes** (`W261`…, `X342`… : ancien encodage « lieu en 4ᵉ »
  conservé dans le kit), ni troncs ni composés, comptés au rapport ;
- deux cas absorbés par la décision **par valeur** : `X59` (0 et 9 =
  sous-codes OMS codables, 1-8 = lieu → tronc partiel) et `X49` (6ᵉ =
  agent, table « précision » par tronc) ;
- variantes de libellé du kit reconnues, non corrigées : lieu 2 « école,
  lieu public » (2), « lieu public » (1).

