"""Krav: K44 i docs/02-KRAV.md, ADR-0067. Test: tests/test_detaljplaner.py.

Detaljplanerna som ett slag av spår över tid: från planbeskedet och
uppdraget till samrådet, granskningen, antagandet och ett överklagande
eller ett avslutat planuppdrag.
"""

from kommunhandlingar.webbplats.spar import Slag
from kommunhandlingar.webbplats.sparformer import (
    BOCK,
    BUBBLA,
    CIRKEL,
    DRAG,
    FYLLD,
    KRYSS,
    RUTER,
    TIMGLAS,
)

DETALJPLANER = Slag(
    id="detaljplaner",
    kolumn="detaljplan",
    rubrik="Detaljplaner",
    sak="Plan",
    saker="Planerna",
    antal="planer",
    faser={
        "planbesked": (CIRKEL, "planbesked"),
        "uppdrag": (f'<path d="M4 2.5v11l9-5.5z" {DRAG}/>', "planuppdrag"),
        "samrad": (BUBBLA, "samråd"),
        "granskning": (RUTER, "granskning"),
        "godkannande": (FYLLD, "godkänd för fullmäktige"),
        "antagande": (FYLLD + BOCK, "antagen"),
        "overklagande": (TIMGLAS, "överklagad"),
        "avslutad": (FYLLD + KRYSS, "planuppdraget avslutat"),
    },
    inledning=(
        "<p>Detaljplanerna som nämnden arbetar med år för år: planbeskedet, "
        "uppdraget att ta fram planen, samrådet, granskningen, godkännandet, "
        "antagandet och "
        "ett överklagande eller ett avslutat planuppdrag. Varje ikon länkar "
        "till sidan i dokumentet som visar steget.</p>"
    ),
    metod=(
        "<p>Ett steg är ett beslut i nämndens, arbetsutskottets, "
        "kommunstyrelsens eller fullmäktiges protokoll; från "
        "kommunstyrelsen planbeskedet och projektbeställningen. Beredningen av "
        "nämndens ärenden, informationen och avstämningarna står inte med, "
        "och ett planbesked bara när det blev en plan på sidan. Varje steg "
        "har en text som står på källans sida, och bygget prövar det.</p>"
        "<p>En plan har ett namn på sidan, med fastighetsbeteckningen, även "
        "när källorna kallar den olika. Där källan inte själv säger att det "
        "gäller planen är kopplingen en bedömning och ikonen har en streckad "
        "ram. Ett år utan ikon betyder att inget steg står i poolen det året, "
        "inte att inget hände; poolen saknar en del protokoll. Sidan visar vad "
        "som står var och värderar inte planerna.</p><p>En plan med ett projekt "
        "på kommunens webbplats länkar dit och till projektets dokument i "
        "poolen. Kopplingen är tolkad när planen och projektet inte gäller "
        "samma fastighet, eller projektet är ett planprogram (ADR-0069).</p>"
    ),
    adr="0067-detaljplanerna-foljs-som-redovisningarna.md",
)
