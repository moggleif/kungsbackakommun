"""Krav: K48 i docs/02-KRAV.md, ADR-0071. Test: tests/test_paragrafer.py.

Ett protokolls text delas vid raderna som inleder en paragraf, `§ 121`,
`BN § 1` eller `§ 121 Dnr GA-2026-00004`. Vilka avsnitt som blir
paragrafer avgör `valda`.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import dropwhile, takewhile
from typing import NamedTuple

from kommunhandlingar.diarienummer import i_huvudet
from kommunhandlingar.paragrafinnehall import beslut, dnr_rader, rubrik
from kommunhandlingar.sidmarkor import SIDA

RUBRIKRAD = re.compile(r"^\s*(?:[A-ZÅÄÖ]{2,4}\s*)?§\s*(\d+)(.*)$")
FORTS = re.compile(r"^[\s,./]*forts", re.IGNORECASE)
DATUM = re.compile(r"\d{4}-\d{2}-\d{2}")
PUNKTER = re.compile(r"\.{4}|…|\.{3}\s*\d+\s*$")


@dataclass(frozen=True)
class Paragraf:
    nummer: int
    rubrik: str | None
    diarienummer: list[str]
    beslut: str | None
    sida: int


class Avsnitt(NamedTuple):
    nummer: int
    start: int
    slut: int


def paragrafer(text: str) -> list[Paragraf]:
    rader = text.splitlines()
    return [paragraf(avsnitt, rader) for avsnitt in valda(rader)]


def valda(rader: list[str]) -> list[Avsnitt]:
    """Innehållsförteckningens rader hoppas över, ett avsnitt direkt efter
    ett med samma nummer är en fortsättningssida, och annars gäller det
    sista avsnittet, eftersom närvarolistan räknar upp numren först."""
    per_nummer, forra = {}, None
    for avsnitt in avsnitten(rader):
        if forteckning(rader[avsnitt.start + 1 : avsnitt.slut]):
            forra = None
            continue
        if forra and forra.nummer == avsnitt.nummer and forra.slut == avsnitt.start:
            avsnitt = avsnitt._replace(start=forra.start)
        per_nummer[avsnitt.nummer] = avsnitt
        forra = avsnitt
    return sorted(per_nummer.values(), key=lambda avsnitt: avsnitt.start)


def forteckning(rader: list[str]) -> bool:
    """Innehållsförteckningens rad: rubriken, på en rad eller tre, följs av
    en punktrad och sidan."""
    rubrik = list(takewhile(str.strip, dropwhile(lambda r: not r.strip(), rader)))
    return any(PUNKTER.search(rad) for rad in rubrik[:3])


def avsnitten(rader: list[str]) -> list[Avsnitt]:
    starter = [(i, int(m[1])) for i, m in rubriker(rader)]
    slut = [i for i, _ in starter[1:]] + [len(rader)]
    return [Avsnitt(n, i, e) for (i, n), e in zip(starter, slut, strict=False)]


def rubriker(rader: list[str]) -> Iterator[tuple[int, re.Match]]:
    for i, rad in enumerate(rader):
        if (m := RUBRIKRAD.match(rad)) and inleder(m[2], rader[i - 1] if i else ""):
            yield i, m


def inleder(rest: str, forra: str) -> bool:
    """Ett ensamt `§ 4` efter en rad text hör till närvarolistan eller texten."""
    rest = rest.strip()
    if not rest:
        forra = forra.strip()
        return not forra or bool(SIDA.match(forra) or DATUM.fullmatch(forra))
    return bool(FORTS.match(rest)) or bool(i_huvudet(rest, ensam=True))


def paragraf(avsnitt: Avsnitt, rader: list[str]) -> Paragraf:
    rest = rader[avsnitt.start + 1 : avsnitt.slut]
    numren = i_huvudet(RUBRIKRAD.match(rader[avsnitt.start])[2], ensam=True)
    for rad in dnr_rader(rest):
        numren += i_huvudet(rad)
    return Paragraf(
        nummer=avsnitt.nummer,
        rubrik=rubrik(rest),
        diarienummer=list(dict.fromkeys(numren)),
        beslut=beslut(rest),
        sida=sida(rader, avsnitt.start),
    )


def sida(rader: list[str], start: int) -> int:
    """Sidan med den senaste sidbrytningen före raden; utan brytning sidan 1."""
    for rad in reversed(rader[:start]):
        if m := SIDA.match(rad):
            return int(m[1])
    return 1
