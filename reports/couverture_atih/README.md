# Couverture ATIH des fiches CIM-10 — ce qui manque, et pourquoi

*Note pour les data scientists — 2026-09-05. Mesure de la phase 1 du
chantier « couverture ATIH » ; les fiches manquantes viendront en phase 2.*

## En une phrase

**Sur les 40 419 codes autorisés en MCO par le kit ATIH 2025, 14 140 ont
une fiche aujourd'hui.** Hors chapitre XX (causes externes), la couverture
est de **93,8 %** (14 140 / 15 071) ; les 931 manquants ont chacun une
cause identifiée, listée ci-dessous. Le chapitre XX pèse à lui seul
25 348 codes absents — c'est une sous-nomenclature lieu × activité que
les fiches ne couvrent pas encore.

## Avant tout : le résolveur

Depuis D0, ne joignez plus vos codes « à la main » sur les fichiers
ci-dessous : `recode-icd resoudre CODE…` (ou
`recode_icd.couverture.resoudre_code`) accepte toute écriture et répond
la fiche ou la raison motivée de son absence, avec un repli (feuilles,
tronc, ancêtre). Avec `--journal fichier.jsonl`, les réponses négatives
sont consignées : c'est la mesure d'usage qui priorise la suite —
envoyez-nous ce fichier. Détail dans `docs/csv_usage_guide.md`.

## Le fichier à ouvrir en premier

**`a_atih_autorises_sans_fiche.csv`** — un enregistrement par code
autorisé MCO (Type MCO ≠ 3) **sans fiche** : 26 368 lignes.

| Colonne | Contenu |
|---|---|
| `code_atih` | code compact ATIH, tel qu'il apparaît dans un RUM (`M0000`, `O0490`, `B24+0`) |
| `type_mco` | 0 pas de restriction · 1 interdit en DP/DR · 2 interdit en DP/DR (cause externe) · 4 interdit en DP |
| `libelle_long` | libellé officiel du kit |
| `classe` | **la cause de l'absence** (voir ci-dessous) |
| `sous_classe` | précision (famille de notation, état des descendants, chapitre XX) |
| `code_maitre` | l'écriture du même code dans nos livrables quand elle existe (`O04.-0.9` pour `O0490`) |
| `ancetre_maitre` | pour un code absent, l'ancêtre le plus proche qui a une fiche |

Les classes, par ordre d'importance pour vous :

| `classe` | n | Ce que ça veut dire | Quoi faire en attendant |
|---|---|---|---|
| `réellement absent` / `extension chapitre XX (lieu/activité)` | 25 348 | code ATIH `W0004` = W00 + lieu `0` + activité `4` ; nos livrables s'arrêtent au tronc OMS (`W00`, `V01.0`) | utiliser la fiche du tronc (`ancetre_maitre`) ; lieu (4e/5e car.) et activité (5e/6e) sont deux tables de 10 et 7 valeurs, constantes sur tout le chapitre |
| `niveau intermédiaire autorisé` | 800 | le code est codable **et** subdivisé chez nous (`M00.0` codable, fiches seulement sur `M00.00`…`M00.09`) ; pour 110 d'entre eux l'ATIH ne connaît pas nos subdivisions (`M16.0`) | prendre la fiche d'une subdivision, ou l'union de leurs fiches ; pour les 110, la subdivision est un raffinement OMS non codable en MCO |
| `notation divergente` | 89 | la fiche existe sous une autre écriture (`O0490` → `O04.-0.9`, `M62810` → `M62.8-01`, `B24+0` → `B24.+0`) | utiliser `code_maitre` — **`notations_divergentes.csv` donne la table complète** |
| `réellement absent` (hors chapitre XX) | 72 | extensions ATIH récentes absentes de la classification ANS : `I70.00/01` (athérosclérose ± gangrène), `J96.1xx`, `M45+x`, localisations `M11.9x`, `M13.9x`, `M83.xx`, `M62.8x` | fiche de l'ancêtre (`ancetre_maitre`) + libellé ATIH |
| `feuille du nested set sans ligne au maître` | 59 | le code existe chez nous mais **aucune source** ne lui attache de texte : `Z37.10…71`, `U07.2…9`, `U08.9`, `U09.9`, `U12.9`, résistances `U82/U83+x`, `Y90.x`, `Y97`, `Y98` | libellé seul ; pas de contenu clinique disponible avant la phase 2 |

## L'autre sens : des fiches à ne pas utiliser en MCO

`b_maitre_inconnu_atih.csv` et la colonne `sous_classe` de
`b_maitre_vs_atih.csv` (16 058 fiches) signalent :

- **299 fiches sur des codes interdits en MCO** (type 3) : 209 catégories
  à 3 caractères du chapitre XX (`W00`, `X06`… — en MCO on code
  obligatoirement le lieu), 79 codes **supprimés** du kit (`*** SUxx ***`,
  ex. `M07.20`), quelques pères interdits (`C79.9`, `C80.9`, `J98.7`,
  `I70.0/8/9`). **Ne jamais tirer ces codes pour générer un RUM.**
- **1 618 fiches sur des codes inconnus de l'ATIH** : les localisations à
  5e caractère du chapitre XIII (`M16.0x`, `M92.xx`…) que le kit ne liste
  pas pour ces catégories ; le code MCO réel est le niveau au-dessus
  (`M16.0`). Cliniquement valides, pas codables tels quels.
- `N06.9` : absent du kit (seul cas).

## Les autres fichiers

| Fichier | Contenu |
|---|---|
| `a_atih_autorises.csv` | les 40 419 codes autorisés, avec ou sans fiche (colonnes identiques) |
| `b_maitre_vs_atih.csv` | les 16 058 fiches et leur statut ATIH (type MCO, notation, préfixe) |
| `notations_divergentes.csv` | les 89 correspondances ATIH ↔ maître qui ne sont pas « point après le 3e caractère » |
| `noeuds_intermediaires_maitre.csv` | les 2 654 nœuds non feuilles de notre nested set et leur statut ATIH (800 autorisés, 1 846 pères interdits, 8 regroupements sans équivalent) |

## Règle de correspondance des codes

ATIH écrit le code **compact** (`A000`, `M0000`, `C169+0`) ; nos livrables
insèrent un point après le 3e caractère (`A00.0`, `M00.00`, `C16.9+0`),
**sans point quand le 4e caractère est `+`** (`T08+0`, `F03+00`). Trois
familles s'en écartent et sont dans `notations_divergentes.csv` : O04
(`O04ab` ↔ `O04.-b.a`), M62.8 (`M628ab` ↔ `M62.8-ba`) et neuf catégories
à `+` ponctué (`B24+0` ↔ `B24.+0`). Ne pas réimplémenter cette règle à la
main : prendre la table.

## Source et régénération

Kit : `data/CIM_ATIH_2025/LIBCIM10MULTI.TXT` (format et sémantique dans
`cim.pdf`). Mesure : `scripts/explore/2026-09-05_couverture_atih.py`
(lecture seule, régénère ce dossier). Rapport complet et méthode :
`docs/analyses/2026-09-05_couverture_atih_phase1.md`.
