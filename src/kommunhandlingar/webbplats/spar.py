"""Krav: K36, K37 och K38 i docs/02-KRAV.md, ADR-0057, ADR-0058 och ADR-0059.
Test: tests/test_lokalbehov.py, tests/test_initiativ.py,
tests/test_handlingsplaner.py.

Läser en spårfil, `<slag>/<kommun>.csv`: en rad per steg en sak tar över
tid – ett lokalbehov, ett initiativärende, en handlingsplan – med en sida
i ett dokument i poolen som källa. Källan får vara vilket organs dokument som helst. Vad
som skiljer slagen åt – kolumnens namn, faserna, värdena och sidans text –
står i slagets fil, listade i `slagen.py`. Bygget stoppas med raden
när den inte går ihop med kommunfilen och poolen (docs/03-ARKITEKTUR.md#lokalbehov och
#initiativärenden och #handlingsplaner).
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import radfil
from kommunhandlingar.webbplats.kallprov import Sidlasare, Sidtext, provbar
from kommunhandlingar.webbplats.partier import star_pa


@dataclass(frozen=True)
class Slag:
    id: str
    kolumn: str
    rubrik: str
    sak: str
    saker: str
    antal: str
    # Fasens ikon och vad den betyder, i fasernas ordning.
    faser: dict[str, tuple[str, str]]
    inledning: str
    metod: str
    adr: str
    # Faser vars värde måste passa mönstret, och vad det då är.
    varden: dict[str, tuple[str, str]] = field(default_factory=dict)
    # Fasen vars värde står som siffra i ikonen.
    siffra: str = ""
    # Fasen vars senaste år ger urvalet "I <rubrik> <år>".
    aktuell: str = ""
    # Fasen vars värde, när det finns, säger vem som står bakom saken.
    avsandare: str = ""
    # Fasen vars källa är själva saken, som kortet länkar till.
    planen: str = ""

    @property
    def kolumner(self) -> list[str]:
        return ["organ", self.kolumn, "ar", "fas", "varde", "text", "kalla", "tolkad"]


@dataclass(frozen=True)
class Steg:
    organ: str
    namn: str
    ar: int
    fas: str
    varde: str
    text: str
    kalla: str
    tolkad: str

    @property
    def kallans_organ(self) -> str:
        return self.kalla.split("/", 1)[0]


@dataclass(frozen=True)
class Underlag:
    organ: set[str]
    sidtext: Sidtext


def lasare(slag: Slag) -> Callable[[Path, Kommun, Path], list[Steg]]:
    def las(fil: Path, kommun: Kommun, data: Path) -> list[Steg]:
        underlag = Underlag(radfil.organen(kommun), Sidlasare(data))
        tolka_unik = radfil.unika(
            lambda rad: tolka(rad, slag, underlag),
            lambda s: (s.organ, s.namn, s.fas, s.kalla),
            "steget står redan med samma källa",
        )
        return radfil.las(fil, slag.kolumner, tolka_unik)

    return las


def tolka(rad: list[str], slag: Slag, underlag: Underlag) -> Steg:
    steg = Steg(rad[0], rad[1], radfil.ar(rad[2]), *rad[3:])
    radfil.i_kommunfilen(steg.organ, underlag.organ)
    if not steg.namn or not steg.text:
        raise ValueError(f"{slag.kolumn} och texten får inte vara tomma")
    if steg.fas not in slag.faser:
        raise ValueError(f"fasen {steg.fas!r} är inte en av {', '.join(slag.faser)}")
    kontrollera_varde(steg, slag)
    radfil.tolkad(steg.tolkad)
    kontrollera_sidan(steg, slag, kallans_sida(steg, underlag))
    return steg


def kallans_sida(steg: Steg, underlag: Underlag) -> str:
    if steg.kallans_organ not in underlag.organ:
        raise ValueError(f"källan {steg.kalla!r} är inget organs dokument")
    return underlag.sidtext(steg.kalla, steg.kallans_organ)


# Avsändaren får stå som partiets namn, eller Alliansen som de fyra
# partiernas förkortningar, minst tre av dem, på sidan (partier.py).
def kontrollera_sidan(steg: Steg, slag: Slag, sidan: str) -> None:
    if provbar(steg.text) not in sidan:
        raise ValueError(f"texten står inte på {steg.kalla}")
    avsandare = steg.fas == slag.avsandare
    if not (star_pa(steg.varde, sidan) if avsandare else provbar(steg.varde) in sidan):
        raise ValueError(f"värdet står inte på {steg.kalla}")


def kontrollera_varde(steg: Steg, slag: Slag) -> None:
    if steg.fas not in slag.varden:
        return
    monster, ar = slag.varden[steg.fas]
    if not re.fullmatch(monster, steg.varde):
        raise ValueError(f"värdet {steg.varde!r} för {steg.fas} är inte {ar}")
