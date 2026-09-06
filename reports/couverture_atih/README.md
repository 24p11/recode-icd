# Couverture ATIH des fiches CIM-10 — ce qui manque, et pourquoi

*Note pour les data scientists — 2026-09-05, mise à jour en fin de
palier 2 du chantier « couverture ATIH » (D2, D3, D4 livrés).*

## En une phrase

**Sur les 40 419 codes autorisés en MCO par le kit ATIH 2025, 15 071 —
tous ceux hors chapitre XX — ont une fiche dans la bibliothèque de
génération (`outputs/cards_library`, 100 %).** Les 89 codes « notation
divergente » de la mesure ci-dessous ont aussi leur fiche, sous
l'écriture du maître (`O0490` → `O04.-0.9`) : le résolveur la trouve.
Restent les 25 348 codes du chapitre XX (sous-nomenclature lieu ×
activité, jamais DP/DR) : ils se couvriront par composition à partir
de la fiche du tronc (palier 3, D5) — le résolveur répond déjà
`tronc_chapitre_xx` avec le tronc.

État du 2026-09-05 au matin, pour mémoire : 14 140 fiches (93,8 %
hors chapitre XX), 931 manquants en quatre classes — toutes traitées
depuis (800 intermédiaires codables, 59 feuilles sans ligne, 72
extensions ATIH absentes, 89 notations divergentes).

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
autorisé MCO (Type MCO ≠ 3) **sans fiche sous son écriture ATIH** :
25 437 lignes — 25 348 du chapitre XX et les 89 notations divergentes
(qui ont une fiche sous l'écriture du maître, colonne `code_maitre`).

| Colonne | Contenu |
|---|---|
| `code_atih` | code compact ATIH, tel qu'il apparaît dans un RUM (`M0000`, `O0490`, `B24+0`) |
| `type_mco` | 0 pas de restriction · 1 interdit en DP/DR · 2 interdit en DP/DR (cause externe) · 4 interdit en DP |
| `libelle_long` | libellé officiel du kit |
| `classe` | **la cause de l'absence** (voir ci-dessous) |
| `sous_classe` | précision (famille de notation, état des descendants, chapitre XX) |
| `code_maitre` | l'écriture du même code dans nos livrables quand elle existe (`O04.-0.9` pour `O0490`) |
| `ancetre_maitre` | pour un code absent, l'ancêtre le plus proche qui a une fiche |

Les classes encore présentes, et ce qu'il en reste :

| `classe` | n | Ce que ça veut dire | Quoi faire |
|---|---|---|---|
| `réellement absent` / `extension chapitre XX (lieu/activité)` | 25 348 | code ATIH `W0004` = W00 + lieu `0` + activité `4` ; nos livrables s'arrêtent au tronc OMS (`W00`, `V01.0`) | utiliser la fiche du tronc (`ancetre_maitre`, ou le résolveur : `tronc_chapitre_xx`) ; lieu (4e/5e car.) et activité (5e/6e) sont deux tables de 10 et 7 valeurs, constantes sur tout le chapitre — la composition sera outillée en D5 |
| `notation divergente` | 89 | la fiche existe sous une autre écriture (`O0490` → `O04.-0.9`, `M62810` → `M62.8-01`, `B24+0` → `B24.+0`) | utiliser `code_maitre` ou le résolveur — **`notations_divergentes.csv` donne la table complète** |

Classes **soldées** au palier 2 (elles n'apparaissent plus dans le
fichier) : `niveau intermédiaire autorisé` (800 — `M00.0`, `F00.0`,
`M16.0`… ont désormais une fiche par héritage, D2), `feuille du nested
set sans ligne` (59 — `Z37.10…71`, `U07.2…9`, résistances `U82/U83+x`,
`Y90.x`… ont une fiche, D3), `réellement absent` hors chapitre XX (72 —
`I70.00/01`, `J96.1xx`, `M45+x`, localisations `M11.9x`… injectés dans
le référentiel depuis le kit, D3 ; `source_existence=ATIH` dans
l'index).

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
