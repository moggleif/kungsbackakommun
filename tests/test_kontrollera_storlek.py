"""Krav: "Ren kod – strikt" i AGENTS.md. Kod: scripts/kontrollera_storlek.py."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.kontrollera_storlek import (
    KOD,
    ROT,
    TESTER,
    brott_i_fil,
    main,
    pythonfiler,
)


def funktion(rader: int, huvud: str = "def f():") -> str:
    kropp = "".join("    x = 1\n" for _ in range(rader - 1))
    return f"{huvud}\n{kropp}"


def kontrollera(kallkod: str, granser=KOD) -> list[str]:
    with tempfile.TemporaryDirectory() as katalog:
        fil = Path(katalog) / "modul.py"
        fil.write_text(kallkod, encoding="utf-8")
        return brott_i_fil(fil, granser)


def kor(filer: dict[str, str]) -> tuple[int, list[str]]:
    with tempfile.TemporaryDirectory() as katalog:
        sokvagar = [Path(katalog) / namn for namn in filer]
        for sokvag, kallkod in zip(sokvagar, filer.values(), strict=True):
            sokvag.write_text(kallkod, encoding="utf-8")
        with (
            mock.patch(
                "scripts.kontrollera_storlek.pythonfiler",
                lambda: [(s, KOD) for s in sokvagar],
            ),
            contextlib.redirect_stdout(io.StringIO()) as utdata,
        ):
            slutkod = main()
    return slutkod, [rad.split(": ", 1)[-1] for rad in utdata.getvalue().splitlines()]


class TestKontrolleraStorlek(unittest.TestCase):
    def kontrollera(self, kallkod: str) -> list[str]:
        return kontrollera(kallkod)

    def test_funktion_vid_gransen_godkanns(self):
        self.assertEqual(self.kontrollera(funktion(KOD.funktion)), [])

    def test_funktion_over_gransen_underkanns(self):
        self.assertEqual(len(self.kontrollera(funktion(KOD.funktion + 1))), 1)

    def test_async_funktion_over_gransen_underkanns(self):
        kallkod = funktion(KOD.funktion + 1, "async def f():")
        self.assertEqual(len(self.kontrollera(kallkod)), 1)

    def test_undantag_med_skal_godkanns(self):
        kallkod = funktion(KOD.funktion + 1, "def f():  # undantag: tabell")
        self.assertEqual(self.kontrollera(kallkod), [])

    def test_undantag_utan_skal_underkanns(self):
        kallkod = funktion(KOD.funktion + 1, "def f():  # undantag:")
        self.assertEqual(len(self.kontrollera(kallkod)), 1)

    def test_fil_vid_gransen_godkanns(self):
        self.assertEqual(self.kontrollera("x = 1\n" * KOD.fil), [])

    def test_fil_over_gransen_underkanns(self):
        kallkod = "x = 1\n" * (KOD.fil + 1)
        self.assertEqual(len(self.kontrollera(kallkod)), 1)

    def test_fil_over_gransen_har_inget_undantag(self):
        kallkod = "# undantag: genererad\n" + "x = 1\n" * KOD.fil
        self.assertEqual(len(self.kontrollera(kallkod)), 1)

    def test_sidbrytning_i_strang_gor_inte_fel(self):
        self.assertEqual(self.kontrollera('s = "a\x0cb"\n'), [])

    def test_korning_med_brott_har_slutkoden_ett(self):
        filer = {"a.py": funktion(KOD.funktion + 1), "b.py": "x = 1\n"}
        self.assertEqual(kor(filer), (1, ["f har 16 rader"]))

    def test_korning_utan_brott_har_slutkoden_noll(self):
        filer = {"a.py": funktion(KOD.funktion)}
        self.assertEqual(kor(filer), (0, ["Inga brott mot storleksgränserna."]))


class TestGranserPerKatalog(unittest.TestCase):
    """K87."""

    def test_funktion_over_malet_faller_i_koden_men_inte_i_testerna(self):
        kallkod = funktion(KOD.funktion + 1)
        self.assertEqual(len(kontrollera(kallkod, KOD)), 1)
        self.assertEqual(kontrollera(kallkod, TESTER), [])

    def test_varje_katalog_med_sina_granser(self):
        filer = dict(pythonfiler())
        self.assertIs(filer[ROT / "src" / "kommunhandlingar" / "monster.py"], KOD)
        self.assertIs(filer[ROT / "scripts" / "kontrollera_storlek.py"], KOD)
        self.assertIs(filer[ROT / "tests" / "test_kontrollera_storlek.py"], TESTER)


if __name__ == "__main__":
    unittest.main()
