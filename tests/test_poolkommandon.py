"""Krav: K81 i docs/02-KRAV.md, med K17, K48 och K73.
Kod: src/kommunhandlingar/kand_inlasning.py, arenden.py, maska_poolen.py,
datakontroll.py och kommando.py.

Poolens kommandon körs som moduler, med `sys.argv` som på kommandoraden,
mot en pool i en temporär katalog. Alla nummer här är påhittade.
"""

import unittest
from itertools import product

from kommunhandlingar import frontmatter
from tests.kommandofall import Katalogfall, kor_modulen
from tests.test_kand_inlasning import dokument

PROTOKOLL = "§ 4 Dnr KS-2025-00001\nSökanden 121212-1212\n"


class TestPoolensKommandon(Katalogfall):
    def test_kand_inlasning_skriver_en_rad_per_kommun_i_ordning(self):
        dokument(self.rot / "ostby" / "ks", "a", "[ok]")
        dokument(self.rot / "exempelby" / "kf", "b", "[ok, ej-konverterad]")
        (self.rot / "README.md").write_text("ingen kommun", encoding="utf-8")
        kod, utskrift = kor_modulen("kand_inlasning", str(self.rot))
        rader = utskrift.splitlines()
        self.assertIsNone(kod)
        self.assertEqual([r.split(":")[0] for r in rader], ["exempelby", "ostby"])
        self.assertTrue(rader[0].startswith("exempelby: 1 av 2 sidor"))

    def test_arenden_och_maska_poolen_raknar_det_som_andrades(self):
        md = self.rot / "exempelby/ks/2025/2025-04-22/protokoll.md"
        md.parent.mkdir(parents=True)
        falt = dict.fromkeys(frontmatter.FALT, "null") | {"typ": "protokoll"}
        md.write_text(frontmatter.skriv(falt) + PROTOKOLL, encoding="utf-8")
        utfall = [
            ("arenden", "1 dokument fick nya ärenden.\n"),
            ("maska_poolen", "1 filer maskades.\n"),
        ]
        for modul, rad in utfall:
            with self.subTest(modul):
                self.assertEqual(kor_modulen(modul, str(self.rot)), (None, rad))

    def test_fel_antal_argument_ger_anvandningstexten(self):
        moduler = ("kand_inlasning", "arenden", "maska_poolen", "datakontroll")
        for modul, argument in product(moduler, ((), ("a", "b"))):
            with self.subTest(modul, argument=argument):
                anvandning = f"Användning: python -m kommunhandlingar.{modul} <data>"
                self.assertEqual(kor_modulen(modul, *argument), (anvandning, ""))


if __name__ == "__main__":
    unittest.main()
