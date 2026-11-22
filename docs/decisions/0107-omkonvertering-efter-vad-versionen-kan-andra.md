---
status: accepted
date: 2026-11-22
decision-makers: projektägaren
consulted: AI-agenten
---

# Varje version säger vad den kan ändra, och bara de dokument den berör konverteras om

## Context and Problem Statement

Med `omkonvertera = true` hämtas och konverteras ett dokument om när
versionen i dess `pipeline` skiljer sig från poolens (ADR-0019). Sedan
0.13.0 hoppas dokument som är `full` över (ADR-0099, alternativ A), och
granskade dokument har alltid hoppats över (ADR-0055). Två fel följer:

* Allt annat konverteras om vid varje ny version, också när versionen
  inte kan ändra dokumentet. 0.16.0 ändrar bara sidor som läses med OCR,
  men 1 692 dokument stod på tur, bland dem några hundra utan en enda
  skannad sida. Det kostar körtid, el och anrop till källan utan att
  något kan bli bättre.
* Ett dokument som är `full` konverteras aldrig om, också när det läses
  av en version som saknar en senare rättning. 1 451 dokument ur
  webbarkivet är `full` men lästa av 0.8.7–0.11.0, före 0.12.0:s rättning
  av Word-tabeller där två kolumner slogs ihop medan sidan ändå märktes
  `ok` (ADR-0087). De kan ha fel tal under märkningen `full`.

Hur avgörs vilka dokument en ny version kan ändra, när PDF:en inte finns
kvar (ADR-0001) och bara front matter och texten är lagrade
([#450](https://github.com/moggleif/kungsbackakommun/issues/450))?

## Decision Drivers

* **Talen ska vara rätt eller märkta.** En regel som lämnar ett dokument
  som en version kan ändra är sämre än en som konverterar om ett för
  mycket.
* **Ingen omkonvertering som inte kan göra något bättre.** Varje
  omkonvertering är en hämtning och en körning, ofta med OCR.
* **Härkomsten ska vara ärlig.** `pipeline` säger vilken version som
  skrev texten.
* **Enkelt först.** Ingen ny lagring, inget nytt tillstånd, inget nytt
  arbetsflöde.

## Considered Options

* A – En tabell i koden säger vad varje version kan ändra, prövad på
  front matter
* B – Som i dag: versionen avgör, och `full` hoppas över
* C – Ett dokument som inte berörs får den nya versionen i `pipeline`
  eller en rad i versionsloggen, så att det inte prövas igen
* D – En egen regel i koden per version, som en funktion

## Decision Outcome

Valt: A, eftersom front matter redan har det som behövs per sida
(`kvalitet_per_sida`, `tal_obekraftade`), och en tabell gör varje
versions räckvidd synlig och prövbar i CI.

* **Tabellen** är `src/kommunhandlingar/omkonvertering.toml` och följer
  med paketet, eftersom den hör till koden och inte till ett datarepo
  (ADR-0080). Varje version har en rad med en lista: `alla`, en
  sidkvalitet (dokumentet har en sådan sida) eller `tal_obekraftade`
  (dokumentet har en sida med obekräftade tal).
* **Ett dokument konverteras om** när kommunfilen har
  `omkonvertera = true`, dokumentet inte är granskat, och någon version
  efter dokumentets och fram till poolens berör det. Det ersätter
  signalen i ADR-0019 ("en annan version") och alternativ A i ADR-0099
  (`full` hoppas över). Allt annat i ADR-0019 och ADR-0076 gäller som
  förut: ordningen, omhämtningen, samma och annan sha256, arkivets egna
  dokument.
* **Varför det räcker att pröva den lagrade texten.** Berörs ett
  dokument inte av version N, skriver N samma sak som versionen före.
  Gäller det varje version efter dokumentets är den lagrade texten
  densamma som poolens version skulle skriva, och dokumentets front
  matter är också det som varje senare rad prövas mot. Raden måste därför
  vara en överskattning: det den kan ändra, inte det den brukar ändra.
* **Per dokument, inte per sida.** Berörs en sida konverteras hela
  dokumentet om, så att tabeller över flera sidor (ADR-0024) och
  dokumentets kvalitet följer med.
* **`pipeline` ändras inte** för ett dokument som inte berörs, och
  inget skrivs i versionsloggen. Regeln räknas fram ur tabellen och front
  matter i varje körning, utan anrop. En rad ändras aldrig i efterhand
  utan ett nytt beslut.
* **Versionerna jämförs som tal**, inte som lika eller olika. Ett
  dokument från en nyare version än poolens lämnas orört, så att en
  äldre utcheckning inte skriver över det med äldre kod. Ett dokument som
  helt är `ej-konverterad` och saknar sidor, eller har en sida som är
  `ej-konverterad`, berörs av varje ny version, eftersom felet kan ha
  varit tillfälligt (Tesseract som fallerar eller når sin tidsgräns). Det
  gällde också med den gamla regeln.
* **Raden gäller allt sedan förra versionen**, inte bara den ändring som
  höjde den. En omstrukturering som sägs lämna beteendet orört och som
  slagits ihop mellan två höjningar omfattas av nästa rad, och
  granskningen av varje höjning prövar raden mot hela diffen sedan förra
  versionen.
* **CI kräver en rad** för versionen i `pyproject.toml`, raderna i
  versionsordning och bara kända värden.

Raderna i efterhand:

| Version | Kan ändra | Skäl |
| --- | --- | --- |
| 0.1.0–0.12.0 | `alla` | tabeller, spalter och text på högkant på textsidorna; går inte att avgränsa ur front matter |
| 0.13.0 | `ocr`, `ej-konverterad` | bilder och vridna sidor prövas bara på sidor som läses med OCR (ADR-0099) |
| 0.14.0 | `ocr`, `ej-konverterad`, `bild`, `tom` | säkra rader prövas före `bild` och `tom` (ADR-0100) |
| 0.15.0 | `alla` | före 0.15.0 gav text på högkant obekräftade tal, men inte ett blanktecken på högkant; 0.15.0 läser också en sådan sida på nytt och räknar dess skarv (ADR-0024) utan tecknet, och sidan syns inte i front matter (ADR-0038, ADR-0103) |
| 0.16.0 | `ocr` | väg H prövas bara på sidor som läses med OCR (ADR-0106) |

Allt före 0.13.0 är `alla`, eftersom varje dokument som är äldre än
0.12.0 ändå berörs av 0.10.0–0.12.0; en snävare rad där ger ingenting.
Agenten föreslog först `tal_obekraftade` för 0.15.0. Granskningen visade
att 0.15.0 prövar alla tecken på högkant, också blanktecken, medan regeln
före 0.15.0 hoppade över blanktecken; en sådan sida var inte märkt och kan
ändå läsas annorlunda. Raden blev därför `alla`.
En sida som 0.13.0 gjorde `tom` går inte att skilja från en vit sida som
aldrig lästes med OCR, så 0.14.0 tar med alla `tom`.

### Consequences

* Bra, eftersom en version som bara ändrar skannade sidor bara hämtar de
  dokument som har sådana sidor.
* Bra, eftersom ett dokument som är `full` konverteras om när en version
  kan ändra det, så att arkivets äldre tabeller rättas.
* Bra, eftersom `pipeline` fortsätter att säga vilken version som skrev
  texten.
* Dåligt, eftersom en fel rad lämnar dokument i en äldre version utan att
  det syns. Därför är raden en överskattning, skälet står i tabellen och
  i ADR:en för versionen, och granskningen av varje versionshöjning
  prövar raden.
* Dåligt, eftersom 0.16.0 i dag ger fler omkonverteringar än förut:
  4 898 av 5 050 ogranskade dokument i stället för 1 692, eftersom raden
  för 0.15.0 är `alla` och de 3 356 dokument som är `full` då kommer med
  en gång. Det är en engångskostnad. En framtida version som bara ändrar
  sidor som läses med OCR berör 1 104 dokument i stället för alla som
  inte är `full`.
* Neutralt, eftersom ett dokument som inte berörs fortsätter att ha en
  äldre version i `pipeline`. Den som läser poolen ser i tabellen att
  texten är densamma som poolens version skulle skriva.

### Confirmation

* `tests/test_omkonvertering_tabell.py`: versionen i `pyproject.toml` har
  en rad, raderna står i ordning med kända värden, och regeln: bara
  versionerna efter dokumentets och fram till poolens räknas, `alla`,
  sidkvalitet och `tal_obekraftade` träffar som de ska, ett nyare
  dokument lämnas orört, och ett dokument utan sidor eller med en sida som
  är `ej-konverterad` berörs.
* `tests/test_omkonvertering.py`: ett dokument som inte berörs är
  oförändrat och flyttas inte sist, ett som berörs konverteras om, också
  när det är `full`, och ett granskat konverteras aldrig om.
* Prov 2026-11-22: 14 dokument från de levande källorna, lästa av 0.12.0
  och som tabellen säger inte berörs av 0.13.0–0.16.0 (6 `full`, 8
  andra), hämtades igen och konverterades med 0.16.0. Text, tabeller och
  kvalitetsfälten blev identiska i alla 14.

## Pros and Cons of the Options

### A – En tabell i koden, prövad på front matter

* Bra, eftersom signalen redan finns i varje dokument.
* Bra, eftersom raderna går att läsa och pröva utan koden.
* Dåligt, eftersom varje versionshöjning kräver en bedömning av vad den
  kan ändra.

### B – Som i dag

* Bra, eftersom ingen bedömning behövs.
* Dåligt, eftersom allt som inte är `full` konverteras om varje gång,
  också när versionen inte kan ändra det.
* Dåligt, eftersom `full` aldrig rättas, också när en version kan ändra
  det (ADR-0099 nämnde det som kostnaden för alternativ A).

### C – Den nya versionen i `pipeline` eller i versionsloggen

* Bra, eftersom ett dokument som prövats en gång inte prövas igen.
* Dåligt, eftersom `pipeline` då påstår att en version skrev en text som
  den aldrig läst. Härkomsten blir oärlig.
* Dåligt, eftersom versionsloggen (ADR-0077) loggar nya original ur
  källan, inte konverteringar, och varje höjning skulle ge tusentals rader.
* Dåligt, eftersom prövningen ändå är billig: front matter, inga anrop.

### D – En regel per version som en funktion

* Bra, eftersom en regel kan vara hur exakt som helst.
* Dåligt, eftersom varje version blir ny kod, och ingen abstraktion behövs
  förrän ett fall kräver mer än sidkvaliteter och `tal_obekraftade`.

## More Information

### Diskussionen som ledde fram till beslutet

1. **Frågan (projektägaren).** Efter 0.16.0 frågade ägaren om dokument
   med full kvalitet också görs om, om det är nödvändigt och om de kan
   vara fel. Ägaren ville ha en generell tanke kring vad en omkonvertering
   slår på, eftersom det är dumt att slösa miljöresurser utan någon
   möjlighet att göra något bättre.
2. **Läget (agenten).** `full` görs inte om sedan 0.13.0. Dokumenten från
   de levande källorna som är `full` är alla lästa av 0.12.0 eller
   senare, och 0.13.0–0.16.0 ändrar bara skannade sidor och sidor med
   obekräftade tal. Provet med 14 dokument gav identisk text. Men 1 451
   dokument ur arkivet som är `full` är lästa före 0.12.0 och kan ha
   ihopslagna kolumner.
3. **Förslaget (agenten).** En tabell per version över vad den kan
   ändra, prövad på front matter. Ingen ny version i `pipeline` och ingen
   rad i versionsloggen för de dokument som inte berörs, så att
   härkomsten förblir ärlig. Front matter räcker, eftersom
   `kvalitet_per_sida` och `tal_obekraftade` redan är per sida. Granskade
   dokument och arkivet följer reglerna som förut.
4. **Beslutet (projektägaren).** Ja till tabellen, och ja till att `full`
   följer den, så att arkivets äldre dokument som är `full` konverteras om
   en gång. Raderna i efterhand som agenten föreslog.
5. **Granskningen (fas 6)** fann att raden för 0.15.0 inte var en
   överskattning, eftersom ett blanktecken på högkant inte gav obekräftade
   tal före 0.15.0. Raden blev `alla`, så att 0.16.0 i dag konverterar om
   nästan hela poolen en gång. Granskningen påpekade också att en sida som
   är `ej-konverterad` kan bero på ett tillfälligt fel, och den prövas nu
   av varje ny version.
6. **Nattkörningen** samma natt konverterade om som förut; regeln gäller
   från den körning som har den här ändringen.
7. **Omprövas** om en version behöver en räckvidd som inte går att
   uttrycka med sidkvaliteter och `tal_obekraftade`.
