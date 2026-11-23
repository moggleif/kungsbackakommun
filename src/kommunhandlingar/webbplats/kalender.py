"""Krav: K22, K49 och K56 i docs/02-KRAV.md, ADR-0032 och ADR-0072.
Test: tests/test_kalenderfil.py, tests/test_kalenderlankar.py och
tests/test_gruppmoten.py.

Läser `kalender/<kommun>.csv` och stoppar bygget med raden när den inte
går ihop med kommunfilen och poolen (docs/03-ARKITEKTUR.md#kalendern), och
lägger till sammanträdenas egna sidor.
"""

import re
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import adresser, radfil

DATUM = re.compile(r"\d{4}-\d{2}-\d{2}")
KOLUMNER = ["organ", "datum", "tid", "plats", "kalla", "osakert"]
# Gruppmötet är inget organ; id:t är inget katalognamn och krockar inte.
GRUPPMOTE = "gruppmöte"


@dataclass(frozen=True)
class Sammantrade:
    organ: str
    datum: date
    tid: str
    plats: str
    kalla: str
    osakert: str
    # Sammanträdets sida i kommunens katalog (K56); tomt utan sida.
    sida: str = ""


def las(fil: Path, kommun: Kommun, data: Path) -> list[Sammantrade]:
    organ = radfil.organen(kommun)
    tolka_unik = radfil.unika(
        lambda rad: tolka(rad, organ, data),
        lambda s: (s.organ, s.datum),
        "organet har redan ett sammanträde dagen",
    )
    return radfil.las(fil, KOLUMNER, tolka_unik)


def tolka(rad: list[str], organ: set[str], data: Path) -> Sammantrade:
    if not DATUM.fullmatch(rad[1]):
        raise ValueError(f"datumet {rad[1]!r} är inte ÅÅÅÅ-MM-DD")
    s = Sammantrade(rad[0], date.fromisoformat(rad[1]), *rad[2:])
    radfil.i_kommunfilen(s.organ, organ)
    if not (s.kalla.startswith("https://") or i_poolen(s.kalla, data)):
        raise ValueError(f"källan {s.kalla!r} är inget dokument i poolen")
    if s.datum.weekday() >= 5 and not s.osakert:
        raise ValueError(f"{s.datum} är en lördag eller söndag, inte märkt osäkert")
    return s


# Sammanträdets sida ligger bredvid dess katalog, <organ>/<år>/<datum>.html
# (K54), och skrivs innan kalendern byggs (bygg.py).
def med_sidor(sammantraden: list[Sammantrade], katalog: Path) -> list[Sammantrade]:
    return [med_sida(s, katalog) for s in sammantraden]


def med_sida(s: Sammantrade, katalog: Path) -> Sammantrade:
    adress = adresser.sammantrade(s.organ, s.datum.isoformat())
    return replace(s, sida=adress) if (katalog / adress).is_file() else s


# Ett dokument ligger på <organ>/<år>/<datum>/<typ>.md (ADR-0003).
def i_poolen(kalla: str, data: Path) -> bool:
    delar = kalla.split("/")
    return len(delar) == 4 and kalla.endswith(".md") and (data / kalla).is_file()
