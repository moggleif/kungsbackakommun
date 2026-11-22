"""Krav: K23 och K31 i docs/02-KRAV.md, ADR-0018, ADR-0039 och ADR-0049.
Test: tests/test_episerver_arkiv.py och tests/test_sammanslagning.py.

Organens mappar i Episerver-generationerna ur Internet Archive. Varje PDF
under en mapp är en fil, också när arkivet har den under http och https,
med och utan www; filen får arkivets största kopia och vid lika den äldsta.
En mapp som arkivet inte svarar för hoppas över och returneras som en
notering. En fil i en syskonmapp som börjar likadant hör inte till mappen.
Ett mötes filer av samma typ i samma mapp, till exempel en per
ärende, blir en kandidat i delar, i sökvägarnas ordning med talen som tal.
Mappen hör till gruppen, så att två nämnder som lagts under samma organ
inte slås ihop när de möttes samma dag.
"""

import re
from dataclasses import dataclass, replace
from urllib.parse import quote, unquote, urlsplit

from kommunhandlingar.adaptrar import episerver, wayback
from kommunhandlingar.fel import Hamtfel, IngenKandidat
from kommunhandlingar.kandidat import Avvisad, Fynd, Kandidat


@dataclass(frozen=True)
class Mapp:
    organ: str
    adress: str

    @property
    def sokvag(self) -> str:
        """Sökvägen efter värden, avkodad."""
        return unquote(self.adress.split("/", 1)[1])


def upptack(kalla: episerver.Kalla, klient) -> Fynd:
    mappar = (Mapp(o, m) for o, adresser in kalla.mappar.items() for m in adresser)
    fynd = sum((fraga_mapp(klient, kalla, mapp) for mapp in mappar), Fynd())
    return replace(fynd, kandidater=moten(fynd.kandidater))


def fraga_mapp(klient, kalla: episerver.Kalla, mapp: Mapp) -> Fynd:
    try:
        kopior = wayback.fraga_under(klient, mapp.adress, "application/pdf")
    except Hamtfel as fel:
        return Fynd(noteringar=[str(fel)])
    return las_mapp(kalla, mapp, kopior)


def moten(kandidater: list[Kandidat]) -> list[Kandidat]:
    grupper: dict[tuple, list[Kandidat]] = {}
    for k in kandidater:
        grupper.setdefault((k.organ, k.kalla, k.datum, k.typ), []).append(k)
    return [
        filer[0] if len(filer) == 1 else i_delar(filer) for filer in grupper.values()
    ]


def i_delar(filer: list[Kandidat]) -> Kandidat:
    """Nyckeln är mappens, mötets och typens, så att den inte beror på
    vilken del som kom först. Ett blanksteg i en adress kodas, så att listan
    går att läsa."""
    filer = sorted(filer, key=lambda k: naturlig(unquote(k.kallnyckel)))
    forsta = filer[0]
    mapp = quote(unquote(forsta.kalla), safe="/")
    nyckel = f"episerver:{mapp}{forsta.datum.isoformat()}/{forsta.typ}"
    delar = tuple(k.url.replace(" ", "%20") for k in filer)
    return replace(forsta, kallnyckel=nyckel, delar=delar)


def naturlig(text: str) -> list:
    return [int(d) if d.isdigit() else d for d in re.split(r"(\d+)", text)]


def las_mapp(kalla: episerver.Kalla, mapp: Mapp, kopior: list[wayback.Kopia]) -> Fynd:
    kandidater, avvisade = [], []
    i_mappen = [k for k in kopior if inne_i(mapp, k)]
    filer = wayback.basta(i_mappen, lambda k: nyckel_av(k.original), wayback.storst)
    for kopia in filer.values():
        try:
            kandidater.append(kandidat(kalla, mapp, kopia))
        except IngenKandidat as fel:
            avvisade.append(Avvisad(mapp.adress, filnamn(kopia), str(fel)))
    return Fynd(kandidater, avvisade)


def nyckel_av(original: str) -> str:
    """Värden utan www och port, och sökvägen kodad på ett enda sätt."""
    delar = urlsplit(original)
    vard = delar.hostname.removeprefix("www.")
    return f"episerver:{vard}{quote(unquote(delar.path), safe='/')}"


def kandidat(kalla: episerver.Kalla, mapp: Mapp, kopia: wayback.Kopia) -> Kandidat:
    kallnyckel = nyckel_av(kopia.original)
    typ, datum = episerver.typ_och_datum(kalla, under(mapp, kopia), kallnyckel)
    return Kandidat(
        organ=mapp.organ,
        datum=datum,
        typ=typ,
        url=wayback.adress(kopia),
        kalla=mapp.adress,
        kallnyckel=kallnyckel,
        filnamn=filnamn(kopia),
    )


def sokvag(kopia: wayback.Kopia) -> str:
    """Kopians sökväg efter värden, avkodad."""
    return unquote(urlsplit(kopia.original).path).lstrip("/")


def inne_i(mapp: Mapp, kopia: wayback.Kopia) -> bool:
    """Arkivets prefix tar också syskonmappar med längre namn, som
    "Kommunstyrelsens arbetsutskott/" för "Kommunstyrelsen/"."""
    return sokvag(kopia).startswith(mapp.sokvag)


def under(mapp: Mapp, kopia: wayback.Kopia) -> str:
    """Sökvägen under mappen, avkodad."""
    return sokvag(kopia)[len(mapp.sokvag) :]


def filnamn(kopia: wayback.Kopia) -> str:
    return sokvag(kopia).rsplit("/", 1)[-1]
