"""Krav: K18 i docs/02-KRAV.md, ADR-0021 och ADR-0023.
Test: tests/test_webbplats_dokument.py.
"""

from html import escape

from markdown_it import MarkdownIt

from kommunhandlingar import frontmatter
from kommunhandlingar.frontmatter import lista
from kommunhandlingar.sidmarkor import sidorna

# HTML i källan är avslaget, så att inget ur poolen kan bli markup.
LASARE = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
OSAKER = '<pre><code class="language-osaker-tabell">'
OSAKER_MARKERAD = (
    '<p class="markering">Osäker tabell, med uppställningen som på sidan:</p>' + OSAKER
)


def pdfsidor(text: str, falt: dict[str, str]) -> str:
    kvalitet = lista(falt["kvalitet_per_sida"])
    obekraftade = set(lista(falt["tal_obekraftade"]))
    return "".join(
        pdfsida(nr, markdown, markering(kvalitet[int(nr) - 1], nr in obekraftade))
        for nr, markdown in sidorna(frontmatter.brodtext(text)).items()
    )


def markering(kvalitet: str, obekraftad: bool) -> str:
    return f"Kvalitet: {kvalitet}." + (
        " Talen på sidan är obekräftade." if obekraftad else ""
    )


def pdfsida(nr: str, markdown: str, rad: str) -> str:
    return (
        f'<section class="sida"><h2 id="sida-{nr}">Sida {nr}</h2>'
        f'<p class="markering">{escape(rad)}</p>{rendera(markdown)}</section>'
    )


def rendera(markdown: str) -> str:
    return LASARE.render(markdown).replace(OSAKER, OSAKER_MARKERAD)
