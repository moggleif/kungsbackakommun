"""Krav: K84 och K85 i docs/02-KRAV.md, ADR-0105 och ADR-0106. Test:
tests/test_radlasning.py.

RapidOCR i väg H, med sina förvalda modeller ur PP-OCRv6 för att hitta och
läsa raderna, och den latinska modellen ur PP-OCRv5 som tredje läsning av
en rad. Modellerna körs i onnxruntime. Versionerna låses i pyproject.toml,
och RapidOCR kontrollerar modellfilernas sha256 när de hämtas. Den
latinska modellen följer inte med paketet utan hämtas första gången; går
den inte att hämta stoppas körningen innan något dokument läses
(`kontrollera`), så att ingen sida blir `ej-konverterad` för att miljön
saknar den (K85).
"""

from functools import cache
from importlib.metadata import version

from PIL import Image
from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR
from rapidocr.utils.download_file import DownloadFileException

from kommunhandlingar.fel import Konfigurationsfel

TYST = {"Global.log_level": "critical"}
LATIN = {
    "Rec.lang_type": LangRec.LATIN,
    "Rec.ocr_version": OCRVersion.PPOCRV5,
    "Rec.model_type": ModelType.MOBILE,
}

Ruta = tuple[float, float, float, float]


@cache
def sidmotor() -> RapidOCR:
    return RapidOCR(params=TYST)


@cache
def radmotor() -> RapidOCR:
    return RapidOCR(params=TYST | LATIN)


def kontrollera() -> None:
    try:
        sidmotor(), radmotor()
    except DownloadFileException as fel:
        raise Konfigurationsfel(f"RapidOCR saknar en modell (K85): {fel}") from fel


def rader(bild: Image.Image) -> list[tuple[Ruta, str]]:
    """Raderna på sidan, med rutan i bildens pixlar och RapidOCR:s text."""
    svar = sidmotor()(bild)
    if svar.boxes is None:
        return []
    par = zip(svar.boxes, svar.txts, strict=True)
    return [(ruta(hornen), text) for hornen, text in par]


def ruta(hornen) -> Ruta:
    xs, ys = [p[0] for p in hornen], [p[1] for p in hornen]
    return float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))


def las_rad(bild: Image.Image) -> str:
    """Den latinska modellens läsning av en bild med en rad."""
    svar = radmotor()(bild, use_det=False, use_cls=False)
    return svar.txts[0] if svar.txts else ""


def verktyg() -> list[str]:
    """RapidOCR och onnxruntime, med version, för `pipeline`."""
    return [f"{namn} {version(namn)}" for namn in ("rapidocr", "onnxruntime")]
