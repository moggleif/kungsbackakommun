"""Krav: K6 i docs/02-KRAV.md, ADR-0038, ADR-0103. Test: tests/test_ordning.py.

Text som inte går att läsa i ordning: tecken som står på högkant inne i
en tabell, eller tecken på samma rad som ritats ovanpå varandra, som en
kolumn som flyter in i nästa. pdfplumber blandar ihop dem till rader som
`aktivitetsstö2d0225-05-21`, och sidans tal räknas då inte som
bekräftade (docs/03-ARKITEKTUR.md#konvertering-och-kvalitet). Text på
högkant utanför tabellerna läses för sig (K41) och räknas här bara när
den har en siffra (ADR-0103); `las_sida.textsida` prövar att den inte
ändrar hur resten av sidan läses.
"""

from collections import defaultdict
from itertools import pairwise

from pdfplumber.page import Page

from kommunhandlingar.konvertering.tabeller import i_tabell


def i_oordning(sida: Page, rutor: list[tuple]) -> bool:
    tecken = list(enumerate(c for c in sida.chars if not c["text"].isspace()))
    pa_hogkant = [c for _, c in tecken if not c["upright"]]
    if any(c["text"].isdigit() or i_tabell(c, rutor) for c in pa_hogkant):
        return True
    rader = defaultdict(list)
    for i, c in (t for t in tecken if t[1]["upright"]):
        rader[round(c["top"])].append((i, c))
    i_lage = [sorted(r, key=lambda t: t[1]["x0"]) for r in rader.values()]
    return any(tacker(a, b) for r in i_lage for a, b in pairwise(r))


def tacker(vanster: tuple[int, dict], hoger: tuple[int, dict]) -> bool:
    """Två tecken som täcker mer än halva det smalare av dem och inte står
    intill varandra i textlagret, mellanslag oräknade. Grannar som
    överlappar, som i kursiv stil, räknas inte, och inte heller samma
    tecken två gånger, som en fetstil som ritats två gånger."""
    (i, a), (j, b) = vanster, hoger
    smalast = min(a["x1"] - a["x0"], b["x1"] - b["x0"])
    grannar = abs(i - j) == 1
    return not grannar and a["text"] != b["text"] and a["x1"] - b["x0"] > smalast / 2
