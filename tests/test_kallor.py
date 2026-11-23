"""Krav: K88 i docs/02-KRAV.md, ADR-0109. Kod: src/kommunhandlingar/adaptrar/
kallor.py, upptack.py, arkivupptackt.py och webbplats/luckavsnitt.py."""

import ast
import unittest
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import ClassVar

from kommunhandlingar import arkivupptackt, upptack
from kommunhandlingar.adaptrar import meetingsplus
from kommunhandlingar.adaptrar.kallor import Episerver, MeetingsPlus, Organsida
from kommunhandlingar.kandidat import Avvisad, Fynd, Kandidat
from kommunhandlingar.konfiguration import las
from kommunhandlingar.webbplats import luckavsnitt
from tests.test_konfiguration import FIXTURER, med_kallan
from tests.test_upptack import BUN, Klient


def kandidat(organ: str, dag: int, nyckel: str) -> Kandidat:
    return Kandidat(organ, date(2025, 1, dag), "protokoll", "u", "k", nyckel, "f.pdf")


@dataclass(frozen=True)
class Fjarde:
    """En påhittad plattform: ett organ, två möten och ett arkiv."""

    bakat: ClassVar[bool] = True

    def levande(self, hamta):
        return Fynd(
            [kandidat("bun", 1, "x:1"), kandidat("bun", int(hamta("dag")), "x:2")],
            [Avvisad("x", "y.pdf", "inte en PDF")],
        )

    def arkivet(self, klient):
        return Fynd([kandidat("fsn", 3, "x:3")], noteringar=[klient.text("arkiv")])

    def projektlistor(self):
        return {}

    def organsida(self, organ):
        return Organsida("https://x/" + organ, "organets sida")


class TestEnFjardeAdapter(unittest.TestCase):
    def setUp(self):
        kommun = las(FIXTURER / "exempelby.toml")
        self.kommun = replace(kommun, kallor=(Fjarde(),))
        self.klient = Klient({"dag": "2", "arkiv": "arkivet läst"})

    def test_det_levande_ordnas_efter_kallans_egenskap(self):
        fynd = upptack.upptack(self.kommun, self.klient)
        self.assertEqual([k.kallnyckel for k in fynd.kandidater], ["x:2", "x:1"])
        self.assertEqual(fynd.avvisade, [Avvisad("x", "y.pdf", "inte en PDF")])

    def test_arkivet_lases_med_klienten(self):
        fynd = arkivupptackt.las(self.kommun, self.klient)
        self.assertEqual([k.kallnyckel for k in fynd.kandidater], ["x:3"])
        self.assertEqual(fynd.noteringar, ["arkivet läst"])

    def test_framat_kommer_fore_nyast_forst(self):
        sitevision = las(FIXTURER / "exempelby.toml").kallor[0]
        kommun = replace(self.kommun, kallor=(Fjarde(), sitevision))
        sidor = {"https://exempelby.se/bun": BUN, "https://exempelby.se/fsn": ""}
        fynd = upptack.upptack(kommun, Klient(sidor | {"dag": "2"}))
        nycklar = [k.kallnyckel[-3:] for k in fynd.kandidater]
        self.assertEqual(nycklar, [".b2", ".b1", "x:2", "x:1"])


class TestUpptackKannerIngenAdapter(unittest.TestCase):
    def test_upptacken_importerar_bara_gransnittet(self):
        for modul in (upptack, arkivupptackt):
            with self.subTest(modul.__name__):
                text = Path(modul.__file__).read_text("utf-8")
                importer = [
                    namn.name
                    for nod in ast.walk(ast.parse(text))
                    if isinstance(nod, ast.ImportFrom)
                    and nod.module.startswith("kommunhandlingar.adaptrar")
                    for namn in nod.names
                ]
                self.assertEqual(importer, [])


class TestKallorUtanEnDel(unittest.TestCase):
    def test_utan_levande_eller_arkiv_blir_fyndet_tomt(self):
        episerver = Episerver(None)
        meetingsplus = MeetingsPlus(None)
        self.assertEqual(episerver.levande(None), Fynd())
        self.assertEqual(meetingsplus.arkivet(None), Fynd())
        self.assertEqual(episerver.projektlistor(), {})
        self.assertIsNone(episerver.organsida("bun"))

    def test_sitevision_utan_wayback_fragar_inte_arkivet(self):
        sitevision = las(FIXTURER / "exempelby.toml").kallor[0]
        self.assertEqual(sitevision.arkivet(Klient({})), Fynd())


class TestLuckornasKallor(unittest.TestCase):
    def test_arkivet_ar_en_kalla(self):
        kommun = med_kallan(las(FIXTURER / "exempelby.toml"), wayback=("fsn",))
        self.assertEqual(
            luckavsnitt.kallor(kommun, "fsn"),
            '<a href="https://exempelby.se/fsn">mötessidan</a> och Internet Archive',
        )
        self.assertEqual(
            luckavsnitt.kallor(kommun, "bun"),
            '<a href="https://exempelby.se/bun">mötessidan</a>',
        )

    def test_meetings_plus_ar_en_kalla(self):
        kalla = meetingsplus.Kalla({"bun": "https://mp.exempelby.se/bun"}, (), ())
        kommun = las(FIXTURER / "exempelby.toml")
        kommun = replace(kommun, kallor=(*kommun.kallor, MeetingsPlus(kalla)))
        self.assertEqual(
            luckavsnitt.kallor(kommun, "bun"),
            '<a href="https://exempelby.se/bun">mötessidan</a>, '
            '<a href="https://mp.exempelby.se/bun">organets sida på Meetings Plus</a>',
        )


if __name__ == "__main__":
    unittest.main()
