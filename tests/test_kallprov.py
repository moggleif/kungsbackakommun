"""Krav: ADR-0021 och ADR-0056. Kod: src/kommunhandlingar/webbplats/kallprov.py.

Ett värde ur en radfil står på källans sida när det står där sedan
radbrytningar, mellanrum, mjuka bindestreck, tabellcellernas `<br>`,
punkter och Markdown-escapning räknats bort. Målen, spåren och
uppföljningarna prövas genom den; här prövas den direkt."""

import tempfile
import unittest
from pathlib import Path

from kommunhandlingar.webbplats.kallprov import Sidlasare, jamforbar, provbar, star_pa

DOKUMENT = "fsn/2024/2024-05-02/protokoll.md"
TEXT = """<!-- sida 14 -->

Målet fortsätter

<!-- sida 15 -->

på nästa sida
"""


class TestStarPa(unittest.TestCase):
    def test_mjuka_bindestreck(self):
        self.assertTrue(star_pa("Ökad trygghet", provbar("Ökad tryg­ghet")))

    def test_br_i_en_tabellcell(self):
        self.assertTrue(star_pa("Ökad trygghet", provbar("| Ökad tryg-<br>ghet |")))
        self.assertTrue(star_pa("Ökad trygghet", provbar("| Ökad<br>trygghet |")))

    def test_punktlistor(self):
        text = "- Fler elever\n• klarar målen"
        self.assertTrue(star_pa("Fler elever klarar målen", provbar(text)))
        self.assertTrue(star_pa("- Fler elever", provbar("Fler elever")))

    def test_escapad_markdown(self):
        self.assertTrue(star_pa("1. Mål *ett*", provbar(r"1\. Mål \*ett\*")))

    def test_trendkolumnens_pilar_och_tankstreck(self):
        self.assertEqual(provbar("Ökar \u2191 \u2013 mål \u2014 \ue001x"), "Ökarmålx")

    def test_text_i_versaler(self):
        self.assertTrue(star_pa("Ökad trygghet", provbar("ÖKAD TRYGGHET")))
        self.assertFalse(star_pa("Ökad Trygghet", provbar("Ökad trygghet")))

    def test_text_som_inte_star_dar(self):
        self.assertFalse(star_pa("Minskad trygghet", provbar("Ökad trygghet")))

    def test_jamforbar_behaller_mellanrummen(self):
        self.assertEqual(jamforbar("- Ökad\n  trygghet\\*"), "Ökad trygghet*")


class TestSidlasare(unittest.TestCase):
    def setUp(self):
        katalog = tempfile.TemporaryDirectory()
        self.addCleanup(katalog.cleanup)
        self.data = Path(katalog.name)
        fil = self.data / DOKUMENT
        fil.parent.mkdir(parents=True)
        fil.write_text(TEXT, encoding="utf-8")
        self.sidtext = Sidlasare(self.data)

    def test_en_provbar(self):
        self.assertEqual(self.sidtext(f"{DOKUMENT}#sida-14", "fsn"), "Måletfortsätter")

    def test_en_kalla_over_tva_sidor(self):
        sidan = self.sidtext(f"{DOKUMENT}#sida-14-15", "fsn")
        self.assertTrue(star_pa("Målet fortsätter på nästa sida", sidan))

    def test_en_sida_som_inte_finns(self):
        for kalla in (f"{DOKUMENT}#sida-16", f"{DOKUMENT}#sida-15-16"):
            with self.subTest(kalla), self.assertRaises(ValueError) as fel:
                self.sidtext(kalla, "fsn")
            self.assertEqual(
                str(fel.exception), f"källan {kalla!r} är ingen sida i dokumentet"
            )

    def test_sidorna_baklanges(self):
        with self.assertRaisesRegex(ValueError, "ingen sida i dokumentet"):
            self.sidtext(f"{DOKUMENT}#sida-15-14", "fsn")

    def test_ett_annat_organs_dokument(self):
        with self.assertRaisesRegex(ValueError, "ingen sida i organets dokument"):
            self.sidtext(f"{DOKUMENT}#sida-14", "ks")

    def test_ingen_sida_i_kallan(self):
        with self.assertRaisesRegex(ValueError, "ingen sida i organets dokument"):
            self.sidtext(DOKUMENT, "fsn")

    def test_ett_dokument_som_inte_finns(self):
        kalla = "fsn/2024/2024-05-02/handlingar.md#sida-1"
        with self.assertRaisesRegex(ValueError, "inget dokument i poolen"):
            self.sidtext(kalla, "fsn")

    def test_dokumentet_lases_en_gang(self):
        self.sidtext(f"{DOKUMENT}#sida-14", "fsn")
        (self.data / DOKUMENT).write_text("<!-- sida 14 -->\nannat", encoding="utf-8")
        self.assertEqual(self.sidtext(f"{DOKUMENT}#sida-14", "fsn"), "Måletfortsätter")


if __name__ == "__main__":
    unittest.main()
