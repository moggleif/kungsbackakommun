"""Krav: K36, K37 och K39 i docs/02-KRAV.md, ADR-0057 och ADR-0058.
Test: tests/test_lokalbehov.py, tests/test_initiativ.py.

En sak på en spårsida – ett lokalbehov, ett initiativ, en plan – med sina
steg i år- och fasordning och märkena för urvalet utöver faserna: vem som
står bakom och om saken nått slagets aktuella fas det senaste året.
"""

import re
from dataclasses import dataclass

from kommunhandlingar.webbplats.spar import Slag, Steg


@dataclass(frozen=True)
class Sak:
    namn: str
    steg: list[Steg]
    markor: list[str]

    @property
    def faserna(self) -> list[str]:
        return list(dict.fromkeys(s.fas for s in self.steg))

    @property
    def aren(self) -> set[int]:
        return {s.ar for s in self.steg}


# Sakerna i den ordning de först står, med stegen i år- och fasordning.
def per_sak(slag: Slag, stegen: list[Steg]) -> list[Sak]:
    namn = dict.fromkeys(s.namn for s in sorted(stegen, key=lambda s: s.ar))
    senaste = senaste_ar(slag, stegen)
    return [samla(slag, [s for s in stegen if s.namn == n], senaste) for n in namn]


def samla(slag: Slag, stegen: list[Steg], senaste: int | None) -> Sak:
    fas = list(slag.faser)
    stegen = sorted(stegen, key=lambda s: ordning(s, fas))
    markor = [markor_for(v) for v in avsandarna(slag, stegen)]
    if any(s.ar == senaste and s.fas == slag.aktuell for s in stegen):
        markor.append("senaste")
    return Sak(stegen[0].namn, stegen, markor)


def markor_for(avsandare: str) -> str:
    return "av-" + re.sub(r"\W+", "-", avsandare.lower()).strip("-")


def senaste_ar(slag: Slag, stegen: list[Steg]) -> int | None:
    return max((s.ar for s in stegen if s.fas == slag.aktuell), default=None)


# Inom ett år kommer den första fasen först och sedan källornas datum, så
# att en återrapport i oktober står före ett beslut i november.
def ordning(steg: Steg, faser: list[str]) -> tuple[int, bool, str, int]:
    datum = steg.kalla.split("/")[2]
    return steg.ar, steg.fas != faser[0], datum, faser.index(steg.fas)


def avsandarna(slag: Slag, stegen: list[Steg]) -> list[str]:
    return list(
        dict.fromkeys(s.varde for s in stegen if s.fas == slag.avsandare and s.varde)
    )
