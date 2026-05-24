"""Audit des 5425 vraies divergences ANS↔OFS sur les notes typées.

Lit `reports/note_merges.csv` (produit par `merge.find_note_merges`) et
écrit `docs/audit/text_divergence_review.md` avec stats globales,
tirage stratifié de 50 cas et patterns détectables.

Usage :
    uv run python scripts/explore/_build_text_divergence_review.py
"""

from __future__ import annotations

import random
import re
from pathlib import Path

import polars as pl

ROOT = Path(__file__).parent.parent.parent
NOTE_MERGES = ROOT / "reports" / "note_merges.csv"
OUT = ROOT / "docs" / "audit" / "text_divergence_review.md"

SEED = 42


def _chapter_for(code: str) -> str:
    """Mappe le premier caractère du code CIM-10 au chapitre romain.

    Approximation (les codes D et H chevauchent deux chapitres ; on tranche
    sur leur partie numérique quand elle est claire).
    """
    if not code:
        return "?"
    c0 = code[0]
    num_part = "".join(ch for ch in code[1:3] if ch.isdigit())
    try:
        num = int(num_part)
    except ValueError:
        num = -1

    mapping = {
        "A": "I", "B": "I",
        "E": "IV", "F": "V", "G": "VI",
        "I": "IX", "J": "X", "K": "XI",
        "L": "XII", "M": "XIII", "N": "XIV",
        "O": "XV", "P": "XVI", "Q": "XVII",
        "R": "XVIII",
        "S": "XIX", "T": "XIX",
        "V": "XX", "W": "XX", "X": "XX", "Y": "XX",
        "Z": "XXI",
        "U": "XXII",
    }
    if c0 == "C":
        return "II"
    if c0 == "D":
        return "II" if 0 <= num <= 48 else "III"
    if c0 == "H":
        return "VII" if 0 <= num <= 59 else "VIII"
    return mapping.get(c0, "?")


def _length_bucket(diff: int) -> str:
    if diff <= 5:
        return "≤ 5"
    if diff <= 20:
        return "6–20"
    if diff <= 50:
        return "21–50"
    if diff <= 100:
        return "51–100"
    return "> 100"


def _format_table(df: pl.DataFrame, key_col: str, val_col: str = "len") -> str:
    rows = list(df.iter_rows(named=True))
    rows.sort(key=lambda r: -r[val_col])
    width = max(len(str(r[key_col])) for r in rows)
    out = [f"| {key_col:<{width}} | {val_col:>8} |"]
    out.append(f"| {'-' * width} | {'-' * 8} |")
    for r in rows:
        out.append(f"| {r[key_col]:<{width}} | {r[val_col]:>8,} |")
    return "\n".join(out)


def _truncate(text: str, n: int = 200) -> str:
    if text is None:
        return ""
    if len(text) <= n:
        return text
    return text[:n].rstrip() + "…"


def _format_sample(rows: list[dict[str, object]]) -> str:
    out = []
    for r in rows:
        ofs = str(r["texte_retenu"])
        ans = str(r["texte_alternatif_ans"])
        out.append(
            f"- **{r['code']}** ({r['type']}) — `len(OFS)={len(ofs)}` / `len(ANS)={len(ans)}`\n"
            f"  - OFS : {_truncate(ofs)}\n"
            f"  - ANS : {_truncate(ans)}"
        )
    return "\n".join(out)


def main() -> None:
    df_all = pl.read_csv(NOTE_MERGES)
    df = df_all.filter(pl.col("difference_significative"))
    total = len(df)
    print(f"Loaded {total} vraies divergences (sur {len(df_all)} note_merges).")

    # Pré-calcul colonnes dérivées
    df = df.with_columns(
        pl.col("code").map_elements(_chapter_for, return_dtype=pl.String).alias("chapter"),
        pl.col("texte_retenu").str.len_chars().alias("len_ofs"),
        pl.col("texte_alternatif_ans").str.len_chars().alias("len_ans"),
    ).with_columns(
        (pl.col("len_ans") - pl.col("len_ofs")).abs().alias("delta_len"),
    ).with_columns(
        pl.col("delta_len").map_elements(_length_bucket, return_dtype=pl.String).alias("delta_bucket"),
    )

    # --- 1. Statistiques ---
    by_chap = df.group_by("chapter").len().sort("len", descending=True)
    by_type = df.group_by("type").len().sort("len", descending=True)
    by_bucket = df.group_by("delta_bucket").len().sort("len", descending=True)

    # --- 2. Patterns automatiques ---
    code_ref_re = re.compile(r"\[[A-Z]\d{2}(?:\.\d+)?]")
    df_with_pat = df.with_columns(
        pl.col("texte_retenu").map_elements(
            lambda t: bool(code_ref_re.search(t or "")), return_dtype=pl.Boolean,
        ).alias("ofs_has_code_ref"),
        pl.col("texte_alternatif_ans").map_elements(
            lambda t: bool(code_ref_re.search(t or "")), return_dtype=pl.Boolean,
        ).alias("ans_has_code_ref"),
    ).with_columns(
        # Substring : OFS contient ANS (ANS est plus court et inclus dedans)
        pl.struct(["texte_retenu", "texte_alternatif_ans"]).map_elements(
            lambda s: (s["texte_alternatif_ans"] or "") in (s["texte_retenu"] or "")
            and len(s["texte_alternatif_ans"] or "") < len(s["texte_retenu"] or "")
            and len(s["texte_alternatif_ans"] or "") > 0,
            return_dtype=pl.Boolean,
        ).alias("ans_substring_of_ofs"),
        pl.struct(["texte_retenu", "texte_alternatif_ans"]).map_elements(
            lambda s: (s["texte_retenu"] or "") in (s["texte_alternatif_ans"] or "")
            and len(s["texte_retenu"] or "") < len(s["texte_alternatif_ans"] or "")
            and len(s["texte_retenu"] or "") > 0,
            return_dtype=pl.Boolean,
        ).alias("ofs_substring_of_ans"),
    )

    n_ans_longer = df_with_pat.filter(pl.col("len_ans") > pl.col("len_ofs")).height
    n_ofs_longer = df_with_pat.filter(pl.col("len_ofs") > pl.col("len_ans")).height
    n_equal = df_with_pat.filter(pl.col("len_ofs") == pl.col("len_ans")).height
    n_ofs_coderef = df_with_pat["ofs_has_code_ref"].sum()
    n_ans_coderef = df_with_pat["ans_has_code_ref"].sum()
    n_ans_substring = df_with_pat["ans_substring_of_ofs"].sum()
    n_ofs_substring = df_with_pat["ofs_substring_of_ans"].sum()

    # --- 3. Échantillons stratifiés (seed fixe pour reproductibilité) ---
    rng = random.Random(SEED)

    def sample_n(filtered: pl.DataFrame, n: int) -> list[dict[str, object]]:
        rows = filtered.to_dicts()
        rng.shuffle(rows)
        return rows[:n]

    samples_ans_longer = sample_n(
        df_with_pat.filter(pl.col("len_ans") > pl.col("len_ofs") + 5),
        10,
    )
    samples_ofs_longer = sample_n(
        df_with_pat.filter(pl.col("len_ofs") > pl.col("len_ans") + 5),
        10,
    )
    samples_similar = sample_n(
        df_with_pat.filter(pl.col("delta_len") <= 5),
        10,
    )
    samples_clinical = sample_n(
        df_with_pat.filter(pl.col("chapter").is_in(["II", "IX", "XIX"])),
        10,
    )
    samples_random = sample_n(df_with_pat, 10)

    # --- Rapport markdown ---
    OUT.parent.mkdir(parents=True, exist_ok=True)
    md = []
    md.append("# Audit des divergences textuelles OFS ↔ ANS")
    md.append("")
    md.append(
        "Source : `reports/note_merges.csv` (produit par "
        "`merge.find_note_merges`)."
    )
    md.append("")
    md.append(
        f"Périmètre : **{total:,} cas** où `difference_significative=True` "
        "(= les textes OFS et ANS restent différents même après normalisation "
        "complète : casse, accents, ponctuation interne, NBSP)."
    )
    md.append("")
    md.append(
        "Sortie générée par `scripts/explore/_build_text_divergence_review.py` "
        f"(seed={SEED}). Ré-exécutable pour stabilité des échantillons."
    )
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Statistiques globales")
    md.append("")
    md.append("### 1.1 Distribution par chapitre CIM-10")
    md.append("")
    md.append(
        "Chapitre déduit du premier caractère du code (avec disambiguïsation "
        "C/D et H/H pour les chapitres II/III et VII/VIII)."
    )
    md.append("")
    md.append(_format_table(by_chap, "chapter"))
    md.append("")
    md.append("### 1.2 Distribution par type de note")
    md.append("")
    md.append(
        "Le pipeline actuel ne distingue que `inclusion` et `exclusion` "
        "(les `note_editorial` OFS ne sont pas matchées avec OWL, donc "
        "n'apparaissent jamais dans `note_merges.csv`)."
    )
    md.append("")
    md.append(_format_table(by_type, "type"))
    md.append("")
    md.append("### 1.3 Distribution par longueur de divergence")
    md.append("")
    md.append(
        "`delta_len = |len(ANS) - len(OFS)|` (différence absolue en nombre de caractères)."
    )
    md.append("")
    md.append(_format_table(by_bucket, "delta_bucket"))
    md.append("")
    md.append("**Sens du delta** :")
    md.append("")
    md.append(f"- ANS strictement plus long : **{n_ans_longer:,}** cas ({n_ans_longer/total:.0%})")
    md.append(f"- OFS strictement plus long : **{n_ofs_longer:,}** cas ({n_ofs_longer/total:.0%})")
    md.append(f"- Longueurs égales : **{n_equal:,}** cas ({n_equal/total:.0%})")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Tirage stratifié — 50 cas représentatifs")
    md.append("")
    md.append(f"Échantillonnage déterministe (seed={SEED}).")
    md.append("")
    md.append("### 2.1 Cas où ANS est strictement plus long que OFS (10 cas)")
    md.append("")
    md.append(
        "*Hypothèse : ANS contient des précisions additionnelles (code source, "
        "qualificatifs cliniques modernes, etc.) absentes d'OFS 2006.*"
    )
    md.append("")
    md.append(_format_sample(samples_ans_longer))
    md.append("")
    md.append("### 2.2 Cas où OFS est strictement plus long que ANS (10 cas)")
    md.append("")
    md.append(
        "*Hypothèse : OFS conserve des notes historiques détaillées que l'ANS "
        "a synthétisées ou abrégées.*"
    )
    md.append("")
    md.append(_format_sample(samples_ofs_longer))
    md.append("")
    md.append("### 2.3 Cas de longueurs similaires (Δ ≤ 5 caractères, 10 cas)")
    md.append("")
    md.append(
        "*Variations de wording sans changement de volume : reformulations, "
        "synonymes lexicaux, différences d'orthographe légères, etc.*"
    )
    md.append("")
    md.append(_format_sample(samples_similar))
    md.append("")
    md.append("### 2.4 Cas dans les chapitres cliniques majeurs (II, IX, XIX — 10 cas)")
    md.append("")
    md.append(
        "*Chapitres à forte fréquence d'annotation (tumeurs, cardiovasculaire, "
        "traumatismes).*"
    )
    md.append("")
    md.append(_format_sample(samples_clinical))
    md.append("")
    md.append("### 2.5 Cas tirés au hasard (10 cas)")
    md.append("")
    md.append("*Échantillon non-stratifié — contrôle.*")
    md.append("")
    md.append(_format_sample(samples_random))
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 3. Patterns détectés automatiquement")
    md.append("")
    md.append("### 3.1 Présence de références à d'autres codes (`[A18.3]`, etc.)")
    md.append("")
    md.append(
        f"- OFS contient une référence-code : **{n_ofs_coderef:,}** "
        f"({n_ofs_coderef/total:.0%})"
    )
    md.append(
        f"- ANS contient une référence-code : **{n_ans_coderef:,}** "
        f"({n_ans_coderef/total:.0%})"
    )
    md.append("")
    md.append(
        "**Lecture** : les notes d'exclusion citent typiquement le code "
        "de redirection entre crochets (`[A18.3]`). Si ANS systématise "
        "ces références plus que OFS, cela milite pour conserver les "
        "versions ANS quand elles sont strictement enrichies."
    )
    md.append("")
    md.append("### 3.2 Inclusion textuelle (substring)")
    md.append("")
    md.append(
        f"- ANS est un sous-texte d'OFS (ANS ⊂ OFS) : **{n_ans_substring:,}** "
        f"({n_ans_substring/total:.0%})"
    )
    md.append(
        f"- OFS est un sous-texte d'ANS (OFS ⊂ ANS) : **{n_ofs_substring:,}** "
        f"({n_ofs_substring/total:.0%})"
    )
    md.append("")
    md.append(
        "**Lecture** : un texte qui en contient un autre indique souvent que "
        "l'une des deux versions a ajouté des qualificatifs (ex. `« asthme »` "
        "vs `« asthme allergique extrinsèque »`). Le côté qui contient l'autre "
        "est, en première approximation, la version *plus précise*."
    )
    md.append("")
    md.append(
        "### 3.3 Pattern OFS-substring-of-ANS dominant ?"
    )
    md.append("")
    md.append(
        "Le ratio `OFS ⊂ ANS` (ANS plus riche) vs `ANS ⊂ OFS` (OFS plus riche) "
        "donne un signal direct sur la direction d'enrichissement éditorial. "
        "À examiner avant de figer la priorité OFS sur le libellé."
    )
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 4. Questions à trancher pour raffiner la politique")
    md.append("")
    md.append(
        f"1. **Sur les ~{n_ofs_substring:,} cas où OFS ⊂ ANS** (ANS strictement "
        "enrichi par rapport à OFS), faut-il garder OFS (politique actuelle) ou "
        "préférer ANS quand on a la garantie qu'il contient au moins l'info OFS ? "
        "La règle « OFS prime sur le libellé textuel » peut-elle être conditionnée "
        "à `len(OFS) ≥ len(ANS)` ?"
    )
    md.append("")
    md.append(
        f"2. **Sur les ~{n_ans_coderef - n_ofs_coderef if n_ans_coderef > n_ofs_coderef else n_ofs_coderef - n_ans_coderef:,} cas " # noqa: E501
        "où une seule des deux versions porte les références-codes** "
        "(`[X##.#]`), faut-il privilégier la version annotée ? Ce sont des "
        "métadonnées de redirection qui restent utiles au LLM."
    )
    md.append("")
    md.append(
        "3. **Distinction inclusion vs exclusion** : la politique « OFS prime » "
        "s'applique-t-elle uniformément, ou faudrait-il moduler par type de note ? "
        "Les exclusions ANS peuvent comporter des codes [A18.3] de redirection à "
        "préserver ; les inclusions ANS sont plus souvent des reformulations "
        "stylistiques sans valeur clinique ajoutée."
    )
    md.append("")
    md.append(
        "4. **Chapitre XX (causes externes)** : les libellés ANS y sont souvent "
        "très différents d'OFS (révisions OMS post-2006 importantes pour les "
        "accidents de transport). Faut-il un override par chapitre, par exemple "
        "ANS prime pour XX et XXI ?"
    )
    md.append("")
    md.append(
        "5. **Logging suffisant ?** Le rapport actuel `note_merges.csv` log les "
        "alternatives ANS mais le CSV final n'expose qu'une seule version. "
        "Faut-il aussi exporter dans `inclusions_exclusions_synonymes.csv` "
        "les variantes ANS — par exemple comme lignes additionnelles avec "
        "`source=ANS` — quand `difference_significative=True` ? Le LLM "
        "bénéficierait des deux formulations."
    )

    OUT.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
