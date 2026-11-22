"""Krav: K14, K22, K26, K36, K37, K46, K58 och K60 i docs/02-KRAV.md.
Test: tests/test_webbplats.py, tests/test_projekt.py, tests/test_kalender.py,
tests/test_mal.py, tests/test_uppfoljningar.py, tests/test_lokalbehov.py och
tests/test_initiativ.py.

Läser in underlaget för webbplatsbygget ur poolens rot: kommunerna och deras
mål-, uppföljnings-, spår- och projektfiler, som Mall bär dem. Kalendern
läses per kommun när dess sida skrivs, eftersom sammanträdena kopplas till de
sidor som bygget redan skrivit.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from kommunhandlingar import konfiguration
from kommunhandlingar.fel import Datafel
from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import kalender, mal, projekt, spar, uppfoljningar
from kommunhandlingar.webbplats.arspann import arspann, poolens_ar, radernas_ar
from kommunhandlingar.webbplats.kalender import Sammantrade
from kommunhandlingar.webbplats.mall import Mall
from kommunhandlingar.webbplats.projekt import Projekt
from kommunhandlingar.webbplats.slagen import SLAGEN
from kommunhandlingar.webbplats.spar import Steg
from kommunhandlingar.webbplats.sparslag import DETALJPLANER


# En katalog i poolens rot med en fil per kommun, som `mal/kungsbacka.csv`.
@dataclass(frozen=True)
class Kommunfiler:
    rot: Path
    kommuner: list[Kommun]

    def med_fil(self, katalog: str) -> frozenset[str]:
        filer = frozenset(f.stem for f in (self.rot / katalog).glob("*.csv"))
        if utan_kommun := filer - {k.id for k in self.kommuner}:
            raise Datafel(f"{katalog}/{min(utan_kommun)}.csv har ingen kommunfil")
        return filer

    def las[T](
        self, katalog: str, las: Callable[[Path, Kommun, Path], T]
    ) -> dict[str, T]:
        filer = self.med_fil(katalog)
        return {
            k.id: las(self.rot / katalog / f"{k.id}.csv", k, self.rot / "data" / k.id)
            for k in self.kommuner
            if k.id in filer
        }


def las(rot: Path, repo: str, byggd: datetime) -> Mall:
    kommuner = [konfiguration.las(f) for f in sorted((rot / "kommuner").glob("*.toml"))]
    filer = Kommunfiler(rot, kommuner)
    mall = Mall(
        kommuner,
        repo,
        byggd,
        kalendrar=filer.med_fil("kalender"),
        malen=filer.las("mal", mal.las),
        uppfoljningar=filer.las("uppfoljningar", uppfoljningar.las),
        spar={s.id: filer.las(s.id, spar.lasare(s)) for s in SLAGEN},
    )
    mall = replace(mall, projekt=las_projekten(filer, mall.spar[DETALJPLANER.id]))
    return replace(mall, aren=kommunernas_ar(rot, mall))


def las_kalender(rot: Path, kommun: Kommun) -> list[Sammantrade]:
    data = rot / "data" / kommun.id
    return kalender.las(rot / "kalender" / f"{kommun.id}.csv", kommun, data)


# Målen, uppföljningarna och spåren per kommun, som Mall har dem (K60).
def kommunernas_ar(rot: Path, mall: Mall) -> dict[str, range]:
    filer = (mall.malen, mall.uppfoljningar, mall.spar)
    return {
        k.id: arspann(
            [
                *poolens_ar(rot / "data" / k.id),
                *radernas_ar(k.id, *filer),
                mall.byggd.year,
            ]
        )
        for k in mall.kommuner
    }


def las_projekten(
    filer: Kommunfiler, planerna: dict[str, list[Steg]]
) -> dict[str, dict[str, Projekt]]:
    projekten = filer.las("projekt", projekt.las)
    for kommun, kopplade in projekten.items():
        fil = f"projekt/{kommun}.csv"
        projekt.kontrollera(kopplade, planerna.get(kommun, []), fil)
    return projekten
