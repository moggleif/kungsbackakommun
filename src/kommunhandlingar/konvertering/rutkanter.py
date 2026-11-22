"""Krav: K61 i docs/02-KRAV.md och ADR-0087.
Test: tests/test_rutkanter.py.

Word ritar en tabells celler som fyllda rutor, en per cell. Där två rutor
möts kant i kant är den gemensamma kanten en cellgräns, också där inget
streck är ritat. Rutornas yttre kanter räknas inte, så en färgad rad
eller kolumn blir ingen gräns (ADR-0005).
"""

import math
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from kommunhandlingar.konvertering.geometri import Ruta

GLAPP = 1  # punkter mellan två rutor som ändå möts kant i kant
KORTASTE = 2  # punkter som rutorna minst ska mötas längs


@dataclass(frozen=True)
class Led:
    """En ruta som slutar vid `slut` möter en som börjar vid `borjan`."""

    slut: str
    borjan: str
    kant: Callable[[dict, dict], dict | None]


def gemensamma(rutor: list[dict]) -> list[dict]:
    """Kanterna där två rutor möts, som linjer för pdfplumber."""
    return [*mots(rutor, LODRAT), *mots(rutor, VAGRAT)]


def mots(rutor: list[dict], led: Led) -> list[dict]:
    """Rutorna slås upp efter heltalspunkt, eftersom en sida kan ha tusentals
    rutor och alla par vore för långsamt. Två värden högst 1 isär har
    heltalsdelar högst 1 isär."""
    efter_borjan = defaultdict(list)
    for ruta in rutor:
        efter_borjan[math.floor(ruta[led.borjan])].append(ruta)
    granne = (
        (a, b)
        for a in rutor
        for steg in (-1, 0, 1)
        for b in efter_borjan[math.floor(a[led.slut]) + steg]
        if abs(a[led.slut] - b[led.borjan]) <= GLAPP
    )
    return [k for a, b in granne if (k := led.kant(a, b))]


def lodrat(a: dict, b: dict) -> dict | None:
    topp, botten = max(a["top"], b["top"]), min(a["bottom"], b["bottom"])
    x = (a["x1"] + b["x0"]) / 2
    return linje((x, topp, x, botten)) if botten - topp >= KORTASTE else None


def vagrat(a: dict, b: dict) -> dict | None:
    vanster, hoger = max(a["x0"], b["x0"]), min(a["x1"], b["x1"])
    y = (a["bottom"] + b["top"]) / 2
    return linje((vanster, y, hoger, y)) if hoger - vanster >= KORTASTE else None


LODRAT = Led("x1", "x0", lodrat)
VAGRAT = Led("bottom", "top", vagrat)


def linje(ruta: Ruta) -> dict:
    x0, top, x1, bottom = ruta
    return {
        "object_type": "line",
        "x0": x0,
        "top": top,
        "x1": x1,
        "bottom": bottom,
        "width": x1 - x0,
        "height": bottom - top,
    }
