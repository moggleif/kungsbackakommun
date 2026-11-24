"""Krav: K5 och K89 i docs/02-KRAV.md, ADR-0031 och ADR-0111.
Test: tests/test_rutnat.py.

Om ett rutnät av linjer går ihop till en tabell: minst två rader och två
kolumner, och varje ord inom dess yta har mittpunkten i en cell. Ett
rutnät med ett ord utanför varje cell går inte ihop; dess text blir
löptext med kolumnerna ihopflätade, och sidan märks `tabell-osaker`.
"""

from pdfplumber.table import Table

from kommunhandlingar.konvertering.geometri import Punkt, inom, mitt


def ar_hel(tabell: Table, ord_: list[dict]) -> bool:
    inne = inom_ytan(tabell, ord_)
    return rutnat(tabell) and bool(inne) and all(i_cell(tabell, p) for p in inne)


def brutet(tabell: Table, ord_: list[dict]) -> bool:
    inne = inom_ytan(tabell, ord_)
    return rutnat(tabell) and not all(i_cell(tabell, p) for p in inne)


def rutnat(tabell: Table) -> bool:
    return len(tabell.rows) > 1 and max(len(rad.cells) for rad in tabell.rows) > 1


def inom_ytan(tabell: Table, ord_: list[dict]) -> list[Punkt]:
    return [mitt(o) for o in ord_ if inom(mitt(o), tabell.bbox)]


def i_cell(tabell: Table, punkt: Punkt) -> bool:
    return any(inom(punkt, c) for c in tabell.cells)
