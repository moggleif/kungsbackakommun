"""Krav: K4, K6, K14, K15 och K34 i docs/02-KRAV.md. Test:
tests/test_frontmatter.py, tests/test_hamta.py och tests/test_webbplats.py.

Front matter så som schemat i docs/03-ARKITEKTUR.md#front-matter skriver den:
varje fält på en egen rad, i schemats ordning, listor inom hakparenteser.
Bara här delas en `.md` i front matter och brödtext (#360).
"""

from datetime import date

GRANS = "---\n"

FALT = (
    "kommun",
    "organ",
    "datum",
    "lopnr",
    "typ",
    "namn",
    "kallnyckel",
    "tidigare_kallnycklar",
    "arenden",
    "kalla_url",
    "sha256",
    "bytes",
    "sidor",
    "hamtad",
    "konverterad",
    "pipeline",
    "kvalitet",
    "fel",
    "kvalitet_per_sida",
    "tal_obekraftade",
    "figurer",
    "tolkade",
    "granskad",
)


def dela(text: str) -> tuple[dict[str, str], str]:
    _, huvud, kropp = text.split(GRANS, 2)
    return dict(rad.split(": ", 1) for rad in huvud.splitlines()), kropp


def las(text: str) -> dict[str, str]:
    return dela(text)[0]


def brodtext(text: str) -> str:
    return dela(text)[1]


def andrad(text: str, nya: dict) -> str:
    """Fälten i `nya` får nya värden; övriga fält och brödtexten står kvar."""
    falt, kropp = dela(text)
    return huvud(falt | nya) + kropp


def lista(varde: str) -> list[str]:
    if varde == "null":
        return []
    return [del_ for del_ in varde.strip("[]").split(", ") if del_]


def adresser(kalla_url: str) -> list[str]:
    """`kalla_url` är en adress, eller en lista för ett dokument i delar."""
    return lista(kalla_url) if kalla_url.startswith("[") else [kalla_url]


def skriv(falt: dict) -> str:
    return huvud({namn: falt[namn] for namn in FALT})


def huvud(falt: dict) -> str:
    """Front matter med fälten i den ordning de står i `falt`."""
    rader = "".join(f"{namn}: {varde_av(varde)}\n" for namn, varde in falt.items())
    return GRANS + rader + GRANS


def varde_av(varde) -> str:
    if varde is None:
        return "null"
    if isinstance(varde, list):
        return "[" + ", ".join(varde_av(v) for v in varde) + "]"
    if isinstance(varde, date):
        return varde.isoformat()
    return str(varde)
