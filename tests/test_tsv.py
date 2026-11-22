"""Krav: K6, ADR-0005. Kod: src/kommunhandlingar/konvertering/tsv.py.

TSV:n är påhittad i Tesseracts format: en rad per sida, block, stycke, rad
och ord, där bara orden har en säkerhet.
"""

import unittest

from kommunhandlingar.konvertering.tsv import Ord, orden

KOLUMNER = [
    "level",
    "page_num",
    "block_num",
    "par_num",
    "line_num",
    "word_num",
    "left",
    "top",
    "width",
    "height",
    "conf",
    "text",
]


def tsv(*rader: tuple) -> str:
    return "\n".join("\t".join(map(str, r)) for r in [KOLUMNER, *rader])


class TestOrden(unittest.TestCase):
    def test_ett_ord_med_ruta_och_radnyckel(self):
        lasning = tsv((5, 1, 2, 3, 4, 1, 10, 20, 30, 40, "91.5", "Protokoll"))
        self.assertEqual(
            orden(lasning),
            [Ord("Protokoll", 91.5, (10, 20, 40, 60), ("1", "2", "3", "4"))],
        )

    def test_rader_med_sakerhet_minus_ett_raknas_inte(self):
        lasning = tsv(
            (4, 1, 1, 1, 1, 0, 0, 0, 100, 20, -1, ""),
            (5, 1, 1, 1, 1, 1, 0, 0, 50, 20, -1, "brus"),
            (5, 1, 1, 1, 1, 2, 60, 0, 40, 20, 88, "ord"),
        )
        self.assertEqual([o.text for o in orden(lasning)], ["ord"])

    def test_tomma_ord_raknas_inte(self):
        lasning = tsv(
            (5, 1, 1, 1, 1, 1, 0, 0, 10, 20, 40, " "),
            (5, 1, 1, 1, 1, 2, 20, 0, 10, 20, 90, ""),
        )
        self.assertEqual(orden(lasning), [])

    def test_citattecken_i_texten_tal_lasningen(self):
        lasning = tsv(
            (5, 1, 1, 1, 1, 1, 0, 0, 10, 20, 90, '"Gröna'),
            (5, 1, 1, 1, 1, 2, 20, 0, 10, 20, 90, 'rum"'),
            (5, 1, 1, 1, 1, 3, 40, 0, 10, 20, 90, "nästa"),
        )
        self.assertEqual([o.text for o in orden(lasning)], ['"Gröna', 'rum"', "nästa"])

    def test_texten_behaller_sina_blanksteg(self):
        lasning = tsv((5, 1, 1, 1, 1, 1, 0, 0, 10, 20, 90, " ord "))
        self.assertEqual(orden(lasning)[0].text, " ord ")


if __name__ == "__main__":
    unittest.main()
