"""Krav: K10 i docs/02-KRAV.md, ADR-0013. Påhittade klienter i
tests/test_upptack.py, tests/test_wayback.py och tests/test_hamta.py.

Det anroparna behöver av en klient: upptäckten läser sidor, steg 2 hämtar
filer. `klient.Klient` är båda; testernas påhittade klienter är den ena.
"""

from pathlib import Path
from typing import Protocol


class Lasare(Protocol):
    def text(self, url: str) -> str: ...


class Hamtare(Protocol):
    def fil(self, url: str, mal: Path) -> None: ...
