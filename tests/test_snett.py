"""Krav: K6, K41, ADR-0112. Kod: src/kommunhandlingar/konvertering/snett.py,
ordning.py och textlagret.py.

PDF:erna beskrivs i tests/fixtures/pdf/skapa_hogkant_ute.py. Tecknen är
påhittade efter #401: `73` upp och ned blev `37`, och `98765` i 45° blev
siffror inne i stycket.
"""

import math
import unittest
from pathlib import Path
from types import SimpleNamespace

import pdfplumber

from kommunhandlingar.konvertering import snett
from kommunhandlingar.konvertering.ordning import i_oordning
from kommunhandlingar.konvertering.textlagret import textsida

PDF = Path(__file__).parent / "fixtures" / "pdf"


def tecken(text: str, x: float, grader: float = 0, upright: bool = True) -> dict:
    """Ett tecken sex punkter brett, `x` punkter längs en baslinje som
    vridits `grader` moturs."""
    v = math.radians(grader)
    a, b = math.cos(v), math.sin(v)
    return {
        "object_type": "char",
        "text": text,
        "x0": x,
        "x1": x + 6,
        "top": 100,
        "bottom": 106,
        "upright": upright,
        "adv": 6,
        "matrix": (a, b, -b, a, x * a, 500 + x * b),
    }


def las(namn: str) -> SimpleNamespace:
    with pdfplumber.open(PDF / namn) as pdf:
        sida = textsida(pdf.pages[0])
    return SimpleNamespace(text=sida.text, obekraftade=sida.tal_obekraftade)


class TestRiktning(unittest.TestCase):
    def test_rakt(self):
        self.assertTrue(snett.rakt(tecken("A", 0)))
        self.assertTrue(snett.rakt(tecken("A", 0, 0.3)))

    def test_kursiv_ar_rak(self):
        """Kursiv stil lutar tecknet, inte baslinjen."""
        kursiv = dict(tecken("A", 0), matrix=(1, 0, 0.2, 1, 0, 0))
        self.assertTrue(snett.rakt(kursiv))

    def test_en_halv_grad_ar_snett(self):
        self.assertFalse(snett.rakt(tecken("A", 0, 0.5)))

    def test_snett_och_upp_och_ned(self):
        for grader in (1, 45, 180, -30):
            self.assertTrue(snett.snett(tecken("A", 0, grader)), grader)

    def test_hogkant_ar_varken_rakt_eller_snett(self):
        vriden = tecken("A", 0, 90, upright=False)
        self.assertFalse(snett.rakt(vriden))
        self.assertFalse(snett.snett(vriden))


class TestTextlagret(unittest.TestCase):
    def test_lases_i_textlagrets_ordning(self):
        """`73` upp och ned: sjuan står till höger, men först längs baslinjen."""
        tecknen = [tecken("7", 100, 180), tecken("3", 106, 180)]
        self.assertEqual(snett.textlagret(SimpleNamespace(chars=tecknen)), ["73"])

    def test_mellanslag_och_nya_rader(self):
        tecknen = [tecken(t, 6 * i, 45) for i, t in enumerate("AB")]
        tecknen += [tecken("C", 16, 45), tecken("D", 80, 45)]
        sida = SimpleNamespace(chars=tecknen)
        self.assertEqual(snett.textlagret(sida), ["AB C", "D"])

    def test_raka_tecken_tas_inte_med(self):
        sida = SimpleNamespace(chars=[tecken("A", 0), tecken("B", 10, 90, False)])
        self.assertEqual(snett.textlagret(sida), [])


class TestOrdning(unittest.TestCase):
    def test_siffra_snett_ger_text_i_oordning(self):
        sida = SimpleNamespace(chars=[tecken("A", 0), tecken("7", 50, 180)])
        self.assertTrue(i_oordning(sida, []))

    def test_bokstav_snett_i_en_tabell(self):
        sida = SimpleNamespace(chars=[tecken("A", 0), tecken("K", 50, 30)])
        self.assertTrue(i_oordning(sida, [(40, 90, 70, 120)]))

    def test_bokstav_snett_ger_inte_text_i_oordning(self):
        sida = SimpleNamespace(chars=[tecken("A", 0), tecken("K", 50, 30)])
        self.assertFalse(i_oordning(sida, []))


class TestSidan(unittest.TestCase):
    def test_upp_och_ned_ger_obekraftade_tal(self):
        sida = las("upp-och-ned.pdf")
        self.assertIn("Belopp kronor", sida.text)
        self.assertTrue(sida.text.endswith("73"))
        self.assertNotIn("37", sida.text)
        self.assertTrue(sida.obekraftade)

    def test_snett_tal_star_inte_i_stycket(self):
        sida = las("snett.pdf")
        stycket, sist = sida.text.rsplit("\n\n", 1)
        self.assertEqual(sist, "98765")
        rader = [r for r in stycket.split("\n") if r]
        lopande = [f"Ett stycke lopande text utan tal rad {i}." for i in range(6)]
        self.assertEqual(rader, lopande)
        self.assertTrue(sida.obekraftade)

    def test_gatunamn_snett_ger_bekraftade_tal(self):
        sida = las("gatunamn.pdf")
        self.assertTrue(sida.text.endswith("Kungsgatan"))
        self.assertEqual(sida.text.count("84 512"), 6)
        self.assertFalse(sida.obekraftade)
