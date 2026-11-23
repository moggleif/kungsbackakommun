"""Krav: K27, K28, K29, K35, K50, K60 och K71 i docs/02-KRAV.md, ADR-0045,
ADR-0046, ADR-0050, ADR-0056, ADR-0073, ADR-0086 och ADR-0098. Test:
tests/test_malgrupper.py, tests/test_uppfoljningar.py, tests/test_fokusomraden.py,
tests/test_malar.py och tests/test_regionmal.py.

Antalet per år på sidan om ett organs mål och direktiv: rubrikerna av
varje slag som finns på sidan, uppföljningarna i poolen som redovisar dem,
och rubrikerna med en bedömning i någon av dem, och ur protokollen
uppföljningarna och dragningarna om målen i protokollen. Ett år utan rader, eller
utan protokoll i poolen, är tomt, inte noll. Det senaste årets antal står
bredvid grafen, och tabellen är hopfälld under dem.
"""

from dataclasses import dataclass

from kommunhandlingar.webbplats.mal import SLAG, Mal
from kommunhandlingar.webbplats.malgraf import Serie, graf
from kommunhandlingar.webbplats.malspar import Underlag
from kommunhandlingar.webbplats.maltexter import ANTALET
from kommunhandlingar.webbplats.uppfoljningar import Uppfoljning

FLERTAL = {
    "nämndmål": "nämndmål",
    "kommunmål": "kommunmål",
    "regionmål": "regionmål",
    "fokusområde": "fokusområden",
    "direktiv": "direktiv",
}
RUBRIKER = ("Uppföljningar med målen", "Med bedömning")
NAMNDEN = ("uppföljningar i protokollen", "dragningar om målen")


@dataclass(frozen=True)
class Antal:
    per_slag: tuple[int, ...]
    uppfoljningar: int
    med_bedomning: int

    @property
    def tal(self) -> tuple[int, ...]:
        return (*self.per_slag, self.uppfoljningar, self.med_bedomning)


@dataclass(frozen=True)
class Aret:
    ar: int
    antal: Antal | None
    namnden: tuple[int, int] | None


def statistik(underlag: Underlag) -> str:
    slagen = slagen_pa(underlag.malen)
    aren = [aret(underlag, slagen, a) for a in underlag.ar]
    sista = max(m.ar for m in underlag.malen)
    return (
        '<h2 id="antal">Antal per år</h2><div class="sammandrag">'
        + arets_ruta(underlag, sista)
        + f'<div class="ruta">{graf(list(underlag.ar), serier(slagen, aren))}</div>'
        + "</div><details><summary>Tabell över antal per år</summary>"
        + tabell(aren, slagen)
        + ANTALET
        + "</details>"
    )


def slagen_pa(malen: list[Mal]) -> list[str]:
    return [s for s in SLAG if any(m.slag == s for m in malen)]


# Ett år utan mål har inget antal, och ett år utan protokoll med text inga
# uppföljningar i protokollen.
def aret(underlag: Underlag, slagen: list[str], ar: int) -> Aret:
    arets = [u for u in underlag.uppfoljda if u.ar == ar]
    namnden = i_namnden(arets) if ar in underlag.protokollar else None
    return Aret(ar, rakna([m for m in underlag.malen if m.ar == ar], slagen), namnden)


def serier(slagen: list[str], aren: list[Aret]) -> list[Serie]:
    return [
        (FLERTAL[s].capitalize(), [a.antal and a.antal.per_slag[i] for a in aren])
        for i, s in enumerate(slagen)
    ]


# Året har mål: rutan bredvid grafen gäller målens senaste år, och Ett år
# i taget visar rutan bara för år med mål.
def senaste(aret: Aret, slagen: list[str]) -> str:
    tal = list(zip(aret.antal.per_slag, (FLERTAL[s] for s in slagen), strict=True))
    if aret.namnden:
        tal += zip(aret.namnden, NAMNDEN, strict=True)
    siffror = "".join(f"<div><dt>{text}</dt><dd>{n}</dd></div>" for n, text in tal)
    return (
        f'<div class="ruta"><h3>{aret.ar}</h3><dl class="siffror">{siffror}</dl></div>'
    )


# Ett år med mål: det senaste i sammandraget, och varje år i Ett år i taget
# (K50).
def arets_ruta(underlag: Underlag, ar: int) -> str:
    slagen = slagen_pa(underlag.malen)
    return senaste(aret(underlag, slagen, ar), slagen)


def rakna(arets: list[Mal], slagen: list[str]) -> Antal | None:
    if not arets:
        return None
    uppfoljda = [m for m in arets if m.uppfoljning]
    return Antal(
        tuple(len({m.spar for m in arets if m.slag == s}) for s in slagen),
        len({m.dokument for m in uppfoljda}),
        len({m.spar for m in uppfoljda if m.bedomning != "ingen"}),
    )


def i_namnden(arets: list[Uppfoljning]) -> tuple[int, int]:
    return (
        sum(u.slag == "uppföljning" for u in arets),
        sum(u.slag == "dragning" for u in arets),
    )


def tabell(aren: list[Aret], slagen: list[str]) -> str:
    rubriker = ["År", *(FLERTAL[s].capitalize() for s in slagen), *RUBRIKER]
    rubriker += [n.capitalize() for n in NAMNDEN]
    huvud = "".join(f'<th scope="col">{t}</th>' for t in rubriker)
    kolumner = len(slagen) + len(RUBRIKER)
    rader = "".join(tabellrad(a, kolumner) for a in aren)
    return (
        f'<div class="tabell"><table><thead><tr>{huvud}</tr></thead>'
        f"<tbody>{rader}</tbody></table></div>"
    )


def tabellrad(aret: Aret, kolumner: int) -> str:
    tal = tal_i(aret.antal and aret.antal.tal, kolumner) + tal_i(aret.namnden, 2)
    celler = "".join(f'<td class="tal">{t}</td>' for t in tal)
    return f'<tr><th scope="row">{aret.ar}</th>{celler}</tr>'


# Ett år utan uppgift är ett streck i varje kolumn, inte en nolla.
def tal_i(varden: tuple[int, ...] | None, kolumner: int) -> list[str]:
    if varden is None:
        return ["–"] * kolumner
    return [str(v) for v in varden]
