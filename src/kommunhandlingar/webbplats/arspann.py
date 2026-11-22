"""Krav: K60 i docs/02-KRAV.md, ADR-0086. Test: tests/test_arspann.py.

Åren som varje sida över tid i en kommun visar, lika för alla organ och
flikar så att de går att jämföra: från poolens första år till året då
webbplatsen byggs, och längre åt något håll om en rad i kommunens mål-,
uppföljnings- eller spårfiler ligger utanför, som en budget för nästa år.
"""

from pathlib import Path


def arspann(ar: list[int]) -> range:
    return range(min(ar), max(ar) + 1)


def poolens_ar(katalog: Path) -> list[int]:
    return [int(p.name) for p in katalog.glob("*/[0-9][0-9][0-9][0-9]")]
