---
status: "proposed"
date: 2026-11-22
decision-makers: projektägaren
consulted: AI-agenten
---

# Skannade sidor får väg H:s tal när den lagrade texten har just dem

## Context and Problem Statement

Kalibreringen i [ADR-0105](0105-vag-h-kalibreras-mot-textlagersidor.md)
mätte väg H på 300 textlagersidor utan en falsk bekräftelse. Nu ska väg H
in i konverteringen, så att en skannad sida vars tal väg H bekräftar
inte längre står i `tal_obekraftade`. Men väg H bekräftar rader, och
sidans lagrade text är Tesseracts. På ungefär en sjättedel av de
bekräftade raderna i kalibreringen (176 av 2 148) var det RapidOCR och
den tredje läsningen som var eniga, inte Tesseract. Hur får den lagrade
texten de tal som bekräftats, utan att en sida märks bekräftad med andra
tal i texten än de väg H mätt
([#411](https://github.com/moggleif/kungsbackakommun/issues/411))?

## Decision Drivers

* Datat ska vara 100 % korrekt: de tal som står i den lagrade texten
  ska vara de bekräftade, och inget annat.
* Hellre märka än gissa: en rad som inte går att placera säkert gör
  sidan obekräftad.
* Texten ska ändras så lite som möjligt mot i dag, så att sidor som inte
  bekräftas ser ut som förut.

## Considered Options

* A – Tesseracts text, med RapidOCR:s text på de rader där den bekräftats
* B – Bara Tesseracts text, och en sida bekräftas bara när Tesseract har
  varje bekräftat tal
* C – Bygga sidans text av RapidOCR:s rader

## Decision Outcome

Valt alternativ: "A – Tesseracts text, med RapidOCR:s text på de rader
där den bekräftats", eftersom det är delbeslut 4 i ADR-0105 och tar med
sidorna där RapidOCR och den tredje läsningen var eniga. Det var 56 av de
117 bekräftade sidorna i kalibreringen. Projektägaren sa ja till att
bygga in väg H på det sättet.

Fyra delbeslut följer med:

1. **Väg H prövas bara på en sida vars första läsning med Tesseract når
   tröskeln utan att sidan läses om.** Väg H får TSV:n från samma
   läsning, så att Tesseracts ord, deras rutor och sidans text hör till
   samma bild. En sida som lästs om, med bildytan maskad, vriden, utan
   ord på högkant eller med de säkra raderna, märks som förut.
2. **Raden placeras bara när den går att placera exakt.** Tesseracts ord
   på raden ska stå i följd på en av Tesseracts rader, och Tesseracts
   text ska vara dess ord rad för rad. Orden byts mot RapidOCR:s text.
3. **Sist jämförs talen i den färdiga texten med de bekräftade**, som
   väg H normaliserar dem, lika många gånger vart och ett. Är de inte
   samma är sidans tal obekräftade. Det fångar också två rader som delar
   ett ord, och tal som skrivs ihop över en radgräns.
4. **RapidOCR och onnxruntime blir vanliga beroenden**, eftersom
   konverteringen behöver dem, och `pipeline` nämner dem när en sida
   gick till OCR. Datakontrollen godtar en `ocr`-sida utanför
   `tal_obekraftade` bara i ett dokument vars `pipeline` nämner RapidOCR.

Poolens version höjs till 0.16.0, så att de skannade sidorna kommer med
i omkonverteringen
([#84](https://github.com/moggleif/kommunhandlingar/issues/84)).
Granskade dokument konverteras inte om
([ADR-0055](0055-granskade-dokument-konverteras-inte-om.md)).

### Consequences

* Bra, eftersom ungefär två av fem skannade sidor kan få bekräftade tal,
  räknat på kalibreringens textlagersidor. På riktiga skanningar blir det
  färre.
* Bra, eftersom jämförelsen sist bygger på talen i den text som lagras,
  inte på hur raderna placerats.
* Dåligt, eftersom en skannad sida tar längre tid att konvertera:
  RapidOCR läser hela sidan, och den tredje läsningen varje rad där de
  två är oense.
* Dåligt, eftersom installationen växer med ungefär 200 MB, också för
  den som bara bygger webbplatsen ur ett paket med fast version.
* Dåligt, eftersom en rad med `09: 35` kan sparas som `09:35`, som
  ADR-0105 beskriver.

### Confirmation

`tests/test_bekraftade.py` prövar placeringen och hela vägen, och
`tests/test_konvertering.py` och `tests/test_datakontroll.py` märkningen.
Kalibreringen (K84) mäter regeln. Den lagrade texten mäts inte mot ett
facit, men jämförelsen sist gör att den inte kan ha andra tal än de
kalibreringen mätt.

## Pros and Cons of the Options

### A – Tesseracts text, med RapidOCR:s text på de rader där den bekräftats

* Bra, eftersom den lagrade texten har de bekräftade talen.
* Bra, eftersom sidor som inte bekräftas ser ut som förut.
* Dåligt, eftersom två läsningar blandas i samma text.

### B – Bara Tesseracts text

* Bra, eftersom texten är oförändrad.
* Dåligt, eftersom ungefär hälften av sidorna som väg H bekräftar inte
  får bekräftade tal.

### C – Bygga sidans text av RapidOCR:s rader

* Bra, eftersom texten och talen kommer ur samma läsning.
* Dåligt, eftersom RapidOCR delar en tabellrad i celler och läser
  styckena i en annan ordning än Tesseract. Texten skulle ändras på
  varje skannad sida, också där talen inte bekräftas.

## More Information

Väg H körs på samma sidbild som Tesseract läste, i 300 dpi i gråskala.
Hur placeringen görs står i
[03-ARKITEKTUR.md](../03-ARKITEKTUR.md#väg-h-och-kalibreringen). Beslutet
bör omprövas när märkningen blir per rad i stället för per sida.
