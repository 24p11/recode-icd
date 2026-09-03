"""Rend les fiches de relecture des candidates depuis les CSV.

Pourquoi ce script existe
-------------------------
Les candidates ont d'abord été rédigées **à la main en markdown**, tables
de rôles comprises. C'est exactement le schéma qui a produit l'incident
ORPHANET du chantier `chapter_policy` : deux énumérations de la même
information, maintenues séparément, qui finissent par diverger sans que
personne l'ait décidé.

Les CSV de `data/guide_mco/extraction/` sont donc la **source unique**,
et les markdown sont **générés**. Un rôle ne peut plus être juste dans
l'un et faux dans l'autre.

    uv run python scripts/rendre_candidates_guide_mco.py
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

RACINE = Path(__file__).resolve().parents[1]
EXTRACTION = RACINE / "data" / "guide_mco" / "extraction"

#: (fichier, titre, pages imprimées, répertoire d'ancrage des citations).
#: Le pilote reste ancré sur les bruts (citations validées ligne à ligne,
#: on ne réancre pas) ; les articles du chantier B s'ancrent sur leur
#: transcription curée.
ARTICLES = {
    "AVC": ("avc", "ACCIDENTS VASCULAIRES CÉRÉBRAUX", "78-81", "extraits_bruts"),
    "D62": ("anemie_posthemorragique_d62", "ANÉMIE POSTHÉMORRAGIQUE AIGÜE APRÈS UNE INTERVENTION", "81-82", "extraits_bruts"),
    "DEN": ("malnutrition_denutrition", "MALNUTRITION, DÉNUTRITION", "109-114", "extraits_bruts"),
    "XXI": ("chapitre_xxi", "EMPLOI DES CODES DU CHAPITRE XXI DE LA CIM-10", "93-103", "extraits_bruts"),
    # -- chantier B (file : data/guide_mco/extraction/file_chantier_B.md) --
    "ACC": ("accouchement_impromptu", "ACCOUCHEMENT IMPROMPTU OU À DOMICILE", "81", "extraits"),
    "ANT": ("antecedents", "ANTÉCÉDENTS", "82-83", "extraits"),
    "ATH": ("atherosclerose_gangrene", "ATHEROSCLEROSE AVEC GANGRENE", "83", "extraits"),
    "CAR": ("carences_vitaminiques", "CARENCES VITAMINIQUES", "83", "extraits"),
    "CHU": ("chutes_a_repetition", "CHUTES A REPETITION", "83", "extraits"),
    "OMS": ("codes_oms_usage_urgent", "CODES OMS RÉSERVÉS A UN USAGE URGENT", "84", "extraits"),
    "COMP": ("complications_actes", "COMPLICATIONS DES ACTES MÉDICAUX ET CHIRURGICAUX", "84-88", "extraits"),
    "CYS": ("cystite_aigue", "CYSTITE AIGÜE", "88", "extraits"),
    "DIA": ("diabete_type2_insuline", "DIABÈTE DE TYPE 2 TRAITÉ PAR INSULINE", "89", "extraits"),
    "DOU": ("douleur_chronique", "DOULEUR CHRONIQUE", "89", "extraits"),
    "REB": ("douleur_chronique_refractaire", "DOULEUR CHRONIQUE REFRACTAIRE (REBELLE)", "89-90", "extraits"),
    "EFN": ("effets_nocifs_medicaments", "EFFETS NOCIFS DES MÉDICAMENTS", "90-91", "extraits"),
    "B95": ("groupe_b95_b98", "EMPLOI DES CODES DU GROUPE B95–B98 CIM–10", "91", "extraits"),
    "O80": ("categories_o80_o84", "EMPLOI DES CATÉGORIES O80 À O84 DE LA CIM–10", "92", "extraits"),
    "P00": ("categories_p00_p04", "EMPLOI DES CATÉGORIES P00 À P04 DE LA CIM–10", "92", "extraits"),
    "ENF": ("enfants_nes_sans_vie", "ENFANTS NÉS SANS VIE", "92-93", "extraits"),
    "GRA": ("etat_grabataire", "ÉTAT GRABATAIRE", "103-104", "extraits"),
    "HEM": ("hemangiome_lymphangiome", "HÉMANGIOME ET LYMPHANGIOME", "104", "extraits"),
    "HYP": ("hypotension", "HYPOTENSION ET BAISSE DE LA TENSION ARTÉRIELLE", "104", "extraits"),
    "POL": ("polyhandicap_lourd", "IDENTIFICATION DU POLYHANDICAP LOURD", "104-105", "extraits"),
    "IDM": ("infarctus_myocarde", "INFARCTUS DU MYOCARDE", "105", "extraits"),
    "IRF": ("insuffisance_renale_fonctionnelle", "INSUFFISANCE RÉNALE FONCTIONNELLE", "105-106", "extraits"),
    "IRA": ("insuffisance_respiratoire_adulte", "INSUFFISANCE RESPIRATOIRE DE L’ADULTE", "106", "extraits"),
    "ITG": ("interruption_grossesse", "INTERRUPTION DE LA GROSSESSE", "106-109", "extraits"),
    "LES": ("lesions_traumatiques", "LÉSIONS TRAUMATIQUES", "109", "extraits"),
    "MPR": ("maladies_professionnelles", "MALADIES PROFESSIONNELLES", "109", "extraits"),
    "OED": ("oedeme_pulmonaire", "ŒDÈME PULMONAIRE", "114", "extraits"),
    "PRE": ("precarite", "PRÉCARITÉ", "114-115", "extraits"),
    "RAM": ("resistance_antimicrobiens", "RÉSISTANCE AUX ANTIMICROBIENS", "115-116", "extraits"),
}

#: Associations déjà versées au commit 2 dont seule l'association manque.
DEJA_VERSEES = {"GM2026-V-AVC-02", "GM2026-V-AVC-04"}


def article_de(rec_id: str) -> str:
    return rec_id.split("-")[2]


def rend(cle: str, recs: pl.DataFrame, codes: pl.DataFrame) -> str:
    fichier, titre, pages, repertoire = ARTICLES[cle]
    extension = "md" if repertoire == "extraits" else "txt"
    mes_recs = recs.filter(pl.col("rec_id").str.contains(f"-{cle}-")).sort("rec_id")
    mes_codes = codes.filter(pl.col("rec_id").str.contains(f"-{cle}-"))

    lignes = [
        f"# Candidates — {titre}",
        "",
        "> **Fichier GÉNÉRÉ.** Source unique :",
        "> `candidates_recommendations.csv` et",
        "> `candidates_recommendation_codes.csv` du même répertoire.",
        "> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.",
        "> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul",
        "> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).",
        ">",
        f"> Texte source : `data/guide_mco/{repertoire}/{fichier}.{extension}`",
        f"> (guide chap. V, pp. imprimées {pages}). Les `L…` y renvoient.",
        "",
        f"**{mes_recs.height} consignes, "
        f"{mes_codes.filter(~pl.col('rec_id').is_in(DEJA_VERSEES)).height} associations**"
        + (
            f" (+ {mes_codes.filter(pl.col('rec_id').is_in(DEJA_VERSEES)).height} "
            f"associations manquantes de consignes déjà versées)"
            if mes_codes.filter(pl.col("rec_id").is_in(DEJA_VERSEES)).height
            else ""
        )
        + ".",
        "",
        "---",
        "",
    ]

    # Associations manquantes de consignes déjà versées au commit 2.
    manquantes = mes_codes.filter(pl.col("rec_id").is_in(DEJA_VERSEES)).sort("rec_id", "code_expr")
    if manquantes.height:
        lignes += [
            "## Associations manquantes de consignes déjà versées",
            "",
            "Ces consignes sont dans `recommendations_curated.csv` mais sans",
            "aucune association : le §5 de la note n'en donnait pas. Elles",
            "ressortent au rapport de build sous",
            "`guide_mco_recommandations_sans_code.csv`.",
            "",
        ]
        for rec_id in manquantes["rec_id"].unique().sort():
            lignes += [f"### {rec_id}", "", _table(manquantes.filter(pl.col("rec_id") == rec_id)), ""]
        lignes += ["---", ""]

    lignes += ["## Consignes nouvelles", ""]
    for r in mes_recs.iter_rows(named=True):
        assoc = mes_codes.filter(pl.col("rec_id") == r["rec_id"]).sort("code_expr", "role")
        lignes += [
            f"### {r['rec_id']} — `{r['type']}`",
            "",
            f"**Situation** : {r['situation']}",
            "",
            f"**Texte** : {r['texte']}",
            "",
            f"**Condition** : {r['condition'] or '—'}",
            "",
            f"**Citation** (`{r['citation_fichier']}` {r['citation_lignes']}) :",
            f"« {r['citation']} »",
            "",
        ]
        lignes += (
            [_table(assoc), ""]
            if assoc.height
            else [
                "*Aucune association.* Le guide ne nomme ici aucun code : "
                "en attribuer supposerait de **choisir** des cibles que le "
                "texte ne donne pas.",
                "",
            ]
        )
    return "\n".join(lignes)


def _table(df: pl.DataFrame) -> str:
    out = [
        "| code_expr | role | centralite | portee | condition |",
        "|---|---|---|---|---|",
    ]
    for ligne in df.iter_rows(named=True):
        centralite = ligne["centralite"]
        marque = f"**{centralite}**" if centralite == "exemple" else centralite
        # `portee` vide = `chaque` (défaut). Une bascule `ensemble` est une
        # décision de curation : elle se met en relief, avec sa justification.
        portee = ligne.get("portee") or "chaque"
        if portee == "ensemble":
            portee = f"**ensemble** — {ligne.get('justification') or '⚠ justification manquante'}"
        out.append(
            f"| `{ligne['code_expr']}` | `{ligne['role']}` | {marque} | {portee} | "
            f"{ligne['condition'] or ''} |"
        )
    return "\n".join(out)


def main() -> None:
    recs = pl.read_csv(
        EXTRACTION / "candidates_recommendations.csv", schema_overrides={"condition": pl.String}
    )
    codes = pl.read_csv(
        EXTRACTION / "candidates_recommendation_codes.csv",
        schema_overrides={"condition": pl.String},
    )
    for cle in ARTICLES:
        chemin = EXTRACTION / f"candidates_{ARTICLES[cle][0]}.md"
        chemin.write_text(rend(cle, recs, codes) + "\n", encoding="utf-8")
        print(f"Écrit : {chemin.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
