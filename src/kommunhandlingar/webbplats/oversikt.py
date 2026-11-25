"""Krav: K39 och K96 i docs/02-KRAV.md, ADR-0060 och ADR-0119.
Test: tests/test_navigering.py.

Kommunens sida: en rad per organ med antalet sammanträden och en kolumn
per sida över tid som något av kommunens organ har (K59), så att det syns
vilka organ som har vilka sidor. Ett
utskott står direkt under organet det hör till, och organen står i
kommunfilens grupper när den har några. En webbplats med en enda kommun
börjar på kommunens sida, som då heter "Handlingar och protokoll" i stället för
sajtens namn (K58, ADR-0082). Överst länkar sidan till GitHubs sökning
i hela texten i kommunens mapp, som inte söker i filer över 350 kB
(K96, ADR-0119).
"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property, partial
from html import escape
from urllib.parse import quote_plus

from kommunhandlingar.konfiguration import Kommun, Organ
from kommunhandlingar.webbplats import adresser
from kommunhandlingar.webbplats.flikar import SIDOR, overtid
from kommunhandlingar.webbplats.mall import Mall
from kommunhandlingar.webbplats.organordning import grupperade
from kommunhandlingar.webbplats.rakning import Organrad
from kommunhandlingar.webbplats.sammanhang import Sammanhang

GITHUB = "https://github.com/"
TOM = '<td class="tom">–<span class="dold"> saknas</span></td>'


def oversiktens_adresser(mall: Mall, kommun: Kommun) -> list[str]:
    egen = adresser.oversikt(kommun.id)
    return [egen, adresser.STARTSIDA] if mall.en_kommun else [egen]


def oversikt(
    sammanhang: Sammanhang, rader: list[Organrad], dokument: list[dict]
) -> str:
    kommun = sammanhang.kommun
    tabellen = Tabellen(
        kommun,
        {o.id: overtid(sammanhang.underlag, o.id) for o in kommun.organ},
        {rad.id: rad.sammantraden for rad in rader},
    )
    grupper = "".join(tabellen.grupp(namn, o) for namn, o in grupperade(kommun))
    return (
        inledning(dokument)
        + fulltext(sammanhang.mall.repo, kommun.id)
        + tabell(tabellen.huvud(), grupper)
    )


def tabell(huvud: str, grupper: str) -> str:
    return (
        '<div class="tabell"><table class="oversikt"><thead><tr>'
        f'<th scope="col">Organ</th><th scope="col">Sammanträden</th>{huvud}'
        f"</tr></thead>{grupper}</table></div>"
    )


# Antalet per organ och sida över tid, och antalet sammanträden per organ.
@dataclass(frozen=True)
class Tabellen:
    kommun: Kommun
    antal: dict[str, dict[str, int]]
    sammantraden: dict[str, int]

    @cached_property
    def sidor(self) -> list[tuple[str, str, str]]:
        return kommunens_sidor(self.antal)

    def huvud(self) -> str:
        return "".join(f'<th scope="col">{escape(r)}</th>' for _, r, _ in self.sidor)

    def grupp(self, namn: str, organen: list[Organ]) -> str:
        rader = "".join(self.rad(o) for o in organen)
        return f"<tbody>{grupprad(namn, len(self.sidor) + 2)}{rader}</tbody>"

    def rad(self, organ: Organ) -> str:
        over_tid = partial(adresser.over_tid, self.kommun.id, organ.id)
        return (
            organrad(self.kommun.id, organ, self.sammantraden[organ.id])
            + celler(over_tid, self.antal[organ.id], self.sidor)
            + "</tr>"
        )


def kommunens_sidor(antal: dict[str, dict[str, int]]) -> list[tuple[str, str, str]]:
    return [s for s in SIDOR if any(a[s[0]] for a in antal.values())]


def inledning(dokument: list[dict]) -> str:
    datum = sorted(d["datum"] for d in dokument) or ["–"]
    antal = f"{len(dokument):,}".replace(",", " ")
    return (
        f"<p>{antal} dokument från {escape(datum[0])} till {escape(datum[-1])}. "
        "Välj ett organ, eller gå direkt till en av dess sidor över tid. "
        "Ett streck betyder att organet inte har sidan.</p>"
    )


def fulltext(repo: str, kommun_id: str) -> str:
    fraga = quote_plus(f"repo:{repo.removeprefix(GITHUB)} path:data/{kommun_id}/")
    adress = escape(f"{GITHUB}search?q={fraga}&type=code")
    return (
        f'<p><a href="{adress}">Sök i hela texten på GitHub</a> '
        "(kräver inloggning på GitHub, och de största handlingarna, filer "
        "över 350 kB, söks inte).</p>"
    )


def grupprad(namn: str, kolumner: int) -> str:
    if not namn:
        return ""
    return (
        f'<tr class="grupp"><th scope="rowgroup" colspan="{kolumner}">'
        f"{escape(namn)}</th></tr>"
    )


def celler(over_tid: Callable[[str], str], antal: dict[str, int], sidor: list) -> str:
    return "".join(
        f'<td><a href="{over_tid(sida)}">{antal[sida]} {escape(enhet)}</a></td>'
        if antal[sida]
        else TOM
        for sida, _, enhet in sidor
    )


def organrad(kommun_id: str, organ: Organ, sammantraden: int) -> str:
    klass = ' class="utskott"' if organ.hor_till else ""
    organets = adresser.organsida(kommun_id, organ.id)
    return (
        f'<tr><th scope="row"{klass}><a href="{organets}">'
        f"{escape(organ.namn[0])}</a></th>"
        f'<td><a href="{organets}">{sammantraden}</a></td>'
    )
