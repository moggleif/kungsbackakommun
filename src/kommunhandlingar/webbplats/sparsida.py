"""Krav: K36, K37 och K39 i docs/02-KRAV.md, ADR-0057 och ADR-0058.
Test: tests/test_lokalbehov.py, tests/test_initiativ.py.

Sidan om ett organs spår av ett slag, byggd som målsidan (ADR-0050): en
hopfälld del om metoden, antalet saker per fas och per avsändare, ett
urval, tidslinjen med en rad per sak och en kolumn per år, där ikonerna
visar årets faser, och ett kort per sak (`sparkort.py`). Sidans ram –
flikarna, stilen, inledningen och delen om sidan – står för sig och
innehållet för sig; sakerna samlas i `sparsak.py` och sammandraget och
urvalet står i `sparsammandrag.py`. Stilen och skriptet är målsidans.
"""

from html import escape

from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import adresser, ram
from kommunhandlingar.webbplats.flikar import flikar
from kommunhandlingar.webbplats.inbaddning import skript, stil
from kommunhandlingar.webbplats.mall import sida
from kommunhandlingar.webbplats.maltexter import AREN
from kommunhandlingar.webbplats.mandatperiod import kolumner, rubriker
from kommunhandlingar.webbplats.sammanhang import Sammanhang
from kommunhandlingar.webbplats.spar import Slag, Steg
from kommunhandlingar.webbplats.sparikon import teckenforklaring
from kommunhandlingar.webbplats.sparkort import Vy, arets, egenskaper, korten
from kommunhandlingar.webbplats.sparsak import Sak, avsandarna, per_sak
from kommunhandlingar.webbplats.sparsammandrag import sammandrag, urval


def adress(kommun: Kommun, organ: str, slag: Slag) -> str:
    return adresser.over_tid(kommun.id, organ, slag.id)


def sparsida(sammanhang: Sammanhang, slag: Slag, stegen: list[Steg]) -> str:
    organ, vy = stegen[0].organ, sammanhang.vy(slag)
    namn = vy.kommun.organnamn(organ)
    innehall = (
        ramen(sammanhang, organ, slag) + innehallet(vy, stegen) + skript("mal.js")
    )
    sidans = adress(vy.kommun, organ, slag)
    return sida(sammanhang.mall, sidans, f"{slag.rubrik} – {namn}", innehall)


# Flikarna, stilen, inledningen och den hopfällda delen om sidan.
def ramen(sammanhang: Sammanhang, organ: str, slag: Slag) -> str:
    return (
        flikar(sammanhang.underlag, organ, slag.id)
        + stil("mal.css", "spar.css")
        + slag.inledning
        + ram.om_sidan(slag.metod + AREN, slag.adr)
    )


def innehallet(vy: Vy, stegen: list[Steg]) -> str:
    sakerna = per_sak(vy.slag, stegen)
    return (
        sammandrag(vy.slag, sakerna)
        + urval(vy.slag, stegen)
        + tidslinje(vy, sakerna)
        + korten(vy, sakerna)
    )


def tidslinje(vy: Vy, sakerna: list[Sak]) -> str:
    huvud = "".join(f'<th scope="col">{a}</th>' for a in vy.ar)
    rader = "".join(rad(vy, nr, s) for nr, s in enumerate(sakerna))
    return (
        f'<h2 id="tidslinje">Tidslinje</h2>{teckenforklaring(vy.slag)}'
        f'<div class="tabell"><table class="tidslinje">{kolumner(vy.ar)}'
        f'<thead>{rubriker(vy.ar)}<tr><th scope="col">{vy.slag.sak}</th>{huvud}'
        f"</tr></thead><tbody>{rader}</tbody></table></div>"
    )


def rad(vy: Vy, nr: int, sak: Sak) -> str:
    celler = "".join(cell(vy, sak, a) for a in vy.ar)
    vem = "".join(f" <small>{escape(v)}</small>" for v in avsandarna(vy.slag, sak.steg))
    return (
        f'<tr {egenskaper(nr, sak)}><th scope="row">'
        f'<a href="#sak-{nr}">{escape(sak.namn)}</a>{vem}</th>{celler}</tr>'
    )


def cell(vy: Vy, sak: Sak, ar: int) -> str:
    finns = sak.aren
    if ar not in finns:
        return "<td></td>"
    klass = "band" + " start" * (ar - 1 not in finns) + " slut" * (ar + 1 not in finns)
    return f'<td class="{klass}">{arets(vy, sak.steg, ar)}</td>'
