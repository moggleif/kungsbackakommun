"""Krav: K6, K41 och K73 i docs/02-KRAV.md, ADR-0005, ADR-0064 och ADR-0100.
Test: tests/test_konvertering.py och tests/test_hogkant.py.

En sida som ska läsas med OCR renderas med pypdfium2 i 300 dpi, i gråskala,
och läses av Tesseract (`tesseract`). Säkerheten är medelvärdet av
Tesseracts säkerhet för de ord den känt igen; under tröskeln, eller utan
ord, ger läsningen ingen text men sin TSV, som de säkra raderna läses ur
(K73). Fallerar Tesseract ger läsningen ingenting.

Ord på högkant, som en stämpel i marginalen, målas vita och sidan läses
om, och de skrivs sist på sidan (K41, ADR-0064). Läsningen ger också
rutorna kring de ord som lästs säkert, som bildytan räknas utan (K72,
ADR-0099).

Två fel som Tesseract gör i protokollen rättas i texten (K34, ADR-0055):
`§` intill en siffra läses som `$`, och en innehållsförtecknings
punktutfyllnad blir punkter och bokstäver fram till sidnumret.
"""

import re
from dataclasses import dataclass, field

import pypdfium2 as pdfium
from PIL import Image

from kommunhandlingar.konvertering import hogkant, tesseract
from kommunhandlingar.konvertering.tsv import Ord, Ruta, orden

TROSKEL = 70
SAKERT_ORD = 50
PARAGRAF = re.compile(r"\$+(?= ?\d)|(?<=\d )\$+|(?<=\d)\$+")
# Punkterna kan börja med brus utan mellanslag (`..ssss.....`); efter dem
# står bara brus fram till sidnumret, på samma rad.
UTFYLLNAD = re.compile(
    r"[ \t]*(?:\.\.[a-zåäö.]*?)?\.{4}[a-zåäö., >-]*?(\d+)[ \t]*$", re.MULTILINE
)


@dataclass(frozen=True)
class Lasning:
    text: str | None
    ord: list[Ruta] = field(default_factory=list)
    ordantal: int | None = None  # None: Tesseract fallerade
    tsv: str = ""


def rendera(rendering: pdfium.PdfPage) -> Image.Image:
    return rendering.render(scale=tesseract.DPI / 72, grayscale=True).to_pil()


def las(bild: Image.Image) -> Lasning:
    """Bildens OCR-text, None när den inte når tröskeln, och rutorna kring
    de säkra orden. Ord på högkant målas vita och sidan läses om; de skrivs
    sist (ADR-0064). Når omläsningen inte tröskeln gäller den första."""
    forsta = tesseract.las_bild(bild)
    if forsta is None:
        return Lasning(None)
    ord_ = orden(forsta.tsv)
    rutor, antal = sakra_ord(ord_), len(ord_)
    if not over_troskeln(ord_):
        return Lasning(None, rutor, antal, forsta.tsv)
    return Lasning(
        text_utan_stamplar(bild, forsta.text, hogkant.ocr_ord(ord_)), rutor, antal
    )


def text_utan_stamplar(bild: Image.Image, text: str, stamplar: list[Ord]) -> str:
    if stamplar:
        bild = bild.copy()
        hogkant.mala_vitt(bild, stamplar)
        andra = tesseract.las_bild(bild)
        if andra is not None and over_troskeln(orden(andra.tsv)):
            return hogkant.sist(rensa(andra.text.strip()), hogkant.ocr_rader(stamplar))
    return rensa(text.strip())


def over_troskeln(ord_: list[Ord]) -> bool:
    sakerhet = medelsakerhet(ord_)
    return sakerhet is not None and sakerhet >= TROSKEL


def rensa(text: str) -> str:
    text = PARAGRAF.sub(lambda m: "§" * len(m[0]), text)
    return UTFYLLNAD.sub(r" .... \1", text)


def medelsakerhet(ord_: list[Ord]) -> float | None:
    varden = [o.sakerhet for o in ord_]
    return sum(varden) / len(varden) if varden else None


def sakra_ord(ord_: list[Ord]) -> list[Ruta]:
    """Rutorna kring ord med minst två tecken och säkerhet minst 50."""
    return [
        o.ruta for o in ord_ if o.sakerhet >= SAKERT_ORD and len(o.text.strip()) >= 2
    ]
