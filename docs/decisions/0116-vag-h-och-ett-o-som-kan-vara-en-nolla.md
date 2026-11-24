---
status: accepted
date: 2026-11-24
decision-makers: projektägaren
consulted: AI-agenten
---

# Väg H bekräftar inte en rad med ett o som kan vara en nolla, och facit räknar inte utfyllnad under ett tecken

## Context and Problem Statement

Kalibreringen av väg H (K84,
[ADR-0105](0105-vag-h-kalibreras-mot-textlagersidor.md)) blev röd också
på `main` den 24 november 2026, med fem falska bekräftelser på två
sidor. Poolen hade fått nya dokument, så att urvalet med det fasta fröet
gav andra sidor än vid den senaste gröna körningen
([#484](https://github.com/moggleif/kungsbackakommun/issues/484)).
Orsakerna är två, och de är av olika slag.

1. **En nolla som ser ut som ett o.** I förskole- och grundskolenämndens
   arbetsutskotts handlingar 2023-11-01, sida 28, står `Årskurs 0` i
   Georgia, där siffrorna är gemena: nollan är lika hög och rund som ett
   `o`. RapidOCR läser `Årskurs o` och Tesseract `Årskurs Oo`. Ingen av
   läsningarna har ett tal, så raden avgjordes aldrig, och sidan blev
   bekräftad med en nolla som saknas. Det är en verklig falsk
   bekräftelse: på en skannad sida skulle samma nolla försvinna utan
   att någon ser det.
2. **Facit läste fel.** Trafikalstringsberäkningen för Tölö ängar syd,
   sida 1, är en PDF ur ett kalkylark. Cellens utfyllnad är blanksteg som
   ritats ovanpå talet, så att ett blanksteg ligger mitt över sjuan i
   `730`. Sorterade från vänster blir tecknen `7`, blanksteg, `30`, och
   facit blev `7 30`, där båda motorerna, och ögat, läser `730`. Väg H
   hade rätt; kalibreringen räknade fyra rätt lästa rader som fel.

## Decision Drivers

* Datat ska vara 100 % korrekt. En falsk bekräftelse är värre än tusen
  obekräftade tal (ADR-0105).
* Ett tal som har lästs rätt ska gå att använda. Regeln ska inte ta
  bekräftelsen från vanliga rader i onödan, som punktlistor.
* Kalibreringens facit ska vara det som syns på sidan, så att ett rött
  arbetsflöde betyder ett fel i väg H.

## Considered Options

För nollan:

* A – En rad med ett fristående `o` efter radens första ord kan ha ett
  tal och bekräftas aldrig
* B – Varje fristående `o`, också först på raden
* C – Ingen ändring i väg H; sidan tas ur kalibreringen

För facit:

* D – Ett blanksteg vars mittpunkt ligger i ett synligt tecken är inget
  mellanrum
* E – Facit bortser från textlagrets blanksteg och mäter bara avstånden

## Decision Outcome

Valt: A och D.

**A.** En rad där ett ord i någon av de två läsningarna, utom radens
första, bara består av `o` och `O`, eventuellt med en punkt, ett
kommatecken eller ett kolon efter (`o`, `Oo`, `o.`), räknas som en rad
som kan ha ett tal, även när ingen läsning har en siffra. Den bekräftas
aldrig, med orsaken `o-som-nolla`, och sidan får då obekräftade tal.
Regeln står i `vag_h.py` (`kan_ha_tal`, `osaker`) och gäller både
kalibreringen och konverteringen, eftersom båda läser med
`radlasning.las`. Radens första ord räknas inte, eftersom Word skriver en
punktlistas andra nivå med `o` som punkt och Tesseract läser den så
(`o 0-7 år`), medan en nolla först på raden är sällsynt. `t.o.m.` och
`O:\` är inga fristående `o`.

**D.** I facit är ett blanksteg i textlagret inget mellanrum när dess
mittpunkt ligger i ett synligt tecken på samma rad, eftersom det inte
syns (`kalibrering/facit.py`).

Poolens version höjs till 0.18.0, och bara dokument med sidor som läses
med OCR konverteras om, eftersom regeln bara rör väg H (ADR-0107).

### Consequences

* Bra, eftersom en nolla som båda motorerna läser som ett `o` inte längre
  ger en bekräftad sida.
* Bra, eftersom kalibreringen inte räknar kalkylarkets utfyllnad som ett
  mellanrum, och ett rött arbetsflöde betyder ett fel i väg H.
* Dåligt, eftersom en rad med ett `o` som brus mitt i en rad blir
  obekräftad också när talen lästs rätt. I den röda körningens 5 016 rätt
  bekräftade rader gäller det 5, alla där RapidOCR eller Tesseract läst
  linjer eller prickar som lösa bokstäver.
* Dåligt, eftersom en nolla som läses som ett `o` först på raden
  fortfarande inte märks. Den lämnas med avsikt, för punktlistornas
  skull, och kalibreringen visar om det händer.
* Dåligt, eftersom gemena siffror har fler former som liknar bokstäver,
  som ettan i Georgia. Inget sådant fel har setts; regeln tar bara det
  som kalibreringen visat, och kalibreringen körs igen i varje PR som
  ändrar väg H.
* Neutralt, eftersom D bara ändrar kalibreringen, inte poolen.

### Confirmation

`tests/test_vag_h.py` prövar att `Årskurs o` och `Årskurs Oo` inte
bekräftas och att `o` som punkt, `t.o.m.` och `O:\` inte räknas.
`tests/test_kalibrering.py` prövar att ett blanksteg under en siffra inte
delar talet. Kalibreringen i PR:en mäter 300 sidor ur poolen med det
fasta fröet och ska ha noll falska bekräftelser.

## Pros and Cons of the Options

### A – Ett fristående o efter radens första ord

* Bra, eftersom den tar felet som kalibreringen hittade och nästan inga
  rätt lästa rader.
* Dåligt, eftersom en nolla först på raden inte märks.

### B – Varje fristående o

* Bra, eftersom också en nolla först på raden märks.
* Dåligt, eftersom varje punktlista med `o` som punkt, och de är vanliga
  i handlingarna, får obekräftade tal.

### C – Ingen ändring i väg H

* Bra, eftersom inget tal blir obekräftat.
* Dåligt, eftersom felet finns kvar på skannade sidor, där ingen ser det.

### D – Blanksteg under ett synligt tecken räknas inte

* Bra, eftersom facit blir det som syns, och textlagrets blanksteg
  räknas som förut där de syns.

### E – Bara avstånden

* Bra, eftersom regeln blir enklare.
* Dåligt, eftersom ett hårt blanksteg eller ett smalt mellanslag, som i
  `12 %` och `1 206`, då kan försvinna ur facit.
