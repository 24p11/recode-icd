# Chantier B — rapport du lot 5 (2026-09-05)

Six articles relus et validés par RF (LES-01, MPR-01, OED-01,
PRE-01..12, RAM-01..05 OK ; ITG-01..09 OK sur le fond, avec
l'**arbitrage 12** sur la notation O04), versés, figés, mergés dans
`main`. Base après lot : **170 consignes, 397 associations curées →
18 489 couples résolus sur 15 045 codes** (après lot 4 : 141 / 339 /
18 090 / 15 009).

## Volumétrie par article

| Article | Consignes | Associations |
|---|---|---|
| INTERRUPTION DE LA GROSSESSE | 9 (ITG-01..09) | 21 (dont 1 `exemple`) |
| LÉSIONS TRAUMATIQUES | 1 (LES-01) | 0 |
| MALADIES PROFESSIONNELLES | 1 (MPR-01) | 1 |
| ŒDÈME PULMONAIRE | 1 (OED-01) | 3 |
| PRÉCARITÉ | 12 (PRE-01..12) | 22 |
| RÉSISTANCE AUX ANTIMICROBIENS | 5 (RAM-01..05) | 11 (dont 3 `exemple`) |
| **Total** | **29** | **58** |

## Arbitrage 12 (nouveau, consigné au registre)

**La curation est fidèle à la notation du guide, la résolution traduit
— jamais l'inverse.** Cinq expressions d'ITG (`O04.90`, `O04.4`,
`O04.-1`, `O04.-2`, `O04.-3`) n'étaient pas parsables : le référentiel
encode O04 avec ses 4e et 5e caractères inversés (`O04.-<5e>.<4e>`,
« O04.90 » du guide = feuille `O04.-0.9`). Décision RF, bornée :

- la table curée déclare les expressions **telles qu'écrites par le
  guide** (aucune ligne curée modifiée) ;
- extension du parseur + **table de correspondance déclarative**
  `referentials/curation/notations_guide.yaml`, lue par le nouveau
  module `recommendations/notations.py` et passée au parseur par le
  build (`--notations`) ; limitée aux catégories à encodage inversé
  (O04 seule aujourd'hui — 44 codes `X00.-…` dans le référentiel,
  tous sous O04) ;
- chaque entrée testée dans les deux sens (guide → référentiel →
  guide, et retour) : unitaires sur la table, régression exhaustive
  sur le vrai référentiel (`tests/regression/test_guide_mco_notations.py`),
  dorés sur les cinq expressions d'ITG ;
- toute forme hors table reste non parsable, au rapport (`O04.94`,
  `O04.123`, `O04.1-O04.3` lèvent) ; les traductions sont tracées dans
  le nouveau rapport `guide_mco_expressions_traduites.csv` ;
- invariant absolu testé sur la table curée entière : aucune expression
  ne porte la forme du référentiel `Xnn.-<5e>.<4e>`.

Granularités retenues sans créer de rang intermédiaire : `O04.90` →
`CODE` ; `O04.-1` (nœud de 5e position) et `O04.4` (une feuille par 5e
déclarée) → `CATEGORIE`.

## Correction de curé (relecture)

`interruption_grossesse.md` l. 76 : le second appel de la note 53,
collé « DP53 » dans l'original, n'était signalé que dans le message de
commit — il porte désormais son commentaire en marge (artefact
conservé, non réparé), comme le « 51 » égaré et le « 71 » de RAM.

## Consignes sans code résolu (10, toutes attendues)

ACC-02, AVC-18, ENF-01/03/04, POL-01, REB-01, et les nouvelles
**ITG-01** (définition IVG/IMG), **ITG-03** (RUM unique de l'IVG
médicamenteuse) et **LES-01** (« les fractures » n'est pas une
expression de codes). Non-résolue : OMS-01/`U00-U49` (arbitrage 9).
Non parsable : **aucune**.

## Associations `ensemble` : aucune dans ce lot. Divergences : aucune.

## Configurations de transcription notables

- ITG : 7 notes ancrées par déclaration ; « 51 » égaré retiré comme
  balisage (appel déclaré de l'article) ; règles 1°)/2°) ramenées de
  titres à paragraphes.
- PRÉCARITÉ borné jusqu'à sa note 65 (URL de la note 64 du voisin
  MALNUTRITION + début de RÉSISTANCE en suppressions) ; définitions
  scindées en un paragraphe par code Z.
- RÉSISTANCE borné jusqu'à sa note 67 (note 65 du voisin + début de
  SEPSIS en suppressions) ; « 71 » égaré conservé et commenté.

## Évolution des témoins de fiches

Aucun attendu modifié — **675 tests verts**. Bibliothèques feuilles
et catégories régénérées : **2 139 fiches avec consignes sur
16 058** (2 031 après lot 4). Parmi les nouvelles : les 40 feuilles de
O04, les 11 codes Z de précarité, U82-U84, Y96, I50.1/J60-J70/J81.

## Prochain article (lot 6, dernier)

SEPSIS ET CHOC SEPTIQUE (pp. 116-117, note 68 repérée), puis SÉQUELLES
DE MALADIES ET DE LÉSIONS TRAUMATIQUES (pp. 117-119), SUICIDES ET
TENTATIVES DE SUICIDE, TRAITEMENT DES GRANDS BRÛLÉS, TUMEURS À
ÉVOLUTION IMPRÉVISIBLE OU INCONNUE, VIOLENCE ROUTIÈRE.

**Blocage outillage sur ce poste** : `pdftotext` (poppler) n'est pas
installé, et Homebrew ne le fournit plus sur macOS Intel (support
abandonné, build depuis les sources exigeant les Command Line Tools
Xcode 26.3). Le brut de SEPSIS n'a donc pas pu être produit ici — cf.
récap de session pour les options.
