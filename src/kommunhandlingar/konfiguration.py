"""Krav: K1, K18, K22, K23, K49 och K57 i docs/02-KRAV.md, ADR-0019, ADR-0032,
ADR-0039, ADR-0072 och ADR-0080.
Test: tests/test_konfiguration.py, tests/test_gruppmoten.py och
tests/test_meetingsplus.py."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from kommunhandlingar import schema
from kommunhandlingar.adaptrar import episerver, meetingsplus, sitevision
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
}


@dataclass(frozen=True)
class Kommun:
    id: str
    namn: str
    organ: tuple[Organ, ...]
    kallor: tuple[sitevision.Kalla, ...]
    omkonvertera: bool
    # Källor som bara finns i Internet Archive (ADR-0039).
    arkivkallor: tuple[episerver.Kalla, ...]
    # Grupperna på kommunens sida, i sin ordning (K39).
    grupper: tuple[str, ...] = ()
    # Partiernas gruppmöten inför ett organs sammanträden (K49).
    gruppmote: Gruppmote | None = None
    # Källor på Formpipe Meetings Plus (ADR-0080).
    meetingsplus_kallor: tuple[meetingsplus.Kalla, ...] = ()
    # Typerna som visar texten på dokumentets sida; None är alla (K18).
    sidor_med_text: tuple[str, ...] | None = None

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
        kallor=av_slag(kallor, sitevision.Kalla),
        omkonvertera=omkonvertera,
        arkivkallor=av_slag(kallor, episerver.Kalla),
        grupper=grupper,
        gruppmote=None if gruppmote is None else gruppmote_av(gruppmote, organ_id),
        meetingsplus_kallor=av_slag(kallor, meetingsplus.Kalla),
        sidor_med_text=sidor_med_text_av(data),
    )


def av_slag[T](kallor: list, slag: type[T]) -> tuple[T, ...]:
    return tuple(k for k in kallor if isinstance(k, slag))


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


ADAPTRAR = {
    "sitevision": sitevision.kalla_av,
    "episerver": episerver.kalla_av,
    "meetingsplus": meetingsplus.kalla_av,
}


def kalla_av(post: dict, nummer: int, organ_id: list[str]):
    var = f"kalla {nummer}"
    adapter = schema.varde(post, "adapter", str, var)
    if adapter not in ADAPTRAR:
        raise Konfigurationsfel(f"{var}: okänd adapter {adapter!r}")
    return ADAPTRAR[adapter](post, organ_id, var)
