"""Krav: K22 och K32 i docs/02-KRAV.md, ADR-0032 och ADR-0053. Kod:
src/kommunhandlingar/webbplats/kalenderkvalitet.py."""

import unittest

from kommunhandlingar.webbplats.kalendersida import kalendersida
from kommunhandlingar.webbplats.mall import Mall
from tests.kalenderfall import (
    KALLELSE,
    NASTA,
    PROTOKOLL,
    RADER,
    REPO,
    TID,
    kommun,
    pool,
)


class TestKvalitet(unittest.TestCase):
    def setUp(self):
        with pool() as sammantraden:
            self.html = kalendersida(
                Mall([kommun()], REPO, TID), kommun(), sammantraden
            )

    def test_inga_osakra(self):
        with pool(f"fsn,2027-01-14,,,{PROTOKOLL},\n") as sammantraden:
            html = kalendersida(Mall([kommun()], REPO, TID), kommun(), sammantraden)
        self.assertIn("Kvalitet: 0 av 1 datum är osäkra", html)
        self.assertIn('<h2 id="osakra">Osäkra datum</h2><p>Inga.</p>', html)

    def test_kallorna_per_organ_och_ar_under_kvalitet(self):
        kvalitet = self.html.split('<details id="kvalitet">')[1].split("</details>")[0]
        kallor = kvalitet.split('<h2 id="kallor">Källor</h2>')[1]
        self.assertIn('<th scope="col">2026</th><th scope="col">2027</th>', kallor)
        self.assertIn(
            '<td><a href="https://exempelby.se/bun">exempelby.se</a></td><td></td>',
            kallor,
        )
        self.assertEqual(kallor.count("protokoll.html"), 2)
        self.assertIn('<th scope="row">Arbetsutskottet</th>', kallor)

    def test_samma_kalla_en_gang_per_organ_och_ar(self):
        with pool(RADER + f"fsn,2027-02-11,,,{PROTOKOLL},\n") as sammantraden:
            html = kalendersida(Mall([kommun()], REPO, TID), kommun(), sammantraden)
        self.assertEqual(html.split('id="kallor"')[1].count("protokoll.html"), 2)
        lista = self.html.split("<h2>Lista</h2>")[1].split("<script>")[0]
        self.assertNotIn("<a href", lista.replace('<a href="#osakra"', ""))

    def test_sammantraden_med_egna_dokument_raknas(self):
        rader = f"fsn,2026-09-17,,,{PROTOKOLL},\nfsn,2026-09-24,,,{NASTA},\n"
        with pool(rader + f"fsn,2026-10-01,,,{KALLELSE},\n") as sammantraden:
            html = kalendersida(Mall([kommun()], REPO, TID), kommun(), sammantraden)
        kallor = html.split('id="kallor"')[1]
        self.assertIn(
            '<td><a href="fsn/2026/2026-09-17/kallelse.html">FSN 2026-09-17, '
            'kallelse</a><br><a href="fsn.html">2 sammanträden i poolen</a></td>',
            kallor,
        )
        self.assertNotIn("protokoll.html", kallor)
