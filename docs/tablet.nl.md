# Een tablet aan de muur als alarmpaneel

Je kunt Vigil bedienen met een tablet met een Home Assistant-dashboard, in plaats van (of naast) het ESPHome-paneel. De tablet is een paneel in het register, gekoppeld aan een Home Assistant-gebruiker, en toont de **Vigil-kaart**: de toestand, de knoppen voor de modi die hij mag gebruiken, een toetsenpaneel en, na de installateurscode van het paneel, de sensoren.

## Instellen

1. **Maak een gebruiker voor de tablet.** In Home Assistant: *Instellingen → Personen → Gebruikers → Gebruiker toevoegen*. Neem een gewone gebruiker. Je mag ook een beheerdersaccount kiezen (het staat als *(admin)* in de lijst), maar dat is dan je eigen verantwoordelijkheid: de instellingen van het paneel gelden dan voor alles wat dat account doet, op elk apparaat waar het is ingelogd, en een gestolen of onbewaakt apparaat is dan als beheerder ingelogd. Vigil geeft zo'n account op het paneel geen beheerdersrechten (voor uitschakelen en omzeilen is altijd een code nodig), en de betere weg is een tweede, gewoon account voor dagelijks gebruik.
2. **Registreer de tablet in Vigil.** Open *Vigil Alarm → Panelen → Paneel toevoegen*. Geef een naam, kies als soort apparaat *Tablet of telefoon met Home Assistant* en kies bij *Home Assistant-account (tablet of telefoon)* het account. Stel in wat de tablet mag (modi, uitschakelen, omzeilen, dempen, sensorlijst, taal), precies zoals bij een ESPHome-paneel. Geef het paneel een **installateurscode** als de tablet de sensoren moet kunnen tonen.
3. **Log de tablet in als die gebruiker** en open een dashboard met de Vigil-kaart. Kies in de dashboardeditor *Kaart toevoegen → Aangepast: Vigil*, of in YAML:

   ```yaml
   type: custom:vigil-card
   ```

   Vigil laadt de kaart zelf; je hoeft niets te installeren of als resource toe te voegen. De kaart kent één instelling, `idle_timeout` (seconden zonder aanraking voordat een half ingetypte code wordt vergeten, standaard 30). Gebruik voor een tablet aan de muur een paneelweergave (één kaart) of een kioskdashboard, zoals Fully Kiosk Browser dat kan tonen, zodat de zijbalk verborgen is.
4. Gebruik **HTTPS** voor Home Assistant. Op gewoon `http://` reist de code leesbaar over je wifi.

## Wat de kaart doet

- Volgt het profiel van het paneel van de tablet: alleen de modi waarin dat paneel mag inschakelen, *Uitschakelen* alleen als het mag, omzeilknoppen alleen als het mag omzeilen, de taal die je voor het paneel koos en helemaal geen sensorlijst als die op *nooit* staat.
- **Uitschakelen en omzeilen vragen altijd een gebruikerscode**; inschakelen alleen als *code nodig om in te schakelen* aan staat. Het toetsenpaneel opent nooit vanzelf: tijdens de aankomstvertraging en bij een alarm laat het scherm eerst zien wat er aan de hand is, en wie wil uitschakelen drukt op *Uitschakelen*.
- **De sensorlijst** opent met de code van een willekeurige Vigil-gebruiker, of de installateurscode van het paneel (via `vigil_alarm.unlock_panel`), zolang je hebt ingesteld. Omzeilen en terugzetten vragen een gebruiker die het recht heeft om te omzeilen (sabotagesensoren: ook het sabotagerecht). Tot die tijd toont de kaart alleen *hoeveel* sensoren open staan, nooit hun namen. De lijst verlaten, of 30 seconden niet aanraken, laat de kaart de ontgrendeling vergeten.
- Een gebruiker die niet aan een paneel is gekoppeld, ziet *Niet gekoppeld*; een geblokkeerd paneel toont *Geblokkeerd* en doet niets.

## Wat Vigil afdwingt

- Vigil herkent de tablet aan de **Home Assistant-gebruiker** achter elke oproep. Home Assistant zet die gebruiker er zelf bij, dus het is niet na te maken met een andere `source`-tekst. Dat is sterker dan bij een ESPHome-paneel, waarvan de oproepen geen gebruiker meedragen.
- Wat de kaart ook toont, de server beslist: een oproep die het profiel niet toestaat, wordt geweigerd en vastgelegd (`panel_refused`). De kaart is alleen een mooier gezicht erop.
- De tablet heeft een eigen blokkade-timer voor foute codes en Vigil behandelt de tablet nooit als beheerder. *Geblokkeerd* weigert alles van die tablet; *Blokkade opheffen* en *Ontgrendelen* werken zoals bij elk paneel.
- In de geschiedenis staat wie het deed, bijvoorbeeld *Anna (hal-tablet)*.

## Offline

De kaart meldt zich elke minuut bij Vigil zolang het dashboard openstaat. Hoort Vigil 10 minuten niets van de kaart, dan krijg je een reparatie *Paneel niet bereikbaar* en een melding op je storingskanalen (`panel_offline`, en `panel_online` als hij terug is), net als bij een ESPHome-paneel. De alarmstatus verandert er nooit door. De paneellijst toont *Vigil-kaart actief* voor een tablet die zich heeft gemeld.

- Alleen een tablet waarvan de kaart zich minstens één keer heeft gemeld, wordt bewaakt. Een tablet met de eigen alarmkaart van Home Assistant kan niets melden en wordt dus nooit als offline gemeld.
- Vigil onthoudt dat een tablet de kaart gebruikt, dus een tablet die dood is als Home Assistant herstart, wordt nog steeds gemeld, tien minuten na de herstart.
- Een tablet met scherm uit en gesloten browser is voor Vigil offline. Laat het dashboard op een tablet aan de muur openstaan.

## Wat het niet doet

- Home Assistant kent geen rechten per entiteit. De gebruiker van de tablet kan elke dienst aanroepen die een gewone gebruiker mag en kan elke toestand lezen. Vigil beschermt het alarm (codes, profiel, blokkade) en de kaart vraagt alleen wat het profiel toestaat, maar de gebruiker kan het dashboard nog verlaten. Geef die gebruiker niet meer dan de tablet nodig heeft.
- De alarmkaart van Home Assistant zelf werkt ook voor een tablet, maar toont alle modi (een modus die het profiel niet toestaat wordt bij indrukken geweigerd) en heeft geen sensorlijst.
- De kaart heeft geen infopagina zoals het ESPHome-paneel; daarvoor heeft de tablet Home Assistant.
- Wordt de tablet gestolen: zet het paneel in Vigil op *Geblokkeerd* en schakel de gebruiker in Home Assistant uit of verwijder zijn vernieuwingstokens (*Profiel → Beveiliging*).

## Twee accounts voor de beheerder en een slot op de browser

De zwakke plek van elk dashboard is het account erachter. Een beheerder wordt door Vigil nooit beperkt; een beheerder die op een tablet of telefoon ingelogd blijft, geeft dat apparaat alle rechten. Gebruik je **beheerdersaccount alleen om te beheren** en maak een tweede, gewoon account voor dagelijks gebruik (en voor de tablet, als je er een wilt). Vergrendel de browser van de tablet op het dashboard (een kioskbrowser zoals Fully Kiosk Browser, of de kioskmodus van Home Assistant) zodat een bezoeker er niet uit kan.

Twee dingen houden een voorbijganger bij een tablet aan de muur van het alarm af: Vigil behandelt het account van de tablet als een gewoon account, wat het in Home Assistant ook is (voor uitschakelen en omzeilen is altijd een code nodig) en ook **inschakelen** vraagt een code als je *Code vereist om in te schakelen* aanzet bij Instellingen. Die instelling geldt voor het hele systeem: staat ze uit, dan kan iedereen die op de knop kan drukken inschakelen.

## Een telefoon of tablet: hetzelfde register

Een tablet aan de muur en de telefoon van een huisgenoot worden hetzelfde behandeld: allebei zijn een regel onder het tabblad *Panelen* die aan een Home Assistant-account is gekoppeld (het veld *Home Assistant-account (tablet of telefoon)*, bij voorkeur een gewoon account; een beheerder mag ook, met de zorg die hierboven staat). Per regel stel je in wat het mag (modi, uitschakelen, omzeilen, dempen, sensorlijst, taal), precies zoals bij een ESPHome-paneel, en de sensorlijst volgt overal hetzelfde stramien: verborgen tot de installateurscode van die regel hem ontgrendelt. Het enige verschil is hoe Vigil het apparaat herkent: een ESPHome-paneel aan zijn paneel-id, een account aan de gebruiker achter de aanroep.

- **Elke geldige code werkt** op zo'n apparaat en de geschiedenis toont van wie de code was, bijvoorbeeld *Bob (cleo-telefoon)*. Geen code, geen bediening (waar een code nodig is).
- **Elke regel heeft een eigen blokkade-timer**: foute codes op Cleo's telefoon blokkeren die telefoon (in stappen, zie *Instellingen*, *Vergrendeling*), niet de tablet of iemand anders.
- **Alleen geregistreerde accounts mogen bedienen.** Zodra één account is geregistreerd, wordt elk ander gewoon Home Assistant-account (bijvoorbeeld van de kinderen) geweigerd voordat een code wordt bekeken (gebeurtenis `user_refused`, de fout *Gebruiker is niet geregistreerd*), en dat telt niet mee voor een blokkade. Beheerders, automatiseringen, scripts en ESPHome-panelen (aanroepen zonder Home Assistant-gebruiker) blijven ongemoeid. Zolang er geen account is geregistreerd verandert er niets, dus een update van een oudere versie verandert niets.
