---
status: "accepted"
date: 2026-11-21
decision-makers: projektägaren
consulted: AI-agenten
---

# Text på högkant utan siffror utanför tabellerna gör inte sidans tal obekräftade

## Context and Problem Statement

Statussidan visade att 30 482 av poolens 276 520 sidor (11,0 %) har
obekräftade tal. Ungefär 7 600 av dem är sidor med textlager som märkts
för att texten inte går att läsa i ordning
([ADR-0038](0038-text-i-oordning-ger-obekraftade-tal.md)). Där räcker ett
enda tecken på högkant någonstans på sidan. ADR-0038 skrevs innan
[ADR-0064](0064-text-pa-hogkant-skrivs-sist.md) (K41) tog text på
högkant utanför tabellerna ur sidans flöde. Behöver all sådan text
fortfarande göra sidans tal obekräftade
([#399](https://github.com/moggleif/kungsbackakommun/issues/399))?

## Decision Drivers

* Datat ska vara 100 % korrekt. Ett tal som kan ha lästs fel får aldrig
  räknas som bekräftat.
* Ett tal som har lästs rätt ska gå att använda. Annars blir poolen
  oanvändbar för statistik i onödan.
* Regeln ska gå att lita på utan att varje sätt som text på högkant kan
  ritas på är känt.

## Considered Options

* A – Text på högkant utanför tabellerna räknas inte när K41 läser den
  entydigt
* B – Text på högkant utanför tabellerna räknas bara när den har en
  siffra
* C – Regeln står kvar som i ADR-0038

## Decision Outcome

Valt: B, eftersom bara en siffra kan ge ett fel tal. Det gäller också
när K41 läser texten på högkant fel, och det kan inte A lova. En sida
med textlager får obekräftade tal när något tecken på högkant

* står inne i en tabell, som förut;
* är en siffra, var det än står;
* ändrar hur resten av sidan läses. En sida med text på högkant läses en
  gång till utan den texten, och allt utom texten på högkant ska bli
  likadant: sidans kvalitet (så att en talrad inte tappar märkningen
  `tabell-osaker`), tabellerna cell för cell, figuren, raderna som avgör
  om en tabell fortsätter på nästa sida, och texten fram till texten på
  högkant. Ett ord på högkant intill en tabell utan linjer kan annars få
  tabellen att tappa en rad i tysthet.

Text ritad ovanpå annan upprätt text ger obekräftade tal som förut.
Reglerna står i `konvertering/ordning.py` och `textsida` i
`konvertering/las_sida.py`. Raderna för tabeller över flera sidor
(ADR-0024) läses nu utan text på högkant, eftersom den skrivs sist på
sidan; annars skulle varje stämpel i marginalen göra att sidan läses
annorlunda.

Granskningen hittade också ett fel i K41: en rad som läses medurs fick
falska mellanslag, så att `11,5` blev `11 ,5`. Mellanrummet mäts nu
mellan tecknens rutor åt båda hållen. Det ändrar inget moturs.

Poolens version höjs till 0.15.0, så att sidorna kommer med i
omkonverteringen ([#84](https://github.com/moggleif/kommunhandlingar/issues/84)).
Granskade dokument konverteras inte om
([ADR-0055](0055-granskade-dokument-konverteras-inte-om.md)).

### Consequences

* Bra, eftersom inget tal på högkant räknas som bekräftat. Regeln
  bygger inte på att K41 läser rätt.
* Bra, eftersom ett stickprov på 169 märkta sidor ur 18 handlingar från
  kungsbacka.se, alla med samma sha256 som i poolen, släpper 81. Det är
  sidor med axeltitlar och kartor vars text på högkant saknar siffror.
  Räknat på hela poolen blir det ungefär 3 600 sidor färre, från 11,0 %
  till cirka 9,7 %. Stickprovet tog bara levande dokument.
* Dåligt, eftersom sidor med diagram vars axlar har årtal på högkant,
  eller med ett diarienummer i marginalen, får obekräftade tal fast
  talen i den upprätta texten är rätt. Det var ungefär hälften av
  stickprovet.
* Dåligt, eftersom text som står snett eller upp och ned märks lika lite
  som förut. pdfminer räknar den som upprätt, och den läses in i
  flödet, så att `73` upp och ned blir `37`. Det fanns före det här
  beslutet och följs upp i
  [#401](https://github.com/moggleif/kungsbackakommun/issues/401).
* Dåligt, eftersom en sida med text på högkant utan siffror läses två
  gånger. Det gäller högst ungefär 3 % av sidorna med textlager, de som
  i dag märks för text i oordning.
* Neutralt, eftersom ändringen syns först när ett dokument konverteras
  om.

### Confirmation

`tests/test_ordning.py` prövar regeln med påhittade tecken och med PDF:er
som skapas av `tests/fixtures/pdf/skapa_hogkant_ute.py`. `axeltitel.pdf`
har en axeltitel utan siffror och får bekräftade tal. `medurs.pdf` har en
stämpel med tal och får obekräftade tal. `tabell-hogkant.pdf` har ett ord
på högkant som får en tabell att tappa en rad, och `talrad-hogkant.pdf`
ett ord som tar bort märkningen `tabell-osaker`; båda får obekräftade
tal. Sidorna 1 och 3 i `hogkant.pdf`, ett diarienummer och en
kolumnrubrik på högkant, får obekräftade tal. `tests/test_hogkant.py` prövar mellanrummen åt båda
hållen.

## Pros and Cons of the Options

### A – Text som K41 läser entydigt räknas inte

* Bra, eftersom stickprovet släppte 154 av 169 sidor.
* Dåligt, eftersom fyra omgångar av granskning hittade nya sätt som
  siffror på högkant läses fel: rader så tätt att `2010` och `2011` blev
  `22001101`, speglade tecken, två läsriktningar på samma linje,
  spärrad text där `11,5` blev `1 1 , 5`, och en hel liggande tabell
  vars tomma celler försvann. Varje fall gick att rätta, men det går
  inte att visa att listan är fullständig.

### B – Text på högkant räknas bara när den har en siffra

* Bra, eftersom ett tecken som inte är en siffra inte kan ge ett fel tal,
  hur det än läses.
* Bra, eftersom regeln om siffror är en rad, och kontrollen av resten
  av sidan bygger inte på att varje väg för ett fel är känd.
* Dåligt, eftersom bara hälften så många sidor släpps som med A.

### C – Regeln står kvar

* Bra, eftersom ingenting ändras.
* Dåligt, eftersom ungefär 3 600 sidor vars tal är rätt lästa inte kan
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

Agenten byggde först A. Stickprovet visade att K41 läste talen rätt på
varje släppt sida. Den oberoende granskningen prövade sedan egna PDF:er
och hittade i fyra omgångar de fall som står under A. Efter den fjärde
omgången valde agenten B, eftersom det följer projektägarens krav
utan att förutsätta att alla fel är kända. Sidorna med årtal på högkant
får vänta på en bättre läsning. Den femte omgången hittade ett ord
på högkant utan siffror som tog bort märkningen `tabell-osaker` från en
talrad. I stället för en kontroll per steg läses därför sidan om utan
texten på högkant, och allt annat ska bli likadant. Det ersatte
kontrollen av tabellernas rutor och regeln om text ovanpå en rad, som
båda bara täckte en del av vägarna.
