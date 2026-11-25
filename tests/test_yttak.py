"""Krav: K92, ADR-0115. Kod: src/kommunhandlingar/konvertering/dokument.py och
src/kommunhandlingar/tolkning.py."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pypdfium2 as pdfium
from PIL import Image

from kommunhandlingar import tolkning
from kommunhandlingar.konvertering import dokument
from kommunhandlingar.konvertering.dokument import konvertera

A0 = 2384 * 3370  # kvadratpunkter


def pdf_med_sida(bredd: int, hojd: int) -> bytes:
    """En sida med en rad text, så att den läses när den inte är för stor."""
    strom = b"BT /F1 12 Tf 1 0 0 1 60 60 Tm (Antalet brukare var 7) Tj ET"
    objekt = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] /Contents 4 0 R"
        b" /Resources << /Font << /F1 5 0 R >> >> >>" % (bredd, hojd),
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(strom), strom),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    ut, platser = b"%PDF-1.4\n", []
    for nr, innehall in enumerate(objekt, 1):
        platser.append(len(ut))
        ut += b"%d 0 obj\n%s\nendobj\n" % (nr, innehall)
    xref = b"".join(b"%010d 00000 n \n" % p for p in platser)
    return ut + (
        b"xref\n0 6\n0000000000 65535 f \n%strailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n%d\n%%%%EOF\n" % (xref, len(ut))
    )


def konverterad(bredd: int, hojd: int) -> dokument.Resultat:
    with tempfile.TemporaryDirectory() as katalog:
        pdf = Path(katalog) / "sida.pdf"
        pdf.write_bytes(pdf_med_sida(bredd, hojd))
        return konvertera(pdf)


class TestYttaket(unittest.TestCase):
    def test_taket_ar_pillows_grans_i_300_dpi(self):
        pixlar = dokument.YTTAK * (300 / 72) ** 2
        self.assertAlmostEqual(pixlar, 2 * Image.MAX_IMAGE_PIXELS)

    def test_en_a0_ryms_under_taket(self):
        self.assertLess(A0, dokument.YTTAK)

    def test_sida_over_taket_blir_ej_konverterad_figur(self):
        # Läses sidan ändå faller testet i stället för att rendera gigabyte.
        with mock.patch.object(dokument, "las_sida", side_effect=AssertionError):
            resultat = konverterad(14400, 14400)
        self.assertEqual(resultat.kvalitet_per_sida, ["ej-konverterad"])
        self.assertEqual(resultat.sidor[0].text, "")
        self.assertEqual(resultat.figurer, [1])

    def test_tolkningen_renderar_en_for_stor_sida_mindre(self):
        with tempfile.TemporaryDirectory() as katalog:
            pdf = Path(katalog) / "sida.pdf"
            pdf.write_bytes(pdf_med_sida(14400, 14400))
            with pdfium.PdfDocument(pdf) as dokumentet:
                png = tolkning.spara(dokumentet, 1, Path(katalog))
            with Image.open(png) as bild:
                self.assertLess(bild.width * bild.height, 1.01 * tolkning.PIXLAR)
                self.assertGreater(bild.width, 9000)

    def test_tolkningen_renderar_en_a4_i_dubbel_skala(self):
        with pdfium.PdfDocument(pdf_med_sida(595, 842)) as dokumentet:
            self.assertEqual(tolkning.skala(dokumentet[0]), tolkning.SKALA)

    def test_sida_under_taket_lases(self):
        resultat = konverterad(595, 842)
        self.assertEqual(resultat.kvalitet_per_sida, ["ok"])
        self.assertIn("Antalet brukare var 7", resultat.sidor[0].text)
