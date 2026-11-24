"""Krav: K54 i docs/02-KRAV.md, ADR-0078. Test: tests/test_sammantradessida.py.

Sammanträdets sida: en rad per dokument från sammanträdet och sedan
dagordningen, en punkt i taget (`punktkort.py`). Sidan ligger bredvid
sammanträdets katalog. Stilen är målkortens (`mal.css`) och `mote.css`.
"""

from html import escape

from kommunhandlingar import frontmatter
from kommunhandlingar.webbplats import adresser
from kommunhandlingar.webbplats.inbaddning import stil
from kommunhandlingar.webbplats.luckor import motesnamn
from kommunhandlingar.webbplats.mall import Mall, sida, stig
from kommunhandlingar.webbplats.meny import oversiktsnamn
from kommunhandlingar.webbplats.organsida import dokumentrubrik
from kommunhandlingar.webbplats.punktkort import Lankar, antal, punktkort
from kommunhandlingar.webbplats.sammantrade import Arende, Mote, adress, ordnade


def sammantradessida(mall: Mall, mote: Mote, arenden: list[Arende]) -> str:
    kommun, forsta = mote.kommun, mote.dokument[0]
    sidans = adresser.i_kommunen(kommun.id, adress(mote.dokument))
    lankar = lankarna(mote, sidans)
    innehall = (
        stig(vagen(mall, mote, lankar))
        + stil("mal.css", "mote.css")
        + "<h2>Sammanträdets dokument</h2>"
        + dokumentlista(kommun.id, mote.dokument, lankar.rot)
        + dagordningen(arenden, lankar, mote)
    )
    organ = lankar.organnamn[forsta["organ"]]
    rubrik = f"{organ} {motesnamn(forsta['datum'], forsta['lopnr'])}"
    return sida(mall, sidans, rubrik, innehall)


def lankarna(mote: Mote, sidans: str) -> Lankar:
    kommun = mote.kommun
    return Lankar(
        adresser.rot(sidans),
        handlingarna(kommun.id, mote.dokument),
        kommun.organnamnen(),
    )


def vagen(mall: Mall, mote: Mote, lankar: Lankar) -> list[tuple[str, str]]:
    kommun, organ = mote.kommun, mote.dokument[0]["organ"]
    return [
        (
            lankar.rot + adresser.oversikt(kommun.id),
            oversiktsnamn(mall.kommuner, kommun),
        ),
        (lankar.rot + adresser.organsida(kommun.id, organ), lankar.organnamn[organ]),
    ]


def dagordningen(arenden: list[Arende], lankar: Lankar, mote: Mote) -> str:
    if not arenden:
        return f"<h2>Dagordningen</h2><p>{utan_dagordning(mote)}</p>"
    return (
        f"<h2>Dagordningen, {antal(len(arenden), 'punkt', 'punkter')}</h2>"
        + "<p>Varje punkt med förslaget ur kallelsen, handlingens sidor, beslutet "
        "i protokollet och historiken i alla organ med samma diarienummer, som "
        f"det står i källan. {om_handlingen(arenden, mote)}</p>"
        + '<div class="malkort punkter">'
        + "".join(punktkort(a, lankar) for a in arenden)
        + "</div>"
    )


# Tomt är inte noll: ett dokument som inte gick att hämta eller läsa skiljs
# från ett som inte finns i poolen (ADR-0113).
def utan_dagordning(mote: Mote) -> str:
    if forsta(mote, "kallelse")["kvalitet"] == "ej-hamtad":
        return "Kallelsen gick inte att hämta, så dagordningen saknas."
    return "Dagordningen gick inte att läsa ur kallelsen."


def om_handlingen(arenden: list[Arende], mote: Mote) -> str:
    if forsta(mote, "handlingar") is None:
        return "Sammanträdet har inga handlingar i poolen."
    if not mote.handlingar:
        return "Handlingarna gick inte att hämta eller läsa."
    hittade = sum(1 for a in arenden if a.handling)
    return f"Handlingen hittades för {hittade} av {len(arenden)}."


def forsta(mote: Mote, typ: str) -> dict | None:
    return next((d for d in ordnade(mote.dokument) if d["typ"] == typ), None)


def dokumentlista(kommun_id: str, dokument: list[dict], till_rot: str) -> str:
    rader = "".join(
        dokumentpost(till_rot + adresser.i_kommunen(kommun_id, d["adress"]), d)
        for d in ordnade(dokument)
    )
    return f"<ul>{rader}</ul>"


def dokumentpost(adress: str, d: dict) -> str:
    return (
        f'<li><a href="{escape(adress)}">'
        f"{escape(dokumentrubrik(d).capitalize())}</a>{sidantal(d)}</li>"
    )


def handlingarna(kommun_id: str, dokument: list[dict]) -> str:
    handlingar = [d["adress"] for d in ordnade(dokument) if d["typ"] == "handlingar"]
    return adresser.i_kommunen(kommun_id, handlingar[0]) if handlingar else ""


def sidantal(d: dict) -> str:
    if frontmatter.saknas(d["sidor"]):
        return ""
    return f" <small>{antal(int(d['sidor']), 'sida', 'sidor')}</small>"
