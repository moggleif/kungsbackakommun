"""Krav: K79 i docs/02-KRAV.md, med K8, K11, K53 och ADR-0088.
Kod: src/kommunhandlingar/hamta.py och provning.py.

Steg 2:s kommando som nattkörningen anropar, i en temporär arbetskatalog
utan nät: klienten och klockan byts ut i `hamta`, och OCR-kontrollen
hoppas över, eftersom fixturen har ett textlager.
"""

import argparse
import contextlib
import csv
import io
import runpy
import shutil
import sys
import tempfile
import unittest
import warnings
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from kommunhandlingar import hamta, konfiguration, provade, provning
from kommunhandlingar.kandidat import lista
from kommunhandlingar.tidsbudget import Tidsgrans
from kommunhandlingar.upptack import skriv
from tests.test_granssnitt import tolkat
from tests.test_hamta import TID, Klient, kandidat

REPO = Path(__file__).parent.parent
EXEMPELBY = Path(__file__).parent / "fixtures" / "exempelby.toml"
TYPER = ("protokoll", "kallelse", "handlingar")
DEL = 15  # minuter
KANDIDATER = [kandidat(f"s:{n}", f"u{n}", typ) for n, typ in enumerate(TYPER, 1)]


class Kommandofall(unittest.TestCase):
    def setUp(self):
        katalog = tempfile.TemporaryDirectory()
        self.addCleanup(katalog.cleanup)
        self.rot = Path(katalog.name)
        (self.rot / "kommuner").mkdir()
        self.kommunfil = self.rot / "kommuner" / "exempelby.toml"
        shutil.copy(EXEMPELBY, self.kommunfil)
        shutil.copy(REPO / "hamtning.toml", self.rot)
        self.arbete = self.rot / "arbete"
        self.arbete.mkdir()
        self.klient = Klient()
        self.klient.filer = {k.url: "kort.pdf" for k in KANDIDATER}

    def argument(self, *flaggor: str) -> argparse.Namespace:
        return tolkat(hamta, str(self.kommunfil), str(self.arbete), *flaggor)

    def kor(self, *flaggor: str, klocka=lambda: TID) -> tuple[int, str]:
        arkiv = "--arkiv" in flaggor
        skriv(KANDIDATER, lista(self.arbete, "exempelby", arkiv))
        utskrift = io.StringIO()
        with (
            mock.patch.object(hamta.tesseract, "kontrollera"),
            mock.patch.object(hamta, "Klient", return_value=self.klient),
            mock.patch.object(hamta, "nu", side_effect=klocka),
            contextlib.redirect_stdout(utskrift),
        ):
            kod = hamta.main(self.argument(*flaggor))
        return kod, utskrift.getvalue()

    def efter_forsta(self) -> datetime:
        """Klockan passerar delens minuter när det första dokumentet hämtats."""
        return TID + timedelta(minutes=DEL + 5 if self.klient.anrop else 0)

    def logg(self) -> Path:
        return self.rot / "versioner" / "exempelby.csv"


class TestKommandot(Kommandofall):
    def test_utfallet_skrivs_ut_och_versionsloggen_far_raderna(self):
        kod, utskrift = self.kor()
        self.assertEqual((kod, utskrift), (0, "3 konverterad\n"))
        with self.logg().open(encoding="utf-8") as fil:
            nycklar = [rad["kallnyckel"] for rad in csv.DictReader(fil)]
        self.assertEqual(nycklar, ["s:1", "s:2", "s:3"])

    def test_arkivet_skriver_ingen_versionslogg(self):
        kod, utskrift = self.kor("--arkiv")
        self.assertEqual((kod, utskrift), (0, "3 konverterad\n"))
        self.assertFalse(self.logg().exists())

    def test_det_som_inte_gick_att_hamta_skrivs_ut_med_adressen(self):
        self.klient.filer["u1"] = "fel:http-404"
        kod, utskrift = self.kor()
        rader = "ej hämtad (http-404): u1\n1 ej hämtad (http-404)\n2 konverterad\n"
        self.assertEqual((kod, utskrift), (0, rader))


class TestDelar(Kommandofall):
    def test_en_del_skriver_de_provade_och_nasta_tar_inte_om_dem(self):
        kod, utskrift = self.kor("--del", str(DEL), klocka=self.efter_forsta)
        self.assertEqual(kod, hamta.MER_I_NASTA_DEL)
        self.assertEqual(utskrift, "1 konverterad\n2 väntar på nästa körning\n")
        provfil = provade.fil(lista(self.arbete, "exempelby", False))
        self.assertEqual(provfil.read_text(encoding="utf-8"), "s:1\n")
        self.klient.anrop.clear()
        self.assertEqual(self.kor("--del", str(DEL))[0], 0)
        self.assertEqual(self.klient.anrop, ["u2", "u3"])
        self.assertEqual(provfil.read_text(encoding="utf-8"), "s:1\ns:2\ns:3\n")

    def test_den_som_lades_at_sidan_raknas_inte_som_provad(self):
        riktig = provning.behandla

        def andra_nar_gransen(steg, k):
            if k.url == "u2":
                raise Tidsgrans
            return riktig(steg, k)

        with mock.patch.object(provning, "behandla", andra_nar_gransen):
            kod, utskrift = self.kor("--del", str(DEL))
        self.assertEqual(kod, hamta.MER_I_NASTA_DEL)
        self.assertIn("lagd åt sidan vid tidsgränsen: u2\n", utskrift)
        provfil = provade.fil(lista(self.arbete, "exempelby", False))
        self.assertEqual(provfil.read_text(encoding="utf-8"), "s:1\n")


class TestOmkonvertering(Kommandofall):
    def omkonvertera(self, i_kommunfilen: bool, *flaggor: str) -> bool:
        kommun = replace(konfiguration.las(self.kommunfil), omkonvertera=i_kommunfilen)
        steg = hamta.bygg_steg(self.argument(*flaggor), kommun, KANDIDATER)
        return steg.omkonvertera

    def test_kommunfilen_och_flaggan_ger_omkonverteringen(self):
        self.assertTrue(self.omkonvertera(True))
        self.assertFalse(self.omkonvertera(True, "--utan-omkonvertering"))
        self.assertFalse(self.omkonvertera(False))
        self.assertFalse(self.omkonvertera(False, "--utan-omkonvertering"))


class TestKonfigurationsfel(Kommandofall):
    def test_stoppas_med_felet_och_en_felkod(self):
        self.kommunfil.write_text('namn = "Exempelby kommun"\nokant = 1\n', "utf-8")
        argv = ["hamta", str(self.kommunfil), str(self.arbete)]
        with (
            warnings.catch_warnings(),
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(hamta.tesseract, "kontrollera"),
            self.assertRaises(SystemExit) as stopp,
        ):
            # runpy varnar när modulen redan är importerad.
            warnings.simplefilter("ignore", RuntimeWarning)
            runpy.run_module("kommunhandlingar.hamta", run_name="__main__")
        self.assertRegex(str(stopp.exception.code), r"^Stoppad: .*okant")


if __name__ == "__main__":
    unittest.main()
