"""Krav: K84, ADR-0105. Skapar `vag-h.pdf` för tests/test_radlasning.py och
tests/test_kalibrering.py.

Körs för hand, bara med standardbiblioteket:
`python tests/fixtures/pdf/skapa_vag_h.py`.

Sidan har fyra rader löptext i 12 punkter, tre av dem med tal, och en
rad med en fotnotssiffra i 7 punkter som står 4 punkter ovanför raden.
"""

from pathlib import Path

HAR = Path(__file__).parent
RADER = [
    "Budgeten for 2027 omfattar 4 078 tkr i intakter.",
    "Kostnaderna okar med 12,5 procent till 1 845 tkr.",
    "Ett stycke lopande text utan tal pa raden.",
    "Beslutet fattades den 11 augusti 2026 i paragraf 42.",
]
FOTNOT = "Kostnaden for lokalerna var 15 mnkr"


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


def text(x: float, y: float, s: str, storlek: int = 12) -> str:
    return f"BT /F1 {storlek} Tf 1 0 0 1 {x} {y} Tm ({s}) Tj ET"


ritning = [text(60, 760 - 24 * i, rad) for i, rad in enumerate(RADER)]
ritning += [text(60, 640, FOTNOT), text(256, 644, "4", 7)]
pdf("vag-h.pdf", ritning)
