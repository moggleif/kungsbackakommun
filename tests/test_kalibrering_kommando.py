"""Krav: K84, ADR-0105. Kod: src/kommunhandlingar/kalibrering/__main__.py
och rapport.py.

Kommandot körs på tests/fixtures/pdf/vag-h.pdf i stället för en hämtad PDF.
"""

import runpy
import shutil
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.hamtning.klient import Klient
from kommunhandlingar.kalibrering import matning, rapport, urval
from kommunhandlingar.kalibrering.__main__ import main
from kommunhandlingar.kalibrering.matning import Sidutfall
from kommunhandlingar.konvertering import radlasning
from tests.kalibreringsfall import SHA, dokument, kopiera, utfall


class Rapport(unittest.TestCase):
    PROV = urval.Prov("k/a.md", "https://exempel.se/a.pdf", SHA, [1, 2])

    def test_kravet_ar_inte_uppfyllt_med_ett_fel_pa_en_bekraftad_sida(self):
        resultat = rapport.Resultat(2)
        rader = [utfall("ratt"), utfall("fel"), utfall("utan-facit")]
        resultat.sidor.append((self.PROV, 1, Sidutfall(rader, True)))
        obekraftad = Sidutfall([utfall("obekraftad", "oense")], False)
        resultat.sidor.append((self.PROV, 2, obekraftad))
        resultat.ej_matta.append((self.PROV, "sha256 ändrad i källan"))
        text = rapport.sammanfattning(resultat)
        self.assertIn("| bekräftade | 1 |", text)
        self.assertIn("| bekräftade med rader utan facit | 1 |", text)
        self.assertIn("| bekräftade med en falsk bekräftelse | 1 |", text)
        self.assertIn("**Kravet är inte uppfyllt: 1 falska bekräftelser.**", text)
        self.assertIn("- `k/a.md` sida 1: fel, läst `1`, textlagret `2`", text)
        self.assertIn("| oense | 1 |", text)
        self.assertFalse(rapport.uppfyllt(resultat))

    def test_fel_pa_en_obekraftad_sida_ror_inte_kravet(self):
        resultat = rapport.Resultat(1)
        resultat.sidor.append((self.PROV, 1, Sidutfall([utfall("fel")], False)))
        self.assertIn("**Kravet är uppfyllt.**", rapport.sammanfattning(resultat))
        self.assertTrue(rapport.uppfyllt(resultat))

    def test_for_fa_matta_sidor(self):
        resultat = rapport.Resultat(300)
        resultat.sidor.append((self.PROV, 1, Sidutfall([utfall("ratt")], True)))
        text = rapport.sammanfattning(resultat)
        self.assertIn("**Kravet är inte prövat: för få sidor är mätta.**", text)
        self.assertFalse(rapport.uppfyllt(resultat))


class Kommando(unittest.TestCase):
    def setUp(self):
        self.rot = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.rot)
        (self.rot / "hamtning.toml").write_text('user_agent = "test"\nintervall = 0\n')
        self.sidor = [" ".join(["2027 4 078 12,5 1 845 11 2026 42 15 4"] * 2)]
        (self.rot / "data" / "k").mkdir(parents=True)
        self.skriv("a.md", SHA)

    def skriv(self, namn: str, sha256: str) -> None:
        text = dokument("[ok]", "[]", self.sidor, sha256=sha256)
        (self.rot / "data" / "k" / namn).write_text(text)

    def kor(self, hamta, antal: int = 1) -> tuple[str, int]:
        argv = [str(self.rot / "data"), str(self.rot / "ut"), "--antal", str(antal)]
        with patch.object(Klient, "fil", hamta), self.assertRaises(SystemExit) as slut:
            main(argv)
            raise SystemExit(0)
        text = (self.rot / "ut" / "rapport.md").read_text(encoding="utf-8")
        return text, slut.exception.code

    def test_mater_den_hamtade_pdf_en(self):
        text, kod = self.kor(kopiera)
        self.assertIn("Mätta sidor: 1 av 1. Ej mätta: 0.", text)
        self.assertIn("**Kravet är uppfyllt.**", text)
        self.assertEqual(kod, 0)
        rader = (self.rot / "ut" / "rader.csv").read_text(encoding="utf-8")
        self.assertIn("k/a.md,1,False,upphojt,obekraftad", rader)

    def test_en_falsk_bekraftelse_ger_kod_1(self):
        falsk = Sidutfall([utfall("fel")], True)
        with patch.object(matning, "mat", return_value=falsk):
            text, kod = self.kor(kopiera)
        self.assertEqual(kod, 1)
        self.assertIn("Kravet är inte uppfyllt", text)

    def test_for_fa_sidor_ger_kod_1(self):
        text, kod = self.kor(kopiera, antal=5)
        self.assertEqual(kod, 1)
        self.assertIn("Mätta sidor: 1 av 5.", text)

    def test_nasta_dokument_tas_nar_ett_inte_gar_att_hamta(self):
        self.skriv("b.md", "annan")

        forsok = iter([b"%PDF annan", None])

        def vaxla(_, url, mal):
            innehall = next(forsok)
            if innehall is None:
                kopiera(_, url, mal)
            else:
                mal.write_bytes(innehall)

        text, kod = self.kor(vaxla)
        self.assertEqual(kod, 0)
        self.assertIn("Mätta sidor: 1 av 1. Ej mätta: 1.", text)

    def test_slutar_nar_antalet_ar_matt(self):
        prov = urval.Prov("k/a.md", "https://exempel.se/a.pdf", SHA, [1])
        andra = urval.Prov("k/b.md", "https://exempel.se/b.pdf", "b", [1])
        with patch.object(urval, "kandidater", return_value=iter([prov, andra])):
            text, kod = self.kor(kopiera)
        self.assertEqual(kod, 0)
        self.assertIn("Mätta sidor: 1 av 1. Ej mätta: 0.", text)

    def test_som_modul(self):
        argv = ["kalibrering", str(self.rot / "data"), str(self.rot / "ut")]
        with (
            warnings.catch_warnings(),
            patch.object(sys, "argv", argv + ["--antal", "1"]),
            patch.object(Klient, "fil", kopiera),
        ):
            # runpy varnar när modulen redan är importerad.
            warnings.simplefilter("ignore", RuntimeWarning)
            runpy.run_module("kommunhandlingar.kalibrering", run_name="__main__")
        self.assertTrue((self.rot / "ut" / "rader.csv").exists())

    def test_andrad_pdf_mats_inte(self):
        text, _ = self.kor(lambda _, url, mal: mal.write_bytes(b"%PDF annan"))
        self.assertIn("Ej mätt: `k/a.md`, sha256 ändrad i källan", text)

    def test_pdf_som_inte_gick_att_hamta(self):
        def hamta(_, url, mal):
            raise Hamtfel("http-404")

        text, _ = self.kor(hamta)
        self.assertIn("Ej mätt: `k/a.md`, hämtning: http-404", text)

    def test_tesseract_som_fallerar(self):
        fallerar = patch.object(
            radlasning, "tesseracts_tsv", side_effect=radlasning.Fallerade
        )
        with fallerar:
            text, _ = self.kor(kopiera)
        self.assertIn("Tesseract fallerade på sidan 1", text)


if __name__ == "__main__":
    unittest.main()
