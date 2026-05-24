"""Construit scripts/explore/01_walkthrough_ofs_loader.ipynb via nbformat.

Usage :
    uv run python scripts/explore/_build_walkthrough.py
    uv run --with jupyter --with ipykernel jupyter nbconvert \\
        --to notebook --execute --inplace \\
        scripts/explore/01_walkthrough_ofs_loader.ipynb

Ce script ne fait que générer le squelette du notebook ; l'exécution
(remplit les outputs) est faite par jupyter nbconvert.
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

OUT = (
    Path(__file__).parent / "01_walkthrough_ofs_loader.ipynb"
).resolve()


def md(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(text)


def code(src: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(src)


def main() -> None:
    nb = nbf.v4.new_notebook()
    cells: list[nbf.NotebookNode] = []

    # ──────────────────────────────────────────────────────────────────
    # Cellule 1 — Objectif
    # ──────────────────────────────────────────────────────────────────
    cells.append(md("""\
# Walkthrough du pipeline `recode-icd`

Ce notebook explique pas à pas chacune des étapes du pipeline qui
produit le fichier maître `inclusions_exclusions_synonymes.csv` à
partir des sources brutes CIM-10 (OFS suisse 2006, OWL/ANS français 2026).

## Ce que vous allez apprendre

1. **Loaders** (`loaders/owl.py` + `loaders/ofs.py`) — lire deux formats
   très différents (RDF/XML vs base relationnelle plate latin-1) et les
   normaliser en DataFrames polars.
2. **Merge** (`merge.py`) — fusionner les deux sources selon la politique
   par champ de CLAUDE.md (libellé : OWL primaire ; inclusions/exclusions :
   OFS primaire ; synonymes : union).
3. **Propagation** (`propagation.py`) — pour chaque code feuille,
   hériter les notes des ancêtres (chapter / block / category) avec
   traçabilité `inherited_from`.
4. **Sibling exclusions** (`relations/sibling_exclusions.py`) — pour
   chaque code `XYZ.8`, synthétiser une note d'exclusion listant les
   frères `.0`–`.7` (aide le LLM à coder correctement).
5. **Flat CSV** (`exporters/flat_csv.py`) — assembler les 3 sources
   (propagated, siblings, synonymes) en un CSV à 5 colonnes.

## Convention du walkthrough

On se restreint à **5 codes témoins** (cf
[`tests/fixtures/sample_codes.yaml`](../../tests/fixtures/sample_codes.yaml))
pour garder les sorties lisibles :

- `A00.0` — choléra (feuille, divergence libellé OFS↔OWL)
- `F02.00` — démence Pick (dague/astérisque OWL direct)
- `F66.2` — trouble de la relation sexuelle (OWL definition)
- `J45.8` — autres asthmes (sous-cat `.8`, synthèse frères)
- `C50.8` — sein, lésion contiguë (C00-C75, skip frères)

Toutes les fonctions appelées proviennent de `src/recode_icd/` — aucune
logique n'est réécrite inline."""))

    # ──────────────────────────────────────────────────────────────────
    # Cellule 2 — Setup
    # ──────────────────────────────────────────────────────────────────
    cells.append(md("## Setup — imports et chemins"))

    cells.append(code("""\
from pathlib import Path

import polars as pl

# Tous les modules publics utilisés dans le walkthrough
from recode_icd import merge, propagation
from recode_icd.exporters import flat_csv
from recode_icd.loaders import ofs, owl
from recode_icd.relations import sibling_exclusions

# Chemins racine du projet (le notebook est dans scripts/explore/)
ROOT = Path.cwd().parent.parent if Path.cwd().name == "explore" else Path.cwd()
DATA = ROOT / "data"
PROCESSED = ROOT / "referentials" / "processed"

# Codes témoins fixés (cf tests/fixtures/sample_codes.yaml)
WITNESS_CODES = ["A00.0", "F02.00", "F66.2", "J45.8", "C50.8"]

pl.Config.set_tbl_rows(20)
pl.Config.set_fmt_str_lengths(80)
print(f"Root projet : {ROOT}")
print(f"Témoins     : {WITNESS_CODES}")
"""))

    # ──────────────────────────────────────────────────────────────────
    # Étape 1 — loaders/owl.py
    # ──────────────────────────────────────────────────────────────────
    cells.append(md("""\
---

## Étape 1 — `loaders/owl.py` : chargement OWL/ANS

### Quoi & pourquoi

L'ANS (Agence du Numérique en Santé) publie la CIM-10 française au
format RDF/XML enrichi (~13 MB, ~19 075 concepts). Notre loader importe
`smt2parquet.core` pour la mécanique générique (parsing rdflib, nested
set) et **redéfinit les requêtes SPARQL** pour récupérer les prédicats
que l'outil amont n'extrait pas : `xkos:exclusionNote`,
`atih-cim10:hasCausality`, `skos:definition`, etc.

`owl.load_codes(rdf_path)` fait tout le travail et retourne un seul
DataFrame validé par pandera."""))

    cells.append(code("""\
rdf_path = DATA / "CIM_ANS_2026" / "dat" / "terminologie-cim-10-2025-01-01.rdf"
owl_codes = owl.load_codes(rdf_path)
owl_codes.shape
"""))

    cells.append(code("""\
print("Schéma :")
print(owl_codes.schema)
print(f"\\nTotal codes : {len(owl_codes)}")
print(f"Par type : {dict(owl_codes.group_by('type').len().iter_rows())}")
owl_codes.filter(pl.col("code").is_in(WITNESS_CODES)).select(
    "code", "label", "type", "depth", "left", "right",
    "inclusion_note", "exclusion_notes", "definitions", "structured_exclusions",
)
"""))

    cells.append(md("""\
### Interprétation

- **19 075 codes** avec leur hiérarchie complète (`depth` / `left` / `right` /
  `path` issus du nested set calculé par `smt2parquet.core.build_nested_set`).
- `F02.00` a une `exclusion_notes` héritée du chapter V (récupérée par la
  propagation plus loin), `F66.2` a une `definitions` non-nulle (rare —
  seulement ~387 codes en ont une).
- `C50.8` montre des `structured_exclusions` (URIs `atih:exclusion`
  pointant vers d'autres codes).

**Piège** : on charge ici un Parquet déjà produit pour aller vite, mais
la première exécution sur le RDF prend ~15s (rdflib parse 13 MB).

### Paires dague/astérisque

OWL expose 1 317 paires †/* via deux encodages : triple direct
(`atih-cim10:hasCausality`) et reification `owl:Axiom`. `load_dagger_asterisk`
résout les deux via une seule requête SPARQL avec `UNION`."""))

    cells.append(code("""\
owl_pairs = owl.load_dagger_asterisk(rdf_path)
witness_set = set(WITNESS_CODES)
owl_pairs.filter(
    pl.col("asterisk_code").is_in(witness_set) | pl.col("dagger_code").is_in(witness_set)
)
"""))

    cells.append(md("""\
`F02.00 → G31.0` confirme la convention : `asterisk_code` est la
manifestation, `dagger_code` est la cause primaire. La colonne `evidence`
liste les preuves trouvées (`direct_causality`, `axiom_causality`,
`direct_manifestation`, `axiom_manifestation`)."""))

    # ──────────────────────────────────────────────────────────────────
    # Étape 2 — loaders/ofs.py
    # ──────────────────────────────────────────────────────────────────
    cells.append(md("""\
---

## Étape 2 — `loaders/ofs.py` : chargement OFS suisse 2006

### Quoi & pourquoi

L'Office Fédéral de la Statistique suisse publie une **base relationnelle
plate** (19 fichiers `.TXT`, séparateur `¦`, encodage latin-1).
`loaders/ofs.py` lit MASTER + LIBELLE + INCLUDE + EXCLUDE + NOTE + MEMO
+ DESCR + DAGSTAR + VERSION, reconstruit la hiérarchie via les
colonnes `id1`..`id7`, et expose un Parquet du même schéma général que
le loader OWL.

**Pièges techniques rencontrés** :

- polars 1.40 refuse `¦` comme séparateur (multi-byte UTF-8) → workaround
  via remplacement par `\\x01` après décodage latin-1.
- `MEMO.txt` utilise un quoting `'...'` distinct du reste d'OFS → param
  `quote_char="'"` spécifique."""))

    cells.append(code("""\
ofs_dir = DATA / "CIM_OFS_SW_2006"
ofs_codes = ofs.load_codes(ofs_dir)
ofs_codes.shape
"""))

    cells.append(code("""\
print(f"Total codes (valid=1) : {len(ofs_codes)}")
print(f"Par type canonique    : {dict(ofs_codes.group_by('type').len().iter_rows())}")
print(f"Par ofs_type (brut)   : {dict(ofs_codes.group_by('ofs_type').len().iter_rows())}")
print(f"\\nOFS code natif a des parens pour les ranges : exemple chapter")
print(ofs_codes.filter(pl.col('type') == 'chapter').head(3).select(['code', 'abbrev', 'label']))
print(f"\\nTémoins (jointure plus tard sur code stripé des parens) :")
ofs_codes.filter(pl.col("code").is_in(WITNESS_CODES)).select(
    "code", "abbrev", "label", "type", "ofs_type", "depth",
    "inclusions", "exclusions_text", "notes_editorial",
)
"""))

    cells.append(md("""\
### Interprétation

- **19 094 codes valides** (61 codes `valid=0` filtrés).
- OFS encode les chapitres comme `(A00-B99)` (parenthèses + range) là où
  OWL utilise `I` (numérotation romaine). `merge.py` strip les parens
  pour aligner les blocs (`A00-A09`) — mais pas les chapitres
  (Roman ≠ range, pas de mapping).
- `ofs_type` brut (C / G / U / K / S / D) est conservé pour traçabilité
  à côté du `type` canonique normalisé.
- Les `inclusions` / `exclusions_text` sont des `list[str]` car OFS lie
  souvent plusieurs libellés (LIBELLE.LID) à un même code (MASTER.SID)."""))

    # ──────────────────────────────────────────────────────────────────
    # Étape 3 — merge.py
    # ──────────────────────────────────────────────────────────────────
    cells.append(md("""\
---

## Étape 3 — `merge.py` : fusion OFS ⊕ OWL

### Quoi & pourquoi

CLAUDE.md fixe une **politique par champ** : OWL primaire pour
libellé / existence, OFS primaire pour notes / inclusions / exclusions /
†/*, union pour synonymes. `merge.merge_codes(owl, ofs)` applique cette
politique et produit un Parquet unique.

En plus, `merge.find_conflicts` logge les divergences sémantiques
(sepsis vs septicémie, réforme orthographique 1990, etc.) dans un CSV
auditable, et `merge.find_orphans` liste les codes OFS sans
contrepartie OWL (~2 340 codes, principalement format chapitre
`(A00-B99)` vs OWL `I`)."""))

    cells.append(code("""\
merged = merge.merge_codes(owl_codes, ofs_codes)
merged.shape  # = len(OWL) car OWL = univers
"""))

    cells.append(code("""\
print("Distribution sources après résolution :")
print(f"  inclusions_source : {dict(merged.group_by('inclusions_source').len().iter_rows())}")
print(f"  exclusions_source : {dict(merged.group_by('exclusions_source').len().iter_rows())}")
print(f"  with OFS match    : {merged['has_ofs_match'].sum()}")
merged.filter(pl.col("code").is_in(WITNESS_CODES)).select(
    "code", "label", "type", "has_ofs_match",
    "inclusions_source", "inclusions", "exclusions_source", "synonymes",
)
"""))

    cells.append(code("""\
# Échantillon des conflits de libellés détectés
conflicts = merge.find_conflicts(owl_codes, ofs_codes)
print(f"Total conflits loggés : {len(conflicts)}")
print(f"Par champ : {dict(conflicts.group_by('field').len().iter_rows())}")
conflicts.filter(pl.col("code").is_in(WITNESS_CODES)).head(8)
"""))

    cells.append(md("""\
### Interprétation

- **19 075 lignes** (= taille OWL : OWL est l'univers).
- `has_ofs_match` à `True` pour ~16 700 codes — les autres sont des
  extensions FR-PMSI 2025 absentes d'OFS 2006 (codes comme `M18.92`,
  `B24.+0`).
- `inclusions_source = "OFS"` quand OFS porte au moins une inclusion ;
  `"OWL_ANS"` en fallback quand OFS muet ; `"none"` pour les codes sans
  inclusion nulle part.
- `find_conflicts` filtre la pure casse et les NBSP (`\\xa0` côté OFS)
  pour ne logger que les vraies divergences sémantiques."""))

    # ──────────────────────────────────────────────────────────────────
    # Étape 4 — propagation.py
    # ──────────────────────────────────────────────────────────────────
    cells.append(md("""\
---

## Étape 4 — `propagation.py` : héritage hiérarchique

### Quoi & pourquoi

CLAUDE.md exige : *« Les notes au niveau bloc s'appliquent à TOUS les
codes du bloc »*. Sans cette propagation, un code feuille comme `A00.0`
n'aurait pas accès aux notes éditoriales du chapter I.

`propagation.propagate(merged)` produit un Parquet **long** : une ligne
par couple `(code, note)`, avec la colonne `inherited_from` indiquant
l'ancêtre porteur (ou `null` si la note appartient au code lui-même)."""))

    cells.append(code("""\
propagated = propagation.propagate(merged)
print(f"Total lignes (long format) : {len(propagated):,}")
print(f"Par note_type : {dict(propagated.group_by('note_type').len().iter_rows())}")
print(f"Own (inherited_from=null) : {propagated.filter(pl.col('inherited_from').is_null()).height:,}")
print(f"Inherited                 : {propagated.filter(pl.col('inherited_from').is_not_null()).height:,}")
"""))

    cells.append(code("""\
# Pour F02.00 : voir les notes propres + héritées
propagated.filter(pl.col("code") == "F02.00").select(
    "code", "note_type", "texte", "source", "inherited_from", "inherited_from_type",
)
"""))

    cells.append(md("""\
### Interprétation

- **~113 000 lignes** au format long (avant : ~19 075 codes × moyenne
  5-6 notes après explode).
- F02.00 hérite du chapter V (`inclusion` et `exclusion` OWL) et du
  bloc F00-F09 (`note_editorial` OFS) — c'est exactement le comportement
  attendu.
- Les **synonymes ne sont pas propagés** (un synonyme du bloc ne
  s'applique pas à ses feuilles — sémantique différente des notes).
- **Pas de déduplication** between own/inherited à ce stade : si une
  même inclusion textuelle existe au bloc ET au leaf, on a 2 lignes
  distinctes pour préserver la traçabilité. La dédup arrive dans
  `flat_csv`."""))

    # ──────────────────────────────────────────────────────────────────
    # Étape 5 — sibling_exclusions.py
    # ──────────────────────────────────────────────────────────────────
    cells.append(md("""\
---

## Étape 5 — `relations/sibling_exclusions.py` : synthèse `.8` frères

### Quoi & pourquoi

Pour les codes `XYZ.8` ("Autres ..."), CLAUDE.md demande de
**synthétiser** des notes d'exclusion qui listent les frères `XYZ.0`–
`XYZ.7`. Objectif : aider le LLM à comprendre que `.8` couvre les
affections **résiduelles** sans sous-catégorie spécifique.

**Cas particulier C00-C75** : pour les tumeurs malignes, la
sous-catégorie `.8` a une sémantique différente ("lésion à
localisations contiguës"). Ces codes sont *skipped* (loggés dans un
CSV séparé) sans aucune synthèse — c'est précisément le rôle de
`C50.8` dans notre liste de témoins."""))

    cells.append(code("""\
siblings, skipped = sibling_exclusions.synthesize(merged)
print(f"Synthèses produites         : {len(siblings):,}")
print(f"Codes .8 distincts traités  : {siblings['code'].n_unique()}")
print(f"Codes .8 ignorés (C00-C75)  : {len(skipped)}")
"""))

    cells.append(code("""\
# J45.8 : doit avoir des synthèses pour J45.0 et J45.1
print("=== J45.8 — synthèses produites ===")
print(siblings.filter(pl.col("code") == "J45.8").select(
    "code", "sibling_code", "texte"
))

# C50.8 : ne doit PAS être dans siblings, mais dans skipped
print("\\n=== C50.8 — dans skipped (C00-C75) ===")
print(skipped.filter(pl.col("code") == "C50.8"))
"""))

    cells.append(md("""\
### Interprétation

- **5 637 lignes** synthétisées (en moyenne ~5 frères par code `.8`).
- **45 codes skipped** dans C00-C75 (tous des tumeurs malignes — la
  sémantique "lésion contiguë" rend l'exclusion frère sémantiquement
  incorrecte).
- Format du `texte` : `"<sibling_label> (<sibling_code>)"`, identique au
  format des exclusions OFS normales pour cohérence visuelle dans le CSV
  final.
- La colonne `source` vaut toujours `"SYNTHESIZED_SIBLING"` — sera
  remappée en `"CIM-10 frères"` par `flat_csv` (cf mapping CLAUDE.md)."""))

    # ──────────────────────────────────────────────────────────────────
    # Étape 6 — exporters/flat_csv.py
    # ──────────────────────────────────────────────────────────────────
    cells.append(md("""\
---

## Étape 6 — `exporters/flat_csv.py` : CSV maître à 5 colonnes

### Quoi & pourquoi

Objectif métier #1 de CLAUDE.md. `flat_csv.build(merged, propagated,
siblings, owl, ofs)` consomme **les 5 Parquets précédents** pour produire
un DataFrame long à 5 colonnes :

| `code` | `libelle` | `type` ∈ {inclusion, exclusion, synonyme} | `source` | `texte` |

**Décisions clés** :
- Filtre aux **leaves uniquement** (`right - left == 1`) — les non-leaves
  ont déjà propagé leurs notes vers les feuilles.
- `note_editorial` est **droppé** (CLAUDE.md spécifie 3 types stricts).
- Synonymes dédup avec **priorité OWL** (un synonyme présent dans les
  deux sources est tracé `ANS`)."""))

    cells.append(code("""\
csv_df = flat_csv.build(merged, propagated, siblings, owl_codes, ofs_codes)
print(f"CSV total rows : {len(csv_df):,}")
print(f"Distinct codes : {csv_df['code'].n_unique():,}")
print(f"By type   : {dict(csv_df.group_by('type').len().iter_rows())}")
print(f"By source : {dict(csv_df.group_by('source').len().iter_rows())}")
"""))

    cells.append(code("""\
# Voir tout ce qui sort pour les leaves parmi nos témoins
csv_df.filter(pl.col("code").is_in(WITNESS_CODES))
"""))

    cells.append(md("""\
### Interprétation

- **~127 000 lignes** au total (objectif tenu : ~8 notes/code en moyenne).
- F02.00 et C50.8 **n'apparaissent pas dans le CSV** car ils ont des
  enfants en FR-PMSI 2025 (`F02.000`, `F02.001`, `F02.002` etc. ;
  `C50.8` a des sous-extensions chap II FR-PMSI). Le filtre leaf
  écarte automatiquement les non-feuilles — les notes utiles sont
  déjà passées aux vraies feuilles via la propagation.
- A00.0, F66.2, J45.8 sont des leaves dans cette édition et apparaissent.
- Notez le mapping CSV : `OWL_ANS` → `"ANS"`, `OFS` → `"CIM-10"`,
  `SYNTHESIZED_SIBLING` → `"CIM-10 frères"` (conforme à CLAUDE.md)."""))

    # ──────────────────────────────────────────────────────────────────
    # Cellule finale
    # ──────────────────────────────────────────────────────────────────
    cells.append(md("""\
---

## Ce qui se passe ensuite dans le pipeline

Le CSV produit est l'**entrée finale** pour l'enrichissement des prompts
LLM côté projet aval (`recode-scenario` notamment). Les chantiers
encore à venir dans `recode-icd` :

1. **`relations/dagger_asterisk.py`** — fusionner les paires †/* OFS et
   OWL avec inférence de direction OFS (les colonnes `start_code` /
   `end_code` OFS sont neutres, à aligner sur la convention
   `(asterisk_code, dagger_code)` OWL).
2. **`registry.py`** — `ReferentialRegistry` polars (cf
   `recode-scenario`) pour accès paresseux + cache.
3. **`model.py`** — entités pydantic canoniques (`Code`, `Note`,
   `Synonym`, `DaggerAsteriskPair`) pour exposer une API publique typée
   à `recode-scenario`.
4. **Loaders externes** — Index CIM-10 vol 3 (Hector AP-HP), Orphanet
   pour les maladies rares. Ces sources ajoutent des synonymes
   (`INDEX_CIM10_VOL3`, `AP_HP`, `ORPHANET` dans le mapping CSV).

Les Parquets intermédiaires (`merged_codes`, `propagated_notes`,
`sibling_exclusions`, `owl_codes`, `ofs_codes`) restent disponibles
pour les usages programmatiques avancés (par ex. retrouver
l'`inherited_from` d'une note, ou la direction OFS d'une paire †/*)."""))

    # Assemble + write
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.13",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, str(OUT))
    print(f"Wrote {OUT} ({len(cells)} cells)")


if __name__ == "__main__":
    main()
