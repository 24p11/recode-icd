# Chantier B — passation de poste (2026-09-04)

> Document de reprise : tout l'état utile du chantier vit dans le dépôt.
> Une nouvelle session Claude Code sur un autre poste reprend avec ce
> fichier, le CLAUDE.md et le registre des arbitrages — rien d'autre
> n'est nécessaire.

## Où en est la file (29/35 traités, 23 versés)

- **Versés, figés, mergés dans `main`** (lots 1-4, 23 articles) :
  ACCOUCHEMENT IMPROMPTU → INSUFFISANCE RESPIRATOIRE DE L'ADULTE.
  Cases cochées dans `data/guide_mco/extraction/file_chantier_B.md`.
  Base : **141 consignes, 339 associations → 18 090 couples sur
  15 009 codes**. Rapports de lot : `docs/sessions/2026-09-03_*.md`.
- **Lot 5 SOUMIS, en attente des verdicts RF** (6 articles, commits
  `5ca8af4` + `a2e1766` sur `feat/guide-mco-serie-1`) :
  INTERRUPTION DE LA GROSSESSE (ITG-01..09), LÉSIONS TRAUMATIQUES
  (LES-01), MALADIES PROFESSIONNELLES (MPR-01), ŒDÈME PULMONAIRE
  (OED-01), PRÉCARITÉ (PRE-01..12), RÉSISTANCE AUX ANTIMICROBIENS
  (RAM-01..05) — 29 consignes, 58 associations, dans les candidates
  (`extraction/candidates_*.md`), **non versées, curés non figés**.
- **Restent à produire** (lot 6, dernier) : SEPSIS ET CHOC SEPTIQUE
  (p. 116, note 68 déjà repérée), SÉQUELLES DE MALADIES ET DE LÉSIONS
  TRAUMATIQUES (pp. 117-119 — le témoin Z86.70 gagnera des consignes),
  SUICIDES ET TENTATIVES DE SUICIDE, TRAITEMENT DES GRANDS BRÛLÉS,
  TUMEURS À ÉVOLUTION IMPRÉVISIBLE OU INCONNUE (p. 119), VIOLENCE
  ROUTIÈRE (pp. 120-121).

## Ce qui attend le verdict de RF (bloquant pour le versement du lot 5)

1. **Verdicts rec_id → OK/correction** sur les 6 articles du lot 5.
2. **Arbitrage O04 (notation FR étendue)** : cinq expressions du guide
   (O04.90, O04.4, O04.-1, O04.-2, O04.-3) ne sont pas parsables — le
   référentiel les encode `O04.-<5e>.<4e>` (« O04.90 » du guide =
   feuille `O04.-0.9`) et `code_expr` ne connaît ni cette forme ni la
   notation à 5e caractère. Déclarées telles qu'écrites, au rapport
   `guide_mco_expressions_non_parsables.csv`. Proposition en attente :
   étendre le parseur aux formes FR étendues + table de correspondance
   notation guide ↔ forme du référentiel.

## Le régime de travail convenu (feu vert standard permanent, RF 2026-09-03)

Production jusqu'au plafond d'un lot (5-6 soumissions) → passe RF
(verdicts en liste ; corrections de curé directement dans les fichiers,
le test d'intégrité veille) → versement/gel/rebuild/rapport de lot →
**accord de merge explicite par lot** → merge `--no-ff` dans `main`,
rebase de la branche → lot suivant sans autre validation. Rythme
constaté : lots 1-4 versés et mergés le 2026-09-03.

## Reprise sur un autre poste

```bash
git clone <remote> recode-icd && cd recode-icd
git checkout feat/guide-mco-serie-1   # la branche du chantier
uv sync
uv run pre-commit install
uv run pytest -q                      # attendu : 628 verts
```

Points de vigilance :

- **Un seul clone, une seule session** (consigne n° 8 du CLAUDE.md).
- **Ne PAS régénérer les bruts** sauf besoin : ils sont committés et
  verrouillés par empreinte. La régénération exige **poppler 26.08.0**
  (version inscrite en tête de chaque brut) — une autre version décale
  les citations.
- `outputs/cards_library*` (bibliothèques de fiches) sont des artefacts
  locaux non committés : `uv run recode-icd cards build` puis
  `cards build-categories` pour les reconstruire (~2,5 min).
- Les artefacts pipeline (`referentials/processed/*.parquet`,
  `reports/*.csv`) sont committés — rien à reconstruire pour commencer.

**Amorce pour la nouvelle session Claude** (à coller tel quel) :

> Chantier B du guide MCO, reprise de session (voir
> docs/sessions/2026-09-04_passation_chantier_B.md pour l'état exact).
> Contexte obligatoire : section « Recommandations du guide
> méthodologique MCO » du CLAUDE.md, la note de conception
> docs/analyses/2026-08-09_conception_base_recommandations_guide_methodo.md,
> et le registre data/guide_mco/extraction/README.md (arbitrages 1-11).
> Le lot 5 est soumis et attend mes verdicts ; le feu vert standard
> permanent s'applique (production au plafond, ma passe,
> versement/gel/rebuild, accord de merge par lot). Voici mes verdicts
> sur le lot 5 : […]

## Rappels de procédure propres au chantier (au-delà du CLAUDE.md)

- Versement = recopier les colonnes 1-7 des candidates validées dans
  `recommendations_curated.csv` (+ `rendu_fiche`/`justification_rendu`
  vides) et toutes les colonnes dans `recommendation_codes_curated.csv` ;
  gel = `shasum -a 256 *.md > SHA256SUMS` (extraits) et idem bruts,
  `validations` (relecteur RF + date) dans `curation.yaml`, cases
  cochées dans la file.
- Après versement : `uv run recode-icd build guide-mco`, vérifier les
  rapports (sans-code attendus : ACC-02, AVC-18, ENF-01/03/04, POL-01,
  REB-01 ; non-résolue attendue : OMS-01/U00-U49), pytest, rebuild des
  deux bibliothèques, rapport de lot dans `docs/sessions/`.
- Les artefacts de l'original (coquilles, numéros égarés « 19 », « 51 »,
  « 71 ») se conservent et se commentent en marge HTML — sauf quand le
  numéro égaré est un appel déclaré de l'article (cas du « 51 » d'ITG,
  retiré comme balisage).
