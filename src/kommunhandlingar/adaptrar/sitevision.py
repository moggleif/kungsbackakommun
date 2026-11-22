"""Krav: K1, K2, K16 och K45 i docs/02-KRAV.md, ADR-0011, ADR-0027, ADR-0062
och ADR-0068.
Test: tests/test_sitevision.py."""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta

from kommunhandlingar import monster, schema
from kommunhandlingar.adaptrar.gemensamt import organsidor
from kommunhandlingar.adaptrar.sitevision_html import Forekomst, forekomster, kallnyckel
from kommunhandlingar.fel import IngenKandidat, Konfigurationsfel
from kommunhandlingar.kandidat import Avvisad, Fynd, Kallsida, Kandidat

FALT = {
    "adapter",
    "monster",
    "manader",
    "sidor",
    "rubrik",
    "rattelser",
    "wayback",
    "projekt",
}
# Ett möte som flyttas, flyttas några dagar (ADR-0062).
FLYTTAT_MOTE = timedelta(days=7)


@dataclass(frozen=True)
class Kalla:
    sidor: dict[str, str]
    rubrik: re.Pattern
    monster: tuple[monster.Monster, ...]
    manader: tuple[str, ...]
    rattelser: dict[str, date]
    wayback: tuple[str, ...]
    # Organet och adressen till kommunens lista med projekt (ADR-0068).
    projekt: dict[str, str]
    # Sätts av arkivets adapter, inte av kommunfilen.
    arkiv: bool = False


def kalla_av(post: dict, organ_id: list[str], var: str) -> Kalla:
    schema.kontrollera_falt(post, FALT, var)
    monsterposter = schema.varde(post, "monster", list, var)
    motessidor = organsidor(schema.varde(post, "sidor", dict, var), organ_id, var)
    return Kalla(
        motessidor,
        monster.datummonster(schema.varde(post, "rubrik", str, var), "rubrik", var),
        monster.filnamnsmonster(monsterposter, var),
        monster.manader(post, var),
        monster.rattelser(
            schema.valfritt(post, "rattelser", dict, var) or {}, "sitevision", var
        ),
        arkivorgan(schema.textlista(post, "wayback", var), motessidor, var),
        organsidor(schema.valfritt(post, "projekt", dict, var) or {}, organ_id, var),
    )


def arkivorgan(
    organ: tuple[str, ...], motessidor: dict[str, str], var: str
) -> tuple[str, ...]:
    if okanda := set(organ) - motessidor.keys():
        raise Konfigurationsfel(f"{var}: wayback {sorted(okanda)} saknar mötessida")
    return organ


def upptack(kalla: Kalla, html_per_sida: dict[str, str]) -> Fynd:
    return las(kalla, [(o, a, html_per_sida[a]) for o, a in kalla.sidor.items()])


def las(kalla: Kalla, sidor: list[tuple[str, str, str]]) -> Fynd:
    """Sidorna som organ, adress och HTML; den första sidan med en fil gäller."""
    kandidater: dict[str, Kandidat] = {}
    avvisade: dict[str, Avvisad] = {}
    for sida, fil in filerna(sidor):
        nyckel = kallnyckel(fil)
        if nyckel in kandidater:
            continue
        try:
            kandidater[nyckel] = kandidat(kalla, sida, fil)
            avvisade.pop(nyckel, None)
        except IngenKandidat as fel:
            avvisade.setdefault(nyckel, Avvisad(sida.adress, fil.filnamn, str(fel)))
    return Fynd(list(kandidater.values()), list(avvisade.values()))


def filerna(sidor: list[tuple[str, str, str]]) -> Iterator[tuple[Kallsida, Forekomst]]:
    return ((Kallsida(o, a), f) for o, a, html in sidor for f in forekomster(html, a))


def kandidat(kalla: Kalla, sida: Kallsida, forekomst: Forekomst) -> Kandidat:
    nyckel = kallnyckel(forekomst)
    tolkning = monster.tolka(kalla.monster, forekomst.filnamn, kalla.manader)
    datum = kalla.rattelser.get(nyckel) or motesdatum(
        kalla, tolkning.datum, forekomst.rubrik
    )
    return Kandidat(
        organ=sida.organ,
        datum=datum,
        typ=tolkning.typ,
        url=forekomst.adress,
        kalla=sida.adress,
        kallnyckel=nyckel,
        filnamn=forekomst.filnamn,
    )


def motesdatum(kalla: Kalla, filnamnsdatum: date | None, rubriktext: str) -> date:
    traff = kalla.rubrik.search(rubriktext)
    rubriksdatum = monster.datum_av(traff.groupdict(), kalla.manader) if traff else None
    if (
        filnamnsdatum
        and rubriksdatum
        and filnamnsdatum != rubriksdatum
        and not under_annat_mote(kalla, filnamnsdatum, rubriksdatum)
    ):
        raise IngenKandidat(f"filnamnet säger {filnamnsdatum}, rubriken {rubriksdatum}")
    if not (filnamnsdatum or rubriksdatum):
        raise IngenKandidat("varken filnamnet eller rubriken har ett datum")
    return filnamnsdatum or rubriksdatum


def under_annat_mote(kalla: Kalla, filnamnsdatum: date, rubriksdatum: date) -> bool:
    """I arkivets kopior står filer ibland under ett annat möte samma år
    (ADR-0062); då gäller filnamnet."""
    return (
        kalla.arkiv
        and filnamnsdatum.year == rubriksdatum.year
        and abs(filnamnsdatum - rubriksdatum) > FLYTTAT_MOTE
    )
