"""Krav: K5 i docs/02-KRAV.md, ADR-0009. Test: tests/test_konvertering.py.

En tabells rader som CSV och som Markdown. Modulen läser ingen PDF.
"""

import csv
import io

from kommunhandlingar.konvertering import markdown


def som_csv(rader: list[list[str]]) -> str:
    ut = io.StringIO()
    csv.writer(ut, lineterminator="\n").writerows(rader)
    return ut.getvalue()


def som_markdown(rader: list[list[str]]) -> str:
    celler = [[markdown.cell(c) for c in r] for r in rader]
    rubrik, *ovriga = celler
    linjer = [rubrik, ["---"] * len(rubrik), *ovriga]
    return "\n".join("| " + " | ".join(rad) + " |" for rad in linjer)
