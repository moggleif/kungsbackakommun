"""Krav: K28, K29 och K50 i docs/02-KRAV.md, ADR-0046, ADR-0050 och ADR-0073.
Test: tests/test_malkort.py och tests/test_malar.py.

Protokollen om målen på sidan om ett organs mål och direktiv: sist i
tidslinjen en rad med en markering per uppföljning och dragning om målen i
protokollen, och ett streck för år utan protokoll med text, och i Ett år i
taget en lista med årets paragrafer.
"""

from html import escape

from kommunhandlingar.webbplats.malkort import kallank
from kommunhandlingar.webbplats.malspar import Underlag
from kommunhandlingar.webbplats.uppfoljningar import Uppfoljning

MARKERINGAR = {"uppföljning": "godkänd uppföljning", "dragning": "dragning om målen"}
KLASS = {"uppföljning": "godkand", "dragning": "dragning"}


def namnden_rad(uppfoljda: list[Uppfoljning], protokollar: set[int], ar: range) -> str:
    if not uppfoljda:
        return ""
    celler = "".join(i_namnden(uppfoljda, a, a in protokollar) for a in ar)
    return (
        '<tbody class="namnden"><tr><th scope="row">Protokollen om målen'
        f"{forklaring()}</th>{celler}</tr></tbody>"
    )


def i_namnden(uppfoljda: list[Uppfoljning], ar: int, protokoll: bool) -> str:
    if not protokoll:
        return '<td class="saknas" title="Inga protokoll med text i poolen">–</td>'
    markeringar = " ".join(
        markering(u.slag, f"{u.datum} § {u.paragraf}: {u.rubrik}")
        for u in uppfoljda
        if u.ar == ar
    )
    return f"<td>{markeringar}</td>"


def markering(slag: str, text: str) -> str:
    return (
        f'<span class="{KLASS[slag]}" role="img" aria-label="{escape(text)}" '
        f'title="{escape(text)}"></span>'
    )


def forklaring() -> str:
    return "".join(
        f'<br><small><span class="{KLASS[slag]}"></span> {text}</small>'
        for slag, text in MARKERINGAR.items()
    )


def protokollen(underlag: Underlag, ar: int) -> str:
    if not underlag.uppfoljda:
        return ""
    if ar not in underlag.protokollar:
        return f"<p>Inga protokoll med text i poolen {ar}.</p>"
    arets = [u for u in underlag.uppfoljda if u.ar == ar]
    if not arets:
        return f"<p>Protokollen {ar} tar inte upp målen.</p>"
    poster = "".join(
        f"<li>{u.datum} § {u.paragraf}, {u.slag}: {escape(u.rubrik)} "
        f"({kallank(u.kalla)})</li>"
        for u in arets
    )
    return f"<h4>Protokollen om målen {ar}</h4><ul>{poster}</ul>"
