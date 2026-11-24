---
status: "accepted"
date: 2026-11-24
decision-makers: projektägaren
consulted: AI-agenten
---

# Hela beroendeträdet installeras ur incheckade låsfiler med hashar: `uv.lock` för Python och `package-lock.json` för npm

## Context and Problem Statement

Säkerhetsgenomgången i
[#348](https://github.com/moggleif/kungsbackakommun/issues/348)
([ADR-0115](0115-sakerhetsgranser-for-hamtning-och-nattkorning.md)) fann
att bara de direkta beroendena var låsta. `pip install -e .` och
`npm install` hämtade beroendenas egna beroenden i den senaste version
som passade, och setuptools, som paketet byggs med, likaså. En kapad
eller trasig version av ett transitivt paket kunde därför nå CI och
nattkörningen, vars gren når `main`, utan att något i repot ändrats.
`package-lock.json` checkades inte in, eftersom den bär
tredjepartspaketens konto- och sponsornamn, och en del av dem är
personnamn ([ADR-0104](0104-webbplatsens-skript-med-eslint-och-jsdom.md)).
Hur ska hela trädet installeras i kända versioner?
Issue [#482](https://github.com/moggleif/kungsbackakommun/issues/482).

## Decision Drivers

* Ingen ny version av något paket når en körning utan en ändring i repot
  som går genom CI.
* Varje fil som installeras prövas mot en hash, inte bara mot ett
  versionsnummer.
* Dependabot håller låsfilerna uppdaterade när ett direkt beroende byts
  eller ett paket i trädet har en känd sårbarhet.
* Inga personnamn i repot (AGENTS.md), utom där projektägaren gjort
  undantag.
* Så lite ny kod och nya verktyg som möjligt.

## Considered Options

* Python: `uv.lock`, som CI exporterar och installerar med
  `pip --require-hashes`
* Python: en `requirements`-fil med hashar ur `pip-compile`
* Python: pips egen `pylock.toml` (`pip lock`)
* npm: `package-lock.json` checkas in, med ett undantag från regeln om
  personnamn
* npm: ingen låsfil, men npm tar bara versioner publicerade före ett datum
  i `.npmrc` (`before`)
* npm: trädet lämnas olåst, som förut

## Decision Outcome

Valt alternativ för Python: "`uv.lock`, som CI exporterar och
installerar med `pip --require-hashes`", och för npm:
"`package-lock.json` checkas in, med ett undantag från regeln om
personnamn", eftersom de låser hela trädet med hashar och är de format
Dependabot håller uppdaterade själv.

* `uv.lock` checkas in. Den gäller alla plattformar och Python-versioner
  som `requires-python` tillåter, och har hashar för varje fil.
* setuptools står i gruppen `bygg` i `pyproject.toml`, så att också det
  paketet byggs med finns i låsfilen. Paketet byggs utan isolering,
  `--no-build-isolation`, med det setuptools som installerats ur låsfilen.
* Varje jobb som installerar paketet – kontrollen, nattkörningens båda
  jobb, webbplatsen och kalibreringen – gör det med den sammansatta
  actionen `.github/actions/installera`: `uv export --locked` skriver
  trädet med hashar till en tillfällig fil, `pip install
  --require-hashes --no-deps --only-binary :all:` installerar den, bara
  från hjul, så att inget byggs med byggberoenden utanför låsfilen, och
  `pip install --no-deps --no-build-isolation -e .` paketet. Actionen ger
  den exporterade filens sökväg som output. `--locked` gör att jobbet faller
  om `uv.lock` inte stämmer med `pyproject.toml`. uv hämtas med
  `astral-sh/setup-uv`, fäst vid en commit och en fast version av uv,
  utan cache. Dependabot följer också de sammansatta actionerna, så att
  setup-uv uppdateras; versionen av uv flyttas för hand när Dependabot
  låser om med en nyare uv och `--locked` därför faller.
* Kalibreringen av väg H körs också när bara `uv.lock` ändras, eftersom
  numpy, opencv och de andra paketen som väg H vilar på nu bara byts där.
* `pip-audit` granskar den exporterade filen, alltså exakt de versioner
  som installerats, i stället för att lösa upp beroendena på nytt.
* `package-lock.json` checkas in. CI installerar med `npm ci
  --ignore-scripts`, som faller om låsfilen inte stämmer med
  `package.json` och prövar varje pakets `integrity`.
* markdownlint-cli2 flyttar in i `package.json`, så att också Markdown-lint
  installeras ur låsfilen, i stället för med `npm install --global`.
* Dependabot följer `uv` i stället för `pip`, så att `pyproject.toml` och
  `uv.lock` uppdateras i samma PR. För npm uppdaterar den
  `package-lock.json`, som den gör när filen finns. Versionsuppdateringar
  gäller de direkta beroendena; ett paket längre ner i trädet flyttas när
  ett direkt beroende kräver det eller när det har en känd sårbarhet.
* AGENTS.md undantar `package-lock.json` från regeln om personnamn: filen
  återger paketens egen metadata, som `data/` återger källan.

Det här ersätter beslutet i ADR-0104 att inte checka in
`package-lock.json`; resten av ADR-0104 står kvar.

### Consequences

* Bra, eftersom en ny version av ett transitivt paket bara når CI och
  nattkörningen genom en ändring av en låsfil, som syns i en PR.
* Bra, eftersom varje installerad fil prövas mot sin hash, också
  setuptools och Markdown-lints paket.
* Bra, eftersom en ändring av ett beroende utan ny låsfil faller i CI i
  stället för att installera något annat än det som står i repot.
* Bra, eftersom `pip-audit` granskar det som faktiskt installeras.
* Dåligt, eftersom ett nytt verktyg, uv, behövs för att skriva och läsa
  `uv.lock`, och en ny extern action för att hämta det i CI. Den körs
  också i nattkörningen, vars gren når `main`, och i webbplatsens jobb,
  som publicerar på Pages.
* Dåligt, eftersom paketen längre ner i trädet står still mellan
  uppdateringarna av de direkta beroendena, utom när en sårbarhet är
  känd. Det är avsikten, men buggrättningar där kommer senare.
* Dåligt, eftersom versionen av uv i actionen inte följs av Dependabot.
* Dåligt, eftersom två låsfiler på tillsammans omkring 400 kB checkas in,
  och Dependabots PR:er blir större.
* Dåligt, eftersom `package-lock.json` bär konto- och sponsornamn som är
  personnamn, i ett paketscope och i sponsoradresser. Det
  är ett uttryckligt undantag i AGENTS.md.
* Dåligt, eftersom den som ändrar ett beroende för hand måste köra
  `uv lock` eller `npm install --package-lock-only` och checka in
  låsfilen ([docs/01-BIDRA.md](../01-BIDRA.md)).
* Dåligt, eftersom datarepona, som installerar en fast version av
  paketet (ADR-0080), inte omfattas: deras installation löser fortfarande
  upp de transitiva beroendena själv.

### Confirmation

CI-steget "Låsta beroenden" faller om `uv.lock` inte stämmer med
`pyproject.toml` eller om en hash inte stämmer, och `npm ci` om
`package-lock.json` inte stämmer med `package.json`. Det prövades för
hand genom att ändra en version i `pyproject.toml` utan att låsa om,
byta en hash i den exporterade filen och lägga till ett paket i
`package.json` utan ny låsfil; alla tre föll.

## Pros and Cons of the Options

### Python: `uv.lock`, som CI exporterar och installerar med `pip --require-hashes`

* Bra, eftersom filen gäller alla plattformar och Python-versioner, med
  hashar för varje fil.
* Bra, eftersom Dependabot har stöd för `uv` och uppdaterar
  `pyproject.toml` och `uv.lock` i samma PR.
* Bra, eftersom `uv export --locked` också prövar att låsfilen stämmer.
* Dåligt, eftersom uv är ett nytt verktyg i CI och lokalt.

### Python: en `requirements`-fil med hashar ur `pip-compile`

* Bra, eftersom pip installerar den direkt.
* Dåligt, eftersom pip-tools är ett nytt beroende, och filen gäller den
  plattform den kompilerades på om inte varje markör löses för hand.
* Dåligt, eftersom ingenting i CI prövar att filen stämmer med
  `pyproject.toml` utan att kompilera om den.

### Python: pips egen `pylock.toml` (`pip lock`)

* Bra, eftersom det är standardformatet (PEP 751) och inget nytt verktyg.
* Dåligt, eftersom pip ännu inte installerar från den, och Dependabot
  inte uppdaterar den.

### npm: `package-lock.json` checkas in, med ett undantag från regeln om personnamn

* Bra, eftersom `npm ci` prövar hela trädet mot hasharna och
  Dependabot sköter filen.
* Bra, eftersom ingen ny kod eller nytt verktyg behövs.
* Dåligt, eftersom filen bär personnamn i paketscope och sponsoradresser.

### npm: ingen låsfil, men npm tar bara versioner publicerade före ett datum i `.npmrc` (`before`)

* Bra, eftersom inga namn checkas in och trädet ändras bara när datumet
  flyttas.
* Dåligt, eftersom ingen hash prövas.
* Dåligt, eftersom varje Dependabot-PR med en nyare version faller tills
  datumet flyttas för hand.

### npm: trädet lämnas olåst, som förut

* Bra, eftersom ingenting ändras.
* Dåligt, eftersom en ny version av ett transitivt paket når CI utan att
  något i repot ändrats, det som #482 handlar om.

## More Information

Issue #482 lämnade frågan om npm till projektägaren. AI-agenten
kontrollerade först om låsfilen gick att rensa från namnen. Sponsorfälten
(`funding`) går att ta bort, men npm och Dependabot skriver tillbaka dem
vid nästa uppdatering, och ett paketscope som är ett personnamn står i själva
paketnamnet och i adressen till paketet, så det går inte att ta bort.
Agenten lade fram tre alternativ – undantag, datum i `.npmrc` eller
olåst – och rekommenderade undantaget, eftersom det ger hashar för hela
trädet med minst kod och Dependabot sköter filen själv. Projektägaren
valde undantaget.

För Python vägde agenten pip-tools mot uv. Avgörande var att `uv.lock`
gäller alla plattformar och att Dependabot uppdaterar `pyproject.toml`
och `uv.lock` tillsammans, medan en kompilerad `requirements`-fil måste
låsas om för hand vid varje Dependabot-PR för `pyproject.toml`. Pip
installerar fortfarande, så att paketen hamnar i samma Python som förut
och resten av jobben inte ändras; uv läser bara låsfilen. setuptools
lades till som en grupp i stället för i `[build-system]`, eftersom
uv inte låser byggberoenden, och `--no-build-isolation` gör att pip inte
hämtar ett eget setuptools vid bygget. En invändning var att setup-uv är
ännu en extern action; den fästs vid en commit som de andra
(ADR-0115), och uv själv vid en version.

Den oberoende granskningen (fas 6) föreslog en enklare väg: checka in den
exporterade filen med hashar, låta alla jobb installera den med pip och
bara kontrollen pröva den mot `uv.lock` med uv. Då behövs uv i ett jobb i
stället för fem. Agenten valde bort det, eftersom Dependabot bara
uppdaterar `pyproject.toml` och `uv.lock`, så varje Dependabot-PR skulle
falla tills filen exporterats om för hand. Granskningen fann också att
ADR:en lovade mer av Dependabot än den gör, att kalibreringen inte
startade på `uv.lock`, att setup-uv inte följdes av Dependabot, att
pip-audit berodde på actionens interna filnamn och att paket utan hjul
skulle byggas med olåsta byggberoenden; allt det rättades.
