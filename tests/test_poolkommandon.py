"""Krav: K81 i docs/02-KRAV.md, med K17, K48 och K73.
Kod: src/kommunhandlingar/kand_inlasning.py, arenden.py och maska_poolen.py.

Poolens kommandon körs som moduler, med `sys.argv` som på kommandoraden,
mot en pool i en temporär katalog.
"""

import contextlib
import io
import runpy
import sys
import unittest
import warnings
from itertools import product
from unittest import mock

from tests.test_kand_inlasning import dokument
from tests.test_kommandon import Katalogfall


def kor_modulen(modul: str, *argument: str) -> tuple[object, str]:
    """Slutkoden, eller None, och det som skrevs på standard ut."""
    with (
        warnings.catch_warnings(),
        mock.patch.object(sys, "argv", [modul, *argument]),
        contextlib.redirect_stdout(io.StringIO()) as utskrift,
    ):
        # runpy varnar när modulen redan är importerad.
        warnings.simplefilter("ignore", RuntimeWarning)
        try:
            runpy.run_module(f"kommunhandlingar.{modul}", run_name="__main__")
        except SystemExit as stopp:
            return stopp.code, utskrift.getvalue()
    return None, utskrift.getvalue()


class TestPoolkommandona(Katalogfall):
    def test_kand_inlasning_skriver_en_rad_per_kommun_i_ordning(self):
        dokument(self.rot / "ostby" / "ks", "a", "[ok]")
        dokument(self.rot / "exempelby" / "kf", "b", "[ok, ej-konverterad]")
        (self.rot / "README.md").write_text("ingen kommun", encoding="utf-8")
        kod, utskrift = kor_modulen("kand_inlasning", str(self.rot))
        rader = utskrift.splitlines()
        self.assertIsNone(kod)
        self.assertEqual([r.split(":")[0] for r in rader], ["exempelby", "ostby"])
        self.assertTrue(rader[0].startswith("exempelby: 1 av 2 sidor"))

    def test_arenden_och_maska_poolen_raknar_det_som_andrades(self):
        utfall = {
            "arenden": "0 dokument fick nya ärenden.\n",
            "maska_poolen": "0 filer maskades.\n",
        }
        for modul, rad in utfall.items():
            with self.subTest(modul):
                self.assertEqual(kor_modulen(modul, str(self.rot)), (None, rad))

    def test_fel_antal_argument_ger_anvandningstexten(self):
        moduler = ("kand_inlasning", "arenden", "maska_poolen")
        for modul, argument in product(moduler, ((), ("a", "b"))):
            with self.subTest(modul, argument=argument):
                anvandning = f"Användning: python -m kommunhandlingar.{modul} <data>"
                self.assertEqual(kor_modulen(modul, *argument), (anvandning, ""))


if __name__ == "__main__":
    unittest.main()
