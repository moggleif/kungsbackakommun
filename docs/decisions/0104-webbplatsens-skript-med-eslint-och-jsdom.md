---
status: "accepted"
date: 2026-11-21
decision-makers: projektägaren
consulted: AI-agenten
---

# Webbplatsens skript kontrolleras med ESLint och prövas i jsdom mot ögonblicksbilden

## Context and Problem Statement

Webbplatsens tre skript, `kalender.js`, `mal.js` och `perspektiv.js`,
bäddas in i sidorna men kontrolleras inte av något i CI. "Ren kod –
strikt" mäts bara för Python, och Python-testerna ser att skripten står
på sidan, inte att de gör rätt (#359). Hur ska skripten hållas mot samma
gränser, och hur ska det de räknar och väljer prövas, utan att de ändras?

## Decision Drivers

* Samma gränser som för Python, hårda i CI och målen listade.
* Skripten ska prövas som de är; beteendet får inte ändras (#347).
* Testerna ska köra på riktiga sidor, inte på påhittad markup.
* Få nya verktyg, och inget som laddar ner en webbläsare i varje körning.

## Considered Options

* ESLint, och Nodes testkörare med jsdom på ögonblicksbildens sidor
* ESLint, och Chromium genom Playwright, som systerrepot `politik`
* ESLint, och den rena logiken lyft ur skripten och prövad i Node
* Ingen lint, bara Python-tester som letar i skriptens text

## Decision Outcome

Valt alternativ: "ESLint, och Nodes testkörare med jsdom på
ögonblicksbildens sidor", eftersom det prövar skripten oförändrade på de
sidor bygget faktiskt skriver, med tre små utvecklingsberoenden och
utan webbläsare.

ESLint får reglerna `max-lines-per-function`, `max-lines`, `max-params`,
`max-depth` och `complexity` med gränserna ur AGENTS.md, och sina
rekommenderade felkontroller. Versionerna står exakt i `package.json`.
`package-lock.json` checkas inte in: den bär tredjepartspaketens
konto- och sponsornamn, och en del av dem är personnamn, som inte får
stå i repot (AGENTS.md). Som Markdown-lint, som också installeras utan
låsfil, kan därför paketens egna beroenden komma i nyare versioner.

### Consequences

* Bra, eftersom ett skript som växer över gränserna stoppas i CI, som
  Python-koden.
* Bra, eftersom testerna läser ögonblicksbilden (K78), så att en ändring
  av sidornas markup som skriptet beror på syns i båda.
* Bra, eftersom skripten inte behövde ändras.
* Dåligt, eftersom beroendenas beroenden inte är låsta, så en körning
  kan få en nyare version av dem än den förra.
* Dåligt, eftersom tre nya utvecklingsberoenden tillkommer (eslint,
  `@eslint/js` och jsdom) och ett andra pakethanterarsystem, npm, med
  Dependabot.
* Dåligt, eftersom jsdom inte är en webbläsare: det som beror på layout
  eller stil prövas inte, och jsdom navigerar till ett ankare senare än
  en webbläsare, så testerna väntar på händelsen.
* Neutralt, eftersom ögonblicksbilden saknar några fall, som ett bytt
  mål, och testerna då ändrar sidan innan skriptet körs.

### Confirmation

Stegen för skripten i `.github/workflows/kontroll.yml`, testerna i
`tests/js/` och `eslint.config.mjs`.

## Pros and Cons of the Options

### ESLint, och Nodes testkörare med jsdom på ögonblicksbildens sidor

* Bra, eftersom skripten körs som de är, på riktiga sidor.
* Bra, eftersom Node redan används i CI och testkörare och `assert`
  finns i standardbiblioteket.
* Dåligt, eftersom jsdom avviker från en webbläsare i detaljer.

### ESLint, och Chromium genom Playwright, som systerrepot `politik`

* Bra, eftersom det är en riktig webbläsare.
* Dåligt, eftersom Chromium laddas ner och installeras i varje körning,
  och ett tyngre beroende tillkommer för tre små skript som inte rör
  layouten.

### ESLint, och den rena logiken lyft ur skripten och prövad i Node

* Bra, eftersom inget DOM-bibliotek behövs.
* Dåligt, eftersom skripten bäddas in utan moduler och skulle behöva
  ändras för att dela kod med ett test, och det mesta de gör är att visa
  och dölja i sidan, som inte prövas så.

### Ingen lint, bara Python-tester som letar i skriptens text

* Bra, eftersom inget nytt verktyg behövs.
* Dåligt, eftersom gränserna inte mäts och beteendet inte prövas.

## More Information

Issue #359 lämnade öppet om testerna skulle köra lyft logik i Node eller
sidorna i en webbläsare. AI-agenten prövade först om logiken gick att
lyfta ut, men av det skripten räknar är bara `tvasiffrigt` och urvalets
`passar` rena funktioner; resten är att visa och dölja delar av sidan.
En invändning mot jsdom var att det inte är en webbläsare; svaret var att
skripten bara använder DOM, adressen och historiken, som jsdom har, och
att vägen till Chromium står öppen om ett skript börjar bero på layouten.
Granskningen (fas 6) fann personnamn i `package-lock.json`, i
paketscope och sponsoradresser. Agenten valde att inte checka in
låsfilen, som för Markdown-lint, i stället för att be om ett undantag
från regeln om personnamn. Testerna prövades genom att ändra skripten på tolv sätt, ett i taget,
och varje ändring fällde ett test. Projektägaren gav uppdraget att
arbeta igenom #347 och godkände där på förhand att agentens
rekommendationer följs och att PR:erna mergas vid grön CI.
