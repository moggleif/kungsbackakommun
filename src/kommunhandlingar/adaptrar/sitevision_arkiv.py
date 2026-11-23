"""Krav: K16 i docs/02-KRAV.md, ADR-0018, ADR-0027, ADR-0011 och ADR-0062.
Test: tests/test_sitevision_arkiv.py.

En Sitevision-källa ur Internet Archive. Den sista ögonblicksbilden per år
av mötessidan för varje organ i källans `wayback` läses med
Sitevision-adaptern, den nyaste först, och varje fil får arkivets största
kopia av sin nyaste version. En fråga som arkivet inte besvarar, och en
mötessida som arkivet inte har, hoppas över och returneras som en notering.
"""

from dataclasses import replace
from urllib.parse import urlsplit

from kommunhandlingar.adaptrar import sitevision, wayback
from kommunhandlingar.adaptrar.sitevision_html import NEDLADDNING, forekomster
from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.hamtning.hamtare import Lasare
from kommunhandlingar.kandidat import Avvisad, Fynd

# Ögonblicksbilderna (adress, HTML) och varför andra inte gick att läsa.
Bilder = tuple[list[tuple[str, str]], list[str]]


def upptack(kalla: sitevision.Kalla, klient: Lasare) -> Fynd:
    try:
        filer = nyaste_kopior(klient, kalla)
    except Hamtfel as fel:
        return Fynd(noteringar=[str(fel)])
    sidor, noteringar = [], []
    for organ in kalla.wayback:
        bilder, fel = ogonblicksbilder(klient, kalla.sidor[organ])
        sidor += [(organ, bild, html) for bild, html in bilder]
        noteringar += fel
    lasta = sitevision.las(replace(kalla, arkiv=True), sidor)
    return med_kopior(lasta, filer) + Fynd(noteringar=noteringar)


def nyaste_kopior(klient: Lasare, kalla: sitevision.Kalla) -> dict[str, wayback.Kopia]:
    vardar = sorted({urlsplit(adress).netloc for adress in kalla.sidor.values()})
    kopior = [
        kopia
        for vard in vardar
        for kopia in wayback.fraga_under(klient, f"{vard}/download/", "application/pdf")
        if NEDLADDNING.match(kopia.original)
    ]
    return wayback.basta(kopior, nyckel, rang)


def nyckel(kopia: wayback.Kopia) -> str:
    return f"sitevision:{NEDLADDNING.match(kopia.original)[1]}"


def rang(kopia: wayback.Kopia) -> tuple[int, int, int]:
    """Nyaste versionen, sedan största kopian, och vid lika den äldsta."""
    return int(NEDLADDNING.match(kopia.original)[2]), *wayback.storst(kopia)


def ogonblicksbilder(klient: Lasare, sidadress: str) -> Bilder:
    """Den sista ögonblicksbilden per år, den nyaste först, med sin HTML."""
    try:
        kopior = wayback.fraga(klient, sidadress, "text/html")
    except Hamtfel as fel:
        return [], [str(fel)]
    if not kopior:
        return [], [f"{sidadress}: ingen kopia av mötessidan i arkivet"]
    bilder, fel = [], []
    for adress in map(wayback.adress, wayback.sista_per_ar(kopior)):
        lasta, olasta = bild(klient, adress)
        bilder += lasta
        fel += olasta
    return bilder, fel


def bild(klient: Lasare, adress: str) -> Bilder:
    """Ögonblicksbilden med sin HTML, eller varför den inte går att läsa."""
    try:
        html = klient.text(adress)
        forekomster(html, adress)  # en kapad sida går inte att läsa
    except Hamtfel as fel:
        return [], [f"{adress}: {fel.orsak}"]
    except ValueError:
        return [], [f"{adress}: sidan går inte att läsa"]
    return [(adress, html)], []


def med_kopior(fynd: Fynd, filer: dict[str, wayback.Kopia]) -> Fynd:
    """En kandidat utan kopia i arkivet blir en fil utan kandidat."""
    kopior = [(k, filer.get(k.kallnyckel)) for k in fynd.kandidater]
    return replace(
        fynd,
        kandidater=[
            replace(k, url=wayback.adress(c)) for k, c in kopior if c is not None
        ],
        avvisade=fynd.avvisade
        + [
            Avvisad(k.kalla, k.filnamn, "ingen kopia i arkivet")
            for k, c in kopior
            if c is None
        ],
    )
