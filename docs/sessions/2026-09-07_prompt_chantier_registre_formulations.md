# Prompt de commande — chantier « registre des formulations » (archivé)

> Prompt de RF reçu le 2026-09-07, archivé tel quel (consigne
> d'archivage des prompts de chantier). Exécution : phase 1 le
> 2026-09-07, verdicts RF et phase 2 le 2026-09-09 — récap dans
> `2026-09-09_chantier_registre_formulations.md`.

---

Chantier « registre des formulations » : filtre déclaré des termes archaïques

Nouveau chantier, léger et borné : retirer des Formulations cliniques
alternatives les formulations de registre archaïque (vocabulaire de
certificat de décès, terminologie désuète — « apoplexie congestive »,
« rachitis », « misère physiologique »…) qui dégradent la qualité des
fiches pour la génération. Cas d'école : la fiche I64, dont la section
est dominée par le nuage « apoplexie » de l'Index vol3.

Préalable : vérifie l'état de main — si le palier 3 de la couverture
ATIH (feat/couverture-atih) n'est pas encore mergé, merge-le d'abord
(accord donné). Puis branche feat/registre-formulations depuis main.
Contexte : section chapter_policy du CLAUDE.md (R3, listes d'exclusion
déclarées, familles de sources), et la doctrine générale — on ne devine
pas, on déclare ; la relecture humaine valide ; jamais d'amputation
(une formulation s'écarte entière, ne se réécrit pas).

Périmètre — deux bornes non négociables

Le filtre s'applique à la SECTION FORMULATIONS uniquement. Le Périmètre
clinique du code (libellés, inclusions OFS/ANS) reste intouché — on ne
modernise pas les libellés officiels.

Les sources OFS et ANS ne sont JAMAIS filtrées (règle R1 existante). Le
filtre vise les familles Index, CepiDc, AP-HP (et, plus tard, LLM — le
point d'application doit être prêt à la couvrir, testé par fixture
comme le flag generation_llm l'a été).

Phase 1 — liste candidate (aucune modification des livrables)

Produis un CSV de relecture des formulations candidates à l'écart, au
niveau FORMULATION ENTIÈRE (jamais au niveau terme). Deux signaux à
croiser, chaque ligne indiquant lequel l'a produite :

Sondes lexicales : balayage des synonymes (hors OFS/ANS) par une liste
de termes sondes que tu élargiras — amorce mesurée :
apoplexie/apoplectique, ramollissement, rachitis, catarrhe, tabès,
crétinisme, ictus, hydropisie, paralysie générale, sénilité, croup,
muguet, hystérie, neurasthénie, engorgement, scrofule/scrofuleu,
chlorose, phtisie, idiotie, imbécillité, folie, mongolisme,
consomption, athrepsie, danse de saint-guy, congestion cérébrale,
embarras gastrique, fièvre puerpérale, gâtisme, misère physiologique,
coup de sang, fluxion, chorée de sydenham. ⚠ La sonde n'est PAS un
verdict : « commotion cérébrale », « folie à deux », « muguet buccal »,
« tabès », « ictus amnésique », « engorgement du sein » sont du
vocabulaire vivant — c'est précisément pourquoi la granularité est la
formulation et le verdict humain.

Signal d'isolement : formulations présentes uniquement dans l'Index
et/ou CepiDc, absentes de toute source contemporaine (AP-HP, OFS, ANS)
pour le même code — à ne lister que si elles portent aussi une sonde OU
sur proposition motivée (pas de liste de dizaines de milliers de
lignes : le signal seul ne suffit pas).

Colonnes : code, formulation (forme rendue ET forme source), source,
signal (sonde:<terme> | isolement), proposition (ecarter | garder),
motif en une ligne. Export dans scripts/explore/relectures/ selon la
convention existante (colonne version_regle). Rapporte la volumétrie
par source et par chapitre, et la liste des fiches dont la section
serait vidée ou réduite à ≤ 2 formulations si toutes les propositions
« ecarter » étaient retenues.

STOP — soumission du CSV à la relecture de RF. Son verdict ligne à
ligne fait foi ; c'est un partage clinicien (archaïque vs vivant), pas
lexical.

Phase 2 — implémentation, après le verdict

La liste validée devient une famille d'exclusion DÉCLARÉE :
referentials/curation/registre_formulations.yaml (formulations
écartées, forme source exacte, motif, décision RF datée), consommée par
l'assemblage des fiches au même titre que les exclusions R3. Aucune
règle en dur ; le CSV maître est INTOUCHÉ (c'est un filtre de rendu,
comme toute la chapter_policy).

Tests : dorés pris dans la liste validée — au moins une formulation
écartée ET une formulation gardée portant le même terme sonde
(préserver le vivant est aussi important qu'écarter l'archaïque) ; le
point d'application couvre la future famille LLM (fixture) ; OFS/ANS
non filtrés (contre-test) ; fiche témoin I64 avant/après.

Rapport de re-mesure : par chapitre, formulations écartées ; liste des
fiches à section vidée ou quasi-vidée (≤ 2) après filtre — ce fichier
est L'ENTRÉE DU CHANTIER SYNONYMES LLM (trous de couverture réels), à
committer dans docs/analyses/ avec une note d'une page.

Rebuild des bibliothèques, doc (CLAUDE.md : la famille d'exclusion, le
pitfall « sonde ≠ verdict — granularité formulation, validation
clinicienne »), récap de session, archivage de ce prompt (consigne
n°9).

Merge sur accord explicite de RF. Référence de tests : l'état de main
post-palier 3 (vérifie le compte).
