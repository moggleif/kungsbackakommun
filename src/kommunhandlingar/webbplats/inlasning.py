"""Krav: K14, K22, K26, K36, K37, K46, K58 och K60 i docs/02-KRAV.md.
Test: tests/test_webbplats.py, tests/test_projekt.py, tests/test_kalender.py,
tests/test_mal.py, tests/test_uppfoljningar.py, tests/test_lokalbehov.py och
tests/test_initiativ.py.

Läser in underlaget för webbplatsbygget ur poolens rot: kommunerna och deras
mål-, uppföljnings-, spår- och projektfiler. Mallen får kommunerna och
vilka som har en kalender; resten blir ett underlag per kommun. Kalendern
läses per kommun när dess sida skrivs, eftersom sammanträdena kopplas till de
sidor som bygget redan skrivit.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from kommunhandlingar import konfiguration
from kommunhandlingar.fel import Datafel
from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import kalender, mal, projekt, spar, uppfoljningar
from kommunhandlingar.webbplats.arspann import arspann, poolens_ar
from kommunhandlingar.webbplats.kalender import Sammantrade
from kommunhandlingar.webbplats.mall import Mall
from kommunhandlingar.webbplats.projekt import Projekt
from kommunhandlingar.webbplats.sammanhang import Kommununderlag
from kommunhandlingar.webbplats.slagen import SLAGEN
from kommunhandlingar.webbplats.spar import Steg
from kommunhandlingar.webbplats.sparslag import DETALJPLANER


# Poolens rot och kommunerna, för kataloger med en fil per kommun, som
# `mal/<kommun>.csv`.
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
        self, katalog: str, lasare: Callable[[Path, Kommun, Path], T]
    ) -> dict[str, T]:
        filer = self.med_fil(katalog)
        return {
            k.id: lasare(
                self.rot / katalog / f"{k.id}.csv", k, self.rot / "data" / k.id
            )
            for k in self.kommuner
            if k.id in filer
        }


def las(
    rot: Path, repo: str, byggd: datetime
) -> tuple[Mall, dict[str, Kommununderlag]]:
    kommuner = [konfiguration.las(f) for f in sorted((rot / "kommuner").glob("*.toml"))]
    filer = Kommunfiler(rot, kommuner)
    mall = Mall(kommuner, repo, byggd, filer.med_fil("kalender"))
    lasta = {"mal": filer.las("mal", mal.las)}
    lasta["uppfoljningar"] = filer.las("uppfoljningar", uppfoljningar.las)
    lasta |= {s.id: filer.las(s.id, spar.lasare(s)) for s in SLAGEN}
    lasta["projekt"] = las_projekten(filer, lasta[DETALJPLANER.id])
    aren = {k.id: [*poolens_ar(rot / "data" / k.id), byggd.year] for k in kommuner}
    return mall, {i: kommunens_underlag(lasta, i, ar) for i, ar in aren.items()}


def las_kalender(rot: Path, kommun: Kommun) -> list[Sammantrade]:
    data = rot / "data" / kommun.id
    return kalender.las(rot / "kalender" / f"{kommun.id}.csv", kommun, data)


# `lasta` har varje katalogs rader per kommun. Åren är kommunens: poolens
# och byggåret, och raderna i mål-, uppföljnings- och spårfilerna (K60).
def kommunens_underlag(
    lasta: dict[str, dict], kommun_id: str, ar: list[int]
) -> Kommununderlag:
    egna = {k: rader[kommun_id] for k, rader in lasta.items() if kommun_id in rader}
    spar = {s.id: egna[s.id] for s in SLAGEN if s.id in egna}
    malen, uppfoljda = egna.get("mal", []), egna.get("uppfoljningar", [])
    rader = [*malen, *uppfoljda, *(s for stegen in spar.values() for s in stegen)]
    return Kommununderlag(
        arspann([*ar, *(r.ar for r in rader)]),
        malen,
        uppfoljda,
        spar,
        egna.get("projekt", {}),
        frozenset(egna),
    )


def las_projekten(
    filer: Kommunfiler, planerna: dict[str, list[Steg]]
) -> dict[str, dict[str, Projekt]]:
    projekten = filer.las("projekt", projekt.las)
    for kommun, kopplade in projekten.items():
        fil = f"projekt/{kommun}.csv"
        projekt.kontrollera(kopplade, planerna.get(kommun, []), fil)
    return projekten
