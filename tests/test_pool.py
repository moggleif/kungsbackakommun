"""Krav: K8, K9 och K12, ADR-0004. Kod: src/kommunhandlingar/pool.py."""

import tempfile
import unittest
from pathlib import Path

from kommunhandlingar import pool
from tests.poolfall import skriv


def huvud(namn: str) -> str:
    return f"---\nnamn: {namn}\n---\ntext om {namn}\n"


class TestDokumenten(unittest.TestCase):
    def setUp(self):
        tillfallig = tempfile.TemporaryDirectory()
        self.addCleanup(tillfallig.cleanup)
        self.data = Path(tillfallig.name)

    def test_dokumenten_ges_i_sokvagarnas_ordning(self):
        skriv(
            self.data,
            {"b/1.md": huvud("b"), "a/2.md": huvud("a2"), "a/1.md": huvud("a1")},
        )
        ordning = [
            fil.relative_to(self.data).as_posix()
            for fil, _, _ in pool.dokumenten(self.data)
        ]
        self.assertEqual(ordning, ["a/1.md", "a/2.md", "b/1.md"])

    def test_falten_och_texten_folger_med(self):
        skriv(self.data, {"kf/protokoll.md": huvud("protokoll")})
        [(_, falt, text)] = pool.dokumenten(self.data)
        self.assertEqual(falt, {"namn": "protokoll"})
        self.assertEqual(text, huvud("protokoll"))

    def test_tabellkatalogen_ar_inget_dokument(self):
        skriv(
            self.data,
            {
                "kf/protokoll.md": huvud("protokoll"),
                "kf/protokoll.tabeller/s1-t1.csv": "a,b\n",
            },
        )
        sokvagar = [fil.name for fil, _, _ in pool.dokumenten(self.data)]
        self.assertEqual(sokvagar, ["protokoll.md"])

    def test_en_tom_katalog_ger_inget(self):
        self.assertEqual(list(pool.dokumenten(self.data)), [])
