"""Krav: K5, K6, K15, K19 och K41 i docs/02-KRAV.md, ADR-0016, ADR-0017,
ADR-0024, ADR-0028, ADR-0033, ADR-0034, ADR-0036, ADR-0038, ADR-0063,
ADR-0064 och ADR-0103.
Test: tests/test_konvertering.py, tests/test_skarvar.py, tests/test_delade.py,
tests/test_kvarvarande.py, tests/test_avskurna.py, tests/test_mellanslag.py,
tests/test_ordning.py, tests/test_spalter.py och tests/test_hogkant.py.

En sida läst ur textlagret: tabellerna med och utan linjer, texten utanför
dem spalt för spalt med text på högkant sist, och skarven för K19, vars
rader bara jämförs och aldrig skrivs.
"""

from dataclasses import replace

from pdfplumber.page import Page
from pdfplumber.table import Table

from kommunhandlingar.konvertering import (
    delade,
    figurer,
    hogkant,
    kvalitet,
    kvarvarande,
    olinjerade,
    spalter,
    tabeller,
)
from kommunhandlingar.konvertering.avskurna import avskuren
from kommunhandlingar.konvertering.funnen import Funnen
from kommunhandlingar.konvertering.geometri import Ruta, inom, mitt
from kommunhandlingar.konvertering.mellanslag import utan_mellanslag_i_tal
from kommunhandlingar.konvertering.ordning import i_oordning
from kommunhandlingar.konvertering.sida import Sida
from kommunhandlingar.konvertering.skarv import skarv
from kommunhandlingar.konvertering.text import stycken
from kommunhandlingar.konvertering.vag import olasliga


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
    hittade, rutor, fallda = tabellerna(sida)
    utanfor = sida.filter(lambda o: not tabeller.i_tabell(o, rutor))
    text, i_texten = sidans_text(utanfor)
    osaker = i_texten or osakra_tal(sida, fallda, rutor)
    return Sida(
        kvalitet.TABELL_OSAKER if osaker else kvalitet.OK,
        olasliga(sida) > 0 or i_oordning(sida, rutor),
        text,
        [t.rader for t in hittade],
        figurer.har_figur(sida, rutor),
        skarv(hogkant.staende(utanfor), hittade),
    )


def tabellerna(sida: Page) -> tuple[list[Funnen], list[Ruta], list[Ruta]]:
    """Tabellerna med och utan linjer i sidans ordning, deras rutor, och
    rutorna för de tabeller med linjer som fälldes."""
    hittade, fallda = med_linjer(sida)
    rutor = [t.ruta for t in hittade]
    utan_linjer = olinjerade.tabeller(sida, rutor)
    rutor += [t.ruta for t in utan_linjer]
    ordnade = sorted(hittade + utan_linjer, key=lambda t: (round(t.ruta[1]), t.ruta[0]))
    return ordnade, rutor, fallda


def sidans_text(utanfor: Page) -> tuple[str, bool]:
    """Texten utanför tabellerna, spalt för spalt, med text på högkant
    sist (K41)."""
    text = spalter.text(hogkant.staende(utanfor))
    return stycken(hogkant.sist(text, hogkant.textlagret(utanfor)))


def med_linjer(sida: Page) -> tuple[list[Funnen], list[Ruta]]:
    """Tabellerna med linjer, också de som delats (ADR-0028), och rutorna
    kring dem som fälldes, också de avskurna (ADR-0034)."""
    ord_ = sida.extract_words(return_chars=True)
    sakra, fallda = tabeller.sakra(sida, ord_)
    hittade = [Funnen(t.bbox, tabeller.rader(t), tabeller.kanter(t)) for t in sakra]
    hittade += [d for d in (delad_tabell(t, ord_) for t in fallda) if d is not None]
    upptagna = [t.ruta for t in hittade] + [t.bbox for t in fallda]
    avskurna = [t.ruta for t in hittade if avskuren(t.ruta, ord_, upptagna)]
    hela = [t for t in hittade if t.ruta not in avskurna]
    return hela, [t.bbox for t in fallda] + avskurna


def delad_tabell(fallen: Table, ord_: list[dict]) -> Funnen | None:
    delningen = delade.tabell(fallen, ord_)
    if delningen is None:
        return None
    rader, kanter = delningen
    return Funnen(fallen.bbox, rader, kanter)


def osakra_tal(sida: Page, fallda: list[Ruta], rutor: list[Ruta]) -> bool:
    """En siffra ur en fälld tabell med linjer, eller talrader i linje,
    utanför de tabeller som lästs."""
    siffror = any(olast_siffra(c, fallda, rutor) for c in sida.chars)
    return siffror or kvarvarande.har_talrader(sida, rutor)


def olast_siffra(tecken: dict, fallda: list[Ruta], rutor: list[Ruta]) -> bool:
    """En siffra i en fälld tabell med linjer som inte lästs i någon tabell."""
    i_fallda = any(inom(mitt(tecken), f) for f in fallda)
    return (
        tecken["text"].isdigit() and i_fallda and not tabeller.i_tabell(tecken, rutor)
    )
