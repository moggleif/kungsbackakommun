---
status: "accepted"
date: 2026-11-25
decision-makers: projektägaren
consulted: AI-agenten
---

# Kommunfilen prövas med kommandot `python -m kommunhandlingar.konfiguration`

## Context and Problem Statement

Region Hallands repo prövar sin kommunfil i kontrollen på varje PR med
en enradare i arbetsflödet, `python -c "… from
kommunhandlingar.konfiguration import las; las(Path(sys.argv[1]))"`
([regionhalland #65](https://github.com/moggleif/regionhalland/issues/65)).
Det är Python inbäddad i YAML, och ett fel i kommunfilen syns som en
traceback. Gränssnittet mot datarepon har kommandon för upptäckt,
hämtning, datakontroll och webbplats, men inget som bara läser och prövar
kommunfilen
([#516](https://github.com/moggleif/kungsbackakommun/issues/516)).

Hur prövar ett datarepo sin kommunfil med ett kommando ur paketet, med
samma läsning som körningen gör?

## Decision Drivers

* Samma prövning som körningen: kommunfilen läses med `las`, som stoppar
  körningen innan något hämtas (K1).
* Ingen Python i datarepots arbetsflöde, och ett fel som går att läsa.
* Kommandot är gränssnitt och ska inte flyttas tyst (K74).
* Den kortaste läsbara lösningen; ingen ny abstraktion.

## Considered Options

* Kommandot i `konfiguration.py`: `python -m kommunhandlingar.konfiguration <kommunfil> …`
* En egen modul, till exempel `python -m kommunhandlingar.kommunfil <kommunfil> …`
* En flagga till upptäckten, `upptack <kommunfil> --bara-kommunfilen`
* Datakontrollen prövar också `kommuner/*.toml`
* Enradaren står kvar i datarepot

## Decision Outcome

Valt alternativ: "Kommandot i `konfiguration.py`", eftersom modulen redan
äger läsningen och schemat, namnet säger vad som prövas, och ändringen är
en funktion på några rader. Kommandot tar en eller flera kommunfiler, så
att arbetsflödet kan ge det `kommuner/*.toml` utan en slinga.

### Consequences

* Bra, eftersom datarepot får ett steg på en rad utan Python, och ett fel
  står som "Stoppad: ", filen och felet.
* Bra, eftersom prövningen är densamma som körningens: `las` och inget
  annat.
* Bra, eftersom kommandot låses i `tests/test_granssnitt.py` och inte kan
  byta namn utan att ett test faller.
* Dåligt, eftersom `konfiguration.py` både tolkar och har en sidoeffekt
  på kommandoraden. Det är samma mönster som `datakontroll.py`,
  `upptack.py` och `hamta.py`.
* Neutralt, eftersom kommandot inte läser `hamtning.toml` eller når nätet:
  det prövar bara det `las` prövar.

### Confirmation

`tests/test_konfiguration_kommando.py` kör kommandot mot giltiga och
felaktiga kommunfiler, och `tests/test_granssnitt.py` kör det som ett
datarepo gör (K110, K74).

## Pros and Cons of the Options

### Kommandot i `konfiguration.py`

* Bra, eftersom läsningen, schemat och kommandot står på ett ställe.
* Bra, eftersom namnet är det som redan står i datarepots enradare.
* Dåligt, eftersom tolkning och kommandorad delar modul.

### En egen modul

* Bra, eftersom tolkningen hålls skild från kommandoraden.
* Dåligt, eftersom en fil till bara anropar `las`, och namnet måste läras
  in vid sidan av `konfiguration`.

### En flagga till upptäckten

* Bra, eftersom inget nytt kommando tillkommer.
* Dåligt, eftersom upptäckten kräver en arbetskatalog och läser
  `hamtning.toml`, och en flagga som hoppar över allt den gör blandar två
  ansvar.

### Datakontrollen prövar också `kommuner/*.toml`

* Bra, eftersom datarepot redan kör den.
* Dåligt, eftersom den tar katalogen `data/` och prövar poolens filer;
  kommunfilerna ligger bredvid, och argumentet skulle behöva ändras för
  alla som anropar den, Kungsbackas nattkörning också.

### Enradaren står kvar i datarepot

* Bra, eftersom inget ändras här.
* Dåligt, eftersom Python står kvar i YAML, felet är en traceback, och
  ett namnbyte på `las` syns först när datarepot höjer sin version.

## More Information

Behovet kom ur Region Hallands refaktorisering av arbetsflödena
([regionhalland #56](https://github.com/moggleif/regionhalland/issues/56)),
där projektägaren valde att kommandot byggs här i stället för att
enradaren skrivs om i datarepot.

AI-agenten rekommenderade kommandot i `konfiguration.py`. Invändningen
var att modulen då får en sidoeffekt. Svaret var att funktionen är liten
och skild från `las` och `tolka`, och att poolens andra kommandon har
samma form. En egen modul vore värd det först om kommandot ska göra mer
än att läsa filen, till exempel pröva `hamtning.toml`; det har inget
datarepo bett om.

Kommandot fångar bara `Konfigurationsfel` och `tomllib.TOMLDecodeError`,
de två fel som säger att filen inte följer schemat. En fil som inte finns
ger som förut ett fel från Python.

Importen `from kommunhandlingar.konfiguration import las` står kvar i
gränssnittet; den används av andra än Region Hallands kontroll.
