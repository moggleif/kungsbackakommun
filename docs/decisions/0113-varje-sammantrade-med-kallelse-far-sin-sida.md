---
status: "accepted"
date: 2026-11-24
decision-makers: projektägaren
consulted: AI-agenten
---

# Varje sammanträde med kallelse får sin sida, i alla organ och alla år

## Context and Problem Statement

Sammanträdets sida punkt för punkt (ADR-0078, K54) prövades först på
kommunstyrelsen 2026 och sedan på alla organ 2026. Vilka sammanträden som
fick sidan stod i kommunfilen, `sammantradessidor` med första året per
organ. Kvar i [#283](https://github.com/moggleif/kommunhandlingar/issues/283)
var de äldre åren: poolen har kallelser från 2013. Ska alla år få sidan,
och ska kommunfilen fortfarande styra vilka?

## Decision Drivers

* **Den kortaste läsbara lösningen vinner.** Fältet behövdes bara för att
  pröva formen i liten skala.
* **Hellre märka än gissa.** En äldre kallelse som inte går att läsa, eller
  ett sammanträde utan handlingar, ska säga det på sidan.
* **Webbplatsen ryms på GitHub Pages**, högst 1 GB.

## Considered Options

* A – Varje sammanträde med kallelse får sidan, och fältet tas bort.
* B – Fältet står kvar, med det första året i poolen för varje organ.
* C – Bara kommunstyrelsen får äldre år.

## Decision Outcome

Valt: A. Varje sammanträde med en kallelse i poolen får sin sida, i alla
organ och alla år. `sammantradessidor` tas bort ur kommunfilen och ur
koden. Ett sammanträde utan kallelse, som revisionens och de äldsta
utan kallelse i poolen, får ingen sida; organets sida listar dess dokument
som förut. Två saker i äldre kallelser läses nu:

* Rubriken slutar också vid `Klockan 13.00-13.30`, `(kl. 14.10-14.20)`,
  `Tid: 19:30 – 19:45`, `ca 13.00-15.00` och `Kl.14.00-14.05`, så att föredragningens tid
  och föredragandenas namn efter den inte står i rubriken.
* Tomt är inte noll: ett sammanträde utan handlingar i poolen säger
  det, handlingar som finns men inte gick att hämta eller läsa säger det,
  och en kallelse som inte gick att hämta säger det, i stället för
  "Handlingen hittades för 0 av …" eller "Dagordningen gick inte att
  läsa".

### Consequences

* Good, eftersom en kodrad, ett fält i kommunfilen och dess test försvinner.
* Good, eftersom en ny kommun får sidorna utan att ange något.
* Bad, eftersom de äldsta kallelserna är svårare att läsa: 232 av 1 487
  sidor säger att dagordningen inte gick att läsa och 5 att kallelsen
  inte gick att hämta. 255 sammanträden har inga handlingar i poolen och
  101 har handlingar som inte gick att hämta eller läsa. Handlingen hittas
  för omkring en tredjedel av punkterna, mot omkring sju av tio för
  kommunstyrelsen 2021–2026.
* Bad, eftersom föredragandens namn fortfarande kan stå i rubriken när en
  äldre kallelse skriver det utan etikett före tiden: 38 av 19 915 punkter
  har kvar ett klockslag i rubriken.

### Confirmation

`tests/test_sammantradessida.py` prövar att ett äldre sammanträde med
kallelse får sin sida och säger att handlingarna saknas, och
`tests/test_dagordning.py` de äldre formerna för klockslaget. Hela
webbplatsen byggdes och mättes före PR:en.

## Pros and Cons of the Options

### A – Varje sammanträde med kallelse, fältet borttaget

* Good, eftersom regeln är en rad: sammanträdet har en kallelse.
* Bad, eftersom ett organ inte kan välja bort sidorna utan en kodändring;
  inget sådant fall finns.

### B – Fältet kvar, med första året i poolen

* Good, eftersom en kommun kan välja år.
* Bad, eftersom fältet då skulle stå på varje organ med samma innebörd som
  att det saknades.

### C – Bara kommunstyrelsen får äldre år

* Good, eftersom kommunstyrelsens kallelser är de som läses bäst.
* Bad, eftersom nämndernas sammanträden då saknar sidan, fast deras
  kallelser läses lika bra som kommunstyrelsens från 2021.

## More Information

Fas 0 för #283 föreslog alla organ och alla år på en gång. Projektägaren
valde först bara årets sammanträden (tillägget i ADR-0078) och bad
2026-11-24 att resten görs.

Storleken mättes på hela poolen: webbplatsen var 703 MB med 168
sammanträdessidor och blir 754 MB med 1 487, i genomsnitt 49 kB per sida.
Gränsen att stanna vid var 900 MB. Stilen bäddas fortfarande in i varje
sida (`inbaddning.py`), omkring 7 kB per sida; att flytta den till en
gemensam fil behövs inte än.

Ett kommande sammanträde utan kallelse i poolen får ingen tom sida.
Kalendern länkar då som förut till kommunens mötessida, som har mer, och
nattkörningen hämtar kallelsen när den kommer (K56).

Tillägg 2026-11-24, samma dag som PR:en mergades: projektägaren såg
sidorna och valde att bara 2026 och framåt ska ha dem. De äldre sidorna
var ofta ofullständiga, och historiken på en aktuell punkt når de gamla
paragraferna ändå, eftersom den länkar till protokollen och inte till de
gamla sammanträdessidorna. Kommunfilen fick därför fältet
`sammantradessidor` igen, men en gång för hela kommunen i stället för per
organ: Kungsbacka har `sammantradessidor = 2026`, och en kommun utan
fältet får sidan för alla år enligt beslutet ovan. Webbplatsen har då
omkring 170 sammanträdessidor. Resten av beslutet gäller: varje
sammanträde med kallelse från det året, i alla organ, och sidans sätt att
säga vad som saknas.
