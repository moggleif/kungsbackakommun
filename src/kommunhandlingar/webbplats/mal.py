"""Krav: K26, K27, K35, K71 och K91 i docs/02-KRAV.md, ADR-0044, ADR-0045,
ADR-0056, ADR-0098 och ADR-0114.
Test: tests/test_mal.py, tests/test_fokusomraden.py, tests/test_regionmal.py och
tests/test_omdopta_kommunmal.py.

Läser `mal/<kommun>.csv` och stoppar bygget med raden när den inte går
ihop med kommunfilen och poolen (docs/03-ARKITEKTUR.md#mål-och-direktiv).
"""

from dataclasses import dataclass
from pathlib import Path

from kommunhandlingar.fel import Datafel
from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import radfil
from kommunhandlingar.webbplats.kallprov import Sidlasare, star_pa
from kommunhandlingar.webbplats.malkontroll import Kontroll

KOLUMNER = [
    *("organ", "ar", "slag", "rubrik", "formulering", "status"),
    *("uppfoljning", "bedomning", "kalla", "grupp", "tolkad", "huvudmal"),
]
# Ett fokusområde hör till ett kommunmål och visas under det (ADR-0056).
# Regionmål är en regions fullmäktigemål (ADR-0098).
SLAG = ("nämndmål", "kommunmål", "regionmål", "fokusområde", "direktiv")
FALTEN = (
    ("rubrik", "rubriken"),
    ("formulering", "formuleringen"),
    ("status", "statusen"),
    ("huvudmal", "huvudmålet"),
)


@dataclass(frozen=True)
class Mal:
    organ: str
    ar: int
    slag: str
    rubrik: str
    formulering: str
    status: str
    uppfoljning: str
    bedomning: str
    kalla: str
    grupp: str
    tolkad: str
    huvudmal: str

    @property
    def namn(self) -> tuple[str, str, str]:
        return self.organ, self.slag, self.rubrik.casefold()

    @property
    def spar(self) -> tuple[str, str]:
        return self.organ, (self.grupp or self.rubrik).casefold()

    @property
    def dokument(self) -> str:
        return self.kalla.split("#")[0]

    @property
    def mote(self) -> str:
        return self.kalla.rsplit("/", 1)[0]

    @property
    def fran_protokoll(self) -> bool:
        return self.kalla.rsplit("/", 1)[1].startswith("protokoll")

    @property
    def prognos(self) -> bool:
        return self.uppfoljning == "prognos"


def las(fil: Path, kommun: Kommun, data: Path) -> list[Mal]:
    organ, sidtext, kontroll = radfil.organen(kommun), Sidlasare(data), Kontroll()

    def tolka_och_prova(rad: list[str]) -> Mal:
        mal = tolka(rad, organ, sidtext)
        kontroll.prova(mal)
        return mal

    malen = radfil.las(fil, KOLUMNER, tolka_och_prova)
    try:
        kontroll.grupperna()
        kontroll.huvudmalens_spar()
    except ValueError as fel:
        raise Datafel(f"{fil}: {fel}") from None
    return [kontroll.under_sparet(m) for m in malen]


def tolka(rad: list[str], organ: set[str], sidtext: Sidlasare) -> Mal:
    mal = Mal(rad[0], radfil.ar(rad[1]), *rad[2:])
    radfil.i_kommunfilen(mal.organ, organ)
    if mal.slag not in SLAG:
        raise ValueError(f"slaget {mal.slag!r} är varken {' eller '.join(SLAG)}")
    if (mal.slag == "fokusområde") != bool(mal.huvudmal):
        raise ValueError("ett fokusområde, och bara det, har ett huvudmål")
    sida = sidtext(mal.kalla, mal.organ)
    for falt, namn in FALTEN:
        if not star_pa(getattr(mal, falt), sida):
            raise ValueError(f"{namn} står inte på {mal.kalla}")
    return mal
