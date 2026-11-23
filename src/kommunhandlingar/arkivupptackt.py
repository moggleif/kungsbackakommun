"""Krav: K11, K16, K23 och K88 i docs/02-KRAV.md, ADR-0018, ADR-0039, ADR-0075
och ADR-0109.
Test: tests/test_upptack.py och tests/test_upptack_kommando.py.

Steg 1 för arkivet: Wayback-kopiorna av källornas sidor och Episervers
arkiv, nyast först. Arkivet frågas inte efter tidsbudgetens mjuka gräns,
och upptäckten avbryts vid den hårda.
"""

from dataclasses import replace
from datetime import UTC, datetime

from kommunhandlingar import konfiguration, tidsbudget
from kommunhandlingar.hamtning.hamtare import Lasare
from kommunhandlingar.kandidat import Fynd, ordna_bakat
from kommunhandlingar.tidsbudget import Tidsgrans


def upptack(
    kommun: konfiguration.Kommun, klient: Lasare, start: datetime | None
) -> Fynd:
    if datetime.now(UTC) >= tidsbudget.mjuk_grans(start):
        return Fynd(noteringar=["väntar på nästa körning; tidsbudgeten är slut"])
    if start:
        tidsbudget.starta_hard_grans(start, datetime.now(UTC))
    try:
        return las(kommun, klient)
    except Tidsgrans:
        return Fynd(noteringar=["avbrutet vid tidsbudgetens hårda gräns"])
    finally:
        tidsbudget.stoppa()


def las(kommun: konfiguration.Kommun, klient: Lasare) -> Fynd:
    fynd = sum((kalla.arkivet(klient) for kalla in kommun.kallor), Fynd())
    organordning = [o.id for o in kommun.organ]
    return replace(fynd, kandidater=ordna_bakat(fynd.kandidater, organordning))
