"""Génère la fixture OFS mini (9 fichiers, latin-1, séparateur ¦).

Usage :
    uv run python tests/fixtures/ofs_sample/_build.py

À ré-exécuter uniquement si tu modifies les données du fixture.
"""

from __future__ import annotations

from pathlib import Path

SEP = "¦"
HERE = Path(__file__).parent


def _write(name: str, lines: list[str]) -> None:
    path = HERE / name
    text = "\n".join(lines) + "\n"
    path.write_bytes(text.encode("iso-8859-1"))
    print(f"  wrote {name} ({len(lines) - 1} data lines)")


def _row(*fields: object) -> str:
    return SEP.join("" if f is None else str(f) for f in fields)


_DATE = "14.7.2003 00:00:00"
_AUTHOR = "fix"
_COMMENT = ""


def main() -> None:
    # MASTER: 14 codes (13 valides + 1 invalide pour test de filtrage)
    # Schéma: SID¦code¦sort¦abbrev¦level¦type¦id1¦id2¦id3¦id4¦id5¦id6¦id7¦valid¦date¦author¦comment
    master = [
        _row(
            "SID",
            "code",
            "sort",
            "abbrev",
            "level",
            "type",
            "id1",
            "id2",
            "id3",
            "id4",
            "id5",
            "id6",
            "id7",
            "valid",
            "date",
            "author",
            "comment",
        ),
        # Chapter I (Certaines maladies infectieuses)
        _row(
            1,
            "(A00-B99)",
            "A00'",
            "(A00-B99)",
            1,
            "C",
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            _DATE,
            _AUTHOR,
            _COMMENT,
        ),
        # Block A00-A09
        _row(
            2,
            "(A00-A09)",
            "A00-",
            "(A00-A09)",
            2,
            "G",
            1,
            2,
            0,
            0,
            0,
            0,
            0,
            1,
            _DATE,
            _AUTHOR,
            _COMMENT,
        ),
        # A00 (choléra) — inclusion
        _row(3, "A00", "A00,", "A00", 3, "K", 1, 2, 3, 0, 0, 0, 0, 1, _DATE, _AUTHOR, _COMMENT),
        _row(4, "A00.0", "A00.0", "A000", 4, "S", 1, 2, 3, 4, 0, 0, 0, 1, _DATE, _AUTHOR, _COMMENT),
        # A01 — exclusion redirect → A02
        _row(5, "A01", "A01,", "A01", 3, "K", 1, 2, 5, 0, 0, 0, 0, 1, _DATE, _AUTHOR, _COMMENT),
        # A02 (target of A01 redirect)
        _row(6, "A02", "A02,", "A02", 3, "K", 1, 2, 6, 0, 0, 0, 0, 1, _DATE, _AUTHOR, _COMMENT),
        # A03 — synonyme + note éditoriale
        _row(7, "A03", "A03,", "A03", 3, "K", 1, 2, 7, 0, 0, 0, 0, 1, _DATE, _AUTHOR, _COMMENT),
        # A99 — invalide (test filtre valid=0)
        _row(8, "A99", "A99,", "A99", 3, "K", 1, 2, 8, 0, 0, 0, 0, 0, _DATE, _AUTHOR, _COMMENT),
        # Chapter IX (I00-I99)
        _row(
            9,
            "(I00-I99)",
            "I00'",
            "(I00-I99)",
            1,
            "C",
            9,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            _DATE,
            _AUTHOR,
            _COMMENT,
        ),
        # Block I40-I49
        _row(
            10,
            "(I40-I49)",
            "I40-",
            "(I40-I49)",
            2,
            "G",
            9,
            10,
            0,
            0,
            0,
            0,
            0,
            1,
            _DATE,
            _AUTHOR,
            _COMMENT,
        ),
        # I41 — astérisque dans la paire DAGSTAR
        _row(11, "I41", "I41,", "I41", 3, "K", 9, 10, 11, 0, 0, 0, 0, 1, _DATE, _AUTHOR, _COMMENT),
        # Chapter X (J00-J99)
        _row(
            12,
            "(J00-J99)",
            "J00'",
            "(J00-J99)",
            1,
            "C",
            12,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            _DATE,
            _AUTHOR,
            _COMMENT,
        ),
        # Block J10-J18
        _row(
            13,
            "(J10-J18)",
            "J10-",
            "(J10-J18)",
            2,
            "G",
            12,
            13,
            0,
            0,
            0,
            0,
            0,
            1,
            _DATE,
            _AUTHOR,
            _COMMENT,
        ),
        # J11 — dague dans la paire DAGSTAR
        _row(14, "J11", "J11,", "J11", 3, "K", 12, 13, 14, 0, 0, 0, 0, 1, _DATE, _AUTHOR, _COMMENT),
    ]
    _write("MASTER.txt", master)

    # LIBELLE: libellés (1 par code) + textes d'inclusion/exclusion + descripteur
    # Schéma: LID¦SID¦source¦valid¦libelle¦FR_OMS¦EN_OMS¦GE_DIMDI¦GE_AUTO¦FR_CHRONOS¦date¦author¦comment
    libelles_data = [
        # (LID, SID, source, libelle)
        (1, 1, "S", "certaines maladies infectieuses et parasitaires"),
        (2, 2, "S", "maladies intestinales infectieuses"),
        (3, 3, "S", "choléra"),
        (4, 4, "S", "choléra à Vibrio cholerae 01, biotype cholerae"),
        (5, 5, "S", "fièvres typhoïdes et paratyphoïdes"),
        (6, 6, "S", "autres salmonelloses"),
        (7, 7, "S", "shigellose"),
        (8, 9, "S", "maladies de l'appareil circulatoire"),
        (9, 10, "S", "autres formes de cardiopathies"),
        (10, 11, "S", "myocardite au cours de maladies classées ailleurs"),
        (11, 12, "S", "maladies de l'appareil respiratoire"),
        (12, 13, "S", "grippe et pneumopathie"),
        (13, 14, "S", "grippe à virus non identifié"),
        (14, 3, "I", "diarrhée à V. cholerae"),
        (15, 5, "E", "salmonelloses à autres germes"),
        (16, 7, "D", "dysenterie bacillaire"),
    ]
    libelle = [
        _row(
            "LID",
            "SID",
            "source",
            "valid",
            "libelle",
            "FR_OMS",
            "EN_OMS",
            "GE_DIMDI",
            "GE_AUTO",
            "FR_CHRONOS",
            "date",
            "author",
            "comment",
        ),
    ]
    for lid, sid, source, text in libelles_data:
        libelle.append(
            _row(
                lid,
                sid,
                source,
                1,
                text,
                text,
                "",
                "",
                "",
                "",
                _DATE,
                _AUTHOR,
                _COMMENT,
            )
        )
    _write("LIBELLE.txt", libelle)

    # INCLUDE: SID¦LID — A00 inclut "diarrhée à V. cholerae"
    include = [
        _row("SID", "LID"),
        _row(3, 14),
    ]
    _write("INCLUDE.txt", include)

    # EXCLUDE: SID¦excl¦plus¦LID¦daget — A01 exclut "salmonelloses..." → A02
    exclude = [
        _row("SID", "excl", "plus", "LID", "daget"),
        _row(5, 6, 1, 15, ""),
    ]
    _write("EXCLUDE.txt", exclude)

    # DAGSTAR: SID¦LID¦assoc¦daget¦plus — I41 ↔ J11
    dagstar = [
        _row("SID", "LID", "assoc", "daget", "plus"),
        _row(11, 10, 14, "H", 0),
    ]
    _write("DAGSTAR.txt", dagstar)

    # NOTE: SID¦MID — A03 a la note MID=1
    note = [
        _row("SID", "MID"),
        _row(7, 1),
    ]
    _write("NOTE.txt", note)

    # MEMO: les en-têtes ET les valeurs textuelles sont entourées d'apostrophes
    # (convention différente du reste d'OFS — voir le vrai MEMO.txt).
    # Schéma : 'MID'¦'SID'¦'source'¦'valid'¦'memo'¦'FR_OMS'¦'EN_OMS'¦'GE_DIMDI'¦'date'¦'author'¦'comment'
    memo = [
        _row(
            "'MID'",
            "'SID'",
            "'source'",
            "'valid'",
            "'memo'",
            "'FR_OMS'",
            "'EN_OMS'",
            "'GE_DIMDI'",
            "'date'",
            "'author'",
            "'comment'",
        ),
        _row(
            1,
            7,
            "'N'",
            "'Yes'",
            "'Inclut: dysenterie de Sonne et de Flexner.'",
            "''",
            "''",
            "''",
            f"'{_DATE}'",
            f"'{_AUTHOR}'",
            "''",
        ),
    ]
    _write("MEMO.txt", memo)

    # DESCR: SID¦LID — A03 a le descripteur LID=16 (synonyme)
    descr = [
        _row("SID", "LID"),
        _row(7, 16),
    ]
    _write("DESCR.txt", descr)

    # VERSION: une seule ligne valide
    version = [
        _row("name", "version", "build", "valid", "date", "expl"),
        _row(
            "ICD10 OFS test",
            "V0",
            "001",
            1,
            "14.7.2003 00:00:00",
            "fixture de test recode-icd",
        ),
    ]
    _write("VERSION.txt", version)


if __name__ == "__main__":
    main()
