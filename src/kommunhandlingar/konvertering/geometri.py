"""Krav: K5 och K15 i docs/02-KRAV.md. Test: tests/test_geometri.py.

Rutor och punkter på PDF-sidan, i pdfplumbers koordinater: punkter, inte
bildens pixlar (de har egna rutor i `rapid.py` och `tsv.py`), med x åt höger
och y nedåt från sidans överkant. En ruta är `(x0, top, x1, bottom)`. En
punkt på rutans kant räknas som inom den.
"""

Punkt = tuple[float, float]
Ruta = tuple[float, float, float, float]


def ruta(objekt: dict) -> Ruta:
    return (objekt["x0"], objekt["top"], objekt["x1"], objekt["bottom"])


def mitt(objekt: dict) -> Punkt:
    return ((objekt["x0"] + objekt["x1"]) / 2, (objekt["top"] + objekt["bottom"]) / 2)


def mitt_av(r: Ruta) -> Punkt:
    return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)


def inom(punkt: Punkt, r: Ruta) -> bool:
    return r[0] <= punkt[0] <= r[2] and r[1] <= punkt[1] <= r[3]


def omslutande(rutor: list[Ruta]) -> Ruta:
    return (
        min(r[0] for r in rutor),
        min(r[1] for r in rutor),
        max(r[2] for r in rutor),
        max(r[3] for r in rutor),
    )
