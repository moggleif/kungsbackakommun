"""Krav: K28 i docs/02-KRAV.md, ADR-0046. Test: tests/test_uppfoljningar.py.

Läser `uppfoljningar/<kommun>.csv`: en rad per paragraf i ett organs
protokoll där nämnden tar upp sina mål, en uppföljning eller en dragning.
Bygget stoppas med raden när den inte går ihop med kommunfilen och poolen.
"""

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import radfil
from kommunhandlingar.webbplats.kallprov import Sidlasare, Sidtext, star_pa

KOLUMNER = ["organ", "datum", "paragraf", "slag", "rubrik", "kalla"]
SLAG = ("uppföljning", "dragning")


@dataclass(frozen=True)
class Uppfoljning:
    organ: str
    datum: str
    paragraf: str
    slag: str
    rubrik: str
    kalla: str

    @property
    def ar(self) -> int:
        return int(self.datum[:4])


def las(fil: Path, kommun: Kommun, data: Path) -> list[Uppfoljning]:
    organ, sidtext = radfil.organen(kommun), Sidlasare(data)
    tolka_unik = radfil.unika(
        lambda rad: tolka(rad, organ, sidtext),
        lambda u: (u.organ, u.datum, u.paragraf),
        "paragrafen står redan i filen",
    )
    return radfil.las(fil, KOLUMNER, tolka_unik)


def tolka(rad: list[str], organ: set[str], sidtext: Sidtext) -> Uppfoljning:
    upp = Uppfoljning(*rad)
    try:
        date.fromisoformat(upp.datum)
    except ValueError:
        raise ValueError(f"datumet {upp.datum!r} är inte ÅÅÅÅ-MM-DD") from None
    radfil.i_kommunfilen(upp.organ, organ)
    if upp.slag not in SLAG:
        raise ValueError(f"slaget {upp.slag!r} är varken {' eller '.join(SLAG)}")
    if not re.fullmatch(r"\d+", upp.paragraf):
        raise ValueError(f"paragrafen {upp.paragraf!r} är inget nummer")
    kontrollera_kalla(upp, sidtext)
    return upp


def kontrollera_kalla(upp: Uppfoljning, sidtext: Sidtext) -> None:
    if not upp.kalla.startswith(f"{upp.organ}/{upp.ar}/{upp.datum}/protokoll"):
        raise ValueError(f"källan {upp.kalla!r} är inte mötets protokoll")
    if not star_pa(upp.rubrik, sidtext(upp.kalla, upp.organ)):
        raise ValueError(f"rubriken står inte på {upp.kalla}")
