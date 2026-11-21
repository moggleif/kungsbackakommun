"""Krav: "Ren kod – strikt" i AGENTS.md. Kod: scripts/kontrollera_storlek.py."""

import contextlib
import io
import re
import tempfile
import unittest
from pathlib import Path

from scripts.kontrollera_storlek import (
    MAL,
    MAX_RADER_FIL,
    MAX_RADER_FUNKTION,
    ROT,
    brott_i_fil,
    main,
    pythonfiler,
)


def funktion(rader: int, huvud: str = "def f():") -> str:
    kropp = "".join("    x = 1\n" for _ in range(rader - 1))
    return f"{huvud}\n{kropp}"


def kontrollera(kallkod: str, *granser) -> list[tuple[int, str]]:
    with tempfile.TemporaryDirectory() as katalog:
        fil = Path(katalog) / "modul.py"
        fil.write_text(kallkod, encoding="utf-8")
        return brott_i_fil(fil, *granser)


def kor(argv: list[str]) -> tuple[int, list[str]]:
    with contextlib.redirect_stdout(io.StringIO()) as utdata:
        slutkod = main(argv)
    return slutkod, utdata.getvalue().splitlines()


class TestKontrolleraStorlek(unittest.TestCase):
    def kontrollera(self, kallkod: str) -> list[tuple[int, str]]:
        return kontrollera(kallkod)

    def test_funktion_vid_gransen_godkanns(self):
        self.assertEqual(self.kontrollera(funktion(MAX_RADER_FUNKTION)), [])

    def test_funktion_over_gransen_underkanns(self):
        self.assertEqual(len(self.kontrollera(funktion(MAX_RADER_FUNKTION + 1))), 1)

    def test_async_funktion_over_gransen_underkanns(self):
        kallkod = funktion(MAX_RADER_FUNKTION + 1, "async def f():")
        self.assertEqual(len(self.kontrollera(kallkod)), 1)

    def test_undantag_med_skal_godkanns(self):
        kallkod = funktion(MAX_RADER_FUNKTION + 1, "def f():  # undantag: tabell")
        self.assertEqual(self.kontrollera(kallkod), [])

    def test_undantag_utan_skal_underkanns(self):
        kallkod = funktion(MAX_RADER_FUNKTION + 1, "def f():  # undantag:")
        self.assertEqual(len(self.kontrollera(kallkod)), 1)

    def test_fil_vid_gransen_godkanns(self):
        self.assertEqual(self.kontrollera("x = 1\n" * MAX_RADER_FIL), [])

    def test_fil_over_gransen_underkanns(self):
        kallkod = "x = 1\n" * (MAX_RADER_FIL + 1)
        self.assertEqual(len(self.kontrollera(kallkod)), 1)

    def test_fil_over_gransen_har_inget_undantag(self):
        kallkod = "# undantag: genererad\n" + "x = 1\n" * MAX_RADER_FIL
        self.assertEqual(len(self.kontrollera(kallkod)), 1)

    def test_sidbrytning_i_strang_gor_inte_fel(self):
        self.assertEqual(self.kontrollera('s = "a\x0cb"\n'), [])

    def test_src_kontrolleras(self):
        self.assertIn(ROT / "src" / "kommunhandlingar" / "monster.py", pythonfiler())

    def test_vanlig_korning_godkanner_repot(self):
        self.assertEqual(kor([]), (0, ["Inga brott mot storleksgränserna."]))


class TestKontrolleraStorlekMal(unittest.TestCase):
    """K76."""

    def test_funktion_vid_malet_listas_inte(self):
        self.assertEqual(kontrollera(funktion(MAL.funktion), MAL), [])

    def test_funktion_over_malet_listas(self):
        fynd = kontrollera(funktion(MAL.funktion + 1), MAL)
        self.assertEqual([antal for antal, _ in fynd], [MAL.funktion + 1])

    def test_fil_vid_malet_listas_inte(self):
        self.assertEqual(kontrollera("x = 1\n" * MAL.fil, MAL), [])

    def test_fil_over_malet_listas(self):
        fynd = kontrollera("x = 1\n" * (MAL.fil + 1), MAL)
        self.assertEqual([antal for antal, _ in fynd], [MAL.fil + 1])

    def test_undantag_med_skal_listas_inte(self):
        kallkod = funktion(MAL.funktion + 1, "def f():  # undantag: tabell")
        self.assertEqual(kontrollera(kallkod, MAL), [])

    def test_listan_har_slutkoden_noll_och_langst_forst(self):
        slutkod, rader = kor(["--mal"])
        antal = [int(re.search(r"har (\d+) rader", rad)[1]) for rad in rader]
        self.assertEqual(slutkod, 0)
        self.assertTrue(antal)
        self.assertEqual(antal, sorted(antal, reverse=True))


if __name__ == "__main__":
    unittest.main()
