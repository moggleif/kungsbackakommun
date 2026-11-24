"""Krav: K96 i docs/02-KRAV.md, ADR-0119. Test: tests/test_sokdokument.py.

Dokumentens grupp i webbplatsens sökindex `sok.json`, efter protokollens
paragrafer (K62): en post per dokument, nyast först, med kvaliteten och
sidorna med obekräftade tal och osäkra tabeller, så att den som söker ser
det innan dokumentet öppnas. Namnet söks med bindestrecken som mellanslag.
"""

from kommunhandlingar import frontmatter
from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats import adresser
from kommunhandlingar.webbplats.organsida import dokumentrubrik
from kommunhandlingar.webbplats.sokindex import klartext


def grupp(kommun: Kommun, dokumenten: list[dict]) -> dict:
    namn = kommun.organnamnen()
    ordnade = sorted(dokumenten, key=lambda d: d["datum"], reverse=True)
    return {
        "rubrik": f"Dokumenten i {kommun.namn}",
        "poster": [post(d, namn[d["organ"]], kommun.id) for d in ordnade],
    }


def post(falt: dict, organ: str, kommun_id: str) -> dict:
    rubrik = dokumentrubrik(falt)
    rubrik = rubrik[:1].upper() + rubrik[1:]
    datum = klartext(falt["datum"])
    return {
        "rubrik": rubrik,
        "adress": adresser.i_kommunen(kommun_id, falt["adress"]),
        "om": [organ, datum, *kvaliteten(falt)],
        "traff": rubrik.replace("-", " ").lower(),
        "text": f"{organ} {datum}".lower(),
    }


def kvaliteten(falt: dict) -> list[str]:
    obekraftade = len(frontmatter.lista(falt["tal_obekraftade"]))
    tabeller = frontmatter.lista(falt["kvalitet_per_sida"]).count("tabell-osaker")
    return [f"kvalitet {falt['kvalitet']}"] + [
        f"{vad} på {antal} {'sida' if antal == 1 else 'sidor'}"
        for vad, antal in (
            ("obekräftade tal", obekraftade),
            ("osäkra tabeller", tabeller),
        )
        if antal
    ]
