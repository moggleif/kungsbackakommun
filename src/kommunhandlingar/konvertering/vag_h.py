"""Krav: K84 i docs/02-KRAV.md, ADR-0005 och ADR-0105. Test: tests/test_vag_h.py.

Väg H avgör en rad som RapidOCR och Tesseract har läst. Raden är bekräftad
när två läsningar har samma tal i samma ordning: först de två, annars den
tredje läsningen tillsammans med en av dem. Den tredje läsningen görs bara
när de två är oense. Talen jämförs efter att minustecken och alla sorters
streck blivit bindestreck, mellanslag kring ett tankstreck eller kolon
mellan två siffror (`2026 – 2030`, `09: 35`) och mellanslaget före ett
procenttecken tagits bort. Båda motorerna läser gärna `09: 35` som
`09:35`, och klockslag och fastighetsbeteckningar är för vanliga för att
lämnas obekräftade. Priset är att `punkt 4: 20` kan sparas som `4:20`.
Ett bindestreck med mellanslag på båda sidor, eller flera streck i rad
(`18:55 —- 19:15`), räknas som ett tankstreck. Annars står mellanslagen
kring ett bindestreck eller minustecken kvar, eftersom `116 −4` är två
tal och inte `116-4`.

En rad där en siffra står direkt intill en bokstav i någon av de två
läsningarna bekräftas aldrig. Där läser båda motorerna gärna en bokstav
som en siffra på samma sätt, som `Kl.` som `K1.`.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

TAL = re.compile(r"-?\d+(?:[,.:/-]\d+)*%?")
STRECK = str.maketrans(dict.fromkeys("−–—‐‑‒", "-"))
KRING_TANKSTRECK = re.compile(r"(?<=\d)(?: *[–—][-–—]* *| +- +)(?=\d)")
PROCENT = re.compile(r"(\d) %")
BOKSTAV_VID_SIFFRA = re.compile(r"[^\W\d_]\d|\d[^\W\d_]")
KRING_KOLON = re.compile(r"(?<=\d) *: *(?=\d)")


@dataclass(frozen=True)
class Avgorande:
    tal: list[str] | None  # None: raden är inte bekräftad
    hur: str


def tal(text: str) -> list[str]:
    text = KRING_TANKSTRECK.sub("-", KRING_KOLON.sub(":", text)).translate(STRECK)
    return TAL.findall(PROCENT.sub(r"\1%", text))


def avgor(rapid: str, tesseract: str, tredje: Callable[[], str]) -> Avgorande:
    if any(BOKSTAV_VID_SIFFRA.search(t) for t in (rapid, tesseract)):
        return Avgorande(None, "bokstav-vid-siffra")
    forsta, andra = tal(rapid), tal(tesseract)
    if forsta == andra:
        return Avgorande(forsta, "eniga")
    avgorande = tal(tredje())
    if avgorande and avgorande == forsta:
        return Avgorande(forsta, "tredje-och-rapid")
    if avgorande and avgorande == andra:
        return Avgorande(andra, "tredje-och-tesseract")
    return Avgorande(None, "oense")
