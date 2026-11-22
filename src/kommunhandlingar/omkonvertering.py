"""Krav: K8 och K86 i docs/02-KRAV.md, ADR-0107. Test i tests/:
test_omkonvertering.py och test_omkonvertering_tabell.py.

Vilka dokument en ny version av poolen kan ändra. Tabellen i
`omkonvertering.toml` säger det för varje version, och ett dokument berörs
när en version efter dess egen, fram till poolens, gör det. Det avgörs ur
dokumentets front matter, utan att hämta något.
"""

import tomllib
from pathlib import Path

from kommunhandlingar import frontmatter
from kommunhandlingar.konvertering import kvalitet

TABELL = Path(__file__).with_name("omkonvertering.toml")
ALLA = "alla"
TAL_OBEKRAFTADE = "tal_obekraftade"

Version = tuple[int, ...]
Andringar = dict[Version, frozenset[str]]


def las() -> Andringar:
    with TABELL.open("rb") as tabell:
        versioner = tomllib.load(tabell)["versioner"]
    return {version_av(v): frozenset(omfang) for v, omfang in versioner.items()}


def version_av(text: str) -> Version:
    return tuple(int(del_) for del_ in text.split("."))


def poolens_version_i(pipeline: str) -> Version:
    """`kommunhandlingar 0.12.0 / pdfplumber …` och `kommunhandlingar
    0.12.0` ger båda (0, 12, 0)."""
    return version_av(pipeline.split(" / ")[0].split(" ")[1])


def berors(andringar: Andringar, falt: dict[str, str], poolens: str) -> bool:
    """Ett dokument från en nyare version än poolens lämnas orört."""
    egen = poolens_version_i(falt["pipeline"])
    tak = poolens_version_i(poolens)
    nyare = (v for v in andringar if egen < v <= tak)
    return any(traffar(andringar[v], falt) for v in nyare)


def traffar(omfang: frozenset[str], falt: dict[str, str]) -> bool:
    """En sida som inte är läst, eller ett dokument utan sidor, prövas av
    varje ny version, eftersom felet kan ha varit tillfälligt."""
    sidor = set(frontmatter.lista(falt["kvalitet_per_sida"]))
    if ALLA in omfang or not sidor or kvalitet.EJ_KONVERTERAD in sidor:
        return True
    obekraftade = bool(frontmatter.lista(falt["tal_obekraftade"]))
    return bool(omfang & sidor) or (TAL_OBEKRAFTADE in omfang and obekraftade)
