"""Krav: K89 och ADR-0111. Skapar `rutnat.pdf` för tests/test_rutnat.py.

Körs för hand med reportlab, som inte är projektets beroende:
`python tests/fixtures/pdf/skapa_rutnat.py`.

1. En riskmatris med streck runt om och mellan alla kolumner i
   rubrikraden, men där kolumnen Till plan saknar högerkant under den.
   Rutnätet går inte ihop till en tabell.
2. Samma riskmatris med högerkanten hela vägen ned. Rutnätet går ihop.
"""

from pathlib import Path

from reportlab.pdfgen.canvas import Canvas

HAR = Path(__file__).parent
X = [60, 220, 330, 440, 520]
Y = [780, 760, 730, 700]
RADER = [
    ("Risk", "Sannolikhet", "Konsekvens", "Till plan"),
    ("Fel i registret", "Möjlig", "Kännbar", "Nej"),
    ("Sen handläggning", "Sannolik", "Lindrig", "Ja"),
]


def riskmatris(c: Canvas, hogerkant_ned_till: int) -> None:
    for y in Y:
        c.line(X[0], y, X[-1], y)
    for x in X[:-1]:
        c.line(x, Y[0], x, Y[-1])
    c.line(X[-1], Y[0], X[-1], hogerkant_ned_till)
    for topp, rad in zip(Y[:-1], RADER, strict=True):
        for vanster, cell in zip(X[:-1], rad, strict=True):
            c.drawString(vanster + 5, topp - 14, cell)


def main() -> None:
    c = Canvas(str(HAR / "rutnat.pdf"), pagesize=(595, 842))
    for botten in (Y[1], Y[-1]):
        riskmatris(c, botten)
        c.showPage()
    c.save()


if __name__ == "__main__":
    main()
