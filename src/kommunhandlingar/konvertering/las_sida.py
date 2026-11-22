"""Krav: K4, K6, K15, K17, K72, K73 och K85 i docs/02-KRAV.md, ADR-0005,
ADR-0017, ADR-0022, ADR-0099 och ADR-0106.
Test: tests/test_konvertering.py, tests/test_maska_poolen.py,
tests/test_styrtecken.py, tests/test_skannad.py, tests/test_hogkant.py,
tests/test_figurer.py och tests/test_ogonblicksbild.py.

En sida blir `tom`, läses ur textlagret (`textlagret.py`), eller läses med
OCR. En OCR-sida får inga tabeller, och dess tal är bekräftade bara när
väg H bekräftar dem (K85); en inskannad sida som inte blir text kan bli
`bild` eller `tom` (K72). En sida som inte är tom prövas för figurer.
Personuppgifterna maskas i text och celler innan sidan lämnas vidare, och
styrtecken blir ersättningstecken.
"""

import re
from dataclasses import replace

import pypdfium2 as pdfium
from pdfplumber.page import Page

from kommunhandlingar.konvertering import figurer, kvalitet, markdown, skannad
from kommunhandlingar.konvertering.sida import Sida
from kommunhandlingar.konvertering.text import komprimera
from kommunhandlingar.konvertering.textlagret import textsida
from kommunhandlingar.konvertering.vag import vag
from kommunhandlingar.personuppgifter import maska

RENDERING_72_DPI = 1
# Styrtecken utom radbrytning, vagnretur och tabb (Unicode Cc).
STYRTECKEN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def las_sida(sida: Page, rendering: pdfium.PdfPage) -> Sida:
    match vag(sida, lambda: ej_vita(rendering)):
        case "tom":
            return Sida(kvalitet.TOM, False)
        case "ocr":
            last = ocr_sida(rendering, figurer.har_figur(sida, []))
        case _:
            last = textsida(sida)
    return maskad(last)


def maskad(sida: Sida) -> Sida:
    tabeller_ = [[[rensad(c) for c in rad] for rad in t] for t in sida.tabeller]
    return replace(sida, text=rensad(sida.text), tabeller=tabeller_)


def rensad(text: str) -> str:
    """Personuppgifterna maskas, och ett styrtecken ur textlagret blir `�`,
    så att filen alltid är text (#257)."""
    return maska(STYRTECKEN.sub("\ufffd", text))


def ocr_sida(rendering: pdfium.PdfPage, figur: bool) -> Sida:
    """En sida som läses med OCR (K72). En `tom` eller `ointressant` sida
    (K73) är utan obekräftade tal och står aldrig i `figurer`, och en
    `ocr`-sida är utan dem när väg H bekräftat dess tal (K85)."""
    skannad_ = skannad.las(rendering)
    figur = figur or skannad_.figur
    match skannad_.kvalitet:
        case kvalitet.OCR:
            rader = [markdown.rad(r) for r in skannad_.text.splitlines()]
            obekraftade = not skannad_.tal_bekraftade
            return Sida(kvalitet.OCR, obekraftade, komprimera(rader), figur=figur)
        case kvalitet.TOM | kvalitet.OINTRESSANT:
            return Sida(skannad_.kvalitet, False)
        case annan:
            return Sida(annan, True, figur=figur)


def ej_vita(rendering: pdfium.PdfPage) -> float:
    bild = rendering.render(scale=RENDERING_72_DPI).to_pil().convert("L")
    staplar = bild.histogram()
    return 1 - staplar[255] / sum(staplar)
