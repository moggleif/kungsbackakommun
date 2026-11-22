"""Krav: K84, ADR-0105. Kod: src/kommunhandlingar/kalibrering/.

Mätningen körs på tests/fixtures/pdf/vag-h.pdf, där textlagret är facit.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pdfplumber
import pypdfium2 as pdfium

from kommunhandlingar.kalibrering import facit, matning, urval
from kommunhandlingar.kalibrering.matning import Utfall
from kommunhandlingar.konvertering import radlasning
from tests.kalibreringsfall import TALSIDA, VAG_H, dokument


class Urval(unittest.TestCase):
    def setUp(self):
        self.rot = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.rot)
        self.data = self.rot / "data"
        (self.data / "k").mkdir(parents=True)

    def skriv(self, namn: str, text: str) -> None:
        (self.data / "k" / namn).write_text(text, encoding="utf-8")

    def kandidater(self) -> list[urval.Prov]:
        return list(urval.kandidater(self.data, 1))

    def test_sidor_med_textlager_bekraftade_tal_och_manga_tal(self):
        sidor = [TALSIDA, TALSIDA, "inga tal", TALSIDA, TALSIDA]
        self.skriv("a.md", dokument("[ok, ocr, ok, ok, ok]", "[4]", sidor))
        self.assertEqual(self.kandidater()[0].sidor, [1, 5])

    def test_hogst_tre_sidor_per_dokument_i_samma_ordning(self):
        self.skriv("a.md", dokument("[ok, ok, ok, ok]", "[]", [TALSIDA] * 4))
        self.skriv("b.md", dokument("[ok, ok]", "[]", [TALSIDA] * 2, sha256="b"))
        valda = self.kandidater()
        self.assertEqual(sorted(len(p.sidor) for p in valda), [2, 3])
        self.assertEqual(valda, self.kandidater())

    def test_samma_pdf_en_gang(self):
        self.skriv("a.md", dokument("[ok]", "[]", [TALSIDA]))
        self.skriv("b.md", dokument("[ok]", "[]", [TALSIDA]))
        self.assertEqual(len(self.kandidater()), 1)

    def test_dokument_som_inte_kan_valjas(self):
        sida = [TALSIDA]
        self.skriv("delar.md", dokument("[ok]", "[]", sida, kalla_url="[a, b]"))
        self.skriv("ej.md", dokument("null", "[]", [], kalla_url="null"))
        self.skriv("stor.md", dokument("[ok]", "[]", sida, bytes="30000000"))
        self.skriv("okand.md", dokument("[ok]", "[]", sida, bytes="null"))
        self.skriv("ocr.md", dokument("[ocr]", "[1]", sida))
        self.assertEqual(self.kandidater(), [])


def tecken(text: str, x0: float, storlek: float = 10, botten: float = 110) -> dict:
    return {
        "text": text,
        "x0": x0,
        "x1": x0 + storlek / 2,
        "top": botten - storlek,
        "bottom": botten,
        "size": storlek,
    }


class Facit(unittest.TestCase):
    ORD = [
        {"text": "Budget", "x0": 60, "x1": 90, "top": 100, "bottom": 110},
        {"text": "2027", "x0": 95, "x1": 115, "top": 100, "bottom": 110},
        {"text": "42", "x0": 60, "x1": 70, "top": 200, "bottom": 210},
    ]
    RUTA = tuple(v / facit.SKALA for v in (50, 95, 300, 115))

    def sida(self, bilder=(), tecken_=()) -> facit.Facitsida:
        return facit.Facitsida(self.ORD, list(tecken_), list(bilder))

    def text(self, text: str, x0: float = 60) -> list[dict]:
        """Tecken 5 punkter breda; ett `_` blir 1,5 punkts mellanrum."""
        tecknen, x = [], x0
        for t in text:
            if t == "_":
                x += 1.5
            elif t != " ":
                tecknen.append(tecken(t, x))
            x += 5 if t != "_" else 0
        return tecknen

    def test_radens_tal_och_talen_utanfor(self):
        sida = self.sida(tecken_=self.text("Budget 2027"))
        self.assertEqual(facit.radens_tal(sida, self.RUTA), ["2027"])
        self.assertEqual(facit.tal_utanfor(sida, [self.RUTA]), ["42"])

    def test_synligt_mellanrum_ar_mellanslag(self):
        sida = self.sida(tecken_=self.text("2021-03-22_15:33:39"))
        self.assertEqual(facit.radens_tal(sida, self.RUTA), ["2021-03-22", "15:33:39"])

    def test_en_rad_som_ror_en_bild_saknar_facit(self):
        bild = (250, 90, 350, 220)
        self.assertIsNone(facit.radens_tal(self.sida([bild]), self.RUTA))
        self.assertEqual(facit.tal_utanfor(self.sida([bild]), [self.RUTA]), ["42"])

    def test_upphojt_tecken_i_textlagret(self):
        rad = [tecken("2", 95), tecken("0", 100), tecken("7", 105)]
        mindre = [*rad, tecken("4", 110, 6, 106)]
        hojt = [*rad, tecken("4", 110, 10, 105)]
        self.assertFalse(facit.har_upphojt(self.sida(tecken_=rad), self.RUTA))
        self.assertTrue(facit.har_upphojt(self.sida(tecken_=mindre), self.RUTA))
        self.assertTrue(facit.har_upphojt(self.sida(tecken_=hojt), self.RUTA))
        self.assertFalse(facit.har_upphojt(self.sida(), self.RUTA))

    def test_fotnotssiffran_i_fixturen(self):
        with pdfplumber.open(VAG_H) as plumber:
            sida = facit.las(plumber.pages[0])
        fotnot = tuple(v / facit.SKALA for v in (55, 190, 400, 205))
        forsta = tuple(v / facit.SKALA for v in (55, 70, 400, 90))
        self.assertTrue(facit.har_upphojt(sida, fotnot))
        self.assertFalse(facit.har_upphojt(sida, forsta))


class Matning(unittest.TestCase):
    def test_utfallen(self):
        self.assertEqual(matning.varde(None, ["8"], None), "obekraftad")
        self.assertEqual(matning.varde(["8"], None, None), "utan-facit")
        self.assertEqual(matning.varde(["8"], ["8"], lambda: True), "upphojt")
        self.assertEqual(matning.varde(["8"], ["8"], lambda: False), "ratt")
        self.assertEqual(matning.varde(["8"], ["9"], lambda: False), "fel")

    def test_missad_rad_och_tal_utanfor_raderna(self):
        forsta = tuple(v / facit.SKALA for v in (55, 70, 400, 90))
        lasning = radlasning.Sidlasning([], [forsta], 0)
        with (
            patch.object(radlasning, "las", return_value=lasning),
            pdfplumber.open(VAG_H) as plumber,
        ):
            pdf = pdfium.PdfDocument(VAG_H)
            sida = matning.mat(pdf, plumber, 1)
            pdf.close()
        self.assertEqual(sida.rader[0], Utfall("", "missad", "", "2027 4 078", "", ""))
        self.assertEqual(sida.rader[1].utfall, "utanfor")
        self.assertTrue(sida.bekraftad)


if __name__ == "__main__":
    unittest.main()
