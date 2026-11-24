"""Krav: K92 i docs/02-KRAV.md, ADR-0115. Kod: src/kommunhandlingar/hamtning/."""

import tempfile
from pathlib import Path
from unittest import mock

from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.hamtning import klient, svar
from tests.test_klient import MedServer, Server


class TestHamtgranser(MedServer):
    def test_bara_https_hamtas(self):
        adresser = ("http://exempelby.se/a", "file:///etc/passwd", "ftp://x/a")
        for adress in adresser:
            with (
                mock.patch.object(klient, "SCHEMA", "https"),
                self.assertRaisesRegex(Hamtfel, "^inte-https$"),
            ):
                self.klient.text(adress)
        self.assertEqual(Server.anrop, [])

    def test_sida_over_taket_hamtas_inte(self):
        Server.svar["/a"] = [(200, {}, "x" * 11)]
        with (
            mock.patch.object(svar, "TEXTTAK", 10),
            self.assertRaisesRegex(Hamtfel, "^for-stor$"),
        ):
            self.klient.text(self.bas + "/a")
        self.assertEqual(len(Server.anrop), 2)

    def test_sida_pa_taket_hamtas(self):
        Server.svar["/a"] = [(200, {}, "x" * 10)]
        with mock.patch.object(svar, "TEXTTAK", 10):
            self.assertEqual(self.klient.text(self.bas + "/a"), "x" * 10)

    def test_fil_over_taket_avbryts(self):
        Server.svar["/a.pdf"] = [(200, {}, "%PDF-1.4 " + "x" * 30)]
        with (
            tempfile.TemporaryDirectory() as katalog,
            mock.patch.multiple(svar, FILTAK=20, BLOCK=8),
            self.assertRaisesRegex(Hamtfel, "^for-stor$"),
        ):
            self.klient.fil(self.bas + "/a.pdf", Path(katalog) / "a.pdf")
        self.assertEqual(len(Server.anrop), 2)

    def test_taken(self):
        self.assertEqual(svar.FILTAK, 1 << 30)
        self.assertEqual(svar.TEXTTAK, 50 << 20)
