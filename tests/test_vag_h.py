"""Krav: K84, ADR-0105. Kod: src/kommunhandlingar/konvertering/vag_h.py."""

import unittest

from kommunhandlingar.konvertering.vag_h import Avgorande, avgor, kan_ha_tal, tal


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
        self.assertEqual(tal("2026‑2030 och 2026 — 2030"), ["2026-2030"] * 2)

    def test_mellanslag_kring_tankstreck_mellan_siffror(self):
        self.assertEqual(
            tal("2026– 2030 och 09:15 — 09:35"), ["2026-2030", "09:15-09:35"]
        )

    def test_bindestreck_med_luft_och_flera_streck_ar_tankstreck(self):
        self.assertEqual(tal("18:55 —- 19:15 och 5 - 3"), ["18:55-19:15", "5-3"])

    def test_mellanslag_kring_minus_och_kolon_star_kvar(self):
        self.assertEqual(
            tal("116 −4, 116 -4 och 09: 35"), ["116", "-4", "116", "-4", "09:35"]
        )


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

    def test_bokstav_intill_en_siffra(self):
        svar = avgor("Kl. 16:05", "K1. 16:05", inte_anropad)
        self.assertEqual(svar, Avgorande(None, "bokstav-vid-siffra"))

    def test_ett_fristaende_o_kan_vara_en_nolla(self):
        svar = avgor("Årskurs o", "Årskurs Oo", inte_anropad)
        self.assertEqual(svar, Avgorande(None, "o-som-nolla"))
        self.assertTrue(kan_ha_tal("Årskurs o."))

    def test_o_som_punkt_och_i_ord_ar_inget_tal(self):
        for text in ("o Budgeten", "t.o.m. idag", "O:\\GBG"):
            self.assertFalse(kan_ha_tal(text), text)

    def test_tre_olika_lasningar(self):
        svar = avgor("1845", "1 845", lambda: "1846")
        self.assertEqual(svar, Avgorande(None, "oense"))

    def test_en_tredje_lasning_utan_tal_bekraftar_inget(self):
        svar = avgor("", "8", lambda: "")
        self.assertEqual(svar, Avgorande(None, "oense"))


if __name__ == "__main__":
    unittest.main()
