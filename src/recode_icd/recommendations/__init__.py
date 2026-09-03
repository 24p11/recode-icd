"""Base de connaissance des recommandations du guide méthodologique MCO.

Livrable séparé (`recommendations.parquet` +
`recommendation_codes.parquet`), sur le patron de
`dagger_asterisk.parquet` : le CSV maître n'est pas modifié.

⚠ **L'extraction LLM ne rentre jamais dans le pipeline.** Le pipeline
déterministe part de tables curées committées
(`data/guide_mco/*_curated.csv`), validées humainement ligne à ligne —
même pattern que `dagger_curation.csv`. Les fichiers de travail de
`data/guide_mco/extraction/` sont une trace de curation, pas une entrée.
"""

from recode_icd.recommendations.code_expr import (
    CodeExprError,
    ExpressionCode,
    TypeExpr,
    parse_code_expr,
)
from recode_icd.recommendations.rendu import consignes_pour, rendre_section_consignes
from recode_icd.recommendations.resolution import ResolutionError, cle_de_tri, resout

__all__ = (
    "CodeExprError",
    "ExpressionCode",
    "ResolutionError",
    "TypeExpr",
    "cle_de_tri",
    "consignes_pour",
    "parse_code_expr",
    "rendre_section_consignes",
    "resout",
)
