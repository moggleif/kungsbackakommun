"""Test: tests/test_inbaddning.py.

Sidornas stilar och skript står i egna filer bredvid koden och bäddas in i
varje sida, så att sidan inte hämtar något annat än Giffås gemensamma meny.
En fil läses en gång per körning, hur många sidor som än byggs.
"""

from functools import cache
from pathlib import Path

KATALOG = Path(__file__).parent


@cache
def las(namn: str) -> str:
    return (KATALOG / namn).read_text(encoding="utf-8")


def stil(*filer: str) -> str:
    return "<style>" + "".join(las(f) for f in filer) + "</style>"


def skript(*filer: str) -> str:
    return "".join(f"<script>{las(f)}</script>" for f in filer)
