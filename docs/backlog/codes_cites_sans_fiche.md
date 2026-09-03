# Backlog — 23 codes cités par le guide sans fiche

> Statut : **à instruire**. Ouvert le 2026-09-03, au chantier du rendu
> des consignes dans les fiches (`feat/cards-recommandations`), en
> expliquant l'écart 995 fiches / 1 018 codes cités.

## Le constat

23 codes visés par des consignes résolues (`recommendation_codes.parquet`)
n'ont **aucune fiche** : ce sont des subdivisions ATIH du chapitre XXI,
feuilles du nested set ANS mais absentes du CSV maître —

`Z37.00`, `Z37.01`, `Z37.10`, `Z37.11`, `Z37.20`, `Z37.21`, `Z37.30`,
`Z37.31`, `Z37.40`, `Z37.41`, `Z37.50`, `Z37.51`, `Z37.60`, `Z37.61`,
`Z37.70`, `Z37.71`, `Z60.20`, `Z60.28`, `Z75.80`, `Z75.88`, `Z76.800`,
`Z76.850`, `Z76.880`.

Elles sont absentes du CSV parce qu'**aucune source ne leur attache la
moindre ligne** (ni note, ni synonyme, `has_ofs_match=False`) : un code
sans ligne n'existe pas dans le CSV, et `build_cards_library` itère sur
les codes du CSV. Les consignes qui les visent (descente du chapitre
XXI notamment) sont donc résolues mais jamais rendues.

## À instruire

1. **Pourquoi les sources les ignorent.** Vérifier s'il s'agit d'un
   trou de couverture (libellé ANS existant mais non repris comme
   synonyme dans l'export) ou d'un choix structurel du pipeline (un
   code sans information textuelle n'a pas de ligne). Rapprocher du
   backlog `inclure_codes_intermediaires.md` — la question de « quels
   codes ont droit à une existence dans les livrables » est commune.
2. **Comportement voulu le jour où un consommateur les demande.** Une
   fiche peut être construite depuis le seul libellé ANS (le fallback
   `_section_*_from_ans` existe déjà pour les post-2006 type U07.1) ;
   faut-il alors élargir la liste des codes construits au-delà du CSV,
   et avec quel contenu minimal (titre + position + consignes) ? À
   trancher explicitement — aujourd'hui l'absence est silencieuse côté
   fiches, seule la différence 995/1 018 la révèle.

Chiffres et contexte : `docs/sessions/2026-09-03_rendu_consignes_fiches.md`.
