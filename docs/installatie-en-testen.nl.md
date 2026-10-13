# Vigil Alarm: installeren op Home Assistant OS en testen

Deze gids is voor Home Assistant OS (HAOS). Je plaatst de map `vigil` in de configuratiemap, voegt een testpakket met virtuele sensoren toe en doorloopt daarna de testen. Alles gebeurt zonder echte sensoren of sirene.

**Let op:** dit is een testversie van een zelfgebouwde integratie, geen gecertificeerd alarmsysteem. De integratie is tot nu toe alleen getest in een testomgeving met Home Assistant 2026.2.3. Verwacht afwijkingen in een echte installatie en meld ze (zie hoofdstuk 7).

---

## 1. Voorbereiding

1. Controleer je versie: **Instellingen → Info**. Minimaal 2026.2.3.
2. Maak een back-up: **Instellingen → Systeem → Back-ups → Back-up maken**. Wacht tot hij klaar is.
3. Pak `vigil-alarm.zip` uit op je Mac. Je krijgt een map `vigil-alarm`. Daarin staat `custom_components/vigil`. Alleen die map `vigil` ga je kopiëren.

## 2. De bestanden op Home Assistant zetten

Je hebt toegang tot de configuratiemap nodig. De makkelijkste weg op een Mac is de Samba-add-on.

1. **Instellingen → Add-ons → Add-on store**, zoek **Samba share**, installeer hem.
2. Open de add-on, tab **Configuratie**: vul bij gebruikersnaam en wachtwoord iets in en sla op. Start de add-on (tab **Info**).
3. In Finder: **Ga → Verbind met server** (⌘K) en typ `smb://homeassistant.local` (lukt dat niet, gebruik het IP-adres van je Home Assistant). Log in met de zojuist gekozen gegevens.
4. Open de share **config**. Zie je daar `configuration.yaml`, dan zit je goed.
5. Bestaat de map `custom_components` nog niet, maak hem dan aan.
6. Kopieer de map `vigil` (uit `vigil-alarm/custom_components/`) in `config/custom_components/`. Het resultaat is `config/custom_components/vigil/manifest.json`. Controleer dat precies dit pad klopt: één map te veel of te weinig is de meest voorkomende fout.

*Alternatief:* de add-on **Terminal & SSH** met `scp -r custom_components/vigil root@homeassistant.local:/config/custom_components/`.

## 3. Het testpakket plaatsen

Het testpakket (`docs/vigil_test_package.yaml`) maakt virtuele sensoren: een voordeur, twee PIR's, rookmelder, sabotagecontact en watermelder, een batterijniveau, een voedingsmodus en een virtuele sirene. Je bedient ze met schakelaars op een dashboard.

1. Maak in de share **config** een map `packages`.
2. Kopieer `vigil_test_package.yaml` (uit `vigil-alarm/docs/`) daarin.
3. Open `configuration.yaml` en zorg dat dit erin staat (staat er al een blok `homeassistant:`, voeg dan alleen de regels `packages` toe):

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
4. **Ontwikkelaarstools → YAML → Configuratie controleren.** Het resultaat moet "Configuratie geldig" zijn.
5. **Ontwikkelaarstools → YAML → Opnieuw starten** (of **Instellingen → Systeem → Opnieuw starten**). Een volledige herstart is nodig voor de nieuwe integratie; alleen YAML herladen is niet genoeg.

Na de herstart bestaan onder andere `binary_sensor.vigil_test_front_door` en `switch.vigil_test_siren`.

## 4. De integratie toevoegen en inrichten

Alles is alleen als beheerder mogelijk.

1. **Instellingen → Apparaten en diensten → Integratie toevoegen**, zoek **Vigil Alarm**. Vind je hem niet, ververs dan de browser hard (⌘⇧R) en kijk in hoofdstuk 8.
2. Vul in voor de test (korte tijden maken testen sneller):
   - Naam: `Vigil Alarm` (laat dit zo, de entiteitsnamen in deze gids gaan hiervan uit)
   - Modi: thuis, weg, nacht
   - Uitlooptijd thuis `0`, weg `20`, nacht `5`
   - Standaard inlooptijd `15`
   - Duur alarm `0`, batterijgrens `20`, code vereist om in te schakelen: aan
3. Klik in de zijbalk op **Vigil Alarm** (het schildje met huisje; alleen zichtbaar voor beheerders). Zie je het niet, ververs dan de browser hard. Hier staan tabbladen **Overzicht, Sensoren, Sensorgroepen, Bevestigingsregels, Gebruikers, Meldingen, Sirenes** en **Instellingen**. Voeg per tabblad met de knop bovenaan de onderdelen hieronder toe. Elke rij heeft knoppen om te bewerken, te kopiëren of te verwijderen. Sensoren, gebruikers enzovoort bewerk je alleen hier; onder *Apparaten en diensten* staat alleen het alarm zelf (met de knop *Opnieuw configureren* voor de basisinstellingen).
   Elke keer dat je iets opslaat laadt Vigil zichzelf opnieuw. Dat duurt een paar seconden; de alarmstatus blijft behouden.

**Gebruikers** (gebruiker toevoegen)

| Naam | Code | Toegestane modi | Mag sabotage omzeilen |
|---|---|---|---|
| Anna | 1234 | leeg (alles) | aan |
| Bob | 5678 | alleen thuis | uit |

**Sensorgroepen.** Een sensorgroep bepaalt in welke modi de sensoren erin bewaken. Bij een nieuwe installatie bestaan er al twee, die je gewoon gebruikt:

| Naam | Actief in modi | Voor |
|---|---|---|
| Buitenschil | thuis, weg, nacht | deuren en ramen |
| Binnen | weg | beweging (PIR) |

*Heb je de vorige versie al geïnstalleerd?* Dan zet Vigil bij het opstarten je oude "modi per sensor" automatisch om in sensorgroepen, met namen als "Weg" en "Thuis + Weg + Nacht". Daar verandert niets aan het gedrag; je kunt ze hernoemen en op het tabblad Sensorgroepen controleren. Kijk ook op het Overzicht bij "Wat bewaakt elke modus".

**Sensoren** (sensor toevoegen; de naam bepaalt de entiteitsnamen, houd je aan deze namen). Kies bij een inbraaksensor in welke sensorgroepen hij zit. Kies je een deurcontact of bewegingssensor als entiteit, dan stelt het paneel zelf de passende groep voor.

| Naam | Entiteit | Klasse | Type | Sensorgroep | Bij open aan einde uitlooptijd |
|---|---|---|---|---|---|
| Front door | binary_sensor.vigil_test_front_door | inbraak | vertraagd | Buitenschil | omzeilen met melding |
| Living PIR | binary_sensor.vigil_test_living_pir | inbraak | direct | Binnen | wachten tot dicht |
| Kitchen PIR | binary_sensor.vigil_test_kitchen_pir | inbraak | direct | Binnen | wachten tot dicht |
| Smoke | binary_sensor.vigil_test_smoke | brand | | | |
| Tamper | binary_sensor.vigil_test_tamper | sabotage | | | |
| Water | binary_sensor.vigil_test_water | water | | | |

Bij "Front door" kun je bij **Batterijsensor** niets invullen. Bij **Kitchen PIR** vul je als batterijsensor `sensor.vigil_test_battery_level` in.

**Bevestigingsregel:** (alleen sensoren van het type *direct* worden aangeboden; Front door is vertraagd en doet dus niet mee) naam `Downstairs`, sensoren Living PIR en Kitchen PIR, benodigd 2, tijdvenster 60 s, melden als onbevestigd: aan.

**Meldingskanaal 1:** naam `Persistent`, dienst `persistent_notification`, alle berichten aan, vertraging 0. Deze melding verschijnt in de zijbalk van Home Assistant (het belletje), dus je hebt geen telefoon nodig. Later kun je een tweede kanaal met je telefoon toevoegen (`mobile_app_...`).

**Meldingskanaal 2 (escalatie):** naam `Escalation`, dienst `persistent_notification`, alleen "Alarm", vertraging 30 s.

**Sirene:** naam `Test siren`, aan/uit `switch.vigil_test_siren`, klinkt bij alles, maximale duur `60`, opnieuw aanzetten `0`, batterijsensor `sensor.vigil_test_battery_level`, voedingsmodus `sensor.vigil_test_siren_power_mode`. Geef de sirene de eerste test geen eigen toon of volume.

## 5. Een dashboard maken

**Het voorbeelddashboard:** maak een nieuw dashboard (**Instellingen → Dashboards → Dashboard toevoegen → Nieuw dashboard vanaf nul**), open het, kies rechtsboven het potlood, de drie puntjes en **Ruwe configuratie-editor**. Plak de inhoud van `examples/dashboard.yaml` (uit de zip) erin en sla op. De voorbeeldsensoren in de kaart *Sensors* heten zoals in hoofdstuk 4 (Front door, Living PIR, Smoke, Tamper); pas ze aan als jij andere namen gebruikt. Het testhuis heeft een watersensor: haal in de kaart *Alarms* het commentaarteken (`#`) weg voor de regel `binary_sensor.vigil_alarm_water_alarm`.

**Een testdashboard voor de schakelaars:** maak een tweede weergave of een nieuw dashboard met een **Entiteitenkaart** met:

`input_boolean.vigil_test_front_door`, `..._living_pir`, `..._kitchen_pir`, `..._smoke`, `..._tamper`, `..._water`, `..._lamp`, `input_number.vigil_test_battery`, `input_select.vigil_test_power`, `switch.vigil_test_siren`, `light.vigil_test_lamp`.

Hou ook **Ontwikkelaarstools → Acties** open: daar roep je de services aan.

## 6. De testen

Zet na elke test alles terug: alle testschakelaars uit, alarm uitgeschakeld. De code is steeds `1234` tenzij anders vermeld. "Melding" betekent: kijk in het belletje in de zijbalk. De meldingsteksten staan in de **systeemtaal** (Instellingen → Systeem → Algemeen); in deze gids staan ze in het Nederlands, bij een Engelse systeemtaal zijn ze Engels (bijvoorbeeld "Single trigger without confirmation").

| # | Doen | Verwacht |
|---|---|---|
| **1. Basis** | Open de integratie | Een apparaat "Vigil Alarm" en een apparaat per sensor (Front door, Living PIR, …). Alarmstatus `disarmed`. Elke sensor toont status "Dicht". |
| **2. Thuis inschakelen** | Alarmpaneel: Thuis, code 1234 | Direct `armed_home` (uitlooptijd 0). Laatste melding: `armed`, door Anna. Uitschakelen met code 1234 werkt. |
| **3. Uitlooptijd** | Inschakelen Weg | Status `arming`, na 20 s `armed_away`. Het attribuut `delay_end` toont het eindtijdstip. |
| **4. Inlooptijd** | Armed weg, zet Front door aan | Status `pending`. Binnen 15 s uitschakelen met code: geen alarm. Nogmaals: laat de 15 s verlopen: `triggered`, oorzaak `intrusion`, melding "ALARM: inbraak (Front door)…", sirene aan, "Inbraakalarm" aan. |
| **5. Bevestigingsregel** | Armed weg, alleen Living PIR aan | Geen alarm; melding "Eén melding zonder bevestiging". Daarna binnen 60 s ook Kitchen PIR aan: `triggered`, `confirmed_by` bevat beide. |
| **6. Open bij inschakelen** | Front door aan, Living PIR aan, dan Inschakelen Weg | Na 20 s `armed_away`. Front door status "Omzeild bij inschakelen" met een melding, Living PIR "Wacht tot dicht". Living PIR uit: wordt weer bewaakt. |
| **7. Brand** | Smoke aan (niet ingeschakeld) | Direct `triggered`, oorzaak `fire`, sirene aan. Inschakelen is geweigerd. Smoke uit, uitschakelen met code. |
| **8. Omzeilen** | Zet de schakelaar "Living PIR Omzeilen" aan. Roep daarna de actie `vigil.bypass` aan met sensor `binary_sensor.vigil_test_kitchen_pir` (zonder code) en `vigil.unbypass`. Probeer `vigil.bypass` voor `binary_sensor.vigil_test_smoke`. | Als beheerder in de interface heb je geen code nodig. Living PIR toont "Omzeild". Smoke heeft geen omzeil-schakelaar en de actie wordt geweigerd (brand kan niet omzeild worden). Bij uitschakelen vervalt de omzeiling. De regel dat Bob geen sabotage mag omzeilen geldt voor gewone gebruikers; als beheerder omzeil je sabotage wel, en dat is zo bedoeld. Dit onderscheid is in de automatische tests gedekt. |
| **9. Codes en rechten** | Bob (5678): Thuis lukt, Weg niet. Foute code. Geen code. | Bob kan alleen thuis. Een foute code en een ontbrekende code geven een foutmelding. Uitschakelen kan nooit zonder code. |
| **10. Escalatie** | Alarm laten afgaan (test 4) en niet uitschakelen | Direct de melding van `Persistent`, na 30 s ook die van `Escalation`. Bij een tweede alarm dat je binnen 30 s uitschakelt komt de escalatiemelding niet. Probeer ook de actie `vigil.acknowledge` (code 1234) binnen 30 s: geen escalatie. |
| **11. Sirene** | Actie `vigil.test_siren` (duur 5). Tijdens een alarm: `vigil.silence` met code. | Testsirene is 5 s aan en gaat vanzelf uit. Tijdens een alarm weigert de test. Na `silence` gaat `switch.vigil_test_siren` uit terwijl de alarmstatus `triggered` blijft. Na de maximale duur (60 s) gaat de sirene uit. |
| **12. Herstart** | Armed weg. Herstart Home Assistant. | Na de herstart nog steeds `armed_away`. |
| **13. Alarm tijdens herstart** | Armed weg, Front door aan (inlooptijd 15 s), herstart direct Home Assistant | Een herstart duurt langer dan 15 s. Na het opstarten is de status `triggered`. Het attribuut `t` van `sensor.vigil_alarm_last_event` (bij het event `triggered`) toont het moment dat de inlooptijd afliep, niet het moment van opstarten. |
| **14. Opstarten** | Direct na een herstart, probeer te schakelen | Eerste 10 s: "nog aan het opstarten". Geen valse storingen of alarmen door sensoren die nog niet geladen zijn. |
| **15. Onbereikbare sensor** | Ontwikkelaarstools → Toestanden: zet `binary_sensor.vigil_test_living_pir` met de hand op `unavailable`. Probeer Weg in te schakelen. | Inschakelen Weg wordt geweigerd (reden: sensor onbereikbaar). Inschakelen Thuis lukt. Herstel door de bijbehorende schakelaar aan en uit te zetten. |
| **16. Water** | Water aan (ook als ingeschakeld) | "Wateralarm" aan met de sensor in het attribuut. De alarmstatus verandert niet. Water uit: beëindigd. |
| **17. Batterij en voeding** | `input_number.vigil_test_battery` naar 15. Daarna `input_select.vigil_test_power` op `battery`. | Twee meldingen: "Batterij bijna leeg: Kitchen PIR (15%)" en "…: Test siren (15%)" (zone en sirene gebruiken in de test dezelfde sensor). Voor de voedingsmodus: "Sirene Test siren heeft geen netstroom meer…". Het attribuut `problems` van het alarm toont beide. Terugzetten geeft "Batterij weer in orde" en "weer netstroom". |
| **18. Alleen beheerder** | Maak een gebruiker zonder beheerdersrechten. Log in als die gebruiker. | De gebruiker kan het alarmpaneel gebruiken (met code) maar de integratie niet configureren. |
| **19. Taal** | **Instellingen → Systeem → Algemeen → Taal** op Nederlands, test een alarm | De tekst van de meldingen volgt de **systeemtaal**, niet de taal van je gebruikersprofiel. De namen in de interface volgen je profieltaal. |
| **20. Wijzigen** | Wijzig een sensor, een sensorgroep en de uitlooptijd | De integratie laadt zelf opnieuw; de alarmstatus blijft zoals hij was (ongeldige combinaties worden met een reden geweigerd). |

### Extra testen: voorinstelling, blueprints en dashboard

**Voorbereiding voor de blueprints:** kopieer de map `vigil` uit `vigil-alarm/blueprints/automation/` naar `config/blueprints/automation/` (maak de mappen aan als ze niet bestaan). Je krijgt `config/blueprints/automation/vigil/flash_lights_on_alarm.yaml` en vijf andere bestanden. Laad daarna de automatiseringen opnieuw: **Ontwikkelaarstools → YAML → Automatiseringen opnieuw laden**. (Met een openbare GitHub-opslagplaats kun je ze ook importeren met de knoppen in de README.) Maak een automatisering via **Instellingen → Automatiseringen → Automatisering maken → Blueprint gebruiken**.

| # | Doen | Verwacht |
|---|---|---|
| **21. Voorinstelling** | Tabblad Sirenes, *Sirene toevoegen*. Kies als sirene `switch.vigil_test_siren`, kies bij *Voorinstelling* "Sonoff SNZB-09P (Zigbee2MQTT)". | Toon, volume en duur worden ingevuld (bij inbraak `siren_classic` en `high`, bij brand `siren_warning` en `max`; waarde bij batterijvoeding `battery`). Onder het veld staat "Geen andere entiteiten gevonden bij dit apparaat; kies ze zelf", want de virtuele sirene is geen Zigbee-apparaat. Opslaan zonder toon- en volume-entiteit geeft een foutmelding (een toon of volume heeft een entiteit nodig): vul dan `select`-entiteiten in of wis de tonen en volumes. Het veld *Voorinstelling* wordt zelf niet bewaard (bewerken toont het weer leeg). Heb je een echte SNZB-09P met Zigbee2MQTT, kies dan de `siren_on`-schakelaar en controleer of de andere entiteiten worden gevonden. |
| **22. Blueprint: lampen knipperen** | Maak een automatisering met "Vigil - Flash lights during an alarm": Vigil events = `event.vigil_alarm_alarm_events`, alarm = `alarm_control_panel.vigil_alarm`, lampen = `light.vigil_test_lamp`, knipperen bij brand. Zet daarna `input_boolean.vigil_test_smoke` aan. | `light.vigil_test_lamp` gaat om de 2 seconden aan en uit zolang het alarm actief is. Schakel uit met code 1234: het knipperen stopt en de lamp staat weer zoals voor het alarm. Doe de test ook met de lamp aan vóór het alarm: daarna staat hij weer aan. |
| **23. Blueprint: inschakelen op tijd** | Automatisering "Vigil - Arm at a set time": tijd over twee minuten, modus Nacht, code 1234 (in dit testhuis is dat Anna). | Op dat tijdstip gaat het alarm naar *arming* en daarna `armed_night`. Is een inbraaksensor die in Nacht bewaakt onbereikbaar, dan wordt inschakelen geweigerd en blijft het alarm uit (met een bericht als je een melding-entiteit kiest). Verwijder de automatisering na de test. |
| **24. Blueprint: events** | Automatisering "Vigil - Run your own actions on alarm events": events `triggered` en `disarmed`, actie "Melding" via `persistent_notification.create` met bericht `{{ event_type }} {{ data.cause | default('') }}`. | Bij een alarm komt "triggered fire" in de meldingen, bij uitschakelen "disarmed". |
| **25. Dashboard** | Plak het voorbeelddashboard (hoofdstuk 5). Zet Smoke aan. | De alarmpaneelkaart toont het alarm; "Status" noemt oorzaak *fire* en sensor *Smoke*; de kaart "Needs attention" verschijnt alleen als er iets mis is (bijvoorbeeld Living PIR op `unavailable`); de logboekkaart toont de events; de knop "Silence the siren" dempt de sirene na bevestiging. |

## 7. Wat je terugmeldt

Per test dat iets anders uitpakt:

- het testnummer en wat je deed;
- wat je verwachtte en wat er gebeurde;
- de logregels met `vigil`: **Instellingen → Systeem → Logboeken**, zoek op `vigil`. Voor meer detail zet je in `configuration.yaml`:

  ```yaml
  logger:
    default: warning
    logs:
      custom_components.vigil: debug
  ```
- bij formulieren: een schermafbeelding.

## 8. Als het niet werkt

- **"Vigil Alarm" staat niet in de lijst:** controleer het pad `config/custom_components/vigil/manifest.json`, herstart volledig en ververs de browser. Kijk in het logboek naar `vigil`.
- **De zijbalk toont geen "Vigil":** alleen beheerders zien hem. Ververs hard, herstart Home Assistant volledig en kijk in het logboek of `vigil` een fout meldt. Er is geen tweede manier om te configureren; blijft het paneel weg, stuur dan de logregel.
- **Het paneel blijft leeg of toont "kon niet geladen worden":** de integratie is niet actief (kijk onder *Apparaten en diensten* of er een fout staat). Ververs de browser.
- **Foutmelding bij het openen van het eerste formulier (naam en basisinstellingen):** meestal een JSON- of vertaalfout of een versieverschil. Stuur de logregel.
- **Entiteiten heten anders dan in deze gids:** de namen volgen uit wat je invulde. Controleer de echte namen onder **Instellingen → Apparaten en diensten → Vigil Alarm**.
- **Testschakelaars verdwijnen na een herstart:** gebruik de helpers uit het testpakket, niet losse toestanden uit de Ontwikkelaarstools.

## 9. Opruimen

1. Verwijder de integratie: **Instellingen → Apparaten en diensten → Vigil Alarm → ⋮ → Verwijderen**.
2. Verwijder `custom_components/vigil` en `packages/vigil_test_package.yaml` uit de share **config**, en haal zo nodig de regels `packages` uit `configuration.yaml`.
3. Herstart Home Assistant. Zet de Samba-add-on uit als je hem niet meer nodig hebt.
