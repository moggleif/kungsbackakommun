"""Gemensamt för tests/test_kalibrering.py och test_kalibrering_kommando.py."""

import hashlib
import shutil
from pathlib import Path

from kommunhandlingar.kalibrering.matning import Utfall

VAG_H = Path(__file__).parent / "fixtures" / "pdf" / "vag-h.pdf"
SHA = hashlib.sha256(VAG_H.read_bytes()).hexdigest()
TALSIDA = " ".join(str(n) for n in range(15))


def dokument(kvalitet: str, obekraftade: str, sidor: list[str], **falt) -> str:
    huvud = {
        "kalla_url": "https://exempel.se/a.pdf",
        "sha256": SHA,
        "bytes": "1000",
        "kvalitet_per_sida": kvalitet,
        "tal_obekraftade": obekraftade,
    } | falt
    text = "".join(f"<!-- sida {n} -->\n\n{t}\n\n" for n, t in enumerate(sidor, 1))
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in huvud.items()) + "---\n\n" + text


def utfall(varde: str, hur: str = "eniga") -> Utfall:
    return Utfall(hur, varde, "1", "2", "r 1", "t 1")


def kopiera(_, url, mal):
    shutil.copy(VAG_H, mal)
