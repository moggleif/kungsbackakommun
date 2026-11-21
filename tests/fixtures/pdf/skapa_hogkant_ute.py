"""Krav: K6, K41, ADR-0103. Skapar PDF:erna för tests/test_ordning.py.

Körs för hand, bara med standardbiblioteket:
`python tests/fixtures/pdf/skapa_hogkant_ute.py`.

- `medurs.pdf`: sex rader löptext och en stämpel med tal på högkant,
  vriden medurs, i högra marginalen.
- `tabell-hogkant.pdf`: en tabell utan linjer med fyra rader och `Not`
  på högkant, vriden medurs, intill första radens sista tal.
- `talrad-hogkant.pdf`: tre talrader med löptext till höger, som inte
  blir en tabell, och `Not` på högkant tre punkter till höger om första
  radens sista tal.
- `axeltitel.pdf`: sex rader löptext med tal och en axeltitel utan
  siffror på högkant, vriden moturs, i vänstra marginalen.
"""

from pathlib import Path

HAR = Path(__file__).parent
SIFFERBREDD = {**dict.fromkeys("0123456789", 556), ",": 278, "-": 333}
STAMPEL = "Belopp 11,5 mnkr, 1.200 kr, dnr 2024/0123"
TABELL = [
    ("Inkomster", "10,0", "11,5"),
    ("Utgifter", "-2,0", "-14,8"),
    ("Netto", "8,0", "-3,3"),
    ("Prognos", "1,0", "2,0"),
]


def pdf(namn: str, ritning: list[str]) -> None:
    strom = "\n".join(ritning).encode("latin-1")
    objekt = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R"
        b" /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(strom) + strom + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica"
        b" /Encoding /WinAnsiEncoding >>",
    ]
    ut, lagen = b"%PDF-1.4\n", []
    for nr, o in enumerate(objekt, 1):
        lagen.append(len(ut))
        ut += b"%d 0 obj\n" % nr + o + b"\nendobj\n"
    xref = len(ut)
    ut += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objekt) + 1)
    ut += b"".join(b"%010d 00000 n \n" % lage for lage in lagen)
    ut += b"trailer\n<< /Size %d /Root 1 0 R >>\n" % (len(objekt) + 1)
    ut += b"startxref\n%d\n%%%%EOF\n" % xref
    (HAR / namn).write_bytes(ut)


def text(x: float, y: float, s: str, matris: str = "1 0 0 1") -> str:
    return f"BT /F1 10 Tf {matris} {x} {y} Tm ({s}) Tj ET"


def medurs(x: float, y: float, s: str) -> str:
    return text(x, y, s, "0 -1 1 0")


def hogerstallt(hoger: float, y: float, s: str) -> str:
    return text(hoger - sum(SIFFERBREDD[c] for c in s) / 100, y, s)


def tabell() -> list[str]:
    ritning = [text(60, 760, "Resultatet for perioden framgar av tabellen nedan.")]
    for i, (post, fore, efter) in enumerate(TABELL):
        y = 700 - 20 * i
        ritning += [text(180, y, post), hogerstallt(300, y, fore)]
        ritning.append(hogerstallt(350, y, efter))
    return ritning


rader = [
    text(60, 700 - 14 * i, f"Ett stycke lopande text utan tal rad {i}.")
    for i in range(6)
]
pdf("medurs.pdf", [*rader, medurs(560, 780, STAMPEL)])
pdf("tabell-hogkant.pdf", [*tabell(), medurs(357, 709.5, "Not")])


def talrader() -> list[str]:
    ritning = [text(60, 760, "Resultatet for perioden framgar nedan.")]
    for i, (post, fore, efter) in enumerate(TABELL[:3]):
        y = 700 - 14 * i
        ritning += [text(60, y, post), hogerstallt(300, y, fore.lstrip("-"))]
        ritning += [
            hogerstallt(326, y, efter.lstrip("-")),
            text(400, y, "loptext ord ord"),
        ]
    return ritning


pdf("talrad-hogkant.pdf", [*talrader(), medurs(329, 709.5, "Not")])
TAL = "Kommunen hade 84 512 invanare den 31 december 2023, rad {}."
tal = [text(60, 700 - 14 * i, TAL.format(i)) for i in range(6)]
pdf("axeltitel.pdf", [*tal, text(40, 560, "Antal invanare", "0 1 -1 0")])
