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


def delar(bild: Image.Image) -> list[tuple[int, int, int, int]]:
    """Varje sammanhängande mörk del som (x0, x1, överkant, underkant), där
    x1 och underkanten är första pixeln utanför delen."""
    ljus, mork = bild.getextrema()
    grans = (ljus + mork) / 2
    pixlar = bild.point(lambda v: 1 if v < grans else 0).tobytes()
    bredd = bild.width
    foralder: list[int] = []
    lopor: list[tuple[int, int, int]] = []
    forra: list[tuple[int, int, int]] = []
    for y in range(bild.height):
        aktuella = []
        borjan = y * bredd
        for m in MORK.finditer(pixlar, borjan, borjan + bredd):
            foralder.append(len(foralder))
            lopor.append((y, m.start() - borjan, m.end() - borjan))
            aktuella.append((len(foralder) - 1, m.start() - borjan, m.end() - borjan))
        koppla(foralder, aktuella, forra)
        forra = aktuella
    return omfang(foralder, lopor)


def koppla(foralder: list[int], aktuella: list, forra: list) -> None:
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
