"""Krav: K44 i docs/02-KRAV.md, ADR-0067. Kod: src/kommunhandlingar/webbplats/
sparslag.py."""

import unittest
from dataclasses import replace

from kommunhandlingar.konfiguration import las as las_kommun
from kommunhandlingar.webbplats import spar
from kommunhandlingar.webbplats.sparkort import Vy
from kommunhandlingar.webbplats.sparsida import sparsida
from kommunhandlingar.webbplats.sparslag import DETALJPLANER
from tests.aren import aren
from tests.test_mal import ROT
from tests.test_webbplats import exempelby
from tests.testpool import dokumenten, mall, testpool

RUBRIK = "organ,detaljplan,ar,fas,varde,text,kalla,tolkad\n"
NAMND = "bun/2024/2024-03-14/protokoll.md"
BESLUT = "fsn/2025/2025-02-11/protokoll.md"
TEXTER = {
    NAMND: "<!-- sida 1 -->\n\nSamråd av detaljplan för Skolan 1:2\n",
    BESLUT: "<!-- sida 1 -->\n\nAntagande av detaljplan för Skolan 1:2\n",
}
PLAN = "bun,Skola inom Skolan 1:2"
RADER = (
    f"{PLAN},2024,samrad,,Samråd av detaljplan för Skolan 1:2,{NAMND}#sida-1,\n"
    f"{PLAN},2025,antagande,,Antagande av detaljplan för Skolan 1:2,"
    f"{BESLUT}#sida-1,\n"
)


def sida(projekten: dict | None = None) -> str:
    with testpool(RUBRIK, RADER, dokumenten(TEXTER, "[ok]")) as (fil, data):
        stegen = spar.las(fil, exempelby(), data, DETALJPLANER)
    vy = replace(
        Vy(DETALJPLANER, exempelby(), aren(stegen)["exempelby"]),
        projekt=projekten or {},
    )
    return sparsida(mall(), vy, stegen)


class TestSidan(unittest.TestCase):
    def test_planen_foljs_till_ett_annat_organs_beslut(self):
        html = sida()
        self.assertIn(">Skola inom Skolan 1:2</a></th>", html)
        self.assertIn("<dt>samråd</dt><dd>1</dd>", html)
        self.assertIn("<dt>antagen</dt><dd>1</dd>", html)
        self.assertIn(BESLUT.removesuffix(".md"), html)


class TestKungsbacka(unittest.TestCase):
    def test_filen_gar_ihop_med_kommunfilen_och_poolen(self):
        kungsbacka = las_kommun(ROT / "kommuner" / "kungsbacka.toml")
        fil = ROT / "detaljplaner" / "kungsbacka.csv"
        stegen = spar.las(fil, kungsbacka, ROT / "data" / "kungsbacka", DETALJPLANER)
        self.assertEqual({s.organ for s in stegen}, {"bygg"})
        self.assertEqual(fil.read_bytes().count(b"\r"), 0)
