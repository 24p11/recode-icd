# Backlog — Taille du CSV maître versionné

> Statut : **à instruire**, pas urgent. Signalé le 2026-08-09 lors du push
> du merge CepiDc.

## Constat

`referentials/processed/inclusions_exclusions_synonymes.csv` pèse
**53,15 Mo** depuis l'intégration de CepiDc (321 097 lignes, contre
199 970 et ~40 Mo auparavant).

GitHub l'a signalé au push :

```
remote: warning: File referentials/processed/inclusions_exclusions_synonymes.csv
        is 53.15 MB; this is larger than GitHub's recommended maximum file
        size of 50.00 MB
```

Deux seuils à connaître :

| Seuil | Valeur | Effet |
|---|---|---|
| Recommandation GitHub | 50 Mo | avertissement au push, rien de bloquant |
| **Limite dure GitHub** | **100 Mo** | **push refusé** |

On est donc à ~53 % de la marge. Ce n'est pas un problème aujourd'hui, mais
le fichier ne fait que croître : chaque source ajoutée (synonymes LLM Mistral,
millésime CepiDc ultérieur, nouvelles feuilles AP-HP) le rapproche du mur. Un
ordre de grandeur : CepiDc seul a ajouté 13 Mo. Deux ou trois apports de cette
taille suffisent à bloquer les pushs.

Autre coût, moins visible : le fichier est réécrit intégralement à chaque
build, donc **chaque régénération ajoute ~53 Mo à l'historique git**, même
quand le contenu bouge peu. Le dépôt grossit vite.

## Deux options à arbitrer

### Option A — Git LFS

Déplacer le CSV (et éventuellement les gros Parquets) vers Git LFS.

- **Pour** : le fichier reste « dans le dépôt » du point de vue de
  l'utilisateur, `git clone` continue de le fournir, aucun changement dans les
  scripts ni la documentation. Plus de limite de taille pratique.
- **Contre** : dépendance à `git-lfs` sur toute machine qui clone (une étape
  d'installation de plus dans la reprise sur nouveau poste, cf
  `docs/sessions/2026-08-09_etat_des_lieux_reprise.md`). Quotas LFS de GitHub
  à surveiller (gratuit : 1 Go de stockage, 1 Go/mois de bande passante — le
  dépôt les dépasserait vite avec des régénérations fréquentes). La migration
  de l'historique existant est intrusive (réécriture).

### Option B — dé-versionner le CSV, ne garder que les Parquets

Le CSV maître est **entièrement reconstructible** :

```bash
uv run recode-icd build flat-csv
```

à partir de `merged_codes`, `propagated_notes`, `sibling_exclusions`,
`owl_codes`, `ofs_codes`, `dagger_asterisk` et `external_to_add` — tous
committés et bien plus compacts (826 Ko à 3,3 Mo chacun).

- **Pour** : règle le problème à la racine, allège l'historique, et le
  pipeline est désormais **prouvé déterministe** (cf commit `fc42373` : deux
  builds successifs produisent des octets identiques), donc la reconstruction
  est fiable et vérifiable.
- **Contre** : le CSV est le **livrable principal** du projet, celui que les
  consommateurs en aval (recode-scenario, analyses ad hoc) attendent. Le
  retirer du dépôt impose une étape de build à quiconque le veut, et casse
  l'usage « je clone et je lis le CSV ». Les tests de régression le lisent
  aussi (`csv_final_df`) : il faudrait soit le générer en amont de la suite,
  soit basculer ces tests sur les Parquets.

### Piste intermédiaire

Publier le CSV comme **artefact de release GitHub** plutôt que comme fichier
versionné : il reste téléchargeable en un lien, sans peser sur l'historique,
et le dépôt ne garde que les Parquets. Combine l'essentiel des avantages des
deux options, au prix d'une étape de publication à automatiser.

## Ce qui déclenche l'arbitrage

À trancher **avant** l'intégration des synonymes LLM Mistral, qui ajouteront
un volume du même ordre que CepiDc. Vérification à faire à ce moment-là :

```bash
ls -lh referentials/processed/inclusions_exclusions_synonymes.csv
```

## Mise à jour 2026-09-06 (chantier couverture ATIH, palier 2)

Le CSV pèse désormais **55,9 Mo** (338 623 lignes après D2) : GitHub
avertit au push que le seuil recommandé de 50 Mo est dépassé. Décision
RF : le backlog devient concret mais **ne s'ouvre pas en vol** ; il est
versé au chantier « revue d'architecture » qui suivra la couverture.
Réponse attendue là-bas : **la formalisation des deux couches** — le
CSV de construction peut se partitionner ou passer sous Git LFS sans
toucher l'interface de consommation (fiches, parquets, résolveur) — et
non un amaigrissement à la hache du CSV.

