"""Krav: K2, K13, K16, K23, K45, K57, K80 och K88 i docs/02-KRAV.md,
ADR-0013, ADR-0018, ADR-0039, ADR-0061, ADR-0068, ADR-0080 och ADR-0109.
Test: tests/test_upptack.py och tests/test_upptack_kommando.py.

Steg 1: `python -m kommunhandlingar.upptack <kommunfil> <arbetskatalog>
[--arkiv] [--start N]`. Hämtar kommunens källsidor, kör adaptern och
skriver kandidatlistan, utan att veta vilken plattform en källa är på
(`adaptrar/kallor.py`); med `--arkiv` arkivets lista, som blir tom när
tidsbudgetens mjuka gräns räknat från `--start` är passerad, eller när den
hårda nås under upptäckten (`arkivupptackt.py`). `hamtning.toml` läses
från repot som kommunfilen ligger i.
"""

import argparse
import sys
from collections import Counter
from functools import partial
from pathlib import Path

from kommunhandlingar import arkivupptackt, konfiguration, tidsbudget
from kommunhandlingar.fel import Hamtfel, Konfigurationsfel
from kommunhandlingar.hamtning import installningar
from kommunhandlingar.hamtning.hamtare import Lasare
from kommunhandlingar.hamtning.klient import Klient
from kommunhandlingar.kandidat import Fynd, lista, ordna, ordna_bakat, skriv


def upptack(kommun: konfiguration.Kommun, klient: Lasare) -> Fynd:
    hamta = partial(sida, klient)
    fynden = [(kalla.bakat, kalla.levande(hamta)) for kalla in kommun.kallor]
    framat = sum((fynd for bakat, fynd in fynden if not bakat), Fynd())
    nyast_forst = sum((fynd for bakat, fynd in fynden if bakat), Fynd())
    organordning = [o.id for o in kommun.organ]
    return Fynd(
        ordna(framat.kandidater, organordning)
        + ordna_bakat(nyast_forst.kandidater, organordning),
        [avvisad for _, fynd in fynden for avvisad in fynd.avvisade],
    )


def sida(klient: Lasare, adress: str) -> str:
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
        fynd = arkivupptackt.upptack(kommun, klient, arg.start)
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
