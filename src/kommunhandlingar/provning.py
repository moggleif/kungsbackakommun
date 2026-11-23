"""Krav: K11 i docs/02-KRAV.md, ADR-0075 och ADR-0088. Test:
tests/test_hamta_kommando.py, tests/test_tidsbudget.py och
tests/test_versionslogg.py.

Steg 2:s körning över kandidaterna, en i taget i listans ordning. Den
slutar när delens tid gått ut eller vid budgetens hårda gräns, och de
kandidater som är kvar räknas då som väntande.
"""

from datetime import datetime

from kommunhandlingar.behandla import Steg2, behandla
from kommunhandlingar.kandidat import Kandidat
from kommunhandlingar.tidsbudget import Tidsgrans
from kommunhandlingar.utfall import AT_SIDAN, VANTAR, Korning, Utfall


def kor(steg: Steg2, kandidater: list[Kandidat], mjuk: datetime) -> Korning:
    korning = Korning()
    for nr, kandidat in enumerate(kandidater):
        utfall = prova(steg, kandidat, mjuk)
        korning.notera(utfall, kandidat.url)
        if utfall in (VANTAR, AT_SIDAN):
            korning.utfall[VANTAR.text] += len(kandidater) - nr - 1
            break
        korning.provade.append(kandidat)
    return korning


def prova(steg: Steg2, kandidat: Kandidat, mjuk: datetime) -> Utfall:
    """VANTAR när delens tid gått ut före kandidaten, AT_SIDAN vid den hårda gränsen."""
    try:
        if steg.tid() >= mjuk:
            return VANTAR
        return behandla(steg, kandidat)
    except Tidsgrans:
        return AT_SIDAN
