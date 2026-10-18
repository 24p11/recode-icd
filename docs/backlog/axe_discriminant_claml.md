# Backlog — axe discriminant des listes de correction (modificateurs ClaML)

> Statut : **différé avec déclencheur** (recadrage RF du 2026-10-18,
> chantier codeur). Les fiches de navigation, le découpage des 44
> catégories longues et l'échantillon de relecture sont ANNULÉS : la
> phase B livre `descendants_codables.csv`, artefact calculé pur.

**Déclencheur** : si les retours de la boucle de correction de `codeur`
montrent que les listes longues noient le LLM (F01/F02 : 126 lignes ;
44 catégories > 50 ; p99 = 77), ajouter l'axe discriminant — colonne de
la relation ou découpage par axe — dérivé des **modificateurs ClaML**
(source déclarée, jamais inventé : « le 5ᵉ caractère précise… »,
chargés par `loaders/claml_notes.py` depuis le chantier notes).

**La base le jour venu** : mesures dans
`docs/analyses/2026-10-18_besoins_codeur_conception.md` (§ 3-4 : les
longues tombent là où les modificateurs portent l'axe officiel) et
`scripts/explore/mesure_besoins_codeur.py`.
