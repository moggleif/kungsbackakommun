"""Krav: K26, K27, K28, K29, K35, K39, K50 och K60 i docs/02-KRAV.md,
ADR-0044, ADR-0045, ADR-0046, ADR-0050, ADR-0051, ADR-0056, ADR-0073 och
ADR-0086. Test: tests/test_mal.py, tests/test_malkort.py, tests/test_malar.py,
tests/test_fokusomraden.py och tests/test_uppfoljningar.py.

Sidan om ett organs mål och direktiv: en hopfälld del om metoden, antalet
per år (`malstatistik.py`), ett urval och tre perspektiv: tidslinjen
(`maltidslinje.py`), ett år i taget (`malar.py`) och ett kort per spår
(`malkort.py`). Skriptet i `mal.js` visar bara det som valts och öppnar
kortet för ett mål som väljs i tidslinjen, och `perspektiv.js` visar ett
perspektiv i taget; utan dem står allt på sidan. Löptexterna står i
`maltexter.py` och stilen i `mal.css`.
"""

from collections import defaultdict

from kommunhandlingar import frontmatter
from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.konvertering.kvalitet import UTAN_TEXT
from kommunhandlingar.webbplats import adresser, ram
from kommunhandlingar.webbplats.flikar import MAL, flikar
from kommunhandlingar.webbplats.inbaddning import skript, stil
from kommunhandlingar.webbplats.mal import SLAG, Mal
from kommunhandlingar.webbplats.malar import aren
from kommunhandlingar.webbplats.malkort import korten
from kommunhandlingar.webbplats.mall import sida
from kommunhandlingar.webbplats.malspar import Underlag
from kommunhandlingar.webbplats.malstatistik import statistik
from kommunhandlingar.webbplats.maltexter import (
    AREN,
    FOKUS,
    INLEDNING,
    METOD,
    PERSPEKTIV,
)
from kommunhandlingar.webbplats.maltidslinje import tidslinje
from kommunhandlingar.webbplats.sammanhang import Sammanhang

ADR_0044 = "0044-namndens-mal-och-direktiv-las-ur-dokumenten-och-skrivs-for-hand.md"
ADR_0045 = "0045-omdopta-mal-grupperas-protokollet-gar-fore-och-status-blir-ikoner.md"
ADR_0050 = "0050-malsidan-visas-som-tidslinje-och-malkort.md"
ADR_0051 = "0051-tidslinjen-visar-varje-rubrik-och-nya-formuleringar.md"
ADR_0056 = "0056-kommunfullmaktiges-mal-med-fokusomraden-och-farg.md"


# Sidan börjar med målens första år; poolens dokument kan vara äldre.
def fore_malen(forsta_dokument: int, forsta_mal: int) -> str:
    if forsta_dokument >= forsta_mal:
        return ""
    return (
        f"<p>Poolen har dokument från organet sedan {forsta_dokument}, men "
        f"inga av organets mål före {forsta_mal}.</p>"
    )


def adress(kommun: Kommun, organ: str) -> str:
    return adresser.over_tid(kommun.id, organ, MAL)


# Alla mål är samma organs.
def malsida(sammanhang: Sammanhang, malen: list[Mal], organets: list[dict]) -> str:
    organ, kommun = malen[0].organ, sammanhang.kommun
    rubrik = f"Mål och direktiv – {kommun.organnamn(organ)}"
    innehall = (
        flikar(sammanhang.underlag, organ, MAL)
        + stil("mal.css")
        + INLEDNING
        + fore_malen(min(frontmatter.ar(d) for d in organets), min(m.ar for m in malen))
        + om_sidan(any(m.huvudmal for m in malen))
        + perspektiven(underlaget(sammanhang, malen, organets))
        + skript("mal.js", "perspektiv.js")
    )
    return sida(sammanhang.mall, adress(kommun, organ), rubrik, innehall)


# Åren är kommunens (K60). Ett år fram till byggåret utan både dokument och
# mål är en lucka: ett år med mål ur ett senare dokument, som en
# årsredovisning, är det inte.
def underlaget(
    sammanhang: Sammanhang, malen: list[Mal], organets: list[dict]
) -> Underlag:
    organ, ar = malen[0].organ, sammanhang.underlag.aren
    uppfoljda = [u for u in sammanhang.underlag.uppfoljningar if u.organ == organ]
    dokumentar = {frontmatter.ar(d) for d in organets}
    luckor = set(range(ar[0], sammanhang.mall.byggd.year + 1)) - dokumentar
    luckor -= {m.ar for m in malen}
    return Underlag(sparen(malen), ar, luckor, uppfoljda, protokollar(organets))


# Uppföljningarna i protokollen räknas bara år med ett protokoll med text.
def protokollar(organets: list[dict]) -> set[int]:
    return {
        frontmatter.ar(d)
        for d in organets
        if d["typ"] == "protokoll" and d["kvalitet"] not in UTAN_TEXT
    }


def perspektiven(underlag: Underlag) -> str:
    malen = underlag.malen
    return (
        statistik(underlag)
        + urval(max(m.ar for m in malen), {m.slag for m in malen})
        + PERSPEKTIV
        + vy("tidslinje", tidslinje(underlag))
        + vy("ar", aren(underlag))
        + vy("kort", korten(underlag))
    )


def vy(namn: str, innehall: str) -> str:
    return f'<section data-vy="{namn}">{innehall}</section>'


def sparen(malen: list[Mal]) -> list[list[Mal]]:
    spar = defaultdict(list)
    for mal in sorted(malen, key=ordning):
        spar[mal.spar].append(mal)
    return list(spar.values())


def ordning(mal: Mal) -> tuple[int, int, str]:
    return mal.ar, SLAG.index(mal.slag), mal.rubrik.casefold()


def om_sidan(fokus: bool) -> str:
    return ram.om_sidan(
        METOD + AREN + FOKUS * fokus, ADR_0044, ADR_0045, ADR_0050, ADR_0051, ADR_0056
    )


def urval(sista: int, slagen: set[str]) -> str:
    val = [("alla", "Alla"), ("aktiv", f"Gäller {sista}")]
    val += [(slag, slag.capitalize()) for slag in SLAG if slag in slagen]
    val += [("bytt", "Har bytt rubrik")]
    return ram.urval(val, sista)
