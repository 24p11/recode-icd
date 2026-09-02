# Backlog — Diff de millésime du guide MCO (provisoire → définitif)

> Statut : **en attente d'un événement externe** — la parution de la
> version définitive du guide méthodologique MCO 2026. Ouvert le
> 2026-09-02, à la clôture du chantier A (base versée à 94 consignes,
> extraite de la version **provisoire** de décembre 2025).

## D'où vient la question

Toute la base de recommandations est ancrée sur
`guide_methodo_mco_2026_version_provisoire.pdf` : le millésime
`2026-provisoire` est porté par chaque consigne (champ structurel du
modèle, cf. note de conception §4.1). Le guide est annuel et la version
définitive peut modifier des articles extraits — la note de conception
(§7) prévoyait dès l'origine cette re-vérification.

## Ce qu'il faudra faire à parution de la version définitive

1. **Extraire les bruts de la définitive** (`pdftotext -layout`, même
   procédé, commande et version de poppler en tête) et **differ contre
   la provisoire**, article par article extrait (AVC, D62, dénutrition,
   chapitre XXI — plus tout article ajouté par le chantier B d'ici là).
2. **Réextraction ciblée des seuls articles modifiés.** Les curés figés
   de la provisoire **restent** — un curé atteste ce que *sa* version
   du guide dit, on ne le réancre pas (même principe que le pilote
   jamais réancré sur les curés). Un article modifié reçoit un
   **nouveau curé au millésime de la définitive**, avec son propre
   circuit brut → curé → validé → figé, et ses consignes portent le
   nouveau millésime.
3. **Vérifier les trois seuils sans comparateur du tableau §4.1** de
   l'article dénutrition (indice de surface musculaire en L3, indice de
   masse musculaire par impédancemétrie, masse musculaire
   appendiculaire au DEXA) : la provisoire ne porte pas la direction de
   comparaison, défaut signalé dans
   `data/guide_mco/hors_perimetre.md` (§ « §4.1 dénutrition — trois
   seuils sans direction de comparaison ») et reproduit tel quel dans
   `GM2026-V-DEN-17`. Si la définitive tranche, la consigne du nouveau
   millésime portera les comparateurs ; sinon, le défaut se signale à
   l'ATIH.

## Points de vigilance

- Le tableau du §4.1 est **incorporé en image** dans le PDF provisoire :
  le diff textuel ne le couvrira pas. Sa comparaison est **visuelle**,
  comme sa restitution l'était (pitfall « le brut est lossy »).
- Un article *non modifié* ne se réextrait pas : ses consignes gardent
  le millésime `2026-provisoire`, qui reste exact (c'est un instantané
  daté, pas une péremption).
- Les `rec_id` sont préfixés `GM2026-` sans distinction
  provisoire/définitif : à la première réextraction, décider si le
  préfixe des nouvelles consignes doit distinguer les millésimes ou si
  le champ `millesime` suffit.
