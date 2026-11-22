"""Krav: K6, K15 och K19 i docs/02-KRAV.md, ADR-0017 och ADR-0099.
Test: tests/test_konvertering.py.

En läst sida: dess kvalitet, text, tabeller, figur och skarv.
"""

from dataclasses import dataclass, field

from kommunhandlingar.konvertering.skarv import Skarv


@dataclass(frozen=True)
class Sida:
    kvalitet: str
    tal_obekraftade: bool
    text: str = ""
    tabeller: list[list[list[str]]] = field(default_factory=list)
    figur: bool = False
    skarv: Skarv | None = None
