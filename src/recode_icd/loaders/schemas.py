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
    redundancy_level: str = pa.Field(isin=["none", "independent", "subordinate"])
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


class FlatCsvSchema(pa.DataFrameModel):
    """Schéma du CSV maître final à 9 colonnes (cf docs/source_mapping.md
    §"Schéma final du CSV principal", §"Couples dague/astérisque :
    politique de représentation" et §"Propagation des notes
    hiérarchiques").

    Refonte 2026-05-30 : suppression de l'expansion par paire
    dague/astérisque. Chaque note d'un code apparaît une seule fois,
    avec deux flags booléens (`is_dagger_in_pair` / `is_asterisk_in_pair`)
    signalant la participation à la mécanique dague/astérisque sans
    détailler les paires (détail dans `dagger_asterisk.parquet`).
    """

    code: str = pa.Field(str_matches=_CODE_RE)
    libelle: str = pa.Field(nullable=True)
    type: str = pa.Field(isin=["inclusion", "exclusion", "synonyme"])
    source: str = pa.Field()
    texte: str = pa.Field(nullable=True)
    source_level: str = pa.Field(isin=["chapter", "block", "category", "code"])
    inherited_from_code: str = pa.Field(nullable=True)
    is_dagger_in_pair: bool = pa.Field()
    is_asterisk_in_pair: bool = pa.Field()

    class Config:
        strict = True
        coerce = False


class LexiqueRectionsSchema(pa.DataFrameModel):
    """Rections attestées dans le corpus : `(nom, joint, occurrences)`.

    Construit sur **toutes** les sources, Index compris — la syntaxe
    interne des entrées d'index est du français naturel et témoigne
    valablement du genre. Cf. le pitfall des trois lexiques dans
    `recode_icd.lexicons`.
    """

    nom: str = pa.Field()
    joint: str = pa.Field(
        isin=["du", "de la", "de l'", "des", "de", "au", "à la", "à l'", "aux", "à"]
    )
    occurrences: int = pa.Field(ge=1)

    class Config:
        strict = True
        coerce = False


class LexiqueCasseSchema(pa.DataFrameModel):
    """Mots attestés en minuscule, **Index exclu**.

    L'Index capitalise toute tête d'entrée par convention : il ne peut
    pas servir de témoin de la casse naturelle d'un terme.
    """

    mot: str = pa.Field(str_matches=r"^[a-zà-ÿ][\wà-ÿ-]*$", unique=True)

    class Config:
        strict = True
        coerce = False


class LexiqueJuxtapositionSchema(pa.DataFrameModel):
    """Juxtapositions adjectivales nues, **CepiDc exclu**.

    CepiDc est télégraphique et supprime les articles : l'inclure ferait
    passer tout nom pour un adjectif.
    """

    mot: str = pa.Field(unique=True)
    occurrences: int = pa.Field(ge=1)

    class Config:
        strict = True
        coerce = False


# ---------------------------------------------------------------------
# Recommandations du guide méthodologique MCO
# ---------------------------------------------------------------------
#: Types de consigne (§4.1 de la note de conception).
TYPES_RECOMMANDATION = (
    "regle_position",
    "interdiction",
    "condition_emploi",
    "definition",
    "regle_association",
)

#: Rôles d'un code dans une consigne (§4.2). Huit modalités.
#: `interdit_DP` / `interdit_DR` sont plus fins que `interdit` : ils
#: interdisent une POSITION, pas l'emploi du code (« les codes du
#: chapitre XX ne doivent jamais être utilisés en DP ou DR » n'interdit
#: pas ces codes, il interdit deux positions).
ROLES_RECOMMANDATION = (
    "DP",
    "DR",
    "DAS",
    "interdit",
    "interdit_association",
    "interdit_DP",
    "interdit_DR",
    "contexte",
)

#: Centralité : le code est-il l'objet de la consigne, ou seulement cité
#: en illustration ? Binaire et volontairement : la fiche de F32 n'a pas
#: vocation à recevoir la consigne AVC parce que F32 y figure comme
#: exemple de manifestation.
CENTRALITES_RECOMMANDATION = ("sujet", "exemple")


class RecommendationsSchema(pa.DataFrameModel):
    """Consignes du guide méthodologique — une ligne par consigne."""

    rec_id: str = pa.Field(str_matches=r"^GM\d{4}-[IVX]+-[A-Z0-9]+-\d{2}$", unique=True)
    millesime: str = pa.Field(nullable=False)
    localisation: str = pa.Field(nullable=False)
    situation: str = pa.Field(nullable=False)
    type: str = pa.Field(isin=TYPES_RECOMMANDATION)
    texte: str = pa.Field(nullable=False)
    condition: str = pa.Field(nullable=True)

    class Config:
        strict = True
        coerce = False


class RecommendationCodesSchema(pa.DataFrameModel):
    """Associations consigne ↔ expression de codes.

    `code_expr` est conservée **telle qu'écrite** dans la table curée :
    c'est elle qui porte la spécificité (cf. `recommendations.code_expr`).
    """

    rec_id: str = pa.Field(nullable=False)
    code_expr: str = pa.Field(nullable=False)
    role: str = pa.Field(isin=ROLES_RECOMMANDATION)
    centralite: str = pa.Field(isin=CENTRALITES_RECOMMANDATION)
    condition: str = pa.Field(nullable=True)

    class Config:
        strict = True
        coerce = False


class ResolvedRecommendationCodesSchema(pa.DataFrameModel):
    """Associations **résolues** — une ligne par (rec_id, code_expr, code).

    `code_expr` est conservée à côté de `code` : l'association compacte
    reste récupérable par déduplication, donc rien n'est perdu par
    l'expansion. `specificite` est la valeur entière de `TypeExpr`, pour
    que le consommateur trie sans avoir à re-parser.
    """

    rec_id: str = pa.Field(nullable=False)
    code_expr: str = pa.Field(nullable=False)
    code: str = pa.Field(nullable=False)
    role: str = pa.Field(isin=ROLES_RECOMMANDATION)
    centralite: str = pa.Field(isin=CENTRALITES_RECOMMANDATION)
    condition: str = pa.Field(nullable=True)
    type_expr: str = pa.Field(isin=("CODE", "CATEGORIE", "PLAGE", "CHAPITRE"))
    specificite: int = pa.Field(ge=0, le=3)

    class Config:
        strict = True
        coerce = False
