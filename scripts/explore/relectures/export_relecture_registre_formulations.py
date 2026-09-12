"""Export CSV des formulations candidates à l'écart pour registre archaïque.

Pourquoi ce script existe
-------------------------
Chantier « registre des formulations » (2026-09-06) : certaines
formulations de la section « Formulations cliniques alternatives »
relèvent d'un registre archaïque (vocabulaire de certificat de décès,
terminologie désuète — « apoplexie congestive », « rachitis »…) qui
dégrade la qualité des fiches pour la génération. Cas d'école : I64,
dont la section est dominée par le nuage « apoplexie » de l'Index vol3.

Ce script produit le support de la relecture : un CSV de candidates au
niveau FORMULATION ENTIÈRE (jamais au niveau terme), à trancher ligne à
ligne par RF. La liste validée deviendra une famille d'exclusion
déclarée (`referentials/curation/registre_formulations.yaml`), appliquée
à l'assemblage des fiches — le CSV maître reste intouché.

⚠ **La sonde n'est PAS un verdict.** « folie à deux », « muguet »,
« tabès », « ictus amnésique », « engorgement du sein » sont du
vocabulaire vivant qui porte pourtant une sonde. C'est précisément
pourquoi la granularité est la formulation entière et le verdict humain
(partage clinicien archaïque / vivant, pas lexical). La colonne
`proposition` n'est qu'une proposition.

Périmètre
---------
- Familles scannées : INDEX, APHP, CEPIDC (les familles de la section
  Formulations ; le point d'application couvrira aussi LLM). OFS et ANS
  ne sont JAMAIS candidates.
- Seules les formulations qui atteignent effectivement une section sont
  listées : R1 (familles admises pour la plage du code) et R3 (entrées
  d'Index écartées par la normalisation) sont appliquées en amont. Une
  entrée masquée par la dédup reste listée : si la gagnante est écartée,
  elle resurgirait.

Signaux
-------
- `sonde:<terme>` : la formulation porte un terme sonde archaïque.
- `+isolement` : la formulation n'est attestée par aucune source
  contemporaine (OFS, ANS, AP-HP) pour le même code. Le signal seul ne
  suffit jamais à lister une ligne (il vaudrait des dizaines de
  milliers de lignes) : il qualifie les lignes à sonde.

Usage
-----
    uv run python scripts/explore/relectures/export_relecture_registre_formulations.py
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path

import polars as pl
from xlsxwriter import Workbook

from recode_icd._normalize import normalize_for_match
from recode_icd.cards import charge_politique
from recode_icd.normalize_index import forme_normalisee
from recode_icd.utils.loaders_dev import load_exploration_context

SORTIE = Path(__file__).parent

#: Version de la règle de sondage. À incrémenter à chaque changement de
#: la liste des sondes ou de la mécanique de sélection, sinon deux
#: relectures se mélangent silencieusement.
VERSION_REGLE = "v1"

#: Familles de la section Formulations visées par le filtre. LLM y sera
#: ajoutée quand une source LLM existera (le point d'application du
#: filtre, lui, la couvrira dès la phase 2).
FAMILLES_SCANNEES = ("INDEX", "APHP", "CEPIDC")

#: Familles contemporaines pour le signal d'isolement.
FAMILLES_CONTEMPORAINES = ("OFS", "ANS", "APHP")


def _plie(texte: str) -> str:
    """Minuscules + accents pliés, pour un matching insensible à la casse."""
    nfkd = unicodedata.normalize("NFKD", texte.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ---------------------------------------------------------------------
# Sondes lexicales
# ---------------------------------------------------------------------
# (terme affiché, motif regex sur texte plié). Les frontières de mot
# protègent les faux amis morphologiques : `rachitis` ≠ `rachitisme`
# (vivant), `croup` ≠ `croupe`, `hysterie` ≠ `hysterectomie`.
SONDES: tuple[tuple[str, str], ...] = (
    ("apoplexie", r"\bapople(?:xie|ctique)"),
    ("ramollissement", r"\bramollissement"),
    ("rachitis", r"\brachitis\b"),
    ("catarrhe", r"\bcatarrhe\b"),
    ("tabès", r"\btabes\b"),
    ("crétinisme", r"\bcretinisme\b"),
    ("ictus", r"\bictus\b"),
    ("hydropisie", r"\bhydropisie\b"),
    ("paralysie générale", r"\bparalysie generale\b"),
    ("sénilité", r"\bsenilite\b"),
    ("croup", r"\bcroup\b"),
    ("muguet", r"\bmuguet\b"),
    ("hystérie", r"\bhyster(?:ie|ique)"),
    ("neurasthénie", r"\bneurasthen"),
    ("engorgement", r"\bengorgement\b"),
    ("scrofule", r"\bscroful"),
    ("chlorose", r"\bchlorose\b"),
    ("phtisie", r"\bphtisi"),
    ("idiotie", r"\bidiotie\b"),
    ("imbécillité", r"\bimbecil?lite\b"),
    ("folie", r"\bfolie\b"),
    ("mongolisme", r"\bmongol"),
    ("consomption", r"\bconsomption\b"),
    ("athrepsie", r"\ba(?:th|t)hrepsie\b|\bathrepsie\b|\batrepsie\b"),
    ("danse de saint-guy", r"\bdanse de saint[ -]guy\b"),
    ("congestion cérébrale", r"\bcongestion cerebrale\b"),
    ("embarras gastrique", r"\bembarras gastrique\b"),
    ("fièvre puerpérale", r"\bfievre puerperale\b"),
    ("gâtisme", r"\bgatisme\b"),
    ("misère physiologique", r"\bmisere physiologique\b"),
    ("coup de sang", r"\bcoup de sang\b"),
    ("fluxion", r"\bfluxion\b"),
    ("chorée de sydenham", r"\bchoree de sydenham\b"),
    # Élargissement mesuré (même registre de certificat de décès) :
    ("aliénation", r"\balienation\b|\baliene\b"),
    ("démence précoce", r"\bdemence precoce\b"),
    ("ivrognerie", r"\bivrogn"),
    ("phlegmasie", r"\bphlegmasie\b"),
    ("poitrinaire", r"\bpoitrinaire\b"),
    ("gourme", r"\bgourme\b"),
    ("sphacèle", r"\bsphacele\b"),
    ("hébéphrénie", r"\bhebephren"),
    ("langueur", r"\blangueur\b"),
)

#: Proposition par défaut portée par chaque sonde : le terme signe un
#: registre désuet, la formulation entière est proposée à l'écart.
MOTIF_DEFAUT = "registre archaïque (certificat de décès / terminologie désuète)"

#: Exceptions vivantes : (regex sur texte plié, préfixes de codes ou
#: None, motif de garde). La première qui matche — et dont le code est
#: dans le périmètre déclaré — fait proposer `garder`. Le périmètre par
#: code évite qu'une garde motivée par une entité précise déborde : la
#: « paralysie générale » n'est une dénomination vivante que pour la
#: neurosyphilis (A52), pas pour une paralysie SAI (G83.9) où elle
#: relève du certificat de décès. Ces motifs sont des PROPOSITIONS — le
#: partage archaïque / vivant appartient à RF.
GARDES: tuple[tuple[str, tuple[str, ...] | None, str], ...] = (
    (r"\bfolie a deux\b", None, "« folie à deux » : entité clinique vivante (F24)"),
    (r"\bmuguet\b", None, "muguet : terme vivant de la candidose buccale (B37.0)"),
    (r"\btabes\b", None, "tabès : terminologie officielle vivante (A52.1, G95)"),
    (r"\bictus amnesique\b", None, "ictus amnésique : entité clinique vivante (G45.4)"),
    (
        r"\bictus larynge\b",
        None,
        "ictus laryngé : dénomination établie de la syncope tussive (ictus laryngis)",
    ),
    (
        r"\bengorgement (?:du sein|mammaire|des seins|lymphatique)",
        None,
        "engorgement mammaire/lymphatique : usage clinique vivant",
    ),
    (r"\bchoree de sydenham\b", None, "chorée de Sydenham : dénomination vivante (I02)"),
    (
        r"\bfievre puerperale\b",
        None,
        "fièvre puerpérale : libellé officiel vivant (O85)",
    ),
    (
        r"\bparalysie generale\b",
        ("A52",),
        "paralysie générale : dénomination encore en usage (neurosyphilis, A52.1)",
    ),
    (r"\b(?:faux )?croup\b", None, "croup : terme officiel vivant (J05.0, diphtérie A36)"),
    (
        r"\bapoplexie utero-placentaire\b",
        None,
        "apoplexie utéro-placentaire : dénomination vivante (syndrome de Couvelaire)",
    ),
    (
        r"\blichen scrofulosorum\b",
        None,
        "lichen scrofulosorum : dénomination vivante (tuberculide)",
    ),
    (
        r"\bhebephren",
        None,
        "hébéphrénie : terminologie CIM-10 vivante (F20.1, schizophrénie hébéphrénique)",
    ),
    (
        r"\btache mongol|\bnaevus mongolien\b",
        None,
        "tache/naevus mongolien : terme dermatologique classique (mélanocytose dermique)",
    ),
    (
        r"\bramollissement de l'ongle\b|\bramollissement (?:de l')?ongle",
        ("L60",),
        "sens propre vivant (hapalonychie — ramollissement unguéal)",
    ),
)


def _sonde_pour(plie: str) -> str | None:
    for terme, motif in SONDES:
        if re.search(motif, plie):
            return terme
    return None


def _garde_pour(plie: str, code: str) -> str | None:
    for motif, perimetres, justification in GARDES:
        if re.search(motif, plie) and (
            perimetres is None or any(code.startswith(p) for p in perimetres)
        ):
            return justification
    return None


def main() -> None:
    ctx = load_exploration_context()
    flat = ctx.flat.collect() if isinstance(ctx.flat, pl.LazyFrame) else ctx.flat
    merged = ctx.merged.collect() if isinstance(ctx.merged, pl.LazyFrame) else ctx.merged
    outils = charge_politique(merged)
    policy = outils.policy
    config = outils.config_normalisation

    # -- attestations contemporaines par code (signal d'isolement) -----
    # Au passage, le libellé officiel de chaque code (celui du CSV
    # maître, le même que le titre de fiche) pour la lecture humaine.
    contemporaines: dict[str, set[str]] = {}
    libelles: dict[str, str] = {}
    for ligne in flat.iter_rows(named=True):
        famille = policy.famille_de(ligne["source"])
        if famille not in FAMILLES_CONTEMPORAINES:
            continue
        cle = normalize_for_match(ligne["texte"])
        if cle:
            contemporaines.setdefault(ligne["code"], set()).add(cle)
    for code, libelle in flat.select("code", "libelle").unique().iter_rows():
        if libelle:
            libelles.setdefault(code, libelle)
        cle = normalize_for_match(libelle)
        if cle:
            contemporaines.setdefault(code, set()).add(cle)

    # -- balayage des formulations rendues (R1 + R3) -------------------
    lignes: list[dict[str, object]] = []
    ecartees_r3_avec_sonde = 0
    for ligne in flat.iter_rows(named=True):
        texte = ligne["texte"]
        if not texte:
            continue
        famille = policy.famille_de(ligne["source"])
        if famille not in FAMILLES_SCANNEES:
            continue
        code = str(ligne["code"])
        chapitre, blocs = outils.hierarchie_de(code)
        if famille not in policy.familles_admises(chapitre, blocs):
            continue  # R1 : jamais rendue pour cette plage
        rendue: str | None = texte
        if famille == "INDEX" and config.active:
            rendue = forme_normalisee(texte, outils.lexiques, config)
            if rendue is None:
                if _sonde_pour(_plie(texte)):
                    ecartees_r3_avec_sonde += 1
                continue  # R3 : jamais rendue
        # La sonde se juge sur la FORME RENDUE : c'est elle que le
        # lecteur de la fiche voit. « Catalepsie (hystérique) » rend
        # « catalepsie » — aucun archaïsme n'atteint la section, la
        # formulation n'est pas candidate.
        plie = _plie(rendue)
        terme = _sonde_pour(plie)
        if terme is None:
            continue
        cle = normalize_for_match(texte)
        isolee = cle not in contemporaines.get(code, set())
        garde = _garde_pour(plie, code)
        lignes.append(
            {
                "code": code,
                "libelle_officiel": libelles.get(code, ""),
                "chapitre": chapitre or "",
                "forme_rendue": rendue,
                "forme_source": texte,
                "source": ligne["source"],
                "signal": f"sonde:{terme}" + ("+isolement" if isolee else ""),
                "proposition": "garder" if garde else "ecarter",
                "motif": garde or MOTIF_DEFAUT,
                "version_regle": VERSION_REGLE,
            }
        )

    lignes.sort(
        key=lambda ligne: (str(ligne["code"]), str(ligne["forme_source"]), str(ligne["source"]))
    )
    df = pl.DataFrame(lignes)
    chemin = SORTIE / f"relecture_registre_formulations_{VERSION_REGLE}.csv"
    df.write_csv(chemin)

    # -- volumétrie ----------------------------------------------------
    print(f"{len(lignes)} candidates → {chemin}")
    print(f"(entrées d'Index déjà écartées par R3 et portant une sonde : {ecartees_r3_avec_sonde})")
    print("\nPar source :")
    print(df.group_by("source", "proposition").len().sort("source", "proposition"))
    print("\nPar chapitre :")
    print(df.group_by("chapitre", "proposition").len().sort("chapitre", "proposition"))
    print("\nPar sonde :")
    sondes = Counter(str(ligne["signal"]).split("+")[0] for ligne in lignes)
    for signal, n in sondes.most_common():
        print(f"  {signal}: {n}")

    # -- impact fiches si toutes les propositions « ecarter » passaient -
    ecartes_par_code: dict[str, set[tuple[str, str]]] = {}
    for ligne_csv in lignes:
        if ligne_csv["proposition"] == "ecarter":
            ecartes_par_code.setdefault(str(ligne_csv["code"]), set()).add(
                (str(ligne_csv["forme_source"]), str(ligne_csv["source"]))
            )

    impact: list[dict[str, object]] = []
    for code, ecartes in sorted(ecartes_par_code.items()):
        sub = flat.filter(pl.col("code") == code)
        chapitre, blocs = outils.hierarchie_de(code)
        admises = policy.familles_admises(chapitre, blocs)
        avant: list[str] = []
        apres: list[str] = []
        for ligne in sub.iter_rows(named=True):
            texte = ligne["texte"]
            if not texte:
                continue
            famille = policy.famille_de(ligne["source"])
            if famille not in FAMILLES_SCANNEES or famille not in admises:
                continue
            rendue = texte
            if famille == "INDEX" and config.active:
                rendue = forme_normalisee(texte, outils.lexiques, config)
                if rendue is None:
                    continue
            avant.append(rendue)
            if (texte, ligne["source"]) not in ecartes:
                apres.append(rendue)

        def _n(formes: list[str]) -> int:
            return len({normalize_for_match(f) or "" for f in formes})

        n_avant, n_apres = _n(avant), _n(apres)
        if n_apres <= 2:
            impact.append(
                {
                    "code": code,
                    "libelle_officiel": libelles.get(code, ""),
                    "chapitre": chapitre or "",
                    "formulations_avant": n_avant,
                    "formulations_apres": n_apres,
                    "section_videe": n_apres == 0,
                    "version_regle": VERSION_REGLE,
                }
            )

    df_impact = pl.DataFrame(impact)
    chemin_impact = SORTIE / f"relecture_registre_formulations_{VERSION_REGLE}_fiches_impact.csv"
    df_impact.write_csv(chemin_impact)
    videes = sum(1 for i in impact if i["section_videe"])
    print(
        f"\nFiches touchées par ≥1 écart proposé : {len(ecartes_par_code)} ; "
        f"section vidée : {videes} ; réduite à ≤2 : {len(impact) - videes} → {chemin_impact}"
    )

    # -- classeur xlsx de relecture (les deux tables, en-têtes figés) --
    # Support de la relecture humaine ; les CSV restent la trace
    # canonique (diffables, committés).
    chemin_xlsx = SORTIE / f"relecture_registre_formulations_{VERSION_REGLE}.xlsx"
    with Workbook(chemin_xlsx) as classeur:
        df.write_excel(workbook=classeur, worksheet="candidates", autofit=True, freeze_panes="A2")
        df_impact.write_excel(
            workbook=classeur, worksheet="fiches_impact", autofit=True, freeze_panes="A2"
        )
    print(f"Classeur de relecture : {chemin_xlsx}")
    print("Remplir/corriger la colonne `proposition` : ecarter | garder — le verdict RF fait foi.")


if __name__ == "__main__":
    main()
