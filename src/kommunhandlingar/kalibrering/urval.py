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

from kommunhandlingar import frontmatter, pool
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
    dokument = list(pool.dokumenten(data))
    random.Random(fro).shuffle(dokument)
    valda, kvar = [], antal
    for fil, falt, text in dokument:
        namn = str(fil.relative_to(data))
        prov = provet(namn, falt, text, random.Random(f"{fro}:{namn}"))
        if prov is not None and kvar > 0:
            prov = Prov(prov.fil, prov.url, prov.sha256, prov.sidor[:kvar])
            valda.append(prov)
            kvar -= len(prov.sidor)
    return valda


def provet(namn: str, falt: dict, text: str, slump: random.Random) -> Prov | None:
    if falt["kalla_url"].startswith(("[", "null")):
        return None
    if falt["bytes"] == "null" or int(falt["bytes"]) > STORST:
        return None
    sidor = mojliga(falt, frontmatter.brodtext(text))
    if not sidor:
        return None
    valda = sorted(slump.sample(sidor, min(PER_DOKUMENT, len(sidor))))
    return Prov(namn, falt["kalla_url"], falt["sha256"], valda)


def mojliga(falt: dict[str, str], brodtext: str) -> list[int]:
    kvalitet = frontmatter.lista(falt["kvalitet_per_sida"])
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
