"""Krav: K4 i docs/02-KRAV.md, ADR-0014. Test: tests/test_sidmarkor.py.

Markören `<!-- sida N -->` först på varje sida i ett dokuments `.md`
(docs/03-ARKITEKTUR.md#markdown-texten). Den räknas bara som en egen
rad: står den mitt i en rad är den sidans text, som PDF:en skrev den.
"""

import re

SIDA = re.compile(r"^<!-- sida (\d+) -->$", re.MULTILINE)


def markor(nr: int) -> str:
    return f"<!-- sida {nr} -->"


def sidorna(md: str) -> dict[str, str]:
    """Varje sidas text efter sitt nummer; det före första markören hör
    inte till någon sida."""
    delar = SIDA.split(md)
    return dict(zip(delar[1::2], delar[2::2], strict=True))
