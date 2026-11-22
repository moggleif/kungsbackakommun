"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_kalibrering.py.

Kalibreringens resultat. `rader.csv` har en rad för varje rad med tal som
mätts, med utfall och läsningar. `rapport.md` räknar raderna per utfall
och de obekräftade per orsak, och sidorna: mätta, bekräftade, bekräftade
med rader utan facit och bekräftade med en falsk bekräftelse. En falsk
bekräftelse är en rad som är `fel`, `upphojt`, `missad` eller `utanfor`
på en bekräftad sida, och varje sådan rad listas. Kravet i K84 är
uppfyllt när det inte finns någon och minst det begärda antalet sidor är
mätt; annars är det inte prövat.
"""

import csv
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from kommunhandlingar.kalibrering.matning import Sidutfall, Utfall
from kommunhandlingar.kalibrering.urval import Prov

FALSKA = {"fel", "upphojt", "missad", "utanfor"}
KOLUMNER = ["fil", "sida", "sidan_bekraftad", *Utfall.__dataclass_fields__]


@dataclass
class Resultat:
    antal: int
    sidor: list[tuple[Prov, int, Sidutfall]] = field(default_factory=list)
    ej_matta: list[tuple[Prov, str]] = field(default_factory=list)


def uppfyllt(resultat: Resultat) -> bool:
    return len(resultat.sidor) >= resultat.antal and not falska(resultat)


def skriv(resultat: Resultat, ut: Path) -> None:
    with (ut / "rader.csv").open("w", encoding="utf-8", newline="") as fil:
        skrivare = csv.DictWriter(fil, KOLUMNER)
        skrivare.writeheader()
        for prov, nummer, sida in resultat.sidor:
            for rad in sida.rader:
                skrivare.writerow(
                    {"fil": prov.fil, "sida": nummer}
                    | {"sidan_bekraftad": sida.bekraftad}
                    | asdict(rad)
                )
    (ut / "rapport.md").write_text(sammanfattning(resultat), encoding="utf-8")


def sammanfattning(resultat: Resultat) -> str:
    rader = Counter(r.utfall for _, _, s in resultat.sidor for r in s.rader)
    orsaker = Counter(
        r.hur for _, _, s in resultat.sidor for r in s.rader if r.utfall == "obekraftad"
    )
    delar = [
        "# Kalibrering av väg H (K84)\n",
        f"Mätta sidor: {len(resultat.sidor)} av {resultat.antal}. "
        f"Ej mätta: {len(resultat.ej_matta)}.\n",
        tabell("Rader", rader),
        tabell("Obekräftade rader per orsak", orsaker),
        tabell("Sidor", sidor(resultat)),
        f"**{utlatande(resultat)}**\n",
        *(
            f"- `{p.fil}` sida {n}: {r.utfall}, läst `{r.tal}`, textlagret "
            f"`{r.facit}` (RapidOCR `{r.rapid}`, Tesseract `{r.tesseract}`)"
            for p, n, r in falska(resultat)
        ),
        *(f"- Ej mätt: `{p.fil}`, {orsak}" for p, orsak in resultat.ej_matta),
    ]
    return "\n".join(delar) + "\n"


def sidor(resultat: Resultat) -> Counter:
    bekraftade = [s for _, _, s in resultat.sidor if s.bekraftad]
    return Counter(
        {
            "bekräftade": len(bekraftade),
            "bekräftade med rader utan facit": sum(
                any(r.utfall == "utan-facit" for r in s.rader) for s in bekraftade
            ),
            "bekräftade med en falsk bekräftelse": len(
                {(p.fil, n) for p, n, _ in falska(resultat)}
            ),
        }
    )


def utlatande(resultat: Resultat) -> str:
    if falska(resultat):
        return f"Kravet är inte uppfyllt: {len(falska(resultat))} falska bekräftelser."
    if len(resultat.sidor) < resultat.antal:
        return "Kravet är inte prövat: för få sidor är mätta."
    return "Kravet är uppfyllt."


def falska(resultat: Resultat) -> list[tuple[Prov, int, Utfall]]:
    return [
        (p, n, r)
        for p, n, s in resultat.sidor
        if s.bekraftad
        for r in s.rader
        if r.utfall in FALSKA
    ]


def tabell(rubrik: str, antal: Counter) -> str:
    rader = "".join(f"| {namn} | {n} |\n" for namn, n in sorted(antal.items()))
    return f"| {rubrik} | Antal |\n| --- | ---: |\n{rader}"
