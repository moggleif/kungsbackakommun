"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_kalibrering.py.

Facit för en rad som väg H läst på en renderad textlagersida: talen i
textlagrets tecken vars mittpunkt ligger i radens ruta, från vänster.
Mellan två tecken står ett mellanslag när textlagret har ett, eller när
avståndet är minst 15 % av tecknets storlek, eftersom pdfplumbers ord
ibland läser ihop det som syns åtskilt (`2021-03-2215:33:39`). En rad som rör en
bild på sidan har inget facit, eftersom ett tal i bilden saknas i
textlagret. pdfplumber läser ihop en upphöjd siffra med ordet före, så
att `118²` blir `1182`. Därför prövas tecknen för sig: raden har ett
upphöjt tecken i textlagret när ett tecken är mindre än 85 % av radens
största, eller slutar mer än en fjärdedel av sin storlek ovanför radens
lägsta underkant.
"""

from dataclasses import dataclass
from itertools import pairwise
from statistics import median

import pdfplumber

from kommunhandlingar.konvertering import ocr, vag_h
from kommunhandlingar.konvertering.rapid import Ruta

SKALA = 72 / ocr.DPI
MINDRE = 0.85
OVER = 0.25
MELLANRUM = 0.15


@dataclass(frozen=True)
class Facitsida:
    ord: list[dict]
    tecken: list[dict]
    bilder: list[Ruta]


def las(sida: pdfplumber.page.Page) -> Facitsida:
    bilder = [(b["x0"], b["top"], b["x1"], b["bottom"]) for b in sida.images]
    return Facitsida(sida.extract_words(), list(sida.chars), bilder)


def radens_tal(sida: Facitsida, ruta: Ruta) -> list[str] | None:
    if any(ror(b, skalad(ruta)) for b in sida.bilder):
        return None
    tecken = sorted(
        (t for t in sida.tecken if inom(t, skalad(ruta))), key=lambda t: t["x0"]
    )
    return vag_h.tal("".join(med_mellanrum(tecken)))


def med_mellanrum(tecken: list[dict]) -> list[str]:
    text = [tecken[0]["text"]] if tecken else []
    for fore, t in pairwise(tecken):
        if t["x0"] - fore["x1"] >= MELLANRUM * t["size"]:
            text.append(" ")
        text.append(t["text"])
    return text


def har_upphojt(sida: Facitsida, ruta: Ruta) -> bool:
    tecken = [
        t for t in sida.tecken if inom(t, skalad(ruta)) and not t["text"].isspace()
    ]
    if not tecken:
        return False
    storst = max(t["size"] for t in tecken)
    botten = median(t["bottom"] for t in tecken)
    return any(
        t["size"] < MINDRE * storst or t["bottom"] < botten - OVER * t["size"]
        for t in tecken
    )


def tal_utanfor(sida: Facitsida, rutor: list[Ruta]) -> list[str]:
    """Talen i textlagrets ord utanför alla rader och bilder."""
    alla = [skalad(r) for r in rutor] + sida.bilder
    return [
        t
        for o in sida.ord
        if not any(inom(o, r) for r in alla)
        for t in vag_h.tal(o["text"])
    ]


def skalad(ruta: Ruta) -> Ruta:
    x0, y0, x1, y1 = (v * SKALA for v in ruta)
    return x0, y0, x1, y1


def ror(bild: Ruta, ruta: Ruta) -> bool:
    return (
        bild[0] < ruta[2]
        and ruta[0] < bild[2]
        and bild[1] < ruta[3]
        and ruta[1] < bild[3]
    )


def inom(o: dict, ruta: Ruta) -> bool:
    x, y = (o["x0"] + o["x1"]) / 2, (o["top"] + o["bottom"]) / 2
    return ruta[0] <= x <= ruta[2] and ruta[1] <= y <= ruta[3]
