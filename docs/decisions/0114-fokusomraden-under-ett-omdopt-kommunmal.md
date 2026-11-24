---
status: proposed
date: 2026-11-24
decision-makers: projektägaren
consulted: AI-agenten
---

# Fokusområden står under kommunmålets spår också när budgeten skrev målet på ett annat sätt, och fullmäktiges äldre mål förs in

## Context and Problem Statement

Kommunfullmäktiges målsida
([ADR-0056](0056-kommunfullmaktiges-mal-med-fokusomraden-och-farg.md))
började 2022, eftersom poolen inte hade fullmäktiges äldre handlingar med
text. Nu har poolen budgetarna 2015, 2018, 2022 och 2023, årsredovisningarna
2016 och 2020–2022 och delårsrapporterna 2021–2023 med text
([#185](https://github.com/moggleif/kungsbackakommun/issues/185)).

De fem kommunövergripande målen gäller sedan budgeten 2018, men
budgeten 2018 skriver "Ett medskapande samhälle och öppen attityd" och
de senare dokumenten "… och en öppen attityd". Målet med den
äldre rubriken står i den nyares grupp
([ADR-0045](0045-omdopta-mal-grupperas-protokollet-gar-fore-och-status-blir-ikoner.md)).
Men ett fokusområdes huvudmål måste stå på källans sida och vara ett
kommunmål utan grupp, och samma fokusområde måste alltid ha samma
huvudmål. Budgetens fokusområden kan då inte få något huvudmål: den nya
rubriken står inte på budgetens sida, och den gamla har en grupp.

Hur ska fokusområdena under ett omdöpt kommunmål föras in?

## Decision Drivers

* **Varje uppgift bär sin härkomst**, och bygget prövar att huvudmålet
  står på källans sida.
* **Samma fokusområde ska gå att följa** genom åren under sitt mål.
* **Ingen kod för säkerhets skull**: det som behövs för det verkliga
  fallet, inget mer.

## Considered Options

* A – Huvudmålet får vara vilket kommunmål som helst i filen, och
  fokusområdet står under det målets spår
* B – Huvudmålet skrivs med den senaste rubriken, och prövas inte mot
  källans sida
* C – Budgetarna med den äldre rubriken lämnas utanför

## Decision Outcome

Valt: A, eftersom huvudmålet då står som i källan och fokusområdet ändå
hamnar under rätt mål.

* **Huvudmålet** är ett kommunmål i filen, med eller utan grupp.
  Läsningen sätter fokusområdets huvudmål till kommunmålets spår, så att
  tidslinjen och korten inte behöver veta om grupperna.
* **Samma fokusområde** ska alltid ha huvudmål i samma kommunmåls spår.
  Annars stoppas bygget och felet säger vilket fokusområde det gäller.
  Kontrollen görs när hela filen är läst, eftersom ett kommunmåls grupp
  kan stå på en senare rad.
* **Fullmäktiges äldre mål** förs in som kommunmål: de prioriterade målen
  i budgeten 2015 är egna spår, eftersom inget i källorna knyter dem till de
  fem målen från 2018.
* **En rubrik som bara skiljer sig med en avslutande punkt** står som i
  källan, i gruppen med den andra skrivningen, utan att vara tolkad.

### Consequences

* Good, eftersom fullmäktiges målsida går tillbaka till 2015.
* Bad, eftersom målsidan saknar det som poolen har men inte går att läsa
  säkert: ett mål och ett direktiv i årsredovisningen 2016 har rubriken
  delad mellan spalterna, och årsredovisningarna 2020–2022 blandar målens
  samlade bedömning med den andra spalten. Det står i issuet.
* Good, eftersom bygget fortfarande prövar varje huvudmål mot källan.
* Bad, eftersom felet för ett fokusområde med två huvudmål inte längre
  pekar på en rad i filen, bara på fokusområdet.
* Bad, eftersom en budget i två spalter, där konverteringen blandat
  spalterna, saknar de fokusområden vars text inte står sammanhängande;
  de kommer med när dokumenten konverteras om.

### Confirmation

`tests/test_omdopta_kommunmal.py` prövar att fokusområdet står under det
omdöpta målets spår, i läsningen och i tidslinjen, och att två spår eller
ett huvudmål som inte är ett kommunmål stoppar bygget.

## Pros and Cons of the Options

### A – Vilket kommunmål som helst, under dess spår

* Good, eftersom huvudmålet står som i källan.
* Bad, eftersom kontrollen av samma fokusområde måste vänta tills hela
  filen är läst.

### B – Den senaste rubriken som huvudmål

* Good, eftersom ingen kontroll ändras.
* Bad, eftersom huvudmålet inte längre går att pröva mot källans sida.

### C – Utan budgetarna med den äldre rubriken

* Good, eftersom ingen kod ändras.
* Bad, eftersom budgeten 2018 då inte står med.

## More Information

Projektägaren bad att issuet skulle göras med det poolen har. AI-agenten
läste färgerna ur PDF:erna i webbarkivet genom en tillfällig körning i
GitHub Actions, eftersom arkivet inte nås från molnmiljön.
