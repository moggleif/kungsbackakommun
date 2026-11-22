"""Krav: K59 i docs/02-KRAV.md, ADR-0085. Kod: src/kommunhandlingar/webbplats/
investeringsslag.py, remissslag.py, overenskommelseslag.py och slagen.py."""

import unittest

from kommunhandlingar.fel import Datafel
from kommunhandlingar.webbplats import spar
from kommunhandlingar.webbplats.flikar import flikar
from kommunhandlingar.webbplats.investeringsslag import INVESTERINGAR
from kommunhandlingar.webbplats.overenskommelseslag import OVERENSKOMMELSER
from kommunhandlingar.webbplats.remissslag import REMISSER
from kommunhandlingar.webbplats.sparkort import Vy
from kommunhandlingar.webbplats.sparsida import sparsida
from tests.aren import aren
from tests.poolfall import dokumenten, mall, tillfallig_pool
from tests.test_webbplats import exempelby

PROTOKOLL = "fsn/2025/2025-10-27/protokoll.md"
TEXT = (
    "<!-- sida 1 -->\n\nRemiss om god och nära vård\n\n"
    "Nya lokaler för vårdcentralen\n\nÖverenskommelse om hemsjukvård\n"
)
FALL = (
    (
        INVESTERINGAR,
        "Vårdcentralens lokaler",
        "beslut",
        "Nya lokaler för vårdcentralen",
    ),
    (REMISSER, "God och nära vård", "yttrande", "Remiss om god och nära vård"),
    (OVERENSKOMMELSER, "Hemsjukvård", "revidering", "Överenskommelse om hemsjukvård"),
)


def las(slag: spar.Slag, rad: str) -> list[spar.Steg]:
    rubrik, texter = ",".join(slag.kolumner) + "\n", {PROTOKOLL: TEXT}
    with tillfallig_pool(rubrik, rad, dokumenten(texter, "[ok]")) as (fil, data):
        return spar.lasare(slag)(fil, exempelby(), data)


def rad(namn: str, fas: str, text: str) -> str:
    return f"fsn,{namn},2025,{fas},,{text},{PROTOKOLL}#sida-1,\n"


class TestSidorna(unittest.TestCase):
    def test_varje_nytt_slag_far_en_sida_och_en_flik(self):
        for slag, namn, fas, text in FALL:
            with self.subTest(slag.id):
                stegen = las(slag, rad(namn, fas, text))
                vy = Vy(slag, exempelby(), aren(stegen)["exempelby"])
                html = sparsida(mall(), vy, stegen)
                self.assertIn(f">{namn}</a></th>", html)
                self.assertIn(f"<dt>{slag.faser[fas][1]}</dt><dd>1</dd>", html)
                vald = mall(spar={slag.id: {"exempelby": stegen}})
                nav = flikar(vald, "exempelby", "fsn", slag.id)
                self.assertIn(f'aria-current="page">{slag.rubrik}<', nav)

    def test_en_okand_fas_stoppar(self):
        for slag, namn, _, text in FALL:
            with self.subTest(slag.id), self.assertRaisesRegex(Datafel, "rad 2: fasen"):
                las(slag, rad(namn, "vackt", text))
