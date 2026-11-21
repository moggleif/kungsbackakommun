"""Krav: K84, ADR-0105. Kod: src/kommunhandlingar/konvertering/radlasning.py
och rapid.py.

Läser tests/fixtures/pdf/vag-h.pdf med RapidOCR och Tesseract.
"""

import unittest
from pathlib import Path
from unittest.mock import patch

import pypdfium2 as pdfium
from PIL import Image

from kommunhandlingar.konvertering import ocr, radlasning, rapid

VAG_H = Path(__file__).parent / "fixtures" / "pdf" / "vag-h.pdf"


def sidbild():
    pdf = pdfium.PdfDocument(VAG_H)
    try:
        return ocr.rendera(pdf[0])
    finally:
        pdf.close()


class Las(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lasning = radlasning.las(sidbild())

    def test_raderna_med_tal_bekraftas(self):
        tal = [r.avgorande.tal for r in self.lasning.rader[:3]]
        self.assertEqual(
            tal, [["2027", "4", "078"], ["12,5", "1", "845"], ["11", "2026", "42"]]
        )

    def test_raden_utan_tal_ar_med_bland_rutorna(self):
        self.assertEqual(len(self.lasning.rutor), 5)
        self.assertEqual(len(self.lasning.rader), 4)

    def test_fotnotssiffran_bekraftas_inte(self):
        self.assertEqual(self.lasning.rader[3].avgorande.hur, "upphojt")
        self.assertEqual(self.lasning.tal_utanfor, 0)

    def test_oense_rad_las_av_den_tredje_modellen(self):
        rapid = "Budgeten for 2027 omfattar 4 078 tkr i intakter."
        tesseract = rapid.replace("2027", "2021")
        ruta = self.lasning.rader[0].ruta
        rad = radlasning.avgor(sidbild(), ruta, (rapid, tesseract), [])
        self.assertEqual(rad.hur, "tredje-och-rapid")

    def test_upphojd_rad_bekraftas_inte(self):
        raden = self.lasning.rader[0].ruta
        siffra = (raden[2], raden[1] - 4, raden[2] + 30, raden[3] - 20)
        rad = radlasning.avgor(sidbild(), siffra, ("4", "4"), [raden, siffra])
        self.assertEqual(rad.hur, "upphojd-rad")


class Tom(unittest.TestCase):
    def test_en_tom_sida_har_inga_rader(self):
        self.assertEqual(rapid.rader(Image.new("L", (600, 800), 255)), [])


class Fallerar(unittest.TestCase):
    def test_tesseract_som_fallerar(self):
        with (
            patch.object(ocr, "las_bild", return_value=None),
            self.assertRaises(radlasning.Fallerade),
        ):
            radlasning.tesseracts_ord(sidbild())


if __name__ == "__main__":
    unittest.main()
