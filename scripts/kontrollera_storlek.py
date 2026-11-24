"""Krav: "Ren kod – strikt" i AGENTS.md, K87 och ADR-0108.
Test: tests/test_kontrollera_storlek.py.

Koden i `src/` och `scripts/` håller målen för rader per funktion och
fil, och testerna de högre gränserna."""

import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Granser(NamedTuple):
    fil: int
    funktion: int


KOD = Granser(fil=150, funktion=15)
TESTER = Granser(fil=250, funktion=30)
KATALOGER = {"src": KOD, "scripts": KOD, "tests": TESTER}
UNDANTAG = re.compile(r"#\s*undantag:\s*\S")
ROT = Path(__file__).resolve().parent.parent


def brott_i_fil(fil: Path, granser: Granser) -> list[str]:
    text = fil.read_text(encoding="utf-8")
    rader = text.split("\n")
    antal = text.count("\n")
    fynd = [f"{fil}: över {granser.fil} rader"] if antal > granser.fil else []
    for nod in ast.walk(ast.parse(text)):
        if not isinstance(nod, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        langd = nod.end_lineno - nod.lineno + 1
        if langd > granser.funktion and not UNDANTAG.search(rader[nod.lineno - 1]):
            fynd.append(f"{fil}:{nod.lineno}: {nod.name} har {langd} rader")
    return fynd


def pythonfiler() -> list[tuple[Path, Granser]]:
    return [
        (fil, granser)
        for katalog, granser in KATALOGER.items()
        for fil in (ROT / katalog).rglob("*.py")
    ]


def main() -> int:
    fynd = [
        brott for fil, granser in pythonfiler() for brott in brott_i_fil(fil, granser)
    ]
    print("\n".join(fynd) or "Inga brott mot storleksgränserna.")
    return 1 if fynd else 0


if __name__ == "__main__":
    sys.exit(main())
