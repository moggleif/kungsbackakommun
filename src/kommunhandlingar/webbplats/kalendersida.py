"""Krav: K22, K32, K49, K51 och K58 i docs/02-KRAV.md, ADR-0032, ADR-0053,
ADR-0072, ADR-0074 och ADR-0084. Test: tests/test_kalender.py,
tests/test_kalenderkvalitet.py, tests/test_gruppmoten.py, tests/test_tema.py
och tests/test_navigering.py.

Kalendersidan: en hopfälld del om kvaliteten (`kalenderkvalitet.py`), urvalet
av organ, en tabell per månad och listan, med partiernas gruppmöten bland
sammanträdena. Skriptet i `kalender.js` visar en månad i taget och döljer
det som valts bort; utan det står allt på sidan.
"""

from datetime import date
from html import escape

from kommunhandlingar.gruppmote import VECKODAGAR, Gruppmote
from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import adresser, kalendervyer
from kommunhandlingar.webbplats.inbaddning import las, skript
from kommunhandlingar.webbplats.kalender import GRUPPMOTE, Sammantrade
from kommunhandlingar.webbplats.kalenderfarger import farger, organstil
from kommunhandlingar.webbplats.kalenderkvalitet import kvalitet
from kommunhandlingar.webbplats.mall import Mall, sida
from kommunhandlingar.webbplats.meny import kommunens

INLEDNING = (
    "<p>Organens sammanträden månad för månad och som lista från idag. "
    "Tidigare sammanträden finns bakåt i månadsvyn och under en knapp i "
    "listan. Välj vilka organ som visas.</p>"
)


def kalendersida(mall: Mall, kommun: Kommun, sammantraden: list[Sammantrade]) -> str:
    moten = gruppmoten(sammantraden, kommun.gruppmote, mall.byggd.date())
    meny = kommunens(mall.kommuner, "Kalender", kommun)
    innehall = innehallet(kommun, sammantraden, moten)
    return sida(mall, adresser.kalender(kommun.id), meny, innehall)


def innehallet(
    kommun: Kommun, sammantraden: list[Sammantrade], moten: list[Sammantrade]
) -> str:
    namn = namnen(kommun, moten)
    farg = farger(kommun, {s.organ for s in sammantraden})
    return (
        f"<style>{las('kalender.css')}{organstil(farg)}</style>"
        + INLEDNING
        + kvalitet(sammantraden, namn)
        + om_gruppmoten(kommun, moten)
        + urval([*farg, *([GRUPPMOTE] if moten else [])], namn)
        + kalendervyer.manader(sammantraden + moten)
        + kalendervyer.lista(sammantraden + moten, namn)
        + skript("kalender.js")
    )


# Ett gruppmöte är en vana, inte ett sammanträde med källa, och ärver inte
# sammanträdets osäkerhet.
def gruppmoten(
    sammantraden: list[Sammantrade], regel: Gruppmote | None, idag: date
) -> list[Sammantrade]:
    if regel is None:
        return []
    dagar = regel.dagarna(((s.organ, s.datum) for s in sammantraden), idag)
    return [Sammantrade(GRUPPMOTE, dag, regel.tid, "", "", "") for dag in dagar]


def namnen(kommun: Kommun, moten: list[Sammantrade]) -> dict[str, str]:
    namn = kommun.organnamnen()
    if moten:
        namn[GRUPPMOTE] = f"Partiernas gruppmöte inför {namn[kommun.gruppmote.fore]}"
    return namn


def om_gruppmoten(kommun: Kommun, moten: list[Sammantrade]) -> str:
    if not moten:
        return ""
    regel = kommun.gruppmote
    return (
        "<p>Partierna har gruppmöte "
        f"{VECKODAGAR[regel.veckodag]}en före varje sammanträde i "
        f"{escape(kommun.organnamn(regel.fore))}. Det är en vana hos partierna, "
        "inget beslutat sammanträde. Datumen är räknade ur sammanträdena, inte "
        "lästa i någon källa, och bara kommande gruppmöten visas.</p>"
    )


def urval(organen: list[str], namn: dict[str, str]) -> str:
    rutor = "".join(
        f'<label><input type="checkbox" checked data-organ="{organ}"> '
        f'<span class="ruta o-{organ}">{kalendervyer.kort(organ)}</span> '
        f"{escape(namn[organ])}</label>"
        for organ in organen
    )
    alla = '<p class="alla" hidden><button type="button">Dölj alla</button></p>'
    rubrik = f"<legend>Organ som visas</legend>{alla}"
    return f'<fieldset class="urval">{rubrik}{rutor}</fieldset>'
