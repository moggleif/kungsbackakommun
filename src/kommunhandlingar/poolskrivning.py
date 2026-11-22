"""Krav: K4, K6, K8, K9, K11 och K48 i docs/02-KRAV.md, ADR-0004, ADR-0019 och
ADR-0071. Test i tests/: test_hamta.py, test_hamta_arkiv.py, test_omkonvertering.py
och test_tidsbudget.py.

Fälten och skrivningen i steg 2: ett dokuments front matter byggs ur kandidaten
och det som redan finns på platsen, och dokumentet skrivs till poolen utan att
tidsgränsen kan avbryta skrivningen (K11). Vad som ska hända med en kandidat
avgör `behandla.py`.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Protocol

from kommunhandlingar import frontmatter, skrivning
from kommunhandlingar.arenden import arenden
from kommunhandlingar.kandidat import Kandidat
from kommunhandlingar.konvertering.las_sida import Sida
from kommunhandlingar.original import Original
from kommunhandlingar.pool import Pool
from kommunhandlingar.tidsbudget import utan_avbrott


class Klient(Protocol):
    def fil(self, url: str, mal: Path) -> None: ...


@dataclass(frozen=True)
class Steg2:
    data: Path
    kommun: str
    pool: Pool
    klient: Klient
    nycklar: frozenset[str]
    tid: Callable[[], datetime]
    version: str
    arkiv: bool = False
    omkonvertera: bool = False
    ensamma: frozenset[str] = frozenset()  # arkivluckor.ensamma


@dataclass(frozen=True)
class Dokument:
    kandidat: Kandidat
    sokvag: PurePosixPath
    befintlig: dict[str, str] | None
    namn: str | None = None
    hamtad: datetime | None = None


def skriv(
    steg: Steg2, dokument: Dokument, falt: dict, sidor: list[Sida] | None
) -> None:
    md = steg.data / dokument.sokvag
    kropp = skrivning.kropp(md, sidor)
    falt = grundfalt(steg, dokument) | falt
    falt["arenden"] = arenden(falt["typ"], kropp)
    text = frontmatter.skriv(falt) + kropp
    tabeller = skrivning.tabellfiler(sidor or [])
    with utan_avbrott():
        skrivning.skriv(md, text, tabeller)
    steg.pool.satt(dokument.sokvag, frontmatter.las(text))


def filfalt(dokument: Dokument, hamtat: Original) -> dict:
    hamtad = dokument.hamtad.isoformat()
    return {"sha256": hamtat.sha256, "bytes": hamtat.bytes, "hamtad": hamtad}


def ny_adress(steg: Steg2, dokument: Dokument) -> str:
    k = dokument.kandidat
    nya = {"kallnyckel": k.kallnyckel, "tidigare_kallnycklar": tidigare(dokument)}
    andra_falt(steg, dokument.sokvag, nya | {"kalla_url": k.kalla_url()})
    return "ny adress, samma innehåll"


def behall(steg: Steg2, dokument: Dokument) -> str:
    """Kandidaten blir en tidigare källnyckel, så att den inte hämtas igen."""
    nycklar = frontmatter.lista(dokument.befintlig["tidigare_kallnycklar"])
    nycklar.append(dokument.kandidat.kallnyckel)
    andra_falt(steg, dokument.sokvag, {"tidigare_kallnycklar": nycklar})
    return "lika eller lägre kvalitet; det befintliga behålls"


def andra_falt(steg: Steg2, sokvag: PurePosixPath, nya: dict) -> None:
    md = steg.data / sokvag
    gammal = md.read_text(encoding="utf-8")
    falt = frontmatter.las(gammal) | nya
    text = frontmatter.skriv(falt) + frontmatter.brodtext(gammal)
    with utan_avbrott():
        skrivning.skriv_md(md, text)
    steg.pool.satt(sokvag, frontmatter.las(text))


def grundfalt(steg: Steg2, dokument: Dokument) -> dict:
    return (
        dict.fromkeys(frontmatter.FALT)
        | platsfalt(dokument)
        | {
            "kommun": steg.kommun,
            "kallnyckel": dokument.kandidat.kallnyckel,
            "tidigare_kallnycklar": tidigare(dokument),
            "kalla_url": dokument.kandidat.kalla_url(),
        }
    )


def platsfalt(dokument: Dokument) -> dict:
    gammal = dokument.befintlig
    if gammal:
        return {f: gammal[f] for f in ("organ", "datum", "lopnr", "typ", "namn")}
    k = dokument.kandidat
    return {"organ": k.organ, "datum": k.datum, "typ": k.typ, "namn": dokument.namn}


def tidigare(dokument: Dokument) -> list[str]:
    gammal = dokument.befintlig
    if not gammal:
        return []
    nycklar = frontmatter.lista(gammal["tidigare_kallnycklar"])
    if gammal["kallnyckel"] != dokument.kandidat.kallnyckel:
        nycklar.append(gammal["kallnyckel"])
    return nycklar
