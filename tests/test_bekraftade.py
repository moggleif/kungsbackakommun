"""Krav: K85, ADR-0106. Kod: src/kommunhandlingar/konvertering/bekraftade.py.

Placeringen prövas med en påhittad TSV och en utbytt väg H; hela vägen
prövas på en ritad sida och på tests/fixtures/pdf/vag-h.pdf.
"""

import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont

from kommunhandlingar.konvertering import bekraftade, radlasning, tesseract
from kommunhandlingar.konvertering.vag_h import Avgorande
from tests.test_radlasning import sidbild

HUVUD = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num"
HUVUD += "\tleft\ttop\twidth\theight\tconf\ttext"
LINJER = [["Budget", "2O27", "kr"], ["Summa", "4", "078"]]
TXT = "Budget 2O27 kr\n\nSumma 4 078\n"


def tsv(linjer: list[list[str]]) -> str:
    rader = [HUVUD]
    for i, ord_ in enumerate(linjer, 1):
        for j, o in enumerate(ord_, 1):
            rader.append(f"5\t1\t{i}\t1\t1\t{j}\t{100 * j}\t{100 * i}\t80\t30\t90\t{o}")
    return "\n".join(rader)


def utdata(txt: str) -> tesseract.Utdata:
    return tesseract.Utdata(tsv(LINJER), txt)


def rad(
    hur: str, tal: list[str] | None, ord_: list[int], rapid: str = ""
) -> radlasning.Rad:
    alla = radlasning.tesseracts_ord(tsv(LINJER))
    return radlasning.Rad(
        (0, 0, 1, 1), rapid, tuple(alla[i] for i in ord_), Avgorande(tal, hur)
    )


def lasning(*rader: radlasning.Rad, utanfor: int = 0) -> radlasning.Sidlasning:
    return radlasning.Sidlasning(list(rader), [], utanfor)


class Placering(unittest.TestCase):
    def text(self, *rader: radlasning.Rad, utanfor: int = 0) -> str | None:
        with patch.object(
            radlasning, "las", return_value=lasning(*rader, utanfor=utanfor)
        ):
            return bekraftade.text(Image.new("L", (10, 10)), utdata(TXT))

    def test_rapidocrs_text_ersatter_tesseracts_ord(self):
        forsta = rad("tredje-och-rapid", ["2027"], [0, 1], "Budget 2027")
        andra = rad("eniga", ["4", "078"], [3, 4, 5])
        self.assertEqual(self.text(forsta, andra), "Budget 2027 kr\n\nSumma 4 078")

    def test_en_obekraftad_rad_eller_ett_tal_utanfor(self):
        andra = rad("eniga", ["4", "078"], [3, 4, 5])
        self.assertIsNone(self.text(rad("oense", None, [1]), andra))
        self.assertIsNone(self.text(andra, utanfor=1))

    def test_en_rad_som_inte_gar_att_placera(self):
        andra = rad("eniga", ["4", "078"], [3, 4, 5])
        for ord_ in ([], [0, 2], [2, 3]):
            forsta = rad("tredje-och-rapid", ["2027"], ord_, "2027")
            self.assertIsNone(self.text(forsta, andra))

    def test_talen_i_texten_maste_vara_de_bekraftade(self):
        forsta = rad("tredje-och-rapid", ["2027"], [1], "2027")
        self.assertIsNone(self.text(forsta, rad("eniga", ["4"], [3, 4])))

    def test_tesseracts_text_maste_vara_dess_ord(self):
        andra = rad("eniga", ["4", "078"], [3, 4, 5])
        forsta = rad("tredje-och-rapid", ["2027"], [1], "2027")
        with patch.object(radlasning, "las", return_value=lasning(forsta, andra)):
            for txt in ("Budget 2O27 kr", "Budget 2O27\n\nSumma 4 078"):
                bild = Image.new("L", (10, 10))
                self.assertIsNone(bekraftade.text(bild, utdata(txt)))


class HelaVagen(unittest.TestCase):
    def test_en_ritad_sida_med_tal_bekraftas(self):
        bild = Image.new("L", (1240, 1754), 255)
        typsnitt = ImageFont.load_default(size=40)
        for i, text in enumerate(["Budgeten 2027 ar 4 078 tkr.", "Beslut den 11 maj."]):
            ImageDraw.Draw(bild).text((120, 120 + 70 * i), text, fill=0, font=typsnitt)
        self.assertEqual(
            bekraftade.text(bild, tesseract.las_bild(bild)),
            "Budgeten 2027 ar 4 078 tkr.\nBeslut den 11 maj.",
        )

    def test_fotnotssiffran_i_fixturen_bekraftas_inte(self):
        bild = sidbild()
        self.assertIsNone(bekraftade.text(bild, tesseract.las_bild(bild)))


if __name__ == "__main__":
    unittest.main()
