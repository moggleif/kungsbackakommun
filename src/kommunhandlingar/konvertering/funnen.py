"""Krav: K5 och K19 i docs/02-KRAV.md, ADR-0016 och ADR-0028.
Test: tests/test_konvertering.py, tests/test_olinjerade.py och
tests/test_skarvar.py.

En tabell som hittats på sidan, med eller utan linjer.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Funnen:
    ruta: tuple[float, float, float, float]
    rader: list[list[str]]
    # Kolumngränserna, som skarven jämför med grannsidornas (K19).
    kanter: tuple[float, ...]
