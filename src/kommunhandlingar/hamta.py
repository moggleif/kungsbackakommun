"""Krav: K4–K6, K8, K9, K11, K13, K16, K52, K53 och K79 i docs/02-KRAV.md,
ADR-0004, ADR-0018, ADR-0019, ADR-0075, ADR-0077 och ADR-0088. Test:
tests/test_hamta.py, tests/test_hamta_kommando.py, tests/test_omkonvertering.py,
tests/test_tidsbudget.py och tests/test_versionslogg.py.

Steg 2: `python -m kommunhandlingar.hamta <kommunfil> <arbetskatalog>
[--arkiv] [--start N] [--del MINUTER] [--utan-omkonvertering]`. Läser
kandidatlistan från steg 1, med `--arkiv` arkivets, och tar kandidaterna i
dess ordning, ett dokument i taget, in i `data/` i samma repo som
kommunfilen; de som bara ska konverteras om tas sist. Med `--start` gäller
tidsbudgeten i K11, räknad från jobbets start. Med `--del` slutar steg 2
efter så många minuter, så att körningen kan spara det klara, och avslutar
med kod 4 när kandidater väntar inom budgeten; en kandidat som redan
provats i körningen tas inte om i nästa del (K11, ADR-0088). Utan
`--arkiv` får `versioner/<kommun>.csv` en rad för varje dokument som kom in
nytt, med en ny adress eller med en ny sha256, också när steg 2 stoppas av
ett fel. Med `--utan-omkonvertering` tas bara det nya och ändrade, så att
mötessidorna inte väntar på omkonverteringen.
"""

import argparse
import sys
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from kommunhandlingar import (
    konfiguration,
    omkonvertering,
    pool,
    provade,
    tidsbudget,
    versionslogg,
)
from kommunhandlingar.arkivluckor import ensamma
from kommunhandlingar.behandla import Steg2, bara_omkonvertering, behandla
from kommunhandlingar.fel import Konfigurationsfel
from kommunhandlingar.hamtning import installningar
from kommunhandlingar.hamtning.klient import Klient
from kommunhandlingar.kandidat import Kandidat, lista
from kommunhandlingar.kandidat import las as las_kandidater
from kommunhandlingar.konvertering import rapid, tesseract
from kommunhandlingar.tidsbudget import Tidsgrans
from kommunhandlingar.utfall import AT_SIDAN, VANTAR, Korning, Utfall

MER_I_NASTA_DEL = 4


def nu() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def ordna(steg: Steg2, kandidater: list[Kandidat]) -> list[Kandidat]:
    return sorted(kandidater, key=lambda k: bara_omkonvertering(steg, k))


def kor(steg: Steg2, kandidater: list[Kandidat], mjuk: datetime) -> Korning:
    korning = Korning()
    for nr, kandidat in enumerate(kandidater):
        utfall = prova(steg, kandidat, mjuk)
        korning.notera(utfall, kandidat.url)
        if utfall in (VANTAR, AT_SIDAN):
            korning.utfall[VANTAR.text] += len(kandidater) - nr - 1
            break
        korning.provade.append(kandidat)
    return korning


def prova(steg: Steg2, kandidat: Kandidat, mjuk: datetime) -> Utfall:
    """VANTAR när delens tid gått ut före kandidaten, AT_SIDAN vid den hårda gränsen."""
    try:
        if steg.tid() >= mjuk:
            return VANTAR
        return behandla(steg, kandidat)
    except Tidsgrans:
        return AT_SIDAN


def steg2(  # noqa: PLR0913  # undantag: testerna väljer loggfilen, None för arkivet
    steg: Steg2, kandidater: list[Kandidat], mjuk: datetime, logg: Path | None
) -> Korning:
    """Kandidaterna kommer ordnade. Loggen skrivs också när steg 2 stoppas."""
    fore = versionslogg.versioner(steg.pool)
    try:
        return kor(steg, kandidater, mjuk)
    finally:
        tidsbudget.stoppa()
        if logg:
            versionslogg.skriv(logg, versionslogg.nya(fore, steg.pool, steg.tid()))


def bygg_steg(arg: argparse.Namespace, kommun, kandidater: list[Kandidat]) -> Steg2:
    rot = arg.kommunfil.resolve().parent.parent
    return Steg2(
        data=rot / "data",
        kommun=kommun.id,
        pool=pool.las(rot / "data", kommun.id),
        klient=Klient(installningar.las(rot / "hamtning.toml")),
        nycklar=frozenset(k.kallnyckel for k in kandidater),
        tid=nu,
        version=f"kommunhandlingar {version('kommunhandlingar')}",
        andringar=omkonvertering.las(),
        arkiv=arg.arkiv,
        omkonvertera=kommun.omkonvertera and not arg.utan_omkonvertering,
        ensamma=ensamma(kandidater),
    )


def forbered(arg: argparse.Namespace) -> tuple[Steg2, list[Kandidat], Path | None]:
    """Steget, kandidaterna att prova i sin ordning och filen med de provade."""
    kommun = konfiguration.las(arg.kommunfil)
    kandidatlista = lista(arg.arbetskatalog, kommun.id, arg.arkiv)
    kandidater = las_kandidater(kandidatlista)
    steg = bygg_steg(arg, kommun, kandidater)
    provfil = provade.fil(kandidatlista) if arg.del_ else None
    return steg, ordna(steg, provade.kvar(kandidater, provfil)), provfil


def main(arg: argparse.Namespace) -> int:
    tesseract.kontrollera()
    rapid.kontrollera()
    steg, att_prova, provfil = forbered(arg)
    mjuk = tidsbudget.delens_grans(arg.start, arg.del_, nu())
    if arg.start:
        tidsbudget.starta_hard_grans(arg.start, nu())
    logg = None if steg.arkiv else steg.data.parent / "versioner" / f"{steg.kommun}.csv"
    korning = steg2(steg, att_prova, mjuk, logg)
    provade.skriv(provfil, korning.provade)
    for text, antal in sorted(korning.utfall.items()):
        print(f"{antal} {text}")
    return slutkod(korning.utfall, arg.start, mjuk)


def slutkod(utfall: Counter, start: datetime | None, mjuk: datetime) -> int:
    """Kod 4 när delen tog slut före budgeten och kandidater väntar (ADR-0088).
    Skriptet som kör delarna, .github/nattkorning/hamta_i_delar.sh, läser den."""
    delen_tog_slut = mjuk < tidsbudget.mjuk_grans(start)
    return MER_I_NASTA_DEL if utfall[VANTAR.text] and delen_tog_slut else 0


def argument() -> argparse.Namespace:
    tolk = argparse.ArgumentParser(prog="python -m kommunhandlingar.hamta")
    tolk.add_argument("kommunfil", type=Path)
    tolk.add_argument("arbetskatalog", type=Path)
    tolk.add_argument("--arkiv", action="store_true", help="arkivets lista (K16)")
    tolk.add_argument("--start", type=tidsbudget.tidpunkt, help=tidsbudget.START)
    tolk.add_argument("--del", dest="del_", type=int, help="minuter per del (ADR-0088)")
    tolk.add_argument(
        "--utan-omkonvertering", action="store_true", help="bara nytt och ändrat (K53)"
    )
    return tolk.parse_args()


if __name__ == "__main__":
    try:
        sys.exit(main(argument()))
    except Konfigurationsfel as fel:
        sys.exit(f"Stoppad: {fel}")
