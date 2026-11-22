"""Krav: K84, ADR-0105. Kod: src/kommunhandlingar/konvertering/upphojt.py.

Raderna är ritade med rektanglar i stället för bokstäver: versaler 30
punkter höga, gemener 21, på baslinjen 50, så att facit går att räkna ut.
Radens ruta går från 12 till 58 i utsnittet, som är 70 högt.
"""

import unittest

from PIL import Image, ImageDraw

from kommunhandlingar.konvertering.upphojt import har_upphojt, upphojd_rad

BASLINJE = 50
RUTAN = (12, 58)


def rad(*tecken: tuple[int, int, int, int]) -> Image.Image:
    """En vit rad med svarta rektanglar (x, bredd, överkant, underkant)."""
    bild = Image.new("L", (400, 70), 255)
    ritning = ImageDraw.Draw(bild)
    for x, bredd, o, n in tecken:
        ritning.rectangle((x, o, x + bredd - 1, n - 1), fill=0)
    return bild


def ord_(start: int) -> list[tuple[int, int, int, int]]:
    """En versal och tre gemener på baslinjen."""
    versal = (start, 14, BASLINJE - 30, BASLINJE)
    gemener = [(start + 18 + 16 * i, 12, BASLINJE - 21, BASLINJE) for i in range(3)]
    return [versal, *gemener]


class HarUpphojt(unittest.TestCase):
    def test_vanlig_rad(self):
        self.assertFalse(har_upphojt(rad(*ord_(10), *ord_(100)), RUTAN))

    def test_fotnotssiffra(self):
        siffra = (180, 8, BASLINJE - 30, BASLINJE - 12)
        self.assertTrue(har_upphojt(rad(*ord_(10), *ord_(100), siffra), RUTAN))

    def test_prick_och_ring_hor_till_bokstaven(self):
        prick = (36, 6, BASLINJE - 29, BASLINJE - 25)
        ring = (46, 8, BASLINJE - 30, BASLINJE - 23)
        self.assertFalse(har_upphojt(rad(*ord_(10), *ord_(100), prick, ring), RUTAN))

    def test_bindestreck_raknas_inte(self):
        streck = (82, 10, BASLINJE - 12, BASLINJE - 9)
        self.assertFalse(har_upphojt(rad(*ord_(10), streck, *ord_(100)), RUTAN))

    def test_snett_angransande_delar_ar_ett_tecken(self):
        trappa = [
            (200 + 3 * i, 3, BASLINJE - 30 + 3 * i, BASLINJE - 27 + 3 * i)
            for i in range(10)
        ]
        self.assertFalse(har_upphojt(rad(*ord_(10), *ord_(100), *trappa), RUTAN))

    def test_raden_nedanfor_slas_inte_ihop_med_en_fotnotssiffra(self):
        siffra = (180, 8, BASLINJE - 30, BASLINJE - 12)
        nedanfor = (178, 12, 62, 70)
        self.assertTrue(
            har_upphojt(rad(*ord_(10), *ord_(100), siffra, nedanfor), RUTAN)
        )

    def test_bara_delar_vid_kanten_gar_inte_att_bedoma(self):
        self.assertTrue(har_upphojt(rad((10, 14, 0, 30), (40, 14, 40, 70)), RUTAN))

    def test_understrykning_slar_inte_ihop_raden(self):
        siffra = (180, 8, BASLINJE - 30, BASLINJE - 12)
        linje = (5, 390, 54, 56)
        self.assertTrue(har_upphojt(rad(*ord_(10), *ord_(100), siffra, linje), RUTAN))

    def test_siffra_som_nuddar_bokstaven_fore(self):
        siffra = (161, 8, 20, 28)
        self.assertTrue(har_upphojt(rad(*ord_(10), *ord_(100), siffra), RUTAN))

    def test_siffra_vid_rutans_overkant(self):
        siffra = (180, 8, 12, 30)
        self.assertTrue(har_upphojt(rad(*ord_(10), *ord_(100), siffra), RUTAN))

    def test_raden_ovanfor_utanfor_rutan_raknas_inte(self):
        ovanfor = (180, 8, 2, 14)
        self.assertFalse(har_upphojt(rad(*ord_(10), *ord_(100), ovanfor), RUTAN))

    def test_tom_bild(self):
        self.assertFalse(har_upphojt(Image.new("L", (40, 20), 255), (2, 18)))


class UpphojdRad(unittest.TestCase):
    RADEN = (100, 1000, 900, 1060)

    def test_fotnotssiffra_med_egen_rad(self):
        siffra = (905, 996, 940, 1040)
        self.assertTrue(upphojd_rad(siffra, [self.RADEN, siffra]))

    def test_rad_pa_samma_baslinje(self):
        liten = (905, 1015, 940, 1058)
        self.assertFalse(upphojd_rad(liten, [self.RADEN, liten]))

    def test_rad_langt_bort_i_sidled(self):
        siffra = (1500, 996, 1535, 1040)
        self.assertFalse(upphojd_rad(siffra, [self.RADEN, siffra]))

    def test_raden_ovanfor(self):
        ovanfor = (100, 940, 900, 995)
        self.assertFalse(upphojd_rad(ovanfor, [self.RADEN, ovanfor]))


if __name__ == "__main__":
    unittest.main()
