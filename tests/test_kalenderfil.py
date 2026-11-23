"""Krav: K22 i docs/02-KRAV.md, ADR-0032. Kod: src/kommunhandlingar/webbplats/
kalender.py."""

import unittest

from kommunhandlingar.fel import Datafel
from kommunhandlingar.konfiguration import las as las_kommun
from kommunhandlingar.webbplats import kalender
from tests.kalenderfall import PROTOKOLL, RADER, ROT, RUBRIK, pool


class TestLasning(unittest.TestCase):
    def test_raderna_lases(self):
        with pool() as sammantraden:
            self.assertEqual(len(sammantraden), 3)
            self.assertEqual(sammantraden[0].tid, "17:00")
            self.assertEqual(sammantraden[2].osakert, "Källan säger lördag <5 dec>.")

    def stoppas(self, rader: str, rubrik: str = RUBRIK) -> str:
        with self.assertRaises(Datafel) as fel, pool(rader, rubrik):
            pass
        return str(fel.exception)

    def test_fel_rubriker(self):
        self.assertIn("rubrikerna", self.stoppas(RADER, "organ,datum\n"))

    def test_okant_organ(self):
        fel = self.stoppas(f"kun,2027-01-14,,,{PROTOKOLL},\n")
        self.assertIn("rad 2", fel)
        self.assertIn("'kun'", fel)

    def test_datum_som_inte_finns(self):
        self.assertIn("rad 2", self.stoppas(f"fsn,2027-02-30,,,{PROTOKOLL},\n"))

    def test_samma_organ_samma_dag(self):
        fel = self.stoppas(RADER + f"fsn,2027-01-14,,,{PROTOKOLL},\n")
        self.assertIn("rad 5", fel)

    def test_kalla_som_inte_ar_ett_dokument_i_poolen(self):
        for kalla in ("fsn/2027/protokoll.md", "fsn/2026/2026-09-17/saknas.md"):
            fel = self.stoppas(f"fsn,2027-01-14,,,{kalla},\n")
            self.assertIn("inget dokument i poolen", fel)

    def test_datum_i_annan_form(self):
        self.assertIn("ÅÅÅÅ-MM-DD", self.stoppas(f"fsn,20270114,,,{PROTOKOLL},\n"))

    def test_helgdag_som_inte_ar_markt(self):
        fel = self.stoppas("bun,2026-12-05,,,https://exempelby.se/bun,\n")
        self.assertIn("lördag eller söndag", fel)

    def test_fel_antal_falt(self):
        self.assertIn("rad 2", self.stoppas("fsn,2027-01-14\n"))


class TestKungsbacka(unittest.TestCase):
    def test_filen_gar_ihop_med_kommunfilen_och_poolen(self):
        kungsbacka = las_kommun(ROT / "kommuner" / "kungsbacka.toml")
        fil = ROT / "kalender" / "kungsbacka.csv"
        sammantraden = kalender.las(fil, kungsbacka, ROT / "data" / "kungsbacka")
        self.assertNotIn("revision", {s.organ for s in sammantraden})
        self.assertEqual(min(s.datum for s in sammantraden).year, 2024)
        self.assertEqual(fil.read_bytes().count(b"\r"), 0)
