"""Krav: K45 i docs/02-KRAV.md, ADR-0068. Test: tests/test_sitevision_projekt.py.

Kommunens lista med projekt: listan och dess bläddringssidor ger
projektsidorna, och en sida en nivå under en projektsida är ett eget
projekt. Varje fil på en projektsida blir handlingar under organet,
daterad med dagen den lades upp och namngiven efter projektet och filen.
"""

import re
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import PurePosixPath
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from kommunhandlingar.adaptrar.gemensamt import adresser
from kommunhandlingar.adaptrar.sitevision_html import (
    NEDLADDNING,
    forekomster,
    kallnyckel,
)
from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.kandidat import Avvisad, Fynd, Kandidat
from kommunhandlingar.plats import namn_av

TIDSZON = ZoneInfo("Europe/Stockholm")


def projektsidor(lista: str, hamta: Callable[[str], str]) -> list[str]:
    """Listans projekt i sidornas ordning."""
    sidor, projekt, i = [lista], [], 0
    while i < len(sidor):
        for adress in adresser(hamta(sidor[i]), sidor[i]):
            if bladdring(lista, adress) and adress not in sidor:
                sidor.append(adress)
            elif ar_projekt(lista, adress) and adress not in projekt:
                projekt.append(adress)
        i += 1
    return projekt


def bladdring(lista: str, adress: str) -> bool:
    """Listans sida med ett sidnummer från 2, `?<parameter>=2`; sida 1 är
    listan själv, och filtren har fler parametrar."""
    sokvag, _, fraga = adress.partition("?")
    traff = re.fullmatch(r"[^&=]+=(\d+)", fraga)
    return sokvag == lista and bool(traff) and int(traff[1]) > 1


# En sida direkt under listan, eller under en projektsida.
def ar_projekt(ovan: str, adress: str) -> bool:
    delar = urlsplit(adress)
    sokvag = PurePosixPath(delar.path)
    return not delar.query and str(sokvag.parent) == urlsplit(ovan).path.rstrip("/")


# Ett fel här stoppar aldrig upptäckten (ADR-0068): sidan hoppas över och
# står i sammanfattningen, så att mötena hämtas ändå.
FEL = (Hamtfel, ValueError, KeyError)


def upptack(projekt: dict[str, str], hamta: Callable[[str], str]) -> Fynd:
    """En fil som står på flera projektsidor är den första sidans."""
    fynd = sum((listan(o, lista, hamta) for o, lista in projekt.items()), Fynd())
    forsta: dict[str, Kandidat] = {}
    for kandidat in fynd.kandidater:
        forsta.setdefault(kandidat.kallnyckel, kandidat)
    return replace(fynd, kandidater=list(forsta.values()))


def listan(organ: str, lista: str, hamta: Callable[[str], str]) -> Fynd:
    try:
        sidor = projektsidor(lista, hamta)
    except FEL as fel:
        return Fynd(avvisade=[Avvisad(lista, "", f"listan: {fel}")])
    return sum((med_sidorna_under(organ, sida, hamta) for sida in sidor), Fynd())


def med_sidorna_under(organ: str, sida: str, hamta: Callable[[str], str]) -> Fynd:
    """Projektsidans filer och filerna på sidorna en nivå under den, som
    räknas som egna projekt. Sidor längre ner läses inte."""
    try:
        html = hamta(sida)
        fynd = Fynd(kandidater_pa(organ, sida, html))
    except FEL as fel:
        return Fynd(avvisade=[Avvisad(sida, "", f"projektsidan: {fel}")])
    under = dict.fromkeys(a for a in adresser(html, sida) if ar_projekt(sida, a))
    return sum((projektsidan(organ, u, hamta) for u in under), fynd)


def projektsidan(organ: str, sida: str, hamta: Callable[[str], str]) -> Fynd:
    try:
        return Fynd(kandidater_pa(organ, sida, hamta(sida)))
    except FEL as fel:
        return Fynd(avvisade=[Avvisad(sida, "", f"projektsidan: {fel}")])


def kandidater_pa(organ: str, sida: str, html: str) -> list[Kandidat]:
    projektet = PurePosixPath(urlsplit(sida).path).name
    return [
        Kandidat(
            organ=organ,
            datum=upplagd(f.adress),
            typ="handlingar",
            url=f.adress,
            kalla=sida,
            kallnyckel=kallnyckel(f),
            filnamn=f.filnamn,
            namn=namn_av(f"{projektet} {PurePosixPath(f.filnamn).stem}"),
        )
        for f in forekomster(html, sida)
    ]


def upplagd(adress: str) -> date:
    """Dagen i Sitevisions tidsstämpel, millisekunder sedan 1970, i svensk tid."""
    millisekunder = int(NEDLADDNING.match(adress)[2])
    return datetime.fromtimestamp(millisekunder / 1000, UTC).astimezone(TIDSZON).date()
