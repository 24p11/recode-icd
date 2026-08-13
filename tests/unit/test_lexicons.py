"""Les trois lexiques et leurs trois périmètres.

**Ce fichier existe pour empêcher une fusion.** Les trois lexiques sont
construits sur des sous-ensembles différents du CSV, et chaque exclusion
répond à une propriété linguistique distincte de la source écartée. Un
repreneur pressé les unifiera « par simplification » ; les tests
ci-dessous cassent alors, chacun avec un message qui dit laquelle des
trois garanties vient d'être perdue.

Les trois cas témoins sont mesurés, pas supposés :

- `Borrelia` / `Lipschütz` — noms propres à préserver ⇒ absents du
  lexique de **casse**, donc jamais minusculés ;
- `cerveau` — substantif ⇒ si CepiDc entrait dans le comptage de
  **juxtaposition**, son ratio tomberait à 0,46 et « hypoplasie du
  cerveau » serait cassé ;
- `médullaire` — adjectif ⇒ doit rester massivement juxtaposé.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from recode_icd import lexicons
from recode_icd.policy import load_policy

pytestmark = pytest.mark.unit

_PROCESSED = Path(__file__).resolve().parents[2] / "referentials" / "processed"


@pytest.fixture(scope="module")
def lex():  # type: ignore[no-untyped-def]
    if not (_PROCESSED / lexicons.RECTIONS_FILENAME).is_file():
        pytest.skip("Lexiques absents. Lancer `uv run recode-icd build lexicons` d'abord.")
    return lexicons.load_lexicons(_PROCESSED)


# ----------------------------------------------------------------------
# Périmètre 1 — rections : Index INCLUS
# ----------------------------------------------------------------------


def test_rections_couvrent_les_genres_usuels(lex) -> None:  # type: ignore[no-untyped-def]
    """Le genre vient du corpus : trois formes distinctes attendues."""
    assert lex.rections["cerveau"].get("du", 0) > 0, "« du cerveau » attendu"
    assert lex.rections["rate"].get("de la", 0) > 0, "« de la rate » attendu"
    assert lex.rections["estomac"].get("de l'", 0) > 0, (
        "« de l'estomac » attendu — si absent, le motif d'attestation a "
        "probablement perdu les formes élidées (piège du `\\s+`)."
    )


def test_rections_incluent_lapport_de_lindex(lex) -> None:  # type: ignore[no-untyped-def]
    """L'Index doit être DANS ce lexique — sa syntaxe interne est naturelle.

    Contre-test du pitfall : si quelqu'un excluait l'Index ici « par
    cohérence » avec le lexique de casse, le lexique perdrait ~265 noms.
    """
    csv = pl.read_csv(
        _PROCESSED / "inclusions_exclusions_synonymes.csv", infer_schema_length=200_000
    )
    policy = load_policy()
    avec = lexicons.build_lexique_rections(csv)["nom"].n_unique()
    index_labels = [
        lib for lib in csv["source"].unique().to_list() if policy.famille_de(lib) == "INDEX"
    ]
    sans = lexicons.build_lexique_rections(csv.filter(~pl.col("source").is_in(index_labels)))[
        "nom"
    ].n_unique()
    assert avec > sans, (
        f"L'Index doit enrichir le lexique de rections ({avec} vs {sans}). "
        f"S'il est exclu, relire le pitfall des trois lexiques."
    )


# ----------------------------------------------------------------------
# Périmètre 2 — casse : Index EXCLU
# ----------------------------------------------------------------------


@pytest.mark.parametrize("nom_propre", ["borrelia", "lipschütz", "eberth", "stellantchasmus"])
def test_casse_ne_contient_pas_les_noms_propres(lex, nom_propre: str) -> None:  # type: ignore[no-untyped-def]
    """Un nom propre non attesté en minuscule doit garder sa capitale.

    Si ce test casse, l'Index a probablement été admis dans le lexique de
    casse : il capitalise toute tête d'entrée, donc n'importe quel mot y
    apparaît — et `Borrelia` serait minusculé.
    """
    assert not lex.est_minuscule_attestee(nom_propre)


@pytest.mark.parametrize("nom_commun", ["rectite", "dysurie", "cerveau"])
def test_casse_contient_les_noms_communs(lex, nom_commun: str) -> None:  # type: ignore[no-untyped-def]
    assert lex.est_minuscule_attestee(nom_commun)


# ----------------------------------------------------------------------
# Périmètre 3 — juxtaposition : CepiDc EXCLU, ponctuation en frontière
# ----------------------------------------------------------------------


def test_dominance_substantive_de_cerveau(lex) -> None:  # type: ignore[no-untyped-def]
    """`cerveau` doit être nettement substantif.

    C'est le témoin du périmètre : CepiDc étant télégraphique, l'inclure
    ferait remonter J et « hypoplasie du cerveau » deviendrait
    « hypoplasie cerveau ».
    """
    a = lex.attestations_avec_joint("cerveau")
    j = lex.attestations_juxtaposees("cerveau")
    assert a >= 2 * max(j, 1), (
        f"cerveau A={a} J={j} : dominance substantive perdue. CepiDc a-t-il "
        f"été admis dans le comptage de juxtaposition ?"
    )


def test_dominance_adjectivale_de_medullaire(lex) -> None:  # type: ignore[no-untyped-def]
    a = lex.attestations_avec_joint("médullaire")
    j = lex.attestations_juxtaposees("médullaire")
    assert j >= 2 * max(a, 1), f"médullaire A={a} J={j} : dominance adjectivale perdue"


def test_frontieres_dures_sur_ponctuation() -> None:
    """Virgules et parenthèses coupent la juxtaposition.

    Sans cela, « Hypoplasie (de), cerveau » compte « cerveau » comme
    juxtaposé et l'Index se contamine lui-même.
    """
    csv = pl.DataFrame(
        {
            "source": ["CIM-10 index", "CIM-10 index"],
            "texte": ["Hypoplasie (de), cerveau", "compression cerveau"],
        }
    )
    out = lexicons.build_lexique_juxtaposition(csv, load_policy())
    compte = dict(out.iter_rows())
    assert compte.get("cerveau") == 1, (
        "Seule « compression cerveau » est une juxtaposition ; l'entrée "
        "d'index en est séparée par une virgule et une parenthèse."
    )


def test_cepidc_exclu_du_comptage() -> None:
    """Une source télégraphique ne doit pas peser sur la juxtaposition."""
    csv = pl.DataFrame(
        {
            "source": ["CepiDc 2015", "ANS"],
            "texte": ["métastases cerveau", "atteinte cerveau"],
        }
    )
    compte = dict(lexicons.build_lexique_juxtaposition(csv, load_policy()).iter_rows())
    assert compte.get("cerveau") == 1, "seule la ligne ANS doit compter"


# ----------------------------------------------------------------------
# Déterminisme
# ----------------------------------------------------------------------


def test_lexiques_deterministes(tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    """Artefacts versionnés : deux constructions donnent les mêmes octets."""
    csv = pl.DataFrame(
        {
            "source": ["ANS", "CIM-10 index", "CepiDc 2015"],
            "texte": ["atteinte du cerveau", "Hypoplasie (de), rate", "métastases foie"],
        }
    )
    policy = load_policy()
    a = lexicons.to_parquet(csv, policy, tmp_path / "a")
    b = lexicons.to_parquet(csv, policy, tmp_path / "b")
    for cle in a:
        assert a[cle].read_bytes() == b[cle].read_bytes(), f"{cle} non déterministe"
