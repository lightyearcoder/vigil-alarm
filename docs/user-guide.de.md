# Vigil Alarm: Benutzerhandbuch

Dieses Handbuch erklärt, wie du Vigil Alarm einrichtest und benutzt. Zur Installation siehe die
[README](../README.md) (Englisch). Die Originalfassung ist das englische
[user-guide.md](user-guide.md); weitere Fassungen gibt es auf
[Niederländisch](user-guide.nl.md), [Französisch](user-guide.fr.md),
[Italienisch](user-guide.it.md) und [Spanisch](user-guide.es.md).

> Vigil Alarm ist keine zertifizierte Alarmanlage. Teste sie regelmäßig und verlasse dich nicht
> darauf als einzigen Schutz.

> Die deutschen Texte wurden von Claude (einer KI) übersetzt und nicht von einer Muttersprachlerin
> oder einem Muttersprachler geprüft. Melde eine holprige oder falsche Stelle bitte als Issue.

## Inhalt

1. [Wie alles zusammenhängt](#wie-alles-zusammenhängt)
2. [Einrichten, Schritt für Schritt](#einrichten-schritt-für-schritt)
3. [Die Alarmanlage im Alltag](#die-alarmanlage-im-alltag)
4. [Was bei einem Alarm passiert](#was-bei-einem-alarm-passiert)
5. [Nachschlagen: das Panel, Tab für Tab](#nachschlagen-das-panel-tab-für-tab)
6. [Automatisierungen und Blueprints](#automatisierungen-und-blueprints)
7. [Automatisches Scharfschalten](#automatisches-scharfschalten)
8. [Selbstüberwachung](#selbstüberwachung)
9. [Neustarts und Updates](#neustarts-und-updates)
10. [Fehlersuche](#fehlersuche)
11. [Grenzen, die du kennen solltest](#grenzen-die-du-kennen-solltest)

## Wie alles zusammenhängt

| Teil | Was es ist |
|---|---|
| **Alarm** | Eine `alarm_control_panel`-Entität. Zustände: *disarmed* (aus), *arming* (Ausgangsverzögerung), *armed home / away / night / vacation / custom* (scharf), *pending* (Eingangsverzögerung) und *triggered* (ausgelöst). |
| **Modi** | *Zuhause* (du bist da, der Außenbereich wird überwacht), *Abwesend* (niemand zu Hause, alles wird überwacht) und *Nacht* (du schläfst, der Außenbereich wird überwacht). Zwei weitere Modi lassen sich unter *Partitionen* (im Formular der Partition) einschalten: *Urlaub* (längere Abwesenheit) und *Benutzerdefiniert* (deine eigene Wahl; Home Assistant nennt ihn *custom bypass*). Jeder Modus hat eine eigene Ausgangsverzögerung, und Sensorgruppen können in ihnen wie in den anderen Modi aktiv sein. Vigil legt nicht fest, was sie bedeuten: Du wählst, welche Sensorgruppen darin überwachen. |
| **Sensor** | Ein Melder, verbunden mit einem `binary_sensor` (an = offen oder Alarm). Jeder Sensor hat eine **Klasse**. |
| **Sensorgruppe** | Bestimmt, **in welchen Modi** die darin enthaltenen Einbruchsensoren überwachen. |
| **Bestätigungsregel** | Optional. Ein Alarm folgt erst, wenn mehrere verschiedene Sensoren innerhalb eines Zeitfensters auslösen. |
| **Benutzer** | Eine Person mit einem Code, optional auf bestimmte Modi beschränkt. |
| **Benachrichtigung** | Ein `notify`-Dienst, der Nachrichten erhält, optional verzögert (Eskalation). |
| **Sirene** | Optional. Etwas, das bei einem Alarm Lärm macht. |

### Sensorklassen

| Klasse | Verhalten |
|---|---|
| **Einbruch** | Überwacht in den Modi seiner Sensorgruppen. Typ *sofort* (Alarm sofort), *verzögert* (zuerst Eingangsverzögerung, für die Haustür) oder *Folger* (löst nur aus, wenn vorher ein verzögerter Sensor geöffnet wurde, zum Beispiel ein Flur-Bewegungsmelder hinter der Haustür). |
| **Feuer** | Überwacht immer, in jedem Modus, auch bei ausgeschaltetem Alarm. Alarm sofort. |
| **Gas** | Überwacht immer. Wähle die Gasart: Kohlenmonoxid, Erdgas, Flüssiggas (LPG) oder andere. Bei Erdgas oder Flüssiggas schaltet Vigil wegen der Funkengefahr nie das Blitzlicht ein. |
| **Sabotage** | Überwacht immer. Ein Sabotagekontakt, der öffnet, löst einen Alarm aus. |
| **Wasser** | Überwacht immer. Ein *technischer Alarm*: Er ändert nie den Alarmzustand, er veröffentlicht nur Ereignisse und einen Sensor „Alarm aktiv“. |
| **24 Stunden hörbar** | Überwacht immer, in jedem Zustand, auch bei ausgeschaltetem Alarm, wie ein Sabotagekontakt: Beim Öffnen ertönt die Sirene und die Alarmkanäle erhalten eine Nachricht (Ursache *24-Stunden-Alarm*). Für einen Panikknopf oder einen Tresor. Solange er offen ist, wird das Scharfschalten verweigert. |
| **24 Stunden still** | Überwacht immer, ohne Sirene: ein *technischer Alarm* wie Wasser, mit einer Nachricht an die *Technik*-Kanäle und einer Zeile im Protokoll. Für einen stillen Panikknopf oder eine Gefriertruhe, die zu warm wird. |

### Sensorgruppen: welche Sensoren in welchem Modus überwachen

Eine Sensorgruppe ist eine Liste von Modi. Ein Einbruchsensor gehört zu einer oder mehreren Gruppen und
überwacht in jedem Modus, in dem eine seiner Gruppen aktiv ist. Zwei Gruppen werden für dich angelegt:

| Gruppe | Aktiv in | Für |
|---|---|---|
| **Außenhaut** | Zuhause, Abwesend, Nacht | Türen und Fenster |
| **Innenraum** | Abwesend | Bewegungsmelder |

In *Zuhause* zählen also nur die Türen und Fenster, und du kannst dich frei bewegen. In *Abwesend* zählen
auch die Bewegungsmelder. Du kannst Gruppen hinzufügen, zum Beispiel *Keller* nur für *Nacht*.

Deshalb verwendet Vigil dafür auch nicht die Bereiche (Areas) von Home Assistant: Ein Bereich sagt, **wo** ein
Sensor sitzt, eine Sensorgruppe sagt, **wie du ihn nutzen willst**. Ein Türkontakt und ein Bewegungsmelder im
selben Raum gehören in verschiedene Gruppen.

Der Tab **Übersicht** zeigt „Was jeder Modus überwacht“, damit du das Ergebnis prüfen kannst.

## Einrichten, Schritt für Schritt

Öffne **Vigil Alarm** in der Seitenleiste (nur Administratoren sehen es). Jedes Speichern lädt Vigil Alarm neu;
der Alarmzustand bleibt erhalten.

1. **Prüfe die Partition** (Tab *Partitionen*, die erste Zeile ist dein Haus): Modi, Ausgangsverzögerungen,
   Standard-Eingangsverzögerung und Alarmdauer. Unter *Einstellungen* prüfst du, ob zum Scharfschalten ein Code nötig ist.
2. **Füge deine Sensoren hinzu.** Der schnelle Weg ist *Sensoren → Sensoren finden*: Vigil listet die Tür-, Fenster-, Bewegungs-, Rauch-, Gas-, Wasser- und Sabotagesensoren auf, die Home Assistant schon kennt, mit dem Batterie- und Sabotagesensor desselben Geräts. Wähle die gewünschten aus, ändere bei Bedarf einen Namen, setze bei Türen, durch die du gehst, den Haken *Eingang* (sie bekommen eine Eingangsverzögerung) und füge alle auf einmal hinzu. Gespeichert wird erst, wenn du unten auf die Schaltfläche drückst. Hast du noch keine Sensorgruppen, drücke zuerst *Standardgruppen erstellen* (Außenhaut für Türen und Fenster, Innenraum für Bewegung). Um einen von Hand hinzuzufügen, nimm *Sensoren → Sensor hinzufügen*:
   - Gib ihm einen Namen („Haustür“). Der Name bestimmt die Entitätsnamen (`sensor.haustuer_status`).
   - Wähle den `binary_sensor`. Bei einem Türkontakt oder Bewegungsmelder schlägt das Panel die passende
     Sensorgruppe selbst vor.
   - Wähle die Klasse und, bei Einbruch, den Typ und die Sensorgruppen.
   - Hat das Gerät auch einen Sabotagekontakt (die meisten Zigbee-Türkontakte haben einen)? Trage ihn unter *Sabotage-Entität* ein. Vigil legt von selbst einen Sabotagesensor namens „Haustür (Sabotage)“ an: immer überwachend, mit eigenem Umgehungsschalter. Er folgt dem Sensor, wenn du ihn umbenennst, änderst oder löschst, und hat keine eigene Zeile in der Tabelle.
   - *Wenn beim Ende der Ausgangsverzögerung offen* bestimmt, was mit einer Tür passiert, die beim Scharfschalten noch offen ist: **umgehen mit Hinweis** (Standard; sie wird wieder überwacht, sobald sie schließt), **warten bis geschlossen**, **Scharfschalten verweigern** oder **Eingangsverzögerung starten**.
   - *Wenn der Sensor nicht erreichbar wird*: **Scharfschalten blockieren** (Standard für Einbruch und
     Sabotage), **nur benachrichtigen** (Standard für Feuer, Gas und Wasser), **Alarm auslösen** oder **trotzdem
     scharfschalten (umgehen)**. Feuer und Gas können nie umgangen werden.
   - Füge optional einen Batteriesensor hinzu; Vigil warnt dann, wenn sie schwach wird.
3. **Füge einen Benutzer hinzu** (Tab *Benutzer*): ein Name und ein Code. Ohne Benutzer ist überhaupt kein Code nötig.
   Ein Benutzer kann auf bestimmte Modi beschränkt werden. Das Umgehen eines Sensors ist ein Recht, das du einem Benutzer gibst (*Darf Sensoren umgehen*): Ohne dieses Recht kann ein Benutzer einen Sensor weder umgehen noch wiederherstellen, auch nicht mit dem richtigen Code. Wer einen Sensor umgehen darf, darf ihn auch wiederherstellen. Ein Sabotagesensor braucht das zusätzliche Recht *Darf Sabotage umgehen*, sowohl zum Umgehen als auch zum Wiederherstellen. Benutzer, die vor diesem Recht gespeichert wurden, behalten es, bis du den Haken entfernst.
4. **Füge eine Benachrichtigung hinzu** (Tab *Benachrichtigungen*): wähle einen `notify`-Dienst oder eine notify-Entität (zum Beispiel eine *Benachrichtigungsgruppe*, die du unter *Einstellungen → Geräte & Dienste → Helfer → Gruppe* anlegst und die als `notify.familie` erscheint) und die Arten von
   Nachrichten, die sie erhalten soll. Eine notify-Entität bekommt nur Titel und Text: keine app-spezifischen Daten, also keinen kritischen Alarm auf dem Handy (wähle dafür einen `mobile_app_…`-Dienst). Mit einer *Verzögerung* sendet der Kanal Alarmnachrichten nur, wenn der Alarm nach dieser Zeit
   noch aktiv ist: Das ist ein Eskalationskanal für eine zweite Person oder ein zweites Gerät.
5. **Optional: eine Bestätigungsregel** (Tab *Bestätigungsregeln*): wähle die Sofort-Einbruchsensoren,
   wie viele auslösen müssen und in welchem Zeitfenster.
6. **Optional: eine Sirene** (Tab *Sirenen*). Siehe unten.
0. **Neu: der Einrichtungsassistent.** Wenn noch nicht genug eingerichtet ist, beginnt der Tab *Übersicht* mit der Karte *Vigil einrichten*, und die Karte *Einsatzbereit?* hat die Schaltfläche *Einrichtungsassistent*. Der Assistent führt Schritt für Schritt durch die Modi, die Sensoren, den Benutzer (auch aus einer Home-Assistant-Person erstellt), den Benachrichtigungskanal (ein Handy mit der App mit einem Klick), die Sirene und das Bedienteil und endet mit *Einsatzbereit?*. Jeder Schritt kann übersprungen werden, *Später weitermachen* schließt den Assistenten, und die Karte *Assistent fortsetzen* bringt dich dorthin zurück, wo du warst. Der Assistent benutzt dieselben Formulare wie die Tabs und speichert nichts, bis du bestätigst.
7. **Sieh dir *Einsatzbereit?* an** oben im Tab *Übersicht*. Es nennt, was noch fehlt (ein Benutzer mit Code, ein Benachrichtigungskanal, ein Modus, den nichts überwacht, Sensoren ohne Batteriesensor) und hat eine Schaltfläche zur richtigen Stelle. Hast du noch keinen Benachrichtigungskanal und Home Assistant kennt dein Handy, fügt eine Schaltfläche ihn hinzu und sendet eine Testnachricht.
8. **Teste alles** mit den *Test*-Schaltflächen und indem du die Anlage scharfschaltest und eine Tür öffnest. Nutze den
   [Testleitfaden](installatie-en-testen.nl.md) (Niederländisch) für einen vollständigen Testplan mit virtuellen Sensoren.

### Sirenen

Eine Sirene hat eine Ein/Aus-Entität (`siren`, `switch` oder `light`) und optionale Extras: ein Blitzlicht,
eine Entität zur Tonauswahl und eine Lautstärke-Entität. Pro Ursache (Einbruch, Feuer, Gas, Sabotage) kannst du
einen Ton und eine Lautstärke festlegen. Sie werden kurz vor dem Ertönen der Sirene gesetzt und danach zurückgesetzt. Die
Sirene stoppt, wenn der Alarm ausgeschaltet wird, und nach einer maximalen Dauer. Eine Sirene, die von selbst stoppt,
kann alle N Sekunden wieder eingeschaltet werden.

Viele Sirenen können nicht melden, ob sie wirklich an sind. Dann hat `siren_started` den Wert
`verified: false`, und ein fehlgeschlagener Befehl ergibt `siren_failed` und eine Benachrichtigung.

**Voreinstellung für die Sonoff SNZB-09P (Zigbee2MQTT):** wähle unter
*Sirene* den Ein/Aus-Schalter der Sirene und dann die Voreinstellung. Vigil trägt Töne ein (klassisch für Einbruch, Warnung für Feuer,
Notfall für Gas, schnell für Sabotage), Lautstärke und Dauer und sucht die Entitäten für Ton, Lautstärke, Blitzlicht,
Batterie und Betriebsart desselben Geräts. Wird etwas nicht gefunden, wählst du es
selbst. Bei ZHA oder einer anderen Integration wähle die Ein/Aus-Entität und trage den Rest von
Hand ein.

## Die Alarmanlage im Alltag

### Scharf- und Unscharfschalten

Nutze die Alarmpanel-Karte (oder die Kachelkarte oder die Companion-App), die *arm*-Aktionen in einer
Automatisierung oder das [Dashboard](../examples/dashboard.yaml). Gib deinen Code ein, wenn einer nötig ist.

- **Scharfschalten** startet die Ausgangsverzögerung (Zustand *arming*), dann ist der Alarm *armed*. Geh hinaus.
- **Unscharfschalten** braucht immer einen Code, wenn es Benutzer gibt. Während der Eingangsverzögerung (*pending*) hast du
  die Zeit der Eingangsverzögerung, ihn einzugeben.
- Ein Benutzer kann auf bestimmte Modi beschränkt sein; das Scharfschalten in einem anderen Modus wird verweigert.

### Wenn das Scharfschalten verweigert wird

Vigil sagt dir, warum: *ein Alarmzustand ist offen* (ein Feuer- oder Sabotagesensor ist an), *ein Sensor ist
nicht erreichbar* (ein Einbruchsensor ist nicht erreichbar und auf Blockieren gestellt) oder *ein Sensor ist offen* (ein
Sensor, der auf Verweigern gestellt ist). Das Attribut `refuse_reason` und die Benachrichtigung nennen die Sensoren. Behebe
den Fehler am Sensor oder umgehe ihn.

**Warum kann ich nicht scharfschalten?** Der Tab *Übersicht* des Vigil-Panels hat eine Karte mit diesem Namen, solange etwas
das Scharfschalten verhindert: pro Sensor, was nicht stimmt und in welchen Modi, mit den Schaltflächen *Anzeigen* und *Umgehen* (ein Feuer- oder
Gassensor kann nicht umgangen werden: Beseitige zuerst die Ursache). Auf dem Touch-Bedienteil und in der Vigil-Karte sagt ein verweigertes
Scharfschalten, was es verhindert (*Scharfschalten nicht möglich: Sabotage Haustür ist offen*) und zeigt, wenn das Bedienteil umgehen darf, eine einzige
Schaltfläche, **Umgehen und scharfschalten**, die nach einem Code fragt, dann umgeht, was das Scharfschalten verhindert, und scharfschaltet. Sie braucht dieselben
Rechte wie das Umgehen von Hand (das Recht zum Umgehen und, bei einem Sabotagesensor, das Recht, Sabotage zu umgehen), und sie ist bei einem Feuer- oder Gassensor nie möglich. In deinen eigenen Automatisierungen ist dasselbe
die Aktion `vigil_alarm.arm` mit `bypass_open: true`.

### Einen Sensor umgehen

Umgehen lässt einen Sensor aus, bis der Alarm ausgeschaltet wird (oder bis du das Umgehen aufhebst).

**Dauerhaftes Umgehen.** Setze bei einem Sensor den Haken *Umgehung nach dem Unscharfschalten behalten (dauerhaft)* (nicht möglich bei Feuer- und Gassensoren), und ein manuelles Umgehen dieses Sensors bleibt nach dem Unscharfschalten bestehen, auch über einen Neustart von Home Assistant hinweg, bis jemand es von Hand wieder aufhebt. Praktisch für einen Sensor, der schon länger defekt ist. Der Sensor bleibt in der Liste als *umgangen*, der Tab *Übersicht* hat eine Karte **Dauerhaft umgangen** mit einer Schaltfläche *Wiederherstellen*, und die Vigil-Karte und das Touch-Bedienteil zeigen unter *Aus* die Zeile *Umgangen: Kaputtes Fenster*, damit es nicht vergessen wird; das Protokoll hat `sensor_bypassed`, wenn es beginnt, und `sensor_unbypassed` (Grund *manuell*), wenn es endet. Ohne den Haken ändert sich nichts: Die Umgehung endet beim Unscharfschalten.

- Im Panel und im Dashboard: der **Umgehen**-Schalter des Sensors (nur Administratoren).
- Per Aktion: `vigil_alarm.bypass` und `vigil_alarm.unbypass` mit der Sensor-Entität und, für Personen, die keine
  Administratoren sind, einem Code. Dieser Code ist nur nötig, wenn auch das Scharfschalten einen braucht (die Einstellung
  *Code zum Scharfschalten erforderlich*). Sabotagesensoren können nur von Administratoren und von Benutzern
  mit diesem Recht umgangen werden.
- Feuer- und Gassensoren können nie umgangen werden.

### Ein Touch-Bedienteil

![Die Zustände des Touch-Bedienteils: aus, nicht bereit, wird scharf, Alarm](images/touch-panel-states-en.png)

Das Bedienteil und die Vigil-Karte haben dasselbe Aussehen. Der Zustand ist ein **Ring mit einem Symbol** in der Farbe des Zustands: grün, wenn aus und alles geschlossen ist, bernsteinfarben, wenn etwas offen ist oder beim Scharfschalten, orange während der Eingangsverzögerung, blau, korallenrot, violett, türkis und rosa für Zuhause, Abwesend, Nacht, Urlaub und Benutzerdefiniert, rot bei einem Alarm (mit einem roten Rahmen um den Bildschirm), grau ohne Verbindung. Während der Ausgangs- und Eingangsverzögerung ist der Ring der **Countdown**: die Sekunden in der Mitte, der Ring läuft bis auf leer herunter; bei null ist der Alarm an. Unter dem Ring siehst du die Schaltflächen für die Modi, die dieses Bedienteil nutzen darf, oder eine große Schaltfläche *Unscharf*, wenn der Alarm an ist. Unten sind die Tabs *Alarm*, *Sensoren* (mit der Zahl offener Sensoren) und *Info*; der Ziffernblock hat keine Tabs.

![Die anderen Seiten: Ziffernblock, Sensoren, Info, scharf abwesend](images/touch-panel-pages-en.png)

Mit eingeschaltetem *Urlaub* und *Benutzerdefiniert* gibt es bis zu fünf Modus-Schaltflächen in einer Reihe (der Text wird kleiner), und *Aus* zeigt den letzten Alarm unter dem Zustand:

![Fünf Modus-Schaltflächen mit dem letzten Alarm, scharf Urlaub, scharf benutzerdefiniert, ein 24-Stunden-Alarm](images/touch-panel-modes-en.png)


Mit dem ESPHome-Bedienteil (Guition 4848) schaltest du ohne Handy scharf und unscharf und umgehst Sensoren. Es liest
sein Profil von Vigil: Es zeigt nur die Modi, in denen das Bedienteil scharfschalten darf, fragt nach einem Code so, wie Vigil es tut, und benutzt die Sprache, die du dafür eingestellt hast.
Installation und Optionen stehen in [esphome/README.md](../esphome/README.md). Der Gerätename ist die Bedienteil-ID und die `source` jedes Aufrufs, die im Verlauf als *Anna (vigil-panel-garage)* erscheint. Ein falscher
Code ergibt das Ereignis `code_rejected`, nie mit dem Code selbst. Die Sperre geht in Stufen, und die Zahlen stellst du unter *Einstellungen*, *Sperre* ein. Standardmäßig: nach 3 falschen Codes ist dieses Bedienteil 5 Minuten gesperrt, nach 2 weiteren falschen Codes 15 Minuten, nach 2 weiteren 60 Minuten, und nach 1 weiteren falschen Code endgültig (Ereignisse `code_locked` und `code_locked_permanent`, auch an deine Störungs-Benachrichtigungskanäle gesendet). Eine dauerhafte Sperre verschwindet nur mit *Sperre aufheben* am Bedienteil, und dann beginnt alles wieder bei der ersten Stufe. Ein richtiger Code setzt auch Zähler und Stufe auf null zurück. Die Sperre bleibt bestehen, wenn Home Assistant neu startet; der gemeinsame Timer für alles, was kein registriertes Bedienteil ist (*other*), sperrt nie endgültig, weil ihn niemand aufheben könnte, sondern wiederholt die letzte Wartezeit; ein Administrator in der Oberfläche kann die Anlage trotzdem bedienen. Jedes registrierte Bedienteil (siehe unten) hat einen eigenen Timer; alles andere (ein Handy, eine Automatisierung, jeder andere Name) teilt sich einen.

#### Bedienteile, Tablets und Handys

Der Tab *Bedienteile* ist das Register von allem, was die Anlage außer über die Home-Assistant-Oberfläche bedienen darf: ESPHome-Bedienteile (erkannt an ihrer Bedienteil-ID) und Tablets oder Handys (erkannt an ihrem Home-Assistant-Konto). Alle werden gleich eingerichtet. Sobald ein Konto registriert ist, werden andere normale Konten abgewiesen, bevor ihr Code geprüft wird (Ereignis `user_refused`); Administratoren, Automatisierungen und ESPHome-Bedienteile sind davon nicht betroffen. Einzelheiten und der Rat, einem Administrator ein zweites, normales Konto für den täglichen Gebrauch zu geben, stehen im [Tablet-Leitfaden](tablet.md).

#### Ein Bedienteil registrieren (Tab *Bedienteile*)

Ein Bedienteil oder Tablet, das du im Tab *Bedienteile* registrierst, wird als „dummes Terminal“ behandelt: Vigil entscheidet, was es darf. Du gibst ihm einen Namen und eine **Bedienteil-ID**, das ist der Name des ESPHome-Geräts und zugleich die `source`, die seine Aufrufe tragen. Pro Bedienteil legst du fest:

Wenn du ein Bedienteil hinzufügst, wählst du zuerst die **Geräteart**. *ESPHome-Bedienteil* fragt nach dem Namen des ESPHome-Geräts (der Bedienteil-ID). *Tablet oder Handy mit Home Assistant* fragt nur nach dem Home-Assistant-Konto; Vigil bildet die Bedienteil-ID selbst aus dem Namen. Alles andere (Modi, Unscharfschalten, Umgehen, Sprache, Sensorliste, Errichtercode) ist bei beiden gleich. Die Sprache beginnt mit der der Person, die das Bedienteil hinzufügt, Englisch, wenn das nicht Niederländisch oder Englisch ist.

- die Modi, in denen es scharfschalten darf, und ob es unscharfschalten, Sensoren umgehen sowie stummschalten oder quittieren darf;
- die Sprache (Standard: die von Home Assistant);
- ob es die Liste der Sensoren zeigen darf: *immer*, *nur nach dem Entsperren* (Standard) oder *nie*, und wie lange es entsperrt bleibt (Standard 60 Sekunden);
- einen optionalen **Errichtercode** für dieses Bedienteil, als Hash gespeichert, mit eigenem Timer für falsche Codes. Das Bedienteil sendet ihn mit `vigil_alarm.unlock_panel`; Vigil prüft ihn und entsperrt das Bedienteil für die eingestellte Zeit. Er öffnet die Informationsseiten und (wie der Code jedes Vigil-Benutzers) die Sensorliste und schaltet den Alarm nie unscharf: Unscharfschalten braucht immer einen gültigen Benutzercode;
- was die Firmware über sich **meldet** (ihre Hardware, Firmware-Version und Profilversion), wird auf der Bedienteil-Karte gezeigt, und *Einsatzbereit?* gibt einen Rat, wenn die Firmware das Profil nicht versteht;
- **überwachen, ob es erreichbar ist** (*Überwachen, ob dieses Bedienteil erreichbar ist*): bei einem ESPHome-Bedienteil standardmäßig an, bei einem Tablet oder Handy standardmäßig aus, denn ein ausgeschaltetes Handy ist keine Störung. Ist es aus, gibt es keine Reparatur und keine Nachricht, wenn das Bedienteil ausfällt, und die Liste sagt *Nicht überwacht*. Einträge, die vor dieser Einstellung angelegt wurden, bleiben an;
- **gesperrt**: Vigil verweist jeden Aufruf mit dieser Bedienteil-ID ab und protokolliert ihn.

Was serverseitig durchgesetzt wird: Ein Aufruf eines registrierten Bedienteils, den sein Profil nicht erlaubt, wird abgelehnt und protokolliert (Ereignis `panel_refused`, mit dem Grund). Das Umgehen eines Sensors von einem registrierten Bedienteil braucht immer einen Benutzercode. Ein gesperrtes Bedienteil wird abgewiesen, bevor irgendein Code geprüft wird. Aufrufe, deren Quelle nicht registriert ist, werden von alldem nicht eingeschränkt.

Jedes registrierte Bedienteil bekommt eine Entität `sensor.<panel_id>_profile` (Bindestriche in der Bedienteil-ID werden zu Unterstrichen, `vigil-panel-garage` ergibt also `sensor.vigil_panel_garage_profile`) mit dem, was es tun und zeigen darf. Die Namen der Sensoren stehen nur darin, solange das Bedienteil entsperrt ist (oder die Liste auf *immer* steht), und die Attribute, die sie enthalten, werden aus dem Verlauf herausgehalten. Sie enthält nie einen Code, Hash, Schlüssel oder ein Passwort. **Sei ehrlich darüber, was das schützt:** `source` ist einfacher Text, Vigil kann also nicht beweisen, dass ein Aufruf wirklich von diesem Bedienteil kommt. Das Profil schützt vor Fehlern und vor einem Bedienteil, das bestimmte Schaltflächen nicht haben soll, nicht vor jemandem, der bereits Dienste aufrufen kann. Der eigentliche Schutz sind der Code, die Sperre, die verschlüsselte Verbindung des Bedienteils und die Zugriffsregeln von Home Assistant selbst.

Zwei Schaltflächen pro Bedienteil, **Entsperren** und **Sperre aufheben**, gibt es nur im Vigil-Panel (nur Administratoren) und nicht als Home-Assistant-Aktionen: Eine Aktion kann von jedem Benutzer, jeder Automatisierung und jedem Bedienteil aufgerufen werden, ein gestohlenes Bedienteil könnte sich also selbst entsperren. *Entsperren* zeigt die Sensorliste für die eingestellte Zeit; *Sperre aufheben* hebt die gespeicherte Sperre nach falschen Codes auf (sie übersteht einen Neustart, so hebst du sie also auf). Beides wird mit dem Administrator protokolliert, der es getan hat (`panel_unlocked`, `panel_lock_cleared`).

**Außer Reichweite.** Kann Vigil das ESPHome-Gerät eines Bedienteils 10 Minuten lang nicht erreichen, bekommst du eine Reparatur *Bedienteil nicht erreichbar* und eine Nachricht auf deinen Störungskanälen (Ereignisse `panel_offline` und `panel_online`). Ein Bedienteil außer Reichweite ändert nie den Alarmzustand. Ein gesperrtes Bedienteil und ein Bedienteil, bei dem *überwachen* aus ist, geben keine Reparatur. Nach einem Neustart von Home Assistant beginnen die zehn Minuten von vorn.

Auch ein Tablet kann registriert werden, an einen Home-Assistant-Benutzer gebunden, und zeigt die Vigil-Karte (`type: custom:vigil-card`); siehe den [Tablet-Leitfaden](tablet.md).

Die ESPHome-Firmware liest dieses Profil selbst. Ein Bedienteil, das nicht im Register steht, zeigt *Nicht verknüpft* mit der Bedienteil-ID, die es erwartet; ein gesperrtes Bedienteil zeigt *Gesperrt*. Die Sensorliste und die Info-Seite des Bedienteils (IP-Adresse, Signal, Firmware, Laufzeit) öffnen sich mit einem Code: die Sensorliste mit dem Code eines beliebigen Vigil-Benutzers (oder dem Errichtercode), die Info-Seite nur mit dem Errichtercode des Bedienteils; bis zum Entsperren zeigt das Bedienteil nur, wie viele Sensoren offen sind. Die Einschränkungen werden von Vigil auch für jeden Aufruf mit der `source` des Bedienteils durchgesetzt, was auch immer die Firmware tut.

### Stummschalten und quittieren

- `vigil_alarm.silence` stoppt die Sirenen, während der Alarm aktiv bleibt.
- `vigil_alarm.acknowledge` bricht die anstehenden Eskalationsnachrichten ab: Du hast es gesehen.

Beide brauchen einen Benutzercode oder einen Administrator in der Oberfläche.

## Was bei einem Alarm passiert

Ein Beispiel mit der Anlage im Modus *Abwesend* scharf und der sich öffnenden Haustür (ein verzögerter Sensor):

| Moment | Was passiert |
|---|---|
| Tür öffnet | Zustand *pending*. Ereignis `pending_started`. Benachrichtigung „Eingangsverzögerung gestartet“. |
| Innerhalb der Eingangsverzögerung | Mit einem Code unscharfschalten: kein Alarm. |
| Eingangsverzögerung endet | Zustand *triggered*, Ursache *Einbruch*. Ereignis `triggered`. Benachrichtigungen gehen raus, Sirenen ertönen, „Einbruchalarm“ schaltet sich ein. |
| Nach der Verzögerung eines Eskalationskanals | Ist der Alarm noch aktiv und nicht quittiert, sendet dieser Kanal seine Nachricht. |
| Unscharfschalten oder die Alarmdauer endet | Sirenen stoppen, `trigger_ended`, Zustand zurück auf *disarmed* oder *armed*. |

Ein Sofort-Sensor überspringt die Eingangsverzögerung. Feuer, Gas und Sabotage lösen sofort aus, in jedem Zustand. Eine
schwerwiegendere Ursache ersetzt eine weniger schwerwiegende (`trigger_cause_changed`): Die Reihenfolge ist Feuer,
dann Gas, Sabotage, Sensorstörung und Einbruch.

Mit einer **Bestätigungsregel** löst ein einzelnes Auslösen eines ihrer Sensoren keinen Alarm aus. Es
veröffentlicht `sensor_unconfirmed` (und eine Benachrichtigung, wenn du informiert werden willst). Lösen die erforderliche
Anzahl verschiedener Sensoren innerhalb des Fensters aus, wird der Alarm mit `confirmed_by`
im Ereignis ausgelöst.

## Nachschlagen: das Panel, Tab für Tab

Aktionen in den Listen sind Symbolschaltflächen (bearbeiten, kopieren, löschen, testen); fahre mit der Maus darüber für den Namen. Regeln und Benutzer haben keine Kopieren-Schaltfläche. Manche Felder haben ein ⓘ: Klicke darauf für eine ausführlichere Erklärung.

| Tab | Was du dort tust |
|---|---|
| **Übersicht** | die Karte *Alarm* mit dem Vigil-Logo und, bei mehr als einer Partition, einer farbigen Kachel pro Partition (grün aus, blau scharf, bernstein im Countdown, rot Alarm), die Karte *Üben und testen* (*Übungsmodus starten* und *Gehtest starten*, siehe *Übungsmodus und Gehtest* unten), die Karte *Vigil einrichten* (der Assistent, solange noch etwas fehlt), die Karte *Neue Sensoren gefunden* (Sensoren, die in Home Assistant hinzugekommen sind, seit Vigil zuletzt nachgesehen hat; *Prüfen und hinzufügen* öffnet die Liste nur mit den neuen, *Jetzt nicht* kündigt sie nicht noch einmal an; nie wird etwas von selbst hinzugefügt, und der Tab *Sensoren* zeigt ein Abzeichen), *Einsatzbereit?* (was noch fehlt), die Karte *Selbsttest* (letzte Prüfung, letzter Sirenentest, nächster Test, *Sirene jetzt testen*), die Karte *Heartbeat* (letzter Erfolg, *Jetzt testen*), eine Karte *Dashboard* mit einer Schaltfläche, die ein Dashboard mit deinen eigenen Entitäts-IDs kopiert, Alarmzustand, Aufmerksamkeitspunkte (schwache Batterien, nicht erreichbare Geräte), was jeder Modus überwacht, und der Live-Status jedes Sensors. |
| **Partitionen** | Eine Zeile pro Partition, die erste (dein Haus) eingeschlossen: Name, Modi, Ausgangsverzögerungen, Standard-Eingangsverzögerung, Alarmdauer und Gong-Gerät, und darunter *Was jeder Modus überwacht*, eine Karte pro Partition und eine für die Sensoren, die immer an sind. Bei mehr als einer Partition haben die nächsten Tabs (*Sensorgruppen*, *Sensoren*, *Bestätigungsregeln*) eine Tabelle pro Partition. Eine Partition, die noch Sensoren oder Sensorgruppen hat, kann nicht gelöscht werden. |
| **Sensoren** | *Sensoren finden* schlägt Sensoren aus Home Assistant vor; Sensoren hinzufügen, bearbeiten, kopieren und löschen. Unter jedem Namen sagt ein Satz, wie der Sensor reagiert und wann er überwacht. Die Tabelle zeigt den Batteriestand in einer eigenen Spalte. Eine Entität kann nur zu einem Sensor gehören. Das Feld *Sabotage-Entität* verknüpft das Sabotagesignal desselben Geräts: Vigil legt einen eigenen Sabotagesensor an, der für sich umgangen werden kann. Du kannst auch einen eigenständigen Sabotagesensor anlegen. |
| **Sensorgruppen** | Welche Sensoren in welchen Modi überwachen. Eine Gruppe kann sich für neue Türkontakte oder Bewegungsmelder *selbst vorschlagen*. Eine Gruppe, die noch benutzt wird, kann nicht gelöscht werden. |
| **Bestätigungsregeln** | Mehrere Sensoren müssen innerhalb eines Zeitfensters auslösen. Ein Sensor, der in einer Regel ist, kann nicht gelöscht werden. |
| **Benutzer** | (Kann nicht kopiert werden.) Name, Code, erlaubte Modi, Recht zum Umgehen, Recht, Sabotage zu umgehen. Codes werden gehasht gespeichert und nie angezeigt. Lass beim Bearbeiten den Code leer, um ihn zu behalten. |
| **Benachrichtigungen** | `notify`-Dienst, Arten von Nachrichten (Alarm, Eingangsverzögerung, Scharf- und Unscharfschalten, Störungen und Hinweise, technische Alarme), Verzögerung, hohe Priorität. *Test* sendet eine Testnachricht. |
| **Sirenen** | Siehe oben. *Test* lässt die Sirene 3 Sekunden ertönen (bei einem echten Alarm verweigert). |
| **Protokoll** | Alles, was Vigil als Ereignis veröffentlicht, das Neueste zuerst (die neuesten 200 werden gezeigt). Die Spalte *Benutzer* sagt, wer es getan hat, und *Über* wo (Bedienteil oder Gerät); an einem Bedienteil ohne Code scharfgeschaltet heißt *unbekannt (kein Code)*. *Download* liefert das ganze Protokoll als JSON Lines oder CSV (RFC 4180), mit Zeiten in UTC (RFC 3339) und den Feldern `time`, `event`, `partition`, `source`, `user`, `item`, `result` und `detail`. Es behält standardmäßig 90 Tage (*Einstellungen*), enthält keine Codes und übersteht Neustarts. |
| **Sicherung** | Die letzten 10 Versionen deiner Konfiguration (bei jeder Änderung wird eine aufbewahrt, mit dem, was sich geändert hat), *Wiederherstellen* für jede (es zeigt zuerst, was sich ändern würde, und die Wiederherstellung selbst lässt sich auf dieselbe Weise rückgängig machen), und *Konfiguration exportieren* und *Konfiguration importieren…* als Datei. Siehe *Sicherungen, Export und Import* unten. |
| **Einstellungen** | Was für das ganze System gilt: wie lange nach einem Neustart von Home Assistant auf langsame Sensoren gewartet wird (Sekunden, Standard 120), der Bildschirm der Bedienteile (Sekunden bis der Bildschirm dunkel wird, Standard 30, ob er auch während eines Alarms dunkel werden darf, Standard nein, und die Zeit bis zum Zurückspringen auf die Standardpartition, Standard 30 Sekunden, 0 = nie), Batteriegrenze, Code zum Scharfschalten erforderlich, minimale Codelänge (4 bis 12 Zeichen, Standard 4; gilt für neue und geänderte Codes, bestehende Codes funktionieren weiter), Tage, die das Protokoll behalten wird (Standard 90), und der Selbsttest: Erinnerungsintervall (Standard 30 Tage, 0 = aus), Sekunden, die die Sirene ertönt (1 bis 5, Standard 2), selbstständiges Ertönen und die Stunden, in denen es das darf, und die Heartbeat-Adresse mit ihrem Intervall in Minuten (Standard 5). |
| **Info** | Ein Abzeichen „neu“ nach einem Update, Version, Links zum Benutzerhandbuch und zu GitHub, Versionshinweise (das Neueste zuerst) und eine Schaltfläche, die die Details für einen Fehlerbericht kopiert. |

Vigil spricht **Englisch, Niederländisch, Deutsch, Französisch, Italienisch und Spanisch**; jede andere Sprache zeigt Englisch. Die
Sprache der **Benachrichtigungstexte** folgt der Home-Assistant-Systemsprache (Einstellungen → System → Allgemein).
Das Admin-Panel und die Vigil-Karte folgen deiner eigenen Profilsprache. Ein Touch-Bedienteil oder Tablet hat die Sprache, die du
dafür unter *Bedienteile* wählst (ein neues Bedienteil beginnt mit der Sprache deines Kontos). Die Übersetzungen ins Deutsche,
Französische, Italienische und Spanische wurden von Claude (einer KI) geschrieben und nicht von Muttersprachlern geprüft: Bitte melde
einen holprigen oder falschen Text als Issue. Ein Touch-Bedienteil (ESPHome) braucht die Firmware 0.5.6, um die neuen Sprachen zu sprechen;
ältere Firmware zeigt dafür Englisch.

## Übungsmodus und Gehtest

Der **Übungsmodus** lässt dich die Anlage echt laufen, ohne die Nachbarn zu erschrecken. In der Übersicht: *Übungsmodus starten* (nur bei ausgeschaltetem Alarm). Der Alarm funktioniert dann wie immer: Er zählt herunter, die Eingangsverzögerung läuft, er löst aus, und die Bedienteile (auch die Vigil-Karte und der Touchscreen) zeigen es. Aber **keine Sirene ertönt** und **keine Nachricht geht raus**, nicht einmal eine Störungsmeldung. Alles steht im Protokoll mit `practice` in den Details. Das Bedienteil zeigt oben ein Chip *Übungsmodus*, die Vigil-Karte eine Zeile, und die Alarm-Entität hat das Attribut `practice`. Der Übungsmodus endet **beim ersten Unscharfschalten** (eine Runde), nach 30 Minuten oder mit *Übungsmodus beenden*, damit ein vergessener Übungsmodus nie einen echten Alarm stumm halten kann. Nach einem Neustart von Home Assistant ist er aus. **Läuft der Übungsmodus ab, während die Anlage scharf ist,** bleibt sie scharf und funktioniert ab dann echt: Ein Einbruch lässt die Sirene ertönen und sendet Nachrichten. Geht der Alarm in diesem Moment gerade los, starten Sirene und Nachrichten dann.

Der **Gehtest** prüft, dass jeder Sensor reagiert. Bei ausgeschaltetem Alarm: *Gehtest starten* (in der Übersicht oder unter *Sensoren*), geh an den Türen, Fenstern und Bewegungsmeldern entlang und sieh zu, wie sie live abgehakt werden. Es nehmen nur **Einbruchsensoren** teil: Sie tun bei ausgeschaltetem Alarm nichts. Feuer-, Gas-, Wasser- und Sabotagesensoren sind immer an und würden einen echten Alarm starten; teste diese mit ihrer eigenen Testschaltfläche. Ein Sensor, der nicht reagiert, stoppt den Test nicht: Am Ende sagt eine Liste, was gefehlt hat (*hat nicht reagiert* oder *ist nicht erreichbar*). Der Test endet, wenn alle Sensoren gesehen wurden, mit *Test beenden*, nach 15 Minuten oder sobald du die Anlage scharfschaltest. Das Protokoll hat `walktest_started` und `walktest_finished`.

## Alarmgedächtnis, Fehlalarme, Bedrohungscode und Gong

**Alarmgedächtnis.** Ab dem Moment, in dem eine Eingangsverzögerung beginnt, bis der Alarm unscharfgeschaltet wird, schreibt Vigil **jeden Sensor auf, der öffnet**, mit der Zeit und dem Raum (dem Bereich, den du dem Sensor in Home Assistant gegeben hast). Das schließt Sensoren ein, die im scharfen Modus nicht zählen (ein Bewegungsmelder, der nur in *Abwesend* überwacht, während du auf *Zuhause* scharf bist), und Sensoren, die umgangen sind: Für den Weg eines Einbrechers durchs Haus sagen sie alle etwas. Ein Sensor, der flackert, ist ein Schritt mit einer Anzahl. Der Tab *Übersicht* hat die Karte **Letzter Alarm**: wann, die Ursache, der erste Sensor, ob er unscharfgeschaltet (und von wem) oder abgebrochen wurde, und die Schritte der Reihe nach, mit der Angabe für jeden Schritt, ob er für den Alarm zählte. Ein Sensor, der zählte, steht im Protokoll als `sensor_faulted`; einer, der nicht zählte, hat eine eigene Zeile `alarm_sensor_seen`. Die Vigil-Karte zeigt *Letzter Alarm: 14:03 Haustür → Flur → Wohnzimmer*, solange der Alarm aus ist (nach dem Code, wenn die Sensorliste verborgen ist). Die Alarm-Entität hat das Attribut `last_alarm` mit demselben in Kurzform (die letzten 8 Schritte).

Das Gedächtnis bleibt nach einem Neustart bestehen, bis jemand es löscht oder der nächste Alarm es ersetzt. **Löschen braucht keinen Code**: *Alarmgedächtnis löschen* auf der Karte im Vigil-Panel (Tab Übersicht), der Dienst `vigil_alarm.clear_alarm_memory` oder eine Automatisierung. Während ein Alarm läuft, kann es nicht gelöscht werden. Eine Eingangsverzögerung, die rechtzeitig mit einem Unscharfschalten endet, ist kein Alarm und hinterlässt nichts. Das Touch-Bedienteil zeigt es noch nicht (dafür braucht es neue Firmware).

**Fehlalarme: das Abbruchfenster.** Wer innerhalb von **60 Sekunden, nachdem die Sirene losging,** einen gültigen Code eingibt (eine Einstellung unter *Einstellungen → Modi und Verzögerungen*; 0 schaltet es aus), hat einen Fehlalarm verursacht: Die Sirene stoppt wie bei jedem Unscharfschalten, das Alarmgedächtnis sagt *abgebrochen*, und eine Nachricht *Alarm abgebrochen: Fehlalarm durch Anna* geht an die Alarmkanäle, die schon vom Alarm erfahren haben. Ereignis `alarm_cancelled`. Es gilt nur für Einbruchalarme; Feuer, Gas und Sabotage gelten nie als Fehlalarm.

**Bedrohungscode.** Bearbeite einen Benutzer und trage *Bedrohungscode (optional)* ein: ein zweiter Code für den Fall, dass dich jemand zwingt, die Anlage auszuschalten. Er muss sich von jedem anderen Code unterscheiden, und Vigil nimmt ihn nur an, wenn es mindestens einen Benachrichtigungskanal mit der Nachrichtenart **Bedrohung** gibt. Seine Eingabe funktioniert genau wie der normale Code: Der Alarm wird unscharfgeschaltet, die Sirene bleibt still, **nichts zeigt sich** am Bedienteil, auf der Karte oder in der Ereignis-Entität. Währenddessen erhalten die Kanäle mit *Bedrohung* *STILLER ALARM: Anna hat um … den Bedrohungscode benutzt* (mit hoher Priorität, wenn der Kanal das hat). Die Zeile `duress_used` steht nur im Protokoll. Er funktioniert auch beim Scharfschalten und bei den anderen Aktionen, und er zählt nie als abgebrochener Alarm. Wähle einen Code, den du ohne Nachdenken eingeben kannst, und schreibe ihn nicht dort auf, wo ein Einbrecher sucht.

**Gong.** Setze bei einem Sensor den Haken *Gong*: Öffnet er **bei ausgeschaltetem Alarm**, ertönt ein kurzer Ton. Unter *Partitionen* (im Formular der Partition) wählst du, was den Ton macht (eine Sirene, ein Schalter, ein Licht, eine Taste oder ein Skript), und unter *Einstellungen → Gong* wie lange. Es gibt keinen Alarm, keine Nachricht und nichts im Protokoll; bei eingeschaltetem Alarm passiert nichts. Das Ereignis `chime` steht auf der Ereignis-Entität, sodass eine Automatisierung mehr tun kann (zum Beispiel eine Nachricht auf einem Lautsprecher), auch wenn du keine Entität wählst. Ein Kontakt, der flackert, läutet einmal pro 3 Sekunden.

## Partitionen: das Haus und die Garage

Standardmäßig hat Vigil einen Alarm. Unter **Partitionen** kannst du weitere hinzufügen, für eine Garage, eine Werkstatt oder ein Gästehaus. Jede Partition hat ihren eigenen Zustand (scharf oder nicht), ihre eigenen Modi und Verzögerungen und ihre eigene Alarm-Entität.

- **Die erste Partition** ist die Anlage, die du schon hattest. Sie ist die erste Zeile unter *Partitionen*, wo du sie umbenennst und ihre Modi und Verzögerungen änderst; *Einstellungen* enthält nur, was für das ganze System gilt. Weitere Partitionen haben ihre eigenen *Modi und Verzögerungen* in ihrem Formular (eine Partition darf weniger Modi haben als das Haus; ein Sensor überwacht dann nur in den Modi, die die Partition hat).
- **Ein Sensor gehört zu einer Partition** (Feld *Partition*). Feuer-, Gas-, Wasser- und 24-Stunden-Sensoren haben keine Partition: Sie überwachen in allen. Der Sabotagekontakt eines Sensors (der Sabotage-Eingang, den du beim Sensor einträgst) überwacht in der Partition dieses Sensors, sodass ein Garagen-Bedienteil nur die Sabotage der Garage zeigt und umgeht. Ein Sabotagesensor, den du selbst hinzufügst (Klasse *Sabotage*), hat ebenfalls eine Auswahl *Partition*, mit *Alle Partitionen* als Standard. Ihr Alarm ist ein Alarm für das ganze Haus; ihn in irgendeiner Partition, die im Alarm ist, unscharfzuschalten beendet ihn überall.
- **Die Entität *Alle*** erscheint, wenn es mehr als eine Partition gibt. Ihr Zustand ist der höchste Zustand einer Partition; unterscheiden sie sich, sagt das Attribut `status` `mixed`, und die Karte sagt *Gemischt*. *Alle* scharfzuschalten schaltet jede Partition oder keine scharf: Wird eine verweigert (eine offene Tür, ein Modus, den sie nicht hat), wird nichts scharfgeschaltet.
- **Wer was darf:** Ein Benutzer, ein Bedienteil, eine Sirene und ein Benachrichtigungskanal haben immer eine Auswahl *Partitionen* (im Formular direkt über den Modi). Sie ist Pflicht: Hake die Partitionen an oder *Alle Partitionen*. Die Modi, die du darunter anhaken kannst, sind die der gewählten Partitionen. Ein Code funktioniert nur für die Partitionen seines Benutzers. Sicherheitsalarme (Feuer, Gas, Wasser, Sabotage, 24 Stunden) ertönen auf jeder Sirene, egal welche Partitionen sie hat. Benachrichtigungen bekommen den Partitionsnamen dazu, wenn es mehr als eine gibt.
- **Standardpartition eines Bedienteils:** Ein Bedienteil hat eine Pflicht-*Standardpartition* (eine seiner Partitionen oder *Alle*). Die bedient das Bedienteil nach dem Start und nach der Zeit *Zurück zur Standardpartition* (*Einstellungen*, *Bedienteil-Bildschirm*, Standard 30 Sekunden, 0 = nie).
- **Dienste:** `vigil_alarm.arm` und `vigil_alarm.disarm` nehmen `partition` (die ID oder `all`). Ohne sie wirken sie auf die erste Partition.
- Eine Partition, die noch Sensoren oder Sensorgruppen hat, kann nicht gelöscht werden; verschiebe sie zuerst.
- **Sensorgruppen gehören zu einer Partition.** Bei mehr als einer Partition hat der Tab *Sensorgruppen* eine Tabelle pro Partition. Eine Gruppe bietet nur die Modi ihrer Partition an, und ein Sensor kann nur die Gruppen seiner eigenen Partition benutzen. Eine neue Partition beginnt ohne Gruppen: Nutze *Standardgruppen erstellen* in ihrer Tabelle. Bestätigungsregeln werden ebenfalls pro Partition aufgelistet (alle Sensoren einer Regel müssen in einer Partition sein).
- **Das Protokoll** hat eine Spalte *Partition*; ein Feuer-, Gas-, Wasser- oder 24-Stunden-Ereignis hat keine (es gilt für das ganze Haus).
- **Touch-Bedienteile und die Tablet-Karte** zeigen immer, welche Partition (oder *Alle*) sie bedienen, auch wenn es nur eine sein darf, zusammen mit *Vigil Alarm* und dem Logo. Ein Bedienteil, das mehrere Partitionen bedienen darf, hat eine Reihe von Schaltflächen zum Wechseln (und eine Schaltfläche oben auf der Seite *Sensoren*, die wählt, wessen Sensoren aufgelistet werden); *Alle* schaltet jede Partition scharf oder unscharf. Nach der Rückkehrzeit ohne Berührung springt es auf seine Standardpartition zurück, nicht aber, solange die Sensorliste offen ist. Der Dienst `vigil_alarm.select_partition` macht denselben Wechsel aus einer Automatisierung.

## Automatisierungen und Blueprints

Alles über Benachrichtigungen und Sirenen hinaus kannst du selbst automatisieren. Vigil veröffentlicht die Ereignis-Entität
`event.<name>_alarm_events`; die [README](../README.md#for-automations) listet alle Ereignisse
und ihre Daten auf.

Die mitgelieferten [Blueprints](../README.md#blueprints) decken die häufigen Fälle ab:

- **Lichter bei einem Alarm blinken lassen** speichert den Zustand deiner Lichter, lässt sie blinken, solange der Alarm
  ausgelöst ist, und stellt sie danach wieder her, auch wenn der Alarm ausgeschaltet wird. Wähle, welche
  Ursachen blinken (Gas ist standardmäßig aus). Der Standard von 2 Sekunden an und 2 Sekunden aus bleibt
  weit unter der Frequenz, die für lichtempfindliche Personen eine Rolle spielt. Nimm für Hue einen Raum oder eine Zone
  (Gruppe) statt einzelner Lampen; Gruppen sind in Home Assistant standardmäßig deaktiviert, aktiviere
  sie also zuerst.
- **Alarmereignisse per Sprache ansagen** spricht eine Nachricht, wenn die Anlage scharf- oder unscharfgeschaltet wird, die Eingangsverzögerung
  beginnt oder sie auslöst. Lass eine Nachricht leer, um bei diesem Ereignis still zu bleiben.
- **Eigene Aktionen bei Alarmereignissen ausführen** ist der allgemeine Baustein: Wähle Ereignisse und füge
  beliebige Aktionen hinzu, mit `event_type` und `data` zur Verfügung.
- **Erinnern beim Ankommen in einem scharfen Haus** sendet eine Nachricht, wenn jemand nach Hause kommt, während die
  Anlage scharf ist. Es schaltet nicht unscharf.

### Automatisches Scharfschalten

**Scharfschalten, wenn alle gegangen sind** und **Scharfschalten zu einer festen Zeit** schalten die Anlage für dich scharf. Sie
schalten nie unscharf: Unscharfschalten braucht immer eine Person mit einem Code.

Das Scharfschalten braucht einen Code, außer *Code zum Scharfschalten erforderlich* ist im Panel ausgeschaltet. Du hast zwei
Möglichkeiten:

1. Schalte *Code zum Scharfschalten erforderlich* aus. Dann kann jeder, der die Alarm-Entität erreicht, scharfschalten
   (Unscharfschalten braucht weiterhin einen Code). Das ist die einfachste Option und enthält kein Geheimnis.
2. Behalte die Code-Pflicht und trage einen Code im Blueprint ein. Dieser Code wird **als Klartext** in der Automatisierung
   gespeichert. Lege dafür einen eigenen Vigil-Benutzer an, beschränkt auf den einen Modus, den die
   Automatisierung benutzt, und nimm nie deinen eigenen Code.

Wird das Scharfschalten verweigert (zum Beispiel weil eine Tür offen ist), kannst du eine Nachricht bekommen, die sagt,
warum. Lässt du das Nachrichtenfeld leer, wird nichts gesendet.

## Selbstüberwachung

Echte Störungen (ein nicht erreichbarer Sensor, eine schwache Batterie, eine Sirene, die nicht verfügbar ist oder mit Batterie läuft) erscheinen auch unter *Einstellungen → System → Reparaturen* und verschwinden von selbst, wenn sie behoben sind. Fehlende Einstellungen sind keine Reparaturen; *Einsatzbereit?* zeigt diese.

- **Batterie:** Gib einem Sensor oder einer Sirene einen Batteriesensor. Vigil meldet `battery_low`, wenn der
  Stand auf die Grenze fällt (Standard 20 %, eine Einstellung), und `battery_ok`, wenn er sich erholt.
- **Sensoren:** Ein nicht erreichbarer Sensor wird durch seine Einstellung *wenn nicht erreichbar* behandelt und
  mit `supervision_lost` und `supervision_restored` gemeldet.
- **Sirenen:** Vigil meldet, wenn eine Sirene nicht verfügbar wird, und, mit einer Betriebsart-Entität,
  wenn sie mit ihrer Batterie läuft (der Wert, der „mit Batterie“ bedeutet, ist eine Einstellung, Standard
  `battery`; prüfe, was dein Gerät meldet). Füge den Sabotagekontakt einer Sirene als Sabotagesensor hinzu.
- Probleme, die beim Start bestehen, stehen ohne Ereignis im Attribut `problems` der Anlage; bei Änderungen folgen Ereignisse. Die Übersicht zeigt sie unter *Achtung*.

### Selbsttest

Niemand testet jede Woche eine Sirene, also übernimmt Vigil das Erinnern. Er läuft von selbst und braucht nichts von dir, bis es Zeit für einen echten Test ist.

- **Stille Prüfung, täglich.** Vigil prüft, dass die Benachrichtigungsdienste, die du eingerichtet hast, noch existieren und dass die Sirenen erreichbar sind. Sie macht keinen Ton. Nur ein Benachrichtigungskanal, der verschwunden ist (zum Beispiel nach einem Handywechsel), erzeugt eine Nachricht und eine Reparatur; eine nicht erreichbare Sirene wird von der Überwachung oben schon als Störung gemeldet.
- **Sirenentest, monatlich.** Standardmäßig alle 30 Tage (eine Einstellung; 0 schaltet es aus) sendet Vigil eine Erinnerung an die Kanäle, die *Störungen und Hinweise* erhalten. Auf einem Handy mit der Home-Assistant-App hat die Nachricht eine Schaltfläche **Sirene testen**; ein Tippen lässt die Sirene 2 Sekunden ertönen. Du kannst auch *Sirene jetzt testen* im Tab Übersicht benutzen oder `vigil_alarm.test_siren` aufrufen.
- **Reagierst du nicht,** folgt nach 3 Tagen eine zweite Erinnerung. Nach 7 weiteren Tagen sagt eine Reparatur, dass der Test überfällig ist. Einen Test zu machen, auf einem der drei Wege, löscht sie.
- **Vigil die Sirene selbst ertönen lassen** ist standardmäßig aus. Schaltest du es ein, lässt Vigil die Sirene ertönen, wenn der Test fällig ist, aber nur zwischen den Stunden, die du festlegst (Standard 9 bis 20 Uhr), damit niemand geweckt wird.
- Der Test wird bei einem echten Alarm verweigert, und er ist kein Alarm: Es wird nichts an die Alarmkanäle gesendet.
- Die Karte *Selbsttest* im Tab Übersicht zeigt die letzte stille Prüfung, den letzten Sirenentest und wann der nächste fällig ist. Selbsttest-Ereignisse (`selftest_checked`, `selftest_reminder`, `selftest_siren_tested`) werden ins Protokoll geschrieben, zählen aber nicht als letztes Ereignis der Anlage.

### Heartbeat

Eine Sirene und eine Benachrichtigung helfen nur, wenn Home Assistant selbst läuft. Der Heartbeat deckt den anderen Fall ab: Wenn Home Assistant, der Rechner, auf dem es läuft, oder deine Internetverbindung ausfällt, kann dir nichts im Haus Bescheid sagen. Also ruft Vigil in festem Abstand eine Webadresse auf, und ein Überwachungsdienst **außerhalb** deines Hauses schlägt Alarm, wenn die Aufrufe ausbleiben.

- Vigil ist an keinen Dienst gebunden. Unter *Einstellungen* trägst du eine **Heartbeat-Adresse** und die **Minuten zwischen den Heartbeats** (Standard 5) ein. Jeder Dienst, der einen regelmäßigen Aufruf erwartet und meldet, wenn er ausbleibt, funktioniert. Lass die Adresse leer, um es auszuschalten.
- Der Aufruf erfolgt ständig, auch bei unscharfer Anlage, denn die Frage, die er beantwortet, lautet „läuft Vigil noch?“.
- Der Aufruf trägt nichts über deine Anlage: keinen Zustand, keine Namen, keine Codes. Es ist eine einfache GET-Anfrage.
- Die Adresse ist ein Geheimnis, denn Dienste legen den Schlüssel meist hinein. Vigil hält sie aus dem Protokoll, den Reparaturen und den heruntergeladenen Diagnosedaten heraus, und das Panel zeigt sie nur einem Administrator im Tab Einstellungen.
- Die Karte *Heartbeat* im Tab Übersicht zeigt das Intervall, den letzten Erfolg und den letzten Fehlschlag und hat eine Schaltfläche *Jetzt testen*. Nach drei Fehlschlägen in Folge erscheint eine Reparatur, die verschwindet, wenn der Heartbeat wieder funktioniert.

**Durchgespieltes Beispiel mit Healthchecks.io** (es gibt einen kostenlosen Tarif, oder du betreibst es selbst):

1. Lege einen Check an. Stelle seine *Periode* etwas über deinem Intervall ein, zum Beispiel 5 Minuten, und eine *Karenzzeit* von 5 bis 10 Minuten, damit ein einzelner verpasster Aufruf keine Nachricht auslöst.
2. Verbinde unter *Integrations*, wohin die Nachricht gehen soll (E-Mail oder eine App auf deinem Handy).
3. Kopiere die *Ping-URL* des Checks. Es ist eine `https://`-Adresse, die in einer langen Kennung endet.
4. Füge sie in Vigil Alarm unter *Einstellungen → Heartbeat-Adresse* ein und speichere.
5. Klicke in der Übersicht auf *Jetzt testen*. Der Check wird innerhalb weniger Sekunden grün.
6. Um zu beweisen, dass es funktioniert, stoppe Home Assistant länger als die Periode plus die Karenzzeit. Du solltest eine Nachricht vom Dienst bekommen.

Andere Dienste funktionieren genauso: Du brauchst eine Adresse, die einen Aufruf erwartet, eine Periode und einen Weg, informiert zu werden, wenn er ausbleibt.

## Neustarts und Updates

### Sicherungen, Export und Import

Wann immer sich deine Konfiguration ändert (eine Änderung im Panel, ein Import, eine Wiederherstellung), behält Vigil die
Konfiguration, wie sie unmittelbar davor war, zusammen mit einer Zusammenfassung dessen, was sich geändert hat (*Sensoren: 3 hinzugefügt,
Benutzer: 1 geändert*). Die letzten 10 Versionen werden behalten (die Zahl ist eine Einstellung, 1 bis 50, unter *Einstellungen* → *Sicherung*; ein Senken wirft die ältesten Versionen sofort weg); der Tab **Sicherung** listet sie auf. *Wiederherstellen* zeigt, was sich
ändern würde, und stellt diese Version wieder her. Wiederherstellen ist ebenfalls eine Änderung, du kannst es also mit der
dabei entstehenden Version rückgängig machen. Nach einem Speichern im Panel hat die Meldung *Gespeichert* einen Link *Rückgängig*, der die
Version von unmittelbar davor wiederherstellt. Das Augensymbol (*Ansehen*) bei einer Version öffnet ein Fenster mit der Änderung selbst (welche Elemente hinzugefügt, geändert oder entfernt wurden und welche Einstellungen). Das Pfeilsymbol (*Wiederherstellen*) stellt die Version wieder her. Die Spalte *Vigil-Version* sagt, welche Vigil-Version jede Version erzeugt hat. Ein **Update von Vigil**, das deine gespeicherte Konfiguration ändert (eine Migration), behält auch die Konfiguration von davor, als *Vigil-Update*. Eine Version, die von einer älteren *Speicherversion* erzeugt wurde, kann angesehen, aber nicht wiederhergestellt werden (das bräuchte eine Migration, und die Liste sagt es); Versionen, die nach dem Update entstanden sind, können es. Nur die Konfiguration wird behalten, nicht der Zustand der Anlage (scharf, umgangen).

*Konfiguration exportieren* lädt die ganze Konfiguration als Datei herunter; *Konfiguration importieren…* liest eine solche
Datei, zeigt, was sich ändern würde, und ersetzt die Konfiguration, wenn du bestätigst (die bisherige Konfiguration
wird zuvor als Version behalten). Die Datei enthält keine Codes, aber die gehashten Codes, die Heartbeat-Adresse
und die Namen deiner Benachrichtigungsdienste, bewahre sie also sicher auf. Eine Datei wird nur aus
demselben Speicherformat akzeptiert (die Datei sagt, welches); importiere sie in derselben Vigil-Version, aus der sie stammt.
Sensoren, Benutzer und Bedienteile behalten ihre ID in der Datei, ein Import in der Installation, aus der sie stammt, behält also
die Entitäten; in einer anderen Installation werden die Entitäten neu angelegt.

- Der Alarmzustand und laufende Timer werden gespeichert. Nach einem Neustart ist die Anlage im selben Zustand;
  eine Eingangsverzögerung, die während des Neustarts abgelaufen ist, wird zu einem Alarm, mit der richtigen Zeit.
- In den ersten 10 Sekunden nach dem Start von Home Assistant werden die Sensorzustände noch nicht für voll genommen, damit
  Sensoren, die noch nicht geladen sind, keine falschen Störungen verursachen. Das Scharfschalten in dieser Zeit wird mit
  „startet noch“ verweigert.
- Ein Update von Vigil Alarm über HACS braucht einen Neustart von Home Assistant. Deine Konfiguration wird
  automatisch migriert.

## Fehlersuche

Siehe auch **[Meine Alarmanlage tut nicht, was ich erwarte](troubleshooting.md)** (Englisch).

| Problem | Was tun |
|---|---|
| **Kein „Vigil“ in der Seitenleiste** | Nur Administratoren sehen es. Lade den Browser hart neu, starte Home Assistant neu und suche im Protokoll nach Zeilen mit `vigil`. |
| **Das Panel bleibt leer oder sagt, es konnte nicht geladen werden** | Die Integration läuft nicht: Sieh unter Einstellungen → Geräte & Dienste nach einem Fehler. Lade den Browser neu. |
| **Das Scharfschalten wird verweigert** | Lies den Grund in der Benachrichtigung oder im Attribut `refuse_reason` und prüfe die dort genannten Sensoren. |
| **Ein Sensor wird als nicht erreichbar gemeldet** | Prüfe das Gerät. Für kurze Zeit kannst du *wenn nicht erreichbar* auf *trotzdem scharfschalten (umgehen)* stellen. |
| **Keine Benachrichtigung kommt an** | Benutze *Test* bei der Benachrichtigung. Prüfe, ob der `notify`-Dienst existiert und die Nachrichtenart angehakt ist. |
| **Die Sirene ertönt nicht** | Benutze *Test* bei der Sirene. Prüfe die Ein/Aus-Entität und die Ursachen unter *Ertönen bei* der Sirene. Manche Sirenen stoppen nach ihrer eigenen Dauer von selbst; siehe *wiederholen alle*. |
| **Eine Automatisierung reagiert nicht** | Löse auf die Ereignis-Entität aus (nicht auf den Alarmzustand) und prüfe `event_type` in der Ablaufverfolgung der Automatisierung. |
| **Ein Blueprint kann nicht scharfschalten** | Das Scharfschalten braucht einen Code. Siehe [Automatisches Scharfschalten](#automatisches-scharfschalten). |

Gib für einen Fehlerbericht an, was du getan hast, was du erwartet hast, was passiert ist, und die Protokollzeilen
mit `vigil` (Einstellungen → System → Protokolle). Für mehr Details füge in `configuration.yaml` ein:

```yaml
logger:
  logs:
    custom_components.vigil_alarm: debug
```

## Grenzen, die du kennen solltest

- Vigil Alarm ist für **keine** Alarm-, Brandmelde- oder Versicherungsnorm **zertifiziert**.
- Es läuft innerhalb von Home Assistant. Ist Home Assistant aus oder startet neu, gibt es keinen Alarm.
- Alles wird von Home-Assistant-Administratoren im Panel konfiguriert. Es gibt keinen anderen
  Weg, Sensoren und Benutzer zu bearbeiten; das ist Absicht.
- **Tags** können bei einem Benutzer gespeichert werden, haben aber **keine Funktion**. Bediene die Anlage
  mit einem Code.
- Dein eigener Code schützt nur die Alarm-Entität. Jeder, der Home-Assistant-Administrator ist,
  kann die Konfiguration ändern.
- Teste regelmäßig, einschließlich eines echten Alarms und deines Benachrichtigungswegs, und tausche Batterien aus,
  wenn Vigil es dir sagt.
