"""Krav: K6 och K41 i docs/02-KRAV.md, ADR-0112. Test: tests/test_snett.py.

Text i textlagret som varken står rakt eller på högkant: snett, som ett
gatunamn längs en väg på en karta, eller upp och ned. pdfminer räknar
den som upprätt (`upright`), och läst med resten av sidan blir `73` upp
och ned `37`. Tecknen tas ur sidans flöde och skrivs sist på sidan i
textlagrets ordning (docs/03-ARKITEKTUR.md#text-på-högkant).
"""

import math
from itertools import pairwise

from pdfplumber.page import Page

TOLERANS = 0.5
ORDLUCKA = 0.25
STYCKESLUCKA = 2


def rakt(tecken: dict) -> bool:
    """Upprätt, med baslinjen högst en halv grad från vågrät."""
    a, b = tecken["matrix"][:2]
    vinkel = math.degrees(math.atan2(b, a))
    return tecken["upright"] and abs(vinkel) < TOLERANS


def snett(tecken: dict) -> bool:
    return tecken["upright"] and not rakt(tecken)


def textlagret(sida: Page) -> list[str]:
    """Raderna i textlagrets ordning, delade där nästa tecken inte står
    där det förra slutar."""
    tecknen = [c for c in sida.chars if snett(c)]
    if not tecknen:
        return []
    text = tecknen[0]["text"]
    for fore, c in pairwise(tecknen):
        text += skiljetecken(fore, c) + c["text"]
    return [" ".join(r.split()) for r in text.split("\n") if r.strip()]


def skiljetecken(fore: dict, tecken: dict) -> str:
    """Mer än en fjärdedels teckenbredd från där det förra tecknet slutar blir
    ett mellanslag, mer än två teckenbredder en ny rad."""
    a, b, _, _, e, f = fore["matrix"]
    slut = (e + a * fore["adv"], f + b * fore["adv"])
    lucka = math.dist(slut, tecken["matrix"][4:])
    bredd = fore["adv"] * math.hypot(a, b)
    if lucka > STYCKESLUCKA * bredd:
        return "\n"
    return " " if lucka > ORDLUCKA * bredd else ""
