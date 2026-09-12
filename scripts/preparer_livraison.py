"""Assemble le paquet de livraison des fiches pour les data scientists.

Contenu de l'archive :

- `cards_library/` — la bibliothèque du profil `generation` complète,
  `_index.csv` compris ;
- `LIVRAISON.md` — une page générée : version, chiffres, contenu ;
- `guide_usage_fiches.md` et `resolveur_mode_emploi.md` — copiés de
  `docs/livraison/`.

Nommage : `recode-icd_fiches_generation_<commit court>_<millésime kit>.tar.gz`
dans `outputs/livraisons/` (non committé). Le script **exige un arbre
git propre** : le nom de l'archive certifie un état exact du dépôt.

Usage
-----
    uv run python scripts/preparer_livraison.py
"""

from __future__ import annotations

import datetime as dt
import subprocess
import tarfile
from pathlib import Path

import polars as pl
import yaml

RACINE = Path(__file__).resolve().parents[1]
BIBLIOTHEQUE = RACINE / "outputs" / "cards_library"
SORTIE = RACINE / "outputs" / "livraisons"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(RACINE), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _millesime_kit() -> str:
    kits = sorted(RACINE.glob("data/CIM_ATIH_*"))
    if not kits:
        raise SystemExit("Aucun kit ATIH sous data/ — millésime introuvable.")
    return kits[-1].name.removeprefix("CIM_").replace("_", "-").lower()  # atih-2025


def main() -> None:
    if _git("status", "--porcelain"):
        raise SystemExit(
            "Arbre git non propre : committer ou remiser avant de livrer "
            "(le nom de l'archive certifie un état exact du dépôt)."
        )
    if not (BIBLIOTHEQUE / "_index.csv").exists():
        raise SystemExit("Bibliothèque absente : lancer `recode-icd cards build` d'abord.")

    sha = _git("rev-parse", "--short", "HEAD")
    millesime = _millesime_kit()
    index = pl.read_csv(BIBLIOTHEQUE / "_index.csv")
    n_total = index.height
    n_troncs = index.filter(pl.col("classe_generation") == "tronc_composition").height
    registre = yaml.safe_load(
        (RACINE / "referentials/curation/registre_formulations.yaml").read_text(encoding="utf-8")
    )
    n_ecartees = len(registre.get("ecartees") or [])

    livraison_md = f"""\
# Livraison — bibliothèque de fiches CIM-10, profil `generation`

**Version** : commit `{sha}` · kit ATIH **{millesime}** · générée le
{dt.date.today().isoformat()} · dépôt `recode-icd`.

## Contenu

| Fichier | Rôle |
|---|---|
| `cards_library/` | {n_total} fiches Markdown, une par code codable en MCO ({n_total - n_troncs} émissibles + {n_troncs} troncs de composition du chapitre XX), rangées par chapitre |
| `cards_library/_index.csv` | index programmatique (code, chemin, sections, statut MCO, `classe_generation`) — **commencer ici** |
| `guide_usage_fiches.md` | structure des fiches, usage de l'index, les quatre « à ne pas faire » |
| `resolveur_mode_emploi.md` | `recode-icd resoudre` : toute écriture d'un code → fiche ou raison motivée |

## Garanties de cette version

- **Couverture 100 %** : tout code autorisé en MCO a sa fiche
  (invariant I1) ; le chapitre XX est couvert par composition
  (25 348 codes composés → 1 021 troncs, dont {n_troncs} portent une
  fiche de génération).
- **Aucun code non codable présenté comme émissible** (invariant I2) —
  seule exception, déclarée et marquée : les troncs du chapitre XX
  (`classe_generation=tronc_composition`).
- **Formulations filtrées du registre archaïque** : {n_ecartees}
  formulations de certificat de décès / terminologie désuète écartées
  sur verdict clinicien ligne à ligne (validation RF
  {registre["validation"]["date"]}, complément {registre["validation"].get("complement", "—")}).
- Fiches **déterministes** : même dépôt, même build, mêmes octets.

## Point d'entrée conseillé

1. Charger `_index.csv`, filtrer `classe_generation == "emissible"`.
2. Lire la fiche via `filepath`.
3. Pour tout code venant d'ailleurs (autre écriture, code composé,
   code interdit) : passer par le résolveur, jamais par une jointure
   manuelle — cf. `resolveur_mode_emploi.md`.

Retours et codes non résolus : joindre le journal du résolveur
(`--journal`) à vos remontées.
"""

    SORTIE.mkdir(parents=True, exist_ok=True)
    nom = f"recode-icd_fiches_generation_{sha}_{millesime}"
    chemin = SORTIE / f"{nom}.tar.gz"
    docs = RACINE / "docs" / "livraison"
    with tarfile.open(chemin, "w:gz") as tar:

        def _ajoute_texte(nom_fichier: str, contenu: str) -> None:
            import io

            donnees = contenu.encode("utf-8")
            info = tarfile.TarInfo(f"{nom}/{nom_fichier}")
            info.size = len(donnees)
            info.mtime = int(dt.datetime.now().timestamp())
            tar.addfile(info, io.BytesIO(donnees))

        _ajoute_texte("LIVRAISON.md", livraison_md)
        tar.add(docs / "guide_usage_fiches.md", arcname=f"{nom}/guide_usage_fiches.md")
        tar.add(docs / "resolveur_mode_emploi.md", arcname=f"{nom}/resolveur_mode_emploi.md")
        tar.add(BIBLIOTHEQUE, arcname=f"{nom}/cards_library")

    taille = chemin.stat().st_size / 1_048_576
    print(f"{chemin} ({taille:.1f} Mo) — {n_total} fiches, commit {sha}, kit {millesime}")


if __name__ == "__main__":
    main()
