"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_kalibrering.py.

Mätningen på en textlagersida: sidan renderas som i konverteringen, läses
med väg H, och varje rad jämförs med textlagret. En bekräftad rad är `ratt`
när talen är textlagrets och annars `fel`. En rad som rör en bild är
`utan-facit`. En rad där ingen läsning har ett tal men textlagret har det
är `missad`, och textlagrets tal utanför alla rader räknas som `utanfor`.
En sida är bekräftad när alla dess rader med tal är det och inget tal i
Tesseracts läsning står utanför raderna.
"""

from dataclasses import dataclass

import pdfplumber
import pypdfium2 as pdfium

from kommunhandlingar.kalibrering import facit
from kommunhandlingar.konvertering import ocr, radlasning


@dataclass(frozen=True)
class Utfall:
    hur: str
    utfall: str
    tal: str
    facit: str
    rapid: str
    tesseract: str


@dataclass(frozen=True)
class Sidutfall:
    rader: list[Utfall]
    bekraftad: bool


def mat(pdf: pdfium.PdfDocument, plumber: pdfplumber.PDF, nummer: int) -> Sidutfall:
    lasning = radlasning.las(ocr.rendera(pdf[nummer - 1]))
    sida = plumber.pages[nummer - 1]
    rader = [utfall(rad, facit.radens_tal(sida, rad.ruta)) for rad in lasning.rader]
    med_tal = {r.ruta for r in lasning.rader}
    rader += [
        Utfall("", "missad", "", " ".join(tal), "", "")
        for ruta in lasning.rutor
        if ruta not in med_tal and (tal := facit.radens_tal(sida, ruta))
    ]
    utanfor = facit.tal_utanfor(sida, lasning.rutor)
    if utanfor:
        rader.append(Utfall("", "utanfor", "", " ".join(utanfor), "", ""))
    alla = all(r.avgorande.tal is not None for r in lasning.rader)
    return Sidutfall(rader, alla and lasning.tal_utanfor == 0)


def utfall(rad: radlasning.Rad, ratt: list[str] | None) -> Utfall:
    tal = rad.avgorande.tal
    if tal is None:
        varde = "obekraftad"
    elif ratt is None:
        varde = "utan-facit"
    else:
        varde = "ratt" if tal == ratt else "fel"
    return Utfall(
        rad.avgorande.hur,
        varde,
        "" if tal is None else " ".join(tal),
        "" if ratt is None else " ".join(ratt),
        rad.rapid,
        rad.tesseract,
    )
