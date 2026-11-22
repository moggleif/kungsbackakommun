"""Krav: K5 i docs/02-KRAV.md, ADR-0028 och ADR-0029. Test:
tests/test_delade.py och tests/test_delade_kolumner.py.

En tabell med linjer där en cell rymmer mer än ett tal delas, i stället
för att fällas, när det går ihop: kolumnerna efter de lodräta linjer som
finns i någon rad och efter tal i linje (`talkolumner.py`), och raderna
efter rutornas textrader
(docs/03-ARKITEKTUR.md#tabeller-med-linjer-och-flera-tal-i-en-cell).
"""

from itertools import pairwise

from pdfplumber.table import Table

from kommunhandlingar.konvertering import talkolumner
from kommunhandlingar.konvertering.delade_rader import Platser, dela
from kommunhandlingar.konvertering.falt import falt, radvis
from kommunhandlingar.konvertering.geometri import Ruta, inom, mitt
from kommunhandlingar.konvertering.ombrutna import ombruten
from kommunhandlingar.konvertering.sammanslagna import I_LINJE, cellens, kolumn

Granser = tuple[float, ...]


def tabell(t: Table, ord_: list[dict]) -> tuple[list[list[str]], Granser] | None:
    """Raderna, och kolumnernas vänsterkanter och tabellens högerkant
    (K19); None när tabellen inte går att dela, eller när gränserna efter
    talen ger rader utan etikett."""
    if any(over_linje(o, t.cells) for o in ord_ if inom(mitt(o), t.bbox)):
        return None
    linjer = kolumngranser(t)
    granser = tuple(sorted({*linjer, *talkolumner.granser(falten(t, ord_, linjer))}))
    rader = alla_rader(t, ord_, granser)
    if rader is None:
        return None
    utan_etiketter = granser != linjer and etiketter_saknas(t, ord_, rader)
    return None if utan_etiketter or ombruten(rader) else (rader, granser)


def etiketter_saknas(t: Table, ord_: list[dict], rader: list[list[str]]) -> bool:
    """Gränserna efter talen lämnar etiketterna utanför tabellen eller
    rader utan etikett."""
    utanfor = talkolumner.etiketter_utanfor(t.bbox, ord_)
    return utanfor or not talkolumner.etiketterade(rader)


def over_linje(o: dict, celler: list[Ruta]) -> bool:
    """Ett ord vars tecken står i olika celler, som en etikett i ett
    diagram vars rutnät pdfplumber läser som en tabell."""
    i_celler = {
        next((i for i, c in enumerate(celler) if inom(mitt(t), c)), None)
        for t in o["chars"]
    }
    return len(i_celler - {None}) > 1


def alla_rader(t: Table, ord_: list[dict], granser: Granser) -> list[list[str]] | None:
    """Tabellens rader, var och en delad; None när en rad inte går att dela."""
    rader: list[list[str]] = []
    for nr, rad in enumerate(t.rows):
        placerat = placera(rad.cells, ord_, granser)
        delrader = None if placerat is None else dela(*placerat, forsta=nr == 0)
        if delrader is None:
            return None
        rader += delrader
    return rader


def falten(t: Table, ord_: list[dict], linjer: Granser) -> list[talkolumner.Rader]:
    """Tabellens fält textrad för textrad, för varje kolumn mellan linjerna."""
    rader = [falt(r, True) for r in radvis([o for o in ord_ if inom(mitt(o), t.bbox)])]
    return [
        [[f for f in r if kolumn(f.x0, f.x1, (vanster, hoger)) == 0] for r in rader]
        for vanster, hoger in pairwise(linjer)
    ]


def kolumngranser(t: Table) -> Granser:
    alla = sorted({x for c in t.cells for x in (c[0], c[2])})
    ut = [alla[0]]
    for x in alla[1:]:
        if x - ut[-1] > I_LINJE:
            ut.append(x)
    return tuple(ut)


def placera(
    celler: list[Ruta | None], ord_: list[dict], granser: Granser
) -> tuple[Platser, set[str]] | None:
    """Radens textrader per kolumn och vilka slags celler den har; None
    om en cell inte går att placera."""
    platser: Platser = [[] for _ in granser[1:]]
    slag = set()
    for cell in filter(None, celler):
        cellens_slag, placerade = cellens(cell, ord_, granser)
        if placerade is None:
            return None
        slag.add(cellens_slag)
        for i, textrad in placerade:
            platser[i].append(textrad)
    return platser, slag
