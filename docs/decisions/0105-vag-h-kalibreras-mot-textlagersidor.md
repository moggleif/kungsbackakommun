---
status: "proposed"
date: 2026-11-21
decision-makers: projektägaren
consulted: AI-agenten
---

# Väg H kalibreras mot textlagersidor innan den får bekräfta tal i poolen

## Context and Problem Statement

19 879 av poolens sidor har obekräftade tal för att de är skannade och
lästa med OCR. Enligt
[ADR-0005](0005-konvertering-verktyg-ocr-och-kvalitet.md) räknas tal på
en sådan sida aldrig som bekräftade, eftersom Tesseract läste 14 av 117
tal fel trots hög säkerhet. Väg H i ADR-0005 är att två motorer läser
sidan och att en tredje läsning avgör en rad där de är oense. Hur vet vi
att väg H inte bekräftar ett tal som är fel, innan regeln får gälla
poolen ([#411](https://github.com/moggleif/kungsbackakommun/issues/411))?

## Decision Drivers

* Datat ska vara 100 % korrekt. En falsk bekräftelse är värre än tusen
  obekräftade tal, eftersom ingen ser den.
* Mätningen ska ha ett facit som inte är en av läsningarna själv.
* Den ska gå att köra om när regeln ändras, med samma urval.
* Nya beroenden ska vara så små som går.

## Considered Options

* A – Kalibrera mot textlagersidor som renderas och läses med OCR
* B – Kalibrera mot skannade sidor som granskats för hand
* C – Bygga väg H direkt på det första provet

## Decision Outcome

Valt alternativ: "A – Kalibrera mot textlagersidor", eftersom det ger ett
facit för varje rad utan handarbete, på hundratals sidor och med samma
urval varje gång. Projektägaren valde det i fas 0, och att kalibreringen
blir en egen PR före väg H i konverteringen.

Kalibreringen mäter minst 300 sidor med textlager och bekräftade tal ur
poolen, högst tre per dokument och med ett fast frö. Varje PDF hämtas
igen och kontrolleras mot sin sha256, och en PDF som inte går att mäta
ersätts av nästa i urvalet. Blir färre sidor mätta är kravet inte
prövat. Sidan renderas i 300 dpi i gråskala,
som en skannad sida i konverteringen, och läses med väg H. Kravet är
**noll falska bekräftelser**: ingen sida som väg H bekräftar får ha en
rad med fel tal, en rad med ett upphöjt tecken i textlagret, en rad med
tal som ingen läsning såg, eller tal utanför raderna. Först när kravet är
uppfyllt byggs väg H in i konverteringen.

Fyra delbeslut följer med:

1. **Den tredje läsningen görs med samma latinska modell som PaddleOCR
   använder, `latin_PP-OCRv5_mobile_rec`, men genom RapidOCR i
   onnxruntime** och inte med PaddleOCR. Beroendet blir ungefär 200 MB i
   stället för över 1 GB, och RapidOCR kontrollerar modellfilens
   sha256 när den hämtas.
2. **Ett skydd mot upphöjda tecken.** En rad med ett upphöjt tecken, som
   en fotnotssiffra eller tvåan i m², bekräftas aldrig. Inte heller en rad
   som själv står upphöjd bredvid en högre rad, som när RapidOCR gett en
   fotnotssiffra en egen rad. Inte heller en rad där en siffra står
   direkt intill en bokstav, eftersom båda motorerna läser `Kl.` som
   `K1.`. Hur tecknen mäts står i
   [03-ARKITEKTUR.md](../03-ARKITEKTUR.md#väg-h-och-kalibreringen).
3. **En sida bekräftas bara när varje rad med tal är bekräftad** och inget
   tal i Tesseracts läsning står utanför raderna. Märkningen är per sida,
   som i dag.
4. **Den lagrade texten får de bekräftade talen.** När väg H byggs in
   ersätts Tesseracts text för en rad som bekräftats utan Tesseract
   (`tredje-och-rapid`) med RapidOCR:s läsning av raden. Annars skulle
   sidan märkas bekräftad med andra tal än de som kalibreringen mätt.
   Hur raden placeras i sidans text avgörs i det steget.

### Consequences

* Bra, eftersom varje regeländring mäts på samma sidor och en falsk
  bekräftelse syns med rad och läsningar i rapporten.
* Bra, eftersom mätningen faller i CI när kravet inte är uppfyllt.
* Dåligt, eftersom en renderad textlagersida är renare än en skanning.
  Kalibreringen visar att regeln inte bekräftar fel på ren text, men inte
  hur mycket som bekräftas på en riktig skanning. Det mäts för sig på
  riktiga skanningar, utan facit.
* Dåligt, eftersom CI får RapidOCR och onnxruntime att installera, och en
  körning tar ungefär en timme.

### Confirmation

`python -m kommunhandlingar.kalibrering` och arbetsflödet
`.github/workflows/kalibrering.yml`, som körs för hand och i varje PR som
ändrar regeln eller mätningen (K84). Regeln och skyddet prövas i
`tests/test_vag_h.py`, `tests/test_upphojt.py` och
`tests/test_radlasning.py`.

## Pros and Cons of the Options

### A – Kalibrera mot textlagersidor som renderas och läses med OCR

* Bra, eftersom textlagret är ett oberoende facit för varje rad.
* Bra, eftersom urvalet kan bli stort och tas om.
* Dåligt, eftersom renderad text är lättare att läsa än en skanning, så
  felen på riktiga skanningar kan vara andra.

### B – Kalibrera mot skannade sidor som granskats för hand

* Bra, eftersom det mäter just de sidor regeln ska gälla.
* Dåligt, eftersom varje sida kräver att en människa läser varje tal. 300
  sidor är tusentals tal.
* Dåligt, eftersom en människa också läser fel, och då är facit fel.

### C – Bygga väg H direkt på det första provet

* Bra, eftersom effekten kommer fortare.
* Dåligt, eftersom provet var 74 sidor och gav 19 falska bekräftelser
  innan skyddet fanns. Ett fel som är ovanligt syns inte i ett litet prov.

## More Information

**Provet i fas 0.** Agenten installerade RapidOCR 3.10 (PP-OCRv6),
Tesseract 5 med `swe` och PaddleOCR 3.7 och läste 74 textlagersidor. Av
1 206 bekräftade rader med tal var 19 fel. 16 gällde upphöjda tecken:
fotnotssiffror som `¹¹` som blev `1`, `m²` och `brukare⁴`, som båda
motorerna tappade på samma sätt. 3 var tal i en bild, där textlagret
saknar talet, så att facit brast och inte läsningen. Inget fel gällde ett
vanligt tal i en mening eller en tabell. På 11 riktiga skanningar ur
kommunstyrelsens arbetsutskott blev 9 av 10 rader med tal bekräftade.

**PaddleOCR eller samma modell i onnxruntime.** ADR-0005 nämner
PaddleOCR. Paketen `paddlepaddle` och `paddleocr` tar över 1 GB.
RapidOCR har samma latinska modell exporterad till ONNX. På en lång rad
läste PaddleOCR `s F1F1F119pfARO.` och modellen i onnxruntime
`41 Diagnos 11-F1, F18-F19 ocheller ugift om LARO.`, eftersom PaddleOCR
skalar raden annorlunda. Agenten rekommenderade onnxruntime. Valet prövas
av kalibreringen som allt annat.

**Facit och upphöjda tecken.** Den oberoende granskningen (fas 6) visade
att pdfplumber läser ihop en upphöjd siffra med ordet före, så att
`118²` blir `1182` i facit. Då kan just den felklass som skyddet finns
för inte mätas: läser motorerna ihop siffrorna på samma sätt blir raden
"rätt". Därför prövas textlagrets tecken för sig, och en bekräftad rad
med ett upphöjt eller mindre tecken i textlagret räknas alltid som en
falsk bekräftelse. Granskningen visade också att en understrykning, en
siffra som nuddar bokstaven före och en siffra vid rutans överkant tog
sig förbi den första versionen av skyddet. Det rättades före
kalibreringen.

**Den första körningen i Actions.** Den gick på koden före granskningens
rättelser och mätte 294 sidor: 5 797 rader rätt och 8 falska
bekräftelser. Två var `m²`, som skyddet nu stoppar. Två var `Kl.` som
båda motorerna läste `K1.`, vilket gav regeln om en siffra intill en
bokstav. Fyra var facit som brast: pdfplumber läste ihop ett datum och en
tid som står åtskilda (`2021-03-2215:33:39`), och ett tankstreck följt av
mellanslag (`2026– 2030`) blev två tal. Facit läser därför tecknen med
synliga mellanrum, och mellanslag kring ett tankstreck mellan två
siffror räknas inte.

**Den andra körningen.** Den mätte 300 sidor: 189 bekräftade och 23
falska bekräftelser. Nio var de fall som redan rättats. Tio var en
rubrik i 7 punkter bredvid ett datum (`Upprättad 2016-08-16`), som facit
tog för upphöjd fast talen var rätt. Facit jämför därför en siffra bara
med tecknet intill. En var ett verkligt fel: två rutor från RapidOCR gick
in i varandra, och den högra läste nian i grannens `2024-02-29` som ett
eget tal, `9 2024-01-24`, och den tredje läsningen höll med. En rad vars
ruta går in i en annan på samma rad bekräftas därför inte. Tre gällde en
blankett där textlagrets tecken är spärrade och vridna, så att facit
läste `4 3 4 8 1` och `001 6002`. Facit räknar därför med radens vanliga
avstånd, och en rad med en vriden siffra har inget facit.

**Den tredje körningen.** 300 sidor: 5 610 rader rätt, 117 sidor
bekräftade och en falsk bekräftelse. Textlagret hade `09: 35` med ett
mellanslag efter kolonet, och båda motorerna läste `09:35`. Att räkna
bort mellanslaget i jämförelsen hade dolt samma fel i `punkt 4: 20`, och
att mäta luckan i bilden skilde inte ett tappat mellanslag från kolonets
egen luft (en fjärdedel mot en femtedel av radhöjden). Därför bekräftas
en rad med ett kolon mellan två siffror aldrig, fast det gäller klockslag och lagrum på ungefär hälften av de
bekräftade sidorna. Regeln om en siffra intill en bokstav kostar också:
305 rader och 99 sidor blev obekräftade bara av den, mest
kontrollsummor, `100kr`, diarienummer som `RES123` och `Kl.`. Den
behålls, eftersom just de raderna är där en bokstav läses som en siffra
utan att någon läsning märker det. Märkning per rad kan ta tillbaka
sidornas övriga tal. Den oberoende granskningen av rättelserna visade
att mellanslag kring bindestreck och minus inte heller får räknas bort,
eftersom `116 −4` då blir `116-4`. Bara tankstreck räknas bort.

**Skyddets form.** Agentens första försök mätte varje mörk del för sig.
Det flaggade ringen i å och pricken i i som upphöjda, och 82 rader med
tal blev obekräftade i onödan. När delar som överlappar i sidled slogs
ihop till ett tecken, och radens höjd räknades från de högsta tecknen,
flaggades 22 rader som annars hade blivit rätt, av dem flera med en
verklig upphöjd bokstav. Skyddet är avsiktligt grovt: ett citattecken
eller en gradsymbol kan också göra en rad obekräftad. Det är "hellre
märka än gissa".

**Det som inte ingår.** Text upp och ned eller snett (#401), sidor som
inte gick att konvertera, handskrift och kryssrutor. Märkning per rad i
stället för per sida kan komma senare, med ett eget beslut.

**När beslutet bör omprövas.** När en motor eller modell byts, när
skyddet ändras, eller om en falsk bekräftelse hittas i poolen efter att
väg H börjat gälla.
