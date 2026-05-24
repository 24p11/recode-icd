from __future__ import annotations

import pandera.polars as pa

_CODE_RE = r"^[A-Z][0-9A-Z.+\-]*$"


class OwlCodesSchema(pa.DataFrameModel):
    code: str = pa.Field(str_matches=_CODE_RE)
    label: str = pa.Field(nullable=True)
    type: str = pa.Field(isin=["chapter", "block", "category"])
    depth: int = pa.Field(ge=0)
    left: int = pa.Field(ge=1)
    right: int = pa.Field(ge=1)
    path: str = pa.Field()
    synonymes: list[str] = pa.Field(nullable=True)
    inclusion_note: str = pa.Field(nullable=True)
    exclusion_notes: list[str] = pa.Field(nullable=True)
    definitions: list[str] = pa.Field(nullable=True)
    scope_notes: list[str] = pa.Field(nullable=True)
    structured_exclusions: list[str] = pa.Field(nullable=True)

    class Config:
        strict = True
        coerce = False


class DaggerAsteriskSchema(pa.DataFrameModel):
    asterisk_code: str = pa.Field(str_matches=_CODE_RE)
    dagger_code: str = pa.Field(str_matches=_CODE_RE)
    evidence: list[str] = pa.Field()
    source: str = pa.Field(eq="OWL_ANS")

    class Config:
        strict = True
        coerce = False


class OfsCodesSchema(pa.DataFrameModel):
    code: str = pa.Field()
    abbrev: str = pa.Field()
    label: str = pa.Field(nullable=True)
    type: str = pa.Field(isin=["chapter", "block", "category"])
    ofs_type: str = pa.Field(isin=["C", "G", "U", "K", "S", "D"])
    depth: int = pa.Field(ge=0)
    left: int = pa.Field(ge=1)
    right: int = pa.Field(ge=1)
    path: str = pa.Field()
    synonymes: list[str] = pa.Field(nullable=True)
    inclusions: list[str] = pa.Field(nullable=True)
    exclusions_text: list[str] = pa.Field(nullable=True)
    exclusions_redirect: list[str] = pa.Field(nullable=True)
    notes_editorial: list[str] = pa.Field(nullable=True)

    class Config:
        strict = True
        coerce = False


class OfsDaggerAsteriskSchema(pa.DataFrameModel):
    start_code: str = pa.Field()
    end_code: str = pa.Field()
    daget: str = pa.Field(isin=["F", "G", "H", "S", "T", "U"], nullable=True)
    plus: bool = pa.Field()
    source: str = pa.Field(eq="OFS")

    class Config:
        strict = True
        coerce = False


class EnrichedDaggerAsteriskSchema(pa.DataFrameModel):
    """Table relationnelle dague/astérisque consolidée (objectif 2 du
    projet). Une ligne par paire sémantique unique (dagger_sid,
    asterisk_sid), agrégeant toutes les lignes DAGSTAR qui pointent
    sur cette combinaison. Cf. docs/source_mapping.md §"Table DAGSTAR
    enrichie"."""

    association_id: int = pa.Field(ge=0, unique=True)
    dagger_code: str = pa.Field(nullable=True)
    dagger_label: str = pa.Field(nullable=True)
    asterisk_code: str = pa.Field(nullable=True)
    asterisk_label: str = pa.Field(nullable=True)
    combination_labels: list[str] = pa.Field()
    levels_present: list[str] = pa.Field()
    redundancy_level: str = pa.Field(
        isin=["none", "independent", "subordinate"]
    )
    source_lids: list[int] = pa.Field()

    class Config:
        strict = True
        coerce = False


class SiblingExclusionsSchema(pa.DataFrameModel):
    code: str = pa.Field(str_matches=_CODE_RE)
    code_label: str = pa.Field(nullable=True)
    code_type: str = pa.Field(eq="category")
    note_type: str = pa.Field(eq="exclusion")
    texte: str = pa.Field()
    source: str = pa.Field(eq="SYNTHESIZED_SIBLING")
    sibling_code: str = pa.Field(str_matches=_CODE_RE)
    sibling_label: str = pa.Field(nullable=True)

    class Config:
        strict = True
        coerce = False


class PropagatedNotesSchema(pa.DataFrameModel):
    code: str = pa.Field(str_matches=_CODE_RE)
    code_label: str = pa.Field(nullable=True)
    code_type: str = pa.Field(isin=["chapter", "block", "category"])
    note_type: str = pa.Field(isin=["inclusion", "exclusion", "note_editorial"])
    texte: str = pa.Field()
    source: str = pa.Field(isin=["OFS", "OWL_ANS"])
    inherited_from: str = pa.Field(nullable=True)
    inherited_from_label: str = pa.Field(nullable=True)
    inherited_from_type: str = pa.Field(nullable=True)

    class Config:
        strict = True
        coerce = False


class MergedCodesSchema(pa.DataFrameModel):
    code: str = pa.Field(str_matches=_CODE_RE)
    label: str = pa.Field(nullable=True)
    type: str = pa.Field(isin=["chapter", "block", "category"])
    depth: int = pa.Field(ge=0)
    left: int = pa.Field(ge=1)
    right: int = pa.Field(ge=1)
    path: str = pa.Field()
    inclusions: list[str] = pa.Field()
    inclusions_per_source: list[str] = pa.Field()
    inclusions_source: str = pa.Field(isin=["OFS", "OWL_ANS", "OFS+OWL_ANS", "none"])
    exclusions: list[str] = pa.Field()
    exclusions_per_source: list[str] = pa.Field()
    exclusions_source: str = pa.Field(isin=["OFS", "OWL_ANS", "OFS+OWL_ANS", "none"])
    exclusions_redirect: list[str] = pa.Field(nullable=True)
    structured_exclusions: list[str] = pa.Field(nullable=True)
    notes_editorial: list[str] = pa.Field(nullable=True)
    definitions: list[str] = pa.Field(nullable=True)
    scope_notes: list[str] = pa.Field(nullable=True)
    synonymes: list[str] = pa.Field()
    has_ofs_match: bool = pa.Field()

    class Config:
        strict = True
        coerce = False
