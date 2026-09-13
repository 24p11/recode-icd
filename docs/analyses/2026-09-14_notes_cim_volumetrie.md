# Notes de la CIM-10 — volumétrie finale (2026-09-14)

Chantier « notes OFS/ANS », phase 2. Verdict RF ligne à ligne du
2026-09-14 sur le tri v3 (1 003 notes de l'union OFS 2006 ⊕ ClaML ANS
2025), versé dans `referentials/curation/notes_cim_curated.csv` — la
source de vérité du build (`build notes-cim`).

## Le verdict (1 003 notes)

| Destination | n |
|---|---|
| non_rendue | 356 |
| section Description clinique (OMS) | 256 |
| section Notes de la CIM-10 | 224 |
| fiche de bloc + héritage borné vers les feuilles | 101 |
| fiche du code (définition) | 48 |
| fiche de chapitre, sans descente | 18 |

Les 18 « fiche de chapitre » appliquent la précision RF à toute ligne
de niveau chapitre marquée non_rendue (le message en comptait 14 — la
règle « toute ligne de niveau chapitre » fait foi avec le classeur).
Le patron boilerplate « utiliser, au besoin, un code supplémentaire »
est écarté intégralement (jurisprudence) ; les 224 instructions
substantielles gardées montrent le partage — on juge la valeur, pas
l'étiquette.

## Ce que la base et les fiches en font

- **`notes_cim.parquet`** : les 1 003, non-rendues comprises,
  réancrées sur MEMO et ClaML à chaque build (0 manquante au premier
  build ; rapport `notes_cim_ancrage.csv`).
- **CSV maître** (12 colonnes désormais) : **21 132 lignes `type=note`**
  — 1 083 au code d'attache (dont 156 non-rendues tracées), 12 996
  héritées d'un bloc (`source_level=block`), 7 053 déployées depuis les
  modificateurs ClaML et catégories (`source_level=category`). Aucune
  ligne héritée d'un chapitre (verrouillé par témoin).
- **Fiches feuilles** : sections « Définition (CIM-10) »,
  « Description clinique (OMS) » (entre Périmètre et consignes),
  « Notes de la CIM-10 » (après les consignes du guide). Témoins :
  E43, F20.0, I21.08 (hérité de I20-I25).
- **Bibliothèque des catégories** : les fiches catégories portent
  leurs notes (F20, A15 — pères interdits inclus, via le parquet) ;
  **fiches nouvelles de bloc** (~40, dont D00-D09/D37-D48 en
  description clinique — héritage tranché à oui) **et de chapitre**
  (10 chapitres, 18 notes, jamais de descente).

## Sources après réparation des loaders

- OFS : le join historique via NOTE.txt perdait 352 des 614 mémos
  (GLOSSAIRE entier + 5 orphelines A15.x/A16.1/E00) — réparé
  (`load_ofs_notes`, et `notes_editorial` de `ofs_codes` complété).
- ANS : le ClaML devient une source du pipeline (`loaders/claml_notes`),
  955 rubriques dont 78 factorisées sous Modifier/ModifierClass,
  References restituées avec leurs espaces.
- Fusion : texte ANS prioritaire (955 lignes), OFS complément (48) —
  miroir de la politique d'existence.

## Suites notées (sans les engager)

- Équivalences terminologiques (dermite = eczéma, ostéo-arthrite =
  arthrose) : candidates au vivier des Formulations — chantier
  synonymes LLM.
- Les 221 boilerplates et autres non-rendues restent récupérables pour
  un futur profil « vérificateur ».
