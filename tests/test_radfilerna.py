"""Krav: K14 i docs/02-KRAV.md. Kod: src/kommunhandlingar/webbplats/radfil.py,
mal.py, spar.py, uppfoljningar.py, kalender.py och projekt.py.

Webbplatsens radfiler stoppar bygget med samma ordalydelse, med fil och
rad: en tom fil, fel rubrikrad, fel antal fält och en dubblett."""

import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path

from kommunhandlingar.fel import Datafel
from kommunhandlingar.webbplats import kalender, mal, projekt, spar, uppfoljningar
from kommunhandlingar.webbplats.slagen import SLAGEN
from tests.test_kalender import kommun as kalenderns_kommun
from tests.test_projekt import kommunen as projektens_kommun
from tests.test_webbplats import exempelby

Lasare = Callable[[Path, Path], object]
LASARNA: dict[str, tuple[list[str], Lasare]] = {
    "mal": (mal.KOLUMNER, lambda fil, data: mal.las(fil, exempelby(), data)),
    "uppfoljningar": (
        uppfoljningar.KOLUMNER,
        lambda fil, data: uppfoljningar.las(fil, exempelby(), data),
    ),
    "kalender": (
        kalender.KOLUMNER,
        lambda fil, data: kalender.las(fil, kalenderns_kommun(), data),
    ),
    "projekt": (
        projekt.KOLUMNER,
        lambda fil, data: projekt.las(fil, projektens_kommun(), data),
    ),
    **{
        slag.id: (
            slag.kolumner,
            lambda fil, data, slag=slag: spar.lasare(slag)(fil, exempelby(), data),
        )
        for slag in SLAGEN
    },
}


def stoppas(lasare: Lasare, text: str) -> tuple[str, Path]:
    with tempfile.TemporaryDirectory() as tmp:
        fil, data = Path(tmp) / "exempelby.csv", Path(tmp) / "data"
        fil.write_text(text, encoding="utf-8")
        try:
            lasare(fil, data)
        except Datafel as fel:
            return str(fel), fil
    raise AssertionError("läsaren stoppade inte")


class TestStommen(unittest.TestCase):
    def test_tom_fil_och_fel_rubrikrad(self):
        for namn, (kolumner, lasare) in LASARNA.items():
            for text in ("", "organ,ar\n", ",".join(reversed(kolumner)) + "\n"):
                with self.subTest(namn, text=text):
                    fel, fil = stoppas(lasare, text)
                    self.assertEqual(
                        fel, f"{fil}: rubrikerna är inte {','.join(kolumner)}"
                    )

    def test_fel_antal_falt_med_radnummer(self):
        for namn, (kolumner, lasare) in LASARNA.items():
            with self.subTest(namn):
                text = ",".join(kolumner) + "\n" + "fsn,x\n"
                fel, fil = stoppas(lasare, text)
                self.assertEqual(fel, f"{fil}, rad 2: 2 fält, inte {len(kolumner)}")

    def test_bara_rubrikraden_ger_inga_rader(self):
        for namn, (kolumner, lasare) in LASARNA.items():
            with self.subTest(namn), tempfile.TemporaryDirectory() as tmp:
                fil = Path(tmp) / "exempelby.csv"
                fil.write_text(",".join(kolumner) + "\n", encoding="utf-8")
                self.assertFalse(lasare(fil, Path(tmp)))


if __name__ == "__main__":
    unittest.main()
