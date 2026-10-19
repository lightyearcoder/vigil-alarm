# Vigil Alarm: installeren op Home Assistant OS en testen

Deze gids is voor Home Assistant OS (HAOS). Je plaatst de map `vigil_alarm` in de configuratiemap, voegt een testpakket met virtuele sensoren toe en doorloopt daarna de testen. Alles gebeurt zonder echte sensoren of sirene.

**Let op:** dit is een testversie van een zelfgebouwde integratie, geen gecertificeerd alarmsysteem. De integratie is tot nu toe alleen getest in een testomgeving met Home Assistant 2026.2.3. Verwacht afwijkingen in een echte installatie en meld ze (zie hoofdstuk 7).

---

## 1. Voorbereiding

1. Controleer je versie: **Instellingen → Info**. Minimaal 2026.2.3.
2. Maak een back-up: **Instellingen → Systeem → Back-ups → Back-up maken**. Wacht tot hij klaar is.
3. Pak `vigil-alarm.zip` uit op je Mac. Je krijgt een map `vigil-alarm`. Daarin staat `custom_components/vigil_alarm`. Alleen die map `vigil_alarm` ga je kopiëren.

## 2. De bestanden op Home Assistant zetten

Je hebt toegang tot de configuratiemap nodig. De makkelijkste weg op een Mac is de Samba-add-on.

1. **Instellingen → Add-ons → Add-on store**, zoek **Samba share**, installeer hem.
2. Open de add-on, tab **Configuratie**: vul bij gebruikersnaam en wachtwoord iets in en sla op. Start de add-on (tab **Info**).
3. In Finder: **Ga → Verbind met server** (⌘K) en typ `smb://homeassistant.local` (lukt dat niet, gebruik het IP-adres van je Home Assistant). Log in met de zojuist gekozen gegevens.
4. Open de share **config**. Zie je daar `configuration.yaml`, dan zit je goed.
5. Bestaat de map `custom_components` nog niet, maak hem dan aan.
6. Kopieer de map `vigil_alarm` (uit `vigil-alarm/custom_components/`) in `config/custom_components/`. Het resultaat is `config/custom_components/vigil_alarm/manifest.json`. Controleer dat precies dit pad klopt: één map te veel of te weinig is de meest voorkomende fout.

*Alternatief:* de add-on **Terminal & SSH** met `scp -r custom_components/vigil_alarm root@homeassistant.local:/config/custom_components/`.

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
3. Klik in de zijbalk op **Vigil Alarm** (het schildje met huisje; alleen zichtbaar voor beheerders). Zie je het niet, ververs dan de browser hard. Hier staan tabbladen **Overzicht, Sensoren, Sensorgroepen, Bevestigingsregels, Gebruikers, Meldingen, Sirenes, Instellingen** en **Over**. Bovenaan het Overzicht staat de kaart **Klaar voor gebruik?**: die laat zien wat er nog ontbreekt en heeft bij elk punt een knop naar de juiste plek. Voeg per tabblad met de knop bovenaan de onderdelen hieronder toe. Elke rij heeft knoppen om te bewerken, te kopiëren of te verwijderen. Sensoren, gebruikers enzovoort bewerk je alleen hier; onder *Apparaten en diensten* staat alleen het alarm zelf (met de knop *Opnieuw configureren* voor de basisinstellingen).
   Elke keer dat je iets opslaat laadt Vigil zichzelf opnieuw. Dat duurt een paar seconden; de alarmstatus blijft behouden.

**Gebruikers** (gebruiker toevoegen)

| Naam | Code | Toegestane modi | Mag sabotage omzeilen |
|---|---|---|---|
| Anna | 1234 | leeg (alles) | aan |
| Bob | 5678 | alleen thuis | uit |

**Sensorgroepen.** Een sensorgroep bepaalt in welke modi de sensoren erin bewaken. Een nieuwe installatie heeft er nog geen. Klik op het Overzicht in de kaart **Klaar voor gebruik?** op **Standaardgroepen maken** (of in het venster *Sensoren zoeken*). Vigil maakt dan twee groepen aan, die je gewoon gebruikt:

| Naam | Actief in modi | Voor |
|---|---|---|
| Buitenschil | thuis, weg, nacht | deuren en ramen |
| Binnen | weg | beweging (PIR) |

Staat Home Assistant op een andere taal, dan heten ze bijvoorbeeld *Perimeter* en *Interior* (Engels), *Außenhaut* en *Innenraum* (Duits), *Périmètre* en *Intérieur* (Frans), *Perimetro* en *Interni* (Italiaans) of *Perímetro* en *Interior* (Spaans). Een soort die je al hebt, maakt Vigil niet nog eens aan.

*Heb je de vorige versie al geïnstalleerd?* Dan zet Vigil bij het opstarten je oude "modi per sensor" automatisch om in sensorgroepen, met namen als "Weg" en "Thuis + Weg + Nacht". Daar verandert niets aan het gedrag; je kunt ze hernoemen en op het tabblad Sensorgroepen controleren. Kijk ook op het Overzicht bij "Wat bewaakt elke modus".

**Sensoren** (sensor toevoegen, of zoek ze met de knop **Sensoren zoeken**, zie test 26; de naam bepaalt de entiteitsnamen, houd je aan deze namen). Kies bij een inbraaksensor in welke sensorgroepen hij zit. Kies je een deurcontact of bewegingssensor als entiteit, dan stelt het paneel zelf de passende groep voor.

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

**Het voorbeelddashboard:** maak een nieuw dashboard (**Instellingen → Dashboards → Dashboard toevoegen → Nieuw dashboard vanaf nul**), open het, kies rechtsboven het potlood, de drie puntjes en **Ruwe configuratie-editor**. Plak de inhoud van `examples/dashboard.yaml` (uit de zip) erin en sla op. De voorbeeldsensoren in de kaart *Sensors* heten zoals in hoofdstuk 4 (Front door, Living PIR, Smoke, Tamper); pas ze aan als jij andere namen gebruikt.

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
| **8. Omzeilen** | Zet de schakelaar "Living PIR Omzeilen" aan. Roep daarna de actie `vigil_alarm.bypass` aan met sensor `binary_sensor.vigil_test_kitchen_pir` (zonder code) en `vigil_alarm.unbypass`. Probeer `vigil_alarm.bypass` voor `binary_sensor.vigil_test_smoke`. | Als beheerder in de interface heb je geen code nodig. Living PIR toont "Omzeild". Smoke heeft geen omzeil-schakelaar en de actie wordt geweigerd (brand kan niet omzeild worden). Bij uitschakelen vervalt de omzeiling. De regel dat Bob geen sabotage mag omzeilen geldt voor gewone gebruikers; als beheerder omzeil je sabotage wel, en dat is zo bedoeld. Dit onderscheid is in de automatische tests gedekt. |
| **9. Codes en rechten** | Bob (5678): Thuis lukt, Weg niet. Foute code. Geen code. | Bob kan alleen thuis. Een foute code en een ontbrekende code geven een foutmelding. Uitschakelen kan nooit zonder code. |
| **10. Escalatie** | Alarm laten afgaan (test 4) en niet uitschakelen | Direct de melding van `Persistent`, na 30 s ook die van `Escalation`. Bij een tweede alarm dat je binnen 30 s uitschakelt komt de escalatiemelding niet. Probeer ook de actie `vigil_alarm.acknowledge` (code 1234) binnen 30 s: geen escalatie. |
| **11. Sirene** | Actie `vigil_alarm.test_siren` (duur 5). Tijdens een alarm: `vigil_alarm.silence` met code. | Testsirene is 5 s aan en gaat vanzelf uit. Tijdens een alarm weigert de test. Na `silence` gaat `switch.vigil_test_siren` uit terwijl de alarmstatus `triggered` blijft. Na de maximale duur (60 s) gaat de sirene uit. |
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

**Voorbereiding voor de blueprints:** kopieer de map `vigil_alarm` uit `vigil-alarm/blueprints/automation/` naar `config/blueprints/automation/` (maak de mappen aan als ze niet bestaan). Je krijgt `config/blueprints/automation/vigil_alarm/flash_lights_on_alarm.yaml` en vijf andere bestanden. Laad daarna de automatiseringen opnieuw: **Ontwikkelaarstools → YAML → Automatiseringen opnieuw laden**. (Met een openbare GitHub-opslagplaats kun je ze ook importeren met de knoppen in de README.) Maak een automatisering via **Instellingen → Automatiseringen → Automatisering maken → Blueprint gebruiken**.

| # | Doen | Verwacht |
|---|---|---|
| **21. Voorinstelling** | Tabblad Sirenes, *Sirene toevoegen*. Kies als sirene `switch.vigil_test_siren`, kies bij *Voorinstelling* "Sonoff SNZB-09P (Zigbee2MQTT)". | Toon, volume en duur worden ingevuld (bij inbraak `siren_classic` en `high`, bij brand `siren_warning` en `max`; waarde bij batterijvoeding `battery`). Onder het veld staat "Geen andere entiteiten gevonden bij dit apparaat; kies ze zelf", want de virtuele sirene is geen Zigbee-apparaat. Opslaan zonder toon- en volume-entiteit geeft een foutmelding (een toon of volume heeft een entiteit nodig): vul dan `select`-entiteiten in of wis de tonen en volumes. Het veld *Voorinstelling* wordt zelf niet bewaard (bewerken toont het weer leeg). Heb je een echte SNZB-09P met Zigbee2MQTT, kies dan de `siren_on`-schakelaar en controleer of de andere entiteiten worden gevonden. |
| **22. Blueprint: lampen knipperen** | Maak een automatisering met "Vigil - Flash lights during an alarm": Vigil events = `event.vigil_alarm_alarm_events`, alarm = `alarm_control_panel.vigil_alarm`, lampen = `light.vigil_test_lamp`, knipperen bij brand. Zet daarna `input_boolean.vigil_test_smoke` aan. | `light.vigil_test_lamp` gaat om de 2 seconden aan en uit zolang het alarm actief is. Schakel uit met code 1234: het knipperen stopt en de lamp staat weer zoals voor het alarm. Doe de test ook met de lamp aan vóór het alarm: daarna staat hij weer aan. |
| **23. Blueprint: inschakelen op tijd** | Automatisering "Vigil - Arm at a set time": tijd over twee minuten, modus Nacht, code 1234 (in dit testhuis is dat Anna). | Op dat tijdstip gaat het alarm naar *arming* en daarna `armed_night`. Is een inbraaksensor die in Nacht bewaakt onbereikbaar, dan wordt inschakelen geweigerd en blijft het alarm uit (met een bericht als je een melding-entiteit kiest). Verwijder de automatisering na de test. |
| **24. Blueprint: events** | Automatisering "Vigil - Run your own actions on alarm events": events `triggered` en `disarmed`, actie "Melding" via `persistent_notification.create` met bericht `{{ event_type }} {{ data.cause | default('') }}`. | Bij een alarm komt "triggered fire" in de meldingen, bij uitschakelen "disarmed". |
| **25. Dashboard** | Plak het voorbeelddashboard (hoofdstuk 5). Zet Smoke aan. | De alarmpaneelkaart toont het alarm; "Status" noemt oorzaak *fire* en sensor *Smoke*; de kaart "Needs attention" verschijnt alleen als er iets mis is (bijvoorbeeld Living PIR op `unavailable`); de logboekkaart toont de events; de knop "Silence the siren" dempt de sirene na bevestiging. |

### Extra testen: inrichten, codes en controle

| # | Doen | Verwacht |
|---|---|---|
| **26. Sensoren zoeken** | Tabblad Sensoren, knop *Sensoren zoeken*. | Een breed venster met de gevonden sensoren (deur, raam, beweging, rook, gas, water, sabotage) van echte of testapparaten, met onder elke naam de entiteit en de integratie. Sensoren die je al hebt staan grijs met "al in gebruik". Vigils eigen indicatoren staan er niet in. Bij een deurcontact staat "Ingang" aan of uit; de batterij- en sabotagesensor van hetzelfde apparaat staan bij "Erbij". Er is nog niets opgeslagen. |
| **27. Meerdere tegelijk toevoegen** | Vink twee sensoren aan en klik *2 toevoegen*. Doe het daarna nog eens met een naam die al bestaat. | De eerste keer komen beide in één keer in de lijst (met een eigen sabotage-item als er een sabotagesensor bij hoort). De tweede keer krijg je een duidelijke foutmelding met de naam van de sensor en wordt er niets opgeslagen. |
| **28. Ontdekkingsgegevens** | Klik in het zoekvenster op *Kopieer ontdekkingsgegevens* en plak het ergens. | Een lijst met per entiteit alleen domein, device class, integratie, een apparaatnummer, categorie en eenheid. Geen namen, entiteit-id's of adressen. |
| **29. Klaar voor gebruik?** | Kijk op het Overzicht. Los een punt op (bijvoorbeeld een gebruiker met code toevoegen). | Elk punt heeft de knop *Ga erheen* (of *Standaardgroepen maken*). Eerst staan de punten die "Eerst regelen" zijn, dan de adviezen. Is een punt opgelost, dan verdwijnt het. Staat alles goed, dan staat er "Alles is ingesteld". |
| **30. Telefoon als kanaal** | Verwijder alle meldingskanalen. Heb je de Home Assistant-app op je telefoon, kijk dan op het Overzicht. | Bij het punt over het meldingskanaal staat de knop *Telefoon toevoegen: <naam van je telefoon>*. Die maakt het kanaal aan en stuurt een testmelding. Daarna staat er een kanaal en verdwijnt het punt. |
| **31. Foute codes** | Schakel vijf keer binnen vijf minuten met een foute code. Probeer dan de goede code. | Na de vijfde foute code is er een gebeurtenis `code_locked`. Gedurende vijf minuten wordt ook de goede code geweigerd. Daarna werkt hij weer. Een beheerder zonder code in het paneel kan wel gewoon bedienen. |
| **32. Minimale codelengte** | Instellingen: zet de minimale codelengte op 6. Voeg een gebruiker met een code van 4 cijfers toe. | De gebruiker wordt geweigerd met de melding dat de code minstens 6 tekens moet hebben. Waarden buiten 4 tot 12 worden geweigerd. |
| **33. Alarmindicatoren en entiteitsnamen** | Kijk bij de entiteiten van Vigil. | Er zijn altijd de binary sensors voor inbraak, brand, gas, sabotage en water, ook als je geen sensor van die klasse hebt. De entiteit-id's eindigen op de Engelse naam (bijvoorbeeld `binary_sensor.vigil_alarm_intrusion_alarm`), ook als Home Assistant op Nederlands staat. |
| **34. Code controleren** | Roep de actie `vigil_alarm.check_code` aan met een goede en een foute code. | Een goede code geeft geen fout. Een foute code geeft een foutmelding en telt mee voor de blokkade (test 31). |
| **35. Batterij laag als aan/uit** | Zet bij een sensor een `binary_sensor` met device class battery als batterijsensor. Zet die aan. | Er komt de melding "Batterij bijna leeg: <naam>" (zonder percentage) en in het attribuut `problems` staat de sensor. Zet je hem uit, dan komt "Batterij weer in orde". In de sensorlijst staat bij Batterij "laag" of "ok". |
| **36. Dashboard kopiëren** | Overzicht, kaart *Dashboard*, knop *Kopieer dashboard*. Plak het in een nieuw dashboard (ruwe configuratie-editor). | Het dashboard toont jouw sensoren en alarmentiteiten met de goede entiteit-id's; alle kaarten werken zonder voorbeeldnamen aan te passen. |
| **37. Sensorlijst op het aanraakpaneel** | Heb je het ESPHome-paneel? Zet bij het paneel in Vigil *Sensorlijst* op *pas na ontgrendelen*, geef het een installateurscode en bekijk de sensorlijst op het paneel. | Zonder code zie je alleen hoeveel sensoren open staan; met de installateurscode van het paneel is de lijst zichtbaar tot de ontgrendeltijd voorbij is. Zie `esphome/README.md`. |
| **38. Wat is nieuw** | Na een update van Vigil: open het paneel. | Op het tabblad *Over* staat een badge "nieuw" tot je het bekijkt. De eerste keer in een browser staat er geen badge. |
| **39. Diagnostics** | Apparaten en diensten → Vigil Alarm → ⋮ → Diagnostische gegevens downloaden. | Een bestand met instellingen, onderdelen en de status. Gebruikersnamen, codes en tags staan er niet in. |
| **40. Repairs** | Zet `binary_sensor.vigil_test_living_pir` met de hand op `unavailable`, of zet de batterij van de test op 15. Kijk onder Instellingen → Systeem → Reparaties. | Er staat een reparatie "Sensor niet bereikbaar: Living PIR" (of "Batterij bijna leeg: … (15%)"). Herstel je het, dan verdwijnt hij vanzelf. Ontbrekende instellingen (zoals een meldingskanaal) geven geen reparatie; die staan in *Klaar voor gebruik?*. |
| **41. Logboek** | Schakel het alarm in en uit, laat een sensor afgaan. Open het tabblad *Logboek*. | De gebeurtenissen staan er, de nieuwste bovenaan, met een leesbare naam, het onderdeel (bijvoorbeeld Front door), wie het deed en het resultaat. Er staan geen codes in. |
| **42. Logboek downloaden** | Klik op *Download (JSON Lines)* en *Download (CSV)*. Open de bestanden in een teksteditor of Excel. | JSON Lines heeft één object per regel; CSV opent met kolommen `time, event, source, user, item, result, detail`. Tijden eindigen op `Z` (UTC). Het bestand begint met de oudste gebeurtenis. |
| **43. Logboek bewaren** | Herstart Home Assistant, kijk daarna in het logboek. Zet bij *Instellingen* het aantal dagen op 1 en daarna op een ongeldige waarde (0). | Na de herstart staan de oude gebeurtenissen er nog. 0 wordt geweigerd met de melding dat het tussen 1 en 3650 moet liggen. |
| **44. Zelftest-kaart** | Overzicht, kaart *Zelftest*. | De laatste stille controle (binnen een uur na het starten, daarna dagelijks), de laatste sirenetest ("nog niet" zolang je niet getest hebt) en wanneer de volgende aan de beurt is. |
| **45. Sirene nu testen** | Klik op *Sirene nu testen* (alleen zichtbaar als er een sirene is ingesteld). | De sirene klinkt 2 seconden. In het logboek staat `selftest_siren_tested`, de kaart toont de nieuwe tijd. Tijdens een echt alarm wordt de test geweigerd. |
| **46. Herinnering** | Zet bij *Instellingen* het interval op 1 dag en wacht tot het is verstreken. Kijk op je telefoon. | Je krijgt een herinnering op de kanalen met storingen en mededelingen. Op een telefoon met de app staat een knop *Sirene testen*; die laat de sirene klinken. Na 3 dagen volgt een tweede herinnering. |
| **47. Ontbrekend kanaal** | Verwijder een `notify`-dienst van een kanaal (bijvoorbeeld door de app van een oude telefoon te verwijderen) en wacht op de dagelijkse controle (of herstart). | Er komt een reparatie over het ontbrekende meldkanaal en de kaart noemt het kanaal. Herstel je het, dan verdwijnt de reparatie. |
| **48. Achterstallig** | Laat een herinnering 10 dagen onbeantwoord. | Er staat een reparatie dat de sirenetest achterstallig is. Een test haalt hem direct weg. |
| **49. Instellingen zelftest** | Zet de sirenetijd op 9 en daarna het laatste uur voor het eerste uur. | 9 wordt geweigerd (1 tot 5); het laatste uur moet na het eerste liggen. Interval 0 zet de herinnering uit; de kaart zegt dat. |
| **50. Hartslag instellen** | Maak een check bij een bewakingsdienst (bijvoorbeeld Healthchecks.io), plak de ping-URL bij *Instellingen → Hartslag-adres* en sla op. Kijk op het Overzicht. | De kaart *Hartslag* toont het interval. Binnen een minuut staat er bij *Laatst gelukt* een tijd en de check bij de dienst is groen. Een adres dat niet met http:// of https:// begint, wordt geweigerd. |
| **51. Nu testen** | Klik op *Nu testen*. | Een melding dat de hartslag is aangekomen, en de tijd van *Laatst gelukt* wordt bijgewerkt. |
| **52. Hartslag bij uitgeschakeld alarm** | Laat het alarm uit staan en kijk bij de dienst na tien minuten. | De aanroepen komen ook binnen terwijl het alarm uit staat. |
| **53. Mislukken** | Zet een fout adres (bijvoorbeeld met een extra letter in de code) en klik op *Nu testen*. Doe dat drie keer. | De kaart toont "Mislukt" met de reden (bijvoorbeeld HTTP 404). Na drie keer komt er een reparatie "Hartslag kan niet worden verstuurd". Herstel je het adres en test je opnieuw, dan verdwijnt hij. |
| **54. Geheim** | Download de diagnostics en zoek op een deel van je ping-URL. Kijk ook in het logboek van Home Assistant. | De URL staat er nergens in; in de diagnostics staat "redacted". |
| **55. Uitval bewijzen** | Zet Home Assistant langer uit dan de periode plus de respijttijd van je check. | De dienst stuurt je een bericht. Zet je Home Assistant weer aan, dan wordt de check weer groen. |
| **56. Paneel registreren** | Tabblad *Panelen → Paneel toevoegen*: naam, paneel-id (apparaatnaam), modi, sensorlijst *pas na ontgrendelen*, installateurscode. Kijk daarna bij Entiteiten naar `sensor.<paneel_id>_profile`. | Het paneel staat in de lijst met een badge. De profielsensor bestaat, heeft `profile_version` 1 en bevat zonder ontgrendelen geen sensornamen (alleen aantallen). Er staat geen code of hash in. |
| **57. Afdwingen door Vigil** | Zet bij het paneel *Mag uitschakelen* uit en roep `vigil_alarm.disarm` aan met `source` = het paneel-id en een geldige code. | De oproep wordt geweigerd; in het logboek staat `panel_refused`. Zonder dat paneel-id als `source` werkt dezelfde oproep gewoon. |
| **58. Ontgrendelen en blokkade opheffen** | Druk bij het paneel op *Ontgrendelen*. Voer daarna drie keer een foute code in via het paneel en druk op *Blokkade opheffen*. | Na *Ontgrendelen* bevat het profiel de sensornamen tot de ontgrendeltijd voorbij is. Na drie foute codes is het paneel vergrendeld (standaard); *Blokkade opheffen* lost dat op, ook na een herstart. |
| **59. ESPHome-paneel met profiel** | Flash het paneel (`esphome/README.md`). Kijk eerst vóór je het paneel in Vigil toevoegt, daarna erna. | Voor registratie: *Niet gekoppeld* met het paneel-id. Daarna: alleen de toegestane modi als knoppen, de taal van het paneel, bij vergrendeld alleen 'Open: n'. Installateurscode opent de sensorlijst en de infopagina; omzeilen vraagt een gebruikerscode. Op het tabblad *Panelen* staan hardware en firmwareversie. |
| **60. Paneel geblokkeerd of niet bereikbaar** | Zet het paneel op *Geblokkeerd*. Zet de blokkade daarna weer uit en haal de stroom van het paneel 10 minuten weg. | Geblokkeerd: het paneel toont *Geblokkeerd* en doet niets. Na 10 minuten zonder verbinding: reparatie *Paneel niet bereikbaar* en een melding; zodra het terug is komt `panel_online`. Het alarm zelf verandert niet. |
| **61. Vigil-kaart op een tablet** | Maak een gewone gebruiker, registreer een paneel met die gebruiker, log de tablet in en zet `type: custom:vigil-card` op een dashboard (zie `docs/tablet.nl.md`). | De kaart toont de status en alleen de modi van het profiel. Inschakelen en uitschakelen met code werken; een verkeerde code geeft een foutmelding op het toetsenpaneel. De sensorlijst opent met de installateurscode en toont zonder die alleen een aantal. Open je het dashboard als beheerder, dan staat er *Niet gekoppeld*. |
| **62. Tablet offline** | Laat de Vigil-kaart een tijdje open staan, sluit daarna de browser op de tablet en wacht 10 minuten. | Het paneel in Vigil toont *Vigil-kaart actief* zolang de kaart open staat. Na 10 minuten stilte: reparatie *Paneel niet bereikbaar* en een melding. Open je de kaart weer, dan verdwijnt de reparatie binnen een minuut. |
| **63. Telefoon als paneel** | Maak in Home Assistant een gewoon account (een beheerder mag ook; die staat in de lijst als *(admin)*). Voeg onder *Panelen* een regel toe met dat account bij *Home Assistant-account (tablet of telefoon)*. Log op je telefoon in als dat account en zet de Vigil-kaart op een dashboard. | De kaart toont de bediening volgens de instellingen van die regel. Kies je een beheerdersaccount of een account dat al bij een ander paneel hoort, dan volgt een foutmelding. |
| **64. Elke code werkt, geen code geen bediening** | Schakel op die telefoon in met de code van een andere gebruiker. Probeer daarna uit te schakelen zonder code. | Met elke geldige code lukt het en de geschiedenis toont bijvoorbeeld *Bob (cleo-telefoon)*. Zonder code staat er *Een code is vereist*. Vijf keer een foute code blokkeert alleen die telefoon, niet de tablet of de automatiseringen. |
| **65. Andere accounts geweigerd** | Log in als een gewoon account dat nergens geregistreerd is (bijvoorbeeld van een kind) en probeer in of uit te schakelen, ook met een geldige code. | Het wordt geweigerd met *Gebruiker is niet geregistreerd* en `user_refused` staat in het logboek, zonder blokkade. Een beheerder, een geregistreerd account, een automatisering en het ESPHome-paneel werken gewoon. |
| **66. Bestaande installatie** | Bij een installatie zonder geregistreerd account (alleen ESPHome-panelen): bedien het alarm met een gewoon account met een geldige code. | Er verandert niets na de update; de filter begint pas zodra een account onder *Panelen* is geregistreerd. |
| **67. Welke code?** | Open op het paneel (of de Vigil-kaart) het toetsenbord om uit te schakelen en daarna dat voor *Sensoren bekijken*. | Onder de punten staat in grijs *Voer uw gebruikerscode in*, bij de sensorlijst *Voer de installateurscode in*. Een foutmelding vervangt de tekst in rood. |
| **68. Volgorde sensorlijst** | Open een deur en een raam en bekijk de sensorlijst op het paneel. | Open sensoren die omzeild kunnen worden staan bovenaan, daarna onbereikbare, open brand- en gassensoren, omzeilde en als laatste de gesloten sensoren. |
| **69. Taal van een nieuw paneel** | Voeg onder *Panelen* een paneel toe. | Het veld *Taal* heeft Nederlands, English, Deutsch, Français, Italiano en Español en staat op de taal van je Home Assistant-account (anders English; een andere taal dan deze zes geeft English). Je kiest eerst het soort apparaat: bij *ESPHome-paneel* vraagt het formulier om het paneel-id, bij *Tablet of telefoon* om het Home Assistant-account. |
| **70. Terugknop op de infopagina** | Open op het paneel de infopagina (tab *Info*, installateurscode). | Onderaan staan de tabs; met *Alarm* ga je terug naar het hoofdscherm en de ontgrendeling wordt vergeten. |
| **71. Eerste tik maakt wakker** | Laat het scherm van het paneel uitgaan en tik op de plek van een knop (bijvoorbeeld *Weg*). | Het scherm gaat aan, maar de knop wordt niet bediend. Een tweede tik doet het wel. Gaat het scherm aan omdat het alarm verandert, dan werkt de eerste tik direct. |
| **72. Geen sprong voor het uitgaan** | Laat een alarm in aankomstvertraging of alarm staan en kijk naar het paneel tot het scherm uitgaat. Tik daarna. | Het scherm springt vlak voor het uitgaan niet meer naar een ander scherm. Na de tik staat het uitschakelscherm er (bij aankomstvertraging of alarm), anders het hoofdscherm. |
| **73. Schermtijd en alarm** | Zet bij *Instellingen*, *Scherm van de panelen*, de tijd op 20 seconden en laat *Scherm ook uit laten gaan tijdens een alarm* uit. Zet het alarm aan en kijk of het scherm tijdens het aftellen blijft branden en 20 seconden na het inschakelen uitgaat. Veroorzaak een alarm: het scherm blijft aan en toont ALARM. Zet de instelling aan en veroorzaak opnieuw een alarm: het scherm gaat na 20 seconden uit. | Het scherm gaat alleen uit bij uitgeschakeld en volledig ingeschakeld (en bij alarm als je dat aanzette), nooit tijdens het aftellen. |
| **74. Te lang op het toetsenbord** | Open bij een uitgeschakeld alarm het toetsenbord en laat het staan. | Na de ingestelde tijd gaat het paneel terug naar het hoofdscherm (zichtbaar), na nog eens dezelfde tijd gaat het scherm uit. |
| **75. Vergrendeling in stappen** | Zet bij *Instellingen*, *Vergrendeling*, voor een snelle test alle aantallen op 1 en de wachttijden op 1 minuut. Voer op het paneel een foute code in, wacht een minuut, voer weer een foute code in, enzovoort. Controleer daarna dat de vierde foute code het paneel permanent vergrendelt, ook na een herstart van Home Assistant, en dat *Blokkade opheffen* het opent. Voer ook een goede code in na een of twee foute codes. | Elke stap duurt de ingestelde tijd; de vierde foute code geeft `code_locked_permanent` en het paneel blijft dicht tot *Blokkade opheffen*; daarna begint alles weer bij de eerste stap. Een goede code zet de teller terug naar nul. Zet de standaardwaarden daarna terug (3, 5, 2, 15, 2, 60, 1). |
| **76. Sensorlijst met gebruikerscode** | Open op het paneel de sensorlijst en voer de code van een gewone Vigil-gebruiker in. Open daarna de tab *Info* met dezelfde code. | De lijst opent met de gebruikerscode; de infopagina vraagt de installateurscode en weigert de gebruikerscode. |
| **77. Recht om te omzeilen** | Maak twee gebruikers: een met en een zonder *Mag sensoren omzeilen*. Probeer in de sensorlijst met beide codes een sensor te omzeilen en terug te zetten. | Zonder het recht worden omzeilen en terugzetten geweigerd met een melding. Met het recht lukt beide; voor een sabotagesensor is ook *Mag sabotage omzeilen* nodig. |
| **78. Meldingen bij foute codes** | Voer op het paneel drie foute codes in (standaard) en kijk naar de melding bij de derde. Probeer daarna nog eens, ook met de goede code. | De derde foute code geeft zelf al "Te veel foute codes. Probeer het over 5 min opnieuw" (in de taal van het paneel); de pogingen daarna tellen niet mee en noemen de resterende minuten. Bij een permanente vergrendeling staat er dat een beheerder het moet opheffen. |
| **79. Herstart zonder valse meldingen** | Herstart Home Assistant volledig terwijl het alarm uit staat (en later nog eens terwijl het aan staat). Kijk naar je storingskanalen en naar het logboek. | Geen `supervision_lost` voor sensoren die binnen de wachttijd terugkomen; het logboek toont `startup_settled` met de wachttijd. Haal een sensor met opzet weg: na de wachttijd volgt wel de melding. |
| **80. Nieuw hoofdscherm** | Zet het alarm uit met alles dicht en kijk naar het paneel. Open daarna een deur of raam. | Een groene ring met een schild met vinkje, *Uitgeschakeld*, *Alles dicht*, drie tegels (*Thuis*, *Weg*, *Nacht*) en onderaan de tabs *Alarm*, *Sensoren*, *Info*. Met een open sensor wordt de ring amber met een uitroepteken, staat er *Open: 1* en heeft de tab *Sensoren* een badge met 1. De namen staan nergens op dit scherm. |
| **81. Aftellen in de ring** | Schakel in op *Weg* met een uitlooptijd van 60 seconden. Laat daarna iemand binnenkomen (aankomstvertraging). | De ring is vol met het getal 60 in het midden en loopt in 60 seconden leeg; bij 0 is het alarm ingeschakeld. Eronder staat *Verlaat nu het huis* (geen seconden in de tekst). Bij binnenkomst is de ring oranje, begint vol en telt af, met *Schakel uit met uw code*. |
| **82. Alarm** | Veroorzaak een alarm. | Rood kader om het scherm, een rodere ondergrond, een rode ring met een bel, *ALARM* met de oorzaak, een grote groene knop *Uitschakelen*. Het toetsenpaneel opent niet vanzelf. |
| **83. Toetsenpaneel en tabs** | Druk op *Uitschakelen* en tik cijfers; druk op de wistoets en op het vinkje. Open daarna de sensorlijst en de infopagina via de tabs. Zet de sensorlijst in Vigil op *nooit*. | Alleen sterretjes in het veld, de vinktoets is groen, op het toetsenpaneel zijn geen tabs en linksboven is een terugpijl. Op de andere pagina's staan de tabs, de actieve tab heeft de kleur van de toestand. Bij *nooit* is de tab *Sensoren* weg. |
| **84. Geen verbinding** | Zet Home Assistant uit of haal het paneel van het netwerk. | De ring wordt grijs met een icoon voor geen wifi en de titel *Geen verbinding*; rechtsboven staat het wifi-icoon (rood doorgestreept zolang er geen verbinding is). |
| **85. Pictogrammen** | Kijk of alle pictogrammen een tekening zijn. | Geen lege vierkantjes. Zo wel, dan is het lettertype met de pictogrammen niet gedownload bij het compileren: controleer de internetverbinding van ESPHome en compileer opnieuw. |
| **86. Nieuw uiterlijk van de kaart** | Open de Vigil-kaart op een telefoon (smal) en op een tablet (breed). Schakel in met aftellen en veroorzaak een alarm. | Op de telefoon staat alles onder elkaar; op de tablet in twee kolommen (ring links, knoppen of toetsenpaneel rechts). Zelfde kleuren en ring met aftellen als het paneel; bij een alarm een rood kader. Controleer ook in een licht thema dat de tekst leesbaar blijft. |
| **87. Bewaking per paneel** | Voeg een paneel toe van het soort *Tablet of telefoon* en kijk naar het veld *Bewaken of dit paneel bereikbaar is*. Wissel het soort naar *ESPHome-paneel* en weer terug. Open de Vigil-kaart op een telefoon en sluit daarna de browser; wacht 10 minuten. Zet daarna bewaken aan bij een tablet die je afsluit. Open een bestaand paneel van vóór deze versie. | Bij tablet of telefoon staat het veld standaard uit, bij een ESPHome-paneel aan (het volgt het soort, tot je het zelf wijzigt). Met bewaken uit krijg je geen reparatie en geen melding, en de lijst toont *Niet bewaakt*. Met bewaken aan komen ze wel na 10 minuten. Een bestaand paneel staat nog aan. |
| **88. Toetsenbord op de kaart** | Open de Vigil-kaart in een browser met een toetsenbord, druk op *Weg* (of *Uitschakelen*) en typ de code met het toetsenbord. Probeer Backspace, Enter en Escape. Typ daarna in een ander invoerveld op het dashboard terwijl het toetsenpaneel open staat. | De cijfers verschijnen als punten, Backspace wist er een, Enter bevestigt en Escape sluit het toetsenpaneel. Een ander invoerveld krijgt zijn eigen toetsen en het toetsenpaneel reageert daar niet op. |
| **89. Back-up bij een wijziging** | Open in het Vigil-paneel het tabblad *Back-up*. Voeg daarna een sensor toe en kijk opnieuw. Klik op het oog-icoon (*Bekijk*) bij die versie. Klik in de melding *Opgeslagen* snel op *Ongedaan maken* (of gebruik het pijl-icoon *Terugzetten* in het tabblad). | Na de wijziging staat bovenaan een versie met *Sensoren: 1 toegevoegd* en in de kolom *Vigil-versie* de versie waarmee ze is gemaakt. *Bekijk* toont de wijziging met de naam van de sensor. *Terugzetten* toont eerst *Sensoren: 1 verwijderd* en vraagt om doorvoeren. Daarna is de sensor weg en staat er een versie *Teruggezet*; die terugzetten brengt de sensor terug. |
| **90. Maximaal 10 versies** | Maak meer dan 10 wijzigingen (bijvoorbeeld een naam steeds aanpassen). | Het tabblad toont er nooit meer dan het ingestelde aantal (standaard 10), de oudste valt af. Verlaag het aantal bij *Instellingen* (kaart *Back-up*): de oudste versies verdwijnen. |
| **91. Exporteren en importeren** | Klik op *Configuratie exporteren* (een bestand wordt gedownload). Voeg een sensor toe. Kies *Configuratie importeren…* en het bestand. Probeer daarna een ander bestand (bijvoorbeeld een foto of een tekstbestand). | Het overzicht toont *Sensoren: 1 verwijderd*; na *Doorvoeren* is de sensor weg en staat de vorige toestand als versie *Import* bij de back-ups. Een bestand dat geen Vigil-export is wordt geweigerd met een duidelijke melding en er verandert niets. |
| **92. Waarom kan ik niet inschakelen?** | Laat een sabotagesensor open staan terwijl het alarm uit staat (activeer hem, wacht op het alarm en schakel het alarm uit terwijl hij nog open is). Kijk op het tabblad *Overzicht* van het Vigil-paneel. Probeer daarna in te schakelen met de Vigil-kaart of het aanraakpaneel. | De kaart *Waarom kan ik niet inschakelen?* noemt de sensor en de modi. Op de kaart en het paneel staat *Inschakelen kan niet: … staat open* en verschijnt (als het paneel mag omzeilen) de knop *Omzeilen en inschakelen*. |
| **93. Omzeilen en inschakelen** | Druk op *Omzeilen en inschakelen* en voer de code in van een gebruiker mét het recht om te omzeilen (en bij sabotage ook dat recht). Herhaal met een gebruiker zonder dat recht. Herhaal met een open rookmelder. | Met het recht: de sensor staat als omzeild in de lijst en het alarm schakelt in. Zonder het recht: een melding dat het recht ontbreekt en het alarm blijft uit. Een open rookmelder kan nooit worden omzeild: de weigering blijft en er verandert niets. |
| **94. Nieuwe sensoren gevonden** | Voeg in Home Assistant een nieuwe deur- of bewegingssensor toe (of schakel er een in die uit stond). Wacht een paar seconden. Klik daarna op *Niet nu*. | Op het tabblad *Sensoren* staat de badge *1 nieuw* en op het Overzicht de kaart *Nieuwe sensoren gevonden* met de naam. *Bekijk en voeg toe* opent de lijst met alleen die sensor. Na *Niet nu* verdwijnen badge en kaart, en de sensor staat nog wel in *Sensoren zoeken*. Er is niets zelf toegevoegd. |
| **95. Wizard** | Klik op de kaart *Vigil instellen* (of *Installatiewizard*) en loop alle stappen door. Voeg in een stap iets toe en annuleer in een andere. | Na een formulier (opgeslagen of geannuleerd) staat de wizard weer op dezelfde stap. De stap *Klaar voor gebruik?* toont wat nog ontbreekt. *Later verder* sluit hem; op het Overzicht staat dan *Ga verder met de wizard*. |
| **96. Export met tijd** | Klik op *Configuratie exporteren*, wacht even en klik nog eens. | De bestandsnaam bevat datum én tijd van de laatste wijziging van de configuratie (niet van het exporteren), bijvoorbeeld `vigil-alarm-2026-10-18-13-27-05.json`. Nogmaals exporteren zonder wijziging geeft dezelfde naam. |
| **97. Oefenmodus** | Zet het alarm uit en klik op *Start oefenmodus*. Schakel in, open een deur en laat het alarm afgaan. Schakel daarna uit. | Er klinkt geen sirene en je krijgt geen melding, maar paneel en Vigil-kaart tonen het alarm gewoon. Bovenin staat de chip *Oefenmodus*. In het logboek staan de gebeurtenissen met `practice`. Na het uitschakelen is de oefenmodus uit; een volgend alarm laat de sirene weer horen. |
| **98. Looptest** | Zet het alarm uit en klik op *Start looptest*. Open een deur of raam en loop langs een bewegingsmelder, maar laat één sensor bewust over. Klik op *Stop de test*. | Elke sensor die reageert wordt direct afgevinkt. Na het stoppen staat de overgeslagen sensor onder *Niet gezien* met *reageerde niet*. Brand-, gas-, water- en sabotagesensoren doen niet mee. In het logboek staat `walktest_finished`. |
| **99. Oefenen kan alleen met het alarm uit** | Schakel het alarm in en probeer dan *Start oefenmodus* of *Start looptest*. Start een looptest, en schakel dan in. | Beide worden geweigerd met de melding dat het alarm eerst uit moet. Inschakelen stopt een lopende looptest. |
| **100. Alarmgeheugen met route** | Schakel in op *Thuis*. Open de voordeur (telt mee) en, voordat het alarm afgaat of daarna, een bewegingsmelder die alleen in *Weg* bewaakt. Laat het alarm afgaan, open nog een sensor en schakel uit met een code. | Op het Overzicht staat *Laatste alarm* met de sensoren in de volgorde waarin ze opengingen, met ruimte en bij elke stap *Telde mee* of *Telde niet mee*. In het logboek staat voor de sensor die niet meetelde een regel *Sensor geopend tijdens alarm*. Op de Vigil-kaart (met de sensorlijst ontgrendeld) staat *Laatste alarm: …* met de route. |
| **101. Geheugen wissen en bewaren** | Herstart Home Assistant na test 100. Controleer de kaart, klik dan op *Alarmgeheugen wissen*. Doe daarna een inlooptijd die je op tijd uitschakelt. | Het geheugen is na de herstart er nog; na wissen is het weg (en er staat *Alarmgeheugen gewist* in het logboek). Een inlooptijd die je op tijd uitschakelt laat niets achter. Tijdens een lopend alarm kun je niet wissen. |
| **102. Vals alarm annuleren** | Laat een inbraakalarm afgaan en schakel binnen 60 seconden uit met een code. Doe het nog eens en wacht nu 70 seconden. | Eerste keer: logboek `alarm_cancelled`, kaart *Geannuleerd als vals alarm*, en een bericht *Alarm geannuleerd: vals alarm door …* naar de alarmkanalen. Tweede keer: gewoon uitgeschakeld, niet geannuleerd. Zet je het venster op 0, dan is het nooit geannuleerd. |
| **103. Dwangcode** | Maak bij een gebruiker een dwangcode (eerst een kanaal met de soort melding *Dwang*; zonder kanaal weigert Vigil de code). Schakel in en schakel uit met de dwangcode. | Het alarm gaat gewoon uit, er is niets te zien op paneel, kaart of gebeurtenis-entiteit. Het kanaal krijgt *STIL ALARM: … gebruikte de dwangcode …*. In het logboek staat `duress_used`. Dezelfde code als een andere code wordt geweigerd. |
| **104. Dwangcode tijdens een alarm** | Laat een inbraakalarm afgaan en schakel binnen 60 seconden uit met de dwangcode. | Het alarm gaat uit, de sirene stopt, er gaat alleen de stille melding uit en **geen** *geannuleerd*. |
| **105. Deurbel** | Vink *Deurbel* aan bij een sensor (deurcontact of bewegingsmelder) en kies bij *Instellingen → Deurbel* een sirene, schakelaar of lamp. Open de deur met het alarm uit. Schakel het alarm in en open de deur weer. | Uit: korte toon, geen melding, niets in het logboek. Ingeschakeld: geen toon. Een deur die snel flikkert geeft maar één toon. |
| **106. Vakantie en Aangepast** | Zet onder *Instellingen* de modi *Vakantie* en *Aangepast* aan en maak (of kies) een sensorgroep die in die modus actief is. Schakel in met de kaart of met `alarm_control_panel.alarm_arm_vacation` / `alarm_arm_custom_bypass`. | Eigen uitlooptijd; daarna status *Vakantie* of *Aangepast* (in Home Assistant `armed_custom_bypass`). Alleen sensoren van de groepen van die modus geven alarm. Kaart en infopagina laten de nieuwe modus zien met een eigen kleur. |
| **107. Paneel met vijf knoppen** | Flash het paneel met de firmware van 0.5.4 en kijk bij uitgeschakeld alarm naar de knoppen. | Vijf knoppen in één rij (kleinere tekst): Thuis, Weg, Nacht, Vakantie, Aangepast. Een gebruiker die maar één modus mag, ziet alleen die knop. |
| **108. Alarmgeheugen op het paneel** | Laat een alarm afgaan, schakel uit en kijk op het hoofdscherm van het paneel. | Onder *Uitgeschakeld* staat *Laatste alarm: 14:03 Voordeur > Gang* (alleen als het paneel sensornamen mag tonen). Na *Wissen* in het beheerpaneel is de regel weg. |
| **109. 24 uur hoorbaar en 24 uur stil** | Maak een sensor van het type *24 uur hoorbaar* en een van *24 uur stil*. Open ze met het alarm uit. | Hoorbaar: sirene en melding met oorzaak *24-uursalarm*, ook uitgeschakeld; inschakelen weigert zolang hij open is. Stil: geen sirene, wel een melding naar de *Technisch*-kanalen en een regel in het logboek; de alarmstatus verandert niet. |
| **110. Permanent omzeilen** | Vink bij een sensor *Omzeiling blijft staan na uitschakelen (permanent)* aan. Omzeil hem met de schakelaar, schakel het alarm in en uit. Herstart Home Assistant. Zet de omzeiling daarna zelf uit. | Na het uitschakelen en na de herstart staat de sensor nog op *omzeild* en geeft geen alarm; het overzicht heeft een kaart *Permanent omzeild* en kaart en paneel tonen *Omzeild: …* onder Uitgeschakeld. Pas na het uitzetten van de omzeiling bewaakt hij weer. Een sensor zonder vinkje is na het uitschakelen weer actief. |
| **111. Zes talen** | Zet het **profiel** van Home Assistant (Gebruikersprofiel → Taal) achtereenvolgens op Deutsch, Français, Italiano en Español. Open het Vigil-paneel en, als je de kaart hebt, de Vigil-kaart. Zet daarna de **systeemtaal** op een van de vier en laat een alarm afgaan. | Het beheerpaneel en de kaart staan volledig in die taal (geen Nederlandse of Engelse restanten, geen `{naam}` of andere accolades in de tekst). De melding is in de systeemtaal; de standaard sensorgroepen heten bijvoorbeeld *Außenhaut* / *Innenbereich*. Een andere taal (bijvoorbeeld Portugees) toont Engels. Meld rare of foute vertalingen. |
| **112. Taal op het aanraakpaneel** | Flash het paneel met de firmware van 0.5.6. Kies onder *Panelen* bij het paneel achtereenvolgens de vier nieuwe talen en kijk naar het scherm, het toetsenbord, de sensorlijst en de info-pagina. | Alle teksten staan in de gekozen taal en passen op het scherm (er worden geen accenten getoond: *Ueberbruecken*, *Desactive*). Een paneel met oudere firmware toont voor de nieuwe talen Engels. |

## 7. Wat je terugmeldt

Per test dat iets anders uitpakt:

- het testnummer en wat je deed;
- wat je verwachtte en wat er gebeurde;
- de logregels met `vigil`: **Instellingen → Systeem → Logboeken**, zoek op `vigil`. Voor meer detail zet je in `configuration.yaml`:

  ```yaml
  logger:
    default: warning
    logs:
      custom_components.vigil_alarm: debug
  ```
- bij formulieren: een schermafbeelding.

## 8. Als het niet werkt

Voor een alarm dat iets anders doet dan je verwacht, zie [Mijn alarm doet niet wat ik verwacht](problemen-oplossen.nl.md).

- **"Vigil Alarm" staat niet in de lijst:** controleer het pad `config/custom_components/vigil_alarm/manifest.json`, herstart volledig en ververs de browser. Kijk in het logboek naar `vigil`.
- **De zijbalk toont geen "Vigil":** alleen beheerders zien hem. Ververs hard, herstart Home Assistant volledig en kijk in het logboek of `vigil` een fout meldt. Er is geen tweede manier om te configureren; blijft het paneel weg, stuur dan de logregel.
- **Het paneel blijft leeg of toont "kon niet geladen worden":** de integratie is niet actief (kijk onder *Apparaten en diensten* of er een fout staat). Ververs de browser.
- **Foutmelding bij het openen van het eerste formulier (naam en basisinstellingen):** meestal een JSON- of vertaalfout of een versieverschil. Stuur de logregel.
- **Entiteiten heten anders dan in deze gids:** de namen volgen uit wat je invulde. Controleer de echte namen onder **Instellingen → Apparaten en diensten → Vigil Alarm**.
- **Testschakelaars verdwijnen na een herstart:** gebruik de helpers uit het testpakket, niet losse toestanden uit de Ontwikkelaarstools.

## 9. Opruimen

1. Verwijder de integratie: **Instellingen → Apparaten en diensten → Vigil Alarm → ⋮ → Verwijderen**.
2. Verwijder `custom_components/vigil_alarm` en `packages/vigil_test_package.yaml` uit de share **config**, en haal zo nodig de regels `packages` uit `configuration.yaml`.
3. Herstart Home Assistant. Zet de Samba-add-on uit als je hem niet meer nodig hebt.
