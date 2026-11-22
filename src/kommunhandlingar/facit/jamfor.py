"""Krav: K20 i docs/02-KRAV.md, ADR-0025. Test: tests/test_facit.py.

Jämför en konvertering med sitt facit och räknar måtten i
docs/03-ARKITEKTUR.md#facit-för-konverteringen: matchningen av raderna,
bedömningen av varje facittabell och talen.
"""

from kommunhandlingar.facit import tal
from kommunhandlingar.facit.bedomning import status
from kommunhandlingar.facit.lasa import Facit
from kommunhandlingar.facit.matchning import granska
from kommunhandlingar.facit.utfall import Utfall
from kommunhandlingar.konvertering import kvalitet
from kommunhandlingar.konvertering.dokument import Resultat
from kommunhandlingar.konvertering.flersidiga import tabeller


def jamfor(facit: Facit, resultat: Resultat) -> Utfall:
    utfall = Utfall()
    for t in tabeller(resultat.sidor):
        granska(t, facit.tabeller, utfall)
    markerade = markerade_sidor(resultat)
    for f in facit.tabeller:
        matt, varfor = status(f, utfall, markerade)
        utfall.rakna(matt, [f"tabell {f.namn}{varfor}"])
    saknas, tillkommer = tal.avvikelser(facit, resultat)
    saknade = [f"saknas {t}" for t in saknas.elements()]
    utfall.rakna("tal_avviker", saknade + [f"ny {t}" for t in tillkommer.elements()])
    omarkta = [nr for nr in facit.skannade if nr not in resultat.tal_obekraftade]
    utfall.rakna("omarkta", [f"skannad sida {nr}" for nr in omarkta])
    return utfall


def markerade_sidor(resultat: Resultat) -> set[int]:
    sidor = enumerate(resultat.kvalitet_per_sida, 1)
    return {nr for nr, k in sidor if k != kvalitet.OK} | set(resultat.tal_obekraftade)
