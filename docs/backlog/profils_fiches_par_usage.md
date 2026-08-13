# Backlog — Profils de fiches par usage

> Statut : **à instruire**. Ouvert le 2026-08-13, au chantier
> `chapter_policy`, en actant l'exclusion d'ORPHANET des Formulations.

## D'où vient la question

La politique de composition (`referentials/curation/chapter_policy.yaml`)
suppose aujourd'hui **un seul usage** des fiches : l'injection dans les prompts
de génération de CRH. Toutes ses décisions découlent de cette finalité —
refléter le langage des médecins, ne jamais élargir le périmètre du code.

Or l'arbitrage sur ORPHANET a montré qu'un autre usage existe. Admettre les
synonymes de maladies rares **biaiserait le corpus généré** vers des événements
à basse fréquence : c'est disqualifiant pour la génération. Mais pour un
**contrôle qualité** — vérifier qu'un CRH est bien codé, repérer ce que le
texte décrit vraiment — cette même information est précieuse : elle élargit le
rappel du vérificateur au lieu de biaiser un générateur.

Les deux usages veulent donc des fiches **différentes**, à partir des mêmes
données.

## Les deux profils pressentis

| | **Génération** (actuel) | **Contrôle qualité** (à construire) |
|---|---|---|
| Finalité | produire un CRH réaliste | juger si un CRH soutient un code |
| ORPHANET | exclu (biais de fréquence) | **admis** (rappel) |
| Exclusions | version courte, voire absente | **complètes** — c'est le cœur du contrôle |
| Formulations | plafonnées, registre CRH | plus larges, registre indifférent |
| Consignes | — | futures consignes du guide méthodologique |

Le profil « contrôle qualité » rejoint le schéma *generate-then-verify* décrit
dans [`2026-08-09_evaluation_fiches_et_contexte_llm.md`](../analyses/2026-08-09_evaluation_fiches_et_contexte_llm.md)
§5, où la fiche complète sert au **vérificateur** et non au générateur. Cette
note relève d'ailleurs que les exclusions injectées en amont *amorcent* ce
qu'elles interdisent — raison de plus pour ne pas les mettre dans le profil
génération et de les réserver au profil contrôle.

## Ce qu'il faudra trancher

1. **Où vit le profil ?** Un second fichier YAML, ou une clé `profils:` dans
   celui qui existe avec héritage d'un profil de base ? Attention : la
   résolution des plages est déjà **par remplacement, pas par fusion** ; y
   superposer un héritage de profils demande de dire lequel des deux
   mécanismes s'applique en premier, sous peine d'un piège de plus.
2. **Une bibliothèque par profil, ou une fiche à sections optionnelles ?**
   La première est plus simple à consommer, la seconde évite de doubler les
   18 000 fichiers.
3. **Le profil contrôle a-t-il besoin de R3 ?** La normalisation sert la
   lisibilité du générateur ; un vérificateur pourrait préférer la forme
   source, qui est la référence auditable.

## Ne rien implémenter avant

Le verrou `test_orphanet_reste_hors_des_formulations` doit rester en place :
il garantit que le profil génération ne s'élargit pas en silence. Le jour où
les profils existent, ce test devient « ORPHANET est dans le profil contrôle
et pas dans le profil génération ».
