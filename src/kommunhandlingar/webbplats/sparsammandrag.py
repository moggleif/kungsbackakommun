"""Krav: K36, K37, K38 och K39 i docs/02-KRAV.md, ADR-0057, ADR-0058 och
ADR-0059.
Test: tests/test_lokalbehov.py, tests/test_initiativ.py, tests/test_ram.py.

Spårsidans sammandrag – antalet saker per fas och, när slaget har en
avsändare, per avsändare – och knapparna för urvalet.
"""

from collections import Counter
from html import escape

from kommunhandlingar.webbplats import ram
from kommunhandlingar.webbplats.spar import Slag, Steg
from kommunhandlingar.webbplats.sparsak import (
    Sak,
    avsandarna,
    markor_for,
    senaste_ar,
)


def sammandrag(slag: Slag, sakerna: list[Sak]) -> str:
    rutor = per_fas(slag, sakerna)
    if slag.avsandare:
        rutor += per_avsandare(slag, sakerna)
    return f'<div class="sammandrag">{rutor}</div>'


def per_fas(slag: Slag, sakerna: list[Sak]) -> str:
    siffror = [
        (betyder, sum(fas in sak.faserna for sak in sakerna))
        for fas, (_, betyder) in slag.faser.items()
    ]
    rubrik = f"{slag.antal.capitalize()} per fas"
    return ruta(rubrik, siffror, f"{slag.antal} som någon gång nått fasen")


def per_avsandare(slag: Slag, sakerna: list[Sak]) -> str:
    vem = Counter(v for sak in sakerna for v in avsandarna(slag, sak.steg))
    rubrik = f"{slag.antal.capitalize()} per avsändare"
    return ruta(rubrik, sorted(vem.items()), f"{slag.antal} per avsändare")


def ruta(rubrik: str, siffror: list[tuple[str, int]], forklaring: str) -> str:
    rader = "".join(f"<div><dt>{escape(t)}</dt><dd>{n}</dd></div>" for t, n in siffror)
    return (
        f'<section class="ruta"><h3>{rubrik}</h3><dl class="siffror">{rader}</dl>'
        f"<p><small>Antal {forklaring} enligt poolen.</small></p></section>"
    )


def urval(slag: Slag, stegen: list[Steg]) -> str:
    val = [("alla", "Alla")]
    if senaste := senaste_ar(slag, stegen):
        val.append(("senaste", f"I {slag.rubrik.lower()} {senaste}"))
    val += [(fas, betyder.capitalize()) for fas, (_, betyder) in slag.faser.items()][1:]
    val += [(markor_for(v), v) for v in sorted(avsandarna(slag, stegen))]
    return ram.urval(val)
