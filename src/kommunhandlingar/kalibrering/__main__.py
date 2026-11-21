"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_kalibrering.py.

`python -m kommunhandlingar.kalibrering <datakatalog> <utkatalog> [--antal N]
[--fro F]`. Väljer textlagersidor ur poolen (`urval`), hämtar varje PDF
med poolens hämtning och kontrollerar dess sha256, mäter väg H på sidorna
(`matning`) och skriver `rader.csv` och `rapport.md` i utkatalogen. Har
en bekräftad sida ett fel avslutas kommandot med kod 1. En PDF
vars sha256 har ändrats i källan, eller som inte går att hämta, räknas i
rapporten och mäts inte. PDF:en raderas när den är mätt (ADR-0001).
"""

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

import pdfplumber
import pypdfium2 as pdfium

from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.hamtning import installningar
from kommunhandlingar.hamtning.klient import Klient
from kommunhandlingar.kalibrering import matning, rapport, urval
from kommunhandlingar.konvertering import radlasning


def main(argv: list[str] | None = None) -> None:
    tolk = argparse.ArgumentParser(prog="python -m kommunhandlingar.kalibrering")
    tolk.add_argument("data", type=Path)
    tolk.add_argument("ut", type=Path)
    tolk.add_argument("--antal", type=int, default=300)
    tolk.add_argument("--fro", type=int, default=411)
    a = tolk.parse_args(argv)
    klient = Klient(installningar.las(a.data.parent / installningar.VAR))
    resultat = rapport.Resultat()
    for prov in urval.urval(a.data, a.antal, a.fro):
        mat_dokument(klient, prov, resultat)
    a.ut.mkdir(parents=True, exist_ok=True)
    rapport.skriv(resultat, a.ut)
    if rapport.falska_bekraftelser(resultat):
        sys.exit(1)


def mat_dokument(klient: Klient, prov: urval.Prov, resultat: rapport.Resultat):
    with tempfile.TemporaryDirectory() as katalog:
        fil = Path(katalog) / "dokument.pdf"
        try:
            klient.fil(prov.url, fil)
        except Hamtfel as fel:
            resultat.ej_matt(prov, f"hämtning: {fel.orsak}")
            return
        if hashlib.sha256(fil.read_bytes()).hexdigest() != prov.sha256:
            resultat.ej_matt(prov, "sha256 ändrad i källan")
            return
        mat_sidor(fil, prov, resultat)


def mat_sidor(fil: Path, prov: urval.Prov, resultat: rapport.Resultat) -> None:
    with pdfplumber.open(fil) as plumber:
        pdf = pdfium.PdfDocument(fil)
        try:
            for nummer in prov.sidor:
                mat_sida((pdf, plumber), prov, nummer, resultat)
        finally:
            pdf.close()


def mat_sida(pdf: tuple, prov: urval.Prov, nummer: int, resultat) -> None:
    try:
        resultat.lagg_till(prov, nummer, matning.mat(*pdf, nummer))
    except radlasning.Fallerade:
        resultat.ej_matt(prov, f"Tesseract fallerade på sidan {nummer}")


if __name__ == "__main__":
    main()
