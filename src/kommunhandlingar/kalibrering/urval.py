"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_kalibrering.py.

Urvalet av textlagersidor att kalibrera väg H på. En sida kan väljas när
den har textlager (`ok`), inte har obekräftade tal och har minst 15 tal i
poolens text. Dokumentet ska vara en enda PDF på högst 20 MB. Dokumenten
blandas med ett fast frö, så att samma urval går att ta om, och högst tre
sidor tas ur varje dokument, slumpade bland de som kan väljas.
"""

import random
import re
from dataclasses import dataclass
from pathlib import Path

from kommunhandlingar import frontmatter
from kommunhandlingar.konvertering import vag_h

MINST_TAL = 15
STORST = 20_000_000
PER_DOKUMENT = 3
SIDMARKERING = re.compile(r"^<!-- sida (\d+) -->$", re.MULTILINE)


@dataclass(frozen=True)
class Prov:
    fil: str
    url: str
    sha256: str
    sidor: list[int]


def urval(data: Path, antal: int, fro: int) -> list[Prov]:
    filer = sorted(data.rglob("*.md"))
    random.Random(fro).shuffle(filer)
    valda, kvar = [], antal
    for fil in filer:
        prov = provet(fil, data, random.Random(f"{fro}:{fil.relative_to(data)}"))
        if prov is not None and kvar > 0:
            prov = Prov(prov.fil, prov.url, prov.sha256, prov.sidor[:kvar])
            valda.append(prov)
            kvar -= len(prov.sidor)
    return valda


def provet(fil: Path, data: Path, slump: random.Random) -> Prov | None:
    text = fil.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    falt = frontmatter.las(text)
    if falt.get("kalla_url", "null").startswith(("[", "null")):
        return None
    if falt.get("bytes", "null") == "null" or int(falt["bytes"]) > STORST:
        return None
    sidor = mojliga(falt, frontmatter.brodtext(text))
    if not sidor:
        return None
    valda = sorted(slump.sample(sidor, min(PER_DOKUMENT, len(sidor))))
    return Prov(str(fil.relative_to(data)), falt["kalla_url"], falt["sha256"], valda)


def mojliga(falt: dict[str, str], brodtext: str) -> list[int]:
    kvalitet = frontmatter.lista(falt.get("kvalitet_per_sida", "null"))
    obekraftade = {int(s) for s in frontmatter.lista(falt["tal_obekraftade"])}
    delar = SIDMARKERING.split(brodtext)[1:]
    texter = {int(n): t for n, t in zip(delar[::2], delar[1::2], strict=True)}
    return [
        n
        for n, k in enumerate(kvalitet, 1)
        if k == "ok"
        and n not in obekraftade
        and len(vag_h.tal(texter.get(n, ""))) >= MINST_TAL
    ]
