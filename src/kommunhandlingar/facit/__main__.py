"""Krav: K20 och K81 i docs/02-KRAV.md, ADR-0025.
Test: tests/test_facit.py och tests/test_facit_kommando.py.

`python -m kommunhandlingar.facit [--urval KATALOG] [--spara]` konverterar
urvalet och skriver måtten per dokument, med en not per avvikelse, och
totalt; med `--spara` också raden för poolens version i matt.csv. Urvalet
läses ur KATALOG, som förval räknad från arbetskatalogen.
"""

import argparse
from collections import Counter
from importlib.metadata import version
from pathlib import Path

from kommunhandlingar.facit.matt import spara, totalt, urvalets_utfall
from kommunhandlingar.facit.utfall import MATT

URVALET = Path("tests/fixtures/facit")


def rad(namn: str, matt: Counter) -> str:
    return f"{namn:<30}" + " ".join(f"{m}={matt[m]}" for m in MATT)


def argumenten() -> argparse.Namespace:
    tolkare = argparse.ArgumentParser(prog="python -m kommunhandlingar.facit")
    tolkare.add_argument("--urval", type=Path, default=URVALET, help="urvalets katalog")
    tolkare.add_argument("--spara", action="store_true", help="skriv raden i matt.csv")
    argument = tolkare.parse_args()
    if not argument.urval.is_dir():
        tolkare.error(f"urvalet finns inte: {argument.urval}")
    return argument


def main():
    argument = argumenten()
    utfall = urvalets_utfall(argument.urval)
    for namn, u in utfall.items():
        print(rad(namn, u.matt))
        for not_ in u.noter:
            print(f"  {not_}")
    print(rad("totalt", totalt(utfall)))
    if argument.spara:
        spara(argument.urval / "matt.csv", version("kommunhandlingar"), totalt(utfall))


if __name__ == "__main__":
    main()
