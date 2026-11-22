"""Krav: K6, ADR-0005. Test: tests/test_tsv.py.

Orden i Tesseracts TSV. Tesseract skriver en rad per sida, block, stycke,
rad och ord; bara orden har en säkerhet, de andra har −1. Ett ord utan
text räknas inte. Citattecken i texten är vanliga tecken (`QUOTE_NONE`).
"""

import csv
from dataclasses import dataclass

Ruta = tuple[int, int, int, int]


@dataclass(frozen=True)
class Ord:
    text: str
    sakerhet: float
    ruta: Ruta
    radnyckel: tuple[str, str, str, str]  # sida, block, stycke och rad


def orden(tsv: str) -> list[Ord]:
    rader = csv.DictReader(tsv.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE)
    return [ordet(r) for r in rader if r["text"].strip() and r["conf"] != "-1"]


def ordet(rad: dict[str, str]) -> Ord:
    x, y = int(rad["left"]), int(rad["top"])
    return Ord(
        rad["text"],
        float(rad["conf"]),
        (x, y, x + int(rad["width"]), y + int(rad["height"])),
        (rad["page_num"], rad["block_num"], rad["par_num"], rad["line_num"]),
    )
