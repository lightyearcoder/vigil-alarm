# Vigil Alarm: gebruikershandleiding

Deze handleiding legt uit hoe je Vigil Alarm instelt en gebruikt. Voor het installeren zie de
[README](../README.md) (Engels). Een Engelse versie van deze handleiding staat in
[user-guide.md](user-guide.md).

> Vigil Alarm is geen gecertificeerd alarmsysteem. Test het regelmatig en vertrouw er niet als
> enige bescherming op.

## Inhoud

1. [Hoe het in elkaar zit](#hoe-het-in-elkaar-zit)
2. [Instellen, stap voor stap](#instellen-stap-voor-stap)
3. [Het alarm dagelijks gebruiken](#het-alarm-dagelijks-gebruiken)
4. [Wat er gebeurt bij een alarm](#wat-er-gebeurt-bij-een-alarm)
5. [Naslag: het paneel, tabblad voor tabblad](#naslag-het-paneel-tabblad-voor-tabblad)
6. [Automatiseringen en blueprints](#automatiseringen-en-blueprints)
7. [Automatisch inschakelen](#automatisch-inschakelen)
8. [Zelfbewaking](#zelfbewaking)
9. [Herstarten en bijwerken](#herstarten-en-bijwerken)
10. [Als het niet werkt](#als-het-niet-werkt)
11. [Beperkingen om te kennen](#beperkingen-om-te-kennen)

## Hoe het in elkaar zit

| Onderdeel | Wat het is |
|---|---|
| **Alarm** | Eén `alarm_control_panel`-entiteit. Standen: *uitgeschakeld*, *bezig met inschakelen* (uitlooptijd), *ingeschakeld thuis / weg / nacht*, *inlooptijd* en *alarm*. |
| **Modi** | *Thuis* (jij bent thuis, de buitenkant wordt bewaakt), *Weg* (niemand thuis, alles wordt bewaakt) en *Nacht* (je slaapt, de buitenkant wordt bewaakt). Elke modus heeft een eigen uitlooptijd. |
| **Sensor** | Eén melder, gekoppeld aan een `binary_sensor` (aan = open of alarm). Elke sensor heeft een **klasse**. |
| **Sensorgroep** | Bepaalt **in welke modi** de inbraaksensoren erin bewaken. |
| **Bevestigingsregel** | Optioneel. Er volgt pas een alarm als meerdere verschillende sensoren binnen een tijdvenster aanslaan. |
| **Gebruiker** | Iemand met een code, eventueel beperkt tot bepaalde modi. |
| **Melding** | Eén `notify`-dienst die berichten krijgt, eventueel met vertraging (escalatie). |
| **Sirene** | Optioneel. Iets dat geluid maakt bij een alarm. |

### Sensorklassen

| Klasse | Gedrag |
|---|---|
| **Inbraak** | Bewaakt in de modi van zijn sensorgroepen. Type *direct* (meteen alarm), *vertraagd* (eerst inlooptijd, voor de voordeur) of *volger* (alleen alarm als eerst een vertraagde sensor openging, bijvoorbeeld een PIR in de gang achter de voordeur). |
| **Brand** | Bewaakt altijd, in elke modus, ook als het alarm uit staat. Meteen alarm. |
| **Gas** | Bewaakt altijd. Kies de soort gas: koolmonoxide, aardgas, lpg of overig. Bij aardgas en lpg schakelt Vigil nooit het flitslicht, vanwege het risico op vonken. |
| **Sabotage** | Bewaakt altijd. Een sabotagecontact dat opengaat geeft alarm. |
| **Water** | Bewaakt altijd. Een *technisch alarm*: het verandert de alarmstand nooit, maar geeft alleen events en een "alarm actief"-sensor. |

### Sensorgroepen: welke sensoren bewaken in welke modus

Een sensorgroep is een lijst van modi. Een inbraaksensor zit in één of meer groepen en bewaakt in
elke modus waarin één van zijn groepen actief is. Er zijn twee groepen voor je aangemaakt:

| Groep | Actief in | Voor |
|---|---|---|
| **Buitenschil** | Thuis, Weg, Nacht | deuren en ramen |
| **Binnen** | Weg | bewegingssensoren |

In *Thuis* tellen dus alleen deuren en ramen en kun je vrij door het huis lopen. In *Weg* tellen de
bewegingssensoren ook mee. Je kunt groepen toevoegen, bijvoorbeeld *Kelder* voor alleen *Nacht*.

Daarom gebruikt Vigil hiervoor geen Home Assistant-gebieden: een gebied zegt **waar** een sensor
hangt, een sensorgroep zegt **hoe je hem wilt gebruiken**. Een deurcontact en een PIR in dezelfde
kamer horen in verschillende groepen.

Het tabblad **Overzicht** toont "Wat bewaakt elke modus", zodat je het resultaat kunt controleren.

## Instellen, stap voor stap

Open **Vigil Alarm** in de zijbalk (alleen beheerders zien het). Bij elke wijziging laadt Vigil Alarm
opnieuw; de alarmstand blijft behouden.

1. **Controleer de instellingen** (tabblad *Instellingen*): modi, uitlooptijden, standaard
   inlooptijd, alarmduur en of er een code nodig is om in te schakelen.
2. **Voeg je sensoren toe.** De snelle weg is *Sensoren → Sensoren zoeken*: Vigil toont de deur-, raam-, beweging-, rook-, gas-, water- en sabotagesensoren die Home Assistant al kent, met de batterij- en sabotagesensor van hetzelfde apparaat. Vink aan wat je wilt, pas zo nodig een naam aan, vink *Ingang* aan voor deuren waar je doorheen loopt (die krijgen een inlooptijd) en voeg ze in één keer toe. Er wordt niets opgeslagen voordat je op de knop onderaan drukt. Heb je nog geen sensorgroepen, klik dan eerst op *Standaardgroepen maken* (Buitenschil voor deuren en ramen, Binnen voor beweging). Zelf één toevoegen kan met *Sensoren → Sensor toevoegen*:
   - Geef een naam ("Voordeur"). De naam bepaalt de entiteitsnamen (`sensor.voordeur_status`).
   - Kies de `binary_sensor`. Bij een deurcontact of bewegingssensor stelt het paneel zelf de
     juiste sensorgroep voor.
   - Kies de klasse en, bij inbraak, het type en de sensorgroepen.
   - Heeft het apparaat ook een sabotagecontact (de meeste Zigbee-deurcontacten wel)? Vul het in bij *Sabotage-entiteit*. Vigil voegt dan zelf een sabotagesensor toe, "Voordeur (sabotage)": altijd actief, met een eigen omzeilschakelaar. Hij volgt de sensor bij hernoemen, wijzigen en verwijderen en heeft geen eigen regel in de tabel.
   - *Als open bij einde uitlooptijd* bepaalt wat er gebeurt met een deur die nog open staat als het
     alarm inschakelt: **omzeilen met melding** (standaard; hij wordt weer bewaakt zodra hij dicht
     is), **wachten tot dicht**, **inschakelen weigeren** of **inlooptijd starten**.
   - *Als de sensor onbereikbaar wordt*: **inschakelen blokkeren** (standaard bij inbraak en
     sabotage), **alleen melden** (standaard bij brand, gas en water), **alarm geven** of
     **toch inschakelen (omzeilen)**. Brand en gas kunnen nooit omzeild worden.
   - Voeg eventueel een batterijsensor toe; Vigil waarschuwt dan als hij bijna leeg is.
3. **Voeg een gebruiker toe** (tabblad *Gebruikers*): een naam en een code. Zonder gebruikers is er
   helemaal geen code nodig. Een gebruiker kan beperkt worden tot bepaalde modi. Omzeilen is een recht dat je een gebruiker geeft (*Mag sensoren omzeilen*): zonder dat recht kan een gebruiker een sensor niet omzeilen en ook niet terugzetten, ook niet met een goede code. Wie een sensor mag omzeilen, mag hem ook terugzetten. Een sabotagesensor vraagt daarnaast het recht *Mag sabotage omzeilen*, voor omzeilen en voor terugzetten. Gebruikers die al bestonden houden het recht tot je het uitvinkt.
4. **Voeg een melding toe** (tabblad *Meldingen*): kies een `notify`-dienst en de soorten berichten
   die hij krijgt. Met een *vertraging* stuurt het kanaal alarmberichten pas als het alarm na die
   tijd nog actief is: dat is een escalatiekanaal voor een tweede persoon of apparaat.
5. **Optioneel: een bevestigingsregel** (tabblad *Bevestigingsregels*): kies de directe
   inbraaksensoren, hoeveel er moeten aanslaan en binnen welk tijdvenster.
6. **Optioneel: een sirene** (tabblad *Sirenes*). Zie hieronder.
7. **Kijk bij *Klaar voor gebruik?*** bovenaan het tabblad *Overzicht*. Daar staat wat er nog ontbreekt (een gebruiker met code, een meldingskanaal, een modus die niets bewaakt, sensoren zonder batterijsensor), met een knop naar de juiste plek. Heb je nog geen meldingskanaal en kent Home Assistant je telefoon, dan voegt één knop hem toe en stuurt een testmelding.
8. **Test alles** met de knoppen *Test* en door in te schakelen en een deur te openen. Het
   [testplan](installatie-en-testen.nl.md) heeft een volledige test met virtuele sensoren.

### Sirenes

Een sirene heeft een aan/uit-entiteit (`siren`, `switch` of `light`) en optionele extra's: een
flitslicht, een toonkeuze-entiteit en een volume-entiteit. Per oorzaak (inbraak, brand, gas,
sabotage) kun je een toon en volume opgeven. Die worden vlak voor het geluid ingesteld en daarna
teruggezet. De sirene stopt als het alarm uitgaat en na een maximale duur. Een sirene die zelf
stopt kan elke N seconden opnieuw worden aangezet.

Veel sirenes kunnen niet melden of ze echt aan staan. Dan heeft `siren_started` de waarde
`verified: false`, en een commando dat mislukt geeft `siren_failed` en een melding.

**Voorinstelling voor de Sonoff SNZB-09P (Zigbee2MQTT):** kies bij *Sirene* de aan/uit-schakelaar
van de sirene en kies dan de voorinstelling. Vigil vult de tonen in (klassiek bij inbraak,
waarschuwing bij brand, noodsignaal bij gas, snel bij sabotage), het volume en de duur, en zoekt de
entiteiten voor toon, volume, flitslicht, batterij en voedingsmodus van hetzelfde apparaat erbij.
Wordt iets niet gevonden, dan kies je het zelf. Met ZHA of een andere integratie kies je de
aan/uit-entiteit en vul je de rest zelf in.

## Het alarm dagelijks gebruiken

### Inschakelen en uitschakelen

Gebruik de alarmpaneelkaart (of de tegelkaart, of de Companion-app), de *arm*-acties in een
automatisering, of het [dashboard](../examples/dashboard.yaml). Voer je code in als die nodig is.

- **Inschakelen** start de uitlooptijd (stand *bezig met inschakelen*), daarna is het alarm
  *ingeschakeld*. Loop naar buiten.
- **Uitschakelen** vraagt altijd een code zodra er gebruikers zijn. Tijdens de inlooptijd
  (*pending*) heb je de inlooptijd om hem in te voeren.
- Een gebruiker kan beperkt zijn tot bepaalde modi; een andere modus inschakelen wordt geweigerd.

### Als inschakelen wordt geweigerd

Vigil zegt waarom: *een alarmmelding staat open* (een brand- of sabotagesensor is aan), *een sensor
is onbereikbaar* (een inbraaksensor is onbereikbaar en staat op blokkeren) of *een sensor staat
open* (een sensor die op weigeren staat). Het attribuut `refuse_reason` en de melding noemen welke
sensoren. Herstel de sensor of omzeil hem.

### Een sensor omzeilen

Omzeilen laat één sensor buiten beschouwing tot het alarm wordt uitgeschakeld (of tot je het
omzeilen opheft).

- In het paneel en op het dashboard: de schakelaar **Omzeilen** van de sensor (alleen beheerders).
- Met een actie: `vigil_alarm.bypass` en `vigil_alarm.unbypass` met de sensor-entiteit en, voor mensen die geen
  beheerder zijn, een code. Die code is alleen nodig als ook inschakelen een code vraagt
  (instelling *code vereist bij inschakelen*). Sabotagesensoren kunnen alleen door beheerders en door gebruikers met
  dat recht worden omzeild.
- Brand- en gassensoren kunnen nooit worden omzeild.

### Een aanraakpaneel

Met het ESPHome-paneel (Guition 4848) schakel je in en uit en omzeil je sensoren zonder telefoon.
Het paneel leest zijn profiel uit Vigil: het toont alleen de modi waarin het mag inschakelen, vraagt een code zoals Vigil dat doet en gebruikt de taal die je ervoor instelt. Installatie en opties staan in [esphome/README.md](../esphome/README.md). De apparaatnaam is het paneel-id en de `source` van elke oproep, en staat in de geschiedenis als
*Anna (vigil-panel-garage)*. Een foute code geeft de gebeurtenis `code_rejected`, nooit met de code zelf. De vergrendeling gaat in stappen en de getallen stel je in bij *Instellingen*, *Vergrendeling*. Standaard: na 3 foute codes is dat paneel 5 minuten vergrendeld, daarna na nog 2 foute codes 15 minuten, daarna na nog 2 foute codes 60 minuten, en na nog 1 foute code permanent (gebeurtenissen `code_locked` en `code_locked_permanent`, ook gemeld op je storingskanalen). Een permanente vergrendeling gaat alleen weg met *Blokkade opheffen* bij het paneel, en dan begint alles weer bij de eerste stap. Een goede code zet de teller en de stap ook terug naar nul. De vergrendeling blijft staan als Home Assistant herstart; de gedeelde timer voor alles wat geen geregistreerd paneel is (*other*) wordt nooit permanent, omdat niemand die zou kunnen opheffen, maar herhaalt de laatste wachttijd; een beheerder in het paneel kan dan nog gewoon bedienen. Elk geregistreerd paneel (zie hieronder) heeft een eigen timer; al het andere (een telefoon, een automatisering, elke andere naam) deelt één timer.

#### Panelen, tablets en telefoons

Het tabblad *Panelen* is het register van alles wat het alarm mag bedienen behalve de Home Assistant-schermen zelf: ESPHome-panelen (herkend aan hun paneel-id) en tablets of telefoons (herkend aan hun Home Assistant-account). Ze worden allemaal op dezelfde manier ingesteld. Zodra één account is geregistreerd, worden andere gewone accounts geweigerd voordat hun code wordt bekeken (gebeurtenis `user_refused`); beheerders, automatiseringen en ESPHome-panelen blijven ongemoeid. Details, en het advies om een beheerder een tweede, gewoon account voor dagelijks gebruik te geven, staan in de [tabletgids](tablet.nl.md).

#### Een paneel registreren (tabblad *Panelen*)

Een paneel of tablet dat je op het tabblad *Panelen* registreert, is een domme terminal: Vigil bepaalt wat het mag. Je geeft het een naam en een **paneel-id**; dat is de naam van het ESPHome-apparaat en ook de `source` die de oproepen meesturen. Per paneel stel je in:

Bij het toevoegen van een paneel kies je eerst het **soort apparaat**. *ESPHome-paneel* vraagt om de naam van het ESPHome-apparaat (het paneel-id). *Tablet of telefoon met Home Assistant* vraagt alleen om het Home Assistant-account; het paneel-id maakt Vigil zelf uit de naam. De rest (modi, uitschakelen, omzeilen, taal, sensorlijst, installateurscode) is voor beide gelijk. De taal begint als die van de persoon die het paneel toevoegt, anders English.

- in welke modi het mag inschakelen, en of het mag uitschakelen, sensoren omzeilen, en dempen of bevestigen;
- de taal (standaard die van Home Assistant);
- of het de sensorlijst mag tonen: *altijd*, *pas na ontgrendelen* (standaard) of *nooit*, en hoe lang het ontgrendeld blijft (standaard 60 seconden);
- een optionele **installateurscode** voor dit paneel, bewaard als hash, met een eigen timer voor foute codes. Het paneel stuurt die mee met `vigil_alarm.unlock_panel`; Vigil controleert hem en ontgrendelt het paneel voor de ingestelde tijd. Dat opent de infopagina's en (net als de code van een Vigil-gebruiker) de sensorlijst, en schakelt het alarm nooit uit: uitschakelen vraagt altijd een geldige gebruikerscode;
- wat de firmware **zelf meldt** (hardware, firmwareversie en profielversie) staat op de paneelkaart, en *Klaar voor gebruik?* geeft advies als de firmware het profiel niet begrijpt;
- **geblokkeerd**: Vigil weigert elke oproep met dat paneel-id en legt het vast.

Wat wordt afgedwongen, aan de serverkant: een oproep van een geregistreerd paneel die zijn profiel niet toestaat, wordt geweigerd en vastgelegd (gebeurtenis `panel_refused`, met de reden). Een sensor omzeilen vanaf een geregistreerd paneel vraagt altijd een gebruikerscode. Een geblokkeerd paneel wordt geweigerd voordat er naar een code wordt gekeken. Oproepen met een bron die niet is geregistreerd, worden hier niet door beperkt.

Elk geregistreerd paneel krijgt een entiteit `sensor.<paneel-id>_profile` (streepjes in het paneel-id worden underscores: `vigil-panel-garage` geeft `sensor.vigil_panel_garage_profile`) met wat het mag en toont. De namen van de sensoren staan er alleen in zolang het paneel is ontgrendeld (of als de lijst op *altijd* staat), en de attributen met die namen blijven buiten de geschiedenis. Er staat nooit een code, hash, sleutel of wachtwoord in. **Eerlijk over wat dit beschermt:** `source` is gewone tekst, dus Vigil kan niet bewijzen dat een oproep echt van dat paneel komt. Het profiel beschermt tegen vergissingen en tegen een paneel dat bepaalde knoppen niet hoort te hebben, niet tegen iemand die al services kan aanroepen. De echte bescherming is de code, de blokkade, de versleutelde verbinding van het paneel en de toegangsregels van Home Assistant zelf.

Twee knoppen per paneel, **Ontgrendelen** en **Blokkade opheffen**, bestaan alleen in het Vigil-paneel (alleen beheerders) en niet als Home Assistant-actie: een actie kan elke gebruiker, automatisering en elk paneel aanroepen, waarmee een gestolen paneel zichzelf kon ontgrendelen. *Ontgrendelen* toont de sensorlijst voor de ingestelde tijd; *Blokkade opheffen* haalt de bewaarde blokkade na foute codes weg (die overleeft een herstart, dus zo hef je hem op). Beide worden vastgelegd met de beheerder die het deed (`panel_unlocked`, `panel_lock_cleared`).

**Niet bereikbaar.** Kan Vigil het ESPHome-apparaat van een paneel 10 minuten niet bereiken, dan krijg je een reparatie *Paneel niet bereikbaar* en een melding op je storingskanalen (gebeurtenissen `panel_offline` en `panel_online`). Een paneel dat niet bereikbaar is, verandert de alarmstatus nooit. Een geblokkeerd paneel geeft geen reparatie. Na een herstart van Home Assistant beginnen de tien minuten opnieuw.

Ook een tablet kan worden geregistreerd, gekoppeld aan een Home Assistant-gebruiker, en toont de Vigil-kaart (`type: custom:vigil-card`); zie de [tabletgids](tablet.nl.md).

De ESPHome-firmware leest dit profiel zelf. Een paneel dat niet in het register staat, toont *Niet gekoppeld* met het paneel-id dat het verwacht; een geblokkeerd paneel toont *Geblokkeerd*. De sensorlijst en de infopagina van het paneel (IP-adres, signaal, firmware, uptime) openen met een code: de sensorlijst met de code van een Vigil-gebruiker (of de installateurscode), de infopagina alleen met de installateurscode van het paneel; zolang het niet ontgrendeld is, toont het paneel alleen hoeveel sensoren open staan. Vigil dwingt de beperkingen ook zelf af voor elke oproep die de `source` van het paneel meestuurt, wat de firmware ook doet.

### Dempen en bevestigen

- `vigil_alarm.silence` stopt de sirenes terwijl het alarm actief blijft.
- `vigil_alarm.acknowledge` annuleert de nog wachtende escalatieberichten: je hebt het gezien.

Beide vragen een gebruikerscode, of een beheerder in de interface.

## Wat er gebeurt bij een alarm

Een voorbeeld met het alarm ingeschakeld op *Weg* en de voordeur (een vertraagde sensor) die open
gaat:

| Moment | Wat er gebeurt |
|---|---|
| Deur gaat open | Stand *pending*. Event `pending_started`. Melding "Inlooptijd gestart". |
| Binnen de inlooptijd | Uitschakelen met een code: geen alarm. |
| Inlooptijd verloopt | Stand *triggered*, oorzaak *intrusion*. Event `triggered`. Meldingen gaan uit, sirenes klinken, "Inbraakalarm" gaat aan. |
| Na de vertraging van een escalatiekanaal | Is het alarm dan nog actief en niet bevestigd, dan stuurt dat kanaal zijn bericht. |
| Uitschakelen, of de alarmduur loopt af | Sirenes stoppen, `trigger_ended`, stand terug naar *uitgeschakeld* of *ingeschakeld*. |

Een directe sensor slaat de inlooptijd over. Brand, gas en sabotage geven meteen alarm, in elke
stand. Een ernstiger oorzaak vervangt een minder ernstige (`trigger_cause_changed`): de volgorde is
brand, dan gas, sabotage, sensorstoring en inbraak.

Bij een **bevestigingsregel** geeft één aanslag van een van de sensoren geen alarm. Er komt
`sensor_unconfirmed` (en een melding als je die wilde). Slaat het vereiste aantal verschillende
sensoren binnen het venster aan, dan volgt het alarm met `confirmed_by` in het event.

## Naslag: het paneel, tabblad voor tabblad

Acties in de lijsten zijn icoonknoppen (bewerken, kopiëren, verwijderen, testen); houd de muis erboven voor de naam. Regels en gebruikers hebben geen kopieerknop. Achter sommige velden staat een ⓘ: klik erop voor een uitgebreide uitleg.

| Tabblad | Wat je er doet |
|---|---|
| **Overzicht** | *Klaar voor gebruik?*, de kaart *Zelftest* (laatste controle, laatste sirenetest, volgende test, *Sirene nu testen*), de kaart *Hartslag* (laatste succes, *Nu testen*), (wat ontbreekt er nog), een kaart *Dashboard* met een knop die een dashboard met je eigen entiteit-id's kopieert, alarmstand, aandachtspunten (bijna lege batterijen, onbereikbare apparaten), wat elke modus bewaakt en de live status van elke sensor. |
| **Sensoren** | *Sensoren zoeken* stelt sensoren uit Home Assistant voor; sensoren toevoegen, bewerken, kopiëren en verwijderen. De tabel toont ook het batterijpercentage in een eigen kolom. Eén entiteit kan maar bij één sensor horen. Met het veld *Sabotage-entiteit* koppel je het sabotagesignaal van dezelfde sensor: Vigil maakt daar vanzelf een aparte sabotagesensor van die je los kunt omzeilen. Je kunt ook gewoon een losse sabotagesensor aanmaken. |
| **Sensorgroepen** | Welke sensoren in welke modi bewaken. Een groep kan zichzelf *voorstellen* voor nieuwe deurcontacten of bewegingssensoren. Een groep die nog in gebruik is kan niet verwijderd worden. |
| **Bevestigingsregels** | Meerdere sensoren moeten binnen een tijdvenster aanslaan. Een sensor die in een regel zit kan niet verwijderd worden. |
| **Gebruikers** | (Niet te kopiëren.) Naam, code, toegestane modi, recht om te omzeilen, recht om sabotage te omzeilen. Codes worden versleuteld opgeslagen en nooit getoond. Laat de code leeg bij bewerken om hem te behouden. |
| **Meldingen** | `notify`-dienst, soorten berichten (alarm, inlooptijd, in- en uitschakelen, storingen en mededelingen, technische alarmen), vertraging, hoge prioriteit. *Test* stuurt een testbericht. |
| **Sirenes** | Zie hierboven. *Test* laat de sirene 3 seconden klinken (geweigerd tijdens een echt alarm). |
| **Logboek** | Alles wat Vigil als gebeurtenis meldt, de nieuwste bovenaan (de laatste 200 staan in beeld). *Download* geeft het hele logboek als JSON Lines of CSV (RFC 4180), met tijden in UTC (RFC 3339) en de velden `time`, `event`, `source`, `user`, `item`, `result` en `detail`. Standaard 90 dagen bewaard (*Instellingen*), zonder codes, en het blijft bestaan na een herstart. |
| **Instellingen** | Modi, uitlooptijden, inlooptijd, alarmduur, hoe lang er na een herstart van Home Assistant op trage sensoren wordt gewacht (seconden, standaard 120), het scherm van de panelen (seconden tot het scherm uitgaat, standaard 30, en of het ook tijdens een alarm uit mag gaan, standaard nee), batterijgrens, code nodig om in te schakelen, minimale codelengte (4 tot 12 tekens, standaard 4; geldt voor nieuwe en gewijzigde codes, bestaande codes blijven werken), dagen dat het logboek bewaard blijft (standaard 90), en de zelftest: herinneringsinterval (standaard 30 dagen, 0 = uit), seconden dat de sirene klinkt (1 tot 5, standaard 2), zelf laten klinken en de uren waarbinnen dat mag, en het hartslag-adres met het interval in minuten (standaard 5). |
| **Over** | Een badge "nieuw" na een update, versie, links naar de handleiding en GitHub, release notes (nieuwste bovenaan) en een knop die de gegevens kopieert voor een foutmelding. |

De taal van de **meldingsteksten** volgt de systeemtaal van Home Assistant (Instellingen → Systeem →
Algemeen). Het paneel volgt de taal van je eigen profiel (Nederlands en Engels).

## Automatiseringen en blueprints

Alles buiten meldingen en sirenes automatiseer je zelf. Vigil publiceert de event-entiteit
`event.<naam>_alarm_events`; de [README](../README.md#for-automations) toont alle events en hun
gegevens.

De meegeleverde [blueprints](../README.md#blueprints) dekken de gewone gevallen:

- **Flash lights during an alarm** bewaart de toestand van je lampen, laat ze knipperen zolang het
  alarm actief is en zet ze daarna terug, ook als het alarm wordt uitgeschakeld. Kies welke
  oorzaken knipperen (gas staat standaard uit). De standaard van 2 seconden aan en 2 seconden uit
  blijft ruim onder de snelheid die voor lichtgevoelige mensen telt. Gebruik bij Hue een kamer of
  zone (groep) in plaats van losse lampen; groepen staan standaard uit in Home Assistant, zet ze
  eerst aan.
- **Announce alarm events with speech** spreekt een bericht uit als het alarm in- of uitschakelt, de
  inlooptijd start of afgaat. Laat een bericht leeg om bij dat event stil te blijven.
- **Run your own actions on alarm events** is de algemene bouwsteen: kies events en voeg
  willekeurige acties toe, met `event_type` en `data` beschikbaar.
- **Remind when arriving at an armed home** stuurt een bericht als iemand thuiskomt terwijl het
  alarm aan staat. Het schakelt niets uit.

De blueprints zelf zijn Engelstalig; de berichten die ze sturen stel je zelf in.

### Automatisch inschakelen

**Arm when everyone has left** en **Arm at a set time** schakelen het alarm voor je in. Ze
schakelen nooit uit: uitschakelen vraagt altijd een persoon met een code.

Inschakelen vraagt een code, tenzij *Code nodig om in te schakelen* in het paneel is uitgezet. Je
hebt twee keuzes:

1. Zet *Code nodig om in te schakelen* uit. Dan kan iedereen die bij de alarm-entiteit kan het
   alarm inschakelen (uitschakelen vraagt nog steeds een code). Dit is de eenvoudigste optie en er
   staat geen geheim in.
2. Houd de codeplicht en zet een code in de blueprint. Die code staat **als leesbare tekst** in de
   automatisering. Maak er een aparte Vigil-gebruiker voor, beperkt tot de ene modus die de
   automatisering gebruikt, en gebruik nooit je eigen code.

Wordt inschakelen geweigerd (bijvoorbeeld omdat een deur openstaat), dan kun je een bericht krijgen
met de reden. Laat je het berichtveld leeg, dan wordt er niets gestuurd.

## Zelfbewaking

Echte storingen (een onbereikbare sensor, een bijna lege batterij, een sirene die niet beschikbaar is of op batterij werkt) staan ook onder *Instellingen → Systeem → Reparaties* en verdwijnen vanzelf als ze zijn opgelost. Ontbrekende instellingen zijn geen reparaties; die staan in *Klaar voor gebruik?*.

- **Batterij:** geef een sensor of sirene een batterijsensor. Vigil meldt `battery_low` als het
  niveau de grens bereikt (standaard 20%, een instelling) en `battery_ok` bij herstel.
- **Sensoren:** een onbereikbare sensor volgt zijn instelling *als onbereikbaar*, en wordt gemeld
  met `supervision_lost` en `supervision_restored`.
- **Sirenes:** Vigil meldt als een sirene onbereikbaar wordt en, met een voedingsmodus-entiteit,
  als hij op batterij draait (de waarde die "op batterij" betekent is een instelling, standaard
  `battery`; controleer wat jouw apparaat meldt). Voeg het sabotagecontact van een sirene toe als
  sabotagesensor.
- Problemen die bij het opstarten al bestaan staan in het attribuut `problems` van het alarm, zonder
  event; events volgen bij veranderingen. Het overzicht toont ze onder *Aandachtspunten*.

### Zelftest

Niemand test elke week een sirene, dus Vigil onthoudt het voor je. De zelftest loopt vanzelf en vraagt pas iets van je als het tijd is voor een echte test.

- **Stille controle, dagelijks.** Vigil controleert of de meldingsdiensten die je hebt ingesteld nog bestaan en of de sirenes bereikbaar zijn. Er klinkt niets. Alleen een meldkanaal dat is verdwenen (bijvoorbeeld na een nieuwe telefoon) geeft een bericht en een reparatie; een onbereikbare sirene wordt al als storing gemeld door de bewaking hierboven.
- **Sirenetest, maandelijks.** Standaard elke 30 dagen (een instelling; 0 zet het uit) stuurt Vigil een herinnering naar de kanalen die *storingen en mededelingen* ontvangen. Op een telefoon met de Home Assistant-app heeft het bericht een knop **Sirene testen**; een tik laat de sirene 2 seconden klinken. Je kunt ook *Sirene nu testen* op het Overzicht gebruiken of de actie `vigil_alarm.test_siren` aanroepen.
- **Reageer je niet,** dan volgt na 3 dagen een tweede herinnering. Na nog eens 7 dagen staat er een reparatie dat de test achterstallig is. Een test, op een van de drie manieren, haalt die weg.
- **Vigil de sirene zelf laten klinken** staat standaard uit. Zet je het aan, dan laat Vigil de sirene klinken als de test aan de beurt is, maar alleen binnen de uren die je instelt (standaard 9 tot 20), zodat niemand wakker wordt.
- De test wordt geweigerd tijdens een echt alarm en is zelf geen alarm: er gaat niets naar de alarmkanalen.
- De kaart *Zelftest* op het Overzicht toont de laatste stille controle, de laatste sirenetest en wanneer de volgende aan de beurt is. De zelftest-events (`selftest_checked`, `selftest_reminder`, `selftest_siren_tested`) komen in het logboek maar tellen niet als laatste gebeurtenis van het alarm.

### Hartslag

Een sirene en een melding helpen alleen als Home Assistant zelf draait. De hartslag dekt het andere geval: als Home Assistant, de computer waarop het draait of je internetverbinding uitvalt, kan niets in huis je dat vertellen. Daarom roept Vigil met vaste tussenpozen een webadres aan, en een bewakingsdienst **buiten** je huis slaat alarm als die aanroepen uitblijven.

- Vigil is niet aan één dienst gebonden. Bij *Instellingen* vul je een **hartslag-adres** in en het aantal **minuten tussen hartslagen** (standaard 5). Elke dienst die een regelmatige aanroep verwacht en meldt als die uitblijft, werkt. Laat het adres leeg om het uit te zetten.
- De aanroep gebeurt altijd, ook als het alarm uit staat, want de vraag die hij beantwoordt is: "draait Vigil nog?".
- De aanroep bevat niets over je alarm: geen status, geen namen, geen codes. Het is een gewone GET-aanvraag.
- Het adres is een geheim, want diensten stoppen er meestal de sleutel in. Vigil houdt het uit het logboek, de reparaties en de gedownloade diagnostics, en het paneel toont het alleen aan een beheerder op het tabblad Instellingen.
- De kaart *Hartslag* op het Overzicht toont het interval, de laatste keer dat het lukte en de laatste keer dat het mislukte, en heeft een knop *Nu testen*. Na drie mislukkingen achter elkaar komt er een reparatie, die verdwijnt als de hartslag weer werkt.

**Uitgewerkt voorbeeld met Healthchecks.io** (er is een gratis plan, of je draait het zelf):

1. Maak een check. Zet de *periode* iets boven je interval, bijvoorbeeld 5 minuten, en een *respijttijd* van 5 tot 10 minuten, zodat één gemiste aanroep nog geen bericht geeft.
2. Koppel onder *Integrations* waar het bericht heen moet (e-mail, of een app op je telefoon).
3. Kopieer de *ping-URL* van de check. Dat is een `https://`-adres dat eindigt op een lange code.
4. Plak die in Vigil Alarm bij *Instellingen → Hartslag-adres* en sla op.
5. Klik op het Overzicht op *Nu testen*. De check wordt binnen een paar seconden groen.
6. Om te bewijzen dat het werkt: zet Home Assistant langer dan de periode plus de respijttijd uit. Je hoort een bericht van de dienst te krijgen.

Andere diensten werken op dezelfde manier: je hebt een adres nodig dat een aanroep verwacht, een periode, en een manier om te horen als die gemist wordt.

## Herstarten en bijwerken

- De alarmstand en lopende timers worden bewaard. Na een herstart staat het alarm in dezelfde stand;
  een inlooptijd die tijdens de herstart afliep wordt een alarm, met de juiste tijd.
- De eerste 10 seconden na het opstarten van Home Assistant worden sensorstanden nog niet
  vertrouwd, zodat sensoren die nog niet geladen zijn geen valse storingen geven. Inschakelen in
  die tijd wordt geweigerd met "nog aan het opstarten".
- Bijwerken van Vigil Alarm via HACS vraagt een herstart van Home Assistant. Je configuratie wordt
  automatisch omgezet.

## Als het niet werkt

Zie ook **[Mijn alarm doet niet wat ik verwacht](problemen-oplossen.nl.md)**.

| Probleem | Wat te doen |
|---|---|
| **Geen "Vigil" in de zijbalk** | Alleen beheerders zien het. Ververs de browser hard, herstart Home Assistant en zoek in het logboek naar `vigil`. |
| **Het paneel blijft leeg of meldt dat het niet geladen kon worden** | De integratie draait niet: kijk onder Instellingen → Apparaten en diensten naar een foutmelding. Ververs de browser. |
| **Inschakelen wordt geweigerd** | Lees de reden in de melding of het attribuut `refuse_reason` en controleer de genoemde sensoren. |
| **Een sensor wordt onbereikbaar gemeld** | Controleer het apparaat. Tijdelijk kun je *als onbereikbaar* op *toch inschakelen (omzeilen)* zetten. |
| **Er komt geen melding** | Gebruik *Test* bij de melding. Controleer of de `notify`-dienst bestaat en of de soort bericht is aangevinkt. |
| **De sirene klinkt niet** | Gebruik *Test* bij de sirene. Controleer de aan/uit-entiteit en de oorzaken bij *Laat klinken bij*. Sommige sirenes stoppen zelf na hun eigen duur; zie *herhaal elke*. |
| **Een automatisering reageert niet** | Trigger op de event-entiteit (niet op de alarmstand) en bekijk `event_type` in de trace van de automatisering. |
| **Een blueprint kan niet inschakelen** | Inschakelen vraagt een code. Zie [Automatisch inschakelen](#automatisch-inschakelen). |

Neem bij een foutmelding op wat je deed, wat je verwachtte, wat er gebeurde en de logregels met
`vigil` (Instellingen → Systeem → Logboeken). Voor meer detail zet je in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.vigil_alarm: debug
```

## Beperkingen om te kennen

- Vigil Alarm is **niet gecertificeerd** voor een alarm-, brandmeld- of verzekeringsnorm.
- Het draait in Home Assistant. Ligt Home Assistant eruit of herstart het, dan is er geen alarm.
- Alles wordt door Home Assistant-beheerders ingesteld, in het paneel. Er is geen andere manier om
  sensoren en gebruikers te bewerken; dat is bewust.
- **Tags** kunnen bij een gebruiker worden bewaard maar hebben **geen functie**. Bedien het alarm
  met een code.
- Je code beschermt alleen de alarm-entiteit. Elke Home Assistant-beheerder kan de configuratie
  wijzigen.
- Test regelmatig, ook een echt alarm en je meldingsroute, en vervang batterijen als Vigil dat meldt.
