"""Chapitre XX par composition : troncs, tables lieu/activité, codes composés (D5).

Le kit ATIH décline chaque cause externe (V01-Y98) en une combinatoire
**lieu × activité** absente de l'export ANS : 27 097 codes pour 373
catégories. Décision RF (2026-09-06) : on ne matérialise pas cette
combinatoire en fiches. La **catégorie** porte la fiche de tronc,
marquée « non codable seul — se compose du lieu (4e) et de l'activité
(5e) », et les consommateurs composent ; le résolveur valide.

Tout ici est **dérivé du kit, déterministe**, jamais écrit à la main :

- le rôle de chaque position (lieu, activité, code OMS, précision) se lit
  dans les libellés — le suffixe d'un code par rapport à son parent est
  comparé aux tables majoritaires ;
- les tables lieu (10 valeurs) et activité (7 valeurs) sont les libellés
  **majoritaires** du kit ; ses variantes (« école, lieu public » pour
  « école et lieu public ») sont rapportées, jamais corrigées ;
- chaque code du chapitre XX est **un tronc, un code OMS sans
  extension, ou un code composé décomposé** — un code qui n'entre dans
  aucun de ces trois cas est une erreur de dérivation, pas un silence.

Patrons mesurés sur le kit 2025 : lieu + activité (201 catégories, tronc
= la catégorie), OMS + activité (102, troncs = les codes OMS à 4
caractères, déjà codables), OMS + lieu + activité avec forme `+` (6),
lieu seul (`Y34`), lieu + activité + précision (`X49`), OMS seul (52) et
sans subdivision (10). Les troncs de classe `tronc_composition` (les
catégories à 3 caractères, type 3) sont admis dans la génération par
exception déclarée au profil ; les troncs codables (`V01.0`) y sont
déjà.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass

import polars as pl

from recode_icd.loaders.schemas import (
    ChapitreXxCodesSchema,
    ChapitreXxTroncsSchema,
    ChapitreXxValeursSchema,
)

_RE_CHAPITRE_XX = re.compile(r"^[VWXY]\d{2}")

#: Signature structurelle de la position « activité » : sept valeurs,
#: toujours les mêmes. C'est ce qui amorce la détection sans rien
#: supposer des libellés.
VALEURS_ACTIVITE = frozenset("0123489")
VALEURS_LIEU = frozenset("0123456789")

ROLES = ("lieu", "activite", "oms", "precision")
CLASSES_TRONC = ("tronc_composition", "tronc_codable")
PATRONS = (
    "lieu_activite",
    "oms_activite",
    "oms_lieu_activite",
    "lieu_seul",
    "lieu_activite_precision",
    "oms_seul",
    "aucun",
)


class CompositionError(ValueError):
    """La dérivation ne couvre pas tout le chapitre XX du kit."""


@dataclass(frozen=True)
class Composition:
    """Les trois tables dérivées, validées par leur schéma."""

    troncs: pl.DataFrame
    valeurs: pl.DataFrame
    codes: pl.DataFrame
    #: Variantes de libellé du kit pour une même valeur (rapport).
    variantes: pl.DataFrame
    #: Effectifs par patron (rapport).
    patrons: pl.DataFrame


def _suffixe(libelle: str, libelle_parent: str) -> str | None:
    if libelle_parent and libelle.startswith(libelle_parent):
        return libelle[len(libelle_parent) :].lstrip(", ").strip()
    return None


def _tables_majoritaires(
    codes_xx: list[str], lib: dict[str, str]
) -> tuple[dict[str, str], dict[str, str], pl.DataFrame, dict[str, set[str]], dict[str, set[str]]]:
    """Libellés majoritaires du lieu et de l'activité, et leurs variantes.

    Le lieu est cherché en 4e position sous les catégories, l'activité
    partout où une position porte exactement les sept valeurs
    {0,1,2,3,4,8,9}. La majorité est écrasante (≈ 207 contre 6 pour le
    lieu) : c'est elle qui fait la table.
    """
    lieu_obs: dict[str, Counter[str]] = defaultdict(Counter)
    act_obs: dict[str, Counter[str]] = defaultdict(Counter)
    par_parent: dict[str, list[str]] = defaultdict(list)
    for c in codes_xx:
        if "+" in c:
            continue
        if len(c) > 3:
            par_parent[c[:-1]].append(c)
    for parent, enfants in par_parent.items():
        valeurs = {e[-1] for e in enfants}
        for e in enfants:
            s = _suffixe(lib[e], lib.get(parent, ""))
            if s is None:
                continue
            if valeurs == VALEURS_ACTIVITE:
                act_obs[e[-1]][s] += 1
            elif len(parent) == 3 and valeurs == VALEURS_LIEU:
                lieu_obs[e[-1]][s] += 1
    lieu = {v: obs.most_common(1)[0][0] for v, obs in sorted(lieu_obs.items())}
    act = {v: obs.most_common(1)[0][0] for v, obs in sorted(act_obs.items())}
    # Variantes : une catégorie dont la 4e position porte au moins huit
    # libellés canoniques de lieu est une catégorie « lieu » ; ses autres
    # libellés (« école, lieu public ») sont des variantes du lieu qu'ils
    # désignent — reconnues, jamais corrigées. Les suffixes d'une catégorie
    # à 4e OMS (« autres et sans précision au cours de leur usage
    # thérapeutique », Y40-Y59) ne sont pas des variantes : ils ne comptent
    # pas, même s'ils ont participé aux observations brutes.
    lieu_variantes: dict[str, set[str]] = {v: {s_} for v, s_ in lieu.items()}
    lieu_obs = defaultdict(Counter)
    for parent, enfants in par_parent.items():
        if len(parent) != 3 or {e[-1] for e in enfants} != VALEURS_LIEU:
            continue
        suffixes = {e[-1]: _suffixe(lib[e], lib.get(parent, "")) for e in enfants}
        if sum(suffixes[v] == lieu.get(v) for v in suffixes) < 8:
            continue
        for v, s_ in suffixes.items():
            if s_ is not None:
                lieu_obs[v][s_] += 1
                lieu_variantes[v].add(s_)
    act_variantes = {v: set(obs) for v, obs in act_obs.items()}
    lignes = [
        {"table": t, "valeur": v, "libelle": s, "n": n, "canonique": s == canon[v]}
        for t, obs_t, canon in (("lieu", lieu_obs, lieu), ("activite", act_obs, act))
        for v, obs in sorted(obs_t.items())
        for s, n in obs.most_common()
    ]
    variantes = pl.DataFrame(
        lignes,
        schema={
            "table": pl.String,
            "valeur": pl.String,
            "libelle": pl.String,
            "n": pl.Int64,
            "canonique": pl.Boolean,
        },
    )
    return lieu, act, variantes, lieu_variantes, act_variantes


def _detecte_role(
    enfant: str,
    parent: str,
    lib: dict[str, str],
    lieu: dict[str, set[str]],
    act: dict[str, set[str]],
    roles_amont: list[str],
) -> str:
    """Rôle d'un enfant codable par rapport à son parent — décidé PAR VALEUR.

    Le suffixe du libellé fait foi : la table lieu, la table activité,
    sinon une précision (6e position sous lieu + activité, cas `X49`),
    sinon un code OMS. Décider par valeur et non par position est ce qui
    absorbe `X59`, où la 4e position mêle sous-codes OMS (0, 9) et lieu
    (1-8).
    """
    valeur = enfant.split("+")[-1][-1]
    if "+" in enfant and "+" not in parent:
        return "activite"
    suffixe = _suffixe(lib[enfant], lib.get(parent, ""))
    if suffixe is not None and suffixe in lieu.get(valeur, set()) and "lieu" not in roles_amont:
        return "lieu"
    if suffixe is not None and suffixe in act.get(valeur, set()) and "activite" not in roles_amont:
        return "activite"
    if "activite" in roles_amont:
        return "precision"
    return "oms"


def _enfants(code: str, par_parent: dict[str, list[str]]) -> list[str]:
    """Enfants directs : `X + 1 caractère`, et les formes `X+n` d'un code à 4 caractères."""
    return sorted(par_parent.get(code, [])) + sorted(par_parent.get(code + "+", []))


def derive_composition(atih_codes: pl.DataFrame) -> Composition:
    """Dérive troncs, valeurs et codes composés depuis `atih_codes.parquet`.

    Parcours de l'arbre du kit sur les seuls codes **codables** : les
    branches de type 3 (`W261`…, `X342`… — un ancien encodage « lieu en
    4e position » conservé mort dans le kit) ne sont ni troncs ni
    composées, elles sont comptées au rapport.
    """
    xx = atih_codes.filter(pl.col("code_atih").str.contains(_RE_CHAPITRE_XX.pattern))
    lib = dict(zip(xx["code_atih"], xx["libelle_long"], strict=True))
    maitre = dict(zip(xx["code_atih"], xx["code"], strict=True))
    codable = dict(zip(xx["code_atih"], xx["codable_mco"], strict=True))
    type_mco = dict(zip(xx["code_atih"], xx["type_mco"], strict=True))
    codes_xx = sorted(lib)
    lieu, act, variantes, lieu_variantes, act_variantes = _tables_majoritaires(codes_xx, lib)

    par_parent: dict[str, list[str]] = defaultdict(list)
    for c in codes_xx:
        if not codable[c]:
            continue
        if "+" in c:
            par_parent[c.split("+")[0] + "+"].append(c)
        elif len(c) > 3:
            par_parent[c[:-1]].append(c)

    troncs: list[dict[str, object]] = []
    valeurs: list[dict[str, object]] = []
    for v, s_lieu in lieu.items():
        valeurs.append({"tronc": None, "table": "lieu", "valeur": v, "libelle": s_lieu})
    for v, s_act in act.items():
        valeurs.append({"tronc": None, "table": "activite", "valeur": v, "libelle": s_act})
    composes: list[dict[str, object]] = []
    couverts: set[str] = set()
    patrons_par_cat: dict[str, str] = {}

    def parcourt(
        tronc: str, noeud: str, roles_amont: list[str], acquis: dict[str, str | None], plus: bool
    ) -> tuple[list[str], set[str], set[str]]:
        """Descend sous `noeud` ; retourne (rôles vus, lieux vus, activités vues)."""
        roles_vus: list[str] = []
        lieux: set[str] = set()
        activites: set[str] = set()
        for enfant in _enfants(noeud, par_parent):
            forme_plus = plus or "+" in enfant
            role = _detecte_role(
                enfant, noeud.rstrip("+"), lib, lieu_variantes, act_variantes, roles_amont
            )
            if role == "oms":
                # Un sous-code OMS sous un tronc : il n'est pas composé ; s'il a
                # des enfants codables, il sera tronc à son tour (boucle appelante).
                continue
            valeur = enfant.split("+")[-1][-1]
            acquis_enfant = dict(acquis)
            acquis_enfant[role] = valeur
            if role == "lieu":
                lieux.add(valeur)
            elif role == "activite":
                activites.add(valeur)
            elif role == "precision":
                valeurs.append(
                    {
                        "tronc": maitre[tronc],
                        "table": "precision",
                        "valeur": valeur,
                        "libelle": _suffixe(lib[enfant], lib[noeud]) or lib[enfant],
                    }
                )
            if role not in roles_vus:
                roles_vus.append(role)
            couverts.add(enfant)
            composes.append(
                {
                    "code_atih": enfant,
                    "code": maitre[enfant],
                    "tronc": maitre[tronc],
                    "lieu": acquis_enfant.get("lieu"),
                    "activite": acquis_enfant.get("activite"),
                    "precision": acquis_enfant.get("precision"),
                    "forme_plus": forme_plus,
                }
            )
            r2, l2, a2 = parcourt(tronc, enfant, [*roles_amont, role], acquis_enfant, forme_plus)
            for r in r2:
                if r not in roles_vus:
                    roles_vus.append(r)
            lieux |= l2
            activites |= a2
        return roles_vus, lieux, activites

    def declare_tronc(
        code: str, roles: list[str], lieux: set[str], activites: set[str], est_categorie: bool
    ) -> None:
        composes_sous = [c for c in composes if c["tronc"] == maitre[code]]
        if not composes_sous:
            return
        forme_plus = any(bool(c["forme_plus"]) for c in composes_sous)
        if est_categorie:
            patron = {
                ("lieu",): "lieu_seul",
                ("lieu", "activite"): "lieu_activite",
                ("lieu", "activite", "precision"): "lieu_activite_precision",
            }.get(tuple(roles), "lieu_activite")
        else:
            patron = "oms_lieu_activite" if "lieu" in roles else "oms_activite"
        troncs.append(
            {
                "tronc": maitre[code],
                "tronc_atih": code,
                "patron": patron,
                "positions": roles,
                "forme_plus": forme_plus,
                "classe": "tronc_codable" if codable[code] else "tronc_composition",
                "n_codes_composes": len(composes_sous),
                "libelle": lib[code],
                "valeurs_lieu": "".join(sorted(lieux)),
                "valeurs_activite": "".join(sorted(activites)),
            }
        )
        couverts.add(code)

    for cat in sorted({c[:3] for c in codes_xx}):
        if cat not in lib:
            raise CompositionError(
                f"Catégorie « {cat} » absente du kit alors que des codes en dépendent : "
                f"un kit partiel ne se dérive pas."
            )
        couverts.add(cat)
        enfants4 = _enfants(cat, par_parent)
        if not enfants4:
            patrons_par_cat[cat] = "aucun" if codable[cat] else "type_3_sans_codable"
            continue
        # La catégorie est tronc pour ses enfants « lieu » ; les autres
        # enfants sont des codes OMS, troncs à leur tour s'ils ont des enfants.
        roles, lieux, activites = parcourt(cat, cat, [], {}, False)
        declare_tronc(cat, roles, lieux, activites, est_categorie=True)
        patron_cat = "lieu_activite" if lieux else None
        for oms in enfants4:
            if oms in couverts:
                continue  # composé sous la catégorie (lieu)
            couverts.add(oms)
            if not _enfants(oms, par_parent):
                patron_cat = patron_cat or "oms_seul"
                continue
            roles_oms, lieux_oms, act_oms = parcourt(oms, oms, [], {}, False)
            declare_tronc(oms, roles_oms, lieux_oms, act_oms, est_categorie=False)
            patron_cat = patron_cat or ("oms_lieu_activite" if lieux_oms else "oms_activite")
        patrons_par_cat[cat] = patron_cat or "oms_seul"

    codables_non_couverts = sorted(c for c in codes_xx if codable[c] and c not in couverts)
    if codables_non_couverts:
        raise CompositionError(
            f"{len(codables_non_couverts)} code(s) codable(s) du chapitre XX ni tronc, ni OMS "
            f"sans extension, ni composé : {codables_non_couverts[:8]}."
        )
    branches_mortes = sorted(
        c for c in codes_xx if not codable[c] and c not in couverts and type_mco[c] == 3
    )

    troncs_df = pl.DataFrame(
        troncs,
        schema={
            "tronc": pl.String,
            "tronc_atih": pl.String,
            "patron": pl.String,
            "positions": pl.List(pl.String),
            "forme_plus": pl.Boolean,
            "classe": pl.String,
            "n_codes_composes": pl.Int64,
            "libelle": pl.String,
            "valeurs_lieu": pl.String,
            "valeurs_activite": pl.String,
        },
    ).sort("tronc")
    valeurs_df = (
        pl.DataFrame(
            valeurs,
            schema={
                "tronc": pl.String,
                "table": pl.String,
                "valeur": pl.String,
                "libelle": pl.String,
            },
        )
        .unique(maintain_order=True)
        .sort("table", "tronc", "valeur", nulls_last=False)
    )
    codes_df = pl.DataFrame(
        composes,
        schema={
            "code_atih": pl.String,
            "code": pl.String,
            "tronc": pl.String,
            "lieu": pl.String,
            "activite": pl.String,
            "precision": pl.String,
            "forme_plus": pl.Boolean,
        },
    ).sort("code_atih")
    patrons_df = pl.concat(
        [
            pl.DataFrame(
                {"categorie": list(patrons_par_cat), "patron": list(patrons_par_cat.values())}
            )
            .group_by("patron")
            .len()
            .rename({"len": "n"})
            .with_columns(pl.lit("categories").alias("dimension"), pl.col("n").cast(pl.Int64))
            .select("dimension", pl.col("patron").alias("valeur"), "n"),
            pl.DataFrame(
                {
                    "dimension": ["branches_mortes_type_3", "codes_composes", "troncs"],
                    "valeur": ["codes", "codes", "troncs"],
                    "n": [len(branches_mortes), codes_df.height, troncs_df.height],
                },
                schema={"dimension": pl.String, "valeur": pl.String, "n": pl.Int64},
            ),
        ]
    ).sort("dimension", "valeur")
    ChapitreXxTroncsSchema.validate(troncs_df)
    ChapitreXxValeursSchema.validate(valeurs_df)
    ChapitreXxCodesSchema.validate(codes_df)
    return Composition(
        troncs=troncs_df,
        valeurs=valeurs_df,
        codes=codes_df,
        variantes=variantes,
        patrons=patrons_df,
    )


def decompose(code_atih: str, composition: Composition) -> dict[str, object] | None:
    """La décomposition d'un code composé, ou None s'il n'en est pas un."""
    ligne = composition.codes.filter(pl.col("code_atih") == code_atih)
    return None if ligne.is_empty() else ligne.row(0, named=True)


def explique_suffixe_invalide(code_atih: str, composition: Composition) -> str | None:
    """Pourquoi un code du chapitre XX ne se compose pas : le message, ou None.

    Cherche le tronc le plus long dont le code est un préfixe, puis dit
    quelle position sort de la table.
    """
    if not _RE_CHAPITRE_XX.match(code_atih):
        return None
    troncs = composition.troncs.filter(pl.col("tronc_atih").str.starts_with(code_atih[:3]))
    candidats = [
        r for r in troncs.iter_rows(named=True) if code_atih.startswith(str(r["tronc_atih"]))
    ]
    if not candidats:
        return f"Aucun tronc de composition sous {code_atih[:3]} pour « {code_atih} »."
    tronc = max(candidats, key=lambda r: len(str(r["tronc_atih"])))
    base = str(tronc["tronc_atih"])
    reste = code_atih[len(base) :]
    positions = list(tronc["positions"])
    if reste.startswith("+"):
        if not tronc["forme_plus"]:
            return f"« {code_atih} » : la forme `+` n'existe pas sous le tronc {base}."
        positions, reste = ["activite"], reste[1:]
    tables = {
        "lieu": set(str(tronc["valeurs_lieu"])),
        "activite": set(str(tronc["valeurs_activite"])),
        "precision": set(
            composition.valeurs.filter(
                (pl.col("table") == "precision") & (pl.col("tronc") == tronc["tronc"])
            )["valeur"]
        ),
    }
    for i, car in enumerate(reste):
        if i >= len(positions):
            return f"« {code_atih} » : {len(reste)} caractère(s) après le tronc {base}, {len(positions)} admis ({', '.join(positions)})."
        role = positions[i]
        if car not in tables.get(role, set()):
            admises = ", ".join(sorted(tables.get(role, set()))) or "aucune"
            return f"« {code_atih} » : {role} « {car} » hors table sous {base} (valeurs admises : {admises})."
    return f"« {code_atih} » : suffixe absent du kit sous le tronc {base}."


__all__ = (
    "CLASSES_TRONC",
    "PATRONS",
    "ROLES",
    "VALEURS_ACTIVITE",
    "VALEURS_LIEU",
    "Composition",
    "CompositionError",
    "decompose",
    "derive_composition",
    "explique_suffixe_invalide",
)
