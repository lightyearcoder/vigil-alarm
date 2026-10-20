# Wat Vigil doet als er iets misgaat

Elke regel hieronder is een scenario dat automatisch getest wordt (`tests/ha/test_failure_scenarios.py` en de tests waar die naar verwijst). Deze pagina beschrijft dus wat het alarm doet, niet wat het zou moeten doen. Eén ding kan geen test veranderen: **Vigil draait binnen Home Assistant. Als Home Assistant niet draait, is er geen alarm.** De [heartbeat](user-guide.nl.md) meldt dat het uit is; hij kan het niet overnemen.

English: [what Vigil does when something goes wrong](failure-behaviour.md).

## Als Home Assistant herstart of stopt

| Situatie | Wat Vigil doet |
|---|---|
| Herstart tijdens de **uitgangsvertraging** | De vertraging loopt door en eindigt op het oorspronkelijke tijdstip; ze begint niet opnieuw. |
| De uitgangsvertraging was **voorbij terwijl Home Assistant uit was** | Het alarm is bij het opstarten ingeschakeld. |
| Herstart terwijl **ingeschakeld** | Nog steeds ingeschakeld, in dezelfde modus, door dezelfde gebruiker (de gebruiker blijft sinds 0.6.4 bewaard over een herstart). De sensoren worden weer bewaakt zodra ze vertrouwd worden (zie hieronder). |
| Een deur werd **geopend terwijl Home Assistant uit was** | Zodra Vigil terug is en de open sensor ziet, begint de ingangsvertraging. |
| Herstart tijdens de **ingangsvertraging** | De ingangsvertraging loopt door en eindigt op het oorspronkelijke tijdstip. Drie keer achter elkaar herstarten verandert niets. Uitschakelen na de herstart stopt haar. |
| Herstart tijdens het **alarm** | Het alarm blijft aan; oorzaak en sensor blijven bewaard; de juiste code schakelt uit, een foute code niet. De sirene klinkt opnieuw en meldingen die nog moesten escaleren, escaleren alsnog, zonder de al verstuurde te herhalen. |
| De **sirenetijd was om terwijl Home Assistant uit was** | Het alarm is bij het opstarten afgelopen en het systeem is weer ingeschakeld, niet uitgeschakeld. |
| De opgeslagen toestand is **onbruikbaar** | Vigil start uitgeschakeld en logt `state_restore_failed`. |
| Sensoren zijn er direct na een start nog niet | Korte tijd noemt Vigil dat geen storing en schakelt niet in; daarna wordt een sensor die nog ontbreekt als onbereikbaar gemeld. |

## Sensoren

| Situatie | Wat Vigil doet |
|---|---|
| Een sensor wordt **onbeschikbaar terwijl ingeschakeld** | Wordt gemeld (`supervision_lost` en een Reparatie) en laat het alarm **niet** afgaan; als hij terug is, `supervision_restored`. Een sensor die al onbeschikbaar is *voor* het inschakelen weigert het inschakelen, tenzij zijn instelling *Bij onbereikbaar* anders zegt. |
| Een sensor meldt **twee keer dezelfde toestand** (nieuw attribuut, batterij-update) | Er verandert niets: de ingangsvertraging begint niet opnieuw en er komt geen tweede gebeurtenis. |
| Een deur **gaat open en weer dicht** in de ingangsvertraging | Het eindigt na de ingangsvertraging toch in een alarm; de deur sluiten annuleert niets, alleen een code. |
| Een **tweede sensor** gaat af tijdens het alarm | Eén alarm: er begint geen tweede. |
| **Rook** tijdens een inbraakalarm | Gaat niet verloren: het alarm toont ook de oorzaak brand. |

## Commando's

| Situatie | Wat Vigil doet |
|---|---|
| Hetzelfde **inschakelcommando twee keer** tijdens de uitgangsvertraging | De vertraging wordt niet verlengd. |
| **Twee keer uitschakelen** | Ongevaarlijk; het systeem is uitgeschakeld. |
| **Uitschakelen tijdens de uitgangsvertraging** | Het inschakelen wordt geannuleerd en blijft geannuleerd. |

## Als de rest van de installatie uitvalt

| Situatie | Wat Vigil doet |
|---|---|
| De **telefoon is niet bereikbaar** (de notify-service faalt) | De fout wordt gemeld en gelogd; het alarm zelf wordt er niet door beïnvloed. |
| De **sirene kan niet aan** | Gemeld en gelogd; het alarm zelf niet beïnvloed en het kan nog steeds worden uitgeschakeld. |
| Beide tegelijk | Het alarm gaat toch af, toont zijn toestand op de panelen en de kaart en kan met een code worden uitgeschakeld. |

## Wat niet gedekt is

- Home Assistant zelf dat uit is, of het netwerk tussen Home Assistant en een Zigbee- of Z-Wave-stick dat uit is: zie de heartbeat en het toezicht op onbereikbare sensoren.
- Een stroomstoring: Vigil weet alleen wat Home Assistant meldt. Zet de host, de router en de Zigbee- of Z-Wave-stick op een UPS als je op het alarm vertrouwt.
- Certificering: Vigil is geen gecertificeerd alarmsysteem.
