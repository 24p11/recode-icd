# Message correctif — chantier notes OFS/ANS : réémission en v3 (archivé)

> Message de RF reçu le 2026-09-14, archivé tel quel. Sa passe v2 est
> suspendue ; le v3 corrige l'alignement (jointure par code seul +
> contrôle plein texte) et le critère (conventions opérantes vs
> présentationnelles), intègre ses dorés, et consigne le cadrage des
> trois usages des fiches au CLAUDE.md.

---

Ma passe de relecture du v2 est SUSPENDUE : elle a détecté dès ses
premières lignes deux défauts, un d'alignement et un de critère.
Corrige les deux et réémets un v3 ; ma passe reprendra dessus. Mes
annotations déjà posées sur le v2 sont à reporter.

1. Défaut d'alignement — fausses « abandonnées » : les notes de bloc
(D00-D09) et (D37-D48), marquées OFS-seul abandonnées, existent dans
l'ANS 2025 (rubriques note sur les plages nues, texte modernisé).
Normaliser les plages AVANT jointure ; joindre par code seul,
rapprocher la classe en second ; contrôle plein texte systématique des
OFS-seul restantes (colonne controle_plein_texte) ; rapporter la
nouvelle provenance et le compte de fausses abandonnées. B95-B97 reste
un vrai témoin d'absence (vérifié : aucune rubrique ANS).

2. Défaut de critère — conventions opérantes : la règle
convention_classement → non_rendue en bloc est trop grossière.
Exemples à RENDRE : (I20-I25) laps de temps I21/I22/I25 ; (J00-J99)
localisation la plus basse ; (K40-K46) hernie gangrène > occlusion ;
(L20-L30) dermite = eczéma ; (M15-M19) ostéo-arthrite = arthrose ;
(O20-O29) O24/O25 pendant l'accouchement. La leçon ANT-01 vise les
descentes NON BORNÉES, pas les notes de bloc bornées. Nouveau critère
sur toute la famille : opérante (définition, équivalence, priorité,
périmètre, résolution) → rendue ; présentationnelle → non_rendue.
Cadrage : les fiches servent trois usages (générer, vérifier,
reconnaître).

3. Verdicts rendus, dorés : (D00-D09)/(D37-D48) description_clinique
texte ANS, destination bibliothèque catégories, héritage à instruire
en phase 2 (cas D06) ; les six exemples du point 2 : rendue.

4. Équivalences terminologiques : candidates au vivier Formulations —
chantier synonymes LLM, pas ici.

5. Séquencement : contrat-index merge en premier ; phase 2 des notes
rebasera dessus. Le v3 est un livrable de phase 1, commit sur
feat/notes-ofs, soumission pour passe unique.
