# Candidates — ANÉMIE POSTHÉMORRAGIQUE AIGÜE APRÈS UNE INTERVENTION (compléments)

> **Statut : à valider ligne à ligne. Rien ici n'est dans les tables curées.**
>
> Source : `data/guide_mco/extraits/anemie_posthemorragique_d62.txt`
> (chap. V, pp. imprimées 81-82).

Le §5.2 de la note a fourni D62-01 (`interdiction`) et D62-02
(`condition_emploi`), toutes deux versées avec leur association.
**Relecture faite du texte source, les deux consignes couvrent
fidèlement l'article** — je ne propose aucune correction.

Une seule candidate nouvelle.

---

### GM2026-V-D62-03 — `definition`
**Situation** : Anémie postopératoire — seuils biologiques de la discussion
**Texte** : La question de l'emploi de D62 se pose devant un hémogramme postopératoire prouvant une chute de l'hémoglobine en deçà de 13 g/dL chez l'homme, 12 g/dL chez la femme (11 g/dL chez la femme enceinte), chez un adulte jusqu'alors non anémié.
**Condition** : Adulte jusqu'alors non anémié
**Citation** (L54-58) : « L'emploi du code D62 Anémie posthémorragique aigüe pour mentionner la constatation d'une anémie postopératoire se discute devant un résultat d'hémogramme postopératoire prouvant la chute de l'hémoglobine en deçà de 13 grammes par décilitre chez l'homme, 12 grammes par décilitre chez la femme (11 grammes par décilitre chez la femme enceinte), chez un adulte jusqu'alors non anémié. »

| code_expr | role | centralite | condition |
|---|---|---|---|
| `D62` | `contexte` | `sujet` | |

> **Pourquoi je la propose.** Elle ne prescrit aucune position — c'est
> une `definition`. Son intérêt est pour la **génération** : elle dit au
> générateur ce qu'un CRH mentionnant D62 doit contenir comme valeur
> d'hémoglobine. Sans elle, la fiche D62 enseigne quand *ne pas* coder
> mais jamais à quoi ressemble le cas où l'on code.
>
> **Contre-argument, à votre arbitrage** : le seuil est un fait
> biologique, pas une consigne de codage. Si vous jugez que la base ne
> doit porter que du prescriptif, cette ligne est à écarter — et alors
> la même question se posera pour les six candidates de critères de la
> dénutrition (fichier `malnutrition_denutrition.md`, §D). Les deux
> décisions doivent aller ensemble.
