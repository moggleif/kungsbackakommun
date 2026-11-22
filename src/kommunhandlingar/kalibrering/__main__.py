"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_kalibrering.py.

`python -m kommunhandlingar.kalibrering <datakatalog> <utkatalog> [--antal N]
[--fro F]`. Väljer textlagersidor ur poolen (`urval`), hämtar varje PDF
med poolens hämtning och kontrollerar dess sha256, mäter väg H på sidorna
(`matning`) och skriver `rader.csv` och `rapport.md` i utkatalogen.
Dokumenten tas i urvalets ordning tills `--antal` sidor är mätta. Är
kravet inte uppfyllt, eller är för få sidor mätta, avslutas kommandot
med kod 1. `hamtning.toml` läses i katalogen ovanför datakatalogen, som
i ett datarepo. En PDF
vars sha256 har ändrats i källan, eller som inte går att hämta, räknas i
rapporten och mäts inte. PDF:en raderas när den är mätt (ADR-0001).
"""

import argparse
import hashlib
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import NamedTuple

import pdfplumber
import pypdfium2 as pdfium

from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.hamtning import installningar
from kommunhandlingar.hamtning.klient import Klient
from kommunhandlingar.kalibrering import matning, rapport, urval
from kommunhandlingar.konvertering import radlasning


class Pdf(NamedTuple):
    pdfium: pdfium.PdfDocument
    plumber: pdfplumber.PDF


def main(argv: list[str] | None = None) -> None:
    tolk = argparse.ArgumentParser(prog="python -m kommunhandlingar.kalibrering")
    tolk.add_argument("data", type=Path)
    tolk.add_argument("ut", type=Path)
    tolk.add_argument("--antal", type=int, default=300)
    tolk.add_argument("--fro", type=int, default=411)
    a = tolk.parse_args(argv)
    klient = Klient(installningar.las(a.data.parent / installningar.VAR))
    resultat = rapport.Resultat(a.antal)
    for prov in urval.kandidater(a.data, a.fro):
        kvar = a.antal - len(resultat.sidor)
        if kvar <= 0:
            break
        mat_dokument(klient, replace(prov, sidor=prov.sidor[:kvar]), resultat)
    a.ut.mkdir(parents=True, exist_ok=True)
    rapport.skriv(resultat, a.ut)
    if not rapport.uppfyllt(resultat):
        sys.exit(1)


def mat_dokument(klient: Klient, prov: urval.Prov, resultat: rapport.Resultat):
    with tempfile.TemporaryDirectory() as katalog:
        fil = Path(katalog) / "dokument.pdf"
        try:
            klient.fil(prov.url, fil)
        except Hamtfel as fel:
            resultat.ej_matta.append((prov, f"hämtning: {fel.orsak}"))
            return
        if hashlib.sha256(fil.read_bytes()).hexdigest() != prov.sha256:
            resultat.ej_matta.append((prov, "sha256 ändrad i källan"))
            return
        mat_sidor(fil, prov, resultat)


def mat_sidor(fil: Path, prov: urval.Prov, resultat: rapport.Resultat) -> None:
    with pdfplumber.open(fil) as plumber:
        pdf = Pdf(pdfium.PdfDocument(fil), plumber)
        try:
            for nummer in prov.sidor:
                mat_sida(pdf, prov, nummer, resultat)
        finally:
            pdf.pdfium.close()


def mat_sida(pdf: Pdf, prov: urval.Prov, nummer: int, resultat: rapport.Resultat):
    try:
        resultat.sidor.append((prov, nummer, matning.mat(*pdf, nummer)))
    except radlasning.Fallerade:
        resultat.ej_matta.append((prov, f"Tesseract fallerade på sidan {nummer}"))


if __name__ == "__main__":
    main()
