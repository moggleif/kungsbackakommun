"""Krav: K5 och K19 i docs/02-KRAV.md, ADR-0016 och ADR-0028.
Test: tests/test_konvertering.py, tests/test_olinjerade.py och
tests/test_skarvar.py.

En tabell som hittats på sidan, med eller utan linjer.
"""

from dataclasses import dataclass

from kommunhandlingar.konvertering.geometri import Ruta


@dataclass(frozen=True)
class Funnen:
    ruta: Ruta
    rader: list[list[str]]
    # Kolumngränserna, som skarven jämför med grannsidornas (K19); hur
    # de mäts står där tabellen läses.
    kanter: tuple[float, ...]
