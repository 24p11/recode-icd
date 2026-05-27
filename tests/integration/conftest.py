"""Fixtures pour les tests d'intégration de Phase 2 (merge externe).

Construit en mémoire un mini-pipeline avec 8 codes terminaux + 1 code
intermédiaire (U07.1) + 1 code orphan (X99.9) couvrant les cas
critiques :

- A00.0 : leaf, inclusion OFS "Choléra (classique)" + synonyme ANS
- A01.0 : leaf, simple
- A18.1 : leaf, côté dague d'une paire
- N33.0 : leaf, côté astérisque
- C50.8 : leaf .8 (chapitre II : pas de synthèse de siblings)
- D59.5 : leaf, témoin ORPHANET E
- U07.1 : NON-leaf (right-left=3, parent de U07.10)
- U07.10 : leaf (enfant de U07.1)
- X99.9 : ORPHAN (pas dans merged)
"""

from __future__ import annotations

import polars as pl
import pytest

# ----------------------------------------------------------------------
# Mini pipeline OFS+ANS en mémoire
# ----------------------------------------------------------------------


@pytest.fixture
def merged_df() -> pl.DataFrame:
    """`merged_codes.parquet`-like avec colonnes minimales utilisées
    par flat_csv et merge_external."""
    rows = [
        {"code": "A00.0", "label": "Choléra dû à Vibrio cholerae, biovar cholerae",
         "type": "category", "left": 1, "right": 2},
        {"code": "A01.0", "label": "Fièvre typhoïde",
         "type": "category", "left": 3, "right": 4},
        {"code": "A18.1", "label": "Tuberculose génito-urinaire",
         "type": "category", "left": 5, "right": 6},
        {"code": "N33.0", "label": "Cystite tuberculeuse",
         "type": "category", "left": 7, "right": 8},
        {"code": "C50.8", "label": "Lésion à localisations contiguës du sein",
         "type": "category", "left": 9, "right": 10},
        {"code": "D59.5", "label": "Hémoglobinurie paroxystique nocturne",
         "type": "category", "left": 11, "right": 12},
        # U07.1 non-leaf (right-left=3 → 1 enfant)
        {"code": "U07.1", "label": "COVID-19",
         "type": "category", "left": 13, "right": 16},
        {"code": "U07.10", "label": "COVID-19, forme respiratoire, virus identifié",
         "type": "category", "left": 14, "right": 15},
    ]
    return pl.DataFrame(rows)


@pytest.fixture
def propagated_df() -> pl.DataFrame:
    """Inclusions / exclusions propagées. Sert d'entrée à
    `build_dedup_index` et au pipeline flat_csv."""
    rows = [
        # A00.0 : 1 inclusion OFS "Choléra classique" pour tester l'absorption
        # par INDEX_CIM10 ou ORPHANET d'un libellé identique normalisé.
        {"code": "A00.0", "code_label": "Choléra dû à Vibrio cholerae",
         "code_type": "category", "note_type": "inclusion",
         "texte": "Choléra classique", "source": "OFS",
         "inherited_from": None, "inherited_from_label": None,
         "inherited_from_type": None},
        # A01.0 : 1 exclusion OWL_ANS
        {"code": "A01.0", "code_label": "Fièvre typhoïde",
         "code_type": "category", "note_type": "exclusion",
         "texte": "Porteur de la typhoïde", "source": "OWL_ANS",
         "inherited_from": None, "inherited_from_label": None,
         "inherited_from_type": None},
    ]
    return pl.DataFrame(rows)


@pytest.fixture
def siblings_df() -> pl.DataFrame:
    """Exclusions synthétisées. Empty pour rester simple."""
    return pl.DataFrame(
        schema={
            "code": pl.String,
            "code_label": pl.String,
            "code_type": pl.String,
            "note_type": pl.String,
            "texte": pl.String,
            "source": pl.String,
            "sibling_code": pl.String,
            "sibling_label": pl.String,
        }
    )


@pytest.fixture
def owl_df() -> pl.DataFrame:
    """`owl_codes.parquet`-like : codes ANS avec leurs synonymes."""
    rows = [
        {"code": "A00.0", "synonymes": ["Asiatic cholera"]},
        {"code": "A01.0", "synonymes": []},
        {"code": "A18.1", "synonymes": []},
        {"code": "N33.0", "synonymes": []},
        {"code": "C50.8", "synonymes": []},
        {"code": "D59.5", "synonymes": []},
        {"code": "U07.1", "synonymes": []},
        {"code": "U07.10", "synonymes": []},
    ]
    return pl.DataFrame(rows, schema={"code": pl.String, "synonymes": pl.List(pl.String)})


@pytest.fixture
def ofs_df() -> pl.DataFrame:
    """`ofs_codes.parquet`-like : codes OFS avec leurs synonymes.

    Inclut `A90` qui n'est PAS dans `merged_df` — il sert à tester
    la catégorie `pre_2006_dropped_by_atih` (OFS-only).

    Manque U07.1 et U07.10 (post-2006, ANS seul)."""
    rows = [
        {"code": "A00.0", "synonymes": []},
        {"code": "A01.0", "synonymes": ["Typhoïde"]},
        {"code": "A18.1", "synonymes": []},
        {"code": "N33.0", "synonymes": []},
        {"code": "C50.8", "synonymes": []},
        {"code": "D59.5", "synonymes": []},
        {"code": "A90", "synonymes": []},
    ]
    return pl.DataFrame(rows, schema={"code": pl.String, "synonymes": pl.List(pl.String)})


@pytest.fixture
def dagger_asterisk_df() -> pl.DataFrame:
    """Paire A18.1+ / N33.0* pour tester l'expansion."""
    return pl.DataFrame(
        [
            {
                "association_id": 1,
                "dagger_code": "A18.1",
                "asterisk_code": "N33.0",
                "redundancy_level": "independent",
            }
        ],
        schema={
            "association_id": pl.Int64,
            "dagger_code": pl.String,
            "asterisk_code": pl.String,
            "redundancy_level": pl.String,
        },
    )


# ----------------------------------------------------------------------
# Fixtures externes (sorties des loaders Phase 1, en miniature)
# ----------------------------------------------------------------------


def _make_external(rows: list[dict]) -> pl.DataFrame:
    """Crée un DataFrame au schéma `ExternalSourceSchema`. Les sous-
    champs metadata sont vides pour les tests (non utilisés en Phase 2)."""
    return pl.DataFrame(
        [
            {**r, "metadata": {"orpha_code": "", "relation": ""}}
            for r in rows
        ],
        schema={
            "code": pl.String,
            "libelle": pl.String,
            "type": pl.String,
            "source": pl.String,
            "metadata": pl.Struct({"orpha_code": pl.String, "relation": pl.String}),
        },
    )


@pytest.fixture
def orphanet_df() -> pl.DataFrame:
    """Échantillon ORPHANET — relation E (synonyme) + NTBT (inclusion)
    + cas orphan + cas non-terminal."""
    return _make_external(
        [
            # E : D59.5 / HPN — sera ajouté au CSV.
            {"code": "D59.5", "libelle": "Hémoglobinurie paroxystique nocturne",
             "type": "synonyme", "source": "ORPHANET"},
            {"code": "D59.5", "libelle": "HPN", "type": "synonyme", "source": "ORPHANET"},
            # NTBT : A01.0 / "Salmonella typhi" — sera ajouté comme inclusion.
            {"code": "A01.0", "libelle": "Infection à Salmonella typhi",
             "type": "inclusion", "source": "ORPHANET"},
            # Match exact d'une inclusion OFS → doit être absorbé.
            {"code": "A00.0", "libelle": "Choléra classique",
             "type": "inclusion", "source": "ORPHANET"},
            # Code orphan absent partout → catégorie `truly_absent`
            {"code": "X99.9", "libelle": "Maladie inconnue",
             "type": "synonyme", "source": "ORPHANET"},
            # Code orphan présent en OFS mais pas dans merged →
            # catégorie `pre_2006_dropped_by_atih` (cas dominant en
            # pratique).
            {"code": "A90", "libelle": "Dengue classique",
             "type": "synonyme", "source": "ORPHANET"},
            # Code non-terminal (U07.1) — silencieusement perdu, compté dans summary
            {"code": "U07.1", "libelle": "SARS-CoV-2 disease",
             "type": "synonyme", "source": "ORPHANET"},
        ]
    )


@pytest.fixture
def index_cim10_df() -> pl.DataFrame:
    """Index CIM-10 vol3 — synonyme nouveau + synonyme déjà dans ANS."""
    return _make_external(
        [
            # Nouveau libellé pour A00.0.
            {"code": "A00.0", "libelle": "Choléra (asiatique)",
             "type": "synonyme", "source": "INDEX_CIM10_VOL3"},
            # Match exact d'un synonyme ANS existant pour A00.0
            # ("Asiatic cholera" est dans owl.synonymes).
            # Normalisation tolérante : "Asiatic cholera" ≈ "asiatic cholera"
            {"code": "A00.0", "libelle": "asiatic cholera",
             "type": "synonyme", "source": "INDEX_CIM10_VOL3"},
            # Match inter-externes : "HPN" est déjà ajouté par ORPHANET.
            # Doit être absorbé.
            {"code": "D59.5", "libelle": "HPN",
             "type": "synonyme", "source": "INDEX_CIM10_VOL3"},
        ]
    )


@pytest.fixture
def aphp_df() -> pl.DataFrame:
    """Une feuille AP-HP métier. Inclut un match inter-externe
    (ORPHANET wins over AP-HP)."""
    return _make_external(
        [
            {"code": "C50.8", "libelle": "Tumeur du sein, sites multiples",
             "type": "synonyme", "source": "APHP_DERMATOLOGIE"},
            # Doit être absorbé : ORPHANET a déjà inséré "HPN" pour D59.5.
            {"code": "D59.5", "libelle": "HPN",
             "type": "synonyme", "source": "APHP_DERMATOLOGIE"},
        ]
    )


@pytest.fixture
def rdf_codes_loader_dropped() -> set[str]:
    """Set RDF custom où `Z99.9` est présent — pour tester la
    catégorie `loader_dropped` (code dans RDF mais absent du Parquet
    OWL = absent de `merged_df`)."""
    return {"Z99.9"}


@pytest.fixture
def external_frames(
    orphanet_df: pl.DataFrame,
    index_cim10_df: pl.DataFrame,
    aphp_df: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    """Dict source_label → DataFrame, attendu par `merge_external_sources`."""
    return {
        "ORPHANET": orphanet_df,
        "INDEX_CIM10_VOL3": index_cim10_df,
        "APHP_DERMATOLOGIE": aphp_df,
    }
