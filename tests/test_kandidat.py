"""Krav: K13 i docs/02-KRAV.md, ADR-0010 och ADR-0018.
Kod: src/kommunhandlingar/kandidat.py."""

import random
import unittest
from datetime import date

from kommunhandlingar.kandidat import Avvisad, Fynd, Kandidat, ordna, ordna_bakat


def kandidat(organ: str, typ: str, datum: str, nod: str) -> Kandidat:
    return Kandidat(
        organ, date.fromisoformat(datum), typ, "u", "k", f"sitevision:{nod}", "f"
    )


FORVANTAD = [
    kandidat("ga", "protokoll", "2024-01-24", "18.2"),
    kandidat("ga", "protokoll", "2024-01-24", "18.3"),
    kandidat("ga", "protokoll", "2025-03-01", "18.1"),
    kandidat("ga", "kallelse", "2024-01-24", "18.4"),
    kandidat("ga", "bilaga", "2024-01-24", "18.5"),
    kandidat("ga", "handlingar", "2023-12-01", "18.6"),
    kandidat("kf", "protokoll", "2023-01-01", "18.7"),
]


class TestOrdningen(unittest.TestCase):
    def test_organ_typ_datum_och_kallnyckel(self):
        self.assertEqual(ordna(list(reversed(FORVANTAD)), ["ga", "kf"]), FORVANTAD)

    def test_upptacktsordningen_spelar_ingen_roll(self):
        for fro in range(5):
            blandad = FORVANTAD[:]
            random.Random(fro).shuffle(blandad)
            self.assertEqual(ordna(blandad, ["ga", "kf"]), FORVANTAD)

    def test_organen_i_konfigurationens_ordning(self):
        ordnade = ordna(FORVANTAD, ["kf", "ga"])
        self.assertEqual(ordnade[0].organ, "kf")


class TestArkivetsOrdning(unittest.TestCase):
    def test_nyast_forst_for_alla_organ(self):
        forvantad = [
            kandidat("ga", "protokoll", "2025-03-01", "18.1"),
            kandidat("ga", "protokoll", "2024-01-24", "18.2"),
            kandidat("ga", "protokoll", "2024-01-24", "18.3"),
            kandidat("ga", "kallelse", "2024-01-24", "18.4"),
            kandidat("kf", "protokoll", "2024-01-24", "18.8"),
            kandidat("ga", "handlingar", "2023-12-01", "18.6"),
            kandidat("kf", "protokoll", "2023-01-01", "18.7"),
        ]
        for fro in range(5):
            blandad = forvantad[:]
            random.Random(fro).shuffle(blandad)
            self.assertEqual(ordna_bakat(blandad, ["ga", "kf"]), forvantad)


class TestFynden(unittest.TestCase):
    def test_tva_fynd_laggs_ihop_i_ordning(self):
        forsta = Fynd(FORVANTAD[:2], [Avvisad("k", "a", "x")], ["en"])
        andra = Fynd(FORVANTAD[2:3], [Avvisad("k", "b", "y")], ["två"])
        self.assertEqual(
            forsta + andra,
            Fynd(
                FORVANTAD[:3],
                [Avvisad("k", "a", "x"), Avvisad("k", "b", "y")],
                ["en", "två"],
            ),
        )

    def test_inga_fynd_ar_tomma_listor(self):
        self.assertEqual(Fynd(), Fynd([], [], []))

    def test_fynden_summeras_fran_inga_fynd(self):
        delar = [Fynd(FORVANTAD[:1]), Fynd(noteringar=["n"]), Fynd(FORVANTAD[1:2])]
        self.assertEqual(sum(delar, Fynd()), Fynd(FORVANTAD[:2], [], ["n"]))

    def test_sammanlaggningen_andrar_inte_delarna(self):
        forsta = Fynd(FORVANTAD[:1])
        forsta + Fynd(FORVANTAD[1:2])  # noqa: B018
        self.assertEqual(forsta, Fynd(FORVANTAD[:1]))


if __name__ == "__main__":
    unittest.main()
