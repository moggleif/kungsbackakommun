"""Krav: K6 i docs/02-KRAV.md, ADR-0005. Test: tests/test_konvertering.py.

Tesseract läser en sidbild i 300 dpi med svensk modell och ger sin TSV och
sin text. Fallerar Tesseract eller blir den inte klar på fem minuter ger
läsningen ingenting. Saknas Tesseract eller modellen stoppas körningen
innan något dokument läses (`kontrollera`). Versionerna av pypdfium2,
Tesseract och språkmodellen skrivs i dokumentets `pipeline` (`verktyg`).
"""

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from functools import cache
from importlib.metadata import version
from pathlib import Path

from PIL import Image

from kommunhandlingar.fel import Konfigurationsfel

DPI = 300
SPRAK = "swe"
TIDSGRANS = 300


@dataclass(frozen=True)
class Utdata:
    tsv: str
    text: str


def las_bild(bild: Image.Image) -> Utdata | None:
    """Tesseracts TSV och text för bilden, eller None när Tesseract fallerar."""
    with tempfile.TemporaryDirectory() as katalog:
        fil, ut = Path(katalog) / "sida.png", Path(katalog) / "ut"
        bild.save(fil)
        if not kor(fil, ut):
            return None
        tsv, txt = (
            ut.with_suffix(s).read_text(encoding="utf-8") for s in (".tsv", ".txt")
        )
        return Utdata(tsv, txt)


def kor(bild: Path, ut: Path) -> bool:
    try:
        subprocess.run(
            ["tesseract", bild, ut, "-l", SPRAK, "--dpi", str(DPI), "txt", "tsv"],
            check=True,
            capture_output=True,
            timeout=TIDSGRANS,
            env=os.environ | {"OMP_THREAD_LIMIT": "1"},
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as fel:
        print(f"Tesseract: {fel}", file=sys.stderr)
        return False
    return True


def kontrollera() -> None:
    try:
        svar = subprocess.run(
            ["tesseract", "--list-langs"], capture_output=True, text=True
        )
    except FileNotFoundError as fel:
        raise Konfigurationsfel("Tesseract saknas (OCR, ADR-0005)") from fel
    for modell in (SPRAK, "osd"):
        if modell not in svar.stdout.split():
            raise Konfigurationsfel(f"Tesseract saknar modellen {modell!r}")


@cache
def verktyg() -> list[str]:
    """pypdfium2, Tesseract och språkmodellen, med version, för `pipeline`."""
    svar = subprocess.run(
        ["tesseract", "--version"], check=True, capture_output=True, text=True
    )
    programmet = svar.stdout.split()[1]
    return [
        f"pypdfium2 {version('pypdfium2')}",
        f"tesseract {programmet} {SPRAK} {modellversion()}",
    ]


def modellversion() -> str:
    """Paketversionen av språkmodellen, utan epok och revision (1:4.1.0-2 → 4.1.0)."""
    try:
        svar = subprocess.run(
            ["dpkg-query", "-W", "-f=${Version}", f"tesseract-ocr-{SPRAK}"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:  # inte Debian eller Ubuntu
        return "okänd"
    if svar.returncode != 0:
        return "okänd"
    return svar.stdout.split(":")[-1].split("-")[0]
