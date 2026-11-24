---
status: "accepted"
date: 2026-11-24
decision-makers: projektägaren
consulted: AI-agenten
---

# Text snett och upp och ned räknas som text på högkant

## Context and Problem Statement

pdfminer räknar ett tecken som upprätt (`upright`) när `a·d > 0` och
`b·c ≤ 0` i dess matris (`a·d` gånger den vågräta skalningen). Text som vridits ett halvt varv, eller snett,
till exempel 45°, räknas därför som upprätt och läses in i sidans flöde
som vanlig text. Granskningen av
[ADR-0103](0103-hogkant-utan-siffror-ger-bekraftade-tal.md) visade att
`73` upp och ned mitt i en rad blev `37`, och att `98765` i 45° blev
siffror på var sin rad, en av dem inne i ett stycke. Båda sidorna fick
bekräftade tal. Det går emot K6: ett tal som kan ha lästs ihop med annan
text får aldrig räknas som bekräftat
([#401](https://github.com/moggleif/kungsbackakommun/issues/401)). Hur
ska sådan text läsas, och vad betyder den för sidans tal?

Ett stickprov visar hur vanligt det är. 32 handlingar ur detaljplanerna
på kungsbacka.se (4 117 sidor med textlager) och 19 slumpade handlingar
från kungsbacka.se 2024–2026 (777 sidor) hade 34 sidor med tecken som
pdfminer räknar som upprätta men vars baslinje lutar mer än en halv
grad: plankartor, illustrationer och sektioner med gatunamn, mått och
koordinater. Inget tecken stod upp och ned. 22 av sidorna hade siffror
i sådan text, och 4 av dem fick bekräftade tal: koordinaterna längs en
karta (`41000`, `42000` …) och mått i en sektion (`4,5 m`, `6 m`).

## Decision Drivers

* Datat ska vara 100 % korrekt. Ett tal som kan ha lästs fel får aldrig
  räknas som bekräftat.
* Ett tal som har lästs rätt ska gå att använda. Ändringen ska inte ta
  bekräftade tal ifrån sidor i onödan.
* Regeln ska vara densamma som för text på högkant, som redan prövats
  i sex granskningsomgångar (ADR-0103).

## Considered Options

* A – Snett och upp och ned räknas som text på högkant
* B – Bara siffror snett eller upp och ned ger obekräftade tal
* C – Texten läses rätt längs sin baslinje och räknas som annan text

## Decision Outcome

Valt: A, eftersom den följer en regel som redan finns och prövats. Ett
tecken står rakt när pdfminer räknar det som upprätt och dess baslinje
lutar mindre än en halv grad (`konvertering/snett.py`). Allt annat är text
på högkant i ADR-0103:s mening:

* det tas ur sidans flöde, och sidans tal blir obekräftade när något av
  tecknen är en siffra, står i en tabell eller ändrar hur resten av
  sidan läses;
* det skrivs sist på sidan. Text på högkant läses som förut (K41), och
  text snett eller upp och ned efter den, i textlagrets ordning: mer än
  en fjärdedels teckenbredd från där förra tecknet slutar blir ett
  mellanslag, mer än två teckenbredder en ny rad.

Kursiv stil lutar tecknet, inte baslinjen, och står rakt. Gränsen på en
halv grad tar text som lutar så lite att den läses ihop med raderna intill
över en hel sidbredd; ingen sida i stickprovet hade tecken som lutade
mindre än så.

Avstånden mäts längs baslinjen från där förra tecknet slutar. En
fjärdedels teckenbredd, inte en femtedel av teckenhöjden som för text på
högkant, eftersom textlagret inte ger teckenhöjden för text snett;
med den läses mellanslagen i stickprovets kartetiketter rätt.

Poolens version höjs till 0.18.0 och alla dokument konverteras om, eftersom
vilka sidor som har text snett inte syns i front matter.

### Consequences

* Bra, eftersom inget tal snett eller upp och ned räknas som bekräftat.
  I stickprovet får 4 sidor obekräftade tal som förut var bekräftade,
  alla med siffror snett, och ingen sida får bekräftade tal som förut var
  obekräftade.
* Bra, eftersom gatunamnen på en karta inte längre står inne i sidans
  text utan sist, och läses hela: `Gamla Kläppavägen`, `Åsa
  stationsväg`. Förut stod de bokstav för bokstav där de råkade hamna.
* Dåligt, eftersom en karta med mått eller koordinater snett får
  obekräftade tal också när de lästs rätt. Det gäller ungefär en sida på
  250 i detaljplanerna och färre i övriga handlingar.
* Dåligt, eftersom diagram med snedställda axeletiketter med årtal eller
  månader, och diagonala vattenstämplar med datum, gör alla sidans tal
  obekräftade. Stickprovet hade inga sådana, men det tog få budget- och
  uppföljningshandlingar, så andelen kan vara större där.
* Dåligt, eftersom en siffra snett inne i en tabell står kvar i cellen
  som den lästs, och tabellen märks inte osäker; bara sidans tal blir
  obekräftade. Så är det också för text på högkant i en tabell
  (ADR-0038), och det följs upp i
  [#479](https://github.com/moggleif/kungsbackakommun/issues/479).
* Dåligt, eftersom textlagrets ordning bara blir rätt när PDF:en ritar
  tecknen i läsordning. Det gör de i stickprovet, men det går inte att
  lova, och därför bekräftas inga tal ur den texten.
* Neutralt, eftersom ändringen syns först när ett dokument konverteras om.

### Confirmation

`tests/test_snett.py` prövar regeln med påhittade tecken och med PDF:er
som skapas av `tests/fixtures/pdf/skapa_hogkant_ute.py`.
`upp-och-ned.pdf` har `73` upp och ned mitt i en rad och får `73` sist
och obekräftade tal; `snett.pdf` har `98765` i 45° över ett stycke, som
står kvar orört; `gatunamn.pdf` har ett gatunamn i 30° och får
bekräftade tal. Facit för konverteringen (K20) ger samma mått som förut.

## Pros and Cons of the Options

### A – Snett och upp och ned räknas som text på högkant

* Bra, eftersom regeln och dess prövning av resten av sidan redan finns.
* Bra, eftersom ett tal aldrig bekräftas på att texten lästs rätt.
* Dåligt, eftersom mått och koordinater på kartor blir obekräftade.

### B – Bara siffror snett eller upp och ned ger obekräftade tal

* Bra, eftersom ändringen blir mindre.
* Dåligt, eftersom bokstäverna står kvar i flödet. Ett gatunamn som
  hamnar mellan två siffror i en rad kan dela ett tal, och det märks
  inte.

### C – Texten läses rätt längs sin baslinje

* Bra, eftersom måtten på kartorna skulle bli bekräftade.
* Dåligt, eftersom text längs en krökt väg har en ny vinkel för varje
  tecken. Att visa att läsningen alltid blir rätt är samma öppna lista
  som ADR-0103 valde bort för text på högkant.
