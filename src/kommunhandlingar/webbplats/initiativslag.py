"""Krav: K37 i docs/02-KRAV.md, ADR-0058. Test: tests/test_initiativ.py.

Initiativärenden och motioner som ett slag av spår över tid: från ärendet
som väcks till beredningen, beslutet, uppföljningen och genomförandet.
"""

from kommunhandlingar.webbplats.spar import Slag
from kommunhandlingar.webbplats.sparformer import (
    BOCK,
    BUBBLA,
    CIRKEL,
    FYLLD,
    KLART,
    KRYSS,
    RUTER,
    TIMGLAS,
)

INITIATIV = Slag(
    id="initiativ",
    kolumn="arende",
    rubrik="Initiativ och motioner",
    sak="Ärende",
    saker="Ärendena",
    antal="ärenden",
    faser={
        "vackt": (CIRKEL, "väckt"),
        "beredning": (TIMGLAS, "beredning"),
        "bifall": (FYLLD + BOCK, "bifall"),
        "avslag": (FYLLD + KRYSS, "avslag"),
        "besvarat": (BUBBLA, "besvarat"),
        "uppfoljning": (RUTER, "uppföljning"),
        "genomfort": (KLART, "genomfört"),
    },
    inledning=(
        "<p>Initiativärenden och motioner år för år: vem som väckte dem, hur "
        "de bereddes, vad som beslutades, hur besluten följdes upp och om "
        "förslaget blev genomfört. Varje ikon länkar till sidan i dokumentet "
        "som visar steget.</p>"
    ),
    metod=(
        "<p>Stegen är lästa ur poolens dokument, från vilket organ som helst. "
        "Avsändaren står som källan skriver den: ett parti, flera partier, "
        "Alliansen, eller partilös där källan skriver (-). Varje steg har en "
        "text som står på källans sida, och bygget prövar det.</p>"
        "<p>Ett ärende har ett namn på sidan även när källorna kallar det "
        "olika. Där källan inte själv säger att det gäller ärendet är "
        "kopplingen en bedömning och ikonen har en streckad ram. Ett år utan "
        "ikon betyder att inget steg står i poolen det året, inte att inget "
        "hände; poolen saknar en del protokoll. Sidan visar vad som står var "
        "och värderar inte ärendena.</p>"
    ),
    adr="0058-initiativarenden-foljs-som-lokalbehoven.md",
    varden={"vackt": (r".+", "en avsändare")},
    avsandare="vackt",
)
