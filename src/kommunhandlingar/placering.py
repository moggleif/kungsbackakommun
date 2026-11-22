"""Krav: K8, K9, K16 och K52 i docs/02-KRAV.md, ADR-0003, ADR-0039 och ADR-0076.
Test i tests/: test_hamta.py, test_hamta_arkiv.py och test_plattformar.py.

Var en kandidat hamnar i poolen i steg 2: på källnyckelns plats, på en
rivals plats när sammanträdet har typen från en annan plattform, och annars
på en ny plats som `plats.py` bestämmer.
"""

from dataclasses import replace
from pathlib import PurePosixPath

from kommunhandlingar.arkivluckor import motstandare, tas_over
from kommunhandlingar.kandidat import Kandidat
from kommunhandlingar.plats import Plats, grundplats, ledigt_for
from kommunhandlingar.poolskrivning import Dokument, Steg2


def motstandare_for(steg: Steg2, kandidat: Kandidat) -> PurePosixPath | None:
    if not steg.arkiv or kandidat.kallnyckel not in steg.ensamma:
        return None
    return motstandare(steg.pool, steg.kommun, kandidat)


def valj_plats(
    steg: Steg2, kandidat: Kandidat, sokvag: PurePosixPath | None
) -> Dokument:
    """Den givna platsen, kandidatens egen eller en rivals, annars en ny."""
    if sokvag is None:
        return placera(steg, kandidat)
    return Dokument(kandidat, sokvag, steg.pool.efter_sokvag[sokvag])


def placera(steg: Steg2, kandidat: Kandidat) -> Dokument:
    plats = grundplats(kandidat)
    sokvag = plats.sokvag(steg.kommun)
    upptagen = steg.pool.efter_sokvag.get(sokvag)
    if upptagen is None:
        return Dokument(kandidat, sokvag, None, plats.namn)
    if upptagen["kallnyckel"] not in steg.nycklar or tas_over(upptagen, kandidat):
        return Dokument(kandidat, sokvag, upptagen)
    namn = ledigt_for(kandidat, lambda forslag: finns(steg, plats, forslag))
    plats = replace(plats, namn=namn)
    return Dokument(kandidat, plats.sokvag(steg.kommun), None, plats.namn)


def finns(steg: Steg2, plats: Plats, namn: str) -> bool:
    return replace(plats, namn=namn).sokvag(steg.kommun) in steg.pool.efter_sokvag
