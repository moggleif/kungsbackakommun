"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_upphojt.py.

En bilds sammanhängande mörka delar, för skyddet mot upphöjda tecken
(`upphojt`). Mörkt är det som är mörkare än mitten mellan bildens
ljusaste och mörkaste grå. Varje rad i bilden delas i löpor av mörka
pixlar, och en löpa hör ihop med löporna på raden ovanför som den rör,
också snett.
"""

import re

from PIL import Image

MORK = re.compile(rb"\x01+")
# En löpa: raden, eller löpans nummer, och dess början och första pixel efter.
Lopa = tuple[int, int, int]


def delar(bild: Image.Image) -> list[tuple[int, int, int, int]]:
    """Varje sammanhängande mörk del som (x0, x1, överkant, underkant), där
    x1 och underkanten är första pixeln utanför delen."""
    pixlar = morka(bild)
    foralder: list[int] = []
    lopor: list[Lopa] = []
    aktuella: list[Lopa] = []
    for y in range(bild.height):
        forra, aktuella = aktuella, []
        for start, slut in radens_lopor(pixlar, y, bild.width):
            foralder.append(len(foralder))
            lopor.append((y, start, slut))
            aktuella.append((len(foralder) - 1, start, slut))
        koppla(foralder, aktuella, forra)
    return omfang(foralder, lopor)


def morka(bild: Image.Image) -> bytes:
    """En byte per pixel: 1 för mörkt, 0 för ljust."""
    ljus, mork = bild.getextrema()
    grans = (ljus + mork) / 2
    return bild.point(lambda v: 1 if v < grans else 0).tobytes()


def radens_lopor(pixlar: bytes, y: int, bredd: int) -> list[tuple[int, int]]:
    """Löporna av mörka pixlar på rad y, som (början, första pixeln efter)."""
    borjan = y * bredd
    return [
        (m.start() - borjan, m.end() - borjan)
        for m in MORK.finditer(pixlar, borjan, borjan + bredd)
    ]


def koppla(foralder: list[int], aktuella: list[Lopa], forra: list[Lopa]) -> None:
    """Förenar varje löpa med löporna på raden ovanför som den rör, också snett."""
    k = 0
    for i, start, slut in aktuella:
        while k < len(forra) and forra[k][2] < start:
            k += 1
        j = k
        while j < len(forra) and forra[j][1] <= slut:
            foralder[rot(foralder, i)] = rot(foralder, forra[j][0])
            j += 1


def rot(foralder: list[int], i: int) -> int:
    while foralder[i] != i:
        foralder[i] = foralder[foralder[i]]
        i = foralder[i]
    return i


def omfang(foralder: list[int], lopor: list) -> list[tuple[int, int, int, int]]:
    delar: dict[int, tuple[int, int, int, int]] = {}
    for i, (y, start, slut) in enumerate(lopor):
        x0, x1, o, n = delar.get(rot(foralder, i), (start, slut, y, y + 1))
        delar[rot(foralder, i)] = (
            min(x0, start),
            max(x1, slut),
            min(o, y),
            max(n, y + 1),
        )
    return list(delar.values())
