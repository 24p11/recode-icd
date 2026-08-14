# Base de connaissance des recommandations du guide méthodologique MCO : note de conception

*Note de travail — 2026-08-09. Destinée à `docs/analyses/` du projet
recode-icd, en préparation d'un futur chantier. Source étudiée : Guide
méthodologique de production des informations relatives à l'activité
médicale et à sa facturation en MCOO, version provisoire, décembre 2025
(applicable au 1er janvier 2026), 164 pages, ATIH.*

## 1. Problème

On souhaite enrichir les fiches descriptives avec les consignes de codage du
guide méthodologique. Or le guide n'est pas organisé par code : ses
consignes sont organisées par **situation clinique**, chacune mobilisant
plusieurs codes dans des **rôles** différents (DP, DR, DAS, interdiction),
à des **granularités** variées (code précis, catégorie, plage, chapitre) et
sous **conditions**. Attacher naïvement le texte des consignes à chaque code
concerné dupliquerait massivement l'information et perdrait la sémantique
positionnelle.

Constats rédactionnels sur le guide (section AVC, chap. V pp. 78-81, et
article D62, chap. V pp. 81-82, utilisés comme cas d'étude) :

- une même consigne cite des codes en DP (« pour un AVC constitué, un code
  I60.–, I61.–, I62.– ou I63.– »), d'autres en DAS (« un code de séquelle
  I69 est placé en DAS »), d'autres en DR (« Z51.5 en DP, l'AVC en DR ») ;
- les interdictions sont fréquentes et précieuses (« le code I64 ne doit
  être employé qu'en l'absence de neuro-imagerie », « I65, I66, G46.0-2,
  I67.0-1 ne doivent pas être employés en association avec I60–I64 »,
  « dans ces conditions le code D62 ne doit pas être mentionné ») ;
- les références vont du code (Z86.70) au chapitre entier (« le DP
  appartient au chapitre XXI ») ;
- les conditions sont essentielles (« à la condition qu'elle soit confirmée
  par l'imagerie », « en l'absence de séquelles », « tant que le malade n'a
  pas quitté le champ MCO ») ;
- certains codes ne sont cités qu'en exemple illustratif (R26, F32 comme
  exemples de manifestations), d'autres sont le sujet même de la consigne
  (I69, D62).

## 2. Principe de conception

**La recommandation est l'entité première ; les codes sont des cibles via
une table d'association.** C'est le pattern déjà éprouvé dans le projet avec dagger_asterisk.parquet : un livrable séparé, seule source de vérité des consignes. Une consigne y est définie une fois ; les fiches en matérialisent le texte à chaque build pour rester autonomes (elles sont injectées telles quelles dans les prompts) — cette duplication de rendu est un produit de compilation régénérable, jamais un contenu à maintenir en double. Le CSV maître n'est pas modifié — les recommandations ne sont pas une source de synonymes/inclusions, c'est une famille d'information nouvelle avec son propre livrable.

Corollaires :

- définition unique : une consigne à N codes = 1 ligne de recommandation + N lignes d'association ; toute correction se fait dans la base, jamais dans les fiches, qui sont régénérées;
- la sémantique positionnelle (DP/DR/DAS/interdit) vit dans l'association,
  pas dans le texte seul ;
- deux consommateurs distincts prévus dès la conception :
  - `cards.py` (fiches) : injecter les consignes pertinentes dans la fiche
    d'un code, pour la génération de CRH ;
  - `recode-scenario` : les rôles DP/DR/DAS sont des **contraintes de
    cohérence de scénario** (« Z51.5 en DP implique la maladie en DR »),
    usage probablement plus puissant encore que l'enrichissement textuel.

## 3. Trois couches de connaissance à ne pas mélanger

Le guide entremêle trois natures d'information ; l'extraction devra trier :

| Couche | Exemple | Destination |
|---|---|---|
| Grammaire CIM-10 générale | « et » du libellé = les deux localisations (cas K57.4) ; sens des .8/.9 ; portée des parenthèses | Préambule commun des prompts de génération (chantier distinct, déjà identifié) |
| Règles générales PMSI | définition du DP/DR/DAS, conditions de production d'un RUM, règles de séjour | Hors périmètre des fiches ; éventuellement documentation de recode-scenario |
| Consignes spécifiques à des codes/situations | règles AVC, article D62, consignes par chapitre CIM | **La base de connaissance objet de cette note** |

## 4. Modèle de données

### 4.1 Table `recommendations`

| Champ | Type | Description |
|---|---|---|
| `rec_id` | str | Identifiant stable, ex. `GM2026-V-AVC-04` (millésime, chapitre du guide, slug de section, n° d'ordre) |
| `millesime` | str | Édition du guide (ex. `2026-provisoire`). Le guide est annuel : le millésime est structurel, pas décoratif |
| `localisation` | str | Chapitre/section/page du guide, pour audit et retour au texte |
| `situation` | str | Situation clinique en clair (ex. « AVC — séjour pour récidive ») |
| `type` | enum | `regle_position` \| `interdiction` \| `condition_emploi` \| `definition` \| `regle_association` |
| `texte` | str | Consigne condensée, autoportante, en français |
| `condition` | str \| null | Condition d'application si elle porte sur toute la consigne |

### 4.2 Table `recommendation_codes`

| Champ | Type | Description |
|---|---|---|
| `rec_id` | str | Clé vers `recommendations` |
| `code_expr` | str | Expression de codes : code (`Z86.70`), catégorie (`I69`), notation à tiret (`I63.–`), plage (`I60-I64`), chapitre (`XXI`) |
| `role` | enum | **huit modalités**, cf. catalogue ci-dessous |
| `centralite` | enum | `sujet` (le code est l'objet de la consigne) \| `exemple` (cité à titre illustratif) |
| `condition` | str \| null | Condition propre à ce code dans la consigne, si plus fine que la condition globale |

**Catalogue des rôles** (mis à jour le 2026-08-14 — les deux modalités
`interdit_DP` / `interdit_DR` avaient été décidées mais jamais reportées
ici) :

| Rôle | Sens | Exemple type |
|---|---|---|
| `DP` | le code occupe la position de diagnostic principal | « le DP est codé Z86.70 » |
| `DR` | position de diagnostic relié | « Z51.5 en DP, l'AVC en DR » |
| `DAS` | position de diagnostic associé | « un code de séquelle I69 est placé en DAS » |
| `interdit` | l'**emploi même** du code est proscrit dans la situation | « dans ces conditions le code D62 ne doit pas être mentionné » |
| `interdit_association` | le code est proscrit **en association** avec une autre cible de la même consigne | « I65, I66 ne doivent pas être employés en association avec I60–I64 » |
| `interdit_DP` | le code reste employable, mais **jamais en DP** | « les codes du chapitre XX ne doivent jamais être utilisés en DP ou DR » |
| `interdit_DR` | le code reste employable, mais **jamais en DR** | *idem* |
| `contexte` | le code situe la consigne sans être ce qu'elle prescrit | `I60-I64` dans « ne pas associer X à un AVC constitué » |

> **`interdit` ≠ `interdit_DP`/`interdit_DR`.** Le premier proscrit le
> code ; les seconds ne proscrivent qu'une **position**. Les confondre
> ferait disparaître des codes parfaitement légitimes en DAS — c'est
> précisément le cas du chapitre XX, dont les codes sont obligatoires en
> DAS et interdits en DP et en DR.

**`centralite` est binaire, et volontairement.** `sujet` = le code est
l'objet de la consigne ; `exemple` = il n'est cité qu'en illustration.
Sans ce champ, la fiche de F32 recevrait la consigne AVC au seul motif
que F32 y figure comme exemple de manifestation. Une graduation plus
fine (« principal », « secondaire », « accessoire ») a été écartée :
elle n'est pas décidable à la lecture du guide, et le seul arbitrage
dont le rendu a besoin est « cette consigne a-t-elle sa place dans cette
fiche ? ».

### 4.3 Résolution vers les codes feuilles

L'expansion de `code_expr` réutilise l'outillage existant :

- expansion catégorie/plage/chapitre → codes feuilles via le nested set
  (`left`/`right`) déjà en place ;
- en cas de consignes multiples matchant un code, priorité par
  spécificité : code > catégorie > bloc/plage > chapitre — la même règle
  de résolution que la chapter_policy (convention unique à documenter) ;
- au build des fiches : plafond du nombre de recommandations par fiche
  (mécanisme analogue à R2), tri par `centralite` (sujet avant exemple)
  puis spécificité ; les `centralite=exemple` peuvent être exclus des
  fiches par défaut (paramètre).

## 5. Preuve de concept : remplissage manuel

### 5.1 Consignes AVC (guide chap. V, pp. 78-81)

`recommendations` (extrait) :

| rec_id | situation | type | texte (condensé) | condition |
|---|---|---|---|---|
| GM2026-V-AVC-01 | AVC/AIT à la phase aigüe — séjour initial | regle_position | Le DP emploie G45.– pour un AIT, I60.– à I63.– pour un AVC constitué ; ces codes restent employés par toutes les unités MCO successives de la première prise en charge | Première prise en charge, patient n'ayant pas quitté le champ MCO |
| GM2026-V-AVC-02 | AVC — emploi de I64 | condition_emploi | I64 n'est employé qu'en l'absence d'examen de neuro-imagerie, jamais en association avec un code plus précis | Absence de neuro-imagerie |
| GM2026-V-AVC-03 | AVC constitué — artère et mécanisme | interdiction | G46.0-G46.2, I65, I66, I67.0, I67.1 ne doivent pas être employés en association avec I60–I64 pour décrire l'artère ou le mécanisme (exclusion CIM-10 en cas d'infarctus) | En association avec un AVC constitué |
| GM2026-V-AVC-04 | AVC — récidive | regle_position | Une récidive confirmée par l'imagerie est codée comme un AVC à la phase aigüe | Confirmation par imagerie |
| GM2026-V-AVC-05 | AVC — surveillance négative sans séquelle | regle_position | DP = Z86.70 ; pas de DR | Aucune affection nouvelle, aucune séquelle |
| GM2026-V-AVC-06 | AVC — soins palliatifs | regle_position | DP = Z51.5 ; le code de l'AVC (aigu ou séquelle selon la phase) en DR | — |

`recommendation_codes` (extrait pour AVC-01, AVC-03, AVC-05, AVC-06) :

| rec_id | code_expr | role | centralite | condition |
|---|---|---|---|---|
| GM2026-V-AVC-01 | G45 | DP | sujet | AIT |
| GM2026-V-AVC-01 | I60-I63 | DP | sujet | AVC constitué |
| GM2026-V-AVC-03 | I60-I64 | contexte | sujet | — |
| GM2026-V-AVC-03 | G46.0-G46.2 | interdit_association | sujet | — |
| GM2026-V-AVC-03 | I65 | interdit_association | sujet | — |
| GM2026-V-AVC-03 | I66 | interdit_association | sujet | — |
| GM2026-V-AVC-03 | I67.0 | interdit_association | sujet | — |
| GM2026-V-AVC-03 | I67.1 | interdit_association | sujet | — |
| GM2026-V-AVC-05 | Z86.70 | DP | sujet | — |
| GM2026-V-AVC-06 | Z51.5 | DP | sujet | — |
| GM2026-V-AVC-06 | I60-I64 | DR | sujet | phase initiale |
| GM2026-V-AVC-06 | I69 | DR | sujet | phase séquellaire |

Note : dans la consigne « aggravation/complication » (situation 3 du
guide), R26, F32, G40, G41, F01 seraient enregistrés avec
`centralite=exemple` — c'est exactement le cas qui motive ce champ : la
fiche de F32 n'a pas vocation à recevoir la consigne AVC, sauf paramétrage
explicite.

### 5.2 Article D62 (anémie posthémorragique aigüe, guide chap. V, pp. 81-82)

| rec_id | situation | type | texte (condensé) | condition |
|---|---|---|---|---|
| GM2026-V-D62-01 | Compensation peropératoire normale des pertes sanguines | interdiction | D62 ne doit pas être mentionné lorsque la transfusion compense les pertes attendues d'une intervention par nature hémorragique | Restitution volémique conforme aux règles de l'art (SFAR), pertes attendues |
| GM2026-V-D62-02 | Hémorragie périopératoire inhabituelle | condition_emploi | D62 est employé lorsque l'anémie résulte d'un phénomène hémorragique inhabituel (lésion, complication) | Saignement inhabituel documenté |

Association : `(GM2026-V-D62-01, D62, interdit, sujet)` et
`(GM2026-V-D62-02, D62, DAS, sujet)`. Cas d'école du bénéfice attendu
pour la génération : la fiche D62 enrichie apprend au générateur qu'une
transfusion peropératoire banale ne justifie pas de décrire une anémie
posthémorragique — précisément le type de mention codable parasite qui
corrompt un corpus annoté.

## 6. Usage dans les fiches (esquisse)

Section nouvelle de la fiche, distincte des Formulations :

```
## Consignes de codage (guide méthodologique 2026)
- [GM2026-V-AVC-02] I64 n'est employé qu'en l'absence de neuro-imagerie,
  jamais en association avec un code plus précis.
- [GM2026-V-AVC-03] Ne pas associer G46.0-G46.2, I65, I66, I67.0, I67.1
  à un code I60–I64 pour décrire l'artère ou le mécanisme.
```

L'identifiant entre crochets assure la traçabilité vers le guide (principe
« jamais d'agrégation silencieuse » du projet). Compte tenu des résultats de
l'évaluation des fiches (cf. note du 2026-08-09 sur l'apport des fiches et
la littérature contexte/négation), les consignes de type `interdiction`
sont candidates prioritaires à un usage en **vérification** (schéma
generate-then-verify) plutôt qu'en injection amont.

## 7. Chantier d'extraction (à cadrer plus tard)

- Extraction LLM-assistée section par section du PDF, avec validation
  humaine ; le schéma generate-then-verify testé sur Stream/notion est
  directement réutilisable (générer les lignes candidates, vérifier
  contre le texte source, réviser) ;
- commencer par les chapitres à plus forte densité de consignes
  spécifiques (chapitre du guide sur le codage de la morbidité et
  articles de situations cliniques), pas par une passe exhaustive ;
- le millésime `2026-provisoire` devra être re-vérifié à la publication de
  la version définitive (diff des sections extraites) ;
- livrables : `referentials/processed/recommendations.parquet` +
  `recommendation_codes.parquet`, validés pandera, avec rapport de build
  (recommandations sans code résolu, expressions non parseables) — mêmes
  conventions que le reste du pipeline.

## 8. Questions ouvertes — **tranchées le 2026-08-14**

1. **Propagation des consignes de niveau chapitre jusqu'aux fiches
   feuilles : OUI.** La suggestion initiale (les réserver à
   recode-scenario) est écartée. Les fiches sont injectées *telles
   quelles* dans des prompts : elles doivent être autonomes, donc porter
   la consigne et non un renvoi. Le risque de bruit était réel mais il se
   traite au **rendu** — les consignes de chapitre sont regroupées en fin
   de section sous « Règles générales du chapitre » — et non en amputant
   la résolution.
2. **Conditions en texte libre**, comme envisagé. Une structuration en
   prédicats reste conditionnée à un besoin d'évaluation automatique côté
   recode-scenario.
3. **Coexistence tracée, pas de dédoublonnage.** Une consigne du guide et
   une exclusion CIM-10 qui se recoupent n'ont ni la même autorité ni la
   même portée : les fusionner ferait perdre l'une des deux. La trace
   n'ajoute **aucune colonne** au modèle — elle vit dans le rapport de
   build, colonne `recouvrement_potentiel`, et c'est une **heuristique de
   repérage pour l'audit humain, sans aucune prétention sémantique** :
   pour chaque `(rec_id, code)` de rôle `interdit` ou
   `interdit_association`, on signale les lignes d'exclusion OFS/ANS
   existantes sur ce code. Ni un dédoublonnage, ni une preuve de
   redondance : un pointeur.
