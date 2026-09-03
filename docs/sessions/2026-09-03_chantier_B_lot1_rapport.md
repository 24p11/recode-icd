# Chantier B — rapport du lot 1 (2026-09-03)

Cinq articles relus et validés par RF (verdict global OK, passe unique),
versés, figés, mergés dans `main`. Base après lot : **108 consignes,
226 associations curées → 16 548 couples résolus sur 14 669 codes**
(avant lot : 94 / 187 / 2 056).

## Volumétrie par article

| Article | Consignes | Associations | Couples résolus | Codes distincts |
|---|---|---|---|---|
| ACCOUCHEMENT IMPROMPTU OU À DOMICILE | 3 (ACC-01..03) | 3 | 20 | 20 |
| ANTÉCÉDENTS | 5 (ANT-01..05) | 29 | 14 414 | 14 152 |
| ATHEROSCLEROSE AVEC GANGRENE | 1 (ATH-01) | 2 | 3 | 3 |
| CARENCES VITAMINIQUES | 2 (CAR-01..02) | 2 | 52 | 26 |
| CHUTES A REPETITION | 3 (CHU-01..03) | 3 | 3 | 1 |
| **Total** | **14** | **39** | **14 492** | — |

L'explosion des couples vient d'ANT-01 : l'interdiction « un antécédent
ne se code pas comme une affection active » descend sur les 19 chapitres
I à XIX (une association `interdit` par chapitre), soit ~14 000 fiches —
c'est le cas que la note de conception §4.2 bis désignait explicitement
comme devant descendre. Dans les fiches, elle se rend sous « Règles
générales du chapitre N », une ligne par fiche.

## Associations `ensemble` déclarées (2)

| Association | Rôle | Justification |
|---|---|---|
| ANT-01 / `XXI` | `regi` | Domaine du choix du code Z selon la nature de l'antécédent ; l'essentiel du chapitre XXI ne code pas d'antécédents (précédent AVC-14, témoin Z23.0 — vérifié inchangé) |
| ANT-05 / `II` | `regi` | « code adapté du chapitre II » : l'alternative cancer/antécédent ne régit pas les tumeurs bénignes/in situ |

Toutes deux au rapport `guide_mco_associations_ensemble.csv`, jamais
résolues (invariant pandera).

## Divergences signalées

Aucune. Une consigne sans code : ACC-02 (accouchement à domicile choisi
= pas de RSS ; aucun code nommé) — au rapport
`guide_mco_recommandations_sans_code.csv` avec AVC-18, c'est normal.

## Évolution des témoins de fiches (6 attendus mis à jour, diff motivé)

Tous les changements viennent d'ANT-01 (règle générale de chapitre) :

- `test_d62_article_historique` : D62 gagne ANT-01 et une sous-section
  « Règles générales du chapitre III » ;
- `test_e43_les_definitions_de_seuils` : E43 gagne ANT-01 (chapitre IV) ;
- `test_f01_000_exemple_seul_en_bloc_cite` : F01.000 gagne les règles
  générales du chapitre V — sa liste principale reste vide ;
- `test_fiche_sans_consigne_strictement_inchangee` : **témoin changé
  R51 → W65** (R51, chapitre XVIII, est désormais couvert par ANT-01 ;
  le témoin doit vivre hors chapitres I-XIX — W65, noyade dans une
  baignoire, chapitre XX, n'est dans le périmètre d'aucun article de la
  file) ;
- `test_parquets_presents_rapport_compte_par_chapitre` : tout le
  chapitre III a désormais la section (D62 garde ses consignes
  d'article) ;
- `test_detect_sections_via_build_card` (unit) : A18.1 a la section.

Témoins **inchangés et probants** : Z23.0 (l'`ensemble` ANT-01/XXI ne
descend pas — la fiche ne porte toujours que XXI-01) et I64, Z86.70,
Z51.5, Z20.1 (le filtre `contexte` et la dédup tiennent).

Suite de tests : **570 verts** après mise à jour.

## Gel

Les cinq curés sont figés (`extraits/SHA256SUMS`), validations
`relecteur: RF, date: 2026-09-03` dans `curation.yaml`. Les cinq bruts
entrent au manifeste `extraits_bruts/SHA256SUMS` (les empreintes du
pilote n'ont pas bougé). Cases 1-5 cochées dans `file_chantier_B.md`.

## Prochain article

CODES OMS RÉSERVÉS À UN USAGE URGENT (p. 84) — puis COMPLICATIONS DES
ACTES MÉDICAUX ET CHIRURGICAUX (pp. 84-88, l'article exceptionnel de la
file : ~4 pages denses, découpage à annoncer à la soumission si besoin).
