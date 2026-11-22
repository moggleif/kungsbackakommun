"""Krav: K6, K15, K72, K73 och K85 i docs/02-KRAV.md, ADR-0005, ADR-0099,
ADR-0100 och ADR-0106. Test: tests/test_skannad.py, tests/test_konvertering.py
och tests/test_bekraftade.py.

En sida som läses med OCR. Når den inte tröskeln maskas bildytan och
sidan läses om, sedan vänds den om Tesseract säger att den ligger fel.
Ger inget text läses de säkra raderna (K73). Ger de för lite text blir
sidan `bild` när den till största delen är en jämn bildyta, `tom` när
nästan inget är mörkt och Tesseract inte hittar något ord, och annars
`ointressant` (docs/03-ARKITEKTUR.md#inskannade-sidor-som-inte-blir-text).
Fallerar Tesseract är sidan `ej-konverterad` direkt, utan fler läsningar.
Når den första läsningen tröskeln utan att sidan läses om prövas väg H,
och bekräftar den sidans tal får sidan väg H:s text (K85, ADR-0106).
"""

from dataclasses import dataclass

import pypdfium2 as pdfium
from PIL import Image, ImageDraw

from kommunhandlingar.konvertering import (
    bekraftade,
    bildyta,
    kvalitet,
    ocr,
    riktning,
    sakra_rader,
    tesseract,
)

FARG_DPI = 100
FIGUR = 0.04
BILD = 0.6
NASTAN_TOM = 0.005


@dataclass(frozen=True)
class Skannad:
    kvalitet: str
    text: str = ""
    figur: bool = False
    tal_bekraftade: bool = False


def las(rendering: pdfium.PdfPage) -> Skannad:
    gra = ocr.rendera(rendering)
    farg = rendering.render(scale=FARG_DPI / 72).to_pil()
    forsta = ocr.las(gra)
    if forsta.ordantal is None:
        return Skannad(kvalitet.EJ_KONVERTERAD)
    skala = FARG_DPI / tesseract.DPI
    yta = bildyta.storsta(farg, [skalad(r, skala) for r in forsta.ord])
    figur = yta.andel >= FIGUR and yta.jamn
    text = forsta.text
    if text is None:
        text = omlast(gra, skalad(yta.ruta, 1 / skala) if figur else None)
    if text is not None:
        return med_vag_h(gra, forsta, text, figur)
    return sakra(gra, forsta.tsv, figur) or utan_text(yta, farg, forsta.ordantal)


def med_vag_h(gra: Image.Image, forsta: ocr.Lasning, text: str, figur: bool):
    """Sidan med väg H:s text när väg H bekräftar dess tal (K85), annars
    med OCR-texten."""
    if forsta.for_vag_h is not None:
        bekraftad = bekraftade.text(gra, forsta.for_vag_h)
        if bekraftad is not None:
            return Skannad(kvalitet.OCR, bekraftad, figur, tal_bekraftade=True)
    return Skannad(kvalitet.OCR, text, figur)


def sakra(gra: Image.Image, tsv: str, figur: bool) -> Skannad | None:
    """Sidan med sina säkra rader (K73), eller None när de är för få."""
    try:
        rader = sakra_rader.las(gra, tsv)
    except sakra_rader.Fallerade:
        return Skannad(kvalitet.EJ_KONVERTERAD, figur=figur)
    return None if rader is None else Skannad(kvalitet.OCR, rader, figur)


def utan_text(yta: bildyta.Yta, farg: Image.Image, ordantal: int) -> Skannad:
    if yta.andel >= BILD and yta.jamn:
        return Skannad(kvalitet.BILD, figur=True)
    if ordantal == 0 and bildyta.mork_andel(farg) <= NASTAN_TOM:
        return Skannad(kvalitet.TOM)
    return Skannad(kvalitet.OINTRESSANT)


def omlast(gra: Image.Image, bildruta: tuple | None) -> str | None:
    """Sidan med bildytan vit, och sedan vänd, tills en läsning når tröskeln."""
    if bildruta is not None:
        text = ocr.las(maskad(gra, bildruta)).text
        if text is not None:
            return text
    grader = riktning.grader(gra)
    if not grader:
        return None
    return ocr.las(gra.rotate(-grader, expand=True, fillcolor=255)).text


def maskad(bild: Image.Image, ruta: tuple) -> Image.Image:
    kopia = bild.copy()
    ImageDraw.Draw(kopia).rectangle(ruta, fill=255)
    return kopia


def skalad(ruta: tuple, skala: float) -> tuple[int, int, int, int]:
    return tuple(int(v * skala) for v in ruta)
