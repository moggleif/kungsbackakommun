"""Kod: src/kommunhandlingar/konvertering/geometri.py."""

import unittest

from kommunhandlingar.konvertering.geometri import inom, mitt, mitt_av, omslutande, ruta

ORDET = {"x0": 10, "top": 20, "x1": 30, "bottom": 24}


class TestGeometri(unittest.TestCase):
    def test_en_punkt_pa_kanten_ar_inom(self):
        for punkt in [(10, 20), (30, 24), (20, 20), (10, 22)]:
            self.assertTrue(inom(punkt, (10, 20, 30, 24)), punkt)

    def test_en_punkt_strax_utanfor_ar_inte_inom(self):
        for punkt in [(9.9, 22), (30.1, 22), (20, 19.9), (20, 24.1)]:
            self.assertFalse(inom(punkt, (10, 20, 30, 24)), punkt)

    def test_mitten_av_ett_objekt_och_av_dess_ruta_ar_densamma(self):
        self.assertEqual(mitt(ORDET), (20, 22))
        self.assertEqual(mitt_av(ruta(ORDET)), mitt(ORDET))

    def test_omslutande_ruta(self):
        rutor = [(10, 20, 30, 24), (5, 30, 12, 40), (25, 1, 28, 3)]
        self.assertEqual(omslutande(rutor), (5, 1, 30, 40))


if __name__ == "__main__":
    unittest.main()
