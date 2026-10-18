# Message CC — recadrage de la phase B du chantier codeur (archivé)

> Message de RF reçu le 2026-10-18, archivé tel quel en substance.

La « fiche de navigation » n'est pas retenue : codeur n'utilise que les
fiches d'identité des codes codables (les colonnes has_* de la phase A
couvrent le besoin de fiches courtes) ; pour la boucle de correction il
a seulement besoin, pour un nœud non codable, de la liste de ses
descendants codables avec libellés.

Phase B = export descendants_codables.csv : une ligne par couple (nœud,
descendant codable) — noeud_atih, noeud_libelle, code_atih, libelle,
ordre de tri du kit. Périmètre : les nœuds non codables du kit à
descendant codable. Calculé par la même logique que le résolveur (pas
de seconde implémentation), invariant testé export == resoudre.
Embarqué par preparer_livraison.py, documenté CONTRAT.md + guide,
format_version = 1. Témoins : Z992, E11, M142, R521, un nœud à notation
divergente, F01/F02 exact (126).

Annulés : les 1 857 fiches de navigation, la question d'emplacement, le
découpage des 44 longues, l'échantillon de relecture — artefact calculé
pur, livrable sur rapport avec témoins, sans STOP. Au backlog avec
déclencheur : l'axe discriminant ClaML si les listes longues noient le
LLM. Phase C inchangée. Rapport de phase B puis push sur accord.
