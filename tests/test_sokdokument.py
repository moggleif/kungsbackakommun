"""Krav: K96, ADR-0119. Kod: src/kommunhandlingar/webbplats/sokdokument.py."""

import json

from kommunhandlingar.webbplats import sokdokument
from tests.test_dokumentindex import Index
from tests.test_webbplats import dokument


class TestSokdokument(Index):
    def dokumentgrupp(self) -> dict:
        self.index()
        sok = json.loads((self.ut / "sok.json").read_text(encoding="utf-8"))
        return sok["grupper"][1]

    def test_varje_dokument_nyast_forst_efter_protokollen(self):
        self.spara("kallelse.md", dokument(typ="kallelse"))
        nyare = self.rot / "data" / "exempelby" / "fsn" / "2025" / "2025-01-15"
        nyare.mkdir(parents=True)
        (nyare / "handlingar.md").write_text(
            dokument(datum="2025-01-15", typ="handlingar"), encoding="utf-8"
        )
        grupp = self.dokumentgrupp()
        self.assertEqual(grupp["rubrik"], "Dokumenten i Exempelby kommun")
        self.assertEqual(
            grupp["poster"][1],
            {
                "rubrik": "Kallelse",
                "adress": "exempelby/fsn/2024/2024-05-02/kallelse.html",
                "om": ["Förskole- och skolnämnden", "2 maj 2024", "kvalitet full"],
                "traff": "kallelse",
                "text": "förskole- och skolnämnden 2 maj 2024",
            },
        )
        self.assertEqual(grupp["poster"][0]["rubrik"], "Handlingar")

    def test_obekraftade_tal_och_osakra_tabeller_raknas(self):
        falt = {
            "organ": "fsn",
            "datum": "2024-05-02",
            "typ": "handlingar",
            "namn": "null",
            "adress": "x.html",
            "kvalitet": "ocr",
            "tal_obekraftade": "[2, 3]",
            "kvalitet_per_sida": "[ok, tabell-osaker, ocr]",
        }
        self.assertEqual(
            sokdokument.post(falt, "Förskole- och skolnämnden", "exempelby")["om"][2:],
            [
                "kvalitet ocr",
                "obekräftade tal på 2 sidor",
                "osäkra tabeller på 1 sida",
            ],
        )

    def test_namnets_bindestreck_ar_mellanslag_i_det_som_soks(self):
        falt = {
            "organ": "bun",
            "datum": "2024-05-02",
            "typ": "detaljplan",
            "namn": "skolan-i-exempelby-plankarta",
            "adress": "x.html",
            "kvalitet": "full",
            "tal_obekraftade": "[]",
            "kvalitet_per_sida": "[ok]",
        }
        post = sokdokument.post(falt, "Barn- och ungdomsnämnden", "exempelby")
        self.assertEqual(post["rubrik"], "Detaljplan – skolan-i-exempelby-plankarta")
        self.assertEqual(post["traff"], "detaljplan – skolan i exempelby plankarta")
