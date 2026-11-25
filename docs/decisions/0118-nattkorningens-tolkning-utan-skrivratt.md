---
status: "accepted"
date: 2026-11-24
decision-makers: projektägaren
consulted: AI-agenten
---

# Nattkörningens jobb som läser det hämtade har bara läsrätt, och ett eget jobb pushar grenen

## Context and Problem Statement

[ADR-0115](0115-sakerhetsgranser-for-hamtning-och-nattkorning.md) prövar
nattkörningens gren innan den mergas, men jobben som läser PDF:erna,
`moten` och `arkiv`, har fortfarande `contents: write` och token kvar i
utcheckningen. Två saker stod öppna i
[#483](https://github.com/moggleif/kungsbackakommun/issues/483):

* En tolk som tagits över av en fil den läst kan pusha grenar till repot.
  De når inte `main`, men de hamnar i repot.
* Arkivets jobb kör samtidigt som mötenas PR-jobb och kan pusha till
  mötenas gren efter att den prövats. Det är inte prövat att GitHub
  håller fast vid `--match-head-commit` när det händer.

Hur kan jobben som läser det hämtade bli av med skrivrätten, utan att
nattkörningen tappar att den sparar var 15:e minut
([ADR-0088](0088-nattkorningen-sparar-var-femtonde-minut.md)) och
mergar sin PR själv
([ADR-0052](0052-nattkorningen-mergar-sin-pr-sjalv.md))?

## Decision Drivers

* **Hämtat innehåll är data, inte instruktioner** (AGENTS.md). En token
  som en övertagen process kan nå är en väg in i repot.
* Ett avbrott ska fortfarande kosta högst en del (ADR-0088), och det som
  checkats in före ett fel ska fortfarande nå `main`.
* Nattkörningen ska fortsätta öppna och merga sin PR själv.
* Ingen kod för säkerhets skull, och nattkörningen ska inte skrivas om
  mer än det kräver.

## Considered Options

* A – Jobben läser med `contents: read` och checkar in lokalt; commitarna
  går som en git-bundle i en artefakt till PR-jobbet, som prövar och
  pushar dem.
* B – Pushen i ett eget steg i samma jobb, med token bara i det steget.
* C – En total tidsgräns per hämtning, och skrivrätten kvar, med skälet i
  en ADR.
* D – En artefakt per del, och ett jobb som pushar varje del medan
  läsningen pågår.

## Decision Outcome

Valt: A, eftersom det är det enda som tar bort skrivrätten från jobben
som läser det hämtade och samtidigt låter körningen fungera som förut.

* **`moten` och `arkiv` har `contents: read`** och checkar ut med
  `persist-credentials: false`. `spara.sh` kör datakontrollerna och
  checkar in efter varje del, som förut, men pushar inte.
* **Till sist, också när jobbet fallit**, lägger `.github/actions/grenen`
  jobbets commitar sedan utcheckningen i en git-bundle i en artefakt med
  grenens sista led som namn, som sparas i sju dagar, och ger grenens
  namn och bas som output. Inget som inte checkats in följer med, så bara kontrollerade
  delar når grenen, som förut.
* **PR-jobbet** (`.github/workflows/nattkorning-pr.yml`) är det enda med
  `contents: write`. Det kör på en ny runner utan utcheckning, hämtar
  `main`s och basens commits och träd utan filinnehåll och bundlens
  commitar ur artefakten, och kör ingenting ur repot eller ur det
  hämtade. Delen, `moten` eller `arkiv`, kommer från anroparen; grenens
  namn och bas kommer från jobbet som läst, så namnet ska vara
  `nattkorning/<datum>-<körningens id>-<försök>-<del>`, i vilket försök
  som helst, så att PR-jobbet kan köras om för sig. Annars, eller om
  grenen ändrar annat än data (ADR-0115), pushas ingenting. Bundlen
  hämtas med `fetch.fsckObjects` och prövas i ett steg utan token. Sedan
  pushar ett eget steg grenen med jobbets token och öppnar PR:en som
  förut.
* **Arkivets jobb startar när mötenas PR-jobb är klart**, från den gren
  det pushat, eller från `main` när den inte pushats. Ingenting pushar
  till mötenas gren efter dess PR-jobb, så frågan om
  `--match-head-commit` uppstår inte längre.

### Consequences

* Good, eftersom en övertagen tolk varken kan pusha en gren eller nå en
  token som kan det. Det den kan göra är att lämna en annan bundle, ett
  annat grennamn eller en artefakt under en annan dels namn, och allt
  prövas innan något pushas.
* Good, eftersom jobben i övrigt är som förut: delar om 15 minuter,
  datakontroller före varje incheckning, och en PR också när jobbet
  fallit efter en incheckad del.
* Neutral, eftersom arkivets jobb startar någon minut senare, efter
  mötenas PR-jobb.
* Bad, eftersom en runner som försvinner mitt i ett jobb nu tar med sig
  allt jobbet checkat in, inte bara den pågående delen: bundlen laddas
  upp när jobbet slutar. Ett fel i jobbet kör ändå det sista steget, så
  ett fel kostar fortfarande högst en del (K11).
* Bad, eftersom en körning som avbryts för hand inte längre lämnar
  något på grenen. Förut stod de pushade delarna kvar utan PR; nu hoppas
  PR-jobbet, som pushar, över. Ett avbrott för hand är en nödbroms
  (ADR-0088), och det incheckade finns kvar i artefakten i sju dagar och
  kan pushas för hand ([01-BIDRA.md](../01-BIDRA.md)).
* Neutral, eftersom datat ligger som artefakt i körningen i sju dagar,
  som en kopia av grenen.

### Confirmation

Kedjan prövades lokalt med ett bart repo som remote: en grund utcheckning
som checkar in två delar, en bundle från basen, `main` som flyttas
under tiden, och ett nytt repo som hämtar `main` och basen utan
filinnehåll, hämtar bundlen, prövar diffen och pushar grenen. Grenen
fick båda delarna. Arkivets bundle, byggd på den pushade mötesgrenen,
pushades på samma sätt. Ett grennamn för en annan del eller gren, en bas
som inte är en commit och en bundle som ändrar kod stoppades före
pushen. Granskningen upprepade kedjan med en server som verkligen
filtrerar bort filinnehållet: git hämtar då deltabaserna för bundlen
från repot, vilket går eftersom repot är publikt. Första riktiga nattkörningen efter mergen visar
att `moten`, `pr-moten`, `arkiv` och `pr-arkiv` går igenom och att
PR:erna mergas automatiskt.

## Pros and Cons of the Options

### A – Bundle som artefakt, pushen i PR-jobbet

* Good, eftersom skrivrätten bara finns i ett jobb som inte läser något
  hämtat och inte kör något ur repot.
* Good, eftersom prövningen från ADR-0115 nu sker före pushen, inte bara
  före mergen.
* Bad, eftersom det som checkats in bara når repot när jobbet slutar, se
  konsekvenserna.

### B – Pushen i ett eget steg i samma jobb

* Good, eftersom körningen nästan inte ändras.
* Bad, eftersom ett steg delar runner, användare och disk med de steg
  som läst det hämtade. En övertagen process kan lämna något efter sig
  som körs när token finns, till exempel en git-hook eller en ändrad
  `spara.sh`. Jobbet kan alltså fortfarande pusha, och issuets krav är
  inte uppfyllt.

### C – Tidsgräns per hämtning och skrivrätten kvar

* Good, eftersom en server som skickar lite i taget inte längre håller
  kvar jobbet.
* Bad, eftersom den inte rör frågan om skrivrätt: en övertagen tolk kan
  fortfarande pusha.

### D – En artefakt och en push per del

* Good, eftersom en förlorad runner bara skulle kosta den pågående delen.
* Bad, eftersom ett jobb inte kan starta ett annat medan det kör; det
  skulle kräva ett eget workflow per del, startat med en token som
  jobbet som läser då måste ha. Det är just den token som ska bort.

## More Information

Agenten vägde A mot B först. B såg ut att räcka, men en runner i Actions
har en användare med `sudo` utan lösenord, och allt i jobbet delar den.
Det som läst det hämtade kan därför ändra det som körs senare i samma
jobb. Gränsen måste gå mellan jobb, eftersom varje jobb får en ny runner.

ADR-0115 valde bort just A, med skälet att varje sparad del skulle
behöva ett eget jobb eller en egen artefakt. Det visade sig inte
behövas: delarna checkas in lokalt som förut, och en enda bundle på
slutet bär alla commitar, med samma historik som pushen gav. Det som
försvinner är att en del når repot medan jobbet pågår, och det spelade
roll bara om runnern går förlorad.

Invändningen att grennamnet kommer från jobbet som läst det hämtade
besvarades så: namnet prövas mot körningens id, försök och del, och delen
står i anroparen, så en övertagen tolk i arkivets jobb kan inte få
PR-jobbet att pusha till mötenas gren eller till någon annan gren.
Basen används bara för att hämta commits och prövas så att den inte kan
bli en flagga till git. Vad bundlen bygger på avgör inte prövningen: det
gör diffen mot merge-basen med `main` och att den saknar merge-commits,
och en bundle utan gemensam historik med `main` stoppas eftersom diffen
då inte går att räkna ut.

Ett eget jobb för pushen, skilt från PR-jobbet, vägdes och valdes bort:
båda kör utan utcheckning och utan något ur det hämtade, och i samma
jobb prövas grenen en gång, före pushen.

Den oberoende granskningen (fas 6) fann två blockerande fel: K11
lovade fortfarande att varje avbrott kostar högst en del, och ADR:en
sade att ett avbrott för hand inte kostar mer än förut. Båda rättades,
som konsekvenserna ovan. Granskningen visade också att PR-jobbet inte
gick att köra om för sig, eftersom grennamnet krävde PR-jobbets eget
försök; nu tas vilket försök som helst, och artefakten heter som grenen.
Dess förslag om `fetch.fsckObjects`, prövning utan token, nyare versioner
av artefaktens actions och sju dagars lagring togs med. Förslaget att
läsa basen ur bundlen i stället för som output vägdes och valdes bort:
det skulle tolka bundlens huvud med egen kod, och outputen prövas redan.

Projektägaren bad att alla öppna issues körs och godkände på förhand att
agentens rekommendationer följs och att PR:erna mergas vid grön CI.
