# Brief CC — chantier besoins codeur : verdicts et feu vert (archivé)

> Brief de RF reçu le 2026-10-18 (consigne n° 9), archivé tel quel en
> substance. Analyse validée (`2026-10-18_besoins_codeur_conception.md`),
> accord de push donné pour `81dc689`.

## Verdicts

1. **Z992 / prémisse corrigée actée** : deux régimes — correction
   obligatoire (non codable) et **affinage proposé, jamais imposé**
   (politique DIM déclarée côté `codeur`). Résolveur inchangé.
   « ni » : instruit côté `codeur`, rien ici.
2. **P1 `codes.csv` : OUI** — export des 42 897 codes du kit (code
   pointé ET `code_atih`, libellé, `codable_mco`, statut MCO, millésime
   kit, commit de livraison). Additif ; noyau d'`index.csv` intact,
   `format_version` = 1 ; section au CONTRAT.md.
3. **P2 : marquage, jamais d'absence** — colonnes informatives
   `has_definition`, `has_description_clinique`, `has_notes_cim` (en
   plus des existantes) ; `codeur` arbitre lui-même le coût en tokens.
   Une fiche reste toujours présente : l'index fait foi.
4. **P3 fiches de navigation : OUI, cœur du chantier** — 1 857 nœuds,
   liste compacte des codables (forme `code_atih` + libellé) précédée
   du critère discriminant **dérivé des modificateurs ClaML** (source
   déclarée, jamais inventé) ; sans axe officiel, la fiche le dit.
   Relecture RF par ÉCHANTILLONNAGE (un par famille de modificateurs +
   la liste exhaustive des singuliers).
5. **P4 : OUI** — découpage par axe modificateur des 44 catégories
   > 50 (témoins F01/F02, chapitre M). Filtrage par formulations =
   repli runtime côté `codeur`.
6. **P5 version prudente** : `extensions_preambule.md` généré du kit ;
   le critère par nœud vit dans les fiches de navigation.
7. **P6 profil revue : DIFFÉRÉ** (backlog avec déclencheur).
8. **P7 `formulations.csv` : OUI, coupe tranchée** — APRÈS R1/R3/
   registre archaïque, SANS plafond R2 (deux usages, deux coupes, même
   vivier). Colonnes : `code_atih`, formulation rendue, source,
   version de livraison.

## Implémentation — trois phases sur main, push sur accord par phase

- **Phase A (exports)** : `codes.csv`, colonnes `has_*`,
  `formulations.csv`, `extensions_preambule.md`,
  `preparer_livraison.py`, CONTRAT.md (+ `codeur` troisième
  consommateur). Témoins : E11 vs Z992 distingués, comptes exacts,
  jointure `code_atih` 100 %.
- **Phase B (navigation)** : 1 857 fiches de nœud, axes ClaML,
  découpage des 44 longues ; **STOP échantillon de relecture** →
  verdicts → versement. Témoins : M142, F01/F02, Z992, nœud sans axe.
- **Phase C (livraison groupée)** : archive post-chantier + note
  « nouveautés » cumulative pour les TROIS consommateurs ;
  `format_version` = 1 ; retrait du zip hors canal.

Règles inchangées : artefacts jamais à la main, déterminisme double
build, jamais au silence, prompt archivé, récap, rapport par phase.
