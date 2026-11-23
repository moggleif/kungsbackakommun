"""Krav: K4, K6, K16, K23, K30, K34, K52 och K86 i docs/02-KRAV.md, ADR-0003,
ADR-0018, ADR-0039, ADR-0048, ADR-0055, ADR-0075, ADR-0076 och ADR-0107. Test i
tests/: test_hamta.py, test_hamta_arkiv.py, test_omkonvertering.py,
test_plattformar.py, test_granskning.py och test_tidsbudget.py.

Steg 2 för en kandidat: hoppa över det som redan finns, annars hämta, konvertera
och skriv. Ett misslyckat försök skriver aldrig över en fullständig `.md`. En
kandidat ur ett arkiv fyller bara luckor, så att en äldre kopia aldrig ersätter
ett dokument i poolen; har sammanträdet typen från en annan plattform står den
med högst kvalitet kvar. Med omkonverteringen påslagen räknas ett dokument som
en senare version av poolen kan ändra, också i arkivet, inte som befintligt,
utom när det är granskat för hand (`omkonvertering.py`). Var kandidaten hamnar står i
`placering.py`, fälten och skrivningen i `poolskrivning.py` och utfallen i
`utfall.py`.
"""

import tempfile
from dataclasses import replace
from pathlib import Path

from kommunhandlingar import frontmatter, omkonvertering, original, tidsbudget, utfall
from kommunhandlingar.arkivluckor import forlorar, hel, ingen_lucka, levande
from kommunhandlingar.fel import Hamtfel
from kommunhandlingar.kandidat import Kandidat
from kommunhandlingar.konvertering import kvalitet
from kommunhandlingar.konvertering.dokument import Resultat, konvertera, kvalitetsfalt
from kommunhandlingar.placering import motstandare_for, valj_plats
from kommunhandlingar.poolskrivning import (
    Dokument,
    Steg2,
    behall,
    filfalt,
    ny_adress,
    skriv,
)
from kommunhandlingar.utfall import Utfall


def behandla(steg: Steg2, kandidat: Kandidat) -> Utfall:
    if kandidat.kallnyckel in steg.pool.tidigare:
        return utfall.TIDIGARE
    sokvag = steg.pool.efter_nyckel.get(kandidat.kallnyckel)
    rival = motstandare_for(steg, kandidat) if sokvag is None else None
    dokument = valj_plats(steg, kandidat, sokvag or rival)
    gammal = dokument.befintlig
    luckor = steg.arkiv and not rival and not bara_omkonvertering(steg, kandidat)
    if luckor and ingen_lucka(steg.pool, steg.kommun, dokument):
        return utfall.LUCKOR
    if sokvag and samma_kalla(gammal, kandidat) and aktuell(steg, gammal):
        return utfall.OFORANDRAD
    return hamta(steg, dokument)


def samma_kalla(falt: dict[str, str], kandidat: Kandidat) -> bool:
    return falt["kalla_url"] == frontmatter.varde_av(kandidat.kalla_url()) and hel(falt)


def aktuell(steg: Steg2, falt: dict[str, str]) -> bool:
    if not steg.omkonvertera or frontmatter.granskad(falt):
        return True
    return not omkonvertering.berors(steg.andringar, falt, steg.version)  # K86


def bara_omkonvertering(steg: Steg2, kandidat: Kandidat) -> bool:
    sokvag = steg.pool.efter_nyckel.get(kandidat.kallnyckel)
    gammal = steg.pool.efter_sokvag[sokvag] if sokvag else None
    return bool(gammal) and samma_kalla(gammal, kandidat) and not aktuell(steg, gammal)


def hamta(steg: Steg2, dokument: Dokument) -> Utfall:
    with tempfile.TemporaryDirectory() as katalog:
        pdf = Path(katalog) / "original.pdf"
        dokument = replace(dokument, hamtad=steg.tid())
        adresser = dokument.kandidat.adresser()
        hamtsatt = original.Hamtsatt(steg.klient, steg.arkiv)
        try:
            hamtat = original.hamta(hamtsatt, adresser, pdf)
        except Hamtfel as fel:
            return misslyckad(steg, dokument, fel.orsak)
        return hamtad_fil(steg, dokument, hamtat)


def misslyckad(steg: Steg2, dokument: Dokument, orsak: str) -> Utfall:
    if orort := orort_vid_hamtfel(steg, dokument, orsak):
        return orort
    gammal = dokument.befintlig
    hamtad = gammal["hamtad"] if gammal else dokument.hamtad.isoformat()
    falt = {"hamtad": hamtad, "pipeline": steg.version, "fel": orsak}
    skriv(steg, dokument, falt | {"kvalitet": kvalitet.EJ_HAMTAD})
    return utfall.ej_hamtad(orsak)


def orort_vid_hamtfel(steg: Steg2, dokument: Dokument, orsak: str) -> Utfall | None:
    gammal = dokument.befintlig
    if gammal and hel(gammal):
        return utfall.ej_hamtad(orsak, utfall.ORORD)
    adress = frontmatter.varde_av(dokument.kandidat.kalla_url())
    if gammal and (gammal["fel"], gammal["kalla_url"]) == (orsak, adress):
        return utfall.ej_hamtad(orsak, "oförändrad")
    if steg.arkiv and gammal and levande(gammal):
        # Annars skriver den levande källan och arkivet om filen varannan gång.
        return utfall.ej_hamtad(orsak, "den levande källans försök orört")
    return None


def hamtad_fil(steg: Steg2, dokument: Dokument, hamtat: original.Original) -> Utfall:
    gammal = dokument.befintlig
    samma_fil = samma_original(gammal, dokument.kandidat, hamtat.sha256)
    if samma_fil and aktuell(steg, gammal):
        return ny_adress(steg, dokument)
    resultat = konverterat(hamtat)
    if resultat.fel == tidsbudget.FEL and samma_fil and har_text(gammal):
        return utfall.ej_konverterad(tidsbudget.FEL, utfall.ORORD)
    if steg.arkiv and forlorar(gammal, dokument.kandidat, resultat.kvalitet):
        return behall(steg, dokument)
    falt = kvalitetsfalt(steg.version, resultat) | filfalt(dokument, hamtat)
    falt["konverterad"] = steg.tid().isoformat()
    skriv(steg, replace(dokument, sidor=resultat.sidor), falt)
    return konverteringens_utfall(resultat, samma_fil)


def konverterat(hamtat: original.Original) -> Resultat:
    if hamtat.fel:
        return Resultat(kvalitet.EJ_KONVERTERAD, hamtat.fel)
    return konvertera(hamtat.pdf)


def konverteringens_utfall(resultat: Resultat, samma_fil: bool) -> Utfall:
    if resultat.fel == tidsbudget.FEL:
        return utfall.ej_konverterad(tidsbudget.FEL)
    return utfall.KONVERTERAD_OM if samma_fil else utfall.KONVERTERAD


def har_text(falt: dict[str, str]) -> bool:
    return falt["kvalitet"] not in kvalitet.UTAN_TEXT


def samma_original(gammal: dict | None, kandidat: Kandidat, sha256) -> bool:
    """Ett granskat dokument behåller sin text också under en ny källnyckel."""
    if gammal is None or gammal["sha256"] != frontmatter.varde_av(sha256):
        return False
    return gammal["kallnyckel"] == kandidat.kallnyckel or frontmatter.granskad(gammal)
