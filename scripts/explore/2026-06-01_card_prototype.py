"""Prototype : génère les fiches markdown des 7 codes témoins.

Toute la logique métier (sections, helpers, orchestration) vit dans
`src/recode_icd/cards.py`. Ce script reste un wrapper minimal pour les
flux interactifs et la vérification rapide de quelques codes
témoins.

Pour générer la bibliothèque complète : voir
`uv run recode-icd cards build` ou
`uv run python scripts/build_cards_library.py`.
"""

from __future__ import annotations

import random
from pathlib import Path

from recode_icd.cards import DEFAULT_SEED, build_card
from recode_icd.utils.loaders_dev import load_exploration_context

WITNESS_CODES = ["M01.08", "M01.05", "M00.00", "A18.1", "J18.8", "R51", "U07.1"]
OUTPUT_DIR = Path("outputs/cards_prototype")


def main() -> None:
    ctx = load_exploration_context(with_external=True)
    rng = random.Random(DEFAULT_SEED)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for code in WITNESS_CODES:
        card = build_card(code, ctx, rng)
        out_path = OUTPUT_DIR / f"{code}.md"
        out_path.write_text(card, encoding="utf-8")
        print(f"écrit : {out_path}  ({len(card)} chars)")


if __name__ == "__main__":
    main()
