"""Krav: K84, ADR-0105. Kod: src/kommunhandlingar/konvertering/vag_h.py."""

import unittest

from kommunhandlingar.konvertering.vag_h import Avgorande, avgor, tal


def inte_anropad() -> str:
    raise AssertionError("den tredje läsningen ska inte göras")


class Tal(unittest.TestCase):
    def test_talen_i_ordning(self):
        self.assertEqual(
            tal("Dnr KS 2023-00686, 12,5 % och 1 845 tkr den 11/8"),
            ["2023-00686", "12,5%", "1", "845", "11/8"],
        )

    def test_minustecken_och_tankstreck_blir_bindestreck(self):
        self.assertEqual(tal("−1,8 och 2010–2032"), ["-1,8", "2010-2032"])


class Avgor(unittest.TestCase):
    def test_eniga_utan_tredje_lasning(self):
        svar = avgor("Budget 4 078 tkr", "Budget 4 078 tkr.", inte_anropad)
        self.assertEqual(svar, Avgorande(["4", "078"], "eniga"))

    def test_tredje_lasningen_med_rapidocr(self):
        svar = avgor("12,5 procent", "12.5 procent", lambda: "12,5 procent")
        self.assertEqual(svar, Avgorande(["12,5"], "tredje-och-rapid"))

    def test_tredje_lasningen_med_tesseract(self):
        svar = avgor("1845 tkr", "1 845 tkr", lambda: "1 845 tkr")
        self.assertEqual(svar, Avgorande(["1", "845"], "tredje-och-tesseract"))

    def test_tre_olika_lasningar(self):
        svar = avgor("1845", "1 845", lambda: "1846")
        self.assertEqual(svar, Avgorande(None, "oense"))

    def test_en_tredje_lasning_utan_tal_bekraftar_inget(self):
        svar = avgor("", "8", lambda: "")
        self.assertEqual(svar, Avgorande(None, "oense"))


if __name__ == "__main__":
    unittest.main()
