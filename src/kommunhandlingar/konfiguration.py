"""Krav: K1, K18, K22, K23, K49, K57 och K88 i docs/02-KRAV.md, ADR-0019, ADR-0032,
ADR-0039, ADR-0072, ADR-0080, ADR-0109 och ADR-0113.
Test: tests/test_konfiguration.py, tests/test_gruppmoten.py och
tests/test_meetingsplus.py."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from kommunhandlingar import schema
from kommunhandlingar.adaptrar import kallor as adaptrarna
from kommunhandlingar.fel import Konfigurationsfel
from kommunhandlingar.gruppmote import Gruppmote, gruppmote_av
from kommunhandlingar.kandidat import TYPORDNING
from kommunhandlingar.organ import Organ, kontrollera_grupper, organen

KOMMUNFALT = {
    "namn",
    "organ",
    "kalla",
    "omkonvertera",
    "grupper",
    "gruppmote",
    "sidor_med_text",
    "sammantradessidor",
}


@dataclass(frozen=True)
class Kommun:
    id: str
    namn: str
    organ: tuple[Organ, ...]
    # Alla källor, i kommunfilens ordning (ADR-0109).
    kallor: tuple[adaptrarna.Kalla, ...]
    omkonvertera: bool
    # Grupperna på kommunens sida, i sin ordning (K39).
    grupper: tuple[str, ...] = ()
    # Partiernas gruppmöten inför ett organs sammanträden (K49).
    gruppmote: Gruppmote | None = None
    # Typerna som visar texten på dokumentets sida; None är alla (K18).
    sidor_med_text: tuple[str, ...] | None = None
    # Första året sammanträdena får en sida punkt för punkt; None är alla
    # år (K54).
    sammantradessidor: int | None = None

    def organnamn(self, organ_id: str) -> str:
        return next(o.namn[0] for o in self.organ if o.id == organ_id)

    def organnamnen(self) -> dict[str, str]:
        return {o.id: o.namn[0] for o in self.organ}


def las(sokvag: Path) -> Kommun:
    with sokvag.open("rb") as fil:
        return tolka(sokvag.stem, tomllib.load(fil))


def tolka(kommun_id: str, data: dict) -> Kommun:  # undantag: följden avgör felet
    schema.kontrollera_falt(data, KOMMUNFALT, "kommunen")
    namn = schema.varde(data, "namn", str, "kommunen")
    organ = organen(poster(data, "organ"))
    grupper = schema.textlista(data, "grupper", "kommunen")
    kontrollera_grupper(organ, grupper)
    organ_id = [o.id for o in organ]
    kallor = [kalla_av(p, i, organ_id) for i, p in enumerate(poster(data, "kalla"), 1)]
    omkonvertera = schema.valfritt(data, "omkonvertera", bool, "kommunen") or False
    gruppmote = schema.valfritt(data, "gruppmote", dict, "kommunen")
    return Kommun(
        id=schema.katalognamn(kommun_id, "kommunen"),
        namn=namn,
        organ=organ,
        kallor=tuple(kallor),
        omkonvertera=omkonvertera,
        grupper=grupper,
        gruppmote=None if gruppmote is None else gruppmote_av(gruppmote, organ_id),
        sidor_med_text=sidor_med_text_av(data),
        sammantradessidor=schema.valfritt(data, "sammantradessidor", int, "kommunen"),
    )


def sidor_med_text_av(data: dict) -> tuple[str, ...] | None:
    if "sidor_med_text" not in data:
        return None
    typer = schema.textlista(data, "sidor_med_text", "kommunen")
    if okanda := set(typer) - set(TYPORDNING):
        raise Konfigurationsfel(f"kommunen: okänd typ i sidor_med_text: {min(okanda)}")
    return typer


def poster(data: dict, falt: str) -> list[dict]:
    lista = schema.varde(data, falt, list, "kommunen")
    if not lista or not all(isinstance(post, dict) for post in lista):
        raise Konfigurationsfel(f"kommunen: {falt} ska vara en lista med tabeller")
    return lista


def kalla_av(post: dict, nummer: int, organ_id: list[str]) -> adaptrarna.Kalla:
    var = f"kalla {nummer}"
    adapter = schema.varde(post, "adapter", str, var)
    if adapter not in adaptrarna.ADAPTRAR:
        raise Konfigurationsfel(f"{var}: okänd adapter {adapter!r}")
    tolkning, omslag = adaptrarna.ADAPTRAR[adapter]
    return omslag(tolkning(post, organ_id, var))
