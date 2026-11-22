"""Krav: K4, K5, K6, K15, K17, K19, K41, K72 och K73 i docs/02-KRAV.md, ADR-0005,
ADR-0016, ADR-0017, ADR-0022, ADR-0024, ADR-0028, ADR-0033, ADR-0034,
ADR-0036, ADR-0038, ADR-0063, ADR-0064, ADR-0099 och ADR-0103.
Test: tests/test_konvertering.py,
tests/test_maska_poolen.py, tests/test_skarvar.py, tests/test_delade.py,
tests/test_kvarvarande.py, tests/test_avskurna.py, tests/test_mellanslag.py,
tests/test_ordning.py, tests/test_spalter.py, tests/test_hogkant.py och
tests/test_skannad.py.

En sida blir `tom`, läses ur textlagret, eller läses med OCR. En OCR-sida
får inga tabeller, och dess tal är aldrig bekräftade; en inskannad sida som
inte blir text kan bli `bild` eller `tom` (K72). En sida som inte är
tom prövas för figurer. Personuppgifterna maskas i text och celler innan
sidan lämnas vidare, och styrtecken blir ersättningstecken. En sida ur
textlagret får en skarv för K19, vars rader bara jämförs och aldrig
skrivs. Text i spalter läses spalt för spalt,
och text på högkant skrivs sist.
"""

import re
from dataclasses import dataclass, field, replace

import pypdfium2 as pdfium
from pdfplumber.page import Page

from kommunhandlingar.konvertering import (
    delade,
    figurer,
    hogkant,
    kvalitet,
    kvarvarande,
    markdown,
    olinjerade,
    skannad,
    spalter,
    tabeller,
)
from kommunhandlingar.konvertering.avskurna import avskuren
from kommunhandlingar.konvertering.mellanslag import utan_mellanslag_i_tal
from kommunhandlingar.konvertering.ordning import i_oordning
from kommunhandlingar.konvertering.skarv import Skarv, skarv
from kommunhandlingar.konvertering.text import komprimera, stycken
from kommunhandlingar.konvertering.vag import olasliga, vag
from kommunhandlingar.personuppgifter import maska

RENDERING_72_DPI = 1
# Styrtecken utom radbrytning, vagnretur och tabb (Unicode Cc).
STYRTECKEN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


@dataclass(frozen=True)
class Sida:
    kvalitet: str
    tal_obekraftade: bool
    text: str = ""
    tabeller: list[list[list[str]]] = field(default_factory=list)
    figur: bool = False
    skarv: Skarv | None = None


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
    """En sida som läses med OCR (K72). Bara en `tom` eller `ointressant`
    sida (K73) är utan obekräftade tal och står aldrig i `figurer`."""
    skannad_ = skannad.las(rendering)
    figur = figur or skannad_.figur
    match skannad_.kvalitet:
        case kvalitet.OCR:
            rader = [markdown.rad(r) for r in skannad_.text.splitlines()]
            return Sida(kvalitet.OCR, True, komprimera(rader), figur=figur)
        case kvalitet.TOM | kvalitet.OINTRESSANT:
            return Sida(skannad_.kvalitet, False)
        case annan:
            return Sida(annan, True, figur=figur)


def ej_vita(rendering: pdfium.PdfPage) -> float:
    bild = rendering.render(scale=RENDERING_72_DPI).to_pil().convert("L")
    staplar = bild.histogram()
    return 1 - staplar[255] / sum(staplar)


def textsida(sida: Page) -> Sida:
    """Text på högkant utan siffror ger obekräftade tal bara när sidan
    läses annorlunda utan den: tabellerna, talraderna eller texten
    (ADR-0103). Prövas bara på sidor med sådan text."""
    last = lasning(sida)
    if last.tal_obekraftade or all(c["upright"] for c in sida.chars):
        return last
    utan = lasning(hogkant.staende(sida))
    andrar = replace(utan, text="") != replace(last, text="")
    tillagt = last.text.removeprefix(utan.text)
    lika = last.text.startswith(utan.text) and not any(t.isnumeric() for t in tillagt)
    return replace(last, tal_obekraftade=andrar or not lika)


def lasning(sida: Page) -> Sida:
    sida = utan_mellanslag_i_tal(sida)
    hittade, fallda = med_linjer(sida)
    rutor = [ruta for ruta, _, _ in hittade]
    utan_linjer = olinjerade.tabeller(sida, rutor)
    rutor += [t.bbox for t in utan_linjer]
    utanfor = sida.filter(lambda o: not tabeller.i_tabell(o, rutor))
    text, i_texten = sidans_text(utanfor)
    osaker = i_texten or osakra_tal(sida, fallda, rutor)
    hittade += [(t.bbox, t.rader, t.kanter) for t in utan_linjer]
    hittade.sort(key=lambda t: (round(t[0][1]), t[0][0]))
    return Sida(
        kvalitet.TABELL_OSAKER if osaker else kvalitet.OK,
        olasliga(sida) > 0 or i_oordning(sida, rutor),
        text,
        [rader for _, rader, _ in hittade],
        figurer.har_figur(sida, rutor),
        skarv(
            hogkant.staende(utanfor), [(ruta, kanter) for ruta, _, kanter in hittade]
        ),
    )


def sidans_text(utanfor: Page) -> tuple[str, bool]:
    """Texten utanför tabellerna, spalt för spalt, med text på högkant
    sist (K41)."""
    text = spalter.text(hogkant.staende(utanfor))
    return stycken(hogkant.sist(text, hogkant.textlagret(utanfor)))


def med_linjer(sida: Page) -> tuple[list[tuple], list[tuple]]:
    """Tabellerna med linjer som ruta, rader och kanter, också de som
    delats (ADR-0028), och rutorna kring dem som fälldes, också de
    avskurna (ADR-0034)."""
    ord_ = sida.extract_words(return_chars=True)
    sakra, fallda = tabeller.sakra(sida, ord_)
    hittade = [(t.bbox, tabeller.rader(t), tabeller.kanter(t)) for t in sakra]
    for t in fallda:
        delad = delade.tabell(t, ord_)
        if delad is not None:
            hittade.append((t.bbox, *delad))
    rutor = [ruta for ruta, _, _ in hittade]
    upptagna = rutor + [t.bbox for t in fallda]
    avskurna = [ruta for ruta in rutor if avskuren(ruta, ord_, upptagna)]
    hela = [t for t in hittade if t[0] not in avskurna]
    return hela, [t.bbox for t in fallda] + avskurna


def osakra_tal(sida: Page, fallda: list[tuple], rutor: list[tuple]) -> bool:
    """En siffra ur en fälld tabell med linjer, eller talrader i linje,
    utanför de tabeller som lästs."""
    siffror = any(olast_siffra(c, fallda, rutor) for c in sida.chars)
    return siffror or kvarvarande.har_talrader(sida, rutor)


def olast_siffra(tecken: dict, fallda: list[tuple], rutor: list[tuple]) -> bool:
    """En siffra i en fälld tabell med linjer som inte lästs i någon tabell."""
    i_fallda = any(tabeller.inom(tabeller.mitt(tecken), f) for f in fallda)
    return (
        tecken["text"].isdigit() and i_fallda and not tabeller.i_tabell(tecken, rutor)
    )
