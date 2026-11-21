"""Krav: K6, ADR-0038, ADR-0103. Kod: src/kommunhandlingar/konvertering/ordning.py.

Tecknen är påhittade efter sidorna i #119: datumet `2025-05-21` som ritats
ovanpå slutet av `stöd` i cellen till vänster.
"""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pdfplumber

from kommunhandlingar.konvertering import las_sida
from kommunhandlingar.konvertering.las_sida import textsida
from kommunhandlingar.konvertering.ordning import i_oordning

PDF = Path(__file__).parent / "fixtures" / "pdf"
HOGKANT = PDF / "hogkant.pdf"


def tecken(text: str, x0: float, bredd: float = 5.6, upright: bool = True) -> dict:
    return {
        "object_type": "char",
        "text": text,
        "x0": x0,
        "x1": x0 + bredd,
        "top": 134,
        "bottom": 140,
        "upright": upright,
    }


def vriden(text: str, x0: float, top: float = 134) -> dict:
    """Ett tecken vridet en kvarts varv moturs, som i tests/test_hogkant.py."""
    return dict(
        tecken(text, x0, 9, upright=False),
        top=top,
        bottom=top + 6,
        matrix=(0, 9, -9, 0, 0, 0),
    )


def sida(*tecken_: dict) -> SimpleNamespace:
    return SimpleNamespace(chars=list(tecken_))


STOD = [tecken("ö", 421.6), tecken("d", 427.2), tecken(" ", 432.8, 2.1)]


class TestOrdning(unittest.TestCase):
    def test_text_i_ordning(self):
        self.assertFalse(i_oordning(sida(*STOD, tecken("2", 434.8)), []))

    def test_text_ritad_ovanpa_annan_text(self):
        """Som i textlagret: en tvåa efter `stöd`, sedan datumet ovanpå."""
        datum = [tecken("2", 434.8), tecken("2", 425.8), tecken("0", 431.4)]
        self.assertTrue(i_oordning(sida(*STOD, *datum), []))

    def test_grannar_som_overlappar_raknas_inte(self):
        """Kursiv stil: tecknens rutor är bredare än tecknen."""
        kursiv = [tecken("r", 139.9, 6.6), tecken("i", 143.3), tecken("g", 146.1)]
        self.assertFalse(i_oordning(sida(*kursiv), []))

    def test_samma_tecken_tva_ganger_raknas_inte(self):
        """Fetstil som ritats två gånger, något förskjuten."""
        fet = [tecken("A", 100), tecken("B", 106), tecken("A", 100.3)]
        self.assertFalse(i_oordning(sida(*fet), []))

    def test_hogkant_i_en_tabell(self):
        self.assertTrue(i_oordning(sida(*STOD, vriden("N", 50)), [(40, 120, 70, 150)]))

    def test_hogkant_utanfor_tabellerna_raknas_inte(self):
        """Den läses för sig och skrivs sist på sidan (K41)."""
        n = vriden("N", 50)
        self.assertFalse(i_oordning(sida(*STOD, n), [(300, 120, 400, 150)]))

    def test_hogkant_ovanpa_uppratt_text(self):
        """En siffra på högkant ritad ovanpå en rad kan flytta talen i den."""
        self.assertTrue(i_oordning(sida(*STOD, vriden("5", 425.8)), []))

    def test_hogkant_bredvid_uppratt_text_raknas_inte(self):
        self.assertFalse(i_oordning(sida(*STOD, vriden("5", 440)), []))

    def test_hogkant_som_inte_gar_att_lasa_entydigt(self):
        """Två årtal på högkant så tätt att de läses ihop till `22001101`."""
        tatt = [vriden(t, 40, 80 - 6 * i) for i, t in enumerate("2010")]
        tatt += [vriden(t, 47, 80 - 6 * i) for i, t in enumerate("2011")]
        self.assertTrue(i_oordning(sida(*STOD, *tatt), []))


class TestRader(unittest.TestCase):
    def test_kursiv_over_ett_mellanrum_raknas_inte(self):
        """Mellanslaget mellan grannarna räknas inte."""
        kursiv = [tecken("f", 100, 7), tecken(" ", 105, 2), tecken("a", 103)]
        self.assertFalse(i_oordning(sida(*kursiv), []))

    def test_tecken_pa_olika_rader_overlappar_inte(self):
        under = dict(tecken("2", 425.8), top=148)
        self.assertFalse(i_oordning(sida(*STOD, tecken("0", 440), under), []))


class TestSidan(unittest.TestCase):
    def test_sidan_i_oordning_far_obekraftade_tal(self):
        with pdfplumber.open(PDF / "sidor.pdf") as pdf:
            sida = pdf.pages[0]
            self.assertFalse(textsida(sida).tal_obekraftade)
            with patch.object(las_sida, "i_oordning", return_value=True):
                self.assertTrue(textsida(sida).tal_obekraftade)

    def test_diarienummer_pa_hogkant_ger_bekraftade_tal(self):
        """Sida 1 i hogkant.pdf: ett stycke och ett diarienummer på högkant."""
        with pdfplumber.open(HOGKANT) as pdf:
            self.assertFalse(textsida(pdf.pages[0]).tal_obekraftade)

    def test_kolumnrubrik_pa_hogkant_ger_obekraftade_tal(self):
        """Sida 3 i hogkant.pdf: en tabell vars kolumnrubrik står på högkant."""
        with pdfplumber.open(HOGKANT) as pdf:
            self.assertTrue(textsida(pdf.pages[2]).tal_obekraftade)
