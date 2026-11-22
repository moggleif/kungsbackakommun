"""Krav: K47 och K48 i docs/02-KRAV.md, ADR-0070 och ADR-0071.
Test: tests/test_dokumentindex.py, tests/test_paragrafindex.py.

`llms.txt` i webbplatsens rot, enligt https://llmstxt.org/: ingången för
en AI, som säger hur poolen ska läsas och pekar på varje kommuns index,
sidor och filer skrivna för hand.
"""

from kommunhandlingar.webbplats.adresser import organets_sida, oversikt
from kommunhandlingar.webbplats.bygge import Bygge
from kommunhandlingar.webbplats.mall import KALLKOD
from kommunhandlingar.webbplats.sammanhang import Sammanhang
from kommunhandlingar.webbplats.slagen import SLAGEN

INLEDNING = """# kommunhandlingar

> Kommunernas politiska handlingar – kallelser, handlingar och protokoll –
> konverterade från PDF till Markdown, med tabellerna som CSV och källan och
> kvaliteten i varje dokument.

Varje dokument börjar med front matter: varifrån det kom, när det hämtades
och hur väl konverteringen lyckades. Fälten förklaras i
[arkitekturen]({kod}/blob/main/docs/03-ARKITEKTUR.md#front-matter).
`kvalitet` säger hur texten lästes. Tal på sidorna i `tal_obekraftade` är
inte bekräftade och ska inte användas som data. Ett fält utan värde är
`null`; tomt är inte noll. Poolen återger källan och drar inga slutsatser.

Indexet har en rad per dokument i JSON Lines, med hela front matter.
`fil` är sökvägen i repot, och Markdown-filen finns på
`{repo}/raw/main/<fil>`. `sida` är dokumentets sida på den här webbplatsen,
och tabellerna i `tabeller` ligger bredvid den i
`<sida utan .html>.tabeller/`.

Paragraferna har en rad per paragraf i protokollen, med rubriken,
diarienumren, beslutet och sidan där paragrafen börjar. `beslut` är `null`
när paragrafen saknar rubriken Beslut eller beslutet når sidans slut;
läs det då på sidan. `arenden` i indexet är protokollets alla diarienummer.
"""


def llms(bygge: Bygge) -> str:
    mall = bygge.mall
    avsnitt = [INLEDNING.format(repo=mall.repo, kod=KALLKOD)]
    avsnitt += [kommunavsnitt(bygge.sammanhang(k)) for k in mall.kommuner]
    return "\n".join(avsnitt)


def kommunavsnitt(sammanhang: Sammanhang) -> str:
    mall, kommun = sammanhang.mall, sammanhang.kommun
    lankar = [
        f"[Index över dokumenten]({kommun.id}/index.jsonl)",
        f"[Protokollens paragrafer]({kommun.id}/paragrafer.jsonl)",
        f"[Översikt]({oversikt(kommun.id)})",
    ]
    lankar += [f"[{o.namn[0]}]({organets_sida(kommun.id, o.id)})" for o in kommun.organ]
    kalendern = {"kalender"} if kommun.id in mall.kalendrar else set()
    lankar += [
        f"[{rubrik}]({mall.repo}/raw/main/{katalog}/{kommun.id}.csv): skriven för hand"
        for katalog, rubrik in handskrivna(sammanhang.underlag.filer | kalendern)
    ]
    return f"## {kommun.namn}\n\n" + "".join(f"- {lank}\n" for lank in lankar)


# Katalogerna i `filer` med sina rubriker, i den ordning de länkas.
def handskrivna(filer: frozenset[str]) -> list[tuple[str, str]]:
    kataloger = [
        ("kalender", "Kalendern"),
        ("mal", "Mål och direktiv"),
        ("uppfoljningar", "Uppföljningar av målen"),
    ]
    kataloger += [(s.id, s.rubrik) for s in SLAGEN]
    kataloger.append(("projekt", "Detaljplanernas projekt"))
    return [(katalog, rubrik) for katalog, rubrik in kataloger if katalog in filer]
