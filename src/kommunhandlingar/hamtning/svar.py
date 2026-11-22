"""Krav: K10 i docs/02-KRAV.md, ADR-0013 och ADR-0061. Test:
tests/test_klient.py.

Läser ett svar och översätter svar och fel till det klienten gör härnäst:
`NyttForsok` för det som kan gå över, `Hamtfel` för resten.
"""

import shutil
from http.client import HTTPResponse
from pathlib import Path
from urllib.error import HTTPError, URLError

from kommunhandlingar.fel import Hamtfel

LANGSTA_VANTAN = 300
BLOCK = 1 << 20


class NyttForsok(Exception):
    def __init__(self, orsak: str, vantan: int | None = None):
        super().__init__(orsak)
        self.orsak, self.vantan = orsak, vantan


def las_text(svar: HTTPResponse) -> str:
    try:
        return svar.read().decode(svar.headers.get_content_charset() or "utf-8")
    except (LookupError, UnicodeDecodeError) as fel:
        raise Hamtfel("teckenkodning") from fel


def spara(svar: HTTPResponse, mal: Path) -> None:
    with mal.open("wb") as fil:
        shutil.copyfileobj(svar, fil, BLOCK)
    # http.client ger tomt i stället för IncompleteRead när en läsning i
    # bitar bryts av, så längden jämförs med vad servern lovade.
    langd = svar.headers.get("Content-Length")
    if langd is not None and mal.stat().st_size != int(langd):
        raise NyttForsok("avbrutet-svar")


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
