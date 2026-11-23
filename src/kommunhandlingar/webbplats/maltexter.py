"""Krav: K26, K27, K28, K29, K35, K50 och K60 i docs/02-KRAV.md, ADR-0044,
ADR-0045, ADR-0046, ADR-0050, ADR-0051, ADR-0056, ADR-0073 och ADR-0086.
Test: tests/test_webbplatsbild.py, tests/test_fokusomraden.py och
tests/test_malar.py.

Löptexterna på sidan om ett organs mål och direktiv: inledningen, metoden,
åren och fokusområdena i Om sidan, förklaringen under tabellen över antal
per år och väljaren av perspektiv.
"""

INLEDNING = (
    "<p>Organets egna mål och direktiv år för år, ur budgetarna, "
    "delårsrapporterna och årsredovisningarna i poolen. Välj ett mål i "
    "tidslinjen för att se hela dess historik.</p>"
)
METOD = (
    "<p>Målen är lästa ur poolens dokument och skrivna ordagrant, med "
    "dokumentet och sidan som källa. Bygget prövar att texten står på den "
    "sidan. Bara det organet självt beslutat står med, så en nämnds sida "
    "har inte kommunfullmäktiges mål eller direktiv. Säger protokollet något "
    "annat än handlingarna till samma möte, gäller protokollet.</p>"
    "<p>Ett mål som bytt rubrik har en rad per rubrik i tidslinjen, i den "
    "ordning de först står, och ett kort med de tidigare rubrikerna under "
    "den senaste. Ett år då samma rubrik får en ny formulering är markerat. "
    "Där källan inte själv säger att det är samma mål, och formuleringen "
    "inte är densamma, är kopplingen en bedömning och rubriken märkt "
    "tolkad.</p>"
    "<p>Statusen är en ikon för uppföljningens bedömning, med källans egen "
    "formulering i pekrutan och i kortets historik. En delårsrapport ger en "
    "prognos, som har en streckad ram. Ett år utan dokument i poolen är en "
    "lucka i poolen, inte ett år utan mål, också före organets första "
    "dokument i poolen.</p>"
)
# Delas med spårsidorna (K60, ADR-0086).
AREN = (
    "<p>Åren är desamma på alla kommunens sidor över tid, så att de går att "
    "jämföra: från poolens första år, eller ett äldre år som någon rad "
    "har, till i år, eller ett senare år som någon rad har, som en budget "
    "för nästa år. Ett år utan rader står tomt.</p>"
)
FOKUS = (
    "<p>Ett mål med fokusområden har dem under sig i tidslinjen och i sitt "
    "kort. En uppföljning kan bedöma med färg i stället för ord. Färgen "
    "följer inte med in i texten, så den är avläst ur PDF:en på källans "
    "sida, visas som ikonen för uppnått, delvis eller ej och är märkt "
    "som avläst ur färgen. Hur källan använder färgerna står i "
    "beskrivningen av kommunens källor. En rad har en status bara där "
    "källans bedömning står i texten. Budgeten och uppföljningen kan "
    "skriva ett fokusområde på olika sätt samma år, och då har det en rad "
    "för varje.</p>"
)

ANTALET = (
    "<p>Varje mål räknas en gång per år, också när det har två rubriker. "
    "Uppföljningarna är de delårsrapporter, årsredovisningar och andra "
    "rapporter som målen är lästa ur; en uppföljning som inte gått att "
    "hämta till poolen räknas inte. Ett år utan mål står som –, eftersom "
    "dokumenten kan saknas i poolen. Uppföljningar i protokollen och "
    "dragningar om målen är paragraferna i mötets protokoll där organet "
    "godkänner eller tar emot en uppföljning, som årsredovisningen, "
    "delårsrapporten eller uppföljningen per april, eller noterar en "
    "dragning om målen, och räknas på mötets år. Ett år utan protokoll i "
    "poolen står som –, och protokoll kan saknas också andra år.</p>"
)

# Väljaren visas av skriptet, som visar ett perspektiv i taget (ADR-0073).
PERSPEKTIV = (
    '<div class="perspektiv" role="group" aria-label="Perspektiv" hidden>'
    '<button type="button" data-vy="tidslinje">Tidslinje</button>'
    '<button type="button" data-vy="ar">Ett år i taget</button>'
    '<button type="button" data-vy="kort">Målkort</button></div>'
)
