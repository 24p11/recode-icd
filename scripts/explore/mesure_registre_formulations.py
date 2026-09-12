"""Re-mesure après application du registre des formulations écartées.

Produit, à partir du YAML validé (`registre_formulations.yaml`) et du
VRAI chemin de code de l'assemblage (`cards._candidates_formulations`,
avec puis sans registre) :

- la volumétrie des écartées par chapitre et par source (stdout, pour
  la note d'analyse) ;
- `docs/analyses/<date>_registre_formulations_fiches_a_completer.csv` :
  les fiches dont la section Formulations est vidée ou réduite à ≤ 2
  après filtre. **Ce fichier est l'entrée du chantier synonymes LLM** :
  ce sont les trous de couverture réels, là où le langage vivant du CRH
  n'a plus de témoin.

Usage
-----
    uv run python scripts/explore/mesure_registre_formulations.py
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import polars as pl

from recode_icd import cards
from recode_icd.registre_formulations import REGISTRE_VIDE
from recode_icd.utils.loaders_dev import load_exploration_context

DATE = "2026-09-09"
SORTIE = Path(__file__).resolve().parents[2] / "docs" / "analyses"


def main() -> None:
    import dataclasses

    ctx = load_exploration_context(with_external=True)
    flat = cards._eager(ctx.flat)
    outils = cards.charge_politique(cards._eager(ctx.merged))
    if not outils.registre.ecartees:
        raise SystemExit("Registre vide : rien à mesurer.")
    outils_sans = dataclasses.replace(outils, registre=REGISTRE_VIDE)

    libelles = {c: (lib or "") for c, lib in flat.select("code", "libelle").unique().iter_rows()}

    codes_touches = sorted({code for code, _, _ in outils.registre.ecartees})

    def _n_section(code: str, avec: cards.PolitiqueFiches) -> int:
        sub = flat.filter(pl.col("code") == code)
        chapitre, blocs = avec.hierarchie_de(code)
        candidates = cards._candidates_formulations(sub, chapitre, blocs, avec)
        return len(cards._dedup_candidates(candidates))

    lignes: list[dict[str, object]] = []
    for code in codes_touches:
        chapitre, _ = outils.hierarchie_de(code)
        lignes.append(
            {
                "code": code,
                "libelle_officiel": libelles.get(code, ""),
                "chapitre": chapitre or "",
                "formulations_avant": _n_section(code, outils_sans),
                "formulations_apres": _n_section(code, outils),
            }
        )

    df = pl.DataFrame(lignes)
    a_completer = df.filter(pl.col("formulations_apres") <= 2).with_columns(
        (pl.col("formulations_apres") == 0).alias("section_videe")
    )
    chemin = SORTIE / f"{DATE}_registre_formulations_fiches_a_completer.csv"
    a_completer.write_csv(chemin)

    # Volumétrie des écartées par chapitre et par source.
    par_chapitre: Counter[str] = Counter()
    par_source: Counter[str] = Counter()
    for code, source, _texte in outils.registre.ecartees:
        chapitre, _ = outils.hierarchie_de(code)
        par_chapitre[chapitre or "?"] += 1
        par_source[source] += 1

    print(
        f"{len(outils.registre.ecartees)} formulations écartées, {len(codes_touches)} fiches touchées"
    )
    print("\nÉcartées par source :")
    for source, n in par_source.most_common():
        print(f"  {source}: {n}")
    print("\nÉcartées par chapitre :")
    for chap, n in sorted(par_chapitre.items()):
        print(f"  {chap}: {n}")
    videes = a_completer.filter(pl.col("section_videe")).height
    print(
        f"\nSections vidées : {videes} ; réduites à ≤2 : {a_completer.height - videes} → {chemin}"
    )
    print("\nDétail des fiches à compléter :")
    with pl.Config(tbl_rows=100):
        print(a_completer.sort("formulations_apres", "code"))

    # Contrôle de cohérence : combien d'écartées n'ont pas retiré de
    # formulation (dédup l'aurait absorbée de toute façon) ?
    retirees = sum(
        int(ligne["formulations_avant"]) - int(ligne["formulations_apres"]) for ligne in lignes
    )
    print(f"\nFormulations retirées des sections (post-dédup) : {retirees}")


if __name__ == "__main__":
    main()
