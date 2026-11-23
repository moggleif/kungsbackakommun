---
status: "accepted"
date: 2026-11-23
decision-makers: projektägaren
consulted: AI-agenten
---

# CI håller målen i Ren kod för koden, och testerna behåller de högre gränserna

## Context and Problem Statement

"Ren kod – strikt" i `AGENTS.md` hade två tal per mått: ett mål (15 rader
per funktion, 150 per fil, 3 parametrar, nästling 2, komplexitet 5) och en
hård gräns på ungefär det dubbla, som CI höll. Målen prövades bara i
granskningen, och allt över dem listades med `--mal`, `mal.toml` och
`eslint.mal.config.mjs` (K76, K83). Refaktoriseringen i #347 har tagit
koden i `src/` och `scripts/` under målen, utom spårslagen i
`webbplats/sparslag.py` (240 rader), som #384 ska dela men som väntar
på #314. Utan en spärr växer listan tillbaka (#395). Ska CI hålla målen, med
eller utan marginal, och gäller det också testerna?

## Decision Drivers

* En ändring som går över ett mål utan skäl i koden ska falla i CI.
* Ett tal per mått och katalog: det som står i tabellen är det CI håller.
* Testerna mättes inte i #347; fem testfiler ligger på 240–250 rader och
  ett trettiotal över 150.
* Ingen kod för säkerhets skull: verktyg som inte längre behövs tas bort.

## Considered Options

* Målen blir gränsen i CI för koden, testerna behåller de högre gränserna
* Målen blir gränsen i CI med en liten marginal kvar
* Målen blir gränsen för koden och testerna
* Målen prövas som förut bara i granskningen

## Decision Outcome

Valt alternativ: "Målen blir gränsen i CI för koden, testerna behåller de
högre gränserna", eftersom det stoppar en ändring över målet utan att
kräva en refaktorisering av testerna, och undantaget med skäl redan är
vägen när en funktion verkligen behöver vara större.

Rader per fil sänks mått för mått, i den ordning listan töms, som #395
säger: för koden hålls den i CI vid 250 tills spårslagen har delats
(#384), och då sänks `KOD.fil` i `scripts/kontrollera_storlek.py` till
150. En fil får inget undantag, så `sparslag.py` behöver inget eget skäl
under tiden.

### Consequences

* Bra, eftersom tabellen i `AGENTS.md` är det CI håller, en kolumn för
  koden och en för testerna.
* Bra, eftersom `--mal`, `mal.toml` och `eslint.mal.config.mjs` tas bort
  (K76 ersätts av K87); det finns ingen lista att läsa när CI håller målen.
* Bra, eftersom de sista funktionerna över målen, i `kalibrering/`,
  `radlasning.py`, `skannad.py` och `sitevision_arkiv.py`, delades i
  samma ändring i stället för att få undantag.
* Dåligt, eftersom testerna har andra tal än koden, i `tests/ruff.toml`
  och i ESLints regel för `tests/**`.
* Dåligt, eftersom en ny fil i koden mellan 150 och 250 rader inte faller
  i CI förrän #384 är gjord; granskningen prövar den till dess.
* Neutralt, eftersom täckningens golv (ADR-0102) lämnas som det är; det
  omprövades och har inget med storleken att göra.

### Confirmation

`tests/test_kontrollera_storlek.py`, `ruff check .` med `pyproject.toml`
och `tests/ruff.toml`, och `npx eslint` med `eslint.config.mjs`, i
"Ren kod och tester" i `.github/workflows/kontroll.yml`.

## Pros and Cons of the Options

### Målen blir gränsen i CI för koden, testerna behåller de högre gränserna

* Bra, eftersom koden redan håller målen.
* Bra, eftersom testerna inte behöver delas för att spärren ska komma på.
* Dåligt, eftersom två uppsättningar tal finns.

### Målen blir gränsen i CI med en liten marginal kvar

* Bra, eftersom en funktion på 16 eller 17 rader går igenom utan undantag.
* Dåligt, eftersom målet och gränsen åter blir två tal, och marginalen blir
  det som i praktiken hålls.

### Målen blir gränsen för koden och testerna

* Bra, eftersom ett tal gäller överallt.
* Dåligt, eftersom ett trettiotal testfiler och femtio testfunktioner
  måste delas först, ett arbete som inte ingick i #347.

### Målen prövas som förut bara i granskningen

* Bra, eftersom inget ändras.
* Dåligt, eftersom det som #347 tog bort växer tillbaka.

## More Information

Issue #395 lämnade öppet om målet och gränsen ska vara samma tal och om
testerna ska hålla målen. AI-agenten rekommenderade samma tal utan
marginal för koden, eftersom undantaget med skäl redan finns, och de
högre gränserna för testerna, eftersom de inte ingick i mätningen
bakom #347. Projektägaren gav uppdraget att arbeta igenom #347 och godkände där
på förhand att agentens rekommendationer följs och att PR:erna mergas vid
grön CI. #370 och #384 hoppades över med flit; de är inte gjorda här.
