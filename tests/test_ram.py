"""Kod: src/kommunhandlingar/webbplats/ram.py och `Kommun.organnamn` i
src/kommunhandlingar/konfiguration.py.

Målsidan, spårsidorna, kalendern och luckorna länkar besluten, bygger
"Om sidan" och urvalsknapparna på samma sätt; här prövas det direkt."""

import unittest
from pathlib import Path
from unittest import mock

from kommunhandlingar.konfiguration import las
from kommunhandlingar.webbplats import malsida, sparsida
from kommunhandlingar.webbplats.granskningsslag import GRANSKNINGAR
from kommunhandlingar.webbplats.ram import (
    BESLUTEN,
    beslutslank,
    hur_och_varfor,
    om_sidan,
    urval,
)

FIL = "0020-luckor-raknas-fram-lagras-inte.md"
EXEMPELBY = Path(__file__).parent / "fixtures" / "exempelby.toml"


class TestBesluten(unittest.TestCase):
    def test_lanken_har_beslutets_nummer(self):
        self.assertEqual(beslutslank(FIL), f'<a href="{BESLUTEN}{FIL}">ADR-0020</a>')

    def test_ett_beslut(self):
        self.assertEqual(
            hur_och_varfor("0001-a.md"),
            f'<p>Hur och varför står i <a href="{BESLUTEN}0001-a.md">ADR-0001</a>.</p>',
        )

    def test_tva_beslut_utan_komma(self):
        text = hur_och_varfor("0001-a.md", "0002-b.md")
        self.assertIn("ADR-0001</a> och <a", text)
        self.assertNotIn(",", text)

    def test_det_sista_beslutet_efter_och(self):
        text = hur_och_varfor("0001-a.md", "0002-b.md", "0003-c.md")
        self.assertIn("ADR-0001</a>, <a", text)
        self.assertIn("ADR-0002</a> och <a", text)

    def test_om_sidan_ar_hopfalld(self):
        text = om_sidan("<p>Metoden.</p>", "0001-a.md")
        self.assertTrue(text.startswith("<details><summary>Om sidan</summary>"))
        self.assertIn("<p>Metoden.</p><p>Hur och varför", text)


class TestUrval(unittest.TestCase):
    def test_vardena_escapas(self):
        text = urval([("<v>", "<t>")])
        self.assertIn('data-urval="&lt;v&gt;">&lt;t&gt;</button>', text)

    def test_sista_aret_star_fore_hidden(self):
        self.assertIn(
            'aria-label="Visa" data-sista="2026" hidden>',
            urval([], 2026),
        )

    def test_malsidan_escapar(self):
        with mock.patch.object(malsida, "SLAG", ("<slag>",)):
            text = malsida.urval(2026, {"<slag>"})
        self.assertIn('data-urval="&lt;slag&gt;"', text)
        self.assertNotIn("<slag>", text)

    def test_sparsidan_escapar(self):
        with mock.patch.object(sparsida, "avsandarna", return_value=["<M>"]):
            text = sparsida.urval(GRANSKNINGAR, [])
        self.assertIn(">&lt;M&gt;</button>", text)
        self.assertNotIn("<M>", text)


class TestOrgannamn(unittest.TestCase):
    def test_organets_forsta_namn(self):
        self.assertEqual(las(EXEMPELBY).organnamn("fsn"), "Förskole- och skolnämnden")

    def test_alla_organens_namn(self):
        namnen = las(EXEMPELBY).organnamnen()
        self.assertEqual(namnen["bun"], "Barn- och ungdomsnämnden")
