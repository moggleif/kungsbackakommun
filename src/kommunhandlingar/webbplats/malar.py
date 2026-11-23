"""Krav: K50 i docs/02-KRAV.md, ADR-0073. Test: tests/test_malar.py.

Ett år i taget på sidan om ett organs mål och direktiv: en knapp per år och
ett avsnitt per år, nyast först. Avsnittet har årets antal, ett kort per
spår med årets rader (`malarskort.py`), vad som försvann sedan året innan,
och protokollens uppföljningar och dragningar det året (`malprotokoll.py`).
Efter en lucka går det inte att veta vad som är nytt, så då jämförs inte.
"""

from kommunhandlingar.webbplats.mal import Mal
from kommunhandlingar.webbplats.malarskort import (
    arets_rubrik,
    arskort,
    forsta_malar,
    ordnade,
    pa_aret,
)
from kommunhandlingar.webbplats.malkort import rubrik
from kommunhandlingar.webbplats.malprotokoll import protokollen
from kommunhandlingar.webbplats.malspar import Underlag
from kommunhandlingar.webbplats.malstatistik import arets_ruta


def aren(underlag: Underlag) -> str:
    knappar = "".join(
        f'<button type="button" data-ar="{a}">{a}</button>' for a in underlag.ar
    )
    avsnitt = "".join(arsavsnitt(underlag, a) for a in reversed(underlag.ar))
    return (
        '<h2 id="aren">Ett år i taget</h2>'
        f'<div class="arval" role="group" aria-label="År" '
        f'data-forval="{senaste_malar(underlag.spar)}" hidden>{knappar}</div>' + avsnitt
    )


def senaste_malar(spar: list[list[Mal]]) -> int:
    return max(m.ar for malen in spar for m in malen)


def arsavsnitt(underlag: Underlag, ar: int) -> str:
    return f'<section class="aret" data-ar="{ar}">{innehall(underlag, ar)}</section>'


def innehall(underlag: Underlag, ar: int) -> str:
    if ar in underlag.luckor:
        return f"<h3>{ar}</h3><p>Lucka i poolen: inga dokument från organet {ar}.</p>"
    if not pa_aret(underlag.spar, ar):
        return (
            f"<h3>{ar}</h3><p>Poolen har inga av organets mål för {ar}.</p>"
            + protokollen(underlag, ar)
        )
    return arets_mal(underlag, ar) + protokollen(underlag, ar)


def arets_mal(underlag: Underlag, ar: int) -> str:
    kort = "".join(arskort(underlag, nr, ar) for nr in ordnade(underlag, ar))
    return (
        arets_ruta(underlag.malen, underlag.uppfoljda, underlag.protokollar, ar)
        + jamforelse(underlag, ar)
        + f'<div class="malkort">{kort}</div>'
    )


def jamforelse(underlag: Underlag, ar: int) -> str:
    if ar == forsta_malar(underlag.spar):
        return "<p>Det första året med mål på sidan.</p>"
    if ar - 1 in underlag.luckor:
        return (
            "<p>Året innan är en lucka i poolen, så det går inte att säga vad "
            "som är nytt eller försvann.</p>"
        )
    return forsvunna(underlag, ar)


def forsvunna(underlag: Underlag, ar: int) -> str:
    borta = pa_aret(underlag.spar, ar - 1) - pa_aret(underlag.spar, ar)
    if not borta:
        return f"<p>Inget mål försvann sedan {ar - 1}.</p>"
    lankar = ", ".join(
        f'<a href="#mal-{nr}">{rubrik(arets_rubrik(underlag.spar[nr], ar - 1))}</a>'
        for nr in sorted(borta)
    )
    return f"<p>Försvann sedan {ar - 1}: {lankar}.</p>"
