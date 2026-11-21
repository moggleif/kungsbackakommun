"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_kalibrering.py.

Facit för en rad som väg H läst på en renderad textlagersida: talen i de
ord ur textlagret vars mittpunkt ligger i radens ruta. En rad som rör en
bild på sidan har inget facit, eftersom ett tal i bilden saknas i
textlagret.
"""

import pdfplumber

from kommunhandlingar.konvertering import ocr, vag_h
from kommunhandlingar.konvertering.rapid import Ruta

SKALA = 72 / ocr.DPI


def radens_tal(sida: pdfplumber.page.Page, ruta: Ruta) -> list[str] | None:
    if any(ror(b, skalad(ruta)) for b in sida.images):
        return None
    ord_ = [o for o in sida.extract_words() if inom(o, skalad(ruta))]
    return vag_h.tal(" ".join(o["text"] for o in sorted(ord_, key=lambda o: o["x0"])))


def tal_utanfor(sida: pdfplumber.page.Page, rutor: list[Ruta]) -> list[str]:
    """Talen i textlagrets ord utanför alla rader och bilder."""
    bilder = [(b["x0"], b["top"], b["x1"], b["bottom"]) for b in sida.images]
    alla = [skalad(r) for r in rutor] + bilder
    return [
        t
        for o in sida.extract_words()
        if not any(inom(o, r) for r in alla)
        for t in vag_h.tal(o["text"])
    ]


def skalad(ruta: Ruta) -> Ruta:
    x0, y0, x1, y1 = (v * SKALA for v in ruta)
    return x0, y0, x1, y1


def ror(bild: dict, ruta: Ruta) -> bool:
    x0, y0, x1, y1 = ruta
    return (
        bild["x0"] < x1 and x0 < bild["x1"] and bild["top"] < y1 and y0 < bild["bottom"]
    )


def inom(o: dict, ruta: Ruta) -> bool:
    x, y = (o["x0"] + o["x1"]) / 2, (o["top"] + o["bottom"]) / 2
    return ruta[0] <= x <= ruta[2] and ruta[1] <= y <= ruta[3]
