# Prompt de commande — chantier « besoins de codeur » (archivé)

> Prompt de RF reçu le 2026-10-18 (consigne d'archivage). Chantier de
> CONCEPTION : analyser et mesurer, proposer des options, ne rien
> mettre en œuvre. Analyse :
> `docs/analyses/2026-10-18_besoins_codeur_conception.md`.

---

# Ouverture d'un chantier recode-icd : les besoins de l'outil de codage `codeur`

Je construis `codeur` (dépôt `24p11/codeur`), un prototype d'outil de
codage CIM-10 assisté par un LLM, destiné à une centaine de testeurs.
`codeur` consomme une livraison de recode-icd : l'index des codes, les
fiches d'identité des codes, et les formulations (synonymes). Traiter
les problèmes à la source, dans recode-icd.

Usages : (1) vérifier qu'un code est codable (index) ; (2) corriger un
code non codable proposé par le LLM (codes codables descendants, avec
libellés) ; (3) revue du codage par le LLM (fiche de chaque code
retenu) ; (4) recherche d'un code par mots-clés (formulations) ;
(5) codes candidats dans le prompt (formulations).

Règles codeur : codes sans point, extension PMSI collée (K409, Z992+0,
E11ni) ; seul le code complet fait foi (Z992 n'est pas une variante
acceptable de Z992+0 : code non codable, RUM en erreur) ; fiches de
catégorie non utilisées ; liste des codables tirée de l'index, jamais
de la présence d'un fichier.

Boucle de correction : signaler + fournir les codables possibles
(descendants ; à défaut la catégorie si courte ; sinon filtrage par
formulations) ; au plus deux tours ; dernier recours le testeur.

Problèmes constatés (100 000 CRH synthétiques mistral-large) : les LLM
omettent les extensions PMSI (2 202 cas : Z992 pour Z992+0, K861 pour
K861+8, J961 pour J961+0) ; arrondissent (247 cas : M14/M146 pour
M1467 ; M142 pour M1427 ; R521 pour R5210) ; aucune invention, que des
troncatures. Difficultés : catégories longues (fractures, extensions
multiples) ; sens des extensions (+0, +1, +8, ni…) pas explicite ;
certaines fiches n'apportent rien au-delà du libellé.

Attentes : (1) index complet et sans ambiguïté, seule source des codes
pour codeur (tous les codes, indicateur codable, libellé, statuts MCO,
forme codeur, versions) ; (2) fiches « utiles ou vides » ; (3) fiches
de navigation des nœuds non codables (liste compacte + critère qui
départage) ; (4) traitement des catégories trop longues (axe
discriminant) ; (5) explication des extensions PMSI ; (6) budget de
taille par fiche (≈ 15 fiches par appel) ; (7) export des formulations
(code complet, formulation, source).

Attendu de la conversation : confronter à l'état de recode-icd ;
mesurer avant de décider (codables par catégorie, nœuds intermédiaires,
fiches vides, tailles en tokens) ; proposer une conception pour les
points 2 à 5 avec options et compromis, sans trancher ; préparer le
brief Claude Code. Doctrine habituelle : on ne devine pas, on déclare ;
relecture humaine structurelle ; artefacts calculés jamais modifiés à
la main ; contrat d'interface mis à jour, codeur nouveau consommateur.
