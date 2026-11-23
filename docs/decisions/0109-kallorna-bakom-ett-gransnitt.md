---
status: "accepted"
date: 2026-11-23
decision-makers: projektägaren
consulted: AI-agenten
---

# Varje källa upptäcker sitt levande och sitt arkiv bakom samma gränssnitt

## Context and Problem Statement

Läsningen har en adapter per publiceringsplattform (Sitevision, Episerver
och Meetings Plus), men koden runt omkring kände varje adapter vid namn.
`konfiguration.Kommun` hade ett fält per plattform, `kallor`,
`arkivkallor` och `meetingsplus_kallor`, fyllda med tre `isinstance`-filter.
`upptack.py` hade en slinga per adapter och importerade tre adaptermoduler,
`arkivupptackt.py` två till, och webbplatsens luckor och projekt läste
plattformarnas egna fält. En ny plattform krävde ändringar i alla dessa
filer (#370). Hur ska upptäckten nå källorna utan att veta vilken plattform
de är på?

## Decision Drivers

* "Adaptrar per publiceringsplattform, inte per kommun" i `AGENTS.md`: en
  ny plattform ska bara behöva sin adapter och en rad i registret.
* Kandidatlistorna och kommunfilernas format ska vara oförändrade.
* Ingen abstraktion förrän två konkreta fall behöver den; här finns tre.
* Adaptrarnas egna moduler, och deras tester, ska inte behöva skrivas om.

## Considered Options

* Ett omslag per plattform i `adaptrar/kallor.py` kring adapterns källa
* Metoder direkt på varje adapters `Kalla`
* Ett register med funktioner per plattform och upptäcktssteg
* Behåll ett fält per plattform

## Decision Outcome

Valt alternativ: "Ett omslag per plattform i `adaptrar/kallor.py` kring
adapterns källa", eftersom det ger `upptack.py` och `arkivupptackt.py` ett
gränssnitt utan att röra adaptrarna, och utan importcirklar mellan en
adapter och dess arkivläsare.

Gränssnittet, `kallor.Kalla`, har fyra delar:

* `levande(hamta)` ger källans levande fynd med en hämtfunktion, som gör
  ett fel till ett fel med sidans adress, som förut.
* `arkivet(klient)` ger arkivets fynd med läsaren. Arkivläsarna ger ett
  fel som en notering utan adress, så de får klienten som förut och inte
  hämtfunktionen.
* `bakat` säger om källans levande kandidater står nyast först (ADR-0080).
  Upptäckten ordnar källorna framåt först och sedan de bakåt, som förut.
* `projektlistor()` och `organsida(organ)` är det webbplatsen läser:
  projektlistorna (ADR-0068) och sidan som luckorna länkar till (K7).

En källa utan levande sidor eller utan arkiv ger ett tomt fynd. `Kommun`
har ett fält, `kallor`, med alla källor i kommunfilens ordning.
Registret `ADAPTRAR` i `kallor.py` ger adapterns tolkning och omslaget per
namn i kommunfilen.

### Consequences

* Bra, eftersom `upptack.py` och `arkivupptackt.py` inte importerar någon
  adapter, och en påhittad fjärde plattform i testerna går igenom båda
  utan ändring i dem.
* Bra, eftersom webbplatsens luckor och projekt inte längre läser
  Sitevisions eller Meetings Plus egna fält.
* Dåligt, eftersom `kallor.py` känner alla plattformar; det är registret,
  och det enda stället en ny plattform läggs till utöver adaptern.
* Dåligt, eftersom en adapters fält nås genom omslaget, `kalla.kalla`, i
  testerna som ändrar dem.
* Neutralt, eftersom en projektsidas fil nu jämförs med mötessidorna i
  samma Sitevision-källa i stället för alla Sitevision-källors. Ingen
  kommun har mer än en Sitevision-källa, så kandidatlistorna är desamma.
* Neutralt, eftersom de avvisade filerna och arkivets noteringar står i
  kommunfilens källordning i stället för plattformsordningen. Kungsbacka
  har Sitevision före Episerver och regionen bara Meetings Plus, så
  sammanfattningen är densamma.

### Confirmation

`tests/test_kallor.py` (en fjärde adapter, och att upptäckten inte
importerar någon adapter), och `tests/test_upptack.py`,
`test_upptack_meetingsplus.py`, `test_sitevision*.py`,
`test_episerver*.py` och `test_meetingsplus*.py` med samma förväntade
kandidater som förut. Kandidatlistorna för Kungsbackas och regionens
levande källor jämfördes före och efter med samma inspelade svar.

## Pros and Cons of the Options

### Ett omslag per plattform i `adaptrar/kallor.py` kring adapterns källa

* Bra, eftersom adaptrarnas moduler och dataklasser är som förut.
* Bra, eftersom ordningen och hämtningen blir källans egenskaper.
* Dåligt, eftersom det blir en modul till, och ett lager mellan
  kommunfilen och adaptern.

### Metoder direkt på varje adapters `Kalla`

* Bra, eftersom inget omslag behövs.
* Dåligt, eftersom `sitevision.py` då måste importera `sitevision_arkiv.py`
  och `episerver.py` `episerver_arkiv.py`, som redan importerar dem: en
  importcirkel.

### Ett register med funktioner per plattform och upptäcktssteg

* Bra, eftersom källorna kan vara adaptrarnas dataklasser som förut.
* Dåligt, eftersom upptäckten måste slå upp plattformen för varje källa,
  och plattformens namn då måste följa med källan.

### Behåll ett fält per plattform

* Bra, eftersom inget ändras.
* Dåligt, eftersom en ny plattform fortsätter att kräva ändringar i
  konfigurationen, upptäckten och webbplatsen.

## More Information

Issue #370 föreslog att varje källa får samma två ingångar med en
hämtfunktion. AI-agenten rekommenderade omslag i stället för metoder på
adaptrarnas dataklasser, eftersom metoderna ger importcirklar, och att
arkivet får läsaren i stället för hämtfunktionen, så att arkivets
noteringar inte ändras. Webbplatsens två läsningar togs med i gränssnittet
eftersom `Kommun` inte längre har ett fält per plattform. Projektägaren
gav uppdraget att arbeta igenom #347 och godkände där på förhand att
agentens rekommendationer följs och att PR:erna mergas vid grön CI.
