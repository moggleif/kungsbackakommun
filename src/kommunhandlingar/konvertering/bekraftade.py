"""Krav: K85 i docs/02-KRAV.md, ADR-0105 och ADR-0106. Test:
tests/test_bekraftade.py.

En skannad sida får bekräftade tal när väg H bekräftar varje rad med tal
och inget tal i Tesseracts läsning står utanför raderna (`radlasning`).
Den lagrade texten är Tesseracts, utom på en rad som RapidOCR och den
tredje läsningen bekräftat (`tredje-och-rapid`): där ersätts Tesseracts
ord på raden med RapidOCR:s text. Orden måste stå i följd på en och
samma rad i Tesseracts text, och Tesseracts text måste vara dess ord rad
för rad; annars går raden inte att placera och sidans tal är
obekräftade. Sist jämförs talen i den färdiga texten med de bekräftade.
Är de inte samma tal, lika många gånger, är sidans tal obekräftade.
"""

from collections import Counter
from itertools import groupby

from PIL import Image

from kommunhandlingar.konvertering import ocr, radlasning, vag_h


def text(bild: Image.Image, tsv: str, txt: str) -> str | None:
    """Sidans text med väg H:s tal, eller None när ett tal inte är bekräftat."""
    lasning = radlasning.las(bild, tsv)
    if lasning.tal_utanfor or any(r.avgorande.tal is None for r in lasning.rader):
        return None
    ersatt = ersattningar(lasning.rader)
    ny = None if ersatt is None else med_ersattningar(txt, tsv, ersatt)
    if ny is None:
        return None
    ny = ocr.rensa(ny.strip())
    bekraftade = Counter(t for r in lasning.rader for t in r.avgorande.tal)
    return ny if Counter(vag_h.tal(ny)) == bekraftade else None


def ersattningar(rader: list[radlasning.Rad]) -> dict[int, str] | None:
    """Ordets nummer i Tesseracts läsning och texten som ersätter det;
    None när en rad inte går att placera."""
    ersatt: dict[int, str] = {}
    for rad in rader:
        if rad.avgorande.hur != "tredje-och-rapid":
            continue
        nr = [o.nr for o in rad.ord]
        i_folj = nr == list(range(nr[0], nr[0] + len(nr))) if nr else False
        if not i_folj or len({o.linje for o in rad.ord}) != 1:
            return None
        ersatt |= dict.fromkeys(nr, "") | {nr[0]: rad.rapid}
    return ersatt


def med_ersattningar(txt: str, tsv: str, ersatt: dict[int, str]) -> str | None:
    linjer = [list(o) for _, o in groupby(radlasning.tesseracts_ord(tsv), linje)]
    rader = txt.split("\n")
    med_text = [i for i, r in enumerate(rader) if r.strip()]
    if len(med_text) != len(linjer):
        return None
    for i, ord_ in zip(med_text, linjer, strict=True):
        if rader[i] != " ".join(o.text for o in ord_):
            return None
        rader[i] = " ".join(t for o in ord_ if (t := ersatt.get(o.nr, o.text)))
    return "\n".join(rader)


def linje(o: radlasning.Ord) -> tuple[str, str, str]:
    return o.linje
