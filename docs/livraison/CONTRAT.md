# CONTRAT — index des bibliothèques de fiches CIM-10

> Ce fichier est le contrat entre le build des bibliothèques et leurs
> consommateurs. Il vit à la racine de chaque bibliothèque ET dans le
> paquet de livraison. Source canonique : `docs/livraison/CONTRAT.md`
> du dépôt `recode-icd`.

## `format_version` : 1

## L'index fait foi

Le fichier **`index.csv`** à la racine de la bibliothèque est la seule
énumération valide des fiches. **Un fichier `.md` présent sur disque
mais absent de l'index n'existe pas** : le build nettoie son répertoire
des résidus (fiches d'anciens builds dont le code est sorti du profil)
et rapporte le compte ; toute consommation passe par l'index, jamais
par un parcours du répertoire.

Leçon fondatrice (2026-09-12, commit `5c73a22`) : 1 709 fiches
résiduelles antérieures aux profils traînaient sur disque — codes
pères interdits, codes inconnus du kit ATIH — et une archive de
livraison construite par parcours du répertoire les aurait embarquées,
en violation de l'invariant « aucun code non codable présenté comme
émissible ».

## Nom canonique et transition

- **`index.csv`** est le nom canonique.
- `_index.csv` est **déprécié** : double écriture pendant un cycle de
  livraison (contenu identique au schéma historique près), retrait au
  cycle suivant. Nouveaux consommateurs : `index.csv` uniquement.

## Noyau garanti (stable sous `format_version` 1)

| Colonne | Contenu |
|---|---|
| `code` | code CIM-10 de la fiche |
| `fichier` | chemin relatif de la fiche depuis la racine de la bibliothèque |
| `statut_mco` | statut d'autorisation au kit ATIH (`codable`, `pere_interdit`, `supprime`, `inconnu_atih`…) |
| `format_version` | version du présent contrat, constante sur toutes les lignes |

Toute rupture sur ces quatre colonnes (nom, sémantique, disparition)
incrémente `format_version` et s'annonce aux consommateurs. Les autres
colonnes (`chapter`, `libelle`, `has_*`, `type_mco`,
`source_existence`, `classe_generation`, `nb_chars`, `n_enfants`…)
sont informatives et peuvent évoluer sans incrément — s'y coupler,
c'est accepter de suivre les évolutions du dépôt.

## Sémantique `tronc_composition` (bibliothèque `generation`)

`classe_generation` vaut `emissible` ou `tronc_composition`. Un tronc
de composition est une catégorie du chapitre XX (`W00`…) **non codable
seule** : le code émis se compose du tronc, du lieu (4ᵉ caractère) et
de l'activité (5ᵉ caractère), et la fiche du tronc porte la table de
composition. **Pour tirer un code à générer, filtrer
`classe_generation == "emissible"`** ; pour résoudre un code composé
(`W0009`), passer par `recode-icd resoudre`, jamais par une jointure
manuelle.

## Canal officiel des consommateurs externes

Le canal officiel est le **paquet de livraison versionné**
(`scripts/preparer_livraison.py` — archive nommée
`<commit court>_<millésime kit>`, construite depuis l'index), **pas le
répertoire `outputs/` du dépôt**, qui est un espace de travail sans
garantie de stabilité entre deux commits.

Consommateurs connus : **fictomed** (CHU Brest), **Stream** (AP-HP).
Tout nouveau consommateur se déclare ici.

## Historique (confirmé contre le git log)

- `_index.csv` existe depuis le 2026-06-07 (`2edf6c5`) ;
- la décision D4 (profils, `4a35d67` du 2026-09-05, mergée le
  2026-09-06) a établi **un index PAR bibliothèque** (autoportance) ;
- le piège des résidus hors index a été attrapé à la livraison du
  2026-09-12 (`5c73a22`) — d'où le présent contrat : nom canonique,
  noyau garanti, nettoyage par le build, canal officiel.
