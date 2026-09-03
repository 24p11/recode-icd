# 2026-09-03 — Chantier B, série 1 : ouverture et cinq premières soumissions

Branche `feat/guide-mco-serie-1`, **worktree `../recode-icd-serie1`**
(voir « Incident » ci-dessous). Base : `main` post-chantier A, 535 tests
verts constatés (la référence disait 526+).

## Fait

1. **File de travail committée** —
   [`file_chantier_B.md`](../../data/guide_mco/extraction/file_chantier_B.md),
   **35 articles** établis depuis le sommaire du guide. Cinq articles
   absents de la liste initiale du prompt réintégrés : ACCOUCHEMENT
   IMPROMPTU OU À DOMICILE (81), CYSTITE AIGÜE (88), EMPLOI DES CODES DU
   GROUPE B95–B98 (91), EMPLOI DES CATÉGORIES O80 À O84 (92), EMPLOI DES
   CATÉGORIES P00 À P04 (92). **ÉTAT GRABATAIRE vérifié** : il porte une
   consigne propre (emploi de R26.30 réservé à la définition, chronicité
   exigée) — il reste en file.

2. **Cinq articles produits et soumis** (curés verts, candidates dans
   les CSV, markdowns régénérés) — **aucun n'est versé ni figé**, tout
   attend la passe de relecture RF :

   | Article | Curé | Candidates | Associations |
   |---|---|---|---|
   | ACCOUCHEMENT IMPROMPTU OU À DOMICILE | 191 mots + 13 de notes | ACC-01..03 | 3 |
   | ANTÉCÉDENTS | 383 + 107 | ANT-01..05 | 29 |
   | ATHEROSCLEROSE AVEC GANGRENE | 144 | ATH-01 | 2 |
   | CARENCES VITAMINIQUES | 71 | CAR-01..02 | 2 |
   | CHUTES A REPETITION | 225 | CHU-01..03 | 3 |

   Soit **14 consignes, 39 associations**. Suite de tests : **545
   verts** (535 + 10 tests paramétrés des nouveaux curés/citations).

## Points saillants pour la relecture

- **ANT-01 descend sur les chapitres I à XIX** (19 associations
  `interdit`, une par chapitre — pas de forme « plage de chapitres »
  dans le parseur). C'est l'article que la note de conception §4.2 bis
  désigne explicitement comme devant descendre sur toutes ses feuilles.
- **Deux portées `ensemble` déclarées** :
  - ANT-01 / `XXI` (`regi`) — domaine du choix du code Z, précédent
    AVC-14 ;
  - ANT-05 / `II` (`regi`) — « code adapté du chapitre II » : les
    tumeurs bénignes/in situ ne sont pas concernées par l'alternative
    cancer/antécédent.
- **ACC-02 sans association** (aucun code nommé — précédent AVC-18,
  sortira au rapport `sans_code`).
- **Ancres de notes** : 4 notes orphelines déclarées (ACC note 5 —
  repliée à la main, définition indentée que `decoupe` ne capte pas ;
  ANT notes 6-8 — appels hissés). Ancres dans `curation.yaml`, à
  contre-lire sur le PDF.
- **Titres sans accents** (ATHEROSCLEROSE, CHUTES A REPETITION)
  transcrits tels quels — la curation ne corrige pas le guide.

## Évolutions d'outillage (portées par cette branche)

- `candidates_recommendation_codes.csv` : colonnes **`portee` /
  `justification`** ajoutées (grille chantier B) ; lignes du pilote
  inchangées (vides = `chaque`).
- `rendre_candidates_guide_mco.py` : colonne portee dans les tables
  (une bascule `ensemble` s'affiche en relief avec sa justification),
  ancrage des citations paramétré par article (pilote → bruts,
  chantier B → curés).
- `extraire_guide_mco.sh` : 5 articles ajoutés ; bruts du pilote
  régénérés à l'identique (poppler 26.08.0 inchangé, empreintes OK).

## Incident — collision avec le chantier branchement (cards)

Le chantier parallèle travaille dans le **même clone** : mon premier
commit de l'article 1 est parti sur `feat/cards-recommandations` en
embarquant son travail non committé. Réparé en coordination avec la
session pair (messages échangés) : sa branche remise à `30ab2ec`, son
arbre restitué à l'identique, mon commit refait proprement sur ma
branche. **Mon chantier vit désormais dans le worktree
`../recode-icd-serie1`** ; le clone principal appartient au chantier
cards. Leçon : deux sessions, deux worktrees — et jamais de
`git add -A` dans un arbre partagé.

## Prochaine étape

Passe de relecture RF sur les cinq soumissions (curés — il peut
corriger par push, le test d'intégrité veille — et verdicts rec_id →
OK/correction). Au retour : application, versement dans les tables
curées, gel (manifeste + relecteur/date), cases cochées dans la file,
puis enchaînement sur CODES OMS RÉSERVÉS À UN USAGE URGENT (p. 84) et
la suite, sans autre accord.
