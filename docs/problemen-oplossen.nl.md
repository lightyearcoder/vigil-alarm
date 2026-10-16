# Mijn alarm doet niet wat ik verwacht

Zoek hieronder wat je ziet. Per verschijnsel staan de meest waarschijnlijke oorzaken, de plek waar je dat controleert en wat je eraan doet.

**Eerst kijken, altijd:**

- **Overzicht** in het paneel: de kaart *Klaar voor gebruik?* noemt wat er in de instellingen ontbreekt. De kaart *Aandachtspunten* noemt sensoren met een lege batterij of die onbereikbaar zijn. *Wat bewaakt elke modus* laat zien welke sensoren in welke modus meedoen.
- **Laatste gebeurtenis:** de entiteit `sensor.vigil_alarm_last_event` en het gebeurtenissenlogboek (`event.vigil_alarm_alarm_events`) vertellen wat er is gebeurd en waarom iets is geweigerd.
- **Attributen van het alarm** (`alarm_control_panel.vigil_alarm`): `open_sensors`, `bypassed_sensors`, `faults`, `problems`, `refuse_reason`.

## Het alarm gaat niet aan

| Je ziet | Oorzaak | Wat te doen |
|---|---|---|
| `refuse_reason: sensor_open` | Een bewaakte sensor staat open (bijvoorbeeld een raam). | Sluit hem, of kies bij de sensor wat er moet gebeuren als hij open staat bij het inschakelen (omzeilen, wachten tot hij dicht is, weigeren). |
| `refuse_reason: sensor_unavailable` | Een sensor is onbereikbaar (batterij leeg, buiten bereik). | Kijk bij *Aandachtspunten* welke. Herstel hem, of omzeil hem. |
| `refuse_reason: alarm_condition` | Er is op dat moment een brand-, gas- of sabotagealarm actief. | Los het op en schakel eerst uit. |
| `refuse_reason: not_disarmed` | Het alarm is al ingeschakeld of in uitlooptijd. | Schakel eerst uit. |
| Foutmelding over de code | Code fout, te kort, niet toegestaan voor die modus, of geblokkeerd (zie hieronder). | Controleer de gebruiker op het tabblad *Gebruikers*. |

## Het alarm gaat niet af bij een open deur of beweging

1. **Staat het alarm echt aan?** Een alarm in uitlooptijd (`arming`) bewaakt nog niet.
2. **Zit de sensor in een sensorgroep?** Een inbraaksensor zonder sensorgroep bewaakt niets. Staat *Wat bewaakt elke modus* op "geen sensorgroep", maak dan de standaardgroepen (kaart *Klaar voor gebruik?*).
3. **Is de groep actief in deze modus?** Bijvoorbeeld *Binnen* geldt alleen bij Weg. In Thuis gaat een bewegingsmelder dus nooit af.
4. **Is de sensor omzeild?** Dan staat hij onder `bypassed_sensors`. Omzeilen vervalt bij uitschakelen.
5. **Is het type "vertraagd"?** Dan krijg je eerst de inlooptijd (`pending`) en gaat het alarm pas af als je niet op tijd uitschakelt.
6. **Is er een bevestigingsregel?** Dan is er pas alarm als genoeg verschillende sensoren binnen het tijdvenster afgaan. Eén sensor geeft alleen de melding "zonder bevestiging".
7. **Is de sensor onbereikbaar?** Dan kan hij niet afgaan. Kijk bij *Aandachtspunten*.
8. **Is de entiteit de juiste?** Controleer in *Ontwikkelaarstools → Toestanden* dat de entiteit echt `on` wordt als de deur opengaat.

## Er komt geen melding op mijn telefoon

1. Is er een **meldingskanaal**? Zo niet, dan zegt *Klaar voor gebruik?* dat, en biedt Vigil je telefoon aan.
2. Staan de goede **categorieën** aan? Alleen berichten in die categorieën komen door (alarm, in afwachting, storing, technisch).
3. Is er een **vertraging** ingesteld? Een escalatiekanaal met 30 seconden vertraging meldt pas na 30 seconden, en niet als je eerder uitschakelt of bevestigt.
4. Gebruik de **testknop** bij het kanaal. Komt de test niet aan, dan ligt het aan Home Assistant of de app, niet aan het alarm: controleer de meldingsrechten van de app op je telefoon.
5. Klopt de **dienst**? Het moet een bestaande `notify.`-dienst zijn.

## De sirene klinkt niet

1. Is er een sirene ingesteld, en klinkt hij bij *deze oorzaak* (inbraak, brand, gas, sabotage, storing)?
2. Probeer de actie `vigil_alarm.test_siren`. Klinkt hij dan niet, dan is de entiteit zelf het probleem (onbereikbaar, batterij leeg).
3. Is de sirene **gedempt** met `vigil_alarm.silence`? Dan blijft het alarm actief maar zwijgt de sirene.
4. Is de **maximale duur** verlopen? Daarna gaat de sirene vanzelf uit.

## Mijn code wordt geweigerd

- **Te kort:** de minimale lengte staat bij *Instellingen* (4 tot 12 tekens).
- **Geblokkeerd:** vijf foute codes binnen vijf minuten blokkeren alle codes vijf minuten lang, ook de goede. Wacht even; in het gebeurtenissenlogboek staat `code_locked`.
- **Niet toegestaan:** de gebruiker mag alleen bepaalde modi. Kijk bij *Toegestane modi*. Uitschakelen kan altijd met een geldige code.

## Valse alarmen

- Gebruik bij deuren het type **vertraagd** met een inlooptijd, zodat je kunt uitschakelen.
- Laat een bewegingsmelder alleen bij Weg bewaken (groep *Binnen*).
- Gebruik een **bevestigingsregel**: pas alarm als twee bewegingsmelders binnen een minuut afgaan.
- Kijk bij een melding in het gebeurtenissenlogboek welke sensor het was.

## Er komen geen batterij- of sabotagemeldingen

- Bij de sensor moet een **batterijsensor** zijn ingevuld. De kaart *Klaar voor gebruik?* noemt sensoren zonder. Een apparaat dat alleen "batterij laag" meldt (aan/uit), werkt ook.
- Heeft het apparaat een **sabotagesensor**, vul die dan in bij de sensor. De kaart noemt sabotagesensoren die nergens aan gekoppeld zijn.

## De entiteiten heten anders dan ik verwachtte

De entiteit-id's van Vigil eindigen altijd op de Engelse naam, ook als Home Assistant op Nederlands staat (bijvoorbeeld `binary_sensor.vigil_alarm_intrusion_alarm`). Wat je in de interface ziet, volgt je eigen taal. Controleer de echte namen onder *Instellingen → Apparaten en diensten → Vigil Alarm*. Wie van een oudere versie komt, moet automatiseringen en dashboards aan de nieuwe id's aanpassen (zie de release notes).

## Het paneel is leeg

Ververs de browser hard (Ctrl+F5) en kijk of de integratie actief is onder *Apparaten en diensten*. Kijk anders in het logboek (*Instellingen → Systeem → Logboeken*, zoek op `vigil`).

## Nog steeds niet?

Download de diagnostische gegevens (*Apparaten en diensten → Vigil Alarm → ⋮ → Diagnostische gegevens downloaden*), zonder codes of namen van personen, en meld het op GitHub (zie het tabblad *Over*).

## Ik blijf een herinnering voor de sirenetest krijgen

De herinnering herhaalt zich tot er een test is gedaan. Tik op *Sirene testen* in het bericht, gebruik *Sirene nu testen* op het Overzicht, of roep `vigil_alarm.test_siren` aan. Wil je geen herinneringen, zet dan het interval bij *Instellingen* op 0.

## De hartslag mislukt

De kaart *Hartslag* op het Overzicht noemt de reden: *geen verbinding* (Home Assistant komt niet op internet of het adres klopt niet), *geen antwoord binnen 10 seconden*, of *HTTP 404* en dergelijke (de dienst kent het adres niet; kopieer het opnieuw). Verbeter het bij *Instellingen* en klik op *Nu testen*.
