"""Krav: K4, ADR-0014. Kod: src/kommunhandlingar/sidmarkor.py."""

import unittest

from kommunhandlingar import sidmarkor


class TestSidmarkor(unittest.TestCase):
    def test_markoren_som_skrivs_ar_den_som_lases(self):
        traff = sidmarkor.SIDA.fullmatch(sidmarkor.markor(7))
        self.assertEqual(traff[1], "7")

    def test_tre_sidor_ges_efter_sitt_nummer(self):
        text = "\n\n".join(
            ["huvud", sidmarkor.markor(1), "ett", sidmarkor.markor(2)]
            + [sidmarkor.markor(3), "tre"]
        )
        self.assertEqual(
            sidmarkor.sidorna(text),
            {"1": "\n\nett\n\n", "2": "\n\n", "3": "\n\ntre"},
        )

    def test_en_text_utan_markorer_har_inga_sidor(self):
        self.assertEqual(sidmarkor.sidorna("bara text\n"), {})

    def test_en_markor_mitt_i_en_rad_ar_sidans_text(self):
        text = f"{sidmarkor.markor(1)}\nse {sidmarkor.markor(2)} här\n"
        self.assertEqual(sidmarkor.sidorna(text), {"1": "\nse <!-- sida 2 --> här\n"})
        self.assertEqual(sidmarkor.SIDA.findall(text), ["1"])
