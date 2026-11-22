"""Krav: K20 i docs/02-KRAV.md, ADR-0025. Test: tests/test_facit.py.

Måtten i docs/03-ARKITEKTUR.md#facit-för-konverteringen och utfallet för ett
dokument, som matchningen och bedömningen fyller i.
"""

from collections import Counter
from dataclasses import dataclass, field

MATT = (
    "ratt",
    "ofullstandiga",
    "osakra",
    "saknade",
    "fel_rader",
    "pahittade",
    "tal_avviker",
    "omarkta",
)


@dataclass
class Utfall:
    matt: Counter = field(default_factory=Counter)
    noter: list[str] = field(default_factory=list)
    # Facittabellens namn, raden i den och namnet på CSV:en där raden stod.
    traffar: set[tuple[str, int, str]] = field(default_factory=set)
    rubriker: dict[str, list[list[str]]] = field(default_factory=dict)

    def rakna(self, matt: str, noter: list[str]):
        self.matt[matt] += len(noter)
        if matt != "ratt":
            self.noter += [f"{matt}: {n}" for n in noter]
