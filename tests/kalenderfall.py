"""Gemensamt för kalenderns tester: en kommun med ett utskott och en
kalenderfil läst mot en temporär pool."""

import tomllib
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from kommunhandlingar.konfiguration import tolka
from kommunhandlingar.webbplats import kalender
from tests.poolfall import tillfallig_pool

FIXTURER = Path(__file__).parent / "fixtures"
ROT = Path(__file__).parent.parent
REPO = "https://github.com/exempel/kommunhandlingar"
TID = datetime(2026, 10, 7, 20, 15, tzinfo=UTC)
RUBRIK = "organ,datum,tid,plats,kalla,osakert\n"
PROTOKOLL = "fsn/2026/2026-09-17/protokoll.md"
KALLELSE = "fsn/2026/2026-09-17/kallelse.md"
NASTA = "fsn/2026/2026-09-24/protokoll.md"
RADER = (
    f"fsn,2027-01-14,17:00,Stadshuset,{PROTOKOLL},\n"
    f"fsn-au,2027-01-14,,,{PROTOKOLL},\n"
    "bun,2026-12-05,,,https://exempelby.se/bun,Källan säger lördag <5 dec>.\n"
)


def kommun():
    with (FIXTURER / "exempelby.toml").open("rb") as fil:
        data = tomllib.load(fil)
    data["organ"].append(
        {"id": "fsn-au", "namn": ["Arbetsutskottet"], "hor_till": "fsn"}
    )
    return tolka("exempelby", data)


@contextmanager
def pool(rader: str = RADER, rubrik: str = RUBRIK):
    """Läser en kalenderfil mot en pool med protokollet, i en temporär katalog."""
    texter = dict.fromkeys((PROTOKOLL, KALLELSE, NASTA), "---\n---\n")
    with tillfallig_pool(rubrik, rader, texter) as (fil, data):
        yield kalender.las(fil, kommun(), data)
