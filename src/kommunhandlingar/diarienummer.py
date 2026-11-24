"""Krav: K48 och K54 i docs/02-KRAV.md, ADR-0071 och ADR-0110.
Test: tests/test_paragrafer.py.

Diarienumret skrivs som det står. Bara tankstreck och
mellanslag kring bindestrecket eller mellan förled och år blir ett
bindestreck, så att `BN 2024-000123`, `BN 2016–000170` och `MH-2021- 3122`
skrivs `BN-2024-000123`, `BN-2016-000170` och `MH-2021-3122`. Efter
etiketten läses också ett förled som står två gånger, `VO VO-2026-00191`,
och mellanslag kring förledets bindestreck, `VO- 2026-00017` och
`KS -2025-00357` (#289). Tolkningen används för protokollens paragrafer och
för handlingarnas tjänsteskrivelser.
"""

import re

FORLED = r"[A-ZÅÄÖ]{1,5}(?: ?[–-] ?|[ /])?"
NUMMER = rf"(?:{FORLED})?\d[\dA-Z]*(?:(?: ?[–-] ?|/|:)[A-Z]?\d[\dA-Z]*)*"
DUBBLERAT = r"(?:(?P<forled>[A-ZÅÄÖ]{1,5}) (?=(?P=forled)(?: ?[–-] ?| )?\d))?"
MED_ETIKETT = re.compile(
    rf"\b(?i:Dnr|Diarienr|Diarienummer)\.?:?\s*{DUBBLERAT}(?P<nummer>{NUMMER})"
)
UTAN_ETIKETT = re.compile(r"[A-ZÅÄÖ]{1,5}[ /–-]?\d{2,4}[–/:-]\d+(?:/\d+)?")


def i_huvudet(text: str, ensam: bool = False) -> list[str]:
    """Numren efter `Dnr`; med `ensam` också ett nummer som står ensamt."""
    if ensam and UTAN_ETIKETT.fullmatch(text.strip()):
        return [normaliserat(text.strip())]
    return efter_etikett(text)


def efter_etikett(text: str) -> list[str]:
    return [normaliserat(m["nummer"]) for m in MED_ETIKETT.finditer(text)]


def normaliserat(nummer: str) -> str:
    nummer = re.sub(r" ?[–-] ?", "-", nummer)
    return re.sub(r"^([A-ZÅÄÖ]+) (?=\d)", r"\1-", nummer)
