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
2. **Voeg je sensoren toe** (tabblad *Sensoren*, *Sensor toevoegen*):
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
   helemaal geen code nodig. Een gebruiker kan beperkt worden tot bepaalde modi en mag eventueel
   sabotagesensoren omzeilen.
4. **Voeg een melding toe** (tabblad *Meldingen*): kies een `notify`-dienst en de soorten berichten
   die hij krijgt. Met een *vertraging* stuurt het kanaal alarmberichten pas als het alarm na die
   tijd nog actief is: dat is een escalatiekanaal voor een tweede persoon of apparaat.
5. **Optioneel: een bevestigingsregel** (tabblad *Bevestigingsregels*): kies de directe
   inbraaksensoren, hoeveel er moeten aanslaan en binnen welk tijdvenster.
6. **Optioneel: een sirene** (tabblad *Sirenes*). Zie hieronder.
7. **Test alles** met de knoppen *Test* en door in te schakelen en een deur te openen. Het
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
Het paneel toont alleen de modi die in Vigil aan staan, vraagt een code zoals Vigil dat doet en kan
van taal wisselen. Installatie en opties staan in [esphome/README.md](../esphome/README.md). Elk
paneel heeft een eigen `source` (bijvoorbeeld *paneel garage*), dat in de geschiedenis staat als
*Anna (paneel garage)*. Een foute code geeft de gebeurtenis `code_rejected`, nooit met de code zelf. Na 5 foute codes binnen 5 minuten zijn alle codes 5 minuten vergrendeld (gebeurtenis `code_locked`); een beheerder in het paneel kan dan nog gewoon bedienen.

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
| **Overzicht** | Alarmstand, aandachtspunten (bijna lege batterijen, onbereikbare apparaten), wat elke modus bewaakt en de live status van elke sensor. |
| **Sensoren** | Sensoren toevoegen, bewerken, kopiëren en verwijderen. De tabel toont ook het batterijpercentage in een eigen kolom. Eén entiteit kan maar bij één sensor horen. Met het veld *Sabotage-entiteit* koppel je het sabotagesignaal van dezelfde sensor: Vigil maakt daar vanzelf een aparte sabotagesensor van die je los kunt omzeilen. Je kunt ook gewoon een losse sabotagesensor aanmaken. |
| **Sensorgroepen** | Welke sensoren in welke modi bewaken. Een groep kan zichzelf *voorstellen* voor nieuwe deurcontacten of bewegingssensoren. Een groep die nog in gebruik is kan niet verwijderd worden. |
| **Bevestigingsregels** | Meerdere sensoren moeten binnen een tijdvenster aanslaan. Een sensor die in een regel zit kan niet verwijderd worden. |
| **Gebruikers** | (Niet te kopiëren.) Naam, code, toegestane modi, recht om sabotage te omzeilen. Codes worden versleuteld opgeslagen en nooit getoond. Laat de code leeg bij bewerken om hem te behouden. |
| **Meldingen** | `notify`-dienst, soorten berichten (alarm, inlooptijd, in- en uitschakelen, storingen en mededelingen, technische alarmen), vertraging, hoge prioriteit. *Test* stuurt een testbericht. |
| **Sirenes** | Zie hierboven. *Test* laat de sirene 3 seconden klinken (geweigerd tijdens een echt alarm). |
| **Instellingen** | Modi, uitlooptijden, inlooptijd, alarmduur, batterijgrens, code nodig om in te schakelen, minimale codelengte (4 tot 12 tekens, standaard 4; geldt voor nieuwe en gewijzigde codes, bestaande codes blijven werken). |
| **Over** | Versie, links naar de handleiding en GitHub, release notes (nieuwste bovenaan) en een knop die de gegevens kopieert voor een foutmelding. |

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

## Herstarten en bijwerken

- De alarmstand en lopende timers worden bewaard. Na een herstart staat het alarm in dezelfde stand;
  een inlooptijd die tijdens de herstart afliep wordt een alarm, met de juiste tijd.
- De eerste 10 seconden na het opstarten van Home Assistant worden sensorstanden nog niet
  vertrouwd, zodat sensoren die nog niet geladen zijn geen valse storingen geven. Inschakelen in
  die tijd wordt geweigerd met "nog aan het opstarten".
- Bijwerken van Vigil Alarm via HACS vraagt een herstart van Home Assistant. Je configuratie wordt
  automatisch omgezet.

## Als het niet werkt

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
