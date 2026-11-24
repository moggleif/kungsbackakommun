"""Krav: K36 i docs/02-KRAV.md, ADR-0057. Test: tests/test_lokalbehov.py.

Nämndens lokalbehov som ett slag av spår över tid: från nämndens
lokalbehov och prioriteringen till kommunens lokalplan, startbeslutet och
den utförda lokalen. Lokaler och investeringar som organet självt beslutar
om står i `investeringsslag.py`.
"""

from kommunhandlingar.webbplats.spar import Slag
from kommunhandlingar.webbplats.sparformer import CIRKEL, DRAG, FYLLD, KLART, RUTER

LOKALBEHOV = Slag(
    id="lokalbehov",
    kolumn="behov",
    rubrik="Lokalbehov",
    sak="Behov",
    saker="Behoven",
    antal="behov",
    faser={
        "lokalbehov": (CIRKEL, "i nämndens lokalbehov"),
        "prioritet": (FYLLD, "prioriterat"),
        "lokalplan": (
            f'<rect x="2" y="2" width="12" height="12" {DRAG}/>',
            "i lokalplanen",
        ),
        "startbeslut": (
            '<path d="M4 2.5v11l9-5.5z" fill="currentColor"/>',
            "startbeslut",
        ),
        "pagar": (
            RUTER + '<path d="M8 1.5v13l-6.5-6.5z" fill="currentColor"/>',
            "på gång",
        ),
        "utfort": (KLART, "utfört"),
    },
    inledning=(
        "<p>Nämndens lokalbehov år för år: när de står i nämndens lokalbehov, "
        "hur de prioriteras, om de kommer in i kommunens lokalplan, får "
        "startbeslut och blir utförda. Varje ikon länkar till sidan i dokumentet "
        "som visar steget.</p>"
    ),
    metod=(
        "<p>Stegen är lästa ur poolens dokument, från vilket organ som helst: "
        "nämndens egna, budgeten, besluten om att starta projekt och "
        "redovisningen från det organ som bygger. Varje steg har en text som "
        "står på källans sida, och bygget prövar det.</p>"
        "<p>Ett behov har ett namn på sidan även när källorna kallar det olika. "
        "Där källan inte själv säger att det gäller behovet är kopplingen en "
        "bedömning och ikonen har en streckad ram. Ett år utan ikon betyder att "
        "inget steg står i poolen det året, inte att inget hände. Sidan visar "
        "vad som står var och värderar inte behoven.</p>"
    ),
    adr="0057-lokalbehoven-foljs-steg-for-steg-ur-alla-organs-dokument.md",
    varden={
        "prioritet": (r".+", "en prioritet"),
        "lokalplan": (r"\d+", "ett löpnummer"),
    },
    siffra="prioritet",
    aktuell="lokalbehov",
)
