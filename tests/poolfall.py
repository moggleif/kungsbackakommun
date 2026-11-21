"""Gemensam uppställning för testerna av webbplatsens tabeller: en CSV-fil
och en pool med dokument i en temporär katalog, och mallen för exempelbyn."""

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from kommunhandlingar.webbplats.mall import Mall
from tests.test_webbplats import REPO, TID, dokument, exempelby


@contextmanager
def tillfallig_pool(
    rubrik: str, rader: str, texter: dict[str, str]
) -> Iterator[tuple[Path, Path]]:
    """Ger exempelby.csv och data/ bredvid; texternas nycklar är sökvägar i data/."""
    with tempfile.TemporaryDirectory() as tmp:
        fil, data = Path(tmp) / "exempelby.csv", Path(tmp) / "data"
        fil.write_text(rubrik + rader, encoding="utf-8")
        skriv(data, texter)
        yield fil, data


def skriv(data: Path, texter: dict[str, str]) -> None:
    for sokvag, text in texter.items():
        (data / sokvag).parent.mkdir(parents=True, exist_ok=True)
        (data / sokvag).write_text(text, encoding="utf-8")


def dokumenten(texter: dict[str, str], per_sida: str) -> dict[str, str]:
    """Varje text som ett dokument med organ och datum ur sin sökväg."""
    return {
        sokvag: dokument(
            sokvag.split("/")[0], sokvag.split("/")[2], text=text, per_sida=per_sida
        )
        for sokvag, text in texter.items()
    }


def mall(**val) -> Mall:
    return Mall([exempelby()], REPO, TID, **val)
