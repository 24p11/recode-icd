"""Kit de nomenclature CIM-10 FR de l'ATIH (`LIBCIM10MULTI.TXT`).

Le kit est **la** source de l'autorisation de codage en MCO : pour
chaque code, le Type MCO/HAD dit s'il peut figurer dans un RUM et à
quelle position. Il devient une donnée des livrables (chantier
couverture ATIH, D1) : `atih_codes.parquet`, joint à `merged_codes`
(`type_mco`, `statut_mco`, `codable_mco`) et rendu sur chaque fiche.

Format (`cim.pdf` du kit, p. 4-5) : ISO-8859-1, CR LF, 6 champs `|` —
code sur 6 positions (point omis, bourrage d'espaces, `+` possible en
4e et 5e position), Type MCO/HAD, Profil SMR (3 × O/N), Type PSY,
libellé court, libellé long. Aucun en-tête.

Type MCO/HAD :

| Valeur | Sens |
|---|---|
| 0 | pas de restriction |
| 1 | interdit en DP et DR, autorisé ailleurs |
| 2 | interdit en DP et DR — cause externe de morbidité |
| 3 | interdit en DP, DR et DA — catégorie ou sous-catégorie non vide, ou code père interdit |
| 4 | interdit en DP, autorisé ailleurs |

**Autorisé en MCO = type ≠ 3 et non supprimé.** Un code supprimé reste
dans le kit avec son libellé préfixé `*** SUaa ***` (aa = millésime de
la suppression) et le type 3.

⚠ **Le type 3 n'est pas une interdiction clinique** : c'est un père
(la catégorie `A00` a des subdivisions) ou un code supprimé. `U07.1` est
type 3 — ses feuilles `U07.10..15` sont codables.

L'écriture des codes vient de la table de notation unique
(`recode_icd.notations`) : la colonne `code` porte l'écriture du maître,
`code_atih` la compacte du kit. Le kit n'est jamais « corrigé » — un
libellé `*** SU09 ***` est décodé en `supprime=True`, pas réécrit.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
from smt2parquet import core

from recode_icd.loaders.schemas import AtihCodesSchema
from recode_icd.notations import Notations, charge_notations

KIT_FILENAME = "LIBCIM10MULTI.TXT"
TERMINOLOGY_NAME = "cim10_atih"
#: Millésime du kit livré dans `data/CIM_ATIH_2025/`. Le kit ne le porte
#: pas lui-même : il se déclare, comme `2026-provisoire` pour le guide.
MILLESIME_DEFAUT = "2025"

_RE_SUPPRIME = re.compile(r"^\*\*\* SU(\d\d) \*\*\*\s*")

#: Statut MCO d'un code, dérivé du type et du marqueur de suppression.
#: Les cinq premiers sont codables ; les deux derniers ne le sont pas.
STATUTS_MCO = (
    "codable",  # type 0
    "interdit_dp_dr",  # type 1
    "cause_externe",  # type 2 : jamais DP ni DR
    "interdit_dp",  # type 4
    "pere_interdit",  # type 3 non supprimé
    "supprime",  # `*** SUaa ***`
)
#: Statut d'un code du maître absent du kit (colonne nullable de merged).
STATUT_INCONNU = "inconnu_atih"

_STATUT_PAR_TYPE = {
    0: "codable",
    1: "interdit_dp_dr",
    2: "cause_externe",
    4: "interdit_dp",
    3: "pere_interdit",
}

LIBELLES_STATUT = {
    "codable": "codable en MCO, pas de restriction",
    "interdit_dp_dr": "codable en MCO, interdit en DP et DR",
    "cause_externe": "codable en MCO en DAS seulement (cause externe de morbidité)",
    "interdit_dp": "codable en MCO, interdit en DP",
    "pere_interdit": "non codable en MCO (catégorie non vide ou code père interdit)",
    "supprime": "supprimé du kit ATIH",
    STATUT_INCONNU: "inconnu du kit ATIH",
}


def statut_mco(type_mco: int, supprime: bool) -> str:
    """Statut MCO d'un code du kit."""
    if supprime:
        return "supprime"
    try:
        return _STATUT_PAR_TYPE[type_mco]
    except KeyError as err:
        raise ValueError(f"Type MCO/HAD inconnu : {type_mco} (attendu 0-4).") from err


def load_atih_kit(path: Path) -> pl.DataFrame:
    """Le kit tel quel : `code` compact (bourrage retiré), champs bruts.

    Refuse un enregistrement qui n'a pas exactement 6 champs — un `|`
    dans un libellé casserait le découpage, et le kit garantit qu'il n'y
    en a pas.
    """
    lignes = [ligne for ligne in path.read_text(encoding="iso-8859-1").splitlines() if ligne]
    champs = [ligne.split("|") for ligne in lignes]
    fautives = [ligne for ligne, c in zip(lignes, champs, strict=True) if len(c) != 6]
    if fautives:
        raise ValueError(
            f"{path} : {len(fautives)} enregistrement(s) sans exactement 6 champs, "
            f"ex. {fautives[0][:60]!r}."
        )
    return pl.DataFrame(
        {
            "code": [c[0].strip() for c in champs],
            "type_mco": [int(c[1]) for c in champs],
            "profil_smr": [c[2] for c in champs],
            "type_psy": [int(c[3]) for c in champs],
            "libelle_court": [c[4] for c in champs],
            "libelle_long": [c[5] for c in champs],
        }
    )


def build_atih_codes(
    kit: pl.DataFrame, notations: Notations, millesime: str = MILLESIME_DEFAUT
) -> pl.DataFrame:
    """Table `atih_codes` : écriture du maître, statut, règles positionnelles.

    Règles dérivées **par construction** depuis le type :
    `interdit_dp` (types 1, 2, 3, 4 et supprimés), `interdit_dr` (1, 2, 3
    et supprimés), `interdit_das` (3 et supprimés), `codable_mco` (type ≠ 3
    et non supprimé). Une seule source de vérité pour le vérificateur et
    recode-scenario.
    """
    supprime_millesime = [
        (m.group(1) if (m := _RE_SUPPRIME.match(lib)) else None) for lib in kit["libelle_long"]
    ]
    libelles = [_RE_SUPPRIME.sub("", lib) for lib in kit["libelle_long"]]
    supprime = [sm is not None for sm in supprime_millesime]
    statuts = [statut_mco(int(t), s) for t, s in zip(kit["type_mco"], supprime, strict=True)]
    df = pl.DataFrame(
        {
            "code": [notations.ecriture_maitre(c) for c in kit["code"]],
            "code_atih": kit["code"],
            "type_mco": kit["type_mco"].cast(pl.Int64),
            "profil_smr": kit["profil_smr"],
            "smr_mmp": kit["profil_smr"].str.slice(0, 1) == "O",
            "smr_ae": kit["profil_smr"].str.slice(1, 1) == "O",
            "smr_das": kit["profil_smr"].str.slice(2, 1) == "O",
            "type_psy": kit["type_psy"].cast(pl.Int64),
            "supprime": supprime,
            "supprime_millesime": pl.Series(supprime_millesime, dtype=pl.String),
            "statut_mco": statuts,
            "codable_mco": [s not in ("pere_interdit", "supprime") for s in statuts],
            "interdit_dp": [s != "codable" for s in statuts],
            "interdit_dr": [s not in ("codable", "interdit_dp") for s in statuts],
            "interdit_das": [s in ("pere_interdit", "supprime") for s in statuts],
            "libelle_court": kit["libelle_court"],
            "libelle_long": libelles,
            "millesime": [millesime] * kit.height,
        }
    ).sort("code_atih")
    doublons = df.filter(pl.col("code").is_duplicated())
    if doublons.height:
        raise ValueError(
            f"Écriture du maître non injective sur le kit : {doublons['code'].unique().to_list()[:5]}."
        )
    AtihCodesSchema.validate(df)
    return df


def resume_kit(atih_codes: pl.DataFrame) -> pl.DataFrame:
    """Rapport : effectifs par statut, type et millésime de suppression."""
    par_statut = (
        atih_codes.group_by("statut_mco", "type_mco")
        .len()
        .sort("statut_mco", "type_mco")
        .select(
            pl.lit("statut_x_type").alias("dimension"),
            (pl.col("statut_mco") + "|" + pl.col("type_mco").cast(pl.String)).alias("valeur"),
            pl.col("len").cast(pl.Int64).alias("count"),
        )
    )
    par_su = (
        atih_codes.filter(pl.col("supprime"))
        .group_by("supprime_millesime")
        .len()
        .sort("supprime_millesime")
        .select(
            pl.lit("supprime_millesime").alias("dimension"),
            pl.col("supprime_millesime").alias("valeur"),
            pl.col("len").cast(pl.Int64).alias("count"),
        )
    )
    total = pl.DataFrame(
        {
            "dimension": ["total", "total"],
            "valeur": ["codes", "codables_mco"],
            "count": [atih_codes.height, int(atih_codes["codable_mco"].sum())],
        },
        schema={"dimension": pl.String, "valeur": pl.String, "count": pl.Int64},
    )
    return pl.concat([total, par_statut, par_su])


def to_parquet(
    kit_path: Path,
    output_dir: Path,
    reports_dir: Path,
    notations_path: Path | None = None,
    millesime: str = MILLESIME_DEFAUT,
) -> dict[str, Path]:
    """`atih_codes.parquet` (avec métadonnées de version) + `reports/atih_kit_summary.csv`."""
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    notations = charge_notations(notations_path)
    codes = build_atih_codes(load_atih_kit(kit_path), notations, millesime)
    metadata = {
        "terminology": TERMINOLOGY_NAME,
        "version": millesime,
        "atih_kit_version": millesime,
        "source_file": kit_path.name,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    paths = {
        "atih_codes": output_dir / "atih_codes.parquet",
        "summary": reports_dir / "atih_kit_summary.csv",
        "chapitre_xx_troncs": output_dir / "chapitre_xx_troncs.parquet",
        "chapitre_xx_valeurs": output_dir / "chapitre_xx_valeurs.parquet",
        "chapitre_xx_codes": output_dir / "chapitre_xx_codes.parquet",
        "chapitre_xx_composition": reports_dir / "chapitre_xx_composition.csv",
    }
    core.write_parquet_with_metadata(codes, paths["atih_codes"], metadata)
    resume_kit(codes).write_csv(paths["summary"])

    # Chapitre XX par composition (D5) : table dérivée déterministe du kit.
    from recode_icd.composition import derive_composition

    composition = derive_composition(codes)
    core.write_parquet_with_metadata(composition.troncs, paths["chapitre_xx_troncs"], metadata)
    core.write_parquet_with_metadata(composition.valeurs, paths["chapitre_xx_valeurs"], metadata)
    core.write_parquet_with_metadata(composition.codes, paths["chapitre_xx_codes"], metadata)
    rapport = pl.concat(
        [
            composition.patrons.select(
                "dimension", "valeur", pl.col("n").cast(pl.String).alias("detail")
            ),
            composition.variantes.filter(~pl.col("canonique")).select(
                pl.lit("variante_libelle").alias("dimension"),
                (pl.col("table") + " " + pl.col("valeur")).alias("valeur"),
                (pl.col("libelle") + " (" + pl.col("n").cast(pl.String) + ")").alias("detail"),
            ),
        ]
    )
    rapport.write_csv(paths["chapitre_xx_composition"])
    return paths


__all__ = (
    "KIT_FILENAME",
    "LIBELLES_STATUT",
    "MILLESIME_DEFAUT",
    "STATUTS_MCO",
    "STATUT_INCONNU",
    "build_atih_codes",
    "load_atih_kit",
    "resume_kit",
    "statut_mco",
    "to_parquet",
)
