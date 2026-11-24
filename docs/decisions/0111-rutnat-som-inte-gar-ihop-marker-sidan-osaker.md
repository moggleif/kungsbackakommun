---
status: accepted
date: 2026-11-24
decision-makers: projektägaren
consulted: AI-agenten
---

# Ett rutnät som inte går ihop till en tabell märker sidan osäker

## Context and Problem Statement

Ett rutnät av linjer blir en säker tabell bara när varje ord inom dess
yta har sin mittpunkt i en cell
([ADR-0031](0031-ett-rutnat-utan-text-ar-ingen-tabell.md)). Går det inte ihop,
som när en kolumn saknar högerkant under rubrikraden, blir rutnätet
ingen tabell och texten läses som löptext, med kolumnerna ihopflätade
rad för rad. Sidan märks ändå `ok`. Bara siffror ur en tabell som
fällts för att en cell rymmer flera tal märker i dag sidan
([ADR-0016](0016-tabeller-utan-lodrata-linjer.md)). Så blev riskmatrisen i
Nämnden för Miljö & Hälsoskydds handlingar 2025-10-09, sidorna 22–27,
omärkt löptext där kolumnerna Risk, Sannolikhet, Konsekvens och Till
plan står om varandra
([#319](https://github.com/moggleif/kungsbackakommun/issues/319), följd
av [ADR-0087](0087-kanten-mellan-tva-cellrutor-ar-en-cellgrans.md)). Hur
ska en sådan sida märkas?

## Decision Drivers

* Data ska vara rätt eller märkt. Löptext med ihopflätade kolumner som
  märks `ok` är det fel som ser riktigt ut.
* Riskmatriser och liknande tabeller har ofta text utan siffror, så en
  regel som bara ser siffror missar dem.
* Sidor som i dag läses rätt ska inte märkas i onödan, och facit
  ([ADR-0025](0025-facit-for-konverteringen.md)) får inte bli sämre.
* Ingen ny gissning: den som läser sidan ska få veta att den är osäker,
  inte en tabell som ser säker ut.

## Considered Options

* A – Ett rutnät som inte går ihop märker sidan `tabell-osaker` när text
  ur det står kvar i sidans text
* B – Ett sådant rutnät räknas som en fälld tabell: bara siffror ur det
  märker sidan, och det prövas för delning
  ([ADR-0028](0028-tabeller-med-linjer-delas-efter-linjer-och-textrader.md))
* C – Laga rutnätet: dra ut den kortare kanten så att det går ihop, och
  läs det som en säker tabell
* D – Som i dag

## Decision Outcome

Valt: A, eftersom den märker just det fel som issuet beskriver, också
när texten saknar siffror, utan att gissa var en kant borde ha gått.

Ett rutnät går inte ihop när det har minst två rader och två kolumner
och ett ord inom dess yta har mittpunkten utanför varje cell. Står ett
tecken ur ett sådant rutnät, utom blanktecken, utanför de tabeller som
lästs, också de utan lodräta linjer, blir sidan `tabell-osaker`. Texten
står kvar i sidans text, som förut. Läses texten i stället som en tabell
utan lodräta linjer märker rutnätet inte sidan.

Poolens version höjs till 0.17.0. Den kan bara ändra sidor som var `ok`
([ADR-0107](0107-omkonvertering-efter-vad-versionen-kan-andra.md)), och
poolen rättas när den konverteras om
([#84](https://github.com/moggleif/kommunhandlingar/issues/84)).

### Consequences

* Bra, eftersom riskmatrisen 2025-10-09 märks `tabell-osaker` på
  sidorna 22–27, och dokumentet blir `text-utan-tabeller`.
* Bra, eftersom ingen sida som i dag är `ok` och läses rätt ändras i
  stickprovet, och facit står kvar på 16 rätt och 3 osäkra.
* Dåligt, eftersom en sida där bara en rubrik eller en fotnot råkar stå
  inom ett rutnäts yta, men utanför cellerna, också märks. Det är en
  märkning för mycket, inte ett fel i datat.
* Neutralt, eftersom rutnätet fortfarande inte blir någon CSV. Att läsa
  det som en tabell är ett annat arbete.

### Confirmation

`tests/test_rutnat.py` prövar när ett rutnät går ihop och när det inte
gör det, och sidorna i `tests/fixtures/pdf/rutnat.pdf`: en riskmatris
där kolumnen Till plan saknar högerkant under rubrikraden blir
`tabell-osaker`, och samma matris med kanten hela vägen blir en säker
tabell och `ok`. Facit ska inte bli sämre.

## Pros and Cons of the Options

### A – Text ur ett rutnät som inte går ihop märker sidan

* Bra, eftersom den täcker text utan siffror, som Ja och Nej i en
  riskmatris.
* Bra, eftersom regeln är en spegel av den som redan finns för en säker
  tabell: samma prov, motsatt utfall.
* Dåligt, eftersom ett rutnät som inte går ihop av andra skäl, som en
  ram där en rubrik sticker ut, också märker sidan.

### B – Rutnätet räknas som en fälld tabell

* Bra, eftersom den återanvänder vägen för fällda tabeller, med delning.
* Dåligt, eftersom bara siffror märker sidan, så riskmatrisen 2025-10-09
  förblir `ok`.
* Dåligt, eftersom delningen är byggd för celler med flera tal, inte för
  saknade kanter, och kan ge en CSV som ser säker ut men är fel.

### C – Laga rutnätet

* Bra, eftersom riskmatrisen kunde bli en tabell.
* Dåligt, eftersom var den saknade kanten ska gå är en gissning; en kant
  som saknas kan lika gärna betyda en sammanslagen cell.
* Dåligt, eftersom det är mer kod för ett fall i ett stickprov.

### D – Som i dag

* Bra, eftersom inget ändras.
* Dåligt, eftersom löptext med ihopflätade kolumner fortsätter att märkas
  `ok`.

## More Information

Issuet kom ur analysen av kolumner utan streck (ADR-0087), där
riskmatrisen gick från en trasig tabell med 5 kolumner till löptext. I
riskmatrisen har rubrikraden alla nio kolumnernas kanter, men raderna
under saknar högerkanten för Till plan, så Ja och Nej i den kolumnen står
inom rutnätets yta utan att ligga i någon cell.

Agenten övervägde att bara räkna rutnät med siffror, som för fällda
tabeller. Det föll eftersom felet i issuet är just text: kolumnerna
flätas ihop också när ingen siffra finns. Alternativ C avvisades för att
den gissar, och poolens grundregel är hellre märka än gissa.

Ett stickprov på 50 slumpvis valda handlingar från 2023–2026 som 0.16.0
konverterat, med 1 702 sidor, jämförde varje sidas kvalitet i poolen med
en ny konvertering. Ingen sida ändrades. I handlingarna 2025-10-09 ändras
bara sidorna 22–27, från `ok` till `tabell-osaker`.
