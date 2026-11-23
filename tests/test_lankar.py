"""Krav: K78. Kod: src/kommunhandlingar/webbplats/adresser.py.

Varje intern länk på varje sida i ögonblicksbilden av webbplatsen
(tests/fixtures/webbplats/ogonblicksbild/) pekar på en fil som finns där.
En länk är intern när den är relativ till sidan; adresser med schema och
de som börjar med `/` eller `#` lämnas.
"""

import posixpath
import unittest
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

from tests.test_webbplatsbild import BILD


class Lankar(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.adresser: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.adresser += [v for k, v in attrs if k in ("href", "src") and v]


def interna(html: str) -> list[str]:
    lasare = Lankar()
    lasare.feed(html)
    delar = [urlsplit(a) for a in lasare.adresser]
    return [
        unquote(d.path)
        for d in delar
        if not d.scheme and not d.netloc and d.path and not d.path.startswith("/")
    ]


class InternaLankar(unittest.TestCase):
    def test_sidorna_har_lankar(self):
        sidor = list(BILD.rglob("*.html"))
        self.assertTrue(sidor)
        self.assertTrue(any(interna(s.read_text(encoding="utf-8")) for s in sidor))

    def test_varje_intern_lank_pekar_pa_en_fil(self):
        for sida in sorted(BILD.rglob("*.html")):
            adress = sida.relative_to(BILD).as_posix()
            for lank in interna(sida.read_text(encoding="utf-8")):
                mal = posixpath.normpath(
                    posixpath.join(posixpath.dirname(adress), lank)
                )
                with self.subTest(sida=adress, lank=lank):
                    self.assertFalse(mal.startswith(".."))
                    self.assertTrue((BILD / mal).is_file())


if __name__ == "__main__":
    unittest.main()
