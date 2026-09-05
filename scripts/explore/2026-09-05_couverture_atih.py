"""Couverture ATIH — phase 1 : MESURE, sans modification des livrables.

Question : tout code autorisé en MCO (kit ATIH 2025, Type MCO ≠ 3)
a-t-il une fiche ? Et réciproquement, tout code du maître est-il connu
de l'ATIH ? Le rapport est bidirectionnel et classe chaque écart par
cause. Rien ne se corrige ici ; tout écart inexpliqué reste au rapport.

Sources :
- `data/CIM_ATIH_2025/LIBCIM10MULTI.TXT` (kit ATIH, cf. cim.pdf) via
  `loaders_dev.load_atih_libcim10` ;
- le nested set `merged_codes.parquet` (tous les nœuds) et le CSV maître
  (les feuilles qui ont une fiche), via `load_exploration_context`.

Correspondance des écritures — établie sur les données, testée dans
les deux sens par ce script :
- ATIH : code compact sur 6 positions, point omis, `+` possible en 4e
  ou 5e position (cim.pdf p. 4) ;
- maître : point après le 3e caractère (`A00.0`, `M00.00`, `S37.800`),
  MAIS trois familles s'en écartent — O04 inversé (`O04.-<5e>.<4e>`),
  codes à `+` tantôt ponctués (`B24.+0`) tantôt non (`T08+0`, `F03+00`),
  tiret de 5e position (`M62.8-00`, `S37.8-0`).

La **clé de correspondance** est le code compact ATIH : `cle_maitre`
ramène une écriture du maître à cette clé (suppression du point et du
tiret, dés-inversion d'O04, `+` conservé). Elle est vérifiée injective
sur le maître ; chaque appariement est ensuite contrôlé dans l'autre
sens (la clé du maître est bien le code ATIH, et l'écriture naïve
`point après le 3e caractère` retrouve — ou non — l'écriture du maître :
c'est la classe « notation divergente »).

Produit `scripts/explore/_couverture_atih_artifacts/*.csv` et un résumé
sur stdout. Lancement :

    uv run python scripts/explore/2026-09-05_couverture_atih.py
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import polars as pl

from recode_icd.utils.loaders_dev import load_atih_libcim10, load_exploration_context

ROOT = Path(__file__).resolve().parents[2]
ARTEFACTS = ROOT / "scripts" / "explore" / "_couverture_atih_artifacts"

ctx = load_exploration_context()
assert ctx.merged is not None and ctx.flat is not None
atih = load_atih_libcim10()

# ----------------------------------------------------------------------
# 1. Correspondance des écritures
# ----------------------------------------------------------------------

_RE_O04_FEUILLE = re.compile(r"^(O04)\.-(\d)\.(\d)$")
#: Feuille à tiret du maître : `M62.8-<6e><5e>` — le tiret introduit un
#: regroupement par le DERNIER caractère, et la feuille l'écrit en
#: premier. ATIH écrit `M628<5e><6e>` (vérifié sur les libellés :
#: `M62.8-01` « Rhabdomyolyse - Région scapulaire » = ATIH `M62810`).
_RE_TIRET_FEUILLE = re.compile(r"^([A-Z]\d{2}\.\d)-(\d)(\d)$")
#: Nœud de regroupement à tiret (`O04.-0`, `M62.8-0`, `S37.8-0`) : sans
#: équivalent ATIH — il garde sa forme et ne matche rien. Retirer le
#: tiret ferait collisionner `S37.8-0` (glande surrénale, nœud) avec
#: `S37.80` (sans plaie, feuille).
_RE_TIRET_NOEUD = re.compile(r"^[A-Z]\d{2}\.\d?-\d$")


def cle_maitre(code: str) -> str:
    """Écriture du maître → code compact ATIH (la clé de correspondance).

    Deux familles inversées : `O04.-<5e>.<4e>` → `O04<4e><5e>` et
    `M62.8-<6e><5e>` → `M628<5e><6e>`. Les nœuds de regroupement à tiret
    n'ont pas d'équivalent ATIH et gardent leur forme. Sinon : point
    retiré, `+` conservé.
    """
    if m := _RE_O04_FEUILLE.match(code):
        return f"{m.group(1)}{m.group(3)}{m.group(2)}"
    if m := _RE_TIRET_FEUILLE.match(code):
        return f"{m.group(1).replace('.', '')}{m.group(3)}{m.group(2)}"
    if _RE_TIRET_NOEUD.match(code):
        return code
    return code.replace(".", "")


def ecriture_naive(code_atih: str) -> str:
    """Code compact ATIH → écriture « point après le 3e caractère ».

    Règle candidate à tester : pas de point si le 4e caractère est `+`
    (le point séparerait une lettre d'un `+`), point sinon. C'est la
    règle que suivent `T08+0`, `F03+00`, `C16.9+0`, `S37.800` ; elle
    échoue — par construction — sur O04, sur `B24.+0` et sur `M62.8-00`.
    """
    if len(code_atih) <= 3 or code_atih[3] == "+":
        return code_atih
    return f"{code_atih[:3]}.{code_atih[3:]}"


merged = ctx.merged.with_columns((pl.col("right") == pl.col("left") + 1).alias("feuille"))
categories = merged.filter(pl.col("type") == "category")
csv_feuilles = set(ctx.flat["code"].unique().to_list())

cles: dict[str, str] = {}
collisions: list[tuple[str, str, str]] = []
for code in categories["code"].to_list():
    k = cle_maitre(code)
    if k in cles:
        collisions.append((k, cles[k], code))
    cles[k] = code
assert not collisions, f"cle_maitre n'est pas injective : {collisions[:5]}"

atih_codes = set(atih["code"].to_list())
assert len(atih_codes) == atih.height, "codes ATIH non uniques"
# Sens ATIH → écriture naïve → clé : identité sur tout le kit.
for c in atih_codes:
    assert cle_maitre(ecriture_naive(c)) == c, c

feuille_par_code = dict(zip(categories["code"], categories["feuille"], strict=True))
label_par_code = dict(zip(categories["code"], categories["label"], strict=True))
cle_par_code = {code: cle_maitre(code) for code in categories["code"].to_list()}
code_par_cle = {k: c for c, k in cle_par_code.items()}

# ----------------------------------------------------------------------
# 2. Divergences d'écriture sur les appariements
# ----------------------------------------------------------------------


def famille_divergence(code_atih: str, code_maitre: str) -> str:
    if code_maitre.startswith("O04.-"):
        return "O04 inversé (O04.-<5e>.<4e>)"
    if "+" in code_atih and "." in code_maitre and code_maitre[3] == ".":
        return "code à + ponctué (A99.+9)"
    if "-" in code_maitre:
        return "M62.8 inversé à tiret (A99.9-<6e><5e>)"
    return "autre"


divergences: list[dict[str, str]] = []
for code_atih in sorted(atih_codes):
    code_maitre = code_par_cle.get(code_atih)
    if code_maitre is not None and ecriture_naive(code_atih) != code_maitre:
        divergences.append(
            {
                "code_atih": code_atih,
                "code_maitre": code_maitre,
                "famille": famille_divergence(code_atih, code_maitre),
                "feuille_maitre": str(feuille_par_code[code_maitre]),
                "fiche": str(code_maitre in csv_feuilles),
            }
        )

# ----------------------------------------------------------------------
# 3. (a) codes autorisés MCO sans fiche
# ----------------------------------------------------------------------


def descendants_feuilles(code_maitre: str) -> list[str]:
    ligne = merged.filter(pl.col("code") == code_maitre).row(0, named=True)
    sub = merged.filter(
        (pl.col("left") > ligne["left"]) & (pl.col("right") < ligne["right"]) & pl.col("feuille")
    )
    return sub["code"].to_list()


def ancetre_maitre(code_atih: str) -> str | None:
    """Le plus long préfixe strict du code ATIH qui existe au maître (via la clé)."""
    for n in range(len(code_atih) - 1, 2, -1):
        prefixe = code_atih[:n].rstrip("+")
        if prefixe in code_par_cle:
            return code_par_cle[prefixe]
    return None


chapitre_xx = re.compile(r"^[VWXY]\d{2}")
lignes_a: list[dict[str, object]] = []
for r in atih.filter(pl.col("type_mco") != 3).sort("code").iter_rows(named=True):
    code_atih = r["code"]
    naive = ecriture_naive(code_atih)
    code_maitre = code_par_cle.get(code_atih)
    if naive in csv_feuilles:
        classe, sous_classe = "fiche (écriture directe)", ""
    elif code_maitre is not None and code_maitre in csv_feuilles:
        classe, sous_classe = "notation divergente", famille_divergence(code_atih, code_maitre)
    elif code_maitre is not None and not feuille_par_code[code_maitre]:
        desc = descendants_feuilles(code_maitre)
        avec_fiche = sum(d in csv_feuilles for d in desc)
        classe = "niveau intermédiaire autorisé"
        sous_classe = (
            "descendants tous avec fiche"
            if avec_fiche == len(desc)
            else f"descendants partiellement avec fiche ({avec_fiche}/{len(desc)})"
        )
    elif code_maitre is not None:
        classe, sous_classe = "feuille du nested set sans ligne au maître", ""
    else:
        classe = "réellement absent"
        anc = ancetre_maitre(code_atih)
        if chapitre_xx.match(code_atih):
            sous_classe = "extension chapitre XX (lieu/activité)"
        elif anc is None:
            sous_classe = "aucun ancêtre au maître"
        else:
            sous_classe = "ancêtre au maître : " + ("feuille" if feuille_par_code[anc] else "nœud")
    lignes_a.append(
        {
            "code_atih": code_atih,
            "type_mco": r["type_mco"],
            "libelle_long": r["libelle_long"],
            "classe": classe,
            "sous_classe": sous_classe,
            "code_maitre": code_maitre or "",
            "ancetre_maitre": (ancetre_maitre(code_atih) or "") if code_maitre is None else "",
        }
    )
table_a = pl.DataFrame(lignes_a)

# ----------------------------------------------------------------------
# 4. (b) codes du maître inconnus de l'ATIH
# ----------------------------------------------------------------------

type_par_atih = dict(zip(atih["code"], atih["type_mco"], strict=True))


def prefixe_atih(cle: str) -> str | None:
    for n in range(len(cle) - 1, 2, -1):
        p = cle[:n].rstrip("+")
        if p in atih_codes:
            return p
    return None


lignes_b: list[dict[str, object]] = []
for code_maitre in sorted(csv_feuilles):
    k = cle_par_code.get(code_maitre, cle_maitre(code_maitre))
    if k in atih_codes:
        t = type_par_atih[k]
        classe = "connu de l'ATIH"
        sous_classe = f"type MCO {t}" + (" — interdit en MCO" if t == 3 else "")
        if ecriture_naive(k) != code_maitre:
            sous_classe += " ; notation divergente"
        pref = k
    else:
        pref = prefixe_atih(k)
        if pref is None:
            classe, sous_classe = "réellement absent", "aucune forme à l'ATIH"
        elif len(pref) == 3:
            classe, sous_classe = "réellement absent", "catégorie seule à l'ATIH"
        else:
            classe = "ATIH s'arrête à un niveau supérieur"
            sous_classe = f"préfixe ATIH {pref} (type MCO {type_par_atih[pref]})"
    lignes_b.append(
        {
            "code_maitre": code_maitre,
            "cle": k,
            "classe": classe,
            "sous_classe": sous_classe,
            "code_atih": pref or "",
            "libelle": label_par_code.get(code_maitre, ""),
        }
    )
table_b = pl.DataFrame(lignes_b)

# Nœuds intermédiaires du maître (sans fiche par construction) : que dit l'ATIH ?
lignes_n: list[dict[str, object]] = []
for r in categories.filter(~pl.col("feuille")).sort("left").iter_rows(named=True):
    k = cle_par_code[r["code"]]
    t = type_par_atih.get(k)
    lignes_n.append(
        {
            "code_maitre": r["code"],
            "cle": k,
            "type_mco_atih": "" if t is None else str(t),
            "statut": "inconnu de l'ATIH"
            if t is None
            else ("autorisé MCO (type ≠ 3)" if t != 3 else "père interdit (type 3)"),
        }
    )
table_n = pl.DataFrame(lignes_n)

# ----------------------------------------------------------------------
# 5. Sorties
# ----------------------------------------------------------------------

ARTEFACTS.mkdir(exist_ok=True)
table_a.write_csv(ARTEFACTS / "a_atih_autorises.csv")
table_a.filter(pl.col("classe") != "fiche (écriture directe)").write_csv(
    ARTEFACTS / "a_atih_autorises_sans_fiche.csv"
)
table_b.write_csv(ARTEFACTS / "b_maitre_vs_atih.csv")
table_b.filter(pl.col("classe") != "connu de l'ATIH").write_csv(
    ARTEFACTS / "b_maitre_inconnu_atih.csv"
)
pl.DataFrame(divergences).write_csv(ARTEFACTS / "notations_divergentes.csv")
table_n.write_csv(ARTEFACTS / "noeuds_intermediaires_maitre.csv")


def _bloc(titre: str, table: pl.DataFrame) -> None:
    print(f"\n=== {titre} ===")
    with pl.Config(tbl_rows=60, fmt_str_lengths=80, tbl_hide_dataframe_shape=True):
        print(table)


print(f"ATIH : {atih.height} codes | type MCO : {dict(sorted(Counter(atih['type_mco']).items()))}")
print(f"maître : {categories.height} nœuds catégorie, {csv_feuilles.__len__()} feuilles avec fiche")
print(
    f"appariements par clé : {sum(k in atih_codes for k in cle_par_code.values())} nœuds du maître connus de l'ATIH"
)
_bloc(
    "divergences d'écriture (appariées par clé, écriture naïve ≠ maître)",
    pl.DataFrame(divergences)
    .group_by("famille", "feuille_maitre", "fiche")
    .len()
    .sort("famille", "feuille_maitre"),
)
_bloc(
    "(a) codes autorisés MCO (type ≠ 3) — classes",
    table_a.group_by("classe", "sous_classe").len().sort("classe", "sous_classe"),
)
_bloc(
    "(a) sans fiche — par type MCO et classe",
    table_a.filter(pl.col("classe") != "fiche (écriture directe)")
    .group_by("type_mco", "classe")
    .len()
    .sort("type_mco", "classe"),
)
_bloc(
    "(a) réellement absents — par chapitre (lettre) et sous-classe",
    table_a.filter(pl.col("classe") == "réellement absent")
    .with_columns(pl.col("code_atih").str.slice(0, 1).alias("lettre"))
    .group_by("lettre", "sous_classe")
    .len()
    .sort("lettre", "sous_classe"),
)
_bloc(
    "(b) feuilles du maître — classes",
    table_b.group_by("classe", "sous_classe").len().sort("classe", "sous_classe"),
)
_bloc(
    "(b) inconnus de l'ATIH — par catégorie 3-car (top 25)",
    table_b.filter(pl.col("classe") != "connu de l'ATIH")
    .with_columns(pl.col("code_maitre").str.slice(0, 3).alias("cat"))
    .group_by("cat", "classe")
    .len()
    .sort("len", descending=True)
    .head(25),
)
_bloc(
    "nœuds intermédiaires du maître — statut ATIH", table_n.group_by("statut").len().sort("statut")
)
libelle_atih = dict(zip(atih["code"], atih["libelle_long"], strict=True))
print("\n=== contrôle de l'inversion M62.8-<6e><5e> ↔ M628<5e><6e> (libellés) ===")
for code_maitre in ["M62.8-00", "M62.8-01", "M62.8-05", "M62.8-80", "M62.8-89"]:
    k = cle_maitre(code_maitre)
    print(
        f"  {code_maitre} ↔ {k} | maître : {label_par_code[code_maitre][:55]!r} | ATIH : {libelle_atih.get(k, '∅')[:55]!r}"
    )
print(f"\nArtefacts : {ARTEFACTS}")
