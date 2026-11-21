"""Krav: K80 i docs/02-KRAV.md, med K2, K16 och ADR-0061.
Kod: src/kommunhandlingar/upptack.py.

Steg 1:s kommando som nattkörningen anropar, i ett temporärt repo utan nät:
klienten byts ut mot en påhittad med fixturernas sidor.
"""

import contextlib
import io
import json
import runpy
import shutil
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest import mock

from kommunhandlingar import upptack
from kommunhandlingar.kandidat import lista
from tests.test_granssnitt import tolkat
from tests.test_sitevision_arkiv import arkivet
from tests.test_upptack import BUN, FSN, Klient

REPO = Path(__file__).parent.parent
EXEMPELBY = Path(__file__).parent / "fixtures" / "exempelby.toml"
LEVANDE = {"https://exempelby.se/bun": BUN, "https://exempelby.se/fsn": FSN}
WAYBACK = '\nwayback = ["bun", "fsn"]\n\n[[kalla.monster]]'


class Kommandofall(unittest.TestCase):
    def setUp(self):
        katalog = tempfile.TemporaryDirectory()
        self.addCleanup(katalog.cleanup)
        self.rot = Path(katalog.name) / "repo"
        (self.rot / "kommuner").mkdir(parents=True)
        self.kommunfil = self.rot / "kommuner" / "exempelby.toml"
        text = EXEMPELBY.read_text("utf-8").replace("\n[[kalla.monster]]", WAYBACK, 1)
        self.assertIn(WAYBACK, text, "exempelby.toml har ändrat form")
        self.kommunfil.write_text(text, "utf-8")
        shutil.copy(REPO / "hamtning.toml", self.rot)
        self.arbete = Path(katalog.name) / "arbete"

    def kor(self, klient, *flaggor: str) -> str:
        arg = tolkat(upptack, str(self.kommunfil), str(self.arbete), *flaggor)
        with (
            mock.patch.object(upptack, "Klient", return_value=klient),
            contextlib.redirect_stdout(io.StringIO()) as utskrift,
        ):
            upptack.main(arg)
        return utskrift.getvalue()

    def nycklar(self, arkiv: bool) -> list[str]:
        poster = json.loads(lista(self.arbete, "exempelby", arkiv).read_text("utf-8"))
        return [post["kallnyckel"][-2:] for post in poster]


class TestListorna(Kommandofall):
    def test_det_levande_skriver_kandidatlistan(self):
        utskrift = self.kor(Klient(LEVANDE))
        self.assertEqual(self.nycklar(arkiv=False), ["b2", "b1", "f1"])
        self.assertFalse(lista(self.arbete, "exempelby", True).exists())
        self.assertTrue(utskrift.startswith("3 kandidater, 1 filer utan kandidat\n"))

    def test_arkivet_skriver_sin_lista_och_noteringarna(self):
        utskrift = self.kor(arkivet(), "--arkiv")
        self.assertEqual(self.nycklar(arkiv=True), ["a2", "a1"])
        self.assertFalse(lista(self.arbete, "exempelby", False).exists())
        notering = "Arkivet: arkivets lista för https://exempelby.se/fsn: anslutning"
        self.assertIn(notering, utskrift.splitlines())


class TestSlutkoderna(Kommandofall):
    def kor_modulen(self, klient, arbete: Path) -> tuple[object, str]:
        argv = ["upptack", str(self.kommunfil), str(arbete)]
        with (
            warnings.catch_warnings(),
            mock.patch.object(sys, "argv", argv),
            mock.patch("kommunhandlingar.hamtning.klient.Klient", return_value=klient),
            contextlib.redirect_stdout(io.StringIO()) as utskrift,
            self.assertRaises(SystemExit) as stopp,
        ):
            # runpy varnar när modulen redan är importerad.
            warnings.simplefilter("ignore", RuntimeWarning)
            runpy.run_module("kommunhandlingar.upptack", run_name="__main__")
        return stopp.exception.code, utskrift.getvalue()

    def test_en_kalla_som_inte_svarar_ger_kod_3(self):
        kod, utskrift = self.kor_modulen(Klient({}), self.arbete)
        self.assertEqual(kod, upptack.KALLAN_STOPPADE)
        self.assertEqual(utskrift, "Stoppad: https://exempelby.se/bun: http-404\n")
        self.assertFalse(self.arbete.exists())

    def test_ett_konfigurationsfel_ger_annan_felkod(self):
        kod, utskrift = self.kor_modulen(Klient({}), self.rot / "arbete")
        self.assertNotEqual(kod, upptack.KALLAN_STOPPADE)
        self.assertRegex(str(kod), r"^Stoppad: arbetskatalogen .* ligger i repot$")
        self.assertEqual(utskrift, "")


if __name__ == "__main__":
    unittest.main()
