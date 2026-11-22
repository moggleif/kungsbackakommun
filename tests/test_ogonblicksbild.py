"""Krav: K77. Kod: src/kommunhandlingar/konvertering/ och
src/kommunhandlingar/skrivning.py.

PDF-fixturerna och facit-utdragen konverteras, och `.md`, med
kvalitetsfälten utom `pipeline` som front matter, och varje CSV jämförs
tecken för tecken med ögonblicksbilden i tests/fixtures/ogonblicksbild/.
En sida som går till OCR läses inte av Tesseract, vars version styr texten
och verktygsversionerna, utan får en fast text. Bilden skrivs om med
`python3 -m tests.test_ogonblicksbild --spara`.
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

from kommunhandlingar import frontmatter, skrivning
from kommunhandlingar.konvertering.dokument import Resultat, konvertera, kvalitetsfalt
from kommunhandlingar.konvertering.sida import Sida

FIXTURER = Path(__file__).parent / "fixtures"
BILD = FIXTURER / "ogonblicksbild"
PDF = ["sidor", "delade", "rutor", "skarvar", "spalter", "hogkant", "kort"]
VERSIONER = "kommunhandlingar.konvertering.dokument.versioner"
OCR_SIDA = Sida("ocr", True, "OCR-sidan ligger utanför ögonblicksbilden.")


def pdfer() -> dict[str, Path]:
    egna = {namn: FIXTURER / "pdf" / f"{namn}.pdf" for namn in PDF}
    utdrag = sorted((FIXTURER / "facit").glob("*/utdrag.pdf"))
    return egna | {pdf.parent.name: pdf for pdf in utdrag}


def konverterad(namn: str, pdf: Path) -> tuple[str, dict[str, str]]:
    ersatt = "kommunhandlingar.konvertering.las_sida.ocr_sida"
    with mock.patch(ersatt, return_value=OCR_SIDA):
        resultat = konvertera(pdf)
    md = BILD / f"{namn}.md"
    text = kvalitet(resultat) + skrivning.kropp(md, resultat.sidor)
    return text, skrivning.tabellfiler(resultat.sidor)


def kvalitet(resultat: Resultat) -> str:
    """Kvalitetsfälten som front matter, utan `pipeline` och dess versioner."""
    with mock.patch(VERSIONER, return_value=[]):
        falt = kvalitetsfalt("", resultat)
    del falt["pipeline"]
    namn = [n for n in frontmatter.FALT if n in falt]
    rader = [f"{n}: {frontmatter.varde_av(falt[n])}" for n in namn]
    return "---\n" + "\n".join(rader) + "\n---\n"


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

    def test_bilden_har_inga_kvarlamnade_dokument(self):
        for monster in ("*.md", "*.tabeller"):
            sparade = {fil.name.split(".")[0] for fil in BILD.glob(monster)}
            self.assertLessEqual(sparade, set(pdfer()), monster)

    def jamfor(self, namn: str, pdf: Path) -> None:
        kropp, tabeller = konverterad(namn, pdf)
        sparad_kropp, sparade = sparad(namn)
        with self.subTest(namn):
            self.assertEqual(kropp, sparad_kropp)
            self.assertEqual(sorted(tabeller), sorted(sparade))
        for fil, innehall in tabeller.items():
            with self.subTest(namn, tabell=fil):
                self.assertEqual(innehall, sparade.get(fil))


def spara() -> None:
    for namn, pdf in pdfer().items():
        kropp, tabeller = konverterad(namn, pdf)
        skrivning.skriv(BILD / f"{namn}.md", kropp, tabeller)


if __name__ == "__main__":
    if sys.argv[1:] == ["--spara"]:
        spara()
    else:
        unittest.main()
