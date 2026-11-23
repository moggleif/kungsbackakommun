"""Krav: K81 i docs/02-KRAV.md, med K15 och K34.
Kod: src/kommunhandlingar/tolkning.py.

`python -m kommunhandlingar.tolkning` med ett dokument i en temporär pool;
renderingen själv prövas i tests/test_figurer.py och byts här ut.
"""

import contextlib
import io
import shutil
import unittest
from pathlib import Path
from unittest import mock

from kommunhandlingar import frontmatter, tolkning
from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.hamtning import installningar
from tests.kommandofall import Katalogfall, utskrift_av
from tests.test_granssnitt import tolkat

REPO = Path(__file__).parent.parent


class TestTolkningKommandot(Katalogfall):
    def setUp(self):
        super().setUp()
        self.md = self.rot / "data/exempelby/ks/2025/2025-04-22/protokoll.md"
        self.md.parent.mkdir(parents=True)
        falt = dict.fromkeys(frontmatter.FALT, "null") | {"kalla_url": "u1"}
        falt |= {"figurer": "[2, 17]", "tolkade": "[2]"}
        self.md.write_text(frontmatter.skriv(falt), encoding="utf-8")

    def rendera(self, *flaggor: str):
        return tolkat(tolkning, "rendera", str(self.md), "ut", *flaggor)

    def test_sidlistan_tolkas_och_raknas_fran_1(self):
        self.assertEqual(self.rendera("--sidor", "3,5").sidor, [3, 5])
        with (
            contextlib.redirect_stderr(io.StringIO()) as fel,
            self.assertRaises(SystemExit),
        ):
            self.rendera("--sidor", "0")
        self.assertIn("sidorna räknas från 1", fel.getvalue())

    def test_lista_skriver_arbetslistan(self):
        arg = tolkat(tolkning, "lista", str(self.rot / "data"))
        rad = "exempelby/ks/2025/2025-04-22/protokoll.md: [17]\n"
        self.assertEqual(utskrift_av(tolkning.main, arg), rad)

    def test_rendera_med_valda_sidor_skriver_bilderna(self):
        png = [Path("ut/1.png"), Path("ut/3.png")]
        with (
            mock.patch.object(tolkning, "klient_for") as klient_for,
            mock.patch.object(tolkning, "rendera", return_value=png) as rendera,
        ):
            utskrift = utskrift_av(tolkning.main, self.rendera("--sidor", "1,3"))
        bestallning = tolkning.Bestallning(self.md, Path("ut"), [1, 3])
        rendera.assert_called_once_with(bestallning, klient_for.return_value)
        self.assertEqual(utskrift.splitlines(), [str(p) for p in png])

    def test_andrat_original_och_hamtfel_stoppar(self):
        for fel in (tolkning.AndratOriginal("ändrat"), Hamtfel("http-404", "u1")):
            with (
                self.subTest(fel=type(fel).__name__),
                mock.patch.object(tolkning, "klient_for"),
                mock.patch.object(tolkning, "rendera", side_effect=fel),
                self.assertRaises(SystemExit) as stopp,
            ):
                tolkning.main(self.rendera())
            self.assertEqual(stopp.exception.code, f"Stoppad: {fel}")

    def test_klienten_far_repots_installningar(self):
        shutil.copy(REPO / "hamtning.toml", self.rot)
        klient = tolkning.klient_for(self.md)
        vantat = installningar.las(REPO / installningar.VAR)
        self.assertEqual(klient.installningar, vantat)


if __name__ == "__main__":
    unittest.main()
