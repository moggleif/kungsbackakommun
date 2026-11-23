"""Krav: målsidans, spårsidornas, kalenderns och luckornas, som står i deras
moduler. Test: tests/test_ram.py.

Det som sidorna över tid delar: länken till ett beslut, den hopfällda
delen om sidan och knapparna för urvalet, som skripten visar.
"""

from html import escape

from kommunhandlingar.webbplats.mall import KALLKOD

BESLUTEN = KALLKOD + "/blob/main/docs/decisions/"


def beslutslank(fil: str) -> str:
    return f'<a href="{escape(BESLUTEN + fil)}">ADR-{fil[:4]}</a>'


def hur_och_varfor(*filer: str) -> str:
    lankar = [beslutslank(fil) for fil in filer]
    if len(lankar) > 1:
        lankar[-2:] = [f"{lankar[-2]} och {lankar[-1]}"]
    return f"<p>Hur och varför står i {', '.join(lankar)}.</p>"


def om_sidan(metod: str, *filer: str) -> str:
    return (
        f"<details><summary>Om sidan</summary>{metod}{hur_och_varfor(*filer)}</details>"
    )


# Knapparna visas av skriptet; utan det står allt och urvalet behövs inte.
def urval(val: list[tuple[str, str]], egenskaper: str = "") -> str:
    knappar = "".join(
        f'<button type="button" data-urval="{escape(v)}">{escape(text)}</button>'
        for v, text in val
    )
    return (
        f'<div class="urval" role="group" aria-label="Visa"{egenskaper} '
        f"hidden>{knappar}</div>"
    )
