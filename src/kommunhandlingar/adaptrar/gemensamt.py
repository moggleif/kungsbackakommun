"""Krav: K2, K45 och K57 i docs/02-KRAV.md. Test: tests/test_gemensamt.py.

Det som fler plattformars adaptrar behöver: sidans länkar och kommunfilens
tabell organ → sida.
"""

from html.parser import HTMLParser
from urllib.parse import urljoin

from kommunhandlingar.fel import Konfigurationsfel


class Lankar(HTMLParser):
    """Varje `<a>` med adress i sidans ordning, och de som stängs med sin text.
    En ny `<a>` utan `</a>` emellan lämnar den förra utan text."""

    def __init__(self):
        super().__init__()
        self.adresser: list[str] = []
        self.lankar: list[tuple[str, str]] = []
        self.adress: str | None = None
        self.text = ""

    def handle_starttag(self, tagg, attribut):
        if tagg == "a":
            self.adress, self.text = dict(attribut).get("href"), ""
            if self.adress:
                self.adresser.append(self.adress)

    def handle_endtag(self, tagg):
        if tagg == "a" and self.adress is not None:
            self.lankar.append((self.adress, " ".join(self.text.split())))
            self.adress = None

    def handle_data(self, data):
        if self.adress is not None:
            self.text += data


def tolkad(html: str) -> Lankar:
    tolk = Lankar()
    tolk.feed(html)
    tolk.close()
    return tolk


def lankar(html: str, sidadress: str) -> list[tuple[str, str]]:
    """Länkarna med sin text och hela adressen, som filen öppnas med."""
    return [(urljoin(sidadress, a), t) for a, t in tolkad(html).lankar]


def adresser(html: str, sidadress: str) -> list[str]:
    """Sidorna som länkas, utan ankare: ett avsnitt på en sida är samma sida."""
    return [urljoin(sidadress, a).split("#")[0] for a in tolkad(html).adresser]


def organsidor(tabell: dict, organ_id: list[str], var: str) -> dict[str, str]:
    for organ, adress in tabell.items():
        if organ not in organ_id or not isinstance(adress, str):
            raise Konfigurationsfel(f"{var}: sidan för {organ!r}")
    return tabell
