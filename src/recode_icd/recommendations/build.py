"""Construction des Parquet de recommandations depuis les tables curées.

⚠ **L'extraction LLM ne rentre jamais ici.** Ce module part
exclusivement de `data/guide_mco/*_curated.csv`, validés humainement
ligne à ligne — même pattern que `dagger_curation.csv`. Les fichiers de
`data/guide_mco/extraction/` sont une trace de curation, pas une entrée
du pipeline. Une seule porte d'entrée vers les tables curées : la
validation ligne à ligne.

Fonctions **pures et déterministes** : tris explicites partout, aucun
recours à l'ordre naturel d'un `group_by` ou d'une jointure — le projet
a déjà été mordu par des artefacts byte-instables produits ainsi.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

from recode_icd.recommendations.code_expr import CodeExprError, parse_code_expr
from recode_icd.recommendations.resolution import ResolutionError, resout

RECOMMENDATIONS_FILENAME = "recommendations.parquet"
RECOMMENDATION_CODES_FILENAME = "recommendation_codes.parquet"

#: Rôles pour lesquels on cherche un recouvrement avec les exclusions
#: OFS/ANS. Les rôles de position (DP/DR/DAS) n'ont pas d'équivalent
#: dans la CIM-10, qui ne connaît pas le PMSI.
ROLES_INTERDICTION = ("interdit", "interdit_association")


class CurationError(ValueError):
    """Incohérence dans les tables curées (intégrité référentielle)."""


@dataclass
class RapportBuild:
    """Ce que le build a rencontré. Tout y est, rien n'est avalé."""

    expressions_non_parsables: list[dict[str, str]] = field(default_factory=list)
    expressions_non_resolues: list[dict[str, str]] = field(default_factory=list)
    recommandations_sans_code: list[str] = field(default_factory=list)
    recouvrement_potentiel: list[dict[str, str]] = field(default_factory=list)
    statistiques: dict[str, int] = field(default_factory=dict)

    @property
    def a_des_erreurs(self) -> bool:
        return bool(self.expressions_non_parsables or self.expressions_non_resolues)


def charge_tables_curees(curation_dir: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Charge les deux CSV curés et vérifie leur intégrité référentielle.

    `condition` est lue en `str` nullable : polars typerait une colonne
    entièrement vide en `Null`, ce que le schéma pandera strict
    refuserait — et une colonne de conditions peut légitimement être
    vide sur un article donné.
    """
    recs = pl.read_csv(
        curation_dir / "recommendations_curated.csv",
        schema_overrides={"condition": pl.String},
    )
    codes = pl.read_csv(
        curation_dir / "recommendation_codes_curated.csv",
        schema_overrides={"condition": pl.String},
    )

    orphelins = sorted(set(codes["rec_id"].to_list()) - set(recs["rec_id"].to_list()))
    if orphelins:
        raise CurationError(
            f"{len(orphelins)} association(s) pointent vers un rec_id inexistant : "
            f"{orphelins[:5]}. Corriger la table curée — une association orpheline "
            f"est une consigne dont le texte a disparu."
        )
    return recs, codes


def construit(
    recs: pl.DataFrame,
    codes: pl.DataFrame,
    merged: pl.DataFrame,
    flat: pl.DataFrame | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, RapportBuild]:
    """Résout les expressions et produit les deux tables de sortie.

    Retourne `(recommendations, recommendation_codes_resolus, rapport)`.
    La table résolue porte **une ligne par (rec_id, code_expr, code)** :
    `code_expr` y est conservée, donc l'association compacte reste
    récupérable par déduplication — aucune information n'est perdue.
    """
    rapport = RapportBuild()
    lignes: list[dict[str, object]] = []

    for ligne in codes.sort("rec_id", "code_expr", "role").iter_rows(named=True):
        rec_id, expr_brute = str(ligne["rec_id"]), str(ligne["code_expr"])
        try:
            expr = parse_code_expr(expr_brute)
        except CodeExprError as err:
            rapport.expressions_non_parsables.append(
                {"rec_id": rec_id, "code_expr": expr_brute, "erreur": str(err)}
            )
            continue
        try:
            feuilles = resout(expr, merged)
        except ResolutionError as err:
            rapport.expressions_non_resolues.append(
                {"rec_id": rec_id, "code_expr": expr_brute, "erreur": str(err)}
            )
            continue
        if not feuilles:
            rapport.expressions_non_resolues.append(
                {
                    "rec_id": rec_id,
                    "code_expr": expr_brute,
                    "erreur": "Expression résolue sur zéro code feuille.",
                }
            )
            continue
        for code in feuilles:
            lignes.append(
                {
                    "rec_id": rec_id,
                    "code_expr": expr_brute,
                    "code": code,
                    "role": str(ligne["role"]),
                    "centralite": str(ligne["centralite"]),
                    "condition": ligne["condition"],
                    "type_expr": expr.type.name,
                    "specificite": int(expr.type),
                }
            )

    resolus = (
        pl.DataFrame(lignes, schema=_SCHEMA_RESOLUS)
        if lignes
        else pl.DataFrame(schema=_SCHEMA_RESOLUS)
    )
    # Tri final explicite : le déterminisme byte-à-byte en dépend.
    resolus = resolus.sort("rec_id", "code_expr", "code", "role")
    recs_tries = recs.sort("rec_id")

    avec_code = set(resolus["rec_id"].to_list())
    rapport.recommandations_sans_code = sorted(set(recs_tries["rec_id"].to_list()) - avec_code)
    rapport.statistiques = _statistiques(recs_tries, resolus, codes.height)
    if flat is not None:
        rapport.recouvrement_potentiel = _recouvrement_potentiel(resolus, flat)

    return recs_tries, resolus, rapport


_SCHEMA_RESOLUS: dict[str, pl.DataType] = {
    "rec_id": pl.String(),
    "code_expr": pl.String(),
    "code": pl.String(),
    "role": pl.String(),
    "centralite": pl.String(),
    "condition": pl.String(),
    "type_expr": pl.String(),
    "specificite": pl.Int64(),
}


def _statistiques(recs: pl.DataFrame, resolus: pl.DataFrame, n_associations: int) -> dict[str, int]:
    stats: dict[str, int] = {
        "recommandations": recs.height,
        "associations_curees": n_associations,
        "couples_rec_code": resolus.height,
        "codes_touches": resolus["code"].n_unique() if resolus.height else 0,
    }
    for valeur, n in sorted(recs["type"].value_counts().iter_rows()):
        stats[f"type_{valeur}"] = n
    for valeur, n in sorted(resolus["role"].value_counts().iter_rows()) if resolus.height else []:
        stats[f"role_{valeur}"] = n
    for valeur, n in (
        sorted(resolus["type_expr"].value_counts().iter_rows()) if resolus.height else []
    ):
        stats[f"granularite_{valeur}"] = n
    return stats


def _recouvrement_potentiel(resolus: pl.DataFrame, flat: pl.DataFrame) -> list[dict[str, str]]:
    """Pointeurs vers des exclusions OFS/ANS qui pourraient recouper une interdiction.

    ⚠ **Heuristique de repérage pour l'audit humain, rien de plus.**
    Aucune prétention sémantique : ce n'est ni un dédoublonnage, ni une
    preuve de redondance. Une consigne du guide et une exclusion CIM-10
    n'ont ni la même autorité ni la même portée — elles coexistent, et
    la trace sert seulement à ce qu'un humain aille voir.

    Critère, volontairement modeste : pour chaque `(rec_id, code)` de
    rôle `interdit` ou `interdit_association`, on liste les lignes
    d'exclusion du CSV maître portées par ce code. Pour
    `interdit_association`, on signale en plus si le texte d'exclusion
    mentionne l'une des **autres cibles de la même consigne** — c'est le
    seul cas où le recoupement est un peu plus qu'une coïncidence de
    code.

    ⚠ **Le second critère ne peut mordre que sur ANS.** ANS écrit ses
    renvois entre parenthèses dans le texte (« entraînant un infarctus
    cérébral (I63.-) ») ; OFS livre le même contenu sans code
    (« entraînant un infarctus cérébral »), le code de redirection vivant
    dans une colonne séparée. Une absence de correspondance côté OFS ne
    dit donc rien sur le fond — c'est une asymétrie de format, pas un
    constat. Mesuré au pilote : 15 correspondances sur 125 lignes, les 15
    du côté ANS.
    """
    interdictions = resolus.filter(pl.col("role").is_in(ROLES_INTERDICTION))
    if interdictions.height == 0:
        return []

    exclusions = flat.filter(pl.col("type") == "exclusion").select("code", "texte", "source")
    concernes = interdictions["code"].unique().to_list()
    exclusions = exclusions.filter(pl.col("code").is_in(concernes))
    if exclusions.height == 0:
        return []

    # Cibles d'une consigne : les racines à 3 caractères de ses codes
    # RÉSOLUS.
    #
    # Piège rencontré, et il rendait l'heuristique inerte : dériver les
    # cibles des BORNES de l'expression ne voit pas l'intérieur d'une
    # plage. Pour « I60-I64 » on n'obtenait que I60 et I64 — or
    # l'exclusion ANS de I65.0 renvoie à « (I63.-) », qui est bien une
    # cible de la consigne. Résultat : zéro correspondance sur 125
    # lignes, ce qui se lisait comme « aucun recouvrement » alors que
    # c'était « la mesure ne mesurait rien ». Les codes résolus donnent
    # l'intérieur de la plage gratuitement.
    cibles: dict[str, set[str]] = {}
    for rec_id, code in resolus.select("rec_id", "code").unique().iter_rows():
        cibles.setdefault(str(rec_id), set()).add(str(code)[:3])

    sorties: list[dict[str, str]] = []
    for ligne in interdictions.sort("rec_id", "code").iter_rows(named=True):
        rec_id, code, role = str(ligne["rec_id"]), str(ligne["code"]), str(ligne["role"])
        for exclu in (
            exclusions.filter(pl.col("code") == code).sort("source", "texte").iter_rows(named=True)
        ):
            texte = str(exclu["texte"])
            autres = cibles.get(rec_id, set()) - {code[:3]}
            reference = any(cible and cible in texte for cible in autres)
            sorties.append(
                {
                    "rec_id": rec_id,
                    "code": code,
                    "role": role,
                    "source_exclusion": str(exclu["source"]),
                    "texte_exclusion": texte,
                    "reference_cible_meme_consigne": "oui" if reference else "non",
                }
            )
    return sorties


def ecrit_parquets(recs: pl.DataFrame, resolus: pl.DataFrame, output_dir: Path) -> dict[str, Path]:
    """Écrit les deux Parquet et retourne leurs chemins."""
    output_dir.mkdir(parents=True, exist_ok=True)
    chemins = {
        "recommendations": output_dir / RECOMMENDATIONS_FILENAME,
        "recommendation_codes": output_dir / RECOMMENDATION_CODES_FILENAME,
    }
    recs.write_parquet(chemins["recommendations"])
    resolus.write_parquet(chemins["recommendation_codes"])
    return chemins


def ecrit_rapport(rapport: RapportBuild, reports_dir: Path) -> dict[str, Path]:
    """Écrit le rapport de build — un CSV par nature de constat."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    chemins: dict[str, Path] = {}

    tables: dict[str, pl.DataFrame] = {
        "guide_mco_expressions_non_parsables": pl.DataFrame(
            rapport.expressions_non_parsables,
            schema={"rec_id": pl.String, "code_expr": pl.String, "erreur": pl.String},
        ),
        "guide_mco_expressions_non_resolues": pl.DataFrame(
            rapport.expressions_non_resolues,
            schema={"rec_id": pl.String, "code_expr": pl.String, "erreur": pl.String},
        ),
        "guide_mco_recommandations_sans_code": pl.DataFrame(
            {"rec_id": rapport.recommandations_sans_code}, schema={"rec_id": pl.String}
        ),
        "guide_mco_recouvrement_potentiel": pl.DataFrame(
            rapport.recouvrement_potentiel,
            schema={
                "rec_id": pl.String,
                "code": pl.String,
                "role": pl.String,
                "source_exclusion": pl.String,
                "texte_exclusion": pl.String,
                "reference_cible_meme_consigne": pl.String,
            },
        ),
        "guide_mco_statistiques": pl.DataFrame(
            {
                "indicateur": sorted(rapport.statistiques),
                "valeur": [rapport.statistiques[k] for k in sorted(rapport.statistiques)],
            },
            schema={"indicateur": pl.String, "valeur": pl.Int64},
        ),
    }
    for nom, table in tables.items():
        chemin = reports_dir / f"{nom}.csv"
        table.write_csv(chemin)
        chemins[nom] = chemin
    return chemins


__all__ = (
    "RECOMMENDATIONS_FILENAME",
    "RECOMMENDATION_CODES_FILENAME",
    "ROLES_INTERDICTION",
    "CurationError",
    "RapportBuild",
    "charge_tables_curees",
    "construit",
    "ecrit_parquets",
    "ecrit_rapport",
)
