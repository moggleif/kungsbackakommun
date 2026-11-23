"""Krav: K6, K34 och K85 i docs/02-KRAV.md, ADR-0055 och ADR-0106. Test:
tests/test_datakontroll.py och tests/test_granskning.py.

Datakontrollen av ett dokuments värden i front matter: typen, kvaliteten,
datumen, att sökvägen följer av fälten, att ett dokument som inte gick att
hämta har null där inget hämtades, och vilka sidor som ska stå i
`tal_obekraftade`.
"""

import re
from pathlib import Path

from kommunhandlingar import frontmatter
from kommunhandlingar.frontmatter import saknas
from kommunhandlingar.kandidat import TYPORDNING
from kommunhandlingar.konvertering import kvalitet

EJ_HAMTAD_NULL = ("sha256", "bytes", "sidor", "konverterad")
EJ_HAMTAD_NULL += ("kvalitet_per_sida", "tal_obekraftade", "figurer", "tolkade")
EJ_HAMTAD_NULL += ("granskad",)
DATUM = re.compile(r"\d{4}-\d{2}-\d{2}")


def faltfel(relativ: Path, falt: dict[str, str]) -> list[str]:
    return vardefel(falt) + sokvagsfel(relativ, falt) + statusfel(falt)


def vardefel(falt: dict[str, str]) -> list[str]:
    fel = [] if falt["typ"] in TYPORDNING else [f"okänd typ {falt['typ']!r}"]
    if falt["kvalitet"] not in kvalitet.KVALITETER:
        fel.append(f"okänd kvalitet {falt['kvalitet']!r}")
    sidor = frontmatter.lista(falt["kvalitet_per_sida"])
    fel += [
        f"okänd sidkvalitet {s!r}" for s in sidor if s not in kvalitet.SIDKVALITETER
    ]
    for namn in ("datum", "granskad"):
        if not saknas(falt[namn]) and not DATUM.fullmatch(falt[namn]):
            fel.append(f"{namn} {falt[namn]!r} är inte ÅÅÅÅ-MM-DD")
    return fel


def sokvagsfel(relativ: Path, falt: dict[str, str]) -> list[str]:
    def med(grund: str, tillagg: str) -> str:
        return grund if saknas(tillagg) else f"{grund}-{tillagg}"

    vantad = Path(
        falt["kommun"],
        falt["organ"],
        falt["datum"][:4],
        med(falt["datum"], falt["lopnr"]),
        med(falt["typ"], falt["namn"]) + ".md",
    )
    return [] if relativ == vantad else [f"sökvägen borde vara {vantad}"]


def statusfel(falt: dict[str, str]) -> list[str]:
    if falt["kvalitet"] == kvalitet.EJ_HAMTAD:
        fel = [f"{n} ska vara null" for n in EJ_HAMTAD_NULL if not saknas(falt[n])]
        return fel + (["fel saknas"] if saknas(falt["fel"]) else [])
    sidor = frontmatter.lista(falt["kvalitet_per_sida"])
    if not saknas(falt["sidor"]) and falt["sidor"] != str(len(sidor)):
        return ["sidor stämmer inte med kvalitet_per_sida"]
    if frontmatter.granskad(falt):
        return []  # granskningen tar själv bort de sidor vars tal den bekräftat
    return obekraftade_fel(falt, sidor)


def obekraftade_fel(falt: dict[str, str], sidor: list[str]) -> list[str]:
    """Sidorna som borde stå i tal_obekraftade. Väg H bekräftar tal per
    sida men skriver det inte per sida, så i ett dokument som lästs med
    väg H får varje OCR-sida stå utanför listan (K85, ADR-0106)."""
    obekraftade = set(frontmatter.lista(falt["tal_obekraftade"]))
    vag_h = "rapidocr" in falt["pipeline"]
    return [
        f"sidan {nr} är {s} men står inte i tal_obekraftade"
        for nr, s in enumerate(sidor, 1)
        if s in kvalitet.OBEKRAFTADE
        and str(nr) not in obekraftade
        and not (vag_h and s == kvalitet.OCR)
    ]
