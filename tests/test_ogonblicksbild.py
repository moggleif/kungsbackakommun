"""Krav: K77. Kod: src/kommunhandlingar/konvertering/ och skrivning.py.

PDF-fixturerna och facit-utdragen konverteras, och `.md` och varje CSV
jämförs tecken för tecken med ögonblicksbilden i
tests/fixtures/ogonblicksbild/. En sida som går till OCR läses inte av
Tesseract, vars version styr texten, utan får en fast text. Bilden skrivs
om med `python3 -m tests.test_ogonblicksbild --skriv-om`.
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

from kommunhandlingar import skrivning
from kommunhandlingar.konvertering.dokument import konvertera
from kommunhandlingar.konvertering.las_sida import Sida

FIXTURER = Path(__file__).parent / "fixtures"
BILD = FIXTURER / "ogonblicksbild"
PDF = ["sidor", "delade", "rutor", "skarvar", "spalter", "hogkant", "kort"]
OCR_SIDA = Sida("ocr", True, "OCR-sidan ligger utanför ögonblicksbilden.")


def pdfer() -> dict[str, Path]:
    egna = {namn: FIXTURER / "pdf" / f"{namn}.pdf" for namn in PDF}
    utdrag = sorted((FIXTURER / "facit").glob("*/utdrag.pdf"))
    return egna | {pdf.parent.name: pdf for pdf in utdrag}


def konverterad(namn: str, pdf: Path) -> tuple[str, dict[str, str]]:
    ersatt = "kommunhandlingar.konvertering.las_sida.ocr_sida"
    with mock.patch(ersatt, return_value=OCR_SIDA):
        sidor = konvertera(pdf).sidor
    md = BILD / f"{namn}.md"
    return skrivning.kropp(md, sidor), skrivning.tabellfiler(sidor or [])


def sparad(namn: str) -> tuple[str, dict[str, str]]:
    md = BILD / f"{namn}.md"
    csv = skrivning.tabellkatalog(md).glob("*.csv")
    return text(md), {fil.name: text(fil) for fil in csv}


def text(fil: Path) -> str:
    """Filen som den står, utan att `\\r` blir radbrytning."""
    return fil.read_bytes().decode("utf-8")


class Ogonblicksbild(unittest.TestCase):
    maxDiff = None

    def test_utdatan_ar_som_i_bilden(self):
        for namn, pdf in pdfer().items():
            self.jamfor(namn, pdf)

    def test_ocr_sidorna_ar_med_som_sidor(self):
        kropp, _ = sparad("sidor")
        self.assertIn(OCR_SIDA.text, kropp)

    def jamfor(self, namn: str, pdf: Path) -> None:
        kropp, tabeller = konverterad(namn, pdf)
        sparad_kropp, sparade = sparad(namn)
        with self.subTest(namn):
            self.assertEqual(kropp, sparad_kropp)
            self.assertEqual(sorted(tabeller), sorted(sparade))
        for fil, innehall in tabeller.items():
            with self.subTest(namn, tabell=fil):
                self.assertEqual(innehall, sparade.get(fil))


def skriv_om() -> None:
    for namn, pdf in pdfer().items():
        kropp, tabeller = konverterad(namn, pdf)
        skrivning.skriv(BILD / f"{namn}.md", kropp, tabeller)


if __name__ == "__main__":
    if sys.argv[1:] == ["--skriv-om"]:
        skriv_om()
    else:
        unittest.main()
