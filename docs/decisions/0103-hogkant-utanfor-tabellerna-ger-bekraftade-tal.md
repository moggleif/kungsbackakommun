---
status: "accepted"
date: 2026-11-21
decision-makers: projektägaren
consulted: AI-agenten
---

# Text på högkant utanför tabellerna gör inte sidans tal obekräftade

## Context and Problem Statement

Statussidan visade att 30 482 av poolens 276 520 sidor (11,0 %) har
obekräftade tal. Ungefär 7 600 av dem är sidor med textlager som märkts
för att texten inte går att läsa i ordning
([ADR-0038](0038-text-i-oordning-ger-obekraftade-tal.md)). Där räcker ett
enda tecken på högkant någonstans på sidan. ADR-0038 skrevs när sådana
tecken blandades in i raderna en bokstav i taget. Sedan
[ADR-0064](0064-text-pa-hogkant-skrivs-sist.md) (K41) tas text på högkant
utanför tabellerna ur sidans flöde och skrivs sist i sin läsriktning.
Behöver den fortfarande göra sidans tal obekräftade
([#399](https://github.com/moggleif/kungsbackakommun/issues/399))?

## Decision Drivers

* Datat ska vara 100 % korrekt: ett tal som kan ha lästs ihop med annan
  text får aldrig räknas som bekräftat.
* Ett tal som har lästs rätt ska gå att använda, annars blir poolen
  oanvändbar för statistik i onödan.
* Märkningen ska följa hur texten faktiskt läses, inte hur den lästes
  förut.

## Considered Options

* A – Tecken på högkant utanför tabellerna räknas inte när de går att
  läsa entydigt; inne i en tabell gör de sidans tal obekräftade som förut
* B – Tecken på högkant räknas bara när något av dem är en siffra
* C – Regeln står kvar som i ADR-0038

## Decision Outcome

Valt: A, eftersom det är precis den text som K41 redan läser för sig.
Tecken på högkant utanför tabellerna tas bort innan regeln för text
ritad ovanpå annan text prövas, eftersom de inte skrivs i samma rad som
den upprätta texten. Men de räknas bara bort när K41 läser dem
entydigt:

* varje tecken är vridet en kvarts varv, utan spegling;
* varje rad på högkant står på en linje, så att två rader inte ligger
  närmare än en teckenstorlek och läses ihop. En rad med årtalen `2010`
  och `2011` sju punkter isär blir annars `22001101`;
* varje rad läses åt ett håll, inte moturs och medurs på samma linje;
* inga tecken i en rad ligger till hälften eller mer över varandra, som
  två stämplar på samma ställe;
* inget tecken på högkant står ovanpå ett upprätt tecken. En `5` på
  högkant över mellanrummet i `12 34` kan annars göra raden till
  `1234`. Därför räknar inte heller mellanslagsregeln i
  [ADR-0036](0036-mellanslag-inne-i-en-siffra-tas-bort.md) siffror på
  högkant.

Annars gör texten på högkant sidans tal obekräftade som förut. Inne i en
tabell står tecknen kvar i cellerna, och där gör ett tecken på högkant
sidans tal obekräftade som förut. Tabellerna är både de med linjer och
de utan. Text ritad ovanpå annan upprätt text ger obekräftade tal som
förut. Reglerna står i `konvertering/ordning.py` och
`konvertering/hogkant.py`. Gränserna för vridning (1 % av matrisens
skala) och linje (en tiondel av teckenstorleken) är satta, inte
uppmätta. I stickprovet var vridningen exakt och raderna utan spridning,
utom på fyra sidor som fortsätter vara märkta.

Poolens version höjs till 0.15.0, så att sidorna kommer med i
omkonverteringen ([#84](https://github.com/moggleif/kommunhandlingar/issues/84)).
Granskade dokument konverteras inte om
([ADR-0055](0055-granskade-dokument-konverteras-inte-om.md)).

### Consequences

* Bra, eftersom ett stickprov på 169 märkta sidor ur 18 handlingar från
  kungsbacka.se släpper 154 med den nya
  regeln. Alla 18 hade samma sha256 som i poolen. De
  154 sidorna hade text på högkant bara utanför tabellerna: axeltitlar,
  axlarnas årtal och åldrar, koordinater på kartor och en filrad i
  marginalen. Kontrollen mot den ritade sidan visar att talen står rätt,
  till exempel åldersaxeln 0–99, årtalen 2010–2032 och `6377000`.
  Räknat på hela poolen blir det ungefär 6 900 sidor färre, från 11,0 %
  till cirka 8,5 %. Stickprovet tog bara levande dokument.
* Bra, eftersom de femton sidorna som inte går att läsa entydigt står kvar: text
  ritad ovanpå annan text, eller tecken på högkant i en tabell.
* Dåligt, eftersom en siffra på högkant utanför tabellerna, som ett
  axelvärde, räknas som bekräftad, fast det är K41:s läsriktning som
  avgör den. Läsriktningen och entydigheten prövas i
  `tests/test_hogkant.py`, och läsningen stämde på varje släppt sida i
  stickprovet.
* Dåligt, eftersom text som står snett eller upp och ned märks lika lite
  som förut. pdfminer räknar den som upprätt, och den läses in i
  flödet, så att `73` upp och ned blir `37`. Det fanns före det här
  beslutet och följs upp i
  [#401](https://github.com/moggleif/kungsbackakommun/issues/401).
* Neutralt, eftersom ändringen syns först när ett dokument konverteras
  om.

### Confirmation

`tests/test_hogkant.py` prövar entydigheten med påhittade tecken: täta
rader, två läsriktningar på samma linje, tecken över varandra och
speglade tecken. `tests/test_mellanslag.py` prövar att en siffra på
högkant inte tar bort ett mellanslag.
`tests/test_ordning.py` prövar regeln med påhittade tecken, och sidorna 1
och 3 i `tests/fixtures/pdf/hogkant.pdf`: ett diarienummer på högkant i
marginalen ger bekräftade tal, och en kolumnrubrik på högkant i en tabell
ger obekräftade.

## Pros and Cons of the Options

### A – Bara tecken på högkant inne i en tabell räknas

* Bra, eftersom det följer K41: det som läses för sig räknas för sig.
* Bra, eftersom regeln blir en rad och tabellerna redan finns.
* Dåligt, eftersom ett axelvärde på högkant litar på K41:s läsriktning.

### B – Bara siffror på högkant räknas

* Bra, eftersom ingen siffra på högkant blir bekräftad.
* Dåligt, eftersom bara hälften av stickprovets sidor släpps (85 av
  169). Diagrammens axlar har nästan alltid årtal eller värden.
* Dåligt, eftersom tecken på högkant inne i en tabell utan siffror ändå
  blandas in i cellerna och kan flytta tal; B skulle släppa dem.

### C – Regeln står kvar

* Bra, eftersom ingenting ändras.
* Dåligt, eftersom ungefär 6 900 sidor vars tal är rätt lästa inte kan
  användas som data.

## More Information

### Diskussionen som ledde fram till beslutet

Projektägaren frågade varför andelen sidor med obekräftade tal var så
hög, och vad som kunde göras. Agenten delade upp de 30 482 sidorna efter
orsak: 65 % skannade sidor (ADR-0005), 25 % text i oordning, 3 %
oläsliga tecken och 8 % sidor som inte gick att konvertera. Agenten
föreslog att regeln görs smalare först och att väg H i ADR-0005 tas som
ett eget arbete för de skannade sidorna. Projektägaren svarade att båda
var rimliga och att det viktiga är att datat är 100 % korrekt, eftersom
det annars inte går att bygga statistik på det.

Agenten tog därför fram stickprovet innan regeln ändrades. Det skulle
visa vad som faktiskt utlöser märkningen, och att talen på de sidor som
släpps står rätt. B prövades i samma stickprov och släppte för lite.
B skyddar inte heller tabellerna, där oordningen verkligen kan flytta ett
tal.

Den oberoende granskningen (fas 6) hittade att K41 läser ihop rader på
högkant som ligger tätt, och att speglade tecken, som inte heller är
upprätta, läses i fel ordning. Regeln skärptes därför så att bara text som K41 läser
entydigt räknas bort. En andra granskning hittade att en siffra på
högkant ovanpå en rad kan flytta talen i den, och att två läsriktningar
på samma linje läses baklänges; också de märks. Det kostade sju sidor i
stickprovet. Ett tal på
dem kan ha lästs ihop med ett annat, och de står därför kvar.
