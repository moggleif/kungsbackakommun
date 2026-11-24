"""Krav: K10 och K92 i docs/02-KRAV.md, ADR-0013, ADR-0061 och ADR-0115.
Test: tests/test_klient.py.

Läser ett svar, högst taket för en sida eller en fil, och
översätter svar och fel till det klienten gör härnäst: `NyttForsok` för
det som kan gå över, `Hamtfel` för resten.
"""

from http.client import HTTPResponse
from pathlib import Path
from typing import BinaryIO
from urllib.error import HTTPError, URLError

from kommunhandlingar.fel import Hamtfel

LANGSTA_VANTAN = 300
BLOCK = 1 << 20
# Filtaket är tre gånger det största originalet i poolen (324 MB).
FILTAK = 1 << 30
TEXTTAK = 50 << 20


class NyttForsok(Exception):
    def __init__(self, orsak: str, vantan: int | None = None):
        super().__init__(orsak)
        self.orsak, self.vantan = orsak, vantan


def las_text(svar: HTTPResponse) -> str:
    text = svar.read(TEXTTAK + 1)
    if len(text) > TEXTTAK:
        raise Hamtfel("for-stor")
    hel(svar, len(text))
    try:
        return text.decode(svar.headers.get_content_charset() or "utf-8")
    except (LookupError, UnicodeDecodeError) as fel:
        raise Hamtfel("teckenkodning") from fel


def spara(svar: HTTPResponse, mal: Path) -> None:
    with mal.open("wb") as fil:
        kopiera(svar, fil)
    hel(svar, mal.stat().st_size)


def hel(svar: HTTPResponse, storlek: int) -> None:
    """http.client ger tomt i stället för IncompleteRead när en läsning i
    bitar bryts av, så längden jämförs med vad servern lovade."""
    langd = svar.headers.get("Content-Length")
    if langd is not None and storlek != int(langd):
        raise NyttForsok("avbrutet-svar")


def kopiera(svar: HTTPResponse, fil: BinaryIO) -> None:
    storlek = 0
    while block := svar.read(BLOCK):
        storlek += len(block)
        if storlek > FILTAK:
            raise Hamtfel("for-stor")
        fil.write(block)


def http_fel(fel: HTTPError) -> Exception:
    orsak = f"http-{fel.code}"
    if fel.code == 429 or fel.code >= 500:
        efter = fel.headers.get("Retry-After", "")
        return NyttForsok(
            orsak, min(int(efter), LANGSTA_VANTAN) if efter.isdigit() else None
        )
    return Hamtfel(orsak)


def natfel(fel: URLError | ConnectionError | TimeoutError) -> Exception:
    # urllib slår in fel vid sändningen i URLError, men inte vid svaret.
    grund = fel.reason if isinstance(fel, URLError) else fel
    if isinstance(grund, ConnectionResetError):
        return NyttForsok("tomt-svar")
    if isinstance(grund, TimeoutError):
        return NyttForsok("tidsgrans")
    return Hamtfel("anslutning")
