"""Krav: K4 i docs/02-KRAV.md. Kod: src/kommunhandlingar/frontmatter.py."""

import unittest
from datetime import date

from kommunhandlingar import frontmatter

FALT = dict.fromkeys(frontmatter.FALT, "null") | {"organ": "ks", "typ": "protokoll"}
BRODTEXT = "<!-- sida 1 -->\nFöre linjen\n\n---\n\nEfter linjen\n"


class TestLasOchSkriv(unittest.TestCase):
    def setUp(self):
        self.text = frontmatter.skriv(FALT) + BRODTEXT

    def test_falten_i_schemats_ordning_ett_per_rad(self):
        rader = frontmatter.skriv(FALT).splitlines()
        self.assertEqual((rader[0], rader[-1]), ("---", "---"))
        self.assertEqual(rader[1:3], ["kommun: null", "organ: ks"])
        self.assertEqual(len(rader), len(frontmatter.FALT) + 2)

    def test_las_ger_tillbaka_falten(self):
        self.assertEqual(frontmatter.las(self.text), FALT)

    def test_brodtext_med_egen_linje(self):
        self.assertEqual(frontmatter.brodtext(self.text), BRODTEXT)


class TestOtolkad(unittest.TestCase):
    def test_huvudet_som_det_star_ocksa_nar_det_inte_gar_att_lasa(self):
        huvud = "---\ntitel:\ntyp: protokoll\n---\n"
        self.assertEqual(frontmatter.otolkad(huvud + BRODTEXT), (huvud, BRODTEXT))

    def test_utan_front_matter_ar_huvudet_tomt(self):
        for text in ("Bara text\n", "---\ntyp: protokoll\nIngen avslutning\n"):
            with self.subTest(text):
                self.assertEqual(frontmatter.otolkad(text), ("", text))

    def test_efter_huvudet_utan_front_matter_ar_resten(self):
        text = "<!-- sida 1 -->\nA\n---\n<!-- sida 2 -->\nB\n---\nC\n"
        self.assertEqual(frontmatter.efter_huvudet(text), "C\n")
        self.assertEqual(frontmatter.efter_huvudet("Bara text\n"), "Bara text\n")

    def test_las_stoppar_utan_front_matter(self):
        self.assertRaises(IndexError, frontmatter.las, "Bara text\n")


class TestAndrad(unittest.TestCase):
    def test_bara_faltets_rad_byts(self):
        text = "\ufeff" + frontmatter.skriv(FALT) + BRODTEXT
        ny = frontmatter.andrad(text, "arenden", "[KS-2025-1, KS-2025-2]")
        vantad = text.replace(
            "\narenden: null\n", "\narenden: [KS-2025-1, KS-2025-2]\n"
        )
        self.assertEqual(ny, vantad)

    def test_ett_falt_som_saknas_stoppar(self):
        text = "---\ntyp: protokoll\n---\n" + BRODTEXT
        self.assertRaises(KeyError, frontmatter.andrad, text, "arenden", "[]")


class TestNull(unittest.TestCase):
    def test_saknas_bara_for_null(self):
        self.assertTrue(frontmatter.saknas("null"))
        for varde in ("", "0", "[]", "Null", "nullnull"):
            with self.subTest(varde):
                self.assertFalse(frontmatter.saknas(varde))

    def test_granskad(self):
        self.assertFalse(frontmatter.granskad(FALT))
        self.assertTrue(frontmatter.granskad(FALT | {"granskad": "2026-11-01"}))

    def test_ar_ur_datum(self):
        self.assertEqual(frontmatter.ar({"datum": "2025-04-22"}), 2025)
        self.assertRaises(ValueError, frontmatter.ar, {"datum": "null"})


class TestVarden(unittest.TestCase):
    def test_varde_av(self):
        self.assertEqual(frontmatter.varde_av(None), "null")
        self.assertEqual(frontmatter.varde_av(date(2025, 4, 22)), "2025-04-22")
        self.assertEqual(frontmatter.varde_av(["a", None]), "[a, null]")
        self.assertEqual(frontmatter.varde_av(3), "3")

    def test_lista(self):
        self.assertEqual(frontmatter.lista("null"), [])
        self.assertEqual(frontmatter.lista("[]"), [])
        self.assertEqual(frontmatter.lista("[a, b]"), ["a", "b"])

    def test_adresser(self):
        self.assertEqual(frontmatter.adresser("https://a/1.pdf"), ["https://a/1.pdf"])
        delar = "[https://a/1.pdf, https://a/2.pdf]"
        self.assertEqual(
            frontmatter.adresser(delar), ["https://a/1.pdf", "https://a/2.pdf"]
        )


if __name__ == "__main__":
    unittest.main()
