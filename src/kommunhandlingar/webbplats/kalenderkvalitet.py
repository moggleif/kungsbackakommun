"""Krav: K22 och K32 i docs/02-KRAV.md, ADR-0032 och ADR-0053.
Test: tests/test_kalenderkvalitet.py.

Kalendersidans hopfällda del om kvaliteten: hur datumen är lästa, de
osäkra datumen och källorna per organ och år.
"""

from collections import Counter, defaultdict
from html import escape
from urllib.parse import urlparse

from kommunhandlingar.webbplats import adresser, kalendervyer
from kommunhandlingar.webbplats.kalender import Sammantrade
from kommunhandlingar.webbplats.ram import hur_och_varfor

ADR_0032 = "0032-kalendern-las-ur-besluten-och-skrivs-for-hand.md"
ADR_0053 = "0053-tidigare-sammantraden-las-ur-poolens-mappar.md"
METOD = (
    "<p>Datumen är lästa ur organens mötessidor och ur deras beslut om "
    "sammanträdesdagar; källorna står per organ och år under rubriken Källor "
    "nedan, och tidigare sammanträden ur poolen, med sitt eget protokoll som "
    "källa; ett tidigare sammanträde utan dokument i poolen saknas, och ett "
    "utan protokoll är märkt osäkert. Inställda möten och "
    "planeringsdagar är inte med. Tiden står där "
    "källan anger den, och platsen visas när man håller över rutan i "
    "månadsvyn. Ett datum är osäkert när källan är svår att läsa, eller när "
    "den anger en veckodag som datumet inte stämmer med. Ett osäkert datum "
    "har ett frågetecken i månadsvyn och ordet osäkert i listan.</p>"
)


def kvalitet(sammantraden: list[Sammantrade], namn: dict[str, str]) -> str:
    osakra = [s for s in sammantraden if s.osakert]
    return (
        f'<details id="kvalitet"><summary>Kvalitet: {len(osakra)} av '
        f"{len(sammantraden)} datum är osäkra</summary>{METOD}"
        + hur_och_varfor(ADR_0032, ADR_0053)
        + f'<h2 id="osakra">Osäkra datum</h2>{osakra_tabell(osakra, namn)}'
        f'<h2 id="kallor">Källor</h2>'
        f"{kallor(sammantraden, namn)}</details>"
    )


def osakra_tabell(osakra: list[Sammantrade], namn: dict[str, str]) -> str:
    if not osakra:
        return "<p>Inga.</p>"
    rader = "".join(
        f"<tr><td>{kalendervyer.datumtext(s)}</td><td>{escape(namn[s.organ])}</td>"
        f"<td>{escape(s.osakert)}</td><td>{kallank(s.kalla)}</td></tr>"
        for s in osakra
    )
    return tabell(["Datum", "Organ", "Skäl", "Källa"], rader)


def kallor(sammantraden: list[Sammantrade], namn: dict[str, str]) -> str:
    celler = per_organ_och_ar(sammantraden)
    ar = sorted({a for _, a in celler})
    organen = {o for o, _ in celler}
    rader = "".join(
        f'<tr><th scope="row">{escape(namn[organ])}</th>'
        + "".join(f"<td>{kallcell(organ, celler.get((organ, a), {}))}</td>" for a in ar)
        + "</tr>"
        for organ in namn
        if organ in organen
    )
    return tabell(["Organ", *ar], rader)


# Sammanträden med sitt eget dokument som källa (ADR-0053) räknas under
# nyckeln "" i stället för att länkas ett och ett.
def per_organ_och_ar(sammantraden: list[Sammantrade]) -> dict[tuple, Counter]:
    celler = defaultdict(Counter)
    for s in sammantraden:
        celler[(s.organ, s.datum.year)]["" if eget_dokument(s) else s.kalla] += 1
    return celler


def eget_dokument(s: Sammantrade) -> bool:
    return s.kalla.split("/")[:3] == [s.organ, str(s.datum.year), s.datum.isoformat()]


def tabell(rubriker: list, rader: str) -> str:
    huvud = "".join(f'<th scope="col">{r}</th>' for r in rubriker)
    return (
        f'<div class="tabell"><table><thead><tr>{huvud}</tr></thead>'
        f"<tbody>{rader}</tbody></table></div>"
    )


def kallcell(organ: str, cell: dict[str, int]) -> str:
    lankar = [kallank(k) for k in cell if k]
    if cell.get(""):
        adress = adresser.organ_i_katalogen(organ)
        lankar.append(f'<a href="{adress}">{cell[""]} sammanträden i poolen</a>')
    return "<br>".join(lankar)


def kallank(kalla: str) -> str:
    if kalla.startswith("https://"):
        return f'<a href="{escape(kalla)}">{escape(urlparse(kalla).netloc)}</a>'
    organ, _, datum, fil = kalla.split("/", 3)
    adress = adresser.dokumentsida(kalla)
    text = f"{organ.upper()} {datum}, {fil.split('-')[0].removesuffix('.md')}"
    return f'<a href="{escape(adress)}">{escape(text)}</a>'
