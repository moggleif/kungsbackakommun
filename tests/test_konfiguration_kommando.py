"""Krav: K110 i docs/02-KRAV.md. Kod: src/kommunhandlingar/konfiguration.py.

`python -m kommunhandlingar.konfiguration` körs mot kommunfiler i en
temporär katalog, med `sys.argv` som på kommandoraden.
"""

import re
import shutil
import unittest

from tests.kommandofall import Katalogfall, kor_modulen
from tests.test_konfiguration import FIXTURER, ROT

ANVANDNING = "Användning: python -m kommunhandlingar.konfiguration <kommunfil> …"


class TestKommandot(Katalogfall):
    def test_en_rad_per_giltig_kommunfil(self):
        exempelby = shutil.copy(FIXTURER / "exempelby.toml", self.rot)
        kungsbacka = str(ROT / "kommuner" / "kungsbacka.toml")
        kod, utskrift = kor_modulen("konfiguration", exempelby, kungsbacka)
        self.assertIsNone(kod)
        rader = utskrift.splitlines()
        self.assertEqual(rader[0], f"{exempelby}: Exempelby kommun, 2 organ")
        self.assertTrue(rader[1].startswith(f"{kungsbacka}: Kungsbacka kommun, "))
        self.assertEqual(len(rader), 2)

    def test_fel_i_kommunfilen_stoppar_med_filen_och_felet(self):
        utan_namn = self.rot / "utan_namn.toml"
        text = (FIXTURER / "exempelby.toml").read_text(encoding="utf-8")
        utan_namn.write_text(text.replace('namn = "Exempelby kommun"', ""), "utf-8")
        trasig = self.rot / "trasig.toml"
        trasig.write_text("namn = ", encoding="utf-8")
        for fil, fel in ((utan_namn, "namn"), (trasig, "Invalid")):
            with self.subTest(fil.name):
                kod, utskrift = kor_modulen("konfiguration", str(fil))
                self.assertRegex(kod, f"^Stoppad: {re.escape(str(fil))}: .*{fel}")
                self.assertEqual(utskrift, "")

    def test_utan_kommunfil_ges_anvandningstexten(self):
        self.assertEqual(kor_modulen("konfiguration"), (ANVANDNING, ""))


if __name__ == "__main__":
    unittest.main()
