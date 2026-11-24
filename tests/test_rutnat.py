"""Krav: K5, K89, ADR-0031 och ADR-0111. Kod:
src/kommunhandlingar/konvertering/rutnat.py och textlagret.py.

Om ett rutnät av linjer går ihop till en tabell, och att en sida med ett
rutnät som inte gör det märks `tabell-osaker`
(docs/03-ARKITEKTUR.md#konvertering-och-kvalitet). Sidorna i rutnat.pdf
beskrivs i tests/fixtures/pdf/skapa_rutnat.py.
"""

import unittest
from pathlib import Path
from types import SimpleNamespace

from kommunhandlingar.konvertering import kvalitet
from kommunhandlingar.konvertering.dokument import konvertera
from kommunhandlingar.konvertering.rutnat import ar_hel, gar_inte_ihop

PDF = Path(__file__).parent / "fixtures" / "pdf" / "rutnat.pdf"
RUTNAT = SimpleNamespace(
    bbox=(0, 0, 200, 20),
    cells=[(0, 0, 100, 10), (100, 0, 200, 10), (0, 10, 100, 20)],
    rows=[SimpleNamespace(cells=[0, 1]), SimpleNamespace(cells=[2, None])],
)
EN_KOLUMN = SimpleNamespace(
    bbox=(0, 0, 100, 20),
    cells=[(0, 0, 100, 10), (0, 10, 100, 20)],
    rows=[SimpleNamespace(cells=[0]), SimpleNamespace(cells=[1])],
)


def ord_(x: float, y: float) -> dict:
    return {"x0": x - 5, "x1": x + 5, "top": y - 2, "bottom": y + 2}


class TestArHel(unittest.TestCase):
    def test_rutnat_utan_text_ar_ingen_tabell(self):
        self.assertFalse(ar_hel(RUTNAT, []))

    def test_rutnat_med_text_ar_en_tabell(self):
        self.assertTrue(ar_hel(RUTNAT, [ord_(50, 5)]))

    def test_ett_ord_utanfor_cellerna_ar_ingen_tabell(self):
        self.assertFalse(ar_hel(RUTNAT, [ord_(50, 5), ord_(150, 15)]))


class TestGarInteIhop(unittest.TestCase):
    def test_ett_ord_utanfor_cellerna_gar_inte_ihop(self):
        self.assertTrue(gar_inte_ihop(RUTNAT, [ord_(50, 5), ord_(150, 15)]))

    def test_ord_i_cellerna_gar_ihop(self):
        self.assertFalse(gar_inte_ihop(RUTNAT, [ord_(50, 5), ord_(50, 15)]))

    def test_rutnat_utan_text_gar_ihop(self):
        self.assertFalse(gar_inte_ihop(RUTNAT, []))

    def test_ord_utanfor_ytan_raknas_inte(self):
        self.assertFalse(gar_inte_ihop(RUTNAT, [ord_(300, 15)]))

    def test_en_kolumn_ar_inget_rutnat(self):
        self.assertFalse(gar_inte_ihop(EN_KOLUMN, [ord_(150, 15)]))


class TestRutnatPdf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sidor = konvertera(PDF).sidor

    def test_ett_rutnat_som_inte_gar_ihop_marker_sidan_osaker(self):
        self.assertEqual(self.sidor[0].kvalitet, kvalitet.TABELL_OSAKER)

    def test_texten_ur_rutnatet_star_kvar_som_loptext(self):
        self.assertEqual(self.sidor[0].tabeller, [])
        self.assertIn("Till plan", self.sidor[0].text)

    def test_samma_rutnat_som_gar_ihop_blir_en_tabell_och_ok(self):
        self.assertEqual(self.sidor[1].kvalitet, kvalitet.OK)
        self.assertEqual(self.sidor[1].tabeller[0][1][3], "Nej")


if __name__ == "__main__":
    unittest.main()
