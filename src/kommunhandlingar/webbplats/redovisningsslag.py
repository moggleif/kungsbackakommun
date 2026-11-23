"""Krav: K42 i docs/02-KRAV.md, ADR-0065. Test: tests/test_redovisningar.py.

Redovisningar som ett slag av spår över tid: direktiv och uppdrag som
redovisas tillbaka, och redovisningar som återkommer.
"""

from kommunhandlingar.webbplats.spar import Slag
from kommunhandlingar.webbplats.sparformer import CIRKEL, FYLLD, RUTER

REDOVISNINGAR = Slag(
    id="redovisningar",
    kolumn="redovisning",
    rubrik="Redovisningar",
    sak="Redovisning",
    saker="Redovisningarna",
    antal="redovisningar",
    faser={
        "direktiv": (CIRKEL, "beställd som direktiv eller uppdrag"),
        "redovisad": (FYLLD, "redovisad"),
        "aterkommande": (RUTER, "återkommande redovisning"),
    },
    inledning=(
        "<p>Det som redovisas för nämnden eller fullmäktige år för år: "
        "redovisningar som beställts som direktiv eller uppdrag, och när de "
        "kom tillbaka, och redovisningar som återkommer enligt lag eller "
        "årshjulet. Varje ikon länkar till sidan i dokumentet "
        "som visar steget.</p>"
    ),
    metod=(
        "<p>Ett direktiv i budgeten står här i stället för bland målen när "
        "rubriken börjar med Redovisning, Utredning eller Information, och "
        "ett uppdrag från fullmäktige står här när det redovisas tillbaka. "
        "Redovisningen är paragrafen i nämndens eller fullmäktiges protokoll. "
        "Uppföljningar av målen står på sidan om mål och direktiv, och "
        "förvaltningens stående information står inte med. Varje steg har "
        "en text som står på källans sida, och bygget prövar det.</p>"
        "<p>Där källan inte själv säger att paragrafen svarar på direktivet "
        "är kopplingen en bedömning och ikonen har en streckad ram. Ett år "
        "utan ikon betyder att inget steg står i poolen det året, inte att "
        "inget hände; poolen saknar en del protokoll. Sidan visar vad som "
        "står var och värderar inte redovisningarna.</p>"
    ),
    adr="0065-redovisningarna-foljs-som-handlingsplanerna.md",
)
