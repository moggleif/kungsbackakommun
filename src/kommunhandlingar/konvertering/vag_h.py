"""Krav: K84 i docs/02-KRAV.md, ADR-0005 och ADR-0105. Test: tests/test_vag_h.py.

Väg H avgör en rad som RapidOCR och Tesseract har läst. Raden är bekräftad
när två läsningar har samma tal i samma ordning: först de två, annars den
tredje läsningen tillsammans med en av dem. Den tredje läsningen görs bara
när de två är oense. Talen jämförs efter att minustecken och tankstreck
blivit bindestreck och mellanslaget före ett procenttecken tagits bort.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

TAL = re.compile(r"-?\d+(?:[,.:/-]\d+)*%?")
STRECK = str.maketrans({"−": "-", "–": "-"})
PROCENT = re.compile(r"(\d) %")


@dataclass(frozen=True)
class Avgorande:
    tal: list[str] | None  # None: raden är inte bekräftad
    hur: str


def tal(text: str) -> list[str]:
    return TAL.findall(PROCENT.sub(r"\1%", text.translate(STRECK)))


def avgor(rapid: str, tesseract: str, tredje: Callable[[], str]) -> Avgorande:
    forsta, andra = tal(rapid), tal(tesseract)
    if forsta == andra:
        return Avgorande(forsta, "eniga")
    avgorande = tal(tredje())
    if avgorande and avgorande == forsta:
        return Avgorande(forsta, "tredje-och-rapid")
    if avgorande and avgorande == andra:
        return Avgorande(andra, "tredje-och-tesseract")
    return Avgorande(None, "oense")
