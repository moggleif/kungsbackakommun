"""Krav: K20 i docs/02-KRAV.md, ADR-0025. Test: tests/test_facit.py.

Raderna i en CSV mot raderna i facittabellerna på samma sidor: vilka som
stämmer, vilka som är fel och vilka tabeller som inte finns i facit
(docs/03-ARKITEKTUR.md#facit-för-konverteringen).
"""

from kommunhandlingar.facit.lasa import Tabell
from kommunhandlingar.facit.rader import lika, siffror, talrad
from kommunhandlingar.facit.utfall import Utfall
from kommunhandlingar.konvertering.flersidiga import Sammanslagen

type Traff = tuple[str, int, bool]


def granska(t: Sammanslagen, facits: list[Tabell], utfall: Utfall):
    kandidater = [
        f for f in facits if t.sida <= f.sista_sida and f.sida <= t.sista_sida
    ]
    if not kandidater:
        if any(map(talrad, t.rader)):
            utfall.rakna("pahittade", [f"tabell {t.namn}"])
        return
    rubrik = rubriken(t, kandidater, utfall)
    anvanda = {(f, i) for f, i, _ in utfall.traffar}
    fel, nya = kroppen(t.rader[len(rubrik) :], kandidater, anvanda)
    utfall.traffar |= {(f, i, t.namn) for f, i in nya}
    fel = rubrikens_fel(rubrik, kandidater) + fel
    utfall.rakna("fel_rader", [f"{t.namn} {rad}" for rad in fel])


def rubriken(t: Sammanslagen, kandidater: list[Tabell], utfall: Utfall) -> list:
    """Raderna före den första dataraden, som sparas för tabellen den hör till."""
    forsta = forsta_dataraden(t.rader, kandidater)
    if forsta is None:
        return []
    namn = traffa(t.rader[forsta], kandidater, set())[0]
    utfall.rubriker.setdefault(namn, t.rader[:forsta])
    return t.rader[:forsta]


def forsta_dataraden(rader: list[list[str]], kandidater: list[Tabell]) -> int | None:
    for i, rad in enumerate(rader):
        traff = traffa(rad, kandidater, set()) if talrad(rad) else None
        if traff and traff[2]:
            return i
    return None


def traffa(rad: list[str], kandidater: list[Tabell], anvanda: set) -> Traff | None:
    """Den första facitraden som stämmer och inte redan använts."""
    facitrader = ((f, i, r) for f in kandidater for i, r in enumerate(f.rader))
    for f, i, facitrad in facitrader:
        if (f.namn, i) not in anvanda and lika(rad, facitrad):
            return f.namn, i, i >= f.rubrikrader
    return None


def kroppen(rader: list[list[str]], kandidater: list[Tabell], anvanda: set):
    """Raderna med tal efter rubriken: de som inte stämmer med en oanvänd
    rad i facit, och de datarader i facit som hittades."""
    fel, nya = [], set()
    for rad in filter(talrad, rader):
        traff = traffa(rad, kandidater, anvanda | nya)
        if traff is None:
            fel.append(rad)
        elif traff[2]:
            nya.add(traff[:2])
    return fel, nya


def rubrikens_fel(rubrik: list[list[str]], kandidater: list[Tabell]) -> list:
    """En rad med tal före den första dataraden får bara ha rubrikens tal."""
    tillatna = set(siffror([r for f in kandidater for r in f.rader[: f.rubrikrader]]))
    return [r for r in rubrik if talrad(r) and not set(siffror([r])) <= tillatna]
