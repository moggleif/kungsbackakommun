"""Krav: K22 i docs/02-KRAV.md, ADR-0032. Kod: src/kommunhandlingar/webbplats/
kalenderfarger.py, kalendervyer.py och kalendersida.py. Filen prövas i
tests/test_kalenderfil.py och kvalitetsavsnittet i tests/test_kalenderkvalitet.py."""

import re
import shutil
import tempfile
import unittest
from pathlib import Path

from kommunhandlingar.fel import Datafel
from kommunhandlingar.webbplats.bygg import bygg
from kommunhandlingar.webbplats.kalenderfarger import farger
from kommunhandlingar.webbplats.kalendersida import kalendersida
from kommunhandlingar.webbplats.mall import Mall
from tests.kalenderfall import (
    FIXTURER,
    PROTOKOLL,
    RADER,
    REPO,
    RUBRIK,
    TID,
    kommun,
    pool,
)


class TestFarger(unittest.TestCase):
    def test_utskottet_far_namndens_farg_ljusare(self):
        farg = farger(kommun(), {"bun", "fsn", "fsn-au"})
        ton = {o: re.findall(r"hsl\((\d+) \d+% (\d+)%\)", farg[o][0])[0] for o in farg}
        self.assertEqual(ton["fsn"][0], ton["fsn-au"][0])
        self.assertGreater(int(ton["fsn-au"][1]), int(ton["fsn"][1]))
        self.assertEqual(farg["fsn"][1], farg["fsn-au"][1])
        self.assertNotEqual(ton["bun"][0], ton["fsn"][0])

    def test_bara_organ_i_kalendern(self):
        self.assertEqual(list(farger(kommun(), {"fsn"})), ["fsn"])


class TestSidan(unittest.TestCase):
    def setUp(self):
        with pool() as sammantraden:
            self.html = kalendersida(
                Mall([kommun()], REPO, TID), kommun(), sammantraden
            )

    def test_en_ruta_per_sammantrade_med_forkortning(self):
        self.assertIn('data-organ="fsn-au">FSN-AU</span>', self.html)

    def test_osakert_markt_i_vyerna_och_skalet_under_kvalitet(self):
        self.assertIn("ruta o-bun osakert", self.html)
        self.assertIn(">BUN ?</span>", self.html)
        self.assertIn(
            '2026-12-05<br><a href="#osakra" '
            'title="Källan säger lördag &lt;5 dec&gt;.">osäkert</a>',
            self.html,
        )
        kvalitet = self.html.split('<details id="kvalitet">')[1].split("</details>")[0]
        self.assertIn("Kvalitet: 1 av 3 datum är osäkra", kvalitet)
        self.assertIn("<td>Källan säger lördag &lt;5 dec&gt;.</td>", kvalitet)
        self.assertIn("Datumen är lästa ur", kvalitet)
        self.assertIn(">ADR-0032</a> och <a", kvalitet)
        self.assertIn("0053-tidigare-sammantraden-las-ur-poolens-mappar.md", kvalitet)

    def test_alla_manader_och_rader_star_i_sidan(self):
        self.assertIn('data-manad="2026-12"', self.html)
        self.assertIn('data-manad="2027-01"', self.html)
        self.assertEqual(self.html.count('class="manad"'), 2)
        self.assertEqual(self.html.count("<tr data-organ="), 3)

    def test_knapp_for_tidigare_sammantraden_i_listan(self):
        lista = self.html.split("<h2>Lista</h2>")[1]
        self.assertTrue(
            lista.startswith(
                '<p class="tidigare" hidden><button type="button" '
                'aria-expanded="false">Visa tidigare sammanträden</button></p>'
            )
        )

    def test_knapp_for_alla_organ_i_urvalet(self):
        urval = self.html.split('<fieldset class="urval">')[1]
        self.assertTrue(
            urval.startswith(
                '<legend>Organ som visas</legend><p class="alla" hidden>'
                '<button type="button">Dölj alla</button></p>'
            )
        )

    def test_tid_i_listan_platsen_i_rutan(self):
        self.assertIn("<td>17:00</td></tr>", self.html)
        self.assertIn('title="Stadshuset">FSN 17:00</span>', self.html)
        self.assertNotIn("<td>Stadshuset</td>", self.html)
        self.assertEqual(self.html.count('type="checkbox" checked'), 3)
        self.assertIn("<script>", self.html)

    def test_manad_utan_sammantraden_far_en_tabell(self):
        with pool(f"fsn,2027-03-10,,,{PROTOKOLL},\n" + RADER) as sammantraden:
            html = kalendersida(Mall([kommun()], REPO, TID), kommun(), sammantraden)
        self.assertIn('data-manad="2027-02"', html)
        self.assertEqual(html.count('class="manad"'), 4)


class TestBygg(unittest.TestCase):
    def bygg(self, med_kalender: bool, namn: str = "exempelby") -> Path:
        tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        rot, ut = tmp / "repo", tmp / "ut"
        (rot / "kommuner").mkdir(parents=True)
        shutil.copy(FIXTURER / "exempelby.toml", rot / "kommuner")
        if med_kalender:
            (rot / "kalender").mkdir()
            rad = "bun,2026-12-07,,,https://exempelby.se/bun,\n"
            (rot / "kalender" / f"{namn}.csv").write_text(RUBRIK + rad)
        bygg(rot, ut, REPO, TID)
        return ut

    def test_kalendern_byggs_och_lankas_fran_menyn(self):
        ut = self.bygg(med_kalender=True)
        self.assertIn("BUN", (ut / "exempelby" / "kalender.html").read_text())
        self.assertIn(
            'href="exempelby/kalender.html"', (ut / "exempelby.html").read_text()
        )

    def test_kalenderfil_utan_kommunfil_stoppar_bygget(self):
        with self.assertRaises(Datafel):
            self.bygg(med_kalender=True, namn="exempelbyn")

    def test_utan_kalenderfil_ingen_sida(self):
        ut = self.bygg(med_kalender=False)
        self.assertFalse((ut / "exempelby" / "kalender.html").exists())
        self.assertNotIn("kalender.html", (ut / "exempelby.html").read_text())
