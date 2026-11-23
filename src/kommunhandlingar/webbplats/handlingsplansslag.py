"""Krav: K38 i docs/02-KRAV.md, ADR-0059. Test: tests/test_handlingsplaner.py.

Handlingsplaner, program och policyer som ett slag av spår över tid:
från uppdraget till planen, antagandet, uppföljningen och revideringen.
"""

from kommunhandlingar.webbplats.spar import Slag
from kommunhandlingar.webbplats.sparformer import (
    BOCK,
    BUBBLA,
    CIRKEL,
    DRAG,
    FYLLD,
    RUTER,
    TIMGLAS,
)

HANDLINGSPLANER = Slag(
    id="handlingsplaner",
    kolumn="plan",
    rubrik="Handlingsplaner",
    sak="Plan",
    saker="Planerna",
    antal="planer",
    faser={
        "uppdrag": (CIRKEL, "förslag, uppdrag eller arbete"),
        "yttrande": (BUBBLA, "yttrande"),
        "plan": (
            f'<path d="M3.5 1.5h6l3 3v10h-9z" {DRAG}/>'
            '<path d="M5.5 7.5h5M5.5 10h5" stroke="currentColor"/>',
            "själva planen",
        ),
        "antagen": (FYLLD + BOCK, "antagen eller framtagen"),
        "uppfoljning": (RUTER, "uppföljning"),
        "revidering": (TIMGLAS, "revidering"),
    },
    inledning=(
        "<p>Handlingsplaner, program och policyer år för år: vem som "
        "föreslog dem, när de antogs och hur de följdes upp och reviderades. "
        "Varje ikon länkar till sidan i dokumentet som visar steget, och "
        "finns själva planen i poolen länkar kortet till den.</p>"
    ),
    metod=(
        "<p>En plan står med när den har ett eget steg i nämndens eller "
        "fullmäktiges protokoll eller handlingar: ett uppdrag, ett beslut, ett "
        "yttrande, en återrapport eller en uppföljning. Organets egna planer "
        "står med, och gemensamma planer där organet har ett eget steg. "
        "Planer som bara nämns, den interna kontrollplanen och planer för "
        "enskilda elever står inte med. Avsändaren står när planen kommer "
        "ur en motion eller ett initiativ, som källan skriver den. Varje steg "
        "har en text som står på källans sida, och bygget prövar det.</p>"
        "<p>En plan har ett namn på sidan även när källorna kallar den olika. "
        "Där källan inte själv säger att det gäller planen är kopplingen en "
        "bedömning och ikonen har en streckad ram. Ett år utan ikon betyder "
        "att inget steg står i poolen det året, inte att inget hände; poolen "
        "saknar en del protokoll. Sidan visar vad som står var och värderar "
        "inte planerna.</p>"
    ),
    adr="0059-handlingsplanerna-foljs-som-initiativen.md",
    avsandare="uppdrag",
    planen="plan",
)
