"""Krav: K86, ADR-0107. Kod: src/kommunhandlingar/omkonvertering.py och
omkonvertering.toml."""

import tomllib
import unittest
from importlib.metadata import version
from pathlib import Path

from kommunhandlingar import omkonvertering
from kommunhandlingar.konvertering.kvalitet import SIDKVALITETER
from kommunhandlingar.omkonvertering import berors, version_av

PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"
TABELL = {
    (0, 12, 0): frozenset({"alla"}),
    (0, 15, 0): frozenset({"tal_obekraftade"}),
    (0, 16, 0): frozenset({"ocr", "tom"}),
}


def falt(version: str, sidor: str = "[ok, ok]", tal: str = "[]") -> dict[str, str]:
    pipeline = f"kommunhandlingar {version} / pdfplumber 0.11.10"
    return {"pipeline": pipeline, "kvalitet_per_sida": sidor, "tal_obekraftade": tal}


class TestTabellen(unittest.TestCase):
    def test_varje_version_har_en_rad(self):
        with PYPROJECT.open("rb") as fil:
            poolens = tomllib.load(fil)["project"]["version"]
        self.assertIn(version_av(poolens), omkonvertering.las())
        self.assertEqual(poolens, version("kommunhandlingar"))

    def test_raderna_star_i_versionsordning(self):
        versioner = list(omkonvertering.las())
        self.assertEqual(versioner, sorted(versioner))

    def test_varje_varde_ar_kant(self):
        kanda = {"alla", "tal_obekraftade", *SIDKVALITETER}
        for version_, berors_ in omkonvertering.las().items():
            with self.subTest(version_):
                self.assertTrue(berors_)
                self.assertLessEqual(berors_, kanda)


class TestBerors(unittest.TestCase):
    def test_samma_version_berors_inte(self):
        self.assertFalse(
            berors(TABELL, falt("0.16.0", "[ocr]"), "kommunhandlingar 0.16.0")
        )

    def test_en_version_som_ror_alla_beror_ett_aldre_dokument(self):
        self.assertTrue(berors(TABELL, falt("0.11.0"), "kommunhandlingar 0.16.0"))

    def test_bara_versionerna_efter_dokumentets_raknas(self):
        poolens = "kommunhandlingar 0.16.0"
        self.assertFalse(berors(TABELL, falt("0.12.0"), poolens))
        self.assertTrue(berors(TABELL, falt("0.12.0", "[ok, tom]"), poolens))
        self.assertTrue(berors(TABELL, falt("0.12.0", tal="[2]"), poolens))
        self.assertFalse(berors(TABELL, falt("0.15.0", tal="[2]"), poolens))

    def test_versioner_efter_poolens_raknas_inte(self):
        dokument = falt("0.12.0", "[ocr]")
        self.assertFalse(berors(TABELL, dokument, "kommunhandlingar 0.15.0"))

    def test_ett_dokument_fran_en_nyare_version_lamnas_orort(self):
        self.assertFalse(berors(TABELL, falt("0.17.0"), "kommunhandlingar 0.16.0"))

    def test_versionerna_jamfors_som_tal(self):
        self.assertTrue(berors(TABELL, falt("0.9.0"), "kommunhandlingar 0.12.0"))

    def test_en_sida_som_inte_ar_last_berors_alltid(self):
        dokument = falt("0.15.0", "[ok, ej-konverterad]")
        self.assertTrue(berors(TABELL, dokument, "kommunhandlingar 0.16.0"))

    def test_ett_dokument_utan_sidor_berors_alltid(self):
        dokument = falt("0.15.0", "null", "null")
        self.assertTrue(berors(TABELL, dokument, "kommunhandlingar 0.16.0"))
