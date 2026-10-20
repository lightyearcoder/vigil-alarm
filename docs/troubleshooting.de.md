# Meine Alarmanlage tut nicht, was ich erwarte

Dies ist eine Übersetzung von [troubleshooting.md](troubleshooting.md), übersetzt von Claude (einer KI) und nicht von Muttersprachlern geprüft. Fehler bitte als Issue melden.

Such unten, was du siehst. Zu jedem Symptom: die wahrscheinlichen Ursachen, wo du nachschaust und was du tun kannst.

**Schau immer zuerst hier nach:**

- **Übersicht** im Panel: Die Karte *Einsatzbereit?* nennt, was in den Einstellungen noch fehlt. *Achtung* nennt Sensoren mit leerer Batterie oder die nicht erreichbar sind. *Was jeder Modus überwacht* zeigt, welche Sensoren in welchem Modus mitmachen.
- **Letztes Ereignis:** Die Entität `sensor.vigil_alarm_last_event` und das Ereignisprotokoll (`event.vigil_alarm_alarm_events`) zeigen, was passiert ist und warum etwas abgelehnt wurde.
- **Attribute der Alarmanlage** (`alarm_control_panel.vigil_alarm`): `open_sensors`, `bypassed_sensors`, `faults`, `problems`, `refuse_reason`.

## Die Alarmanlage lässt sich nicht scharfschalten

| Du siehst | Ursache | Was tun |
|---|---|---|
| `refuse_reason: sensor_open` | Ein überwachter Sensor ist offen (zum Beispiel ein Fenster). | Schließe ihn, oder wähle am Sensor, was beim Scharfschalten geschieht, wenn er offen ist (umgehen, auf Schließen warten, ablehnen). |
| `refuse_reason: sensor_unavailable` | Ein Sensor ist nicht erreichbar (leere Batterie, außer Reichweite). | Unter *Achtung* steht, welcher. Behebe es oder umgehe ihn. |
| `refuse_reason: alarm_condition` | Ein Brand-, Gas- oder Sabotagealarm ist aktiv. | Behebe die Ursache und schalte zuerst unscharf. |
| `refuse_reason: not_disarmed` | Die Alarmanlage ist schon scharf oder in der Ausgangsverzögerung. | Schalte zuerst unscharf. |
| Ein Fehler zum Code | Falscher Code, zu kurz, für diesen Modus nicht erlaubt oder gesperrt (siehe unten). | Prüfe den Benutzer im Tab *Benutzer*. |

## Die Alarmanlage löst bei offener Tür oder Bewegung nicht aus

1. **Ist die Alarmanlage wirklich scharf?** Während der Ausgangsverzögerung (`arming`) wird noch nichts überwacht.
2. **Ist der Sensor in einer Sensorgruppe?** Ein Einbruchsensor ohne Gruppe überwacht nichts. Wenn *Was jeder Modus überwacht* „keine Sensorgruppe“ sagt, lege die Standardgruppen an (Karte *Einsatzbereit?*).
3. **Ist die Gruppe in diesem Modus aktiv?** *Innenraum* gilt zum Beispiel nur für Abwesend. In Zuhause löst ein Bewegungsmelder nie aus.
4. **Ist der Sensor umgangen?** Dann steht er unter `bypassed_sensors`. Eine Umgehung endet beim Unscharfschalten.
5. **Ist der Typ „verzögert“?** Dann kommt zuerst die Eingangsverzögerung (`pending`), und der Alarm löst nur aus, wenn du nicht rechtzeitig unscharf schaltest.
6. **Gibt es eine Bestätigungsregel?** Dann löst der Alarm erst aus, wenn genügend verschiedene Sensoren innerhalb des Zeitfensters auslösen. Ein einzelner Sensor gibt nur den Hinweis „ohne Bestätigung“.
7. **Ist der Sensor nicht erreichbar?** Dann kann er nicht auslösen. Siehe *Achtung*.
8. **Ist es die richtige Entität?** Prüfe unter *Entwicklerwerkzeuge → Zustände*, ob die Entität wirklich auf `on` wechselt, wenn die Tür sich öffnet.

## Keine Benachrichtigung auf meinem Handy

1. Gibt es einen **Benachrichtigungskanal**? Wenn nicht, sagt *Einsatzbereit?* das und bietet dein Handy an.
2. Sind die richtigen **Kategorien** aktiv? Nur Nachrichten dieser Kategorien werden gesendet (Alarm, Eingangsverzögerung, Störung, Technisch).
3. Gibt es eine **Verzögerung**? Ein Eskalationskanal mit 30 Sekunden Verzögerung benachrichtigt erst nach 30 Sekunden, und nicht, wenn du vorher unscharf schaltest oder quittierst.
4. Benutze die **Testtaste** des Kanals. Kommt der Test nicht an, liegt das Problem bei Home Assistant oder der App, nicht an der Alarmanlage: Prüfe die Benachrichtigungsberechtigung der App auf deinem Handy.
5. Ist der **Dienst** richtig? Es muss ein vorhandener `notify.`-Dienst sein.

## Die Sirene ertönt nicht

1. Ist eine Sirene eingerichtet, und ertönt sie bei *dieser Ursache* (Einbruch, Brand, Gas, Sabotage, Störung)?
2. Probiere die Aktion `vigil_alarm.test_siren`. Ertönt sie nicht, liegt das Problem an der Entität selbst (nicht erreichbar, leere Batterie).
3. Wurde die Sirene mit `vigil_alarm.silence` **stummgeschaltet**? Dann bleibt der Alarm aktiv, aber die Sirene schweigt.
4. Ist die **Höchstdauer** abgelaufen? Danach stoppt die Sirene von selbst.

## Mein Code wird abgelehnt

- **Zu kurz:** Die Mindestlänge steht in den *Einstellungen* (4 bis 12 Zeichen).
- **Gesperrt:** Nach einigen falschen Codes sperrt Vigil diese Stelle stufenweise (standardmäßig 5, dann 15, dann 60 Minuten), auch für den richtigen Code. Warte kurz; das Ereignisprotokoll zeigt `code_locked`. Zeigt es `code_locked_permanent`, bleibt das Bedienteil gesperrt, bis ein Administrator unter Bedienteile auf *Sperre aufheben* drückt. Die Zahlen stehen unter *Einstellungen*, *Sperre*.
- **Nicht erlaubt:** Der Benutzer darf nur bestimmte Modi verwenden. Prüfe *Erlaubte Modi*. Unscharfschalten funktioniert immer mit einem gültigen Code.

## Fehlalarme

- Gib Türen den Typ **verzögert** mit einer Eingangsverzögerung, damit du rechtzeitig unscharf schalten kannst.
- Lass einen Bewegungsmelder nur in Abwesend überwachen (Gruppe *Innenraum*).
- Benutze eine **Bestätigungsregel**: ein Alarm nur, wenn zwei Bewegungsmelder innerhalb einer Minute auslösen.
- Bei einer Benachrichtigung zeigt das Ereignisprotokoll, welcher Sensor es war.

## Keine Batterie- oder Sabotagemeldungen

- Der Sensor braucht einen **Batteriesensor**. *Einsatzbereit?* nennt Sensoren ohne. Ein Gerät, das nur „Batterie schwach“ (an/aus) meldet, funktioniert auch.
- Hat das Gerät einen **Sabotagesensor**, trage ihn am Sensor ein. Die Karte nennt Sabotagesensoren, die mit nichts verbunden sind.

## Die Entitäten heißen anders als erwartet

Die Entitäts-IDs von Vigil enden immer auf den englischen Namen, auch wenn Home Assistant auf eine andere Sprache eingestellt ist (zum Beispiel `binary_sensor.vigil_alarm_intrusion_alarm`). Was du in der Oberfläche siehst, folgt deiner eigenen Sprache. Die echten Namen findest du unter *Einstellungen → Geräte & Dienste → Vigil Alarm*. Kommst du von einer älteren Version, passe deine Automatisierungen und Dashboards an die neuen IDs an (siehe die Versionshinweise).

## Das Panel ist leer

Lade den Browser neu (Strg+F5) und prüfe unter *Geräte & Dienste*, dass die Integration läuft. Sonst schau ins Protokoll (*Einstellungen → System → Protokolle*, nach `vigil` suchen).

## Es funktioniert immer noch nicht?

Lade die Diagnose herunter (*Geräte & Dienste → Vigil Alarm → ⋮ → Diagnose herunterladen*), sie enthält keine Codes oder Namen von Personen, und melde es auf GitHub (siehe den Tab *Info*).

## Ich bekomme immer wieder eine Sirenentest-Erinnerung

Die Erinnerung wiederholt sich, bis ein Test gemacht wurde. Tippe in der Nachricht auf *Sirene testen*, benutze *Sirene jetzt testen* im Tab Übersicht oder rufe `vigil_alarm.test_siren` auf. Um die Erinnerungen zu beenden, setze das Intervall unter *Einstellungen* auf 0.

## Der Heartbeat schlägt fehl

Die Karte *Heartbeat* im Tab Übersicht nennt den Grund: *keine Verbindung* (Home Assistant erreicht das Internet nicht oder die Adresse ist falsch), *keine Antwort innerhalb von 10 Sekunden* oder *HTTP 404* und ähnlich (der Dienst kennt die Adresse nicht; kopiere sie erneut). Korrigiere es unter *Einstellungen* und klicke auf *Jetzt testen*.
