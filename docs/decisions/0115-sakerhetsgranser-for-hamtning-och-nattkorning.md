---
status: "accepted"
date: 2026-11-24
decision-makers: projektägaren
consulted: AI-agenten
---

# Hämtningen tar bara https och har tak, stora sidor renderas inte, och nattkörningens gren mergas bara när den ändrar data

## Context and Problem Statement

Säkerhetsgenomgången i
[#348](https://github.com/moggleif/kungsbackakommun/issues/348) gick
igenom hur poolen läser filer från internet, kör Tesseract, hämtar,
låser beroenden, kör sina arbetsflöden, renderar text på webbplatsen och
hanterar hemligheter. Det mesta höll redan. Det som inte höll:

* Klienten byggdes med `urllib.request.build_opener`, som också öppnar
  `file:`, `ftp:` och `data:`. En länk på en källsida som pekade på
  `file:///…` skulle ha lästs från runnerns disk, om adaptern släppt
  igenom den.
* Varken en sida eller en fil hade något storlekstak. En server som
  svarade utan slut fyllde disken eller minnet.
* En PDF-sida renderas i 300 dpi av pypdfium2, utan Pillows skydd mot
  dekompressionsbomber, som bara gäller när Pillow själv öppnar en bild.
  En sida på 5 × 5 meter blir en bild på flera gigabyte.
* Nattkörningens jobb läser PDF:er med `contents: write` och token i
  utcheckningen, och dess gren mergas automatiskt när CI går igenom. Tar
  en fil över tolken kan den pusha kod till grenen, och den kod når `main`
  utan att en människa ser den. `spara.sh` släpper bara igenom `data/` och
  `versioner/`, men den körs i samma jobb som den övertagna processen.
* Actions var fästa vid major-taggar, som utgivaren kan flytta.
* npm-paketen installerades med sina installationsskript, utan låsfil.
* Tre små PDF:er från kalibreringen i #429 låg i roten. De innehöll bara
  text, så git såg dem som text och CI:s kontroll av binärer släppte
  igenom dem.

Hur ska gränserna dras, så att de skyddar utan att stoppa riktiga
handlingar?

## Decision Drivers

* **Hämtat innehåll är data, inte instruktioner** (AGENTS.md).
* **Tomt är inte noll.** Det som stoppas av en gräns ska stå med sin
  orsak, inte försvinna.
* **Ingen kod för säkerhets skull.** Varje gräns ska svara mot en väg som
  faktiskt finns.
* **De riktiga handlingarna ska gå igenom.** Det största originalet i
  poolen är 324 MB och 2 449 sidor, och detaljplanernas plankartor kan
  vara A0.

## Considered Options

* A – Gränser där det hämtade och nattkörningens gren passerar: bara
  https och tak i klienten, ett yttak före renderingen, en kontroll av
  grenen i PR-jobbet och fästa actions.
* B – Som A, och dessutom en lista över tillåtna värdar i klienten, ur
  kommunfilerna.
* C – Dela nattkörningen i ett jobb som bara läser och ett som pushar,
  med datat som artefakt emellan.

## Decision Outcome

Valt: A, eftersom varje del stänger en väg som finns, med några rader
var, och inget i poolens nuvarande innehåll stoppas.

* **Bara https.** Klienten hämtar ingenting, inte heller `robots.txt`,
  från en adress som inte är `https://`; orsaken är `inte-https`. Alla
  5 236 `kalla_url` i poolen är https.
* **Tak.** En sida läses högst 50 MB och en fil högst 1 GiB, tre gånger
  det största originalet. Över taket avbryts läsningen, orsaken är
  `for-stor`, och inget nytt försök görs.
* **Yttak.** En sida som i 300 dpi skulle bli större än Pillows gräns för
  en dekompressionsbomb, `2 × MAX_IMAGE_PIXELS` eller omkring 10,3
  miljoner kvadratpunkter, renderas inte: den blir `ej-konverterad` och
  står i `figurer`, som en sida över teckentaket (ADR-0079). En A0 är 8,0
  miljoner kvadratpunkter och läses. Tolkningen av figurer, som renderar
  sådana sidor, minskar skalan så att bilden håller sig under Pillows
  varningsgräns, `MAX_IMAGE_PIXELS`.
* **Grenen prövas innan den mergas.** PR-jobbet, som redan körs utan
  utcheckning på en ny runner, hämtar grenens och `main`s commits och
  träd, utan filinnehåll och utan att köra något ur repot. Grenen får bara
  lägga till, ändra och ta bort vanliga filer under `data/` och
  `versioner/`, utan namnbyten (`--no-renames`, så att en fil som flyttas
  in i `data/` syns där den kom ifrån), utan symboliska länkar och
  undermoduler, och utan merge-commits, så att diffen från merge-basen är
  det som mergas. Annars öppnas ingen PR och jobbet faller. Jobbet kör med
  `pipefail`, så att ett fel i prövningen stoppar den i stället för att
  släppa igenom grenen. Automatisk merge slås på med
  `--match-head-commit` för den prövade commiten.
* **Actions fästa vid en commit**, med versionen i en kommentar som
  Dependabot håller uppdaterad. CI faller om en extern action står på en
  tagg.
* **npm utan installationsskript** (`--ignore-scripts`), för ESLint,
  jsdom och markdownlint-cli2.
* **Ingen PDF utanför `tests/fixtures/`.** CI faller på filändelsen, inte
  bara på git:s gissning om binärer, och de tre filerna i roten tas bort.

Det som granskades och höll står i PR:en för #348: underprocesserna,
dokumentets tidsgräns, escapningen på webbplatsen, `permissions` per
jobb och historiken.

### Consequences

* Good, eftersom en övertagen tolk i nattkörningen inte längre kan föra in
  kod i `main` utan att en människa ser det.
* Good, eftersom en källa som pekar fel eller svarar utan slut ger en
  orsak i sammanfattningen i stället för en full disk.
* Neutral, eftersom klientens tester kör mot en lokal server över http
  och därför byter schemat i testet.
* Bad, eftersom en riktig sida större än lite mer än A0 inte läses. Ingen
  sådan finns i poolen i dag; den blir en figur och syns som
  `ej-konverterad`.
* Bad, eftersom PR-jobbet hämtar grenen anonymt och förutsätter att repot
  är publikt. Blir det privat faller jobbet, i stället för att merga
  utan prövning.
* Bad, eftersom det inte är prövat att GitHub håller fast vid
  `--match-head-commit` när en commit pushas efter att automatisk merge
  slagits på. Arkivets jobb, som kör samtidigt som mötenas PR-jobb, har
  skrivrätt och kunde i så fall pusha till mötenas gren efter prövningen.
  Skyddet mot det är alternativ C, som väljs bort nedan och står kvar i
  [#483](https://github.com/moggleif/kungsbackakommun/issues/483).
* Bad, eftersom en hämtning bara har tidsgränsen per läsning, 60
  sekunder. En server som skickar lite i taget hålls kvar tills
  tidsbudgetens hårda gräns avbryter jobbet (ADR-0088); en egen gräns per
  hämtning är inte infört.
* Bad, eftersom npm-paketens egna beroenden fortfarande kan komma i nyare
  versioner: låsfilen checkas inte in (ADR-0104), och inte heller pip har
  en låsfil för de transitiva beroendena. Det står i
  [#482](https://github.com/moggleif/kungsbackakommun/issues/482).

### Confirmation

`tests/test_hamtgranser.py` prövar https, sidtaket och filtaket mot en
lokal server, och `tests/test_yttak.py` att en för stor sida blir
`ej-konverterad` och att en A4 och en A0 ryms. `tests/test_yttak.py` prövar också att tolkningen renderar en för stor
sida mindre. PR-jobbets prövning kördes för hand mot en nattkörnings gren
och mot lokala grenar som ändrade data, tog bort data, ändrade koden,
flyttade kod in i `data/`, lade en symbolisk länk i `data/` och hade en
merge-commit; bara de två första släpptes igenom. CI-stegen "Externa actions fästa vid en commit" och "Inga binärer
utom små testfixturer" faller på en tagg respektive en PDF i roten.

## Pros and Cons of the Options

### A – Gränser där det hämtade och grenen passerar

* Good, eftersom varje gräns sitter på ett ställe: klienten, dokumentets
  sidslinga och PR-jobbet.
* Good, eftersom nattkörningen i övrigt är oförändrad.
* Bad, eftersom jobbet som läser PDF:erna fortfarande har skrivrätt till
  repot. En övertagen process kan pusha grenar, men de når inte `main`.

### B – Som A, med tillåtna värdar

* Good, eftersom klienten inte kunde nå någon annan värd än källornas.
* Bad, eftersom omdirigeringar redan inte följs och adaptrarna bara tar
  adresser som matchar plattformens mönster, så listan stänger ingen väg
  som A lämnar öppen. En PDF från en annan värd är inte farligare än en
  från kommunens.
* Bad, eftersom kommunfilerna, Wayback och kommande plattformar skulle
  behöva föra in värdar i klienten: en ny abstraktion för ett fall som
  inte finns.

### C – Läsa och pusha i skilda jobb

* Good, eftersom tolken aldrig skulle se en token med skrivrätt.
* Bad, eftersom nattkörningen sparar var femtonde minut (ADR-0088) och
  varje sparad del då skulle behöva ett eget jobb eller en egen
  artefakt; det är en omskrivning av körningen.
* Bad, eftersom A redan hindrar det som spelar roll, att koden når `main`.

## More Information

Agenten gick igenom punkterna i #348 en i taget. Underprocesserna
(`tesseract.py`, `riktning.py`) tar argumenten som listor utan skal, och
sökvägarna är tillfälliga filer som koden själv namnger; där fanns inget
att rätta. Varje dokument har redan en tidsgräns på 30 minuter (ADR-0075),
som också gränsar sidantalet i praktiken, och varje Tesseract-anrop fem
minuter. Webbplatsen renderar med
markdown-it-py med rå HTML avslagen, som också vägrar `javascript:`- och
`file:`-länkar, och skripten skriver ingen markup. `pip-audit .` löser
upp projektets beroenden med de transitiva och granskar alla.

Den oberoende granskningen (fas 6) fann två blockerande fel i PR-jobbets
första version: ett namnbyte från koden in i `data/` syntes bara under
det nya namnet, och utan `pipefail` släppte ett fel i `git diff` igenom
grenen, eftersom ett anropat workflow inte ärver anroparens `shell`. Båda
rättades och prövades som ovan, och granskningens förslag om symboliska
länkar och merge-commits togs med. Granskningen pekade också på att
`kalla_url` länkas på dokumentsidan utan kontroll av schemat; där går
länken genom `mall.lank`, som bara gör `https://` och `http://` till
länkar, så det behövde inte rättas. Ett trasigt `Content-Length` kraschar
inte längre läsningen av en sida.

Två saker kan agenten inte se och projektägaren kontrollerar i repots
inställningar: att `NATTKORNING_TOKEN` är en finkornig token för bara det
här repot, med *Contents* och *Pull requests* och ett utgångsdatum
([01-BIDRA.md](../01-BIDRA.md)), och att *Secret scanning* och *Push
protection* är påslagna under *Code security*.

Historiken söktes igenom efter token, nycklar och lösenord i alla 883
commits, utom poolens data. Inget hittades.

Invändningen mot yttaket var att en plankarta kan vara större än A0.
Svaret: Pillows egen gräns är vad renderingen annars skulle ha mött om
bilden öppnats av Pillow, och en sida över den blir märkt, inte borta.
Invändningen mot att pröva grenen i PR-jobbet var att `spara.sh` redan
gör det. Svaret: `spara.sh` körs i samma jobb som tolken och kan inte
skydda mot den.

Projektägaren bad att alla öppna issues körs och godkände på förhand att
agentens rekommendationer följs och att PR:erna mergas vid grön CI.
