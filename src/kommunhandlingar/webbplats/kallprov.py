"""Krav: K26, K28 och K36–K38 i docs/02-KRAV.md, ADR-0021 och ADR-0056.
Test: tests/test_kallprov.py.

Prövar att ett värde ur en radfil står på källans sida i ett dokument i
poolen: målen, spåren och uppföljningarna gör det på samma sätt.
"""

import re
from collections.abc import Callable
from functools import cache
from pathlib import Path

from kommunhandlingar.konvertering.markdown import utan_escapning
from kommunhandlingar.sidmarkor import sidorna

# Ett dokument ligger på <organ>/<år>/<datum>/<namn>.md (ADR-0003). Ett
# värde som fortsätter på nästa sida har sidorna, till exempel `#sida-14-15`.
KALLA = re.compile(
    r"(?P<dokument>(?P<organ>[^/]+)/\d{4}/[^/]+/[^/]+\.md)"
    r"#sida-(?P<forsta>\d+)(?:-(?P<sista>\d+))?"
)
PUNKT = re.compile(r"^[ \t]*[-•*][ \t]*", re.MULTILINE)
# Mellanrum, mjuka bindestreck, ett ord delat i en tabellcell och
# trendkolumnens pilar och tankstreck, som hamnar mitt i texten (ADR-0056).
UTFYLLNAD = re.compile(r"-<br>|<br>|[\s­–—←-⇿-]")

Sidtext = Callable[[str, str], str]


class Sidlasare:
    """Ger källans sidor som prövbar text och läser varje dokument en gång."""

    def __init__(self, data: Path) -> None:
        self.data = data
        self.sidor = cache(las_sidor)

    def __call__(self, kalla: str, organ: str) -> str:
        traff = KALLA.fullmatch(kalla)
        if not traff or traff["organ"] != organ:
            raise ValueError(f"källan {kalla!r} är ingen sida i organets dokument")
        fil = self.data / traff["dokument"]
        if not fil.is_file():
            raise ValueError(f"källan {kalla!r} är inget dokument i poolen")
        dokumentet, nr = self.sidor(fil), sidnummer(traff)
        if not nr or any(n not in dokumentet for n in nr):
            raise ValueError(f"källan {kalla!r} är ingen sida i dokumentet")
        return "".join(dokumentet[n] for n in nr)


def sidnummer(traff: re.Match) -> list[str]:
    forsta = int(traff["forsta"])
    sista = int(traff["sista"] or forsta)
    return [str(n) for n in range(forsta, sista + 1)]


def las_sidor(fil: Path) -> dict[str, str]:
    sidor = sidorna(fil.read_text(encoding="utf-8"))
    return {nr: provbar(text) for nr, text in sidor.items()}


# Versalerna räknas, utom när källan sätter hela texten i versaler.
def star_pa(text: str, sida: str) -> bool:
    provad = provbar(text)
    return provad in sida or provad.upper() in sida


# Radbrytningarna ur PDF:en, punkterna först i en rad och
# Markdown-escapningen (ADR-0021) räknas inte.
def jamforbar(text: str) -> str:
    return " ".join(PUNKT.sub("", utan_escapning(text)).split())


def provbar(text: str) -> str:
    return UTFYLLNAD.sub("", jamforbar(text))
