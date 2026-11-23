"""Krav: K35 och K50 i docs/02-KRAV.md, ADR-0056 och ADR-0073. Test:
tests/test_malar.py.

Korten i Ett år i taget på sidan om ett organs mål och direktiv: ett kort
per spår med årets rubrik, formuleringar och rader, märkt nytt när spåret
inte stod året innan, och ett kommunmåls fokusområden i dess kort.
"""

from html import escape

from kommunhandlingar.webbplats.mal import SLAG, Mal
from kommunhandlingar.webbplats.malkort import kallank, rubrik, status
from kommunhandlingar.webbplats.malspar import (
    Underlag,
    egenskaper,
    forsta,
    fristaende,
    slagen,
    under,
)


# Åren är kommunens (K60), så målens första år är inte alltid det första.
def forsta_malar(spar: list[list[Mal]]) -> int:
    return min(m.ar for malen in spar for m in malen)


def pa_aret(spar: list[list[Mal]], ar: int) -> set[int]:
    return {nr for nr, malen in enumerate(spar) if any(m.ar == ar for m in malen)}


# Bara året efter ett år som går att jämföra med har något nytt.
def nytt(underlag: Underlag, ar: int) -> set[int]:
    if ar == forsta_malar(underlag.spar) or ar - 1 in underlag.luckor:
        return set()
    return pa_aret(underlag.spar, ar) - pa_aret(underlag.spar, ar - 1)


# Ett fokusområde står i sitt kommunmåls kort, och för sig de år kommunmålet
# saknas, så att inget av årets mål utelämnas.
def ordnade(underlag: Underlag, ar: int) -> list[int]:
    aret = pa_aret(underlag.spar, ar)
    nummer = []
    for nr, malen in fristaende(underlag.spar):
        egna = [nr] if nr in aret else [f for f, _ in under(underlag.spar, malen)]
        nummer += [n for n in egna if n in aret]
    return sorted(nummer, key=lambda nr: nyckel(underlag.spar[nr], ar))


def nyckel(malen: list[Mal], ar: int) -> tuple[int, str]:
    sista = [m for m in malen if m.ar == ar][-1]
    return SLAG.index(sista.slag), sista.rubrik.casefold()


def arskort(underlag: Underlag, nr: int, ar: int) -> str:
    malen = underlag.spar[nr]
    arets = [m for m in malen if m.ar == ar]
    markor = [*slagen(arets), *(["nytt"] if nr in nytt(underlag, ar) else [])]
    return (
        f"<article {egenskaper(nr, malen)}>"
        f'<p class="markor">{" ".join(f"<span>{m}</span>" for m in markor)}</p>'
        f"<h4>{rubrik(arets_rubrik(malen, ar))}</h4>{rader(arets)}"
        f"{fokusomraden(underlag, nr, ar)}</article>"
    )


# Varje formulering står en gång i kortet; varje rad har sin status och källa.
def rader(arets: list[Mal]) -> str:
    formuleringar = dict.fromkeys(m.formulering for m in arets if m.formulering)
    citat = "".join(
        f"<blockquote><q>{escape(f)}</q></blockquote>" for f in formuleringar
    )
    poster = "".join(f"<li>{rad(m)}</li>" for m in arets)
    return f'{citat}<ol class="rader">{poster}</ol>'


def rad(mal: Mal) -> str:
    besked = status(mal) if mal.uppfoljning else "Beslutat"
    return f"{besked}<br>Källa: {kallank(mal.kalla)}"


def fokusomraden(underlag: Underlag, nr: int, ar: int) -> str:
    fokus = "".join(
        arskort(underlag, n, ar)
        for n, m in under(underlag.spar, underlag.spar[nr])
        if any(f.ar == ar for f in m)
    )
    if not fokus:
        return ""
    return f'<div class="fokusomraden"><h4>Fokusområden</h4>{fokus}</div>'


# Rubriken som den först står, som i tidslinjen.
def arets_rubrik(malen: list[Mal], ar: int) -> Mal:
    return forsta(malen)[[m for m in malen if m.ar == ar][-1].namn]
