"""Krav: K14 i docs/02-KRAV.md. Test: tests/test_webbplats.py.

Ett webbplatsbygge: utkatalogen och mallen som alla sidor skrivs med.
"""

from dataclasses import dataclass
from pathlib import Path

from kommunhandlingar.webbplats.mall import Mall


@dataclass(frozen=True)
class Bygge:
    ut: Path
    mall: Mall

    def skriv(self, adress: str, html: str) -> Path:
        fil = self.ut / adress
        fil.parent.mkdir(parents=True, exist_ok=True)
        fil.write_text(html, encoding="utf-8")
        return fil
