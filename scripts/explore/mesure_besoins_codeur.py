"""Mesures d'ouverture du chantier « besoins de codeur » (2026-10-18).

`codeur` (24p11/codeur) consomme la livraison recode-icd pour un outil
de codage assisté. Son prompt d'ouverture demande de MESURER avant de
décider. Ce script produit les chiffres, sans rien modifier :

A. vérification des exemples du prompt (Z992, K861, J961, M146…) contre
   le kit ATIH 2025 — statut réel des « codes tronqués » ;
B. taille des listes de correction : pour chaque nœud du maître, le
   nombre de codes CODABLES qui en descendent (c'est la liste que la
   boucle de correction enverrait au LLM) ;
C. codes codables par catégorie 3 caractères (distribution, têtes) ;
D. fiches « vides » : rien au-delà du titre/libellé/statut selon les
   colonnes has_* de l'index, croisé avec les notes rendues ;
E. taille des fiches (caractères → estimation tokens, budget 15 fiches) ;
F. volumétrie des formulations exportables (recherche par mots-clés).

Usage
-----
    uv run python scripts/explore/mesure_besoins_codeur.py
"""

from __future__ import annotations

import polars as pl

from recode_icd.utils.loaders_dev import load_exploration_context

#: Les 1 003 notes rendues peuvent remplir une fiche par ailleurs vide.
DESTINATIONS_RENDUES_EXCLUES = ("non_rendue",)

#: ≈ caractères par token pour du français médical (ordre de grandeur).
CHARS_PAR_TOKEN = 3.2


def main() -> None:
    ctx = load_exploration_context()
    merged = ctx.merged.collect() if isinstance(ctx.merged, pl.LazyFrame) else ctx.merged
    flat = ctx.flat.collect() if isinstance(ctx.flat, pl.LazyFrame) else ctx.flat
    atih = pl.read_parquet("referentials/processed/atih_codes.parquet")
    idx = pl.read_csv(
        "outputs/cards_library/index.csv", schema_overrides={"format_version": pl.String}
    )

    # ---- A. Les exemples du prompt contre le kit --------------------------
    print("== A. Statut kit ATIH 2025 des « codes tronqués » du prompt codeur")
    exemples = [
        "Z992",
        "Z992+0",
        "K861",
        "K861+8",
        "J961",
        "J961+0",
        "M146",
        "M1467",
        "M142",
        "M1427",
        "R521",
        "R5210",
        "E11",
    ]
    sous = atih.filter(pl.col("code_atih").is_in(exemples)).select(
        "code_atih", "type_mco", "statut_mco", "codable_mco", "libelle_court"
    )
    for r in sous.sort("code_atih").iter_rows(named=True):
        print(
            f"  {r['code_atih']:<8} type={r['type_mco']} {r['statut_mco']:<14} codable={r['codable_mco']} | {str(r['libelle_court'])[:50]}"
        )
    n_ni = atih.filter(pl.col("code_atih").str.contains("ni", literal=True)).height
    n_plus = atih.filter(pl.col("code_atih").str.contains("+", literal=True)).height
    print(f"  codes à extension « + » au kit : {n_plus} ; contenant « ni » : {n_ni}")

    # Cas piège : codes CODABLES ayant des descendants codables (Z992 !).
    codables = atih.filter(pl.col("codable_mco"))
    prefixes = codables["code_atih"].to_list()
    ensemble = set(prefixes)
    parents_codables = sorted(
        {c for c in ensemble for autre in (c + "+",) if any(p.startswith(autre) for p in ensemble)}
    )
    print(
        f"  codes CODABLES dont des extensions « + » sont aussi codables : {len(parents_codables)}"
    )
    print(f"    exemples : {parents_codables[:10]}")

    # ---- B. Taille des listes de correction (descendants codables) -------
    print("\n== B. Descendants codables par nœud du maître (liste de correction)")
    positions = merged.select("code", "left", "right", "type", "label")
    codables_maitre = set(merged.filter(pl.col("codable_mco").fill_null(False))["code"].to_list())
    feuilles_pos = sorted(
        (r["left"], r["code"]) for r in merged.iter_rows(named=True) if r["code"] in codables_maitre
    )
    lignes_noeuds: list[dict[str, object]] = []
    for r in positions.iter_rows(named=True):
        gauche, droite = r["left"], r["right"]
        if droite - gauche == 1:
            continue  # feuille
        n = sum(1 for left, _ in feuilles_pos if gauche < left < droite)
        lignes_noeuds.append(
            {"code": r["code"], "type": r["type"], "n_codables": n, "libelle": r["label"]}
        )
    noeuds = pl.DataFrame(lignes_noeuds)
    interieurs = noeuds.filter(pl.col("type") == "category")  # nœuds code/catégorie
    non_codables_int = interieurs.filter(~pl.col("code").is_in(sorted(codables_maitre)))
    print(f"  nœuds intermédiaires (hors blocs/chapitres) : {interieurs.height}")
    print(f"  dont NON codables (cible de la boucle de correction) : {non_codables_int.height}")
    for q in (0.5, 0.9, 0.99):
        print(f"  n_codables p{int(q * 100)} : {non_codables_int['n_codables'].quantile(q)}")
    print("  les 10 plus longs :")
    for r in non_codables_int.sort("n_codables", descending=True).head(10).iter_rows(named=True):
        print(f"    {r['code']:<10} {r['n_codables']:>4} codables | {str(r['libelle'])[:55]}")

    # ---- C. Codables par catégorie 3 caractères ---------------------------
    print("\n== C. Codes codables par catégorie 3 caractères")
    cat = (
        merged.filter(pl.col("codable_mco").fill_null(False))
        .with_columns(pl.col("code").str.slice(0, 3).alias("cat"))
        .group_by("cat")
        .len()
    )
    for q in (0.5, 0.9, 0.99):
        print(f"  p{int(q * 100)} : {cat['len'].quantile(q)}")
    print(
        f"  catégories : {cat.height} ; > 20 codables : {cat.filter(pl.col('len') > 20).height} ; > 50 : {cat.filter(pl.col('len') > 50).height}"
    )
    print("  les 10 plus longues :")
    libelles_cat = dict(merged.select("code", "label").iter_rows())
    for r in cat.sort("len", descending=True).head(10).iter_rows(named=True):
        print(f"    {r['cat']:<5} {r['len']:>4} | {str(libelles_cat.get(r['cat'], ''))[:55]}")

    # ---- D. Fiches « vides » ----------------------------------------------
    print("\n== D. Fiches sans contenu au-delà du titre/libellé/statut")
    has_cols = [c for c in idx.columns if c.startswith("has_")]
    vides_idx = idx.filter(~pl.any_horizontal([pl.col(c) for c in has_cols]))
    notes_rendues = set(
        flat.filter((pl.col("type") == "note") & (pl.col("note_destination") != "non_rendue"))[
            "code"
        ]
        .unique()
        .to_list()
    )
    vraiment_vides = vides_idx.filter(~pl.col("code").is_in(sorted(notes_rendues)))
    print(f"  colonnes has_* de l'index : {has_cols}")
    print(f"  fiches avec tous les has_* à faux : {vides_idx.height} / {idx.height}")
    print(f"  dont SANS note rendue non plus (vraiment vides) : {vraiment_vides.height}")
    print(
        "  ⚠ l'index ne trace pas les sections notes (has_definition…) — mesure croisée via le CSV"
    )
    par_chap = vraiment_vides.group_by("chapter").len().sort("len", descending=True)
    print(f"  par chapitre (tête) : {par_chap.head(6).to_dicts()}")
    print(f"  exemples : {vraiment_vides.head(8)['code'].to_list()}")

    # ---- E. Taille des fiches ---------------------------------------------
    print("\n== E. Taille des fiches (profil generation)")
    for q in (0.5, 0.9, 0.99):
        v = idx["nb_chars"].quantile(q)
        print(f"  p{int(q * 100)} : {v:.0f} chars ≈ {v / CHARS_PAR_TOKEN:.0f} tokens")
    vmax = idx["nb_chars"].max()
    print(
        f"  max : {vmax} chars ≈ {vmax / CHARS_PAR_TOKEN:.0f} tokens ({idx.sort('nb_chars', descending=True).head(1)['code'].to_list()})"
    )
    for q, nom in ((0.5, "médiane"), (0.9, "p90")):
        v = idx["nb_chars"].quantile(q)
        print(f"  budget 15 fiches à la {nom} : ≈ {15 * v / CHARS_PAR_TOKEN:,.0f} tokens")

    # ---- F. Formulations exportables ---------------------------------------
    print("\n== F. Formulations (familles de la section Formulations)")
    formulations = flat.filter(
        (pl.col("type") == "synonyme")
        & (
            pl.col("source").is_in(["CIM-10 index", "CepiDc 2015"])
            | pl.col("source").str.starts_with("AP-HP")
        )
    )
    print(f"  lignes : {formulations.height} ; codes couverts : {formulations['code'].n_unique()}")
    print(formulations.group_by("source").len().sort("len", descending=True).head(4))


if __name__ == "__main__":
    main()
