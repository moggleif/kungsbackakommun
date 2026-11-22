"""Krav: K84 i docs/02-KRAV.md, ADR-0005 och ADR-0105. Test:
tests/test_radlasning.py.

Väg H på en sidbild i 300 dpi. RapidOCR hittar raderna och läser dem.
Tesseract läser hela sidan, och varje ord hör till de rader vars ruta
har ordets mittpunkt. Raderna där någon läsning har ett tal avgörs med
`vag_h.avgor`. En rad bekräftas aldrig när den har ett upphöjt tecken
eller själv är upphöjd (`upphojt`), prövat i ett utsnitt med 15 pixlars
marginal. Inte heller när rutan går in i en annan ruta på samma rad,
eftersom RapidOCR då kan läsa en bit av grannens tal som ett eget
(`9 2024-01-24` ur `2024-02-29 2024-01-24`). Ett tal i Tesseracts ord
utanför alla rader räknas för sig, eftersom ingen rad kan bekräfta det.
"""

from dataclasses import dataclass

from PIL import Image

from kommunhandlingar.konvertering import ocr, rapid, upphojt, vag_h
from kommunhandlingar.konvertering.rapid import Ruta

MARGINAL = 15


class Fallerade(Exception):
    """Tesseract kunde inte läsa sidan."""


@dataclass(frozen=True)
class Ord:
    x: float
    y: float
    vanster: int
    text: str


@dataclass(frozen=True)
class Rad:
    ruta: Ruta
    rapid: str
    tesseract: str
    avgorande: vag_h.Avgorande


@dataclass(frozen=True)
class Sidlasning:
    rader: list[Rad]  # raderna där någon läsning har ett tal
    rutor: list[Ruta]  # alla rader
    tal_utanfor: int


def las(bild: Image.Image) -> Sidlasning:
    hittade = rapid.rader(bild)
    ord_ = tesseracts_ord(bild)
    rutor = [r for r, _ in hittade]
    rader = []
    for ruta, text in hittade:
        tess = radens_text(ord_, ruta)
        if vag_h.tal(text) or vag_h.tal(tess):
            rader.append(Rad(ruta, text, tess, avgor(bild, ruta, (text, tess), rutor)))
    utanfor = [o for o in ord_ if not any(inom(o, r) for r in rutor)]
    return Sidlasning(rader, rutor, sum(len(vag_h.tal(o.text)) for o in utanfor))


def avgor(bild: Image.Image, ruta: Ruta, texter: tuple[str, str], rutor: list):
    if upphojt.upphojd_rad(ruta, rutor):
        return vag_h.Avgorande(None, "upphojd-rad")
    if overlappar(ruta, rutor):
        return vag_h.Avgorande(None, "overlappar")
    utsnitt = med_marginal(ruta, bild)
    rad = (int(ruta[1]) - utsnitt[1], int(ruta[3]) - utsnitt[1])
    if upphojt.har_upphojt(bild.crop(utsnitt), rad):
        return vag_h.Avgorande(None, "upphojt")
    return vag_h.avgor(*texter, lambda: rapid.las_rad(bild.crop(utsnitt)))


def overlappar(ruta: Ruta, rutor: list[Ruta]) -> bool:
    return any(
        andra != ruta
        and andra[0] < ruta[2]
        and ruta[0] < andra[2]
        and min(ruta[3], andra[3]) - max(ruta[1], andra[1])
        > min(ruta[3] - ruta[1], andra[3] - andra[1]) / 2
        for andra in rutor
    )


def med_marginal(ruta: Ruta, bild: Image.Image) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = (int(v) for v in ruta)
    return (
        max(0, x0 - MARGINAL),
        max(0, y0 - MARGINAL),
        min(bild.width, x1 + MARGINAL),
        min(bild.height, y1 + MARGINAL),
    )


def inom(o: Ord, ruta: Ruta) -> bool:
    return ruta[0] <= o.x <= ruta[2] and ruta[1] <= o.y <= ruta[3]


def radens_text(ord_: list[Ord], ruta: Ruta) -> str:
    pa_raden = sorted((o for o in ord_ if inom(o, ruta)), key=lambda o: o.vanster)
    return " ".join(o.text for o in pa_raden)


def tesseracts_ord(bild: Image.Image) -> list[Ord]:
    lasning = ocr.las_bild(bild)
    if lasning is None:
        raise Fallerade
    return [
        Ord(
            int(r["left"]) + int(r["width"]) / 2,
            int(r["top"]) + int(r["height"]) / 2,
            int(r["left"]),
            r["text"],
        )
        for r in ocr.ordrader(lasning[0])
    ]
