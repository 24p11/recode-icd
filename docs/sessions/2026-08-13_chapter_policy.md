# Session 2026-08-13 — chantier `chapter_policy`

> Porte les règles R1/R2/R3, instruites et figées lors des sessions
> précédentes, du prototype de notebook vers `src/`, sous configuration
> YAML. Premier chantier autorisé à modifier `cards.py`.

## Ce qui a été fait

Six commits. La série va de la configuration déclarative au rebuild des
18 000 fiches.

| # | Commit | Contenu |
|---|---|---|
| 1 | `feat(policy)` | `policy.py`, `hierarchie.py`, le YAML, 14 tests |
| 2 | `feat(lexicons)` | les trois lexiques, schémas pandera, `build lexicons`, 14 tests |
| 3 | `feat(normalize-index)` | port v5 à l'identique, 28 tests dorés |
| 4 | `feat(cards)` | câblage R1/R2/R3, RNG par code, options CLI |
| 5 | `chore(cards)` | retrait d'ORPHANET, rebuild des 18 000 fiches, rapport |
| 6 | `docs` | CLAUDE.md, migration du notebook, export de relecture, ce récap |

Suite à **423 tests verts** (366 en entrée de chantier), `ruff` et
`mypy` propres.

## L'invariant, et le test qui le tient

Les trois règles s'appliquent à l'**assemblage des fiches**. Le CSV
maître, les Parquets et la colonne `texte` ne sont jamais modifiés.

Ce n'est pas une intention, c'est une assertion :
`test_le_csv_nest_pas_modifie` construit la fiche R51, vérifie que le
markdown rend « céphalée » (forme normalisée) et que « Céphalée (de) »
(forme source) est **toujours** dans le CSV après le build. Si R3
fuyait en amont, le libellé officiel du volume 3 deviendrait
irrécupérable.

## Effet mesuré sur les fiches

Sur 161 607 candidats à la section Formulations :

| | Entrées |
|---|---|
| Écartées par R1 (plage × famille) | 31 441 |
| Écartées par R3 (normalisation Index) | 24 989 |
| Normalisées par R3 | 10 922 |
| **Conservées** | **94 255** |

Sections Formulations : **8 629 → 5 983**, soit **2 646 vidées**. La
ventilation par chapitre ne laisse **aucun résidu inexpliqué** :

- **1 747 (66 %)** sur les chapitres XIX-XX-XXI, où R1 exclut les
  sources externes — c'est l'effet voulu ;
- **899 ailleurs**, et les 899 avaient **l'Index pour seule source**.
  R3 les a toutes écartées, ce qui est cohérent avec son taux
  d'exclusion global (24 989 / 36 627).

Le plafond par famille R2 côté AP-HP ne touche que **21 fiches** : son
effet isolé est marginal, l'essentiel du plafonnement porte sur l'Index
et CepiDc.

## Trois décisions prises en séance

### ORPHANET sort des Formulations

Le YAML admettait ORPHANET alors que la constante Python l'excluait :
**1 467 fiches avaient changé sans que personne l'ait décidé**, et 31
avaient gagné une section. Auto-signalé, puis tranché — exclusion, pour
une raison de fond : des synonymes de maladies rares dans les prompts
de génération **biaiseraient le corpus vers des événements à basse
fréquence**.

Un profil de fiche « contrôle qualité », qui les admettrait, est ouvert
au backlog ([`profils_fiches_par_usage.md`](../backlog/profils_fiches_par_usage.md)) :
pour un vérificateur, la même information élargit le rappel au lieu de
biaiser un générateur.

### Les constantes de libellés sont supprimées, pas synchronisées

L'incident ci-dessus vient de **deux énumérations testées l'une contre
l'autre**. Les maintenir synchronisées ne fait que déplacer le risque.
Toutes les constantes `FORMULATION_SOURCE*` de `cards.py` ont été
supprimées ; le YAML est la vérité unique, et la couverture
bidirectionnelle YAML ↔ `_SOURCE_CSV_MAP` est verrouillée par
`test_policy.py`.

### Résolution par remplacement

Bloc > chapitre > défaut, la règle la plus spécifique **remplace**
intégralement la moins spécifique. C'est le seul choix qui permette de
*ré-admettre* une source au niveau d'un bloc. Le test dédié porte un
message qui dit au lecteur de relire le pitfall plutôt que de
« réparer » le test.

## Deux mesures faites, à arbitrer

### Variante d'ordre des connecteurs

Testé : « familles fléchies (`de`/`à`) prioritaires sur les
littéraux, ordre source ensuite », au lieu de l'ordre source seul.

**16 entrées sur 264 changent, avec un bilan mitigé.** Meilleur sur les
sites anatomiques (« myiase **de l'**orbite », « problème de santé
**dans la** famille ») ; **moins bon sur les complications** — « zona
**avec** encéphalite » devient « zona **de** encéphalite », qui en
prime rate l'élision.

**Recommandation : garder l'ordre source.** Le gain sur les sites ne
compense pas une régression sur une classe entière, et le cas
« de encéphalite » est une faute de forme visible.

### Confirmation G02.1

Vérifié : la fiche rend **une seule forme**, « méningite à Candida »
(la forme OFS), alors que le CSV porte bien les deux (`[ANS]
"Méningite (à) (due à) Candida"` et `[CIM-10] "méningite à Candida"`).

Mais le mécanisme n'est **pas** une dédup tolérante : c'est une
**priorité de source** (OFS primaire, ANS en repli) dans
`_perimeter_code_level_block`. Aux niveaux d'héritage,
`_perimeter_heritage_block` filtre sur `source_level` **sans** priorité
de source — d'où le cas S00.7, où un bloc ANS de 12 sites *et* 12 items
plats OFS sont tous deux rendus. Documenté au backlog
([`perimetre_doublons_inter_sources.md`](../backlog/perimetre_doublons_inter_sources.md)).

## Le notebook importe désormais `src/`

`scripts/explore/qualite_sources_par_chapitre.py` ne redéfinit plus les
règles. Il importe `policy`, `lexicons` et `normalize_index`, et une
section finale **assure** que l'implémentation reproduit exactement le
prototype figé :

```
Référence figée : {'index': 36627, 'retenues': 11638, 'reecrites': 10922}
Implémentation  : {'index': 36627, 'retenues': 11638, 'reecrites': 10922}
```

L'assertion est bloquante : tout écart signalerait une divergence entre
le prototype et le code de production. Les cellules pédagogiques
restent — elles racontent comment les règles ont été trouvées et les
quatre pièges qu'il a fallu lever.

## Un défaut corrigé au passage

`DEFAULT_POLICY_PATH` et le répertoire des lexiques étaient **relatifs
au répertoire courant**, donc valides depuis la racine du dépôt
seulement. `nbconvert` exécute un notebook depuis son propre
répertoire : l'exécution échouait sur `FileNotFoundError`. Les deux
chemins sont désormais ancrés sur l'emplacement du paquet
(`DEFAULT_POLICY_PATH`, `DEFAULT_LEXICONS_DIR`).

## Reste ouvert

- Arbitrer la variante d'ordre des connecteurs (recommandation :
  statu quo).
- [`profils_fiches_par_usage.md`](../backlog/profils_fiches_par_usage.md) —
  profil « contrôle qualité ».
- [`perimetre_doublons_inter_sources.md`](../backlog/perimetre_doublons_inter_sources.md) —
  doublons ANS/OFS aux niveaux d'héritage, et élisions manquantes dans
  le texte source OFS.
- [`taille_csv_maitre.md`](../backlog/taille_csv_maitre.md) — le CSV
  maître à 53,15 Mo face aux limites GitHub.
