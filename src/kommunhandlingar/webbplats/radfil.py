"""Krav: K14 i docs/02-KRAV.md. Test: tests/test_radfilerna.py.

Läser en av webbplatsens radfiler – målen, spåren, uppföljningarna,
kalendern och projekten – och stoppar bygget med filen och raden när
rubrikraden eller en rad inte går ihop. Filens egen funktion tolkar en
rad och kastar ValueError med vad som är fel; kontrollerna som flera
filer gör står här.
"""

import csv
import re
from collections.abc import Callable, Hashable
from pathlib import Path

from kommunhandlingar.fel import Datafel
from kommunhandlingar.konfiguration import Kommun


def las[T](fil: Path, kolumner: list[str], tolka: Callable[[list[str]], T]) -> list[T]:
    with fil.open(encoding="utf-8", newline="") as f:
        rader = list(csv.reader(f))
    if not rader or rader[0] != kolumner:
        raise Datafel(f"{fil}: rubrikerna är inte {','.join(kolumner)}")
    poster = []
    for nr, rad in enumerate(rader[1:], 2):
        try:
            poster.append(tolka(antal_falt(rad, kolumner)))
        except ValueError as fel:
            raise Datafel(f"{fil}, rad {nr}: {fel}") from None
    return poster


def unika[T](
    tolka: Callable[[list[str]], T], nyckel: Callable[[T], Hashable], dubblett: str
) -> Callable[[list[str]], T]:
    sedda = set()

    def tolka_unik(rad: list[str]) -> T:
        post = tolka(rad)
        if nyckel(post) in sedda:
            raise ValueError(dubblett)
        sedda.add(nyckel(post))
        return post

    return tolka_unik


def antal_falt(rad: list[str], kolumner: list[str]) -> list[str]:
    if len(rad) != len(kolumner):
        raise ValueError(f"{len(rad)} fält, inte {len(kolumner)}")
    return rad


def organen(kommun: Kommun) -> set[str]:
    return {o.id for o in kommun.organ}


def i_kommunfilen(organ: str, organen: set[str]) -> None:
    if organ not in organen:
        raise ValueError(f"organet {organ!r} står inte i kommunfilen")


def ar(text: str) -> int:
    if not re.fullmatch(r"\d{4}", text):
        raise ValueError(f"året {text!r} är inte fyra siffror")
    return int(text)


def tolkad(text: str) -> None:
    if text not in ("", "ja"):
        raise ValueError(f"tolkad {text!r} är varken tom eller ja")
