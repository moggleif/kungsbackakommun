"""Krav: K49 i docs/02-KRAV.md, ADR-0072. Test: tests/test_gruppmoten.py.

Kommunfilens `[gruppmote]`: vilket organs sammanträden partierna har
gruppmöte inför, på vilken veckodag före och vid vilken tid, och de
kommande gruppmötenas dagar räknade ur sammanträdena.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from kommunhandlingar import schema
from kommunhandlingar.fel import Konfigurationsfel

VECKODAGAR = ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"]


@dataclass(frozen=True)
class Gruppmote:
    fore: str
    veckodag: int
    tid: str

    # Två sammanträden samma vecka ger ett gruppmöte.
    def dagarna(
        self, sammantraden: Iterable[tuple[str, date]], idag: date
    ) -> list[date]:
        dagar = {
            dag
            for organ, datum in sammantraden
            if organ == self.fore and (dag := dagen_fore(datum, self.veckodag)) >= idag
        }
        return sorted(dagar)


def dagen_fore(datum: date, veckodag: int) -> date:
    return datum - timedelta(days=(datum.weekday() - veckodag - 1) % 7 + 1)


def gruppmote_av(post: dict, organ_id: list[str]) -> Gruppmote:
    schema.kontrollera_falt(post, {"fore", "veckodag", "tid"}, "gruppmote")
    fore = schema.varde(post, "fore", str, "gruppmote")
    veckodag = schema.varde(post, "veckodag", str, "gruppmote")
    if fore not in organ_id:
        raise Konfigurationsfel(f"gruppmote: organet {fore!r} finns inte")
    if veckodag not in VECKODAGAR:
        raise Konfigurationsfel(f"gruppmote: {veckodag!r} är ingen veckodag")
    tid = schema.varde(post, "tid", str, "gruppmote")
    return Gruppmote(fore, VECKODAGAR.index(veckodag), tid)
