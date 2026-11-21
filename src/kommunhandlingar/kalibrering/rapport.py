"""Krav: K84 i docs/02-KRAV.md och ADR-0105. Test: tests/test_kalibrering.py.

Kalibreringens resultat. `rader.csv` har en rad för varje rad med tal som
mätts, med utfall och läsningar. `rapport.md` sammanfattar: hur många
rader som blev rätt, fel, utan facit, missade och obekräftade, hur många
sidor som blev bekräftade, och hur många av dem som har ett fel. Kravet
i K84 är uppfyllt när ingen bekräftad sida har en rad som är `fel`,
`missad` eller `utanfor`. Varje sådan rad listas.
"""

import csv
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from kommunhandlingar.kalibrering.matning import Sidutfall, Utfall
from kommunhandlingar.kalibrering.urval import Prov

FALSKA = {"fel", "missad", "utanfor"}
KOLUMNER = ["fil", "sida", "sidan_bekraftad", *Utfall.__dataclass_fields__]


@dataclass
class Resultat:
    sidor: list[tuple[Prov, int, Sidutfall]] = field(default_factory=list)
    ej_matta: list[tuple[Prov, str]] = field(default_factory=list)

    def lagg_till(self, prov: Prov, nummer: int, utfall: Sidutfall) -> None:
        self.sidor.append((prov, nummer, utfall))

    def ej_matt(self, prov: Prov, orsak: str) -> None:
        self.ej_matta.append((prov, orsak))


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
    bekraftade = [(p, n, s) for p, n, s in resultat.sidor if s.bekraftad]
    falska = [
        (p, n, r) for p, n, s in bekraftade for r in s.rader if r.utfall in FALSKA
    ]
    delar = [
        "# Kalibrering av väg H (K84)\n",
        f"Mätta sidor: {len(resultat.sidor)}. Ej mätta: {len(resultat.ej_matta)}.\n",
        tabell("Rader", rader),
        tabell("Obekräftade rader per orsak", orsaker),
        f"Bekräftade sidor: {len(bekraftade)} av {len(resultat.sidor)}.\n",
        f"Falska bekräftelser på bekräftade sidor: {len(falska)}.\n",
        f"**Kravet {'är' if not falska else 'är inte'} uppfyllt.**\n",
        *(
            f"- `{p.fil}` sida {n}: {r.utfall}, läst `{r.tal}`, textlagret "
            f"`{r.facit}` (RapidOCR `{r.rapid}`, Tesseract `{r.tesseract}`)"
            for p, n, r in falska
        ),
        *(f"- Ej mätt: `{p.fil}`, {orsak}" for p, orsak in resultat.ej_matta),
    ]
    return "\n".join(delar) + "\n"


def falska_bekraftelser(resultat: Resultat) -> list[tuple[Prov, int, Utfall]]:
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
