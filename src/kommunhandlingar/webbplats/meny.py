"""Krav: K51 och K58 i docs/02-KRAV.md, ADR-0081, ADR-0082 och ADR-0084.
Test: tests/test_navigering.py.

Webbplatsens meny i den gemensamma form som Giffå ritar (ADR-0081): sajtens
namn och högst sex poster, där en post är en länk eller en undermeny. Med
flera kommuner får varje kommun en enda post: en undermeny med översikten,
kalendern och statussidan och sedan organen i kommunfilens grupper, och sist
står avvikelserna. Så ryms fem kommuner. En pool med en enda kommun heter som
den, och då är kommunfilens grupper själva posterna (ADR-0082): först
*Handlingar och protokoll*, översikten som är startsidan (ADR-0084), sedan
kalendern, en undermeny per grupp och sist *Om poolen*.
Knappen för mörkt tema står i Giffås sajtrad (ADR-0083).
"""

from html import escape

from kommunhandlingar.konfiguration import Kommun, Organ
from kommunhandlingar.webbplats import adresser
from kommunhandlingar.webbplats.organordning import grupperade

NAMN = "Kommunhandlingar"
# Giffå publicerar menyns stil och skript, och tema.js som sätter det valda
# temat innan sidan ritas (ADR-0083), på samma värd som poolens sida.
GEMENSAM = (
    '<link rel="stylesheet" href="/giffa/sajter.css">\n'
    '<script src="/giffa/tema.js"></script>\n'
    '<script src="/giffa/sajter.js" defer></script>'
)

Grupp = tuple[str, list[tuple[str, str]]]

EN_KOMMUN = "Handlingar och protokoll"


def meny(kommuner: list[Kommun], kalendrar: frozenset[str], aktuell: str) -> str:
    if len(kommuner) == 1:
        poster = en_kommuns_poster(kommuner[0], kalendrar, aktuell)
    else:
        poster = [undermeny(k.namn, sidorna(k, kalendrar), aktuell) for k in kommuner]
        poster.append(post(adresser.AVVIKELSER, "Avvikelser", aktuell))
    namn = lank(adresser.STARTSIDA, sajtnamn(kommuner), aktuell).replace(
        "<a ", '<a class="sajtnamn" ', 1
    )
    return (
        f'<nav class="sajtmeny" aria-label="Webbplatsen">{namn}'
        f"<ul>{''.join(poster)}</ul></nav>"
    )


def en_kommuns_poster(
    kommun: Kommun, kalendrar: frozenset[str], aktuell: str
) -> list[str]:
    kalender = adresser.kalender(kommun.id)
    kalenderpost = (
        [post(kalender, "Kalender", aktuell)] if kommun.id in kalendrar else []
    )
    grupper = [*organgrupper(kommun), ("Om poolen", om_poolen(kommun.id))]
    return [
        post(adresser.STARTSIDA, EN_KOMMUN, aktuell),
        *kalenderpost,
        *(enkel_undermeny(namn, lankar, aktuell) for namn, lankar in grupper),
    ]


def om_poolen(kommun_id: str) -> list[tuple[str, str]]:
    return [
        (adresser.status(kommun_id), "Poolens status"),
        (adresser.AVVIKELSER, "Avvikelser"),
    ]


# Med en enda kommun upprepar varken översiktens namn eller en rubrik
# kommunens namn, som är sajtens (ADR-0082).
def oversiktsnamn(kommuner: list[Kommun], kommun: Kommun) -> str:
    return EN_KOMMUN if len(kommuner) == 1 else kommun.namn


def kommunens(kommuner: list[Kommun], rubrik: str, kommun: Kommun) -> str:
    return rubrik if len(kommuner) == 1 else f"{rubrik} – {kommun.namn}"


# En pool med en enda kommun, som Kungsbackas eller regionens datarepo, heter
# som den.
def sajtnamn(kommuner: list[Kommun]) -> str:
    return kommuner[0].namn if len(kommuner) == 1 else NAMN


# Översikten först, sedan organen; utskotten nås från sitt organ.
def sidorna(kommun: Kommun, kalendrar: frozenset[str]) -> list[Grupp]:
    return [("Översikt", oversikt(kommun.id, kalendrar)), *organgrupper(kommun)]


# Kommunfilens grupper; en kommunfil utan grupper får gruppen "Organen".
def organgrupper(kommun: Kommun) -> list[Grupp]:
    return [
        (namn or "Organen", organlankar(kommun.id, i_gruppen))
        for namn, i_gruppen in grupperade(kommun)
    ]


def oversikt(kommun_id: str, kalendrar: frozenset[str]) -> list[tuple[str, str]]:
    kalender = [(adresser.kalender(kommun_id), "Kalender")]
    return (
        [(adresser.oversikt(kommun_id), "Alla organ")]
        + (kalender if kommun_id in kalendrar else [])
        + [(adresser.status(kommun_id), "Poolens status")]
    )


def organlankar(kommun_id: str, organen: list[Organ]) -> list[tuple[str, str]]:
    return [
        (adresser.organsida(kommun_id, o.id), o.namn[0])
        for o in organen
        if not o.hor_till
    ]


def undermeny(rubrik: str, grupper: list[Grupp], aktuell: str) -> str:
    kolumner = "".join(grupp(namn, lankar, aktuell) for namn, lankar in grupper)
    return utfallbar(rubrik, f'<div class="grupper">{kolumner}</div>')


def enkel_undermeny(rubrik: str, lankar: list[tuple[str, str]], aktuell: str) -> str:
    return utfallbar(rubrik, lista(lankar, aktuell))


def utfallbar(rubrik: str, panel: str) -> str:
    return f"<li><details><summary>{escape(rubrik)}</summary>{panel}</details></li>"


def grupp(namn: str, lankar: list[tuple[str, str]], aktuell: str) -> str:
    return f'<div><p class="grupp">{escape(namn)}</p>{lista(lankar, aktuell)}</div>'


def lista(lankar: list[tuple[str, str]], aktuell: str) -> str:
    return (
        "<ul>"
        + "".join(post(adress, namn, aktuell) for adress, namn in lankar)
        + "</ul>"
    )


def post(adress: str, namn: str, aktuell: str) -> str:
    return f"<li>{lank(adress, namn, aktuell)}</li>"


def lank(adress: str, namn: str, aktuell: str) -> str:
    markering = ' aria-current="page"' if adress == aktuell else ""
    upp = adresser.rot(aktuell)
    return f'<a href="{upp}{adress}"{markering}>{escape(namn)}</a>'
