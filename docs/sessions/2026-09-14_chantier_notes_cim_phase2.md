# Chantier notes OFS/ANS — phase 2 : les notes dans la base et les fiches (2026-09-14)

**Sur `main`** (travail direct, régime deux-postes). **Statut : livré,
rapport soumis à RF** — sa passe sur ce rapport vaut l'accord explicite
de fin de phase 2 (plus de branche à merger). Messages archivés :
`2026-09-14_message_correctif_notes_v3.md` (v3),
`2026-09-14_message_verdict_v3_phase2.md` (verdict + feu vert).
Volumétrie : `docs/analyses/2026-09-14_notes_cim_volumetrie.md`.

## Le circuit

`relecture_notes_union_v3.xlsx` (verdict RF ligne à ligne, classeur
committé, fait foi) → `referentials/curation/notes_cim_curated.csv`
(1 003 notes ; les 18 lignes de chapitre non_rendue relues « fiche de
chapitre, sans descente » — précision RF, le message en comptait 14) →
`build notes-cim` (réancrage sur MEMO et ClaML, 0 manquante,
`reports/notes_cim_ancrage.csv`) → `notes_cim.parquet` → `build
flat-csv` (lignes `type=note`) → fiches.

## Livrables

| Volet | Livrable |
|---|---|
| Loader ANS | `loaders/claml_notes.py` — le ClaML devient une source du pipeline (955 rubriques, References restituées, modificateurs déployés sur leurs cibles via ModifiedBy) |
| Loader OFS | join MEMO **réparé** (NOTE.txt perdait GLOSSAIRE entier + 5 orphelines : 352/614) ; `load_ofs_notes` public ; `notes_editorial` de `ofs_codes` complété |
| Assemblage | `notes_cim.py` — la table curée fait foi, fusion « texte ANS prioritaire, OFS complément » (955/48), chapitres normalisés en romain, erreurs bruyantes sur classe/destination inconnues |
| CSV maître | **12 colonnes** (+`classe_note`, `note_destination`, `note_provenance`) ; 21 132 lignes note : 1 083 au code d'attache (156 non-rendues tracées — la base sait tout), 12 996 héritées de blocs, 7 053 déployées (modificateurs, catégories) ; **aucune** héritée d'un chapitre |
| Fiches feuilles | sections « Définition (CIM-10) » et « Description clinique (OMS) » entre Périmètre et consignes ; « Notes de la CIM-10 » après les consignes du guide (jamais fondues) ; provenance « *(note du bloc X)* » sur les héritées |
| Bibliothèque catégories | notes des catégories (pères interdits compris, via parquet) ; **fiches nouvelles de bloc (`<fiche_node>`) et de chapitre** — D00-D09/D37-D48 en description clinique (héritage tranché oui), 10 chapitres |
| Tests | +8 témoins (`test_notes_cim_witnesses.py`) : E43 définition, F20.0 description, I21.08 hérité de I20-I25, chapitre X sans descente (contre-témoin CSV verrouillé), boilerplate en base hors fiches, déterminisme, fiche sans note, parquet ancré. Schémas des tests CSV migrés 9 → 12 colonnes. **883 verts, 0 skippé** |
| Doc | CLAUDE.md : famille notes, jurisprudences boilerplate et chapitre, cadrage « trois usages », CSV 12 colonnes |

## Rebuild sous contrat (premier depuis CONTRAT.md)

Les trois bibliothèques régénérées : `index.csv` canonique +
`_index.csv` déprécié double-écrits, CONTRAT.md posé, répertoires
nettoyés par le build. **Conformité CONTRAT.md** : le noyau garanti
(`code, fichier, statut_mco, format_version`) est inchangé —
`format_version` reste 1. **Évolution informative à signaler aux
consommateurs (fictomed, Stream) à la prochaine livraison** : l'index
de la bibliothèque des catégories gagne des LIGNES nouvelles (fiches
de bloc « I20-I25 » et de chapitre « X » — codes non-catégorie), et
les fiches feuilles gagnent trois sections. Aucun champ ne change.

## Jurisprudences gravées (CLAUDE.md)

1. **Boilerplate** : la permission pure OMS ne se rend pas (221
   écartées, en base, récupérables pour un profil vérificateur) ;
   l'instruction substantielle se rend (224). Partage par patron quand
   homogène, ligne à ligne sinon.
2. **Niveau chapitre** : jamais de descente ; fiche de chapitre en
   bibliothèque catégories. Bloc : héritage borné quand le verdict le
   dit (101).

## Suites (non engagées)

- Équivalences terminologiques → vivier Formulations (chantier
  synonymes LLM, avec `fiches_a_completer.csv`).
- Profil « vérificateur » : les non-rendues sont en base, prêtes.
- Prochaine livraison data scientists : embarquera notes + contrat
  (signalement de l'évolution d'index aux consommateurs).
