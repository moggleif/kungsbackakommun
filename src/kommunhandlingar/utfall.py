"""Krav: K8, K9 och K11 i docs/02-KRAV.md. Test i tests/: test_hamta.py,
test_hamta_arkiv.py, test_tidsbudget.py och test_hamta_kommando.py.

Vad steg 2 gjorde med en kandidat. Texten räknas i sammanfattningen, och ett
utfall som ska loggas skrivs också ut med kandidatens adress.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Utfall:
    text: str
    loggas: bool = False


TIDIGARE = Utfall("tidigare källnyckel")
LUCKOR = Utfall("finns redan; arkivet fyller bara luckor")
OFORANDRAD = Utfall("oförändrad")
NY_ADRESS = Utfall("ny adress, samma innehåll")
BEHALLS = Utfall("lika eller lägre kvalitet; det befintliga behålls")
KONVERTERAD = Utfall("konverterad")
KONVERTERAD_OM = Utfall("konverterad om")
VANTAR = Utfall("väntar på nästa körning")
AT_SIDAN = Utfall("lagd åt sidan vid tidsgränsen", loggas=True)

ORORD = "fullständig .md orörd"


def ej_hamtad(orsak: str, *foljd: str) -> Utfall:
    return Utfall(", ".join([f"ej hämtad ({orsak})", *foljd]), loggas=True)


def ej_konverterad(orsak: str, *foljd: str) -> Utfall:
    return Utfall(", ".join([f"ej konverterad ({orsak})", *foljd]), loggas=True)
