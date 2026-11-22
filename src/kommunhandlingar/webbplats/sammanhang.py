"""Krav: K26, K36, K37, K39, K46, K47 och K60 i docs/02-KRAV.md.
Test: tests/test_navigering.py, tests/test_arspann.py och tests/test_mal.py.

En kommuns sammanhang för sidorna: mallen för sidans ram, kommunen och
kommunens inlästa underlag. Underlaget är det som de sidor som visar mål,
uppföljningar, spår och projekt läser; menyn och sidfoten läser bara mallen.
"""

from dataclasses import dataclass, field

from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats.mal import Mal
from kommunhandlingar.webbplats.mall import Mall
from kommunhandlingar.webbplats.projekt import Projekt
from kommunhandlingar.webbplats.spar import Slag, Steg
from kommunhandlingar.webbplats.sparkort import Vy
from kommunhandlingar.webbplats.sparslag import DETALJPLANER
from kommunhandlingar.webbplats.uppfoljningar import Uppfoljning


@dataclass(frozen=True)
class Kommununderlag:
    # Åren som sidorna över tid visar (K60).
    aren: range
    malen: list[Mal] = field(default_factory=list)
    uppfoljningar: list[Uppfoljning] = field(default_factory=list)
    # Stegen per spårslag, som `spar["lokalbehov"]`.
    spar: dict[str, list[Steg]] = field(default_factory=dict)
    # Detaljplanernas projekt per plan (K46).
    projekt: dict[str, Projekt] = field(default_factory=dict)
    # Katalogerna där kommunen har en fil skriven för hand, som "mal" (K47);
    # kalendern står i mallen, som menyn läser.
    filer: frozenset[str] = frozenset()

    def stegen(self, slag: str) -> list[Steg]:
        return self.spar.get(slag, [])


@dataclass(frozen=True)
class Sammanhang:
    mall: Mall
    kommun: Kommun
    underlag: Kommununderlag

    # Bara detaljplanerna har projekt (K46).
    def vy(self, slag: Slag) -> Vy:
        projekt = self.underlag.projekt if slag == DETALJPLANER else {}
        return Vy(slag, self.kommun, self.underlag.aren, projekt)
