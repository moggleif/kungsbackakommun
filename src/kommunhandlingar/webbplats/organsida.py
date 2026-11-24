"""Krav: K18, K26, K36, K37, K39 och K54 i docs/02-KRAV.md, ADR-0023.
Test: tests/test_webbplats_dokument.py, tests/test_mal.py, tests/test_lokalbehov.py,
tests/test_initiativ.py."""

from collections import defaultdict
from html import escape

from kommunhandlingar import frontmatter
from kommunhandlingar.webbplats import adresser
from kommunhandlingar.webbplats.flikar import SAMMANTRADEN, flikar
from kommunhandlingar.webbplats.luckor import motesnamn
from kommunhandlingar.webbplats.mall import lank, sida
from kommunhandlingar.webbplats.rakning import Organrad
from kommunhandlingar.webbplats.sammanhang import Sammanhang
from kommunhandlingar.webbplats.sammantrade import adress as sammantradets
from kommunhandlingar.webbplats.sammantrade import har_sida, ordnade

Mote = tuple[str, str]


def organsida(sammanhang: Sammanhang, rad: Organrad, dokument: list[dict]) -> str:
    moten = defaultdict(list)
    for d in dokument:
        moten[(d["datum"], d["lopnr"])].append(d)
    saknas = {(lucka.datum, lucka.lopnr): lucka.saknas for lucka in rad.luckor}
    ar = defaultdict(list)
    for mote in sorted(moten, key=ordning, reverse=True):
        rubrik = moterubrik(mote, moten[mote])
        ar[mote[0][:4]].append(motesavsnitt(rubrik, moten[mote], saknas.get(mote, ())))
    adress = adresser.organsida(sammanhang.kommun.id, rad.id)
    innehall = flikar(sammanhang.underlag, rad.id, SAMMANTRADEN) + (
        "".join(f"<h2>{escape(a)}</h2>{''.join(m)}" for a, m in ar.items())
        or "<p>Inget hämtat än.</p>"
    )
    return sida(sammanhang.mall, adress, rad.namn, innehall)


# Det första sammanträdet en dag har inget löpnummer, nästa har 2 (ADR-0003).
def ordning(mote: Mote) -> tuple[str, int]:
    datum, lopnr = mote
    return datum, 1 if frontmatter.saknas(lopnr) else int(lopnr)


def dokumentrubrik(d: dict) -> str:
    return d["typ"] + ("" if frontmatter.saknas(d["namn"]) else f" – {d['namn']}")


# Rubriken länkar till sammanträdets sida när den finns (K54).
def moterubrik(mote: Mote, dokument: list[dict]) -> str:
    namn = escape(motesnamn(*mote))
    if not har_sida(dokument):
        return f'<h3 id="{namn}">{namn}</h3>'
    lank = f'<a href="{escape(sammantradets(dokument))}">punkt för punkt</a>'
    return f'<h3 id="{namn}">{namn} – {lank}</h3>'


def motesavsnitt(rubrik: str, dokument: list[dict], saknas: tuple[str, ...]) -> str:
    poster = [dokumentpost(d) for d in ordnade(dokument)]
    poster += [f"{escape(grupp)} saknas" for grupp in saknas]
    punkter = "".join(f"<li>{post}</li>" for post in poster)
    return f"{rubrik}<ul>{punkter}</ul>"


def dokumentpost(d: dict) -> str:
    rader = [f"kvalitet {d['kvalitet']}"]
    if obekraftade := len(frontmatter.lista(d["tal_obekraftade"])):
        rader.append(f"obekräftade tal på {obekraftade} sidor")
    post = f'<a href="{escape(d["adress"])}">{escape(dokumentrubrik(d))}</a>: '
    post += escape(", ".join(rader))
    if not frontmatter.saknas(d["fel"]):
        post += f", fel {escape(d['fel'])}, " + lank(
            frontmatter.adresser(d["kalla_url"])[0], "källan"
        )
    return post
