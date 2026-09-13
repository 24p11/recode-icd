# Message CC — verdict RF sur le v3, feu vert phase 2 (archivé)

> Message de RF reçu le 2026-09-14, archivé tel quel (consigne
> d'archivage des prompts de chantier). Récap d'exécution :
> `2026-09-14_chantier_notes_cim_phase2.md`.

---

Ma passe sur relecture_notes_union_v3.xlsx est terminée. Le classeur
annoté fait foi — 1 003 lignes, mes verdicts dans destination_proposee
(aucune modification de classe_proposee). Répartition finale : 374
non_rendue, 256 descriptions cliniques, 224 notes CIM-10, 101 fiches
de bloc avec héritage borné, 48 définitions.

Précisions : (1) patron utiliser_code_supplementaire écarté
intégralement (221/221), délibéré — jurisprudence boilerplate ; les
écartées restent dans la base, récupérables pour un profil
vérificateur. (2) Les notes de chapitre marquées non_rendue : lecture
« pas de descente » — la note reste sur la fiche du CHAPITRE
(bibliothèque des catégories) ; niveau chapitre → jamais de descente.

Jurisprudences à graver : boilerplate (permission pure non rendue,
substantiel rendu, partage par patron quand homogène) ; niveau
chapitre (jamais de descente ; les notes de bloc héritent quand le
verdict le dit — 101 lignes).

Verdicts notables : D00-D09/D37-D48 description_clinique texte ANS,
héritage TRANCHÉ à oui (D06/NIC n'est plus à instruire) ; abandonnées :
9 gardées en définitions (B48.7, E00, E40, K01.0, K01.1, O03-O06),
A09 gardée en note CIM-10, 28 écartées (dont A15.1-3/A16.1 et la série
S12…T14.2) ; F78/F79 écartées ; blocs C81-C96, V01-V99, O95-O99
écartés.

Phase 2 : extension des DEUX loaders (ClaML nouveau fichier source ;
OFS join réparé + GLOSSAIRE + 5 orphelines), fusion texte ANS
prioritaire ; CSV maître type note + classe_note, source tracée,
non-rendues comprises ; rendu par destination (Description clinique
entre Périmètre et consignes ; définitions sur la fiche du code ;
Notes de la CIM-10 distincte des consignes du guide ; fiches de
bloc/chapitre en bibliothèque catégories, héritage borné bloc →
feuilles, jamais depuis un chapitre) ; tests témoins (E43, F3x,
I20-I25 → I21.x, chapitre sans descente, boilerplate, déterminisme,
hors périmètre byte-identiques) ; doc (jurisprudences, trois usages) ;
rebuild SOUS CONTRAT avec vérification de conformité au CONTRAT.md.

Merge sur accord explicite en fin de phase 2, rapport de chantier à la
soumission.
