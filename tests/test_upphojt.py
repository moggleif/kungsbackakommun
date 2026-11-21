"""Krav: K84, ADR-0105. Kod: src/kommunhandlingar/konvertering/upphojt.py.

Raderna är ritade med rektanglar i stället för bokstäver: versaler 30
punkter höga, gemener 21, på baslinjen 50, så att facit går att räkna ut.
"""

import unittest

from PIL import Image, ImageDraw

from kommunhandlingar.konvertering.upphojt import har_upphojt, upphojd_rad

BASLINJE = 50


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
        self.assertFalse(har_upphojt(rad(*ord_(10), *ord_(100))))

    def test_fotnotssiffra(self):
        siffra = (180, 8, BASLINJE - 30, BASLINJE - 12)
        self.assertTrue(har_upphojt(rad(*ord_(10), *ord_(100), siffra)))

    def test_prick_och_ring_hor_till_bokstaven(self):
        prick = (36, 6, BASLINJE - 29, BASLINJE - 25)
        ring = (54, 8, BASLINJE - 30, BASLINJE - 23)
        self.assertFalse(har_upphojt(rad(*ord_(10), *ord_(100), prick, ring)))

    def test_bindestreck_raknas_inte(self):
        streck = (82, 10, BASLINJE - 12, BASLINJE - 9)
        self.assertFalse(har_upphojt(rad(*ord_(10), streck, *ord_(100))))

    def test_snett_angransande_delar_ar_ett_tecken(self):
        trappa = [
            (200 + 3 * i, 3, BASLINJE - 30 + 3 * i, BASLINJE - 27 + 3 * i)
            for i in range(10)
        ]
        self.assertFalse(har_upphojt(rad(*ord_(10), *ord_(100), *trappa)))

    def test_tom_bild(self):
        self.assertFalse(har_upphojt(Image.new("L", (40, 20), 255)))


class UpphojdRad(unittest.TestCase):
    RADEN = (100, 1000, 900, 1060)

    def test_fotnotssiffra_med_egen_rad(self):
        siffra = (905, 996, 940, 1040)
        self.assertTrue(upphojd_rad(siffra, [self.RADEN, siffra]))

    def test_rad_pa_samma_baslinje(self):
        liten = (905, 1015, 940, 1058)
        self.assertFalse(upphojd_rad(liten, [self.RADEN, liten]))

    def test_raden_ovanfor(self):
        ovanfor = (100, 940, 900, 995)
        self.assertFalse(upphojd_rad(ovanfor, [self.RADEN, ovanfor]))


if __name__ == "__main__":
    unittest.main()
