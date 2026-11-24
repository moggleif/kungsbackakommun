---
status: "accepted"
date: 2026-11-24
decision-makers: projektägaren
consulted: AI-agenten
---

# Diarienumret efter etiketten läses också med förledet två gånger

## Context and Problem Statement

Sammanträdessidorna för Vård & Omsorg 2026 (K54) hittade handlingen för
bara 19 av 175 punkter. Tjänsteskrivelserna skriver numret på raden efter
`Diarienummer` med förledet två gånger, `VO VO-2026-00191`, och ibland med
mellanslag kring förledets bindestreck, `VO- 2026-00017`. Den delade
tolkningen efter etiketten (`diarienummer.MED_ETIKETT`, ADR-0071) läste
inte de formerna (#289). Mätningen mot poolen visade samma former hos
förvaltningarna för Individ & Familj, Teknik, Service och andra, och
`KS -2025-00357` med mellanslaget före bindestrecket. Hur ska tolkningen
läsa dem utan att läsa fel nummer någon annanstans?

## Decision Drivers

* Tolkningen är delad: protokollens paragrafer och `arenden` (ADR-0071)
  och handlingens sidor (ADR-0078) läser med samma uttryck.
* Hellre märka än gissa: ett nummer som inte går att läsa säkert ska inte
  bli ett annat nummer.
* Inget nummer som läses i dag får ändras eller försvinna.

## Considered Options

* Hoppa över ett förled bara när samma förled följer direkt efter
* Hoppa över vilket ord i versaler som helst före ett förled och en siffra
* Skriv om tjänsteskrivelsens rad före tolkningen, bara i `punktsidor.py`

## Decision Outcome

Valt alternativ: "Hoppa över ett förled bara när samma förled följer
direkt efter", eftersom det läser förvaltningarnas form och inget annat.

* Efter etiketten får ett förled om en till fem versaler och ett mellanslag
  stå före numret, om numret börjar med samma förled (`VO VO-2026-00191`).
  Numret blir `VO-2026-00191`.
* Förledets bindestreck får ha mellanslag före och efter (`VO- 2026-00017`,
  `KS -2025-00357`), och det blir ett bindestreck som förut. Ett snedstreck
  med mellanslag efter (`KKL/ 24`) läses inte, som förut.
* `diarienummer.efter_etikett` ger numren efter etiketten. Paragraferna
  och handlingens sidor anropar den i stället för att läsa uttrycket själva.

### Consequences

* Bra, eftersom fler punkter på sammanträdessidorna 2026 får sin handling:
  Vård & Omsorg 89 av 175 i stället för 19, Teknik 43 i stället för 41,
  och Miljö & Hälsoskydd, Förskola & Grundskolas arbetsutskott och
  valnämnden en var till. De 86 punkter som Vård & Omsorg saknar har ingen
  tjänsteskrivelse med numret i handlingarna, utom någon enstaka där
  numret bara står i en uppräkning.
* Bra, eftersom 23 punkter som redan hade en handling får ett kortare och
  riktigare intervall: nästa punkts tjänsteskrivelse känns nu igen, så att
  handlingen inte längre sträcker sig över den (17 i Vård & Omsorg, två i
  Förskola & Grundskola, två i Teknik, en i arbetsutskottet och en i
  valnämnden). Till exempel går Vård & Omsorgs punkt 4 den 11 juni från
  sidorna 3–35 till 1–6.
* Bra, eftersom ingen av poolens 71 570 tidigare träffar efter etiketten
  ändras eller försvinner, 475 tillkommer, och ingen `arenden` i
  protokollen ändras.
* Neutralt, eftersom ett nummer som delats över två rader (`KFT KFT-2024-`
  och `00319`, `KS -2025-` och `00357`) läses till radbrytningen, som när
  förledet står en gång utan mellanslag.
* Dåligt, eftersom uttrycket blir längre; namnen `FORLED` och `DUBBLERAT`
  säger vad delarna gör.

## Pros and Cons of the Options

### Hoppa över ett förled bara när samma förled följer direkt efter

* Good, eftersom det inte kan läsa ett annat nummer än det som står.
* Bad, eftersom ett förled som dubbleras med ett annat förled, eller som
  står på en egen rad, inte läses; inget sådant finns i poolen.

### Hoppa över vilket ord i versaler som helst före ett förled och en siffra

* Good, eftersom uttrycket blir kortare.
* Bad, eftersom det läste `III R13` som `R13` i en lantmäteriförrättning i
  KS och `LS SLE0L4E` ur en skannad sida i VO. Mätningen mot poolen visade
  felen.

### Skriv om tjänsteskrivelsens rad före tolkningen, bara i `punktsidor.py`

* Good, eftersom protokollen inte berörs alls.
* Bad, eftersom samma nummer då läses olika i handlingen och i
  protokollet, och tolkningen inte längre är delad.

## More Information

Issue [#289](https://github.com/moggleif/kommunhandlingar/issues/289).
Projektägaren bad att ändringen görs i den delade tolkningen och prövas mot
alla organ. AI-agenten mätte alla träffar efter etiketten i hela poolen
före och efter, och punkternas handlingar för alla organ 2026. Den första
versionen hoppade över vilket ord i versaler som helst och tillät
mellanslag efter snedstrecket; mätningen visade felaktiga nummer, och
regeln snävades in till samma förled.

Granskningen (fas 6) visade att den första texten här missade
arbetsutskottet, valnämnden och de ändrade intervallen, att formen finns
hos fler förvaltningar än Vård & Omsorg, och att hela nummer som
`KS -2025-00357` och `IF -2024-00227` inte lästes. Mellanslaget före
förledets bindestreck togs därför med.

Poolens version höjs inte: texten ändras inte, och `arenden` blir
detsamma (`python -m kommunhandlingar.arenden data` ändrar inget
dokument).
