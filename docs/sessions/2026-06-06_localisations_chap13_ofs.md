# Tableau de codage des localisations ostéo-articulaires (chap XIII)

**Date** : 2026-06-06
**Type** : investigation OFS — découverte structurelle
**Statut** : investigation aboutie, en lien avec le chantier 2 (qualité des synonymes ANS)

---

## 1. Contexte

Cette session prolonge l'investigation du chantier 2 ouvert dans
`docs/sessions/2026-05-30_refonte_dagger_asterisk.md` section 9 :
*synonymes ANS de qualité douteuse (D21.6 « Tronc », M01.08 noms
anatomiques bruts)*.

Lors de l'exploration de M01.08 via `inspect_code_extended()`, on a
observé que ses 6 `skos:altLabel` ANS sont des noms anatomiques bruts
(« colonne vertébrale », « cou », « crâne », « côtes », « tête »,
« tronc »). Question initiale : où sont stockés ces noms dans OFS, et
existe-t-il un référentiel canonique ?

## 2. Découverte structurelle

Le chapitre XIII de la CIM-10 OMS définit un **système de
sous-classifications additionnelles en 5ᵉ position** : chaque code
`Mxx.x` peut être suffixé d'un chiffre 0-9 qui indique la localisation
anatomique (épaule, coude, hanche, genou, etc.).

### Convention OMS — Liste canonique des 5ᵉ positions

| Position | Localisation |
|---|---|
| 0 | sièges multiples |
| 1 | région scapulaire |
| 2 | bras |
| 3 | avant-bras |
| 4 | main |
| 5 | région pelvienne et cuisse |
| 6 | jambe |
| 7 | cheville et pied |
| 8 | **autres** (tête, cou, tronc, côtes, crâne, colonne vertébrale) |
| 9 | siège non précisé |

### Comment OFS stocke cette information — 3 conventions complémentaires

**(a) Atomisation dans MASTER** — chaque combinaison `Mxx.x` + 5ᵉ
position est encodée comme un code à 5 caractères (`M01.00`,
`M01.01`, …, `M01.09`) avec son propre SID. Type=`D` (Détail), level=6.
C'est la convention principale et la seule porteuse de SID exploitable
par le pipeline.

**(b) Convention de libellé `<parent> | <localisation>`** — le séparateur
`|` (pipe) dans la colonne `LIBELLE.libelle` matérialise la 5ᵉ
position dans le texte :

```
M01.01 → arthrite méningococcique | région scapulaire
M01.05 → arthrite méningococcique | région pelvienne et cuisse
M01.08 → arthrite méningococcique | autres
M02.05 → arthropathie après dérivation intestinale | région pelvienne et cuisse
```

C'est la signature lexicale permettant de détecter les codes touchés
par le tableau et d'extraire la position canonique.

**(c) Pointeur vers le tableau OMS de référence** — la table REFER
référence le chapitre XIII (SID=5401) vers deux entrées LIBELLE avec
une **nouvelle source `R` (Référence)** :

```
LID=31711, ref=v1c13n1,  source=R → "tableau de codage de la localisation ostéo-articulaire"
LID=31790, ref=v1c13ast, source=R → "liste des catégories à code astérisque"
```

LIBELLE multilingue (FR_OMS, EN_OMS, GE_DIMDI). Mais ce n'est qu'un
pointeur de titre, sans le contenu (les 10 valeurs 0-9) — celui-ci est
implicite, à reconstituer par lecture des libellés MASTER.

### Découverte bonus : la source `R` de LIBELLE

Distribution `source` dans LIBELLE :

| source | n | nature |
|---|---|---|
| S | 19 094 | Systématique (libellé officiel) |
| D | 8 539 | Descripteur (synonyme) |
| E | 3 602 | Exclusion (texte) |
| I | 1 332 | Inclusion |
| N | 43 | iNdir (exclusion indirecte) |
| **R** | **19** | **Référence** (vers tableaux OMS) |

Les 19 LID de `LIBELLE.source='R'` sont en **intersection parfaite**
avec les 19 LID de la table REFER. C'est le seul lien formel entre OFS
et les tableaux structurés de la CIM-10 OMS. Cette source n'est pas
documentée dans `docs/sources/ofs_schema.md` — à intégrer.

## 3. Lien avec le chantier 2 (synonymes ANS qualité douteuse)

Hypothèse : les 6 `skos:altLabel` de M01.08 (et autres codes M*.8) ne
sont pas des reformulations cliniques mais des **extraits du tableau
de la 5ᵉ position 8 « autres »**, étiquetés par erreur comme
synonymes lors de la génération du RDF ANS depuis la classification
OMS.

Cette hypothèse a été quantifiée sur l'ensemble des codes M*.X8 du
chapitre XIII (cf cellule dédiée du notebook
`scripts/explore/2026-06-04_qualite_synonymes_ans.ipynb` produisant les
4 livrables : liste canonique, détection des localisations dans les
altLabel, quantification du problème, échantillon de codes touchés).

**Implications pour la décision chantier 2** :

- Les altLabel concernés sont sémantiquement valides (ce sont bien des
  localisations qui appartiennent à la sémantique de `.8`) mais
  étiquetés au mauvais niveau (synonyme du code complet plutôt que
  composant d'une 5ᵉ position).
- Filtrer aveuglément les altLabel courts est risqué — mieux vaut
  croiser avec la liste canonique des 5ᵉ positions du chapitre XIII.
- Pour les futurs chantiers de qualité ANS : détecter les altLabel
  qui matchent une 5ᵉ position est un signal fiable et déterministe
  qu'on a affaire à un extrait du tableau, pas à un vrai synonyme.

## 4. Pistes pour des chantiers futurs

- **Étendre `loaders_dev`** : exposer une fonction `position5_table(ctx)`
  qui retourne le DataFrame canonique des 5ᵉ positions (réutilisable
  par d'autres analyses).
- **Documenter LIBELLE.source='R'** dans `docs/sources/ofs_schema.md`.
- **Décision politique chantier 2** : quand un altLabel ANS est dans la
  liste canonique des 5ᵉ positions du chapitre XIII pour un code
  M*.x8, faut-il :
  1. le filtrer du CSV (perte d'information, mais netteté)
  2. le retyper en `localisation` (nouveau type, complique le schéma)
  3. le laisser tel quel et documenter la limitation (statu quo)
- **Étendre à d'autres chapitres** : la CIM-10 a d'autres systèmes de
  sous-classifications additionnelles (chapitre XIX traumatismes par
  exemple). À vérifier si la même structure se retrouve via
  LIBELLE.source='R' / REFER.

## 5. Fichiers de référence du projet impactés

| Fichier | Statut après cette session |
|---------|----------------------------|
| `docs/sessions/2026-06-06_localisations_chap13_ofs.md` | Créé (le présent fichier) |
| `scripts/explore/2026-06-04_qualite_synonymes_ans.ipynb` | Extension : cellule des 4 livrables sur les localisations chap XIII |
| `docs/sources/ofs_schema.md` | À mettre à jour avec `LIBELLE.source='R'` (futur chantier doc) |

## 6. Quantification empirique du périmètre

Une quantification exhaustive a été menée pour cadrer précisément le
chantier de retypage qui suit. 3 questions empiriques exécutées sur la
table MASTER OFS et le RDF ANS.

### Q1 — Volume des codes type=D par chapitre

| Chapitre        | Codes type=D |
|-----------------|--------------|
| XIII (M00-M99)  | 3 711        |
| Tous les autres | 0            |

**100 % de concentration sur le chapitre XIII**. Le retypage peut donc
être limité strictement à XIII sans risque de manquer des cas
ailleurs dans la classification.

### Q2 — Pattern altLabel ⊆ inclusionNote

| Mesure                                                  | Valeur | Part   |
|---------------------------------------------------------|--------|--------|
| Codes type=D au total                                   | 3 711  | 100 %  |
| Présents dans le RDF ANS                                | 3 621  | 97,6 % |
| Avec ≥1 `skos:altLabel`                                 | 2 280  | 61,4 % |
| Avec ≥1 `xkos:inclusionNote`                            | 2 280  | 61,4 % |
| Avec les deux                                           | 2 280  | 61,4 % |
| Suivant altLabel ⊆ inclusionNote                        | 2 280  | 100 %  |
| altLabel ANS sans correspondance dans inclusionNote     | 0 / 9 405 | 0,0 % |

**Pattern parfaitement déterministe** : zéro exception sur 9 405
altLabel inspectés.

### Q3 — Cas particuliers

| Cas                                                  | n     |
|------------------------------------------------------|-------|
| type=D sans altLabel                                 | 1 341 |
| type=D sans inclusionNote                            | 1 341 |
| type=D avec altLabel ET inclusionNote, alt ⊄ incl    | 0     |
| type=D absents du RDF ANS                            | 90    |

**Observation structurelle décisive** : la co-occurrence entre
`skos:altLabel` et `xkos:inclusionNote` est stricte. Soit le code a
les deux (2 280 codes), soit aucun des deux (1 341 codes). Total dans
le RDF ANS : 2 280 + 1 341 = 3 621.

**Dichotomie parfaite** : un code type=D est soit "avec expansion
ANS" (atomique + groupé), soit "sans expansion ANS".

## 7. Décisions actées

### Critère de détection

**Critère D — Détection structurelle via MASTER** : pour tout code
ayant `type=D, level=6` dans MASTER, les `skos:altLabel` ANS sont à
retypage en `inclusion`.

Justifications :

1. **Robustesse** : la table MASTER ne dépend pas de la qualité
   d'extraction de l'ANS. Si demain l'ANS change sa façon d'extraire
   les altLabel, ça ne casse rien.
2. **Traçabilité sémantique** : un code `type=D, level=6` dans MASTER
   a une définition précise (5e position d'une sous-catégorie). On agit
   sur une caractéristique structurelle du référentiel, pas sur un
   artefact d'export.
3. **Compatibilité future** : si on découvre d'autres chapitres avec
   des 5e positions (autres formats possibles selon les versions), la
   détection MASTER reste valide.
4. **Validation empirique** : 100 % des codes type=D du chapitre XIII
   suivent le pattern, zéro exception.

Alternatives écartées :
- **Critère heuristique sur le pattern altLabel ⊆ inclusionNote** :
  fonctionne, mais dépend de la qualité d'extraction ANS. Moins
  robuste.
- **Critère "chapitre M"** : équivalent en pratique mais moins précis
  conceptuellement. Le critère D est plus fin et explicite.
- **Critère textuel sur les altLabel** (liste de vocabulaire
  anatomique) : fragile (rate "thoracolombaire", "costochondrale",
  etc.) et nécessite curation.

### Périmètre du retypage

| Sous-population                                    | Action                  |
|----------------------------------------------------|--------------------------|
| Codes type=D avec altLabel et inclusionNote (2 280) | Retypage altLabel→inclusion |
| Codes type=D sans altLabel ni inclusionNote (1 341) | Neutres (rien à retyper) |
| Codes type=D absents du RDF ANS (90)               | Hors périmètre, audit séparé |

### Politique de redondance — option α retenue

Après retypage, un code comme M01.08 aura dans le CSV à la fois :
- 6 lignes `type=inclusion, source=ANS, source_level=code` (altLabel
  atomiques retypés)
- 1 ligne `type=inclusion, source=ANS, source_level=code` (bloc
  multi-ligne d'inclusionNote)

Soit **7 lignes d'inclusion** portant la même information sémantique
sous deux formes (atomique et groupée).

**Décision** : redondance acceptée dans le CSV.

Justifications :
- Le CSV est un format intermédiaire ; les consommateurs (script de
  fiche, future génération LLM) peuvent dédoublonner côté usage si
  nécessaire.
- L'option de filtrage automatique (ne garder que les atomiques ou
  ne garder que le bloc) introduirait une logique complexe pour un
  gain marginal.
- La forme atomique et la forme groupée ont des usages potentiellement
  différents selon le consommateur.

## 8. Chantier d'implémentation à venir

### Architecture

**Le retypage se fait dans le merger** (`merge.py`), pas dans le
loader OWL/ANS ni dans un module de post-traitement séparé.

Justifications :
- Le loader OWL/ANS reste simple, indépendant d'OFS.
- Le merger a déjà accès aux deux sources (OFS et ANS).
- Le retypage est sémantiquement une forme de réconciliation, qui
  est précisément le rôle du merger.

### Périmètre

- Modifier le loader OFS pour exposer le type MASTER (`type_master`,
  `level_master`) si pas déjà exposé.
- Modifier le merger pour retypage les `skos:altLabel` ANS en
  `inclusion` quand le code est `type=D` dans MASTER.
- Préserver tous les autres `skos:altLabel` (autres chapitres).
- Générer un rapport `reports/orphan_type_d_codes.csv` pour les 90
  codes absents du RDF ANS.

### Périmètre d'inchangé

- Le pipeline OFS reste inchangé sur sa structure.
- La structure du CSV final reste inchangée (9 colonnes).
- La logique de propagation reste inchangée.
- Les loaders externes (ORPHANET, Index, AP-HP) restent intacts.
- Le script de fiche n'est pas modifié.

### Tests de régression

À ajouter :
- **M01.08** : 0 ligne `type=synonyme, source=ANS, source_level=code`,
  7+ lignes `type=inclusion, source=ANS, source_level=code`
- **M01.05** : 0 ligne synonyme ANS, 2+ lignes inclusion ANS
- **M00.00** : code neutre, pas de changement attendu
- **Code hors chapitre M** (ex : un code U07.x) : synonymes ANS
  préservés (non affectés par le retypage)

### Validation empirique attendue

Mesures sur le CSV avant/après :

| Mesure                                | Avant     | Après attendu |
|---------------------------------------|-----------|---------------|
| Lignes total CSV                      | ~199 970  | ~199 970 (inchangé) |
| Lignes `type=synonyme, source=ANS`    | 15 567    | ~6 162 (–9 405) |
| Lignes `type=inclusion, source=ANS`   | (à mesurer) | +9 405 |
| Codes avec ≥1 synonyme ANS            | 4 531     | 2 251 |

## 9. Conséquences pour les fiches descriptives

L'impact sur les fiches descriptives sera automatique au prochain
build :

- **Section 2 "Périmètre clinique"** : pour M01.08 et autres codes
  type=D, le fallback sur synonymes ANS ne sera plus déclenché.
  Les inclusions retypées seront disponibles via la logique existante.
- **Section 3 "À ne pas décrire"** : inchangée (utilise les
  exclusions, pas les synonymes).
- **Section 4 "Formulations cliniques alternatives"** : inchangée
  (utilise déjà uniquement Index + AP-HP).

À vérifier empiriquement après le chantier en régénérant les 4 fiches
témoins (A18.1, J18.8, R51, U07.1) plus quelques fiches du chapitre
XIII (M01.08, M01.05, M00.00).

## 10. Chantiers collatéraux identifiés

### Audit des 90 codes type=D absents du RDF ANS

Pas urgent. Probablement à grouper avec d'autres chantiers d'audit
de couverture.

### Divergence DAGSTAR ↔ ANS hasCausality/hasManifestation

Observation collatérale lors de l'investigation via
`inspect_code_extended` : la table DAGSTAR OFS et les relations ANS
structurées (`atih-cim10:hasCausality`, `atih-cim10:hasManifestation`)
sont divergentes pour certains codes.

Exemple : F02.83 a 0 paire dans DAGSTAR OFS, mais 9 relations
`hasCausality` dans le RDF ANS, chacune avec un libellé humain réifié
dans un `owl:Axiom` (ex. "Démence au cours de sclérose en plaques").

C'est une **information précieuse perdue par le loader actuel**.
Chantier d'enrichissement possible, non urgent.

### Étoffer le loader OWL pour les propriétés RDF non extraites

Le pipeline `smt2parquet` actuel extrait 5 attributs sur les 14+
propriétés présentes dans le RDF. Propriétés actuellement perdues :
- `xkos:exclusionNote` (2 817 occurrences)
- `atih-cim10:exclusion` (5 739)
- `atih-cim10:hasCausality` (1 317)
- `atih-cim10:hasManifestation` (341)
- `skos:definition` (381)
- `skos:scopeNote` (355)
- `skos:note` (783)
- `owl:annotatedSource/Target/Property` (1 134 axiomes réifiés)

Chantier d'enrichissement, non urgent. À cadrer séparément quand on
en aura besoin.