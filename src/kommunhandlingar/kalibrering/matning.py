"""Krav: K84 i docs/02-KRAV.md, ADR-0105 och ADR-0116. Test: tests/test_kalibrering.py.

Mätningen på en textlagersida: sidan renderas som i konverteringen, läses
med väg H, och varje rad jämförs med textlagret. En bekräftad rad är `ratt`
när talen är textlagrets och annars `fel`, och `upphojt` när textlagret
har ett upphöjt tecken på raden, eftersom det är just det skyddet ska
stoppa. En rad som rör en bild eller har vridna tecken är `utan-facit`.
En rad som väg H inte avgjort, eftersom ingen läsning kan ha ett tal
(`vag_h.kan_ha_tal`), men där textlagret har ett är `missad`, och
textlagrets tal utanför alla rader räknas som `utanfor`. En sida är
bekräftad när alla rader som kan ha tal är det och inget tal i
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
    bild = ocr.rendera(pdf[nummer - 1])
    lasning = radlasning.las(bild, radlasning.tesseracts_tsv(bild))
    sida = facit.las(plumber.pages[nummer - 1])
    rader = [utfall(rad, sida) for rad in lasning.rader] + missade(lasning, sida)
    alla = all(r.avgorande.tal is not None for r in lasning.rader)
    return Sidutfall(rader, alla and lasning.tal_utanfor == 0)


def missade(lasning: radlasning.Sidlasning, sida: facit.Facitsida) -> list[Utfall]:
    """Textlagrets tal på rader som väg H inte avgjort, och utanför raderna."""
    avgjorda = {r.ruta for r in lasning.rader}
    rader = [
        Utfall("", "missad", "", " ".join(tal), "", "")
        for ruta in lasning.rutor
        if ruta not in avgjorda and (tal := facit.radens_tal(sida, ruta))
    ]
    utanfor = facit.tal_utanfor(sida, lasning.rutor)
    if utanfor:
        rader.append(Utfall("", "utanfor", "", " ".join(utanfor), "", ""))
    return rader


def utfall(rad: radlasning.Rad, sida: facit.Facitsida) -> Utfall:
    tal, ratt = rad.avgorande.tal, facit.radens_tal(sida, rad.ruta)
    return Utfall(
        rad.avgorande.hur,
        varde(tal, ratt, lambda: facit.har_upphojt(sida, rad.ruta)),
        "" if tal is None else " ".join(tal),
        "" if ratt is None else " ".join(ratt),
        rad.rapid,
        rad.tesseract,
    )


def varde(tal: list[str] | None, ratt: list[str] | None, upphojt) -> str:
    if tal is None:
        return "obekraftad"
    if ratt is None:
        return "utan-facit"
    if upphojt():
        return "upphojt"
    return "ratt" if tal == ratt else "fel"
