"""Krav: K81 i docs/02-KRAV.md, med K20. Kod: src/kommunhandlingar/facit/.

`python -m kommunhandlingar.facit` körs mot ett urval med ett dokument i en
temporär katalog.
"""

import shutil
import sys
import unittest
from importlib.metadata import version
from unittest import mock

from kommunhandlingar.facit import __main__ as facit_kommando
from kommunhandlingar.facit.jamfor import MATT
from kommunhandlingar.facit.matt import URVALET, sparade
from tests.kommandofall import Katalogfall, utskrift_av

DOKUMENTET = "skuggbudget-2027"


class TestFacitKommandot(Katalogfall):
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


if __name__ == "__main__":
    unittest.main()
