"""Krav: K20 i docs/02-KRAV.md, ADR-0025. Test: tests/test_facit.py.

En facittabells utfall ur matchningens träffar: rätt, ofullständig och
varför, märkt osäker eller saknad (docs/03-ARKITEKTUR.md#facit-för-konverteringen).
"""

from collections import defaultdict

from kommunhandlingar.facit.lasa import Tabell
from kommunhandlingar.facit.rader import kolumnernas_siffror, talrad
from kommunhandlingar.facit.utfall import Utfall


def status(f: Tabell, utfall: Utfall, markerade: set[int]) -> tuple[str, str]:
    """Tabellens utfall och, när den är ofullständig, varför."""
    per_csv = defaultdict(set)
    for namn, i, csv_namn in utfall.traffar:
        per_csv[csv_namn].add((namn, i))
    if not egna(f, per_csv):
        spannet = set(range(f.sida, f.sista_sida + 1))
        return ("osakra" if spannet & markerade else "saknade"), ""
    fel = orsak(f, per_csv, utfall.rubriker.get(f.namn))
    return ("ofullstandiga", f" ({fel})") if fel else ("ratt", "")


def egna(f: Tabell, per_csv: dict) -> dict[str, set[int]]:
    """Raderna ur tabellen som hittades, per CSV där någon av dem stod."""
    rader = {c: {i for n, i in r if n == f.namn} for c, r in per_csv.items()}
    return {c: r for c, r in rader.items() if r}


def orsak(f: Tabell, per_csv: dict, rubrik: list | None) -> str:
    funna = egna(f, per_csv)
    data = {i for i, r in enumerate(f.rader) if i >= f.rubrikrader and talrad(r)}
    hela = [c for c, rader in funna.items() if data <= rader]
    if not hela:
        saknas = len(data - set().union(*funna.values()))
        return f"{saknas} rader saknas" if saknas else f"delad på {len(funna)} CSV:er"
    if all(len(per_csv[c]) > len(funna[c]) for c in hela):
        return "ihop med en annan tabell"
    return "" if rubrik_stammer(f, rubrik) else "rubriken stämmer inte"


def rubrik_stammer(f: Tabell, rubrik: list[list[str]] | None) -> bool:
    facits = kolumnernas_siffror(f.rader[: f.rubrikrader])
    if not any(facits):
        return True
    return rubrik is not None and kolumnernas_siffror(rubrik) == facits
