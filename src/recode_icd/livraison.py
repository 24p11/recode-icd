"""Exports additifs de la livraison (phase A du chantier codeur, 2026-10-18).

Trois livrables, construits à l'assemblage du paquet
(`scripts/preparer_livraison.py`) et versionnés par le nommage de
l'archive — jamais modifiés à la main :

- **`codes.csv`** — les 42 897 codes du kit ATIH, forme pointée ET
  forme `codeur` (`code_atih`, sans point, extension collée), libellé,
  `codable_mco`, `statut_mco`, millésime du kit, version de livraison.
  recode-icd devient la seule source de la liste des codes pour les
  consommateurs : la sélection « codable » selon la notice ATIH est
  faite ici, une fois pour toutes.
- **`formulations.csv`** — le vivier de recherche par mots-clés :
  formulations RENDUES, c'est-à-dire **après** les filtres de qualité
  (R1 périmètre par chapitre, R3 normalisation de l'Index, registre
  des formulations archaïques) et **sans** le plafond R2 — le plafond
  contient les fiches ; pour un index de recherche, c'est le rappel qui
  compte (verdict RF 2026-10-18 : deux usages, deux coupes, même
  vivier).
- **`extensions_preambule.md`** — généré du kit : ce qu'est une
  extension PMSI, la forme `codeur`, le fait qu'il n'existe PAS de
  sémantique transversale des « + » (le sens est porté par le libellé
  de chaque extension — les fiches de navigation portent le critère
  par nœud).
"""

from __future__ import annotations

import polars as pl

from recode_icd import normalize_index
from recode_icd._normalize import normalize_for_match
from recode_icd.cards import PolitiqueFiches
from recode_icd.registre_formulations import RegistreFormulations

#: Familles de la section Formulations dont les lignes du CSV maître
#: sont des formulations (type synonyme, sources Index / AP-HP / CepiDc).
_TYPE_FORMULATION = "synonyme"


def construit_codes_csv(atih: pl.DataFrame, version_livraison: str) -> pl.DataFrame:
    """`codes.csv` : une ligne par code du kit ATIH, aucune exclusion.

    Les deux écritures sont présentes — `code_atih` est LA clé de
    `codeur` (sans point, extension collée : `Z992+0`), `code` la forme
    pointée du maître. `codable_mco` applique la règle gravée
    (type ≠ 3 et non supprimé) ; `statut_mco` détaille (codable,
    cause_externe, pere_interdit, interdit_dp, interdit_dp_dr,
    supprime).
    """
    return (
        atih.select(
            "code_atih",
            "code",
            pl.coalesce("libelle_long", "libelle_court").alias("libelle"),
            "codable_mco",
            "statut_mco",
            "interdit_dp",
            "interdit_dr",
            "interdit_das",
            pl.col("millesime").alias("millesime_kit"),
        )
        .with_columns(pl.lit(version_livraison).alias("version_livraison"))
        .sort("code_atih")
    )


def construit_formulations_csv(
    flat: pl.DataFrame,
    atih: pl.DataFrame,
    outils: PolitiqueFiches,
    version_livraison: str,
) -> tuple[pl.DataFrame, int]:
    """`formulations.csv` : le vivier rendu, sans plafond R2.

    Reproduit la sélection de `cards._candidates_formulations` (R1 par
    famille admise, registre des formulations archaïques, R3 pour
    l'Index, dédup tolérante par code) en CONSERVANT le libellé de
    source — et s'arrête avant R2. La clé est `code_atih` : les
    formulations d'un code inconnu du kit (non codable en MCO par
    définition) sont écartées, leur compte est retourné — jamais au
    silence.
    """
    policy = outils.policy
    config = outils.config_normalisation
    registre: RegistreFormulations = outils.registre

    candidates = flat.filter(pl.col("type") == _TYPE_FORMULATION)
    lignes: list[dict[str, object]] = []
    for sub in candidates.partition_by("code"):
        code = str(sub["code"][0])
        chapitre, blocs = outils.hierarchie_de(code)
        admises = policy.familles_admises(chapitre, blocs)
        vues: set[str] = set()
        for ligne in sub.iter_rows(named=True):
            texte = ligne["texte"]
            if not texte:
                continue
            source = str(ligne["source"])
            famille = policy.famille_de(source)
            if famille not in policy.familles_formulations or famille not in admises:
                continue
            if registre.est_ecartee(code, source, texte):
                continue
            rendue: str | None = texte
            if famille == "INDEX" and config.active:
                rendue = normalize_index.forme_normalisee(texte, outils.lexiques, config)
                if rendue is None:
                    continue
            cle = normalize_for_match(rendue) or ""
            if cle in vues:
                continue
            vues.add(cle)
            lignes.append({"code": code, "formulation": rendue, "source": source})

    brut = pl.DataFrame(lignes)
    joint = brut.join(atih.select("code", "code_atih"), on="code", how="left")
    hors_kit = joint.filter(pl.col("code_atih").is_null()).height
    final = (
        joint.filter(pl.col("code_atih").is_not_null())
        .select("code_atih", "formulation", "source")
        .with_columns(pl.lit(version_livraison).alias("version_livraison"))
        .sort("code_atih", "formulation")
    )
    return final, hors_kit


def redige_preambule_extensions(atih: pl.DataFrame) -> str:
    """`extensions_preambule.md`, généré du kit — jamais écrit à la main."""
    a_extension = atih.filter(pl.col("code_atih").str.contains("+", literal=True))
    n_ext = a_extension.height
    peres = a_extension.with_columns(pl.col("code_atih").str.split("+").list.first().alias("pere"))[
        "pere"
    ].n_unique()
    exemple = atih.filter(pl.col("code_atih").str.starts_with("Z992")).select(
        "code_atih", "libelle_court", "codable_mco"
    )
    lignes_exemple = "\n".join(
        f"| `{r['code_atih']}` | {r['libelle_court']} | {'oui' if r['codable_mco'] else 'non'} |"
        for r in exemple.iter_rows(named=True)
    )
    millesime = str(atih["millesime"][0])
    return f"""# Les extensions PMSI — préambule pour les consommateurs

> Généré du kit ATIH {millesime} ({n_ext} codes à extension « + »,
> portés par {peres} codes souches). Ne pas modifier à la main.

Une **extension PMSI** est un suffixe ajouté par l'ATIH à un code
CIM-10 pour distinguer des situations que l'OMS ne sépare pas. Dans la
forme `codeur` (sans point, extension collée), elle suit un « + » :
`Z992+0`, `K861+8`.

**Trois choses à savoir :**

1. **Il n'existe PAS de sémantique transversale des extensions.** Le
   « +0 » de `Z992+0` (hémodialyse) n'a rien à voir avec le « +0 »
   d'un autre code : le sens est porté par le LIBELLÉ de chaque
   extension. Pour savoir quelle information chercher dans le texte,
   lire les libellés des extensions du code — la fiche de navigation
   du code souche les rassemble avec le critère qui les départage.
2. **Un code souche à extensions peut être lui-même codable.**
   Exemple, la famille `Z992` (kit {millesime}) :

   | Code | Libellé | Codable |
   |---|---|---|
{lignes_exemple}

   Proposer `Z992` n'est donc pas une erreur de RUM : c'est un code
   valide, moins précis. L'affinage vers l'extension est proposé quand
   le texte porte l'information, jamais imposé. À l'inverse, un père
   interdit (`E11`, `R521`) n'est JAMAIS codable : la correction est
   obligatoire (`codes.csv`, colonne `codable_mco`).
3. **L'extension « ni » n'existe pas au kit {millesime}** (0 code sur
   {atih.height}). Une forme comme `E11ni` ne se résoudra jamais ;
   seul « + » introduit une extension.
"""


__all__ = (
    "construit_codes_csv",
    "construit_formulations_csv",
    "redige_preambule_extensions",
)


def construit_descendants_codables(
    ctx_resolution: object,
    atih: pl.DataFrame,
    version_livraison: str,
) -> pl.DataFrame:
    """`descendants_codables.csv` — la liste de la boucle de correction.

    Une ligne par couple (nœud du kit, descendant codable avec fiche).
    Périmètre : tout nœud du kit ayant au moins un descendant codable,
    qu'il soit lui-même NON codable (E11, R521 — correction
    obligatoire) ou CODABLE avec des descendants plus précis (Z992,
    M142, 49 cas — affinage proposé, verdict RF 2026-10-18) : les deux
    régimes de la boucle consomment la même liste.

    **Même logique que le résolveur, pas une seconde implémentation** :
    les descendants viennent de `couverture._descendants` et le filtre
    « avec fiche » de la carte `ctx.fiches` — exactement ce que
    `resoudre_code` renvoie dans `codes_avec_fiche` (invariant testé).
    L'ordre (`ordre_kit`) est l'ordre du fichier du kit ATIH.
    """
    from recode_icd import couverture

    ctx = ctx_resolution  # ContexteResolution (import différé : cycle)
    merged: pl.DataFrame = ctx.merged  # type: ignore[attr-defined]
    fiches: dict[str, str] = ctx.fiches  # type: ignore[attr-defined]

    ordre_kit = {c: i for i, c in enumerate(atih["code_atih"].to_list())}
    kit_par_code: dict[str, tuple[str, str]] = {
        r["code"]: (
            r["code_atih"],
            str(r["libelle_long"] or r["libelle_court"] or ""),
        )
        for r in atih.iter_rows(named=True)
    }
    codable_kit: dict[str, bool] = dict(atih.select("code", "codable_mco").iter_rows())

    lignes: list[dict[str, object]] = []
    for noeud in merged.iter_rows(named=True):
        code = str(noeud["code"])
        if code not in kit_par_code:
            continue  # blocs, chapitres, codes du maître inconnus du kit
        if _entier_nœud(noeud["right"]) == _entier_nœud(noeud["left"]) + 1:
            continue  # feuille : rien à lister
        descendants = couverture._descendants(merged, noeud)
        avec_fiche = [d for d in descendants if d in fiches and d in kit_par_code]
        if not avec_fiche:
            continue
        noeud_atih, noeud_libelle = kit_par_code[code]
        for descendant in avec_fiche:
            code_atih, libelle = kit_par_code[descendant]
            lignes.append(
                {
                    "noeud_atih": noeud_atih,
                    "noeud_libelle": noeud_libelle,
                    # Les deux régimes de la boucle sans re-jointure :
                    # False = correction obligatoire (E11), True =
                    # affinage proposé, jamais imposé (Z992).
                    "noeud_codable": bool(codable_kit.get(code, False)),
                    "code_atih": code_atih,
                    "libelle": libelle,
                    "ordre_kit": ordre_kit.get(code_atih, 10**9),
                    "_ordre_noeud": ordre_kit.get(noeud_atih, 10**9),
                }
            )
    return (
        pl.DataFrame(lignes)
        .sort("_ordre_noeud", "ordre_kit")
        .drop("_ordre_noeud")
        .with_columns(pl.lit(version_livraison).alias("version_livraison"))
    )


def _entier_nœud(valeur: object) -> int:
    assert isinstance(valeur, int)
    return valeur
