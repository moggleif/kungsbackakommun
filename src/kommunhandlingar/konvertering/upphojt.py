"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_upphojt.py.

Skyddet mot upphöjda tecken i väg H. En fotnotssiffra eller tvåan i m²
tappas ofta av båda OCR-motorerna på samma sätt, så att de blir eniga om
fel tal. En rad med ett upphöjt tecken bekräftas därför aldrig.

Radens bild delas i sammanhängande mörka delar, och delar som överlappar
i sidled slås ihop till ett tecken, så att pricken över i och ringen i å
hör till sin bokstav. Baslinjen är medianen av tecknens underkanter och
radens höjd är avståndet från baslinjen till tecknens överkant, räknat på
den tiondel av tecknen som når högst. Ett tecken är upphöjt när det är
högst sju tiondelar av radens höjd och slutar minst en fjärdedel av
radens höjd ovanför baslinjen. Det som är lägre än en femtedel av radens
höjd, som ett bindestreck, räknas inte. Delar som når bildens över- eller
underkant hör till raden ovanför eller nedanför, eftersom rutorna går in
i varandra, och räknas inte; en bild där alla delar gör det räknas som
upphöjd, eftersom den inte går att bedöma. Mörkt är det som är mörkare än
mitten mellan bildens ljusaste och mörkaste grå.

En rad som RapidOCR har hittat är upphöjd när den står bredvid en rad som
är minst en fjärdedel högre och slutar minst en fjärdedel av den radens
höjd ovanför dess underkant, som när en fotnotssiffra har fått en egen
rad. Rutorna är tilltagna, så gränsen för en rad är högre än för ett
tecken.
"""

import re
from statistics import median

from PIL import Image

LAG = 0.7
LAG_RAD = 0.8
OVER = 0.25
STRECK = 0.2
HOGST = 0.1
MORK = re.compile(rb"\x01+")


def har_upphojt(bild: Image.Image) -> bool:
    alla = delar(bild.convert("L"))
    inne = [d for d in alla if d[2] > 0 and d[3] < bild.height]
    if not inne:
        return bool(alla)
    tecken = sammanfogade(inne)
    baslinje = median(n for _, n in tecken)
    toppar = sorted(o for o, _ in tecken)
    hojd = baslinje - toppar[int(HOGST * len(toppar))]
    return any(
        STRECK * hojd <= n - o <= LAG * hojd and n <= baslinje - OVER * hojd
        for o, n in tecken
    )


def upphojd_rad(ruta: tuple, rutor: list[tuple]) -> bool:
    return any(
        andra[1] < ruta[3] <= andra[3] - OVER * (andra[3] - andra[1])
        and ruta[3] - ruta[1] <= LAG_RAD * (andra[3] - andra[1])
        for andra in rutor
    )


def sammanfogade(delar: list[tuple[int, int, int, int]]) -> list[tuple[int, int]]:
    """Överkant och underkant för varje tecken: delarna som överlappar i sidled."""
    tecken: list[list[int]] = []
    for x0, x1, o, n in sorted(delar):
        if tecken and x0 < tecken[-1][1]:
            sista = tecken[-1]
            sista[1:] = max(sista[1], x1), min(sista[2], o), max(sista[3], n)
        else:
            tecken.append([x0, x1, o, n])
    return [(o, n) for _, _, o, n in tecken]


def delar(bild: Image.Image) -> list[tuple[int, int, int, int]]:
    """Vänsterkant, högerkant, överkant och underkant, de två högra exklusive,
    för bildens sammanhängande mörka delar."""
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
