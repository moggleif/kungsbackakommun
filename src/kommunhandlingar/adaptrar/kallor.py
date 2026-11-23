"""Krav: K88 i docs/02-KRAV.md, ADR-0109. Test: tests/test_kallor.py.

Källorna bakom ett gränssnitt. Varje källa i kommunfilen blir en `Kalla`
som upptäcker det levande med en hämtfunktion och arkivet med en läsare,
och som säger om dess levande kandidater står nyast först (ADR-0080). En
källa utan levande sidor, eller utan arkiv, ger ett tomt fynd.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import ClassVar, NamedTuple, Protocol

from kommunhandlingar.adaptrar import (
    episerver,
    episerver_arkiv,
    meetingsplus,
    sitevision,
    sitevision_arkiv,
    sitevision_projekt,
)
from kommunhandlingar.hamtning.hamtare import Lasare
from kommunhandlingar.kandidat import Fynd

Hamta = Callable[[str], str]


class Organsida(NamedTuple):
    """Organets sida i källan, som luckorna länkar till."""

    adress: str
    text: str
    i_arkivet: bool = False


class Kalla(Protocol):
    bakat: ClassVar[bool]

    def levande(self, hamta: Hamta) -> Fynd: ...

    def arkivet(self, klient: Lasare) -> Fynd: ...

    def projektlistor(self) -> dict[str, str]: ...

    def organsida(self, organ: str) -> Organsida | None: ...


@dataclass(frozen=True)
class Sitevision:
    kalla: sitevision.Kalla
    bakat: ClassVar[bool] = False

    def levande(self, hamta: Hamta) -> Fynd:
        """En fil på en projektsida som också står på en mötessida är mötets."""
        html = {adress: hamta(adress) for adress in self.kalla.sidor.values()}
        moten = sitevision.upptack(self.kalla, html)
        projekt = sitevision_projekt.upptack(self.kalla.projekt, hamta)
        motenas = {k.kallnyckel for k in moten.kandidater}
        egna = [k for k in projekt.kandidater if k.kallnyckel not in motenas]
        return moten + replace(projekt, kandidater=egna)

    def arkivet(self, klient: Lasare) -> Fynd:
        if not self.kalla.wayback:
            return Fynd()
        return sitevision_arkiv.upptack(self.kalla, klient)

    def projektlistor(self) -> dict[str, str]:
        return self.kalla.projekt

    def organsida(self, organ: str) -> Organsida | None:
        if organ not in self.kalla.sidor:
            return None
        arkiv = organ in self.kalla.wayback
        return Organsida(self.kalla.sidor[organ], "mötessidan", arkiv)


@dataclass(frozen=True)
class Episerver:
    kalla: episerver.Kalla
    bakat: ClassVar[bool] = True

    def levande(self, hamta: Hamta) -> Fynd:
        return Fynd()

    def arkivet(self, klient: Lasare) -> Fynd:
        return episerver_arkiv.upptack(self.kalla, klient)

    def projektlistor(self) -> dict[str, str]:
        return {}

    def organsida(self, organ: str) -> Organsida | None:
        return None


@dataclass(frozen=True)
class MeetingsPlus:
    kalla: meetingsplus.Kalla
    # Hela historiken är levande: nyast först, som arkivet (ADR-0080).
    bakat: ClassVar[bool] = True

    def levande(self, hamta: Hamta) -> Fynd:
        return meetingsplus.upptack(self.kalla, hamta)

    def arkivet(self, klient: Lasare) -> Fynd:
        return Fynd()

    def projektlistor(self) -> dict[str, str]:
        return {}

    def organsida(self, organ: str) -> Organsida | None:
        if organ not in self.kalla.sidor:
            return None
        return Organsida(self.kalla.sidor[organ], "organets sida på Meetings Plus")


ADAPTRAR = {
    "sitevision": (sitevision.kalla_av, Sitevision),
    "episerver": (episerver.kalla_av, Episerver),
    "meetingsplus": (meetingsplus.kalla_av, MeetingsPlus),
}
