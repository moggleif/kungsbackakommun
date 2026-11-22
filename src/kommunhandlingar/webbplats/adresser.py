"""Var webbplatsens sidor ligger. Sidorna i en kommuns katalog har adresser
relativa till katalogen, som poolens dokument (ADR-0003); `i_kommunen` gör
dem relativa till webbplatsens rot. En sida som har en katalog ligger bredvid
den: organets `ks.html` bredvid `ks/`, sammanträdets `2026-10-20.html`
bredvid `2026-10-20/` (K54).
"""

from datetime import date

STARTSIDA = "index.html"
AVVIKELSER = "avvikelser.html"


def rot(adress: str) -> str:
    return "../" * adress.count("/")


def i_kommunen(kommun_id: str, adress: str) -> str:
    return f"{kommun_id}/{adress}"


def bredvid(katalog: str) -> str:
    return f"{katalog}.html"


def oversikt(kommun_id: str) -> str:
    return bredvid(kommun_id)


def kalender(kommun_id: str) -> str:
    return i_kommunen(kommun_id, "kalender.html")


def status(kommun_id: str) -> str:
    return i_kommunen(kommun_id, "status.html")


def organsida(organ: str) -> str:
    return bredvid(organ)


def organets_sida(kommun_id: str, organ: str) -> str:
    return i_kommunen(kommun_id, organsida(organ))


# Organets sidor över tid ligger i dess katalog; `organet` är katalogen,
# relativ till kommunens katalog eller till roten.
def over_tid(organet: str, sida: str) -> str:
    return f"{organet}/{sida}.html"


def sammantrade(organ: str, datum: date) -> str:
    return bredvid(f"{organ}/{datum.year}/{datum.isoformat()}")


def dokumentsida(kalla: str) -> str:
    return kalla.removesuffix(".md") + ".html"


def kallfil(adress: str) -> str:
    return adress.removesuffix(".html") + ".md"
