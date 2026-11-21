---
status: "accepted"
date: 2026-11-21
decision-makers: projektägaren
consulted: AI-agenten
---

# Täckningen mäts i CI med coverage, och kontrollen faller under ett golv

## Context and Problem Statement

Refaktoriseringen mot "Ren kod – strikt" (#347) flyttar mycket kod utan
att beteendet får ändras. Testernas täckning mättes inte, så en flytt som
tappar ett test syntes inte (#349). Hur ska täckningen mätas, och ska
kontrollen falla när den sjunker?

## Decision Drivers

* En flytt av kod som tappar ett test ska synas, helst stoppas.
* Kontrollen ska inte falla för att kod flyttas eller död kod tas bort.
* Standardbiblioteket först; ett nytt verktyg motiveras.
* Kontrollen ska inte bli märkbart långsammare.

## Considered Options

* coverage i CI, rapport i sammanfattningen och ett golv för totalen
* coverage i CI, bara rapport
* coverage med ett golv per modul
* standardbibliotekets `trace`

## Decision Outcome

Valt alternativ: "coverage i CI, rapport i sammanfattningen och ett golv
för totalen", eftersom det både syns per modul och stoppar ett tappat
test utan att fälla en ren flytt.

Golvet är 96 %, knappt en och en halv procentenhet under den uppmätta
totalen (97,4 % med Tesseract, 2026-11-21). Testissuerna under #347 höjer täckningen; golvet
höjs i samma ändring när det går.

### Consequences

* Bra, eftersom varje körning visar modulerna under 90 % först.
* Bra, eftersom ett tappat test för en modul av några hundra rader fäller
  kontrollen.
* Bra, eftersom rapporten skrivs också när ett test har fallit.
* Dåligt, eftersom ett nytt utvecklingsberoende tillkommer (coverage).
* Dåligt, eftersom testerna tar ungefär tio procent längre tid under
  mätningen.
* Neutralt, eftersom datakontrollens processpool nu stängs och väntas in
  i stället för att stoppas, så att arbetarnas mätning hinner sparas;
  resultatet är detsamma.

### Confirmation

Steget "Testerna, med täckningen i sammanfattningen" i
`.github/workflows/kontroll.yml` och `fail_under` i `pyproject.toml`.

## Pros and Cons of the Options

### coverage i CI, rapport i sammanfattningen och ett golv för totalen

* Bra, eftersom rapporten syns i varje körning.
* Bra, eftersom golvet stoppar en tydlig förlust.
* Dåligt, eftersom en liten förlust i en liten modul inte stoppas.

### coverage i CI, bara rapport

* Bra, eftersom kontrollen aldrig faller för täckningen.
* Dåligt, eftersom ingen läser sammanfattningen när kontrollen är grön.

### coverage med ett golv per modul

* Bra, eftersom varje modul skyddas.
* Dåligt, eftersom refaktoriseringen delar och flyttar moduler, och
  golven skulle behöva skrivas om i nästan varje ändring.

### standardbibliotekets `trace`

* Bra, eftersom inget nytt beroende behövs.
* Dåligt, eftersom den saknar grenar, sammanslagning av processer och en
  rapport i Markdown, som skulle behöva skrivas här.

## More Information

Issue #349 lämnade öppet om CI ska falla och under vilken gräns.
AI-agenten rekommenderade ett golv för totalen strax under den uppmätta
nivån, i hela procent: en invändning var att ett golv precis på nivån
fäller en ändring som bara tar bort testad, död kod, vilket #347
uttryckligen vill ha. En procentenhet motsvarar ungefär 75 satser och
grenar; marginalen är ungefär 105, mer än en liten modul. Projektägaren
gav uppdraget att arbeta igenom #347 och godkände där på förhand att
agentens rekommendationer följs och att PR:erna mergas vid grön CI.

Den första mätningen räknade inte datakontrollens arbetsprocesser:
`with Pool()` stoppar dem med `terminate`, och då hinner coverage inte
spara. Därför stängs poolen och väntas in innan den lämnas.

Beslutet omprövas när #395 låter CI hålla målen i "Ren kod – strikt".
