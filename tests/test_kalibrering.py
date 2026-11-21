"""Krav: K84, ADR-0105. Kod: src/kommunhandlingar/kalibrering/.

Mätningen körs på tests/fixtures/pdf/vag-h.pdf, där textlagret är facit.
"""

import hashlib
import runpy
import shutil
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pdfplumber
import pypdfium2 as pdfium

from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.hamtning.klient import Klient
from kommunhandlingar.kalibrering import facit, matning, rapport, urval
from kommunhandlingar.kalibrering.__main__ import main
from kommunhandlingar.kalibrering.matning import Sidutfall, Utfall
from kommunhandlingar.konvertering import radlasning, vag_h

VAG_H = Path(__file__).parent / "fixtures" / "pdf" / "vag-h.pdf"
SHA = hashlib.sha256(VAG_H.read_bytes()).hexdigest()
TALSIDA = " ".join(str(n) for n in range(15))


def dokument(kvalitet: str, obekraftade: str, sidor: list[str], **falt) -> str:
    huvud = {
        "kalla_url": "https://exempel.se/a.pdf",
        "sha256": SHA,
        "bytes": "1000",
        "kvalitet_per_sida": kvalitet,
        "tal_obekraftade": obekraftade,
    } | falt
    text = "".join(f"<!-- sida {n} -->\n\n{t}\n\n" for n, t in enumerate(sidor, 1))
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in huvud.items()) + "---\n\n" + text


class Urval(unittest.TestCase):
    def setUp(self):
        self.rot = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.rot)
        self.data = self.rot / "data"
        (self.data / "k").mkdir(parents=True)

    def skriv(self, namn: str, text: str) -> None:
        (self.data / "k" / namn).write_text(text, encoding="utf-8")

    def test_sidor_med_textlager_bekraftade_tal_och_manga_tal(self):
        sidor = [TALSIDA, TALSIDA, "inga tal", TALSIDA, TALSIDA]
        self.skriv("a.md", dokument("[ok, ocr, ok, ok, ok]", "[4]", sidor))
        self.assertEqual(urval.urval(self.data, 10, 1)[0].sidor, [1, 5])

    def test_hogst_tre_sidor_per_dokument_och_antalet(self):
        self.skriv("a.md", dokument("[ok, ok, ok, ok]", "[]", [TALSIDA] * 4))
        self.skriv("b.md", dokument("[ok, ok]", "[]", [TALSIDA] * 2))
        valda = urval.urval(self.data, 4, 1)
        self.assertEqual(sum(len(p.sidor) for p in valda), 4)
        self.assertTrue(all(len(p.sidor) <= 3 for p in valda))
        self.assertEqual(valda, urval.urval(self.data, 4, 1))

    def test_dokument_som_inte_kan_valjas(self):
        sida = [TALSIDA]
        self.skriv("delar.md", dokument("[ok]", "[]", sida, kalla_url="[a, b]"))
        self.skriv("ej.md", dokument("null", "[]", [], kalla_url="null"))
        self.skriv("stor.md", dokument("[ok]", "[]", sida, bytes="30000000"))
        self.skriv("okand.md", dokument("[ok]", "[]", sida, bytes="null"))
        self.skriv("README.md", "# Inget dokument\n")
        self.skriv("ocr.md", dokument("[ocr]", "[1]", sida))
        self.assertEqual(urval.urval(self.data, 10, 1), [])


class Facit(unittest.TestCase):
    ORD = [
        {"text": "Budget", "x0": 60, "x1": 90, "top": 100, "bottom": 110},
        {"text": "2027", "x0": 95, "x1": 115, "top": 100, "bottom": 110},
        {"text": "42", "x0": 60, "x1": 70, "top": 200, "bottom": 210},
    ]

    def sida(self, bilder: list) -> SimpleNamespace:
        return SimpleNamespace(images=bilder, extract_words=lambda: self.ORD)

    def ruta(self, x0, top, x1, bottom):
        return tuple(v / facit.SKALA for v in (x0, top, x1, bottom))

    def test_radens_tal_och_talen_utanfor(self):
        ruta = self.ruta(50, 95, 300, 115)
        self.assertEqual(facit.radens_tal(self.sida([]), ruta), ["2027"])
        self.assertEqual(facit.tal_utanfor(self.sida([]), [ruta]), ["42"])

    def test_en_rad_som_ror_en_bild_saknar_facit(self):
        bild = {"x0": 250, "x1": 350, "top": 90, "bottom": 220}
        ruta = self.ruta(50, 95, 300, 115)
        self.assertIsNone(facit.radens_tal(self.sida([bild]), ruta))
        self.assertEqual(facit.tal_utanfor(self.sida([bild]), [ruta]), ["42"])


def utfall(varde: str, hur: str = "eniga") -> Utfall:
    return Utfall(hur, varde, "1", "2", "r 1", "t 1")


class Rapport(unittest.TestCase):
    PROV = urval.Prov("k/a.md", "https://exempel.se/a.pdf", SHA, [1, 2])

    def test_kravet_ar_inte_uppfyllt_med_ett_fel_pa_en_bekraftad_sida(self):
        resultat = rapport.Resultat()
        resultat.lagg_till(
            self.PROV, 1, Sidutfall([utfall("ratt"), utfall("fel")], True)
        )
        resultat.lagg_till(
            self.PROV, 2, Sidutfall([utfall("obekraftad", "oense")], False)
        )
        resultat.ej_matt(self.PROV, "sha256 ändrad i källan")
        text = rapport.sammanfattning(resultat)
        self.assertIn("Bekräftade sidor: 1 av 2.", text)
        self.assertIn("**Kravet är inte uppfyllt.**", text)
        self.assertIn("- `k/a.md` sida 1: fel, läst `1`, textlagret `2`", text)
        self.assertIn("| oense | 1 |", text)

    def test_fel_pa_en_obekraftad_sida_ror_inte_kravet(self):
        resultat = rapport.Resultat()
        resultat.lagg_till(self.PROV, 1, Sidutfall([utfall("fel")], False))
        self.assertIn("**Kravet är uppfyllt.**", rapport.sammanfattning(resultat))


class Kommando(unittest.TestCase):
    def setUp(self):
        self.rot = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.rot)
        (self.rot / "hamtning.toml").write_text('user_agent = "test"\nintervall = 0\n')
        sidor = [" ".join(["2027 4 078 12,5 1 845 11 2026 42 15 4"] * 2)]
        (self.rot / "data" / "k").mkdir(parents=True)
        (self.rot / "data" / "k" / "a.md").write_text(dokument("[ok]", "[]", sidor))

    def kor(self, hamta) -> str:
        with patch.object(Klient, "fil", hamta):
            main([str(self.rot / "data"), str(self.rot / "ut"), "--antal", "5"])
        return (self.rot / "ut" / "rapport.md").read_text(encoding="utf-8")

    def test_mater_den_hamtade_pdf_en(self):
        text = self.kor(lambda _, url, mal: shutil.copy(VAG_H, mal))
        self.assertIn("Mätta sidor: 1. Ej mätta: 0.", text)
        self.assertIn("Bekräftade sidor: 0 av 1.", text)
        rader = (self.rot / "ut" / "rader.csv").read_text(encoding="utf-8")
        self.assertIn("k/a.md,1,False,upphojt,obekraftad", rader)

    def test_som_modul(self):
        argv = ["kalibrering", str(self.rot / "data"), str(self.rot / "ut")]
        with (
            warnings.catch_warnings(),
            patch.object(sys, "argv", argv),
            patch.object(Klient, "fil", lambda _, url, mal: shutil.copy(VAG_H, mal)),
        ):
            # runpy varnar när modulen redan är importerad.
            warnings.simplefilter("ignore", RuntimeWarning)
            runpy.run_module("kommunhandlingar.kalibrering", run_name="__main__")
        self.assertTrue((self.rot / "ut" / "rader.csv").exists())

    def test_andrad_pdf_mats_inte(self):
        text = self.kor(lambda _, url, mal: mal.write_bytes(b"%PDF annan"))
        self.assertIn("Ej mätt: `k/a.md`, sha256 ändrad i källan", text)

    def test_pdf_som_inte_gick_att_hamta(self):
        def hamta(_, url, mal):
            raise Hamtfel("http-404")

        self.assertIn("Ej mätt: `k/a.md`, hämtning: http-404", self.kor(hamta))

    def test_tesseract_som_fallerar(self):
        with patch.object(
            radlasning, "tesseracts_ord", side_effect=radlasning.Fallerade
        ):
            text = self.kor(lambda _, url, mal: shutil.copy(VAG_H, mal))
        self.assertIn("Tesseract fallerade på sidan 1", text)


class Matning(unittest.TestCase):
    def test_utan_facit_och_ratt(self):
        rad = radlasning.Rad((0, 0, 1, 1), "8", "8", vag_h.Avgorande(["8"], "eniga"))
        self.assertEqual(matning.utfall(rad, None).utfall, "utan-facit")
        self.assertEqual(matning.utfall(rad, ["8"]).utfall, "ratt")

    def test_missad_rad_och_tal_utanfor_raderna(self):
        forsta = tuple(v / facit.SKALA for v in (55, 70, 400, 90))
        lasning = radlasning.Sidlasning([], [forsta], 0)
        with (
            patch.object(radlasning, "las", return_value=lasning),
            pdfplumber.open(VAG_H) as plumber,
        ):
            pdf = pdfium.PdfDocument(VAG_H)
            sida = matning.mat(pdf, plumber, 1)
            pdf.close()
        self.assertEqual(sida.rader[0], Utfall("", "missad", "", "2027 4 078", "", ""))
        self.assertEqual(sida.rader[1].utfall, "utanfor")
        self.assertTrue(sida.bekraftad)


if __name__ == "__main__":
    unittest.main()
