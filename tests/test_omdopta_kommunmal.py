"""Krav: K91 i docs/02-KRAV.md, ADR-0114. Kod:
src/kommunhandlingar/webbplats/mal.py, malkontroll.py och malspar.py."""

import unittest
from contextlib import contextmanager

from kommunhandlingar.fel import Datafel
from kommunhandlingar.webbplats import mal
from kommunhandlingar.webbplats.malsida import malsida
from tests.aren import aren
from tests.poolfall import sammanhang, tillfallig_pool
from tests.test_mal import RUBRIK
from tests.test_webbplats import dokument, exempelby, protokoll

BUDGET = "fsn/2018/2018-06-14/handlingar.md"
AR = "fsn/2019/2019-04-09/handlingar.md"
# Budgeten skriver kommunmålet utan "en", årsredovisningen med.
TEXTER = {
    BUDGET: "<!-- sida 1 -->\n\nETT MEDSKAPANDE SAMHÄLLE OCH ÖPPEN ATTITYD\n\n"
    "Fokusområden:\n• Digitaliseringen gör oss smartare.\n",
    AR: "<!-- sida 1 -->\n\nEtt medskapande samhälle och en öppen attityd\n\n"
    "| Digitaliseringen gör oss smartare. | → |\n",
}
GAMLA = "Ett medskapande samhälle och öppen attityd"
NYA = "Ett medskapande samhälle och en öppen attityd"
FOKUS = "Digitaliseringen gör oss smartare."
RADER = (
    f"fsn,2018,fokusområde,{FOKUS},,,,,{BUDGET}#sida-1,,,{GAMLA}\n"
    f"fsn,2018,kommunmål,{GAMLA},,,,,{BUDGET}#sida-1,{NYA},,\n"
    f"fsn,2018,fokusområde,{FOKUS},,,utfall,uppnatt,{AR}#sida-1,,,{NYA}\n"
    f"fsn,2018,kommunmål,{NYA},,,,,{AR}#sida-1,,,\n"
)


@contextmanager
def pool(rader: str = RADER):
    texter = {k: dokument(text=t, typ="handlingar") for k, t in TEXTER.items()}
    with tillfallig_pool(RUBRIK, rader, texter) as (fil, data):
        yield mal.las(fil, exempelby(), data)


class TestOmdoptKommunmal(unittest.TestCase):
    def stoppas(self, rader: str) -> str:
        with self.assertRaises(Datafel) as fel, pool(rader):
            pass
        return str(fel.exception)

    def test_fokusomradet_star_under_det_omdopta_malets_spar(self):
        with pool() as malen:
            self.assertEqual({m.huvudmal for m in malen if m.huvudmal}, {NYA})

    def test_samma_fokusomrade_under_tva_spar_stoppas(self):
        rader = RADER.replace(f",{NYA},,\n", ",,,\n")
        self.assertIn("huvudmål tidigare", self.stoppas(rader))

    def test_huvudmal_som_inte_ar_ett_kommunmal_stoppas(self):
        rader = RADER.replace(f"kommunmål,{GAMLA}", f"nämndmål,{GAMLA}")
        self.assertIn("inget kommunmål", self.stoppas(rader))

    def test_huvudmal_i_ett_namndmals_grupp_stoppas(self):
        rader = RADER.replace(f"kommunmål,{NYA}", f"nämndmål,{NYA}")
        self.assertIn("inget kommunmål", self.stoppas(rader))

    def test_samma_fokusomradesspar_under_tva_spar_stoppas(self):
        andra = "Digitaliseringen gör oss smartare"
        rader = RADER.replace(
            f"{FOKUS},,,utfall,uppnatt,{AR}#sida-1,,,{NYA}",
            f"{andra},,,utfall,uppnatt,{AR}#sida-1,{FOKUS},,{NYA}",
        ).replace(f",{NYA},,\n", ",,,\n")
        self.assertIn("huvudmål tidigare", self.stoppas(rader))

    def test_kortet_har_fokusomradet_inuti_malets_kort(self):
        korten = self.sida().split('<section data-vy="kort">')[1]
        fokus = korten.split('<div class="fokusomraden">')[1]
        self.assertIn(FOKUS, fokus)
        self.assertEqual(korten.count('<div class="fokusomraden">'), 1)

    def sida(self) -> str:
        with pool() as malen:
            return malsida(sammanhang(aren=aren(malen)), malen, protokoll(2018, 2019))

    def test_tidslinjen_har_fokusomradet_under_malet(self):
        efter = self.sida().split('<section data-vy="tidslinje">')[1]
        tidslinje = efter.split("</section>")[0]
        self.assertEqual(tidslinje.count('<th scope="row" class="fokus">'), 1)
        self.assertLess(tidslinje.index(NYA), tidslinje.index(FOKUS))
