---
status: accepted
date: 2026-11-24
decision-makers: projektägaren
consulted: AI-agenten
---

# Dokumenten i sökindexet, och hela texten söks på GitHub

## Context and Problem Statement

[#67](https://github.com/moggleif/kungsbackakommun/issues/67) vill att
det går att söka i poolens dokument på webbplatsen och komma till
träffen, med härkomst och kvalitet synliga. Sedan issuet skrevs har
knappen *Sök* i sajtraden fått ett index över protokollens paragrafer
([ADR-0089](0089-sokindex-over-protokollens-paragrafer.md)), och
webbplatsen har skript på flera sidor, så
[ADR-0012](0012-webbplatsen-byggs-i-actions-och-publiceras-pa-pages.md)
hindrar inte längre. Men handlingarna och kallelserna har inga
paragrafer och finns inte i indexet, och ord inne i texten hittas inte.
Hur ska dokumenten bli sökbara?

## Decision Drivers

* Ingen server och inget externt i webbläsaren.
* Webbplatsen ska rymmas under GitHub Pages tak på 1 GB. Den är redan
  178 MB packad, och regionens bilagor visar bara härkomsten av samma
  skäl ([ADR-0080](0080-meetings-plus-las-motessidorna-nyast-forst.md)).
* Det som hämtas ska gå att hämta på en mobil.
* Den som söker ska se om ett dokument är osäkert innan det öppnas.

## Considered Options

* Dokumenten i sökindexet och en länk till fulltextsök på GitHub
* Bara en länk till fulltextsök på GitHub
* Fulltextindex i webbläsaren med Pagefind, per organ eller år
* Vänta på en egen server
  ([#18](https://github.com/moggleif/kungsbackakommun/issues/18))

## Decision Outcome

Valt alternativ: "Dokumenten i sökindexet och en länk till fulltextsök
på GitHub", eftersom dokumenten då hittas från samma knapp som
paragraferna utan att webbplatsen växer märkbart, och fulltexten finns
redan sökbar i repot.

Varje dokument blir en post i en egen grupp per kommun, *Dokumenten i*
och kommunens namn, med typ och namn, organ, datum och kvalitet, och
sidorna med obekräftade tal och osäkra tabeller räknade, med samma
text som organets sida, som nu också räknar de osäkra tabellerna. Kommunens
översikt länkar till GitHubs kodsökning med repot och kommunens mapp
ifyllda.

### Consequences

* Bra, eftersom handlingar och kallelser hittas på organ, typ och datum,
  och planernas och utredningarnas handlingar på sitt namn.
* Bra, eftersom ett osäkert dokument syns som osäkert redan i träfflistan.
* Bra, eftersom indexet växer med omkring 5 000 poster för Kungsbacka,
  någon megabyte, och regionhalland får samma grupp med nästa kodversion.
* Dåligt, eftersom de flesta dokumenten saknar namn: en träff på
  handlingarna säger bara organ och datum, inte vad som står i dem.
* Dåligt, eftersom GitHubs kodsökning kräver inloggning, bara söker i
  `main` och visar Markdown-filen, inte dokumentets sida.
* Dåligt, eftersom GitHub inte söker i filer över 350 kB: 357 av
  Kungsbackas 5 236 dokument, de största handlingarna. Länken säger det.

### Confirmation

`tests/test_sokdokument.py` bygger en liten pool och läser gruppen i
`sok.json`. `tests/test_navigering.py` prövar länken på översikten.

## Pros and Cons of the Options

### Dokumenten i sökindexet och en länk till fulltextsök på GitHub

* Bra, eftersom det är litet och använder formatet som redan finns.
* Dåligt, eftersom ord inne i texten hittas bara på GitHub.

### Bara en länk till fulltextsök på GitHub

* Bra, eftersom det är minst kod.
* Dåligt, eftersom handlingarna och kallelserna fortfarande inte hittas
  från knappen *Sök*, och kvaliteten inte syns förrän dokumentet öppnas.

### Fulltextindex i webbläsaren med Pagefind, per organ eller år

* Bra, eftersom varje ord hittas på webbplatsen och leder till sidan.
* Dåligt, eftersom mätningen i oktober gav omkring 100 MB index per 1 600
  dokument. För dagens 5 236 dokument blir det runt 330 MB, mer än
  webbplatsen själv packad, och poolen växer.
* Dåligt, eftersom det blir ett nytt verktyg i bygget.

### Vänta på en egen server

* Bra, eftersom en server kan söka i hela texten utan att något hämtas
  till webbläsaren.
* Dåligt, eftersom ingenting blir sökbart nu.

## More Information

I fas 0 visade AI-agenten att sökningen i ADR-0089 bara når protokollens
paragrafer och att ett fulltextindex inte ryms på Pages. Projektägaren
valde dokumenten i indexet och länken till GitHub. Fulltext på
webbplatsen prövas igen med en egen server (#18).
