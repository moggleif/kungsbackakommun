"""Krav: K15, K34 och K81 i docs/02-KRAV.md, ADR-0017 och ADR-0055.
Test: tests/test_figurer.py och tests/test_tolkning_kommando.py.

Verktygen för den som tolkar figurerna (docs/03-ARKITEKTUR.md#tolkade-figurer):

- `python -m kommunhandlingar.tolkning lista <data>` skriver arbetslistan,
  varje dokument med sidor i `figurer` som inte står i `tolkade`.
- `python -m kommunhandlingar.tolkning rendera <md> <katalog>` hämtar
  dokumentets original, i delar som i steg 2 (ADR-0049), prövar att sha256
  stämmer med front matter och sparar de otolkade figursidorna som PNG i
  katalogen. PDF:en raderas.
  Ett dokument utan otolkade sidor hämtas inte. Med `--sidor 3,5` sparas
  de sidorna i stället, för granskningen (K34).
"""

import argparse
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium

from kommunhandlingar import frontmatter, original, pool
from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.hamtning import installningar
from kommunhandlingar.hamtning.hamtare import Hamtare
from kommunhandlingar.hamtning.klient import Klient

SKALA = 2


class AndratOriginal(Exception):
    """Originalet har inte samma sha256 som när det konverterades."""


def otolkade(falt: dict[str, str]) -> list[int]:
    tolkade = set(frontmatter.lista(falt["tolkade"]))
    return [int(s) for s in frontmatter.lista(falt["figurer"]) if s not in tolkade]


def arbetslista(data: Path) -> list[str]:
    rader = []
    for md, falt, _ in pool.dokumenten(data):
        if sidor := otolkade(falt):
            rader.append(f"{md.relative_to(data).as_posix()}: {sidor}")
    return rader


@dataclass(frozen=True)
class Bestallning:
    """Dokumentet, katalogen för bilderna och sidorna; None är de otolkade."""

    md: Path
    katalog: Path
    sidor: list[int] | None = None


def rendera(bestallning: Bestallning, klient: Hamtare) -> list[Path]:
    falt = frontmatter.las(bestallning.md.read_text(encoding="utf-8"))
    sidor = bestallning.sidor or otolkade(falt)
    if not sidor:
        return []
    bestallning.katalog.mkdir(parents=True, exist_ok=True)
    with (
        original_pdf(bestallning.md, falt, klient) as pdf,
        pdfium.PdfDocument(pdf) as dokument,
    ):
        return [spara(dokument, nr, bestallning.katalog) for nr in sidor]


@contextmanager
def original_pdf(md: Path, falt: dict[str, str], klient: Hamtare) -> Iterator[Path]:
    """Originalet i en tillfällig katalog, som raderas efteråt."""
    with tempfile.TemporaryDirectory() as tillfallig:
        pdf = Path(tillfallig) / "original.pdf"
        adresser = frontmatter.adresser(falt["kalla_url"])
        hamtat = original.hamta(original.Hamtsatt(klient, arkiv=False), adresser, pdf)
        if frontmatter.varde_av(hamtat.sha256) != falt["sha256"]:
            raise AndratOriginal(f"{md}: originalet har ändrats sedan konverteringen")
        yield pdf


def spara(dokument: pdfium.PdfDocument, nr: int, katalog: Path) -> Path:
    png = katalog / f"{nr}.png"
    dokument[nr - 1].render(scale=SKALA).to_pil().save(png)
    return png


def klient_for(md: Path) -> Klient:
    data = next(p for p in md.resolve().parents if p.name == "data")
    return Klient(installningar.las(data.parent / installningar.VAR))


def argument() -> argparse.Namespace:
    tolk = argparse.ArgumentParser(prog="python -m kommunhandlingar.tolkning")
    kommandon = tolk.add_subparsers(dest="kommando", required=True)
    kommandon.add_parser("lista").add_argument("data", type=Path)
    rendering = kommandon.add_parser("rendera")
    rendering.add_argument("md", type=Path)
    rendering.add_argument("katalog", type=Path)
    rendering.add_argument("--sidor", type=sidlista)
    return tolk.parse_args()


def sidlista(text: str) -> list[int]:
    sidor = [int(nr) for nr in text.split(",")]
    if min(sidor) < 1:
        raise argparse.ArgumentTypeError("sidorna räknas från 1")
    return sidor


def main(arg: argparse.Namespace) -> None:
    if arg.kommando == "lista":
        for rad in arbetslista(arg.data):
            print(rad)
        return
    try:
        bestallning = Bestallning(arg.md, arg.katalog, arg.sidor)
        for png in rendera(bestallning, klient_for(arg.md)):
            print(png)
    except (AndratOriginal, Hamtfel) as fel:
        sys.exit(f"Stoppad: {fel}")


if __name__ == "__main__":
    main(argument())
