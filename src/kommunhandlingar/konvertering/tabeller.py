"""Krav: K5, K19, K61 och K89 i docs/02-KRAV.md, ADR-0005, ADR-0009, ADR-0016,
ADR-0024, ADR-0031, ADR-0087 och ADR-0111.
Test: tests/test_konvertering.py, tests/test_celler.py och tests/test_rutkanter.py.

En säker tabell är avgränsad av ritade linjer: streck, fyllda rektanglar
högst 2 punkter breda eller höga och kanten där två bredare möts
(`rutkanter.py`). Den har minst ett ord, varje ord inom dess yta har
mittpunkten i en cell (`rutnat.py`), och ingen cell rymmer mer än ett
tal. De rutnät som inte går ihop lämnas vidare, så att sidan kan märkas.

Talen i en cell känns igen vidare än `text.TAL`, med decimalpunkt,
plustecken, parentes, enhet och fotnotsstjärna, eftersom ett tal för mycket bara fäller
tabellen, medan ett tal för lite ger en cell med två tal i en CSV. En
fälld tabell kan ändå delas (`delade.py`, ADR-0028).
"""

import re

from pdfplumber.page import Page
from pdfplumber.table import Table

from kommunhandlingar.konvertering import rutkanter
from kommunhandlingar.konvertering.falt import falt, radvis
from kommunhandlingar.konvertering.geometri import Ruta, inom, mitt
from kommunhandlingar.konvertering.rutnat import ar_hel, gar_inte_ihop
from kommunhandlingar.konvertering.text import TAL

Tabeller = list[Table]
LINJEBREDD = 2
ENHET = r"%|kr|tkr|mkr|mnkr|mdkr|st"
# Ett tal, med eller utan parentes och enhet.
TALET = rf"\(?[-−–+]?\d+(?:[ \xa0]\d{{3}})*(?:[,.]\d+)?\)?(?: ?(?:{ENHET}))?"
TALRAD = re.compile(rf"{TALET}|[-−–]", re.IGNORECASE)
# En etikett på ett eller två ord utan siffror följd av ett tal.
ETIKETT_OCH_TAL = re.compile(rf"[^\d\s]+(?: [^\d\s]+)? {TALET}", re.IGNORECASE)
VARDE = re.compile(r"[-−–+]?\d+(?:[,.]\d+)?%?|[-−–]")
SKILJE = re.compile(r"\s+/\s+|[\s()]+")
# En fotnotsstjärna direkt efter en siffra, som i `4 078*`.
FOTNOT = re.compile(r"(?<=\d)\*+(?!\d)")


def sakra(sida: Page, ord_: list[dict]) -> tuple[Tabeller, Tabeller, Tabeller]:
    """De säkra tabellerna, de som fälldes för att en cell rymmer flera
    tal, och rutnäten som inte går ihop (#319)."""
    linjer = linjerna(sida)
    if len(linjer) < 2:
        return [], [], []
    funna = sida.find_tables(bara_linjerna(linjer))
    hela = [t for t in funna if ar_hel(t, ord_)]
    brutna = [t for t in funna if gar_inte_ihop(t, ord_)]
    fallda = [t for t in hela if rymmer_flera_tal(t, ord_)]
    return [t for t in hela if t not in fallda], fallda, brutna


def bara_linjerna(linjer: list[dict]) -> dict:
    """pdfplumbers inställning för att bara se de givna linjerna."""
    return {
        "vertical_strategy": "explicit",
        "horizontal_strategy": "explicit",
        "explicit_vertical_lines": linjer,
        "explicit_horizontal_lines": linjer,
    }


def linjerna(sida: Page) -> list[dict]:
    """Sidans linjer, smala rutor och kanterna där fyllda rutor möts."""
    smala = [r for r in sida.rects if smal(r)]
    ytor = [r for r in sida.rects if r["fill"] and not smal(r)]
    return sida.lines + smala + rutkanter.gemensamma(ytor)


def smal(ruta: dict) -> bool:
    return min(ruta["width"], ruta["height"]) <= LINJEBREDD


def rymmer_flera_tal(tabell: Table, ord_: list[dict]) -> bool:
    if any(flera_tal(c) for rad in rader(tabell) for c in rad):
        return True
    i_cell = ([o for o in ord_ if inom(mitt(o), c)] for c in tabell.cells)
    return any(map(flera_falt, i_cell))


def flera_tal(cell: str) -> bool:
    rader_ = [FOTNOT.sub("", r).strip() for r in cell.split("\n")]
    med_tal = sum(
        1 for r in rader_ if TALRAD.fullmatch(r) or ETIKETT_OCH_TAL.fullmatch(r)
    )
    return med_tal > 1 or any(map(flera_pa_raden, rader_))


def flera_pa_raden(rad: str) -> bool:
    delar = [d for d in SKILJE.split(rad) if d and not enhet(d)]
    return (
        len(delar) > 1
        and all(VARDE.fullmatch(d) for d in delar)
        and not TAL.fullmatch(" ".join(delar).replace(".", ","))
    )


def flera_falt(ord_: list[dict]) -> bool:
    """Två fält på samma rad i cellen som var för sig är ett tal eller ett
    streck."""
    for rad in radvis(ord_):
        if sum(1 for f in falt(rad, dela_tvetydiga=True) if talfalt(f.text)) > 1:
            return True
    return False


def talfalt(text: str) -> bool:
    """Ett tal eller ett streck, med eller utan fotnotsstjärna."""
    return TALRAD.fullmatch(FOTNOT.sub("", text)) is not None


def enhet(text: str) -> bool:
    return re.fullmatch(ENHET, text, re.I) is not None


def forsta_med_text(rader: list[list[str]]) -> int:
    """Tabellens första kolumn med text, där etiketterna står."""
    return next(i for i in range(len(rader[0])) if any(r[i] for r in rader))


def siffra(text: str) -> bool:
    return any(c.isdigit() for c in text)


def i_tabell(objekt: dict, rutor: list[Ruta]) -> bool:
    """Ett tecken vars mitt ligger i någon av tabellernas rutor."""
    if objekt.get("object_type") != "char":
        return False
    return any(inom(mitt(objekt), ruta) for ruta in rutor)


def kanter(tabell: Table) -> tuple[float, ...]:
    """Kolumnernas vänsterkanter och tabellens högerkant."""
    return (*(k.bbox[0] for k in tabell.columns), tabell.bbox[2])


def rader(tabell: Table) -> list[list[str]]:
    return [[cell or "" for cell in rad] for rad in tabell.extract()]
