"""Krav: K6, K11, K15, K19, K72 och K73 i docs/02-KRAV.md, ADR-0005, ADR-0009,
ADR-0099 och ADR-0100.
Test: tests/test_konvertering.py.

Kvalitetsvärdena och de mängder av dem som har en mening i schemat.
Dokumentets kvalitet följer av sidornas; den första regeln som stämmer
gäller (docs/03-ARKITEKTUR.md#konvertering-och-kvalitet).
"""

FULL = "full"
TEXT_UTAN_TABELLER = "text-utan-tabeller"
OCR = "ocr"
DELVIS = "delvis"
EJ_KONVERTERAD = "ej-konverterad"
EJ_HAMTAD = "ej-hamtad"
OK = "ok"
TABELL_OSAKER = "tabell-osaker"
BILD = "bild"
OINTRESSANT = "ointressant"
TOM = "tom"

# Dokumentets kvalitetsnivåer, från bäst till sämst.
KVALITETER = (FULL, TEXT_UTAN_TABELLER, OCR, DELVIS, EJ_KONVERTERAD, EJ_HAMTAD)
SIDKVALITETER = (OK, TABELL_OSAKER, OCR, BILD, OINTRESSANT, TOM, EJ_KONVERTERAD)
# Sidor som gav en läsning; utan någon är dokumentet `ej-konverterad`.
LASTA = {OK, TABELL_OSAKER, OCR, BILD, OINTRESSANT}
# Dokument utan text.
UTAN_TEXT = (EJ_HAMTAD, EJ_KONVERTERAD)
# Sidor vars tal ska stå i `tal_obekraftade`.
OBEKRAFTADE = {OCR, BILD, EJ_KONVERTERAD}
# Sidor lästa ur textlagret.
TEXTLAGER = {OK, TABELL_OSAKER}
# Sidor som kan ha gått till OCR; `pipeline` nämner då OCR-verktygen.
MED_OCR = {OCR, BILD, OINTRESSANT, EJ_KONVERTERAD}


def dokumentets(per_sida: list[str]) -> str:
    if not LASTA & set(per_sida):
        return EJ_KONVERTERAD
    for sida, dokument in (
        (EJ_KONVERTERAD, DELVIS),
        (OCR, OCR),
        (TABELL_OSAKER, TEXT_UTAN_TABELLER),
    ):
        if sida in per_sida:
            return dokument
    return FULL
