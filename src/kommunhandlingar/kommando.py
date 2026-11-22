"""Krav: K81 i docs/02-KRAV.md. Test: tests/test_poolkommandon.py.

Poolens kommandon som tar en enda katalog, `python -m
kommunhandlingar.<modul> <data>`, läser den här (#365).
"""

import sys
from pathlib import Path


def datakatalog(modul: str) -> Path:
    if len(sys.argv) != 2:
        sys.exit(f"Användning: python -m kommunhandlingar.{modul} <data>")
    return Path(sys.argv[1])
