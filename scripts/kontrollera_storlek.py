"""Krav: "Ren kod – strikt" i AGENTS.md, K76.
Test: tests/test_kontrollera_storlek.py."""

import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Granser(NamedTuple):
    fil: int
    funktion: int


MAX_RADER_FUNKTION = 30
MAX_RADER_FIL = 250
HARDA = Granser(fil=MAX_RADER_FIL, funktion=MAX_RADER_FUNKTION)
MAL = Granser(fil=150, funktion=15)
UNDANTAG = re.compile(r"#\s*undantag:\s*\S")
ROT = Path(__file__).resolve().parent.parent
KATALOGER = ("src", "scripts", "tests")


def brott_i_fil(fil: Path, granser: Granser = HARDA) -> list[tuple[int, str]]:
    text = fil.read_text(encoding="utf-8")
    rader = text.split("\n")
    antal = text.count("\n")
    fynd = [(antal, f"{fil}: över {granser.fil} rader")] if antal > granser.fil else []
    for nod in ast.walk(ast.parse(text)):
        if not isinstance(nod, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        langd = nod.end_lineno - nod.lineno + 1
        if langd > granser.funktion and not UNDANTAG.search(rader[nod.lineno - 1]):
            fynd.append((langd, f"{fil}:{nod.lineno}: {nod.name} har {langd} rader"))
    return fynd


def pythonfiler() -> list[Path]:
    return [fil for katalog in KATALOGER for fil in (ROT / katalog).rglob("*.py")]


def main(argv: list[str]) -> int:
    granser = MAL if "--mal" in argv else HARDA
    fynd = [brott for fil in pythonfiler() for brott in brott_i_fil(fil, granser)]
    if granser is MAL:
        print("\n".join(text for _, text in sorted(fynd, key=lambda f: (-f[0], f[1]))))
        return 0
    print("\n".join(text for _, text in fynd) or "Inga brott mot storleksgränserna.")
    return 1 if fynd else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
