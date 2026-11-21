"""Krav: K81 i docs/02-KRAV.md, med K15 och K20.
Kod: src/kommunhandlingar/facit/__main__.py och tolkning.py.

Kommandona körs genom sin ingång i en temporär katalog, utan nät. Poolens
kommandon prövas i tests/test_poolkommandon.py.
"""

import argparse
import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from importlib.metadata import version
from pathlib import Path
from unittest import mock

from kommunhandlingar import frontmatter, tolkning
from kommunhandlingar.facit import __main__ as facit_kommando
from kommunhandlingar.facit.jamfor import MATT
from kommunhandlingar.facit.matt import URVALET, sparade
from kommunhandlingar.fel import Hamtfel
from tests.test_granssnitt import tolkat

REPO = Path(__file__).parent.parent
DOKUMENTET = "skuggbudget-2027"


def utskrift_av(kommando, *argument) -> str:
    with contextlib.redirect_stdout(io.StringIO()) as utskrift:
        kommando(*argument)
    return utskrift.getvalue()


class Katalogfall(unittest.TestCase):
    def setUp(self):
        katalog = tempfile.TemporaryDirectory()
        self.addCleanup(katalog.cleanup)
        self.rot = Path(katalog.name)


class TestFacit(Katalogfall):
    def setUp(self):
        super().setUp()
        shutil.copytree(URVALET / DOKUMENTET, self.rot / DOKUMENTET)
        self.matt = self.rot / "matt.csv"
        self.matt.write_text(
            "version," + ",".join(MATT) + "\n0.0.1" + ",9" * len(MATT) + "\n",
            encoding="utf-8",
        )

    def kor(self, *flaggor: str) -> list[str]:
        with (
            mock.patch.object(facit_kommando, "URVALET", self.rot),
            mock.patch.object(sys, "argv", ["facit", *flaggor]),
        ):
            return utskrift_av(facit_kommando.main).splitlines()

    def test_matten_skrivs_per_dokument_och_totalt(self):
        rader = self.kor()
        self.assertTrue(rader[0].startswith(DOKUMENTET))
        self.assertTrue(rader[-1].startswith("totalt"))
        self.assertEqual(rader[0].split()[1:], rader[-1].split()[1:])
        self.assertEqual(list(sparade(self.matt)), ["0.0.1"])

    def test_spara_lagger_till_raden_och_behaller_de_aldre(self):
        totalt = self.kor("--spara")[-1].split()[1:]
        rader = sparade(self.matt)
        self.assertEqual(list(rader), ["0.0.1", version("kommunhandlingar")])
        ny = rader[version("kommunhandlingar")]
        self.assertEqual([f"{m}={ny[m]}" for m in MATT], totalt)
        self.assertEqual(rader["0.0.1"]["ratt"], "9")


class TestTolkning(Katalogfall):
    def setUp(self):
        super().setUp()
        self.md = self.rot / "data/exempelby/ks/2025/2025-04-22/protokoll.md"
        self.md.parent.mkdir(parents=True)
        falt = dict.fromkeys(frontmatter.FALT, "null") | {"kalla_url": "u1"}
        falt |= {"figurer": "[2, 17]", "tolkade": "[2]"}
        self.md.write_text(frontmatter.skriv(falt), encoding="utf-8")

    def test_sidlistan(self):
        self.assertEqual(tolkning.sidlista("3,5"), [3, 5])
        with self.assertRaisesRegex(argparse.ArgumentTypeError, "räknas från 1"):
            tolkning.sidlista("0")

    def test_lista_skriver_arbetslistan(self):
        arg = tolkat(tolkning, "lista", str(self.rot / "data"))
        rad = "exempelby/ks/2025/2025-04-22/protokoll.md: [17]\n"
        self.assertEqual(utskrift_av(tolkning.main, arg), rad)

    def test_rendera_med_valda_sidor_skriver_bilderna(self):
        arg = tolkat(tolkning, "rendera", str(self.md), "ut", "--sidor", "1,3")
        png = [Path("ut/1.png"), Path("ut/3.png")]
        with (
            mock.patch.object(tolkning, "klient_for") as klient_for,
            mock.patch.object(tolkning, "rendera", return_value=png) as rendera,
        ):
            utskrift = utskrift_av(tolkning.main, arg)
        anrop = (self.md, Path("ut"), klient_for.return_value, [1, 3])
        rendera.assert_called_once_with(*anrop)
        self.assertEqual(utskrift.splitlines(), [str(p) for p in png])

    def test_andrat_original_och_hamtfel_stoppar(self):
        arg = tolkat(tolkning, "rendera", str(self.md), str(self.rot / "ut"))
        for fel in (tolkning.AndratOriginal("ändrat"), Hamtfel("http-404", "u1")):
            with (
                self.subTest(fel=type(fel).__name__),
                mock.patch.object(tolkning, "klient_for"),
                mock.patch.object(tolkning, "rendera", side_effect=fel),
                self.assertRaises(SystemExit) as stopp,
            ):
                tolkning.main(arg)
            self.assertEqual(stopp.exception.code, f"Stoppad: {fel}")

    def test_klienten_far_repots_installningar(self):
        shutil.copy(REPO / "hamtning.toml", self.rot)
        klient = tolkning.klient_for(self.md)
        self.assertIsInstance(klient, tolkning.Klient)


if __name__ == "__main__":
    unittest.main()
