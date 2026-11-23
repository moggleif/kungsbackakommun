"""Var webbplatsens sidor ligger, och bara här. En sida som har en katalog
ligger bredvid den: översikten `kungsbacka.html` bredvid `kungsbacka/`,
organets `ks.html` bredvid `ks/`, sammanträdets `2026-10-20.html` bredvid
`2026-10-20/` (K54).
"""

STARTSIDA = "index.html"
AVVIKELSER = "avvikelser.html"


def bredvid(katalog: str) -> str:
    return f"{katalog}.html"


# Relativa till webbplatsens rot.


def rot(adress: str) -> str:
    return "../" * adress.count("/")


def i_kommunen(kommun_id: str, adress: str) -> str:
    return f"{kommun_id}/{adress}"


def oversikt(kommun_id: str) -> str:
    return bredvid(kommun_id)


def kalender(kommun_id: str) -> str:
    return i_kommunen(kommun_id, "kalender.html")


def status(kommun_id: str) -> str:
    return i_kommunen(kommun_id, "status.html")


def organsida(kommun_id: str, organ: str) -> str:
    return i_kommunen(kommun_id, organ_i_katalogen(organ))


def over_tid(kommun_id: str, organ: str, sida: str) -> str:
    return i_kommunen(kommun_id, over_tid_i_katalogen(organ, sida))


# Relativa till kommunens katalog, som dokumentens adresser i poolen.

UR_ORGANETS_KATALOG = "../"


def organ_i_katalogen(organ: str) -> str:
    return bredvid(organ)


def over_tid_i_katalogen(organ: str, sida: str) -> str:
    return f"{organ}/{sida}.html"


# `katalog` är sammanträdets katalog, datumet med löpnumret när det har ett.
def sammantrade(organ: str, katalog: str) -> str:
    return bredvid(f"{organ}/{katalog[:4]}/{katalog}")


def dokumentsida(kalla: str) -> str:
    return kalla.removesuffix(".md") + ".html"


def kallfil(adress: str) -> str:
    return adress.removesuffix(".html") + ".md"
