"""Krav: K14, K18, K22, K26, K27, K28, K36, K37, K39 och K51 i docs/02-KRAV.md,
ADR-0074 och ADR-0083 för temat. Test: tests/test_webbplats.py och
tests/test_tema.py.

Stilen står i `mall.css`. Varje färg har ett ljust och ett mörkt värde
(ADR-0074); en webbläsare utan light-dark() får de ljusa värdena. Knappen och
det valda temat kommer från Giffås gemensamma meny (ADR-0083).
"""

from dataclasses import dataclass
from datetime import datetime
from html import escape

from kommunhandlingar.konfiguration import Kommun
from kommunhandlingar.webbplats.inbaddning import stil
from kommunhandlingar.webbplats.meny import GEMENSAM, meny, sajtnamn

# Dokumentationen bor med koden, också när poolen ligger i ett eget datarepo,
# som regionens (K14).
KALLKOD = "https://github.com/moggleif/kungsbackakommun"


@dataclass(frozen=True)
class Mall:
    kommuner: list[Kommun]
    repo: str
    byggd: datetime
    # Kommunerna med en kalender, som menyn länkar till.
    kalendrar: frozenset[str] = frozenset()

    @property
    def en_kommun(self) -> bool:
        return len(self.kommuner) == 1


def sida(mall: Mall, adress: str, rubrik: str, innehall: str) -> str:  # noqa: PLR0913  # undantag: HTML-mallen blir inte tydligare av att delas, och varje sida ger sin adress, rubrik och sitt innehåll
    namn = sajtnamn(mall.kommuner)
    titel = namn if rubrik == namn else f"{rubrik} – {namn}"
    return f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titel)}</title>
{GEMENSAM}
{stil("mall.css")}
</head>
<body>
{meny(mall.kommuner, mall.kalendrar, adress)}
<main>
<h1>{escape(rubrik)}</h1>
{innehall}
</main>
{sidfot(mall)}
</body>
</html>
"""


def menypost(adress: str, namn: str, aktuell: bool) -> str:
    markering = ' aria-current="page"' if aktuell else ""
    return f'<li><a href="{adress}"{markering}>{escape(namn)}</a></li>'


def stig(lankar: list[tuple[str, str]]) -> str:
    poster = " › ".join(
        f'<a href="{escape(adress)}">{escape(namn)}</a>' for adress, namn in lankar
    )
    return f'<nav aria-label="Här är du"><p>{poster}</p></nav>'


def lank(adress: str, text: str) -> str:
    if not adress.startswith(("https://", "http://")):
        return escape(text)
    return f'<a href="{escape(adress)}">{escape(text)}</a>'


def sidfot(mall: Mall) -> str:
    repo, kod = escape(mall.repo), escape(KALLKOD)
    tid = mall.byggd.strftime("%Y-%m-%d %H:%M UTC")
    lankar = (
        f'Källkod och data: <a href="{repo}">{repo}</a>'
        if mall.repo == KALLKOD
        else f'Data: <a href="{repo}">{repo}</a>. Källkod: <a href="{kod}">{kod}</a>'
    )
    return f"<footer><p>{lankar}. Sidan byggdes {tid}.</p></footer>"
