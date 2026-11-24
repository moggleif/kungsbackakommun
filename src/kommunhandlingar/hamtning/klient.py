"""Krav: K10 och K92 i docs/02-KRAV.md, ADR-0013, ADR-0061 och ADR-0115.
Test: tests/test_klient.py.

Hämtar bara över https, håller intervallet per värd, följer robots.txt,
följer inga omdirigeringar och försöker igen vid 429, 5xx, tidsgräns och
svar som bryts av; för robots.txt också vid omdirigering och när värden
inte går att nå.
"""

import time
from collections.abc import Callable
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.hamtning import robots
from kommunhandlingar.hamtning.installningar import Installningar
from kommunhandlingar.hamtning.svar import NyttForsok, http_fel, las_text, natfel, spara

FORSOK = 4
FORSTA_VANTAN = 5
TIDSGRANS = 60
SCHEMA = "https"
# Har visat sig gå över för robots.txt (ADR-0061).
TILLFALLIGA_PA_ROBOTS = ("http-3", "anslutning")


class IngenOmdirigering(HTTPRedirectHandler):
    def redirect_request(self, *_):
        return None


class Klient:
    def __init__(
        self,
        installningar: Installningar,
        klocka: Callable[[], float] = time.monotonic,
        sov: Callable[[float], None] = time.sleep,
    ):
        self.installningar = installningar
        self.klocka, self.sov = klocka, sov
        self.senast: dict[str, float] = {}
        self.regler: dict[str, tuple[robots.Regel, ...]] = {}
        self.oppnare = build_opener(IngenOmdirigering)

    def text(self, url: str) -> str:
        self.prova(url)
        return self.med_forsok(url, las_text)

    def fil(self, url: str, mal: Path) -> None:
        """Strömmar svaret till `mal`; filer kan vara hundratals MB."""
        self.prova(url)
        self.med_forsok(url, lambda svar: spara(svar, mal))

    def prova(self, url: str) -> None:
        if urlsplit(url).scheme != SCHEMA:
            raise Hamtfel("inte-https")
        if not robots.tillater(self.robotregler(url), url):
            raise Hamtfel("robots")

    def robotregler(self, url: str) -> tuple[robots.Regel, ...]:
        varden = vard(url)
        if varden not in self.regler:
            self.regler[varden] = self.las_robots(varden)
        return self.regler[varden]

    def las_robots(self, varden: str) -> tuple[robots.Regel, ...]:
        try:
            text = self.med_forsok(
                f"{varden}/robots.txt", las_text, TILLFALLIGA_PA_ROBOTS
            )
        except Hamtfel as fel:
            if fel.orsak.startswith("http-4") and fel.orsak != "http-429":
                return ()
            raise Hamtfel(f"robots-{fel.orsak}") from fel
        return robots.tolka(text, produkt(self.installningar.user_agent))

    def med_forsok(self, url: str, las: Callable, tillfalliga: tuple[str, ...] = ()):
        for forsok in range(FORSOK - 1):
            try:
                return self.anrop(url, las, tillfalliga)
            except NyttForsok as fel:
                self.sov(fel.vantan or FORSTA_VANTAN * 2**forsok)
        try:
            return self.anrop(url, las, tillfalliga)
        except NyttForsok as fel:
            raise Hamtfel(fel.orsak) from fel

    def anrop(self, url: str, las: Callable, tillfalliga: tuple[str, ...]):
        try:
            return self.oppna(url, las)
        except Hamtfel as fel:
            if fel.orsak.startswith(tillfalliga):
                raise NyttForsok(fel.orsak) from fel
            raise

    def oppna(self, url: str, las: Callable):
        self.vanta_pa(vard(url))
        fraga = Request(url, headers={"User-Agent": self.installningar.user_agent})
        try:
            with self.oppnare.open(fraga, timeout=TIDSGRANS) as svar:
                return las(svar)
        except HTTPError as fel:
            raise http_fel(fel) from fel
        except (URLError, ConnectionError, TimeoutError) as fel:
            raise natfel(fel) from fel
        except HTTPException as fel:
            raise NyttForsok("avbrutet-svar") from fel
        finally:
            self.senast[vard(url)] = self.klocka()

    def vanta_pa(self, varden: str) -> None:
        if varden in self.senast:
            kvar = self.senast[varden] + self.installningar.intervall - self.klocka()
            if kvar > 0:
                self.sov(kvar)


def vard(url: str) -> str:
    delar = urlsplit(url)
    return f"{delar.scheme}://{delar.netloc}".lower()


def produkt(user_agent: str) -> str:
    return user_agent.split("/")[0].split()[0]
