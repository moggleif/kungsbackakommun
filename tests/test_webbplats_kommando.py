"""Krav: K82 i docs/02-KRAV.md, med K14 och K33.
Kod: src/kommunhandlingar/webbplats/__main__.py.

Kommandot körs som modul, med `sys.argv` som på kommandoraden, i en
temporär arbetskatalog med kommunfilen ur webbplatsens fixturpool.
"""

import contextlib
import importlib
import shutil
import sys
from unittest import mock

from tests.kommandofall import Katalogfall, kor_modulen
from tests.test_webbplats import REPO
from tests.test_webbplatsbild import POOL


class Webbplatskommandot(Katalogfall):
    def setUp(self):
        super().setUp()
        (self.rot / "kommuner").mkdir()
        shutil.copy(POOL / "kommuner" / "exempelby.toml", self.rot / "kommuner")
        (self.rot / "avvikelser.jsonl").touch()
        self.enterContext(contextlib.chdir(self.rot))

    def test_importen_bygger_ingenting(self):
        # Med testkörarens argv kunde den gamla modulen ha byggt.
        sys.modules.pop("kommunhandlingar.webbplats.__main__", None)
        with mock.patch.object(sys, "argv", ["webbplats"]):
            importlib.import_module("kommunhandlingar.webbplats.__main__")
        self.assertEqual(
            sorted(p.name for p in self.rot.iterdir()), ["avvikelser.jsonl", "kommuner"]
        )

    def test_bygger_oversikten_och_avvikelserna_som_ett_datarepo_kor_det(self):
        kod, _ = kor_modulen("webbplats", "_site", REPO, "avvikelser.jsonl")
        self.assertIsNone(kod)
        oversikten = (self.rot / "_site" / "index.html").read_text(encoding="utf-8")
        self.assertIn(REPO, oversikten)
        self.assertTrue((self.rot / "_site" / "avvikelser.html").is_file())

    def test_fel_antal_argument_ger_anvandningstexten(self):
        kod, _ = kor_modulen("webbplats", "_site", REPO)
        self.assertIn("Användning: python -m kommunhandlingar.webbplats", kod)
