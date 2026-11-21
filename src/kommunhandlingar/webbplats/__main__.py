"""Krav: K14, K33 och K82 i docs/02-KRAV.md. Test:
tests/test_webbplats_kommando.py. Bygger webbplatsen:
<utkatalog> <repoadress> <avvikelsefil>, där repoadressen är repot med
poolens data och issues och avvikelsefilen har de öppna avvikelserna i
källan, ett issue per rad (ADR-0054). Poolen läses ur arbetskatalogen.
Dokumentationen länkas alltid i kommunhandlingar (`KALLKOD`).
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

from kommunhandlingar.webbplats import avvikelser
from kommunhandlingar.webbplats.avvikelsesida import avvikelsesida
from kommunhandlingar.webbplats.bygg import bygg


def main(ut: Path, repo: str, avvikelsefil: Path) -> None:
    mall = bygg(Path.cwd(), ut, repo, datetime.now(UTC))
    html = avvikelsesida(mall, avvikelser.las(avvikelsefil))
    (ut / avvikelser.ADRESS).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(
            "Användning: python -m kommunhandlingar.webbplats"
            " <utkatalog> <repoadress> <avvikelsefil>"
        )
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
