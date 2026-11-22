"""Krav: K2, K13, K16, K23, K45, K57 och K80 i docs/02-KRAV.md, ADR-0013,
ADR-0018, ADR-0039, ADR-0061, ADR-0068 och ADR-0080.
Test: tests/test_upptack.py och tests/test_upptack_kommando.py.

Steg 1: `python -m kommunhandlingar.upptack <kommunfil> <arbetskatalog>
[--arkiv] [--start N]`. Hämtar kommunens källsidor, kör adaptern och
skriver kandidatlistan; med `--arkiv` arkivets lista, som blir tom när
tidsbudgetens mjuka gräns räknat från `--start` är passerad, eller när den
hårda nås under upptäckten. `hamtning.toml` läses från repot som
kommunfilen ligger i.
"""

import argparse
import sys
from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

from kommunhandlingar import konfiguration, tidsbudget
from kommunhandlingar.adaptrar import (
    episerver_arkiv,
    meetingsplus,
    sitevision,
    sitevision_arkiv,
    sitevision_projekt,
)
from kommunhandlingar.fel import Hamtfel, Konfigurationsfel
from kommunhandlingar.hamtning import installningar
from kommunhandlingar.hamtning.klient import Klient
from kommunhandlingar.kandidat import Fynd, lista, ordna, ordna_bakat, skriv
from kommunhandlingar.tidsbudget import Tidsgrans


def upptack(kommun: konfiguration.Kommun, klient) -> Fynd:
    motena = sum((motessidorna(kalla, klient) for kalla in kommun.kallor), Fynd())
    projekt = projekten(kommun, klient, {k.kallnyckel for k in motena.kandidater})
    meetingsplus_fynd = meetingsplus_kallorna(kommun, klient)
    organordning = [o.id for o in kommun.organ]
    # Meetings Plus har hela historiken levande: nyast först, som arkivet (ADR-0080).
    return Fynd(
        ordna(motena.kandidater + projekt.kandidater, organordning)
        + ordna_bakat(meetingsplus_fynd.kandidater, organordning),
        motena.avvisade + projekt.avvisade + meetingsplus_fynd.avvisade,
    )


def motessidorna(kalla: sitevision.Kalla, klient) -> Fynd:
    html = {adress: sida(klient, adress) for adress in kalla.sidor.values()}
    return sitevision.upptack(kalla, html)


def meetingsplus_kallorna(kommun: konfiguration.Kommun, klient) -> Fynd:
    hamta = partial(sida, klient)
    kallorna = kommun.meetingsplus_kallor
    return sum((meetingsplus.upptack(k, hamta) for k in kallorna), Fynd())


def projekten(kommun: konfiguration.Kommun, klient, moten: set[str]) -> Fynd:
    """Projektsidornas filer; en fil som också står på en mötessida är mötets."""
    hamta = partial(sida, klient)
    listorna = (sitevision_projekt.upptack(k.projekt, hamta) for k in kommun.kallor)
    fynd = sum(listorna, Fynd())
    egna = [k for k in fynd.kandidater if k.kallnyckel not in moten]
    return replace(fynd, kandidater=egna)


def upptack_arkiv(kommun: konfiguration.Kommun, klient, start: datetime | None) -> Fynd:
    """Arkivet frågas inte efter den mjuka gränsen och avbryts vid den hårda."""
    if datetime.now(UTC) >= tidsbudget.mjuk_grans(start):
        return Fynd(noteringar=["väntar på nästa körning; tidsbudgeten är slut"])
    if start:
        tidsbudget.starta_hard_grans(start, datetime.now(UTC))
    try:
        return las_arkivet(kommun, klient)
    except Tidsgrans:
        return Fynd(noteringar=["avbrutet vid tidsbudgetens hårda gräns"])
    finally:
        tidsbudget.stoppa()


def las_arkivet(kommun: konfiguration.Kommun, klient) -> Fynd:
    lasningar = [(sitevision_arkiv.upptack, k) for k in kommun.kallor if k.wayback] + [
        (episerver_arkiv.upptack, k) for k in kommun.arkivkallor
    ]
    fynd = sum((upptack_kallan(k, klient) for upptack_kallan, k in lasningar), Fynd())
    organordning = [o.id for o in kommun.organ]
    return replace(fynd, kandidater=ordna_bakat(fynd.kandidater, organordning))


def sida(klient, adress: str) -> str:
    try:
        return klient.text(adress)
    except Hamtfel as fel:
        raise Hamtfel(fel.orsak, adress) from fel


def sammanfattning(kommun: konfiguration.Kommun, fynd: Fynd) -> str:
    antal = Counter(k.organ for k in fynd.kandidater)
    rader = [
        f"{len(fynd.kandidater)} kandidater, {len(fynd.avvisade)} filer utan kandidat"
    ]
    rader += [f"  {o.id}: {antal[o.id]}" for o in kommun.organ]
    rader += [
        f"Ingen kandidat: {a.filnamn} ({a.orsak}) på {a.kalla}" for a in fynd.avvisade
    ]
    rader += [f"Arkivet: {notering}" for notering in fynd.noteringar]
    return "\n".join(rader)


def utanfor_repot(katalog: Path, rot: Path) -> Path:
    if katalog.resolve().is_relative_to(rot.resolve()):
        raise Konfigurationsfel(f"arbetskatalogen {katalog} ligger i repot")
    return katalog


def main(arg: argparse.Namespace) -> None:
    rot = arg.kommunfil.resolve().parent.parent
    katalog = utanfor_repot(arg.arbetskatalog, rot)
    kommun = konfiguration.las(arg.kommunfil)
    klient = Klient(installningar.las(rot / "hamtning.toml"))
    if arg.arkiv:
        fynd = upptack_arkiv(kommun, klient, arg.start)
    else:
        fynd = upptack(kommun, klient)
    katalog.mkdir(parents=True, exist_ok=True)
    skriv(fynd.kandidater, lista(katalog, kommun.id, arg.arkiv))
    print(sammanfattning(kommun, fynd))


def argument() -> argparse.Namespace:
    tolk = argparse.ArgumentParser(prog="python -m kommunhandlingar.upptack")
    tolk.add_argument("kommunfil", type=Path)
    tolk.add_argument("arbetskatalog", type=Path)
    tolk.add_argument("--arkiv", action="store_true", help="arkivets lista (K16)")
    tolk.add_argument("--start", type=tidsbudget.tidpunkt, help=tidsbudget.START)
    return tolk.parse_args()


# Nattkörningen hoppar över det levande vid den här koden och går vidare
# (ADR-0061); varje annat fel stoppar den.
KALLAN_STOPPADE = 3


def kommandot(arg: argparse.Namespace) -> None:
    try:
        main(arg)
    except Konfigurationsfel as fel:
        sys.exit(f"Stoppad: {fel}")
    except Hamtfel as fel:
        print(f"Stoppad: {fel}", flush=True)
        sys.exit(KALLAN_STOPPADE)


if __name__ == "__main__":
    kommandot(argument())
