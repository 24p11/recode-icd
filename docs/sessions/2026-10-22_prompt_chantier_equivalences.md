# Prompt de commande — chantier « dictionnaire d'équivalences » (archivé)

> Brief de RF reçu le 2026-10-22 (consigne d'archivage). Chantier de
> CONCEPTION : analyser, mesurer, proposer des options (points 1, 2,
> 4), ne rien mettre en œuvre. Analyse :
> `docs/analyses/2026-10-22_equivalences_termes_conception.md`.

---

# Ouverture d'un chantier recode-icd : un dictionnaire d'équivalences entre mots pour `codeur`

`codeur` (24p11/codeur, consommateur officiel, livraison
`65701d6_atih-2025` chargée) est terminé en v1 : surlignage, proposition
de codes par LLM, boucle de correction, et une recherche de codes
appuyée sur les formulations livrées (par début de code ; par morceaux —
tous les morceaux dans la formulation, accents/casse ignorés, ≤ 3
lettres en début de mot seulement, classement mot entier > début de
mot > libellé officiel > autre > plus courte, codables seulement ; par
trigrammes en secours).

Problèmes constatés : (1) les mots ne se combinent pas (« HTA
pulmonaire » ne trouve rien alors qu'« hypertension artérielle
pulmonaire » existe) ; (2) les variantes ne se rejoignent pas
(« tumeur » vs « tumoral » — le libellé LLM « Fracture pathologique au
cours d'une tumeur maligne secondaire de l'os » n'a pas retrouvé M907
« Fracture osseuse au cours de maladies tumorales ») ; (3) les
abréviations courtes sont peu sélectives (« FA » → 200 codes).

Attente : des correspondances entre mots ou expressions, INDÉPENDANTES
des codes, pour élargir la recherche (« hta » OU « hypertension
artérielle ») ET « pulm ». Pistes : format simple (terme, equivalent,
type, sens, source, statut, version) ; ambiguïtés (IRC, IC, PR) ;
sources (formulations existantes, terminologies ouvertes sous licence,
LLM toujours relu, usage des testeurs — codeur journalise texte tapé /
résultats / code choisi et exportera des candidats) ; circuit des
ajouts (jamais deux dictionnaires divergents — recode-icd seule
source ?) ; couverture (centaines d'abréviations MCO d'abord) ; autres
usages (boucle de correction, candidats de prompt, autres
consommateurs).

Attendu : confronter à l'état de recode-icd ; mesurer (équivalences
auto-extractibles des formulations et leur qualité, abréviations
distinctes, fréquences) ; conception pour les points 1, 2 et 4 avec
options sans trancher ; préparer le brief Claude Code. Doctrine
habituelle : on ne devine pas, on déclare ; relecture humaine
structurelle ; artefacts calculés jamais modifiés à la main ; contrat
mis à jour.
