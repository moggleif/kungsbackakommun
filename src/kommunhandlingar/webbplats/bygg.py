"""Krav: K14, K18, K22, K26, K28, K36, K37, K39, K46, K47, K48, K54, K56, K58, K60 och
K62 i docs/02-KRAV.md.
Test: tests/test_webbplats.py, tests/test_projekt.py,
tests/test_webbplats_dokument.py, tests/test_kalender.py, tests/test_mal.py,
tests/test_uppfoljningar.py, tests/test_lokalbehov.py, tests/test_initiativ.py,
tests/test_dokumentindex.py, tests/test_paragrafindex.py,
tests/test_sammantradessida.py, tests/test_sokindex.py.

Underlaget läses i `inlasning`; här skrivs sidorna i ordningen startsida,
per kommun och sökindex.
"""

import shutil
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from kommunhandlingar import pool
from kommunhandlingar.fel import Datafel
from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import (
    dokumentindex,
    inlasning,
    kalender,
    paragrafindex,
    sammantradesbygge,
    sidor,
    sokindex,
)
from kommunhandlingar.webbplats.bygge import Bygge
from kommunhandlingar.webbplats.dokumentsida import dokumentsida
from kommunhandlingar.webbplats.kalendersida import kalendersida
from kommunhandlingar.webbplats.llms import llms
from kommunhandlingar.webbplats.mall import Mall, sida
from kommunhandlingar.webbplats.malsida import adress as malsidans_adress
from kommunhandlingar.webbplats.malsida import malsida
from kommunhandlingar.webbplats.meny import oversiktsnamn, statusadress
from kommunhandlingar.webbplats.organsida import organsida
from kommunhandlingar.webbplats.oversikt import adresser, oversikt
from kommunhandlingar.webbplats.rakning import okanda, rakna
from kommunhandlingar.webbplats.slagen import SLAGEN
from kommunhandlingar.webbplats.spar import Slag
from kommunhandlingar.webbplats.sparkort import Vy
from kommunhandlingar.webbplats.sparsida import adress as sparets_adress
from kommunhandlingar.webbplats.sparsida import sparsida
from kommunhandlingar.webbplats.sparslag import DETALJPLANER


# Signaturen står kvar med fyra parametrar: `webbplats/__main__.py`, och
# genom den regionens datarepo, bygger webbplatsen härifrån.
def bygg(rot: Path, ut: Path, repo: str, byggd: datetime) -> Mall:
    bygge = Bygge(ut, inlasning.las(rot, repo, byggd))
    ut.mkdir(parents=True, exist_ok=True)
    if not bygge.mall.en_kommun:
        bygge.skriv("index.html", sidor.startsida(bygge.mall))
    bygge.skriv("llms.txt", llms(bygge.mall))
    sokgrupper = []
    for kommun in bygge.mall.kommuner:
        sokgrupper.append(bygg_kommun(bygge, rot / "data" / kommun.id, kommun))
        if kommun.id in bygge.mall.kalendrar:
            bygg_kalender(bygge, rot, kommun)
    sokindex.skriv(ut, sokgrupper)
    return bygge.mall


# Kommunens grupp i sökindexet lämnas tillbaka.
def bygg_kommun(bygge: Bygge, katalog: Path, kommun: Kommun) -> dict:
    dokument, stycken = skriv_dokumenten(bygge, katalog, kommun)
    dokumentindex.skriv(bygge.ut, dokument, katalog)
    paragrafindex.skriv(bygge.ut, stycken, katalog)
    underlag = sammantradesbygge.underlag(
        bygge.mall, katalog, kommun, (dokument, stycken)
    )
    sammantradesbygge.bygg(bygge.ut, bygge.mall, underlag)
    bygge.skriv(statusadress(kommun.id), sidor.statussida(bygge.mall, kommun, dokument))
    bygg_oversikten(bygge, kommun, dokument)
    bygg_organen(bygge, kommun, dokument)
    return sokindex.grupp(kommun, underlag.paragrafer)


# Varje dokuments sida skrivs när det läses, så att poolens text inte hålls
# i minnet. Dokumentens fält och paragraferna lämnas tillbaka.
def skriv_dokumenten(
    bygge: Bygge, katalog: Path, kommun: Kommun
) -> tuple[list[dict], list[dict]]:
    (bygge.ut / kommun.id).mkdir(exist_ok=True)
    dokument, stycken = [], []
    for fil, falt, text in pool.dokumenten(katalog):
        prova(fil, falt, kommun)
        falt["adress"] = fil.relative_to(katalog).with_suffix(".html").as_posix()
        html = dokumentsida(bygge.mall, kommun, falt, text)
        kopiera_tabeller(fil, bygge.skriv(f"{kommun.id}/{falt['adress']}", html))
        dokument.append(falt)
        stycken += paragrafindex.av_dokument(falt, text, katalog)
    return dokument, stycken


def bygg_oversikten(bygge: Bygge, kommun: Kommun, dokument: list[dict]) -> None:
    mall = bygge.mall
    rader = rakna(kommun, dokument, mall.byggd.date())
    innehall = oversikt(mall, kommun, rader, dokument)
    rubrik = oversiktsnamn(mall.kommuner, kommun)
    for adress in adresser(mall, kommun):
        bygge.skriv(adress, sida(mall, adress, rubrik, innehall))


def bygg_organen(bygge: Bygge, kommun: Kommun, dokument: list[dict]) -> None:
    mall = bygge.mall
    for rad in rakna(kommun, dokument, mall.byggd.date()):
        organets = [d for d in dokument if d["organ"] == rad.id]
        html = organsida(mall, kommun, rad, organets)
        bygge.skriv(f"{kommun.id}/{rad.id}.html", html)
        if malen := [m for m in mall.malen.get(kommun.id, []) if m.organ == rad.id]:
            html = malsida(mall, kommun, malen, organets)
            bygge.skriv(malsidans_adress(kommun, rad.id), html)
        bygg_sparen(bygge, kommun, rad.id)


def bygg_sparen(bygge: Bygge, kommun: Kommun, organ: str) -> None:
    for slag in SLAGEN:
        alla = bygge.mall.spar[slag.id].get(kommun.id, [])
        if stegen := [s for s in alla if s.organ == organ]:
            html = sparsida(bygge.mall, vy(bygge.mall, kommun, slag), stegen)
            bygge.skriv(sparets_adress(kommun, organ, slag), html)


def vy(mall: Mall, kommun: Kommun, slag: Slag) -> Vy:
    vyn = Vy(slag, kommun, mall.aren[kommun.id])
    if slag == DETALJPLANER:
        return replace(vyn, projekt=mall.projekt.get(kommun.id, {}))
    return vyn


def bygg_kalender(bygge: Bygge, rot: Path, kommun: Kommun) -> None:
    sammantraden = inlasning.las_kalender(rot, kommun)
    sammantraden = kalender.med_sidor(sammantraden, bygge.ut / kommun.id)
    html = kalendersida(bygge.mall, kommun, sammantraden)
    bygge.skriv(f"{kommun.id}/kalender.html", html)


def prova(fil: Path, falt: dict, kommun: Kommun) -> None:
    if fel := okanda(falt, kommun):
        raise Datafel(f"{fil}: okänt {', '.join(fel)}")


def kopiera_tabeller(fil: Path, sidfil: Path) -> None:
    if (tabeller := fil.with_suffix(".tabeller")).is_dir():
        shutil.copytree(tabeller, sidfil.with_suffix(".tabeller"), dirs_exist_ok=True)
