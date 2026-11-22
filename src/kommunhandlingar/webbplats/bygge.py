"""Krav: K14 i docs/02-KRAV.md. Test: tests/test_webbplats.py.

Ett webbplatsbygge: utkatalogen, mallen som sidorna skrivs med och
kommunernas underlag. Katalogen för sidan ska finnas. Indexen och
sammanträdenas sidor skrivs av sina egna moduler direkt i utkatalogen.
"""

from dataclasses import dataclass
from pathlib import Path

from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats.mall import Mall
from kommunhandlingar.webbplats.sammanhang import Kommununderlag, Sammanhang


@dataclass(frozen=True)
class Bygge:
    ut: Path
    mall: Mall
    # Med kommunens id som nyckel.
    underlagen: dict[str, Kommununderlag]

    def sammanhang(self, kommun: Kommun) -> Sammanhang:
        return Sammanhang(self.mall, kommun, self.underlagen[kommun.id])

    def skriv(self, adress: str, html: str) -> Path:
        fil = self.ut / adress
        fil.write_text(html, encoding="utf-8")
        return fil
