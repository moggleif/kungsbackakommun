"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_kalibrering.py.

Facit för en rad som väg H läst på en renderad textlagersida: talen i
textlagrets tecken vars mittpunkt ligger i radens ruta, från vänster.
Mellan två tecken står ett mellanslag när textlagret har ett, eller när
avståndet är minst 15 % av tecknets storlek större än radens vanliga
avstånd, eftersom pdfplumbers ord ibland läser ihop det som syns
åtskilt (`2021-03-2215:33:39`) och en spärrad rad har luft mellan alla
tecken. Det vanliga avståndet räknas bara när raden har minst fyra
avstånd mellan tecken intill varandra, så att ett enda synligt mellanrum
inte blir det vanliga. En rad som rör en bild på sidan har inget facit,
eftersom ett tal i bilden saknas i textlagret. Inte heller en rad med en
siffra som är vriden eller spegelvänd, eftersom tecknens ordning från
vänster då inte är textens (`001 6002` för `100 2006`). Andra vridna
tecken, som en stående marginaltext, hoppas över. Kursiv räknas som rak.

pdfplumber läser ihop en upphöjd siffra med ordet före, så att `118²`
blir `1182`. Därför prövas tecknen för sig: raden har ett upphöjt tecken
i textlagret när en siffra står intill närmaste synliga tecken, närmare
än en teckenstorlek, och är mindre än 85 % av det eller slutar mer än
en fjärdedel av sin storlek ovanför det. Siffran jämförs bara med
tecknet intill, eftersom en rubrik i mindre stil bredvid ett datum
(`Upprättad 2016-08-16`) inte är upphöjd.
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
INTILL = 1.0
SNETT = 0.01
SPARRAD = 4


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
    tecken = radens_tecken(sida, ruta)
    if any(t["text"].isdigit() and not rak(t) for t in tecken):
        return None
    return vag_h.tal(med_mellanrum([t for t in tecken if rak(t)]))


def radens_tecken(sida: Facitsida, ruta: Ruta) -> list[dict]:
    pa_raden = (t for t in sida.tecken if inom(t, skalad(ruta)))
    return sorted(pa_raden, key=lambda t: t["x0"])


def rak(tecken: dict) -> bool:
    a, b, _, d, _, _ = tecken["matrix"]
    return a > 0 and d > 0 and abs(b) <= SNETT * a


def med_mellanrum(tecken: list[dict]) -> str:
    synliga = [t for t in tecken if not t["text"].isspace()]
    avstand = [b["x0"] - a["x1"] for a, b in pairwise(synliga) if intill(a, b)]
    vanligt = max(0, median(avstand)) if len(avstand) >= SPARRAD else 0
    text = [tecken[0]["text"]] if tecken else []
    for fore, t in pairwise(tecken):
        if t["x0"] - fore["x1"] - vanligt >= MELLANRUM * t["size"]:
            text.append(" ")
        text.append(t["text"])
    return "".join(" " if t.isspace() else t for t in text)


def har_upphojt(sida: Facitsida, ruta: Ruta) -> bool:
    synliga = [t for t in radens_tecken(sida, ruta) if not t["text"].isspace()]
    return any(
        upphojd(a, b) or upphojd(b, a) for a, b in pairwise(synliga) if intill(a, b)
    )


def intill(a: dict, b: dict) -> bool:
    return b["x0"] - a["x1"] < INTILL * max(a["size"], b["size"])


def upphojd(siffra: dict, granne: dict) -> bool:
    return siffra["text"].isdigit() and (
        siffra["size"] < MINDRE * granne["size"]
        or siffra["bottom"] < granne["bottom"] - OVER * siffra["size"]
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
