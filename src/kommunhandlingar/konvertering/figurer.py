"""Krav: K15 i docs/02-KRAV.md, ADR-0017. Test: tests/test_figurer.py.

Om en sida kan ha en figur: ett diagram, en karta, ett schema eller en
bild (docs/03-ARKITEKTUR.md#figurer). Regeln får hellre ta med en sida för
mycket än missa en; den som tolkar sidan avgör om det är en figur.
"""

from pdfplumber.page import Page

from kommunhandlingar.konvertering import vag
from kommunhandlingar.konvertering.geometri import (
    Ruta,
    inom,
    mitt,
    mitt_av,
    omslutande,
    ruta,
)

MINSTA_BILD = 0.02
HELSIDA = 0.9
MINSTA_ANTAL = 8
MINSTA_SPANN = 0.02
TUNN = 2
VITT = {(1,), (1, 1, 1), (0, 0, 0, 0)}


def har_figur(sida: Page, tabeller: list[Ruta]) -> bool:
    def utanfor(rutor: list[Ruta]) -> list[Ruta]:
        return [r for r in rutor if not any(inom(mitt_av(r), t) for t in tabeller)]

    yta = sida.width * sida.height
    bilder = utanfor([vag.ruta(b, sida) for b in sida.images])
    if any(MINSTA_BILD <= andel(r, yta) < HELSIDA for r in bilder):
        return True
    objekt = utanfor([ruta(o) for o in vektorobjekt(sida)])
    return (
        len(objekt) >= MINSTA_ANTAL and andel(omslutande(objekt), yta) >= MINSTA_SPANN
    )


def vektorobjekt(sida: Page) -> list[dict]:
    tecken = [mitt(t) for t in sida.chars]
    rutor = [r for r in sida.rects if synlig(r) and min(r["width"], r["height"]) > TUNN]
    rutor = [r for r in rutor if not any(inom(t, ruta(r)) for t in tecken)]
    return sida.curves + rutor


def synlig(rektangel: dict) -> bool:
    farg = rektangel["non_stroking_color"]
    farg = tuple(farg) if isinstance(farg, list | tuple) else (farg,)
    return rektangel["stroke"] or (rektangel["fill"] and farg not in VITT)


def andel(r: Ruta, yta: float) -> float:
    return max(0.0, r[2] - r[0]) * max(0.0, r[3] - r[1]) / yta
