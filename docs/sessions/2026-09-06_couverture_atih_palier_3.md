# Chantier couverture ATIH — palier 3 : chapitre XX par composition (2026-09-06)

**Branche** `feat/couverture-atih` · **Décision RF** : option « tronc
explicite » (rapport d'ouverture :
`docs/analyses/2026-09-06_couverture_atih_d5_ouverture.md`). **Statut** :
livré, en attente de l'accord de merge du palier.

## Ce qui est en place

| Volet | Livrable |
|---|---|
| Dérivation déterministe | `recode_icd/composition.py` ; `build atih` écrit `chapitre_xx_troncs.parquet` (1 021 troncs : 211 catégories `tronc_composition`, 810 codes OMS `tronc_codable`), `chapitre_xx_valeurs.parquet` (lieu 10, activité 7, précisions `X49`), `chapitre_xx_codes.parquet` (25 348 codes composés décomposés) et `reports/chapitre_xx_composition.csv` |
| Profil | `profils.generation.exceptions: [tronc_composition]` — la seule classe non codable admise (`policy.EXCEPTIONS_ADMISES`) |
| Fiches | marquage « Tronc de composition (chapitre XX) — non codable seul : se compose du lieu (4ᵉ caractère) et de l'activité (5ᵉ caractère) » en **première ligne** sous le titre ; section « Composition MCO (kit ATIH 2025) » sur les 1 021 troncs ; colonne `classe_generation` des index |
| Invariants | I2 reformulé sans affaiblissement (`couverture.verifie_generation`, testé dans les deux sens : `W00` passe, `M07.20` et un faux tronc échouent) ; I1 étendu — tout code composé a un tronc avec fiche de génération |
| Résolveur | `compose` (positif : fiche du tronc + lieu / activité / précision libellés) et `composition_invalide` (rejet motivé : position fautive et valeurs admises) ; `tronc_chapitre_xx` disparaît |

Bibliothèques : `generation` **15 282** fiches = 15 071 émissibles + 211
troncs ; `controle` 16 988. Le résolveur : `W0009` → tronc `W00` + lieu 0
« domicile » + activité 9 ; `W0005` → « activité 5 hors table sous W00
(valeurs admises : 0, 1, 2, 3, 4, 8, 9) » ; `W260+4` → forme `+` sans
lieu ; `X49001` → lieu, activité et précision « exposition au ciment ».

## Ce que la dérivation a appris du kit

- Le rôle d'une position se décide **par valeur**, d'après le libellé,
  pas par position : `X59` mêle en 4ᵉ des sous-codes OMS codables (0 et 9)
  et le lieu (1-8) — tronc partiel ; `X49` ajoute une 6ᵉ position
  « agent » (acide fluorhydrique, ciment).
- **L'invariant a servi avant le merge** : la première dérivation
  (1 057 troncs, 25 308 composés) prenait `W200`, `W220`, `W240`, `X380`…
  pour des sous-codes OMS, parce que le kit réécrit le libellé du parent
  dans ses enfants (« (d'un)(d') objet(s) » → « d'un objet », « Victime
  d'inondation » → « Inondation ») et que la détection ne lisait que le
  préfixe. I1 par composition a rendu 40 codes de lieu sans fiche ; la
  détection lit désormais aussi les queues à la virgule, toujours par
  valeur (`composition._candidats`, testé sur mini-kit). Résultat : 1 021
  troncs, 25 348 composés — le compte exact de la phase 1.
- **200 codes de type 3 sont des branches mortes** (`W261`…`W269`,
  `X342`…`X347` et leurs enfants) : un ancien encodage « lieu en 4ᵉ »
  conservé dans le kit, tout en type 3. Ni troncs ni composés ; comptés
  au rapport, jamais réparés.
- Deux variantes de libellé pour le lieu 2 (« école, lieu public »,
  « lieu public ») : reconnues comme le lieu 2, rapportées, non
  corrigées.
- Les 810 troncs codables (`V01.0`, `W26.0`) étaient déjà dans la
  génération : ils gagnent la section, pas le marquage.

## Couverture finale

Hors chapitre XX : 15 071 / 15 071 codes autorisés avec fiche (I1).
Chapitre XX : 25 348 codes composés couverts par 1 021 troncs avec fiche
(I1 par composition). Ce qui reste hors fiche est ce qui doit l'être :
200 branches mortes de type 3, 1 619 codes du maître inconnus du kit,
79 supprimés, les pères interdits — tous dans `controle`, tous
explicables par le résolveur.

## Tests

{TESTS} verts. Ajoutés au palier : dérivation sur mini-kit synthétique
(rôles par valeur, variante de libellé, branche morte, hybride, forme
`+`, précision, erreur bruyante sur un codable non couvert, déterminisme),
profil et exception, fiche de tronc (marquage en première ligne, section),
résolveur (compose / invalide, synthétique et réel), invariants dans les
deux sens, régression sur le kit réel.

## Dette et suites

- `reports/curation_applied.csv` dupliqué à chaque `build flat-csv`
  (backlog existant).
- Taille du CSV maître (55,9 Mo) : revue d'architecture — formalisation
  des deux couches.
- Section « Subdivisions codables » des fiches (D2-P) : backlog vérificateur.
- Prochain chantier après merge : revue d'architecture.
