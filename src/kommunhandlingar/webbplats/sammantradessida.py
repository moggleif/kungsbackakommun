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
        + dagordningen(arenden, lankar, bool(mote.handlingar))
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


def dagordningen(arenden: list[Arende], lankar: Lankar, handlingar: bool) -> str:
    if not arenden:
        return (
            "<h2>Dagordningen</h2><p>Dagordningen gick inte att läsa ur kallelsen.</p>"
        )
    return (
        f"<h2>Dagordningen, {antal(len(arenden), 'punkt', 'punkter')}</h2>"
        + forklaring(arenden, handlingar)
        + '<div class="malkort punkter">'
        + "".join(punktkort(a, lankar) for a in arenden)
        + "</div>"
    )


# Ett äldre sammanträde kan ha kallelsen men inte handlingarna i poolen.
def forklaring(arenden: list[Arende], handlingar: bool) -> str:
    hittade = sum(1 for a in arenden if a.handling)
    return (
        "<p>Varje punkt med förslaget ur kallelsen, handlingens sidor, beslutet "
        "i protokollet och historiken i alla organ med samma diarienummer, som "
        "det står i källan. "
        + (
            f"Handlingen hittades för {hittade} av {len(arenden)}.</p>"
            if handlingar
            else "Sammanträdet har inga handlingar i poolen.</p>"
        )
    )


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
