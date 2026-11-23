"""Krav: K78. Kod: src/kommunhandlingar/webbplats/.

Webbplatsen byggs som `python -m kommunhandlingar.webbplats` bygger den,
ur poolen i tests/fixtures/webbplats/pool/ och med en fast byggtid, och
varje fil i utkatalogen jämförs tecken för tecken med ögonblicksbilden i
tests/fixtures/webbplats/ogonblicksbild/. Bilden skrivs om med
`python3 -m tests.test_webbplatsbild --spara`.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from kommunhandlingar.webbplats import adresser, avvikelser
from kommunhandlingar.webbplats.avvikelsesida import avvikelsesida
from kommunhandlingar.webbplats.bygg import bygg
from tests.test_webbplats import REPO, TID

KATALOG = Path(__file__).parent / "fixtures" / "webbplats"
POOL = KATALOG / "pool"
BILD = KATALOG / "ogonblicksbild"


def bygg_webbplatsen(ut: Path) -> None:
    """Som webbplatsens `__main__`, men med testets byggtid."""
    mall = bygg(POOL, ut, REPO, TID)
    html = avvikelsesida(mall, avvikelser.las(POOL / "avvikelser.jsonl"))
    (ut / adresser.AVVIKELSER).write_text(html, encoding="utf-8")


def filer(katalog: Path) -> dict[str, str]:
    """Varje fil som den står, utan att `\\r` blir radbrytning."""
    return {
        fil.relative_to(katalog).as_posix(): fil.read_bytes().decode("utf-8")
        for fil in sorted(katalog.rglob("*"))
        if fil.is_file()
    }


class Webbplatsbild(unittest.TestCase):
    maxDiff = None

    def test_varje_fil_ar_som_i_bilden(self):
        with tempfile.TemporaryDirectory() as tmp:
            bygg_webbplatsen(Path(tmp))
            byggda = filer(Path(tmp))
        sparade = filer(BILD)
        self.assertEqual(list(byggda), list(sparade))
        for namn, text in byggda.items():
            with self.subTest(namn):
                self.assertEqual(text, sparade[namn])


def spara() -> None:
    if BILD.exists():
        shutil.rmtree(BILD)
    bygg_webbplatsen(BILD)


if __name__ == "__main__":
    if sys.argv[1:] == ["--spara"]:
        spara()
    else:
        unittest.main()
