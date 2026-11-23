"""Krav: K39 i docs/02-KRAV.md, ADR-0060. Test: tests/test_navigering.py.

Ett organs sidor: sammanträdena och de sidor över tid som organet har
rader för, i samma ordning för alla organ. Kommunsidans översikt och
flikarna på organets sidor byggs ur samma lista.
"""

from kommunhandlingar.webbplats import adresser
from kommunhandlingar.webbplats.mall import menypost
from kommunhandlingar.webbplats.sammanhang import Kommununderlag
from kommunhandlingar.webbplats.slagen import SLAGEN

MAL = "mal-och-direktiv"
SAMMANTRADEN = "sammantraden"
# Sidorna över tid, med id, rubrik och vad som räknas, i flikarnas och
# kolumnernas ordning.
SIDOR = [(MAL, "Mål och direktiv", "mål")] + [(s.id, s.rubrik, s.antal) for s in SLAGEN]


# Antalet mål eller saker på varje sida över tid för organet; noll när
# sidan inte finns för organet.
def overtid(underlag: Kommununderlag, organ: str) -> dict[str, int]:
    malen = [m for m in underlag.malen if m.organ == organ]
    antal = {MAL: len({m.spar for m in malen})}
    for slag in SLAGEN:
        stegen = underlag.stegen(slag.id)
        antal[slag.id] = len({s.namn for s in stegen if s.organ == organ})
    return antal


# `aktuell` är den visade flikens id. Adresserna är relativa till den
# visade sidan: organets sida eller, ett steg ner, en sida över tid.
def flikar(underlag: Kommununderlag, organ: str, aktuell: str) -> str:
    upp = "" if aktuell == SAMMANTRADEN else adresser.UR_ORGANETS_KATALOG
    antal = overtid(underlag, organ)
    poster = [
        (upp + adresser.organ_i_katalogen(organ), SAMMANTRADEN, "Sammanträden")
    ] + [
        (upp + adresser.over_tid_i_katalogen(organ, sida), sida, rubrik)
        for sida, rubrik, _ in SIDOR
        if antal[sida]
    ]
    lankar = "".join(
        menypost(adress, rubrik, sida == aktuell) for adress, sida, rubrik in poster
    )
    return f'<nav class="flikar" aria-label="Organets sidor"><ul>{lankar}</ul></nav>'
