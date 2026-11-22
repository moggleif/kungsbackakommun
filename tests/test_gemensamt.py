"""Adaptrarnas gemensamma delar. Kod: src/kommunhandlingar/adaptrar/gemensamt.py."""

import unittest

from kommunhandlingar.adaptrar.gemensamt import adresser, lankar, organsidor
from kommunhandlingar.fel import Konfigurationsfel

SIDA = "https://exempelby.se/politik/namnd"
HTML = (
    '<a href="mote-1">Möte <b>ett</b>\n i  mars</a>'
    '<a name="topp">utan adress</a>'
    '<a href="/fil.pdf#sida-2">fil.pdf</a>'
    '<a href="">tom</a>'
    '<a href="https://annan.se/x">x'
)


class Lankarna(unittest.TestCase):
    def test_adress_och_text_med_ankaret_kvar(self):
        self.assertEqual(
            lankar(HTML, SIDA),
            [
                ("https://exempelby.se/politik/mote-1", "Möte ett i mars"),
                ("https://exempelby.se/fil.pdf#sida-2", "fil.pdf"),
                (SIDA, "tom"),
            ],
        )

    def test_adresserna_utan_ankare_aven_ostangda(self):
        self.assertEqual(
            adresser(HTML, SIDA),
            [
                "https://exempelby.se/politik/mote-1",
                "https://exempelby.se/fil.pdf",
                "https://annan.se/x",
            ],
        )

    def test_en_ny_lank_stanger_inte_den_forra(self):
        html = '<a href="a">a<a href="b">b</a>'
        self.assertEqual(lankar(html, SIDA), [("https://exempelby.se/politik/b", "b")])
        self.assertEqual(
            adresser(html, SIDA),
            ["https://exempelby.se/politik/a", "https://exempelby.se/politik/b"],
        )


class Sidorna(unittest.TestCase):
    def test_organ_och_adress_godtas(self):
        tabell = {"ks": SIDA}
        self.assertIs(organsidor(tabell, ["ks", "kf"], "k"), tabell)

    def test_okant_organ_eller_adress_som_inte_ar_text(self):
        for tabell in ({"gn": SIDA}, {"ks": 1}):
            with self.subTest(tabell), self.assertRaises(Konfigurationsfel):
                organsidor(tabell, ["ks"], "k")


if __name__ == "__main__":
    unittest.main()
