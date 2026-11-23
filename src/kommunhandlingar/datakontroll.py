"""Krav: K6, K11, K15, K17, K34, K48 och K81 i docs/02-KRAV.md, ADR-0006,
ADR-0017, ADR-0022, ADR-0055 och ADR-0071. Test: tests/test_datakontroll.py,
tests/test_granskning.py, tests/test_arenden.py och tests/test_poolkommandon.py.

`python -m kommunhandlingar.datakontroll <data>` prövar varje fil under
`data/` mot schemat i docs/03-ARKITEKTUR.md: front matter, sökvägen,
tabellkatalogerna, att inga temporära filer finns kvar, att inga
personuppgifter står omaskade, att inga styrtecken står i texten och att
`arenden` stämmer med protokollets paragrafer. Värdena i front matter prövas
i `datakontroll_varden.py`.
Varje fel skrivs ut, och kommandot avslutas med fel om något hittades.
"""

import sys
from functools import partial
from multiprocessing import Pool
from pathlib import Path

from kommunhandlingar import datakontroll_tolkning, datakontroll_varden, frontmatter
from kommunhandlingar.arenden import ratt_varde
from kommunhandlingar.datakontroll_tabeller import tabellfel
from kommunhandlingar.frontmatter import saknas
from kommunhandlingar.kommando import datakatalog
from kommunhandlingar.konvertering.las_sida import STYRTECKEN
from kommunhandlingar.personuppgifter import maskad_md, maskade_celler

ALLTID = ("kommun", "organ", "datum", "typ", "kallnyckel", "kalla_url")
ALLTID += ("tidigare_kallnycklar", "hamtad", "pipeline", "kvalitet")


def fel_i(data: Path) -> list[str]:
    """Filerna prövas var för sig, på alla kärnor."""
    filer = [fil for fil in sorted(data.rglob("*")) if fil.is_file()]
    with Pool() as pool:
        fel = pool.map(partial(fel_i_fil, data), filer, chunksize=64)
        # Arbetarna avslutas själva i stället för att stoppas, så att
        # täckningsmätningen hinner spara deras del (K75).
        pool.close()
        pool.join()
    return [rad for filens in fel for rad in filens]


def fel_i_fil(data: Path, fil: Path) -> list[str]:
    relativ = fil.relative_to(data).as_posix()
    return [f"{relativ}: {f}" for f in filfel(data, fil)]


def filfel(data: Path, fil: Path) -> list[str]:
    if fil.suffix == ".md" and fil.parent != data:
        text = fil.read_text(encoding="utf-8")
        fel = dokumentfel(fil.relative_to(data), text) + styrteckenfel(text)
        return fel + personuppgiftsfel(maskad_md(text) != text)
    if fil.parent.suffix == ".tabeller":
        # En CSV med formfel går kanske inte att läsa; formfelen rättas först.
        return tabellfel(fil) or tabellens_personuppgifter(fil)
    return ["oväntad fil, till exempel kvar efter en avbruten körning"]


def tabellens_personuppgifter(fil: Path) -> list[str]:
    text = fil.read_text(encoding="utf-8")
    fel = personuppgiftsfel(maskade_celler(text) is not None)
    return fel + styrteckenfel(text)


def styrteckenfel(text: str) -> list[str]:
    """Ett styrtecken ska vara `�` (#257); NUL gör filen binär för git."""
    return ["styrtecken i texten"] if STYRTECKEN.search(text) else []


def personuppgiftsfel(finns: bool) -> list[str]:
    if not finns:
        return []
    return ["personuppgifter som ska maskas (python -m kommunhandlingar.maska_poolen)"]


def dokumentfel(relativ: Path, text: str) -> list[str]:
    try:
        falt = frontmatter.las(text)
    except (IndexError, ValueError):
        return ["front matter går inte att läsa"]
    if tuple(falt) != frontmatter.FALT:
        return ["front matter har inte schemats fält i schemats ordning"]
    fel = [f"{namn} är null" for namn in ALLTID if saknas(falt[namn])]
    if fel:
        return fel
    fel = datakontroll_varden.faltfel(relativ, falt)
    return fel + arendefel(falt, text) + datakontroll_tolkning.dokumentfel(falt, text)


def arendefel(falt: dict[str, str], text: str) -> list[str]:
    if falt["arenden"] == (ratt := ratt_varde(text)):
        return []
    return [f"arenden borde vara {ratt} (python -m kommunhandlingar.arenden)"]


if __name__ == "__main__":
    hittade = fel_i(datakatalog("datakontroll"))
    print("\n".join(hittade) or "Datakontrollerna gick igenom.")
    sys.exit(1 if hittade else 0)
