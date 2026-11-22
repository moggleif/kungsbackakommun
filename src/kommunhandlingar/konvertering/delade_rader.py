"""Krav: K5 i docs/02-KRAV.md, ADR-0028 och ADR-0029. Test:
tests/test_delade_rader.py och tests/test_delade.py.

En rad i en tabell med linjer delas efter rutornas textrader, kolumn för
kolumn, när en cell rymmer mer än ett tal (`delade.py`,
docs/03-ARKITEKTUR.md#tabeller-med-linjer-och-flera-tal-i-en-cell).
"""

from kommunhandlingar.konvertering.falt import RADTOLERANS
from kommunhandlingar.konvertering.sammanslagna import Textrad
from kommunhandlingar.konvertering.tabeller import flera_tal, talfalt

Platser = list[list[Textrad]]


def dela(platser: Platser, slag: set[str], forsta: bool) -> list[list[str]] | None:
    """Raden som den står när ingen cell rymmer mer än ett tal, annars
    delad nerifrån; None när det inte går ihop. En rubrikcell och en text
    över en kolumngräns får bara stå i första raden. En rad med en delad
    cell ska ha sina tal på samma höjd, utom i första raden när den
    första kolumnen med text har högst en textrad: då antas den vara en
    rubrik i flera rader."""
    if slag & {"rubrik", "over"} and not forsta:
        return None
    if flera(platser):
        return nerifran(platser)
    if slag <= {"egen"} or talen_i_hojd(platser):
        return [celler(platser)]
    forsta_med_text = next(filter(None, platser), [])
    return [celler(platser)] if forsta and len(forsta_med_text) <= 1 else None


def nerifran(platser: Platser) -> list[list[str]] | None:
    """Den nedersta textraden blir en egen rad när den står på samma höjd
    i varje cell som inte är tom. Det som står ovanför blir en rad när
    varje textrad med ett tal står på samma höjd som en textrad i
    varje cell."""
    if not flera(platser):
        return [celler(platser)] if talen_i_hojd(platser) else None
    sista = [p[-1].topp for p in platser if p]
    nederst = [p[-1:] for p in platser]
    if max(sista) - min(sista) > RADTOLERANS or flera(nederst):
        return None
    ovanfor = nerifran([p[:-1] for p in platser])
    return None if ovanfor is None else [*ovanfor, celler(nederst)]


def talen_i_hojd(platser: Platser) -> bool:
    hojder = [r.topp for p in platser for r in p if r.har_tal]
    if not hojder:
        return True
    if max(hojder) - min(hojder) > RADTOLERANS:
        return False
    return all(i_hojd(p, hojder[0]) for p in platser if p)


def i_hojd(ruta: list[Textrad], hojd: float) -> bool:
    """En textrad på talens höjd, eller talen mitt emellan två textrader,
    som en etikett som bryts runt sina tal. Mitt emellan är inom en sjättedel
    av avståndet, så att talen inte står närmare den ena."""
    toppar = [r.topp for r in ruta]
    if any(abs(t - hojd) <= RADTOLERANS for t in toppar):
        return True
    ovan = [t for t in toppar if t < hojd]
    under = [t for t in toppar if t > hojd]
    if not ovan or not under:
        return False
    marginal = min(RADTOLERANS, (min(under) - max(ovan)) / 6)
    return abs((max(ovan) + min(under)) / 2 - hojd) <= marginal


def celler(platser: Platser) -> list[str]:
    return ["\n".join(r.text for r in p) for p in platser]


def flera(platser: Platser) -> bool:
    """Mer än ett tal i någon cell, efter cellens text eller dess fält."""
    if any(map(flera_tal, celler(platser))):
        return True
    rader = (r for p in platser for r in p)
    return any(sum(1 for f in r.falt if talfalt(f)) > 1 for r in rader)
