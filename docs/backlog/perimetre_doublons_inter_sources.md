# Backlog — Doublons inter-sources et élisions dans le Périmètre clinique

> Statut : **à instruire**. Constaté le 2026-08-13 pendant le chantier
> `chapter_policy`, requalifié après vérification des données. **Hors
> périmètre de ce chantier**, qui ne touche que la section Formulations.

## 1. Doublons ANS / OFS aux niveaux d'héritage

### Le constat, sur S00.7

Les inclusions héritées du bloc S00-S09 arrivent **deux fois**, sous deux
formes différentes de la même information :

```
[ANS    bloc] "lésions traumatiques de :\n - articulation temporomandibulaire\n
               - cavité buccale\n - cuir chevelu\n …"     ← UN bloc, 12 sites
[CIM-10 bloc] "lésions traumatiques de articulation temporo-maxillaire"
[CIM-10 bloc] "lésions traumatiques de cavité buccale"
[CIM-10 bloc] "lésions traumatiques de cuir chevelu"      ← 12 items PLATS
…
```

La fiche rend les treize lignes : le bloc ANS *plus* les douze items OFS.
Chaque site apparaît donc deux fois.

### Pourquoi le mécanisme existant ne l'attrape pas

**Il existe déjà une résolution, mais seulement au niveau code.**
`_perimeter_code_level_block` applique une **priorité de source** — OFS
primaire, ANS en repli — et c'est ce qui règle G02.1 proprement :

```
CSV : [ANS]    "Méningite (à) (due à) Candida"
      [CIM-10] "méningite à Candida"
Fiche : « méningite à Candida »        ← une seule forme, la forme OFS
```

Aux niveaux d'héritage (`chapter`, `block`, `category`),
`_perimeter_heritage_block` filtre sur `source_level` **sans priorité de
source** : les deux sources sont émises.

Et même avec une priorité, le cas S00.7 resterait particulier : la dédup
tolérante compare des chaînes entières, or **côté ANS les douze sites sont
une seule chaîne**. Aucune normalisation de chaîne ne fera correspondre un
bloc multi-lignes à douze items plats — il faut d'abord éclater le bloc.

### Deux pistes

1. **Étendre la priorité de source aux niveaux d'héritage.** Simple, cohérent
   avec le niveau code, et suffisant partout où les deux sources livrent des
   items plats. Ne règle pas S00.7 seul.
2. **Éclater les blocs multi-lignes ANS avant dédup.** Traite S00.7, mais
   revient à faire de l'atomisation ANS — que le CLAUDE.md écarte
   explicitement (pitfall n° 8 : « pas de parsing automatique »). À n'envisager
   qu'au **rendu**, jamais dans les données, et en mesurant d'abord combien de
   codes sont concernés.

Commencer par mesurer : combien de couples (code, niveau) ont à la fois une
inclusion ANS et une inclusion OFS ? Combien parmi eux ont un bloc ANS
multi-lignes ?

## 2. Élisions manquantes — le texte source, pas le rendu

« lésions traumatiques **de** articulation », « **de** oeil », « **de**
oreille ». Vérification faite : **ces formes sont dans le texte source OFS**,
telles quelles dans la colonne `texte` du CSV. Ce n'est donc pas un défaut de
rendu introduit par le chantier.

Le corriger supposerait une **normalisation légère à l'affichage** — élision
`de` + voyelle ou h muet → `de l'`, contraction `de` + `le` → `du` — soit
exactement le mécanisme de joints déjà écrit pour R3
(`normalize_index._colle`, `_rection_attestee`). Il est réutilisable tel quel,
et le lexique de rections est déjà construit.

Deux précautions :

- ce serait la **première normalisation appliquée à une source OFS**, jusqu'ici
  rendue verbatim. Le principe « ne jamais normaliser silencieusement un texte
  source » (CLAUDE.md) impose que ça reste un rendu, comme R3, et que ce soit
  documenté ;
- l'élision est déterministe, mais la contraction demande le genre — que le
  lexique de rections fournit, avec la même limite de couverture que pour R3.

## Ordre suggéré

Le point 2 est indépendant et peu risqué. Le point 1 demande d'abord une
mesure, puis un arbitrage sur l'atomisation ANS, qui touche un pitfall
documenté du CLAUDE.md.
