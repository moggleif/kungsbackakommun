"""Krav: K6, ADR-0005.
Kod: src/kommunhandlingar/konvertering/dokument.py."""

import unittest
from pathlib import Path
from unittest import mock

from kommunhandlingar.konvertering.dokument import konvertera

BEGRANSAD = Path(__file__).parent / "fixtures" / "pdf" / "begransad.pdf"
LAS = "kommunhandlingar.konvertering.dokument.las_sidor"


class TestDokumentfel(unittest.TestCase):
    def test_godtyckligt_fel_ur_pdfminer_ger_trasig_pdf_och_en_loggrad(self):
        with (
            mock.patch(LAS, side_effect=TypeError("x")),
            mock.patch("sys.stderr") as stderr,
        ):
            resultat = konvertera(BEGRANSAD)
        self.assertEqual(resultat.fel, "trasig-pdf")
        self.assertTrue(stderr.write.called)

    def test_dokument_utan_sidor_ger_trasig_pdf(self):
        with mock.patch(LAS, return_value=[]):
            resultat = konvertera(BEGRANSAD)
        self.assertEqual(
            (resultat.kvalitet, resultat.fel), ("ej-konverterad", "trasig-pdf")
        )


if __name__ == "__main__":
    unittest.main()
