"""Krav: K14, K18, K22, K26, K28, K36, K37, K39, K46, K47, K48, K54, K56, K58, K60,
K62 och K96 i docs/02-KRAV.md.
Test: tests/test_webbplats.py, tests/test_projekt.py,
tests/test_webbplats_dokument.py, tests/test_kalender.py, tests/test_mal.py,
tests/test_uppfoljningar.py, tests/test_lokalbehov.py, tests/test_initiativ.py,
tests/test_dokumentindex.py, tests/test_paragrafindex.py,
tests/test_sammantradessida.py, tests/test_sokindex.py, tests/test_sokdokument.py.

Underlaget läses i `inlasning`; här skrivs sidorna i ordningen startsida,
per kommun och sökindex.
"""

import shutil
from datetime import datetime
from pathlib import Path

from kommunhandlingar import pool
from kommunhandlingar.fel import Datafel
from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import (
    adresser,
    dokumentindex,
    inlasning,
    kalender,
    paragrafindex,
    sammantradesbygge,
    sidor,
    sokdokument,
    sokindex,
)
from kommunhandlingar.webbplats.bygge import Bygge
from kommunhandlingar.webbplats.dokumentsida import dokumentsida
from kommunhandlingar.webbplats.kalendersida import kalendersida
from kommunhandlingar.webbplats.llms import llms
from kommunhandlingar.webbplats.mall import Mall, sida
from kommunhandlingar.webbplats.malsida import adress as malsidans_adress
from kommunhandlingar.webbplats.malsida import malsida
from kommunhandlingar.webbplats.meny import oversiktsnamn
from kommunhandlingar.webbplats.organsida import organsida
from kommunhandlingar.webbplats.oversikt import oversikt, oversiktens_adresser
from kommunhandlingar.webbplats.rakning import okanda, rakna
from kommunhandlingar.webbplats.sammanhang import Sammanhang
from kommunhandlingar.webbplats.slagen import SLAGEN
from kommunhandlingar.webbplats.sparsida import adress as sparets_adress
from kommunhandlingar.webbplats.sparsida import sparsida


def bygg(rot: Path, ut: Path, repo: str, byggd: datetime) -> Mall:  # noqa: PLR0913  # undantag: __main__ och regionens datarepo bygger genom signaturen
    bygge = Bygge(ut, *inlasning.las(rot, repo, byggd))
    ut.mkdir(parents=True, exist_ok=True)
    if not bygge.mall.en_kommun:
        bygge.skriv(adresser.STARTSIDA, sidor.startsida(bygge.mall))
    bygge.skriv("llms.txt", llms(bygge))
    sokgrupper = []
    for kommun in bygge.mall.kommuner:
        sokgrupper.extend(bygg_kommun(bygge, rot / "data" / kommun.id, kommun))
        if kommun.id in bygge.mall.kalendrar:
            bygg_kalender(bygge, rot, kommun)
    sokindex.skriv(ut, sokgrupper)
    return bygge.mall


# Kommunens grupper i sökindexet lämnas tillbaka.
def bygg_kommun(bygge: Bygge, katalog: Path, kommun: Kommun) -> list[dict]:
    dokument, stycken = skriv_dokumenten(bygge, katalog, kommun)
    dokumentindex.skriv(bygge.ut, dokument, katalog)
    paragrafindex.skriv(bygge.ut, stycken, katalog)
    underlag = sammantradesbygge.underlag(
        bygge.sammanhang(kommun), katalog, (dokument, stycken)
    )
    sammantradesbygge.bygg(bygge.ut, bygge.mall, underlag)
    bygge.skriv(
        adresser.status(kommun.id), sidor.statussida(bygge.mall, kommun, dokument)
    )
    bygg_oversikten(bygge, kommun, dokument)
    bygg_organen(bygge, kommun, dokument)
    return kommunens_sokgrupper(kommun, underlag.paragrafer, dokument)


def kommunens_sokgrupper(
    kommun: Kommun, paragrafer: list[dict], dokument: list[dict]
) -> list[dict]:
    return [sokindex.grupp(kommun, paragrafer), sokdokument.grupp(kommun, dokument)]


# Varje dokuments sida skrivs när det läses, så att poolens text inte hålls
# i minnet. Dokumentens fält och paragraferna lämnas tillbaka.
def skriv_dokumenten(
    bygge: Bygge, katalog: Path, kommun: Kommun
) -> tuple[list[dict], list[dict]]:
    (bygge.ut / kommun.id).mkdir(exist_ok=True)
    dokument, stycken = [], []
    for fil, falt, text in pool.dokumenten(katalog):
        prova(fil, falt, kommun)
        falt["adress"] = adresser.dokumentsida(fil.relative_to(katalog).as_posix())
        adress = adresser.i_kommunen(kommun.id, falt["adress"])
        (bygge.ut / adress).parent.mkdir(parents=True, exist_ok=True)
        sidfil = bygge.skriv(adress, dokumentsida(bygge.sammanhang(kommun), falt, text))
        kopiera_tabeller(fil, sidfil)
        dokument.append(falt)
        stycken += paragrafindex.av_dokument(falt, text, katalog)
    return dokument, stycken


def bygg_oversikten(bygge: Bygge, kommun: Kommun, dokument: list[dict]) -> None:
    mall = bygge.mall
    rader = rakna(kommun, dokument, mall.byggd.date())
    innehall = oversikt(bygge.sammanhang(kommun), rader, dokument)
    rubrik = oversiktsnamn(mall.kommuner, kommun)
    for adress in oversiktens_adresser(mall, kommun):
        bygge.skriv(adress, sida(mall, adress, rubrik, innehall))


def bygg_organen(bygge: Bygge, kommun: Kommun, dokument: list[dict]) -> None:
    sammanhang = bygge.sammanhang(kommun)
    for rad in rakna(kommun, dokument, bygge.mall.byggd.date()):
        organets = [d for d in dokument if d["organ"] == rad.id]
        html = organsida(sammanhang, rad, organets)
        bygge.skriv(adresser.organsida(kommun.id, rad.id), html)
        if malen := [m for m in sammanhang.underlag.malen if m.organ == rad.id]:
            html = malsida(sammanhang, malen, organets)
            bygge.skriv(malsidans_adress(kommun, rad.id), html)
        bygg_sparen(bygge, sammanhang, rad.id)


def bygg_sparen(bygge: Bygge, sammanhang: Sammanhang, organ: str) -> None:
    for slag in SLAGEN:
        alla = sammanhang.underlag.stegen(slag.id)
        if stegen := [s for s in alla if s.organ == organ]:
            html = sparsida(sammanhang, slag, stegen)
            bygge.skriv(sparets_adress(sammanhang.kommun, organ, slag), html)


def bygg_kalender(bygge: Bygge, rot: Path, kommun: Kommun) -> None:
    sammantraden = inlasning.las_kalender(rot, kommun)
    sammantraden = kalender.med_sidor(sammantraden, bygge.ut / kommun.id)
    html = kalendersida(bygge.mall, kommun, sammantraden)
    bygge.skriv(adresser.kalender(kommun.id), html)


def prova(fil: Path, falt: dict, kommun: Kommun) -> None:
    if fel := okanda(falt, kommun):
        raise Datafel(f"{fil}: okänt {', '.join(fel)}")


def kopiera_tabeller(fil: Path, sidfil: Path) -> None:
    if (tabeller := fil.with_suffix(".tabeller")).is_dir():
        shutil.copytree(tabeller, sidfil.with_suffix(".tabeller"), dirs_exist_ok=True)
