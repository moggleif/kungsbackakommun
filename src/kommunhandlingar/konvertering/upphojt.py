"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_upphojt.py.

Skyddet mot upphöjda tecken i väg H. En fotnotssiffra eller tvåan i m²
tappas ofta av båda OCR-motorerna på samma sätt, så att de blir eniga om
fel tal. En rad med ett upphöjt tecken bekräftas därför aldrig.

Utsnittet tas med marginal kring radens ruta och delas i sammanhängande
mörka delar. En del räknas bara när den inte når utsnittets kant och dess
mitt ligger inom rutan i höjdled; det andra hör till raderna ovanför och
nedanför, eftersom rutorna går in i varandra. Ett streck, minst fyra
gånger så brett som högt, räknas inte, så att en understrykning eller en
tabellinje inte slår ihop raden till ett tecken. Två delar är samma tecken
när de överlappar i sidled med minst halva den smalares bredd, så att
pricken över i och ringen i å hör till sin bokstav, men inte en siffra som
bara nuddar bokstaven före. Baslinjen är medianen av tecknens underkanter
och radens höjd är avståndet från baslinjen till tecknens överkant, räknat
på den tiondel av tecknen som når högst. Ett tecken är upphöjt när det är
högst sju tiondelar av radens höjd och slutar minst en fjärdedel av
radens höjd ovanför baslinjen. Det som är lägre än en femtedel av radens
höjd räknas inte. Har utsnittet mörka delar men inga som räknas, räknas
raden som upphöjd, eftersom den inte går att bedöma. Delarna hittas av
`morka_delar`.

En rad som RapidOCR har hittat är upphöjd när den står bredvid en rad,
högst den radens höjd ifrån i sidled, som är minst en fjärdedel högre,
och slutar minst en fjärdedel av den radens höjd ovanför dess underkant,
som när en fotnotssiffra har fått en egen rad. Rutorna är tilltagna, så
gränsen för en rad är högre än för ett tecken.
"""

from statistics import median

from PIL import Image

from kommunhandlingar.konvertering.morka_delar import delar

LAG = 0.7
LAG_RAD = 0.8
OVER = 0.25
STRECK = 0.2
HOGST = 0.1


def har_upphojt(bild: Image.Image, rad: tuple[int, int]) -> bool:
    """Om utsnittet har ett upphöjt tecken; `rad` är rutans över- och
    underkant i utsnittet."""
    alla = delar(bild.convert("L"))
    inne = [d for d in alla if raknas(d, rad, bild.height)]
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


def raknas(del_: tuple[int, int, int, int], rad: tuple[int, int], hojd: int) -> bool:
    x0, x1, o, n = del_
    vid_kanten = o == 0 or n == hojd
    return not vid_kanten and rad[0] <= (o + n) / 2 <= rad[1] and x1 - x0 < 4 * (n - o)


def upphojd_rad(ruta: tuple, rutor: list[tuple]) -> bool:
    return any(bredvid(ruta, andra) and lagre(ruta, andra) for andra in rutor)


def bredvid(ruta: tuple, andra: tuple) -> bool:
    hojd = andra[3] - andra[1]
    return ruta[0] - andra[2] <= hojd and andra[0] - ruta[2] <= hojd


def lagre(ruta: tuple, andra: tuple) -> bool:
    hojd = andra[3] - andra[1]
    return (
        andra[1] < ruta[3] <= andra[3] - OVER * hojd
        and ruta[3] - ruta[1] <= LAG_RAD * hojd
    )


def sammanfogade(delar: list[tuple[int, int, int, int]]) -> list[tuple[int, int]]:
    """Överkant och underkant för varje tecken."""
    tecken: list[list[int]] = []
    for x0, x1, o, n in sorted(delar):
        if tecken and samma_tecken(tecken[-1], x0, x1):
            sista = tecken[-1]
            sista[1:] = max(sista[1], x1), min(sista[2], o), max(sista[3], n)
        else:
            tecken.append([x0, x1, o, n])
    return [(o, n) for _, _, o, n in tecken]


def samma_tecken(tecknet: list[int], x0: int, x1: int) -> bool:
    overlapp = min(tecknet[1], x1) - x0
    return overlapp >= min(tecknet[1] - tecknet[0], x1 - x0) / 2
