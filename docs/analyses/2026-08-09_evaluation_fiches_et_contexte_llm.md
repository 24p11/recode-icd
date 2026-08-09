# Apport des fiches dans les prompts de génération de CRH : lecture des résultats, littérature, protocole v2

*Note de travail — 2026-08-09. Destinée à `docs/analyses/` et à la discussion
avec l'équipe PARTAGES (data augmentation PARHAF).*

## 1. Résultat expérimental à expliquer

Évaluation manuelle par médecins DIM d'environ 20 CRH par bras (avec fiche /
sans fiche dans le prompt), génération via API Mistral (Mistral Large,
budget projet). Deux dimensions évaluées : qualité médicale du texte et
adéquation code↔texte. Résultat : pas d'apport mesurable des fiches, et une
qualité moyenne légèrement *supérieure* sans fiche, sur les deux dimensions.

Exemple caricatural : K57.4 « Diverticulose du côlon et de l'intestin grêle,
avec perforation et abcès » — aucun des deux prompts n'obtient un texte
précisant que l'atteinte touche à la fois le côlon ET l'intestin grêle. Le
« et » de la grammaire CIM-10 (= les deux localisations) n'est pas exploité.

## 2. Ce que dit la littérature

Quatre lignes de résultats rendent ce constat cohérent, et non anecdotique.

**a. Le contexte non nécessaire dégrade.** Shi et al., ICML 2023 (*Large
Language Models Can Be Easily Distracted by Irrelevant Context*) : de
l'information correcte mais non nécessaire à la tâche fait baisser la
performance. Mallen et al., ACL 2023 (*When Not to Trust Language Models*) :
le contexte externe aide sur les entités rares (connaissance paramétrique
lacunaire) mais peut dégrader sur les entités fréquentes, où le modèle
savait déjà. Implication : sur des codes fréquents, la fiche est du poids
mort ou de la distraction ; son bénéfice attendu se concentre sur la queue
de distribution (codes rares, subdivisions ATIH fines). Une moyenne sur un
échantillon dominé par des codes fréquents peut masquer ce bénéfice.

**b. Les exclusions amorcent ce qu'elles interdisent.** Kassner & Schütze,
ACL 2020 (*Negated and Misprimed Probes*) et littérature ultérieure sur la
négation : les LLM traitent mal les consignes négatives ; mentionner « ne
pas décrire X » augmente la probabilité d'évoquer X. Les fiches sont riches
en exclusions — injectées en amont, elles peuvent contaminer la génération
avec précisément les affections à écarter.

**c. Le milieu du contexte est mal exploité.** Liu et al., TACL 2024
(*Lost in the Middle*) : l'information placée au milieu d'un long prompt
est nettement moins utilisée qu'en début ou fin. La position d'insertion
des fiches dans le prompt n'est pas neutre.

**d. L'ICL est un mécanisme de copie.** Olsson et al., 2022 (*In-context
Learning and Induction Heads*, Anthropic) : le cœur de l'apprentissage en
contexte est un circuit de copie (têtes d'induction) qui repère des motifs
du contexte et les prolonge. Min et al., EMNLP 2022 (*Rethinking the Role
of Demonstrations*) : les démonstrations transmettent surtout le format et
la distribution de sortie, plus que le contenu. Implication directe pour la
data augmentation PARHAF : donner 10 CRH *proches du scénario cible*
maximise les conditions de déclenchement de la copie verbatim — le
phénomène observé (reproduction du texte exemple, incohérences induites)
est le comportement attendu du mécanisme, pas un accident.

## 3. Implications pour la data augmentation PARHAF

Le levier n'est pas de renoncer aux exemples mais de **décorréler style et
contenu** :

- donner des CRH stylistiquement représentatifs mais portant sur des
  pathologies *différentes* du scénario cible — la copie ne peut alors
  porter que sur le registre, la structure, les tournures ;
- variante plus contrôlée : étape préalable d'*extraction de style*
  (faire décrire explicitement par le modèle la structure des sections,
  la longueur des phrases, l'usage des abréviations, le degré de
  télégraphie des 10 CRH), puis générer avec cette description de style
  plutôt qu'avec les exemplaires bruts. Plus robuste, un peu moins fin.

## 4. Pistes pour les fiches (génération)

1. **Injection conditionnelle** : fiche complète réservée aux codes rares
   ou aux subdivisions fines ; fiche réduite (voire absente) sur les codes
   fréquents. Le critère de rareté peut venir des fréquences PMSI.
2. **Position** : si injection, placer la fiche en fin de prompt, au plus
   près de la consigne de génération.
3. **Grammaire CIM-10 dans les fiches** (chantier identifié) : expliciter
   les conventions de lecture des libellés — « et » = les deux
   localisations/formes (cas K57.4), « avec/sans », portée des
   parenthèses, sens des « autres » (.8) et « sans précision » (.9)
   déjà traité. Une courte section « lecture du libellé » par fiche, ou
   un préambule commun de grammaire, à arbitrer (le préambule commun est
   plus économe en tokens et évite la redite).
4. **Exclusions hors du prompt de génération** : compte tenu du point 2b,
   déplacer les exclusions vers l'étape de vérification (cf. §5) plutôt
   que de les injecter en amont.

## 5. Schéma generate-then-verify (à tester)

Clarification importante : il ne s'agit **pas** de demander au LLM de
« corriger le codage » — tâche sur laquelle le scepticisme est justifié et
partagé. Le schéma sépare trois rôles de difficulté très différente :

1. **Générer** : produire le CRH depuis le scénario, avec fiche réduite
   (formulations seules) ou sans fiche.
2. **Vérifier** (le rôle clé) : tâche de *lecture contrainte*, pas de
   codage — pour chaque code du scénario, muni de la fiche complète
   (périmètre, exclusions, grammaire du libellé), répondre à une
   check-list fermée : le texte soutient-il ce code ? chaque élément
   obligatoire du libellé est-il présent (les DEUX localisations pour
   K57.4) ? une exclusion de la fiche est-elle décrite ? une affection
   codable hors scénario apparaît-elle ? Sortie structurée : liste de
   violations localisées (citation du passage fautif ou mention
   manquante), sans réécriture.
3. **Réviser** : réécriture *ciblée* du CRH avec la seule liste de
   violations comme consigne (pas la fiche entière) — le modèle corrige
   des points désignés, il ne re-code pas.

Pourquoi c'est plus prometteur que « LLM correcteur » : la vérification est
un jugement fermé sur un texte court avec un référentiel explicite (la
fiche) — configuration où l'usage du contexte par les LLM est le plus
fiable — et la révision est bornée par la liste de violations, ce qui évite
la dérive de réécriture libre. Le point 2 produit en outre, gratuitement,
la **métrique de fidélité** du protocole v2 (taux de violations par CRH),
utilisable même si l'étape 3 est abandonnée.

Risques à surveiller lors du test : faux positifs du vérificateur sur les
formulations implicites (le texte dit la chose sans les mots de la fiche) ;
sur-correction en étape 3 (réécritures qui dégradent la fluidité) ; coût
(3 appels par CRH au lieu d'un).

## 6. Protocole d'évaluation v2 — recommandations

- **Puissance** : ~20 CRH/bras ne détecte qu'un effet massif. Viser un
  ordre de grandeur de plus par bras pour un effet modéré, quitte à
  automatiser une partie du jugement.
- **Stratifier par fréquence de code** (fréquent / rare / subdivision
  fine) : c'est la variable dont la littérature prédit qu'elle module
  l'effet des fiches. Analyser les bras *par strate*, pas en moyenne
  globale.
- **Métriques automatiques en complément du jugement humain** :
  fidélité scénario↔texte (le vérificateur du §5, étape 2) et diversité
  inter-CRH d'un même scénario (self-BLEU / distinct-n). Pour un corpus
  d'entraînement, fidélité et diversité priment sur le poli stylistique.
- **Conditions à comparer** (suggestion) : sans fiche / fiche complète /
  fiche formulations-seules / fiche conditionnelle (rares uniquement) /
  generate-then-verify. Les deux dernières sont les candidates issues de
  cette note.

## 7. Références

- Shi et al., 2023. *Large Language Models Can Be Easily Distracted by
  Irrelevant Context.* ICML 2023.
- Mallen et al., 2023. *When Not to Trust Language Models: Investigating
  Effectiveness of Parametric and Non-Parametric Memories.* ACL 2023.
- Kassner & Schütze, 2020. *Negated and Misprimed Probes for Pretrained
  Language Models.* ACL 2020.
- Liu et al., 2024. *Lost in the Middle: How Language Models Use Long
  Contexts.* TACL.
- Olsson et al., 2022. *In-context Learning and Induction Heads.*
  Transformer Circuits Thread, Anthropic.
- Min et al., 2022. *Rethinking the Role of Demonstrations: What Makes
  In-Context Learning Work?* EMNLP 2022.
