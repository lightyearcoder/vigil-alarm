/* Vigil Alarm: admin panel.
 *
 * A plain web component (no build step). It talks only to the vigil_alarm/* websocket
 * commands, which are admin-only and share their validation with the config
 * flows. All text that comes from the user is added as text nodes, never as HTML.
 */

const TXT = {
  nl: {
    title: "Vigil Alarm",
    tamperShort: "sabotage",
    about: {
      details: "Gegevens", aboutIntro: "Een modulair alarmsysteem voor Home Assistant.",
      version: "Versie", license: "Licentie", author: "Auteur", links: "Links",
      manual: "Handleiding", manualOther: "Handleiding (English)", repository: "GitHub-project", releases: "Releases op GitHub",
      issues: "Probleem melden of idee delen", panelDocs: "Aanraakpaneel (ESPHome)", licenseText: "Licentietekst",
      notes: "Release notes", notesOnlyEnglish: "De release notes zijn in het Engels.", noNotes: "Geen release notes gevonden.",
      system: "Systeem", haVersion: "Home Assistant", python: "Python", alarmState: "Alarmstatus", items: "Onderdelen",
      copyInfo: "Kopieer gegevens voor een melding", copied: "Gekopieerd", copyFailed: "Kopiëren is niet gelukt",
      disclaimer: "Vigil Alarm is geen gecertificeerd alarmsysteem. Test het regelmatig en vertrouw er niet als enige bescherming op.",
      unreleased: "Nog niet uitgebracht", firstRelease: "eerste versie",
    },
    tabs: { overview: "Overzicht", sensor: "Sensoren", sensor_group: "Sensorgroepen", rule: "Bevestigingsregels", user: "Gebruikers", notification: "Meldingen", siren: "Sirenes", log: "Logboek", settings: "Instellingen", backup: "Back-up", about: "Over", panel: "Panelen" },
    add: { sensor: "Sensor toevoegen", sensor_group: "Sensorgroep toevoegen", rule: "Bevestigingsregel toevoegen", user: "Gebruiker toevoegen", notification: "Melding toevoegen", siren: "Sirene toevoegen", panel: "Paneel toevoegen" },
    edit: { sensor: "Sensor bewerken", sensor_group: "Sensorgroep bewerken", rule: "Bevestigingsregel bewerken", user: "Gebruiker bewerken", notification: "Melding bewerken", siren: "Sirene bewerken", panel: "Paneel bewerken" },
    intro: {
      sensor: "Eén melder, zoals een deurcontact, PIR of rookmelder. Bij een inbraaksensor kies je in welke sensorgroepen hij zit. Brand-, gas-, water- en sabotagesensoren bewaken altijd en hebben geen sensorgroep nodig. Ook 24 uur hoorbaar (een paniekknop, een schuurdeur: alarm met sirene, ook als het alarm uit staat) en 24 uur stil (een vriezer of lekdetectie: alleen een melding en een regel in het logboek) bewaken altijd.",
      sensor_group: "Een sensorgroep bepaalt in welke modi de sensoren erin bewaken. Bijvoorbeeld: Buitenschil (deuren en ramen) bij Thuis, Weg en Nacht, en Binnen (beweging) alleen bij Weg.",
      rule: "Een alarm volgt pas als het opgegeven aantal verschillende sensoren binnen het tijdvenster afgaat. Handig tegen een vals alarm door één PIR.",
      user: "Personen die het alarm met een code kunnen bedienen. Wie bedient, bepaalt de code; welk apparaat bedient, regel je onder Panelen.",
      notification: "Naar wie en wanneer berichten gaan. Elke melding is één notify-dienst.",
      siren: "Optioneel. Zonder sirene werkt het alarm met meldingen.",
      panel: "Een apparaat aan de muur: een ESPHome-paneel, of een tablet of telefoon met een eigen Home Assistant-account Vigil bepaalt wat elk paneel mag en welke gegevens het krijgt; het paneel zelf beslist niets. Het paneel-id is de naam van het ESPHome-apparaat. Zodra één account is gekoppeld, kunnen andere gewone accounts het alarm niet meer bedienen.",
    },
    empty: {
      sensor: "Nog geen sensoren. Voeg eerst een sensorgroep toe als er nog geen is, en daarna je sensoren.",
      sensor_group: "Nog geen sensorgroepen. Een sensorgroep bepaalt in welke modi sensoren bewaken.",
      rule: "Nog geen bevestigingsregels. Optioneel: een alarm pas na meerdere sensoren.",
      user: "Nog geen gebruikers. Zonder gebruiker is er geen code nodig om te bedienen.",
      notification: "Nog geen meldingen. Voeg een notify-dienst toe om berichten te krijgen.",
      siren: "Nog geen sirene. Dit is optioneel; zonder sirene werkt het alarm met meldingen.",
      panel: "Nog geen panelen. Zonder geregistreerd paneel krijgt een ESPHome-paneel geen profiel en bedient het niets.",
    },
    save: "Opslaan", cancel: "Annuleren", del: "Verwijderen", dup: "Kopiëren", editBtn: "Bewerken", testBtn: "Test", close: "Sluiten",
    ready: {
      title: "Klaar voor gebruik?", allGood: "Alles is ingesteld. Test het alarm toch regelmatig.", problem: "Eerst regelen", advice: "Advies", go: "Ga erheen",
      createGroups: "Standaardgroepen maken", groupsMade: "Sensorgroepen gemaakt",
      addPhone: "Telefoon toevoegen: {name}", phoneAdded: "{name} toegevoegd; er is een testmelding verstuurd. Is die aangekomen?",
      text: {
        no_sensors: "Er zijn nog geen sensoren. Voeg ze toe of laat ze zoeken.",
        no_sensor_groups: "Er zijn nog geen sensorgroepen. Zonder groep bewaakt een inbraaksensor niets. Vigil kan twee voorstellen: Buitenschil (deuren en ramen) en Binnen (beweging).",
        mode_unwatched: "In deze modus bewaakt geen enkele inbraaksensor: {modes}.",
        no_user_code: "Er is nog geen gebruiker met een code, dus niemand kan het alarm bedienen.",
        no_notification: "Er is nog geen meldingskanaal, dus je hoort niets als het alarm afgaat. Gebruik bijvoorbeeld de app op je telefoon.",
        no_siren: "Er is geen sirene. Het alarm werkt dan alleen met meldingen.",
        battery_missing: "{n} sensoren hebben geen batterijsensor, dus je hoort niet als de batterij leeg raakt: {names}.",
        tamper_unlinked: "{n} sensoren hebben een sabotagesensor op hetzelfde apparaat die nergens aan gekoppeld is: {names}.",
        panel_firmware: "De firmware van paneel {name} begrijpt profielversie {seen}, Vigil gebruikt versie {wanted}. Werk de firmware van het paneel bij.",
      },
    },
    heartbeat: { title: "Hartslag", off: "Uit. Vul bij Instellingen een hartslag-adres in om te beginnen.", lastOk: "Laatst gelukt", lastFail: "Laatst mislukt", never: "nog niet", every: "Elke {n} minuten", test: "Nu testen", ok: "De hartslag is aangekomen.", failed: "De hartslag is niet aangekomen ({reason}).", reason: { timeout: "geen antwoord binnen 10 seconden", connection: "geen verbinding", } , failing: "Mislukt: {reason}" },
    selftest: { title: "Zelftest", last: "Laatste stille controle", lastSiren: "Laatste sirenetest", next: "Volgende sirenetest", never: "nog niet", off: "Herinnering staat uit (Instellingen)", noSiren: "Er is geen sirene ingesteld.", overdue: "Achterstallig: de test had {days} dagen geleden moeten gebeuren.", test: "Sirene nu testen", started: "De sirene klinkt {seconds} seconden.", auto: "Vigil laat de sirene zelf klinken binnen de ingestelde uren.", problems: "Ontbrekend meldkanaal: {name}" },
    dash: { title: "Dashboard", text: "Een dashboard met de eigen entiteiten van dit alarm. Kopieer het en plak het in een nieuw dashboard (Instellingen > Dashboards > nieuw dashboard > ruwe configuratie-editor).", copy: "Kopieer dashboard" },
    log: { intro: "Alles wat Vigil als gebeurtenis meldt. Het logboek bewaart {days} dagen (zie Instellingen) en bevat geen codes. Tijden zijn in jouw tijdzone; in de downloads staan ze in UTC volgens RFC 3339.", empty: "Nog niets in het logboek.",
      cols: { time: "Tijd", event: "Gebeurtenis", item: "Onderdeel", who: "Gebruiker", via: "Via", result: "Resultaat", noCode: "onbekend (geen code)", installer: "installateurcode", auto: "automatisch" }, showing: "De nieuwste {n} van {total}", jsonl: "Download (JSON Lines)", csv: "Download (CSV)", refresh: "Vernieuwen" },
    summary: { always: "{cls}, altijd actief", instant: "direct", delayed: "vertraagd ({s} s)", follower: "volger", and: "en", watching: "{type}, bewaakt in {modes}", nowhere: "{type}, bewaakt in geen enkele modus" },
    whatsNew: "nieuw", batteryLow: "laag", batteryOk: "ok",
    copySuffix: " (kopie)",
    permBypass: { title: "Permanent omzeild", intro: "Deze sensoren staan omzeild en bewaken niet, ook niet na het uitschakelen. Herstel ze zodra ze gerepareerd zijn:", restore: "Herstellen", restored: "Hersteld" },
    memory: { title: "Laatste alarm", running: "Het alarm loopt nog.", endedBy: "Uitgeschakeld om {time} door {who}.", cancelled: "Geannuleerd als vals alarm.", cause: "Oorzaak", first: "Eerste sensor", path: "Route door het huis", pathIntro: "Elke sensor die openging vanaf het begin van het alarm tot het uitschakelen, in volgorde. Ook sensoren die in deze modus niet meetelden of omzeild waren staan erbij: samen laten ze zien waar iemand is geweest.", time: "Tijd", sensor: "Sensor", room: "Ruimte", counted: "Telde mee", notCounted: "Telde niet mee", times: "{n}× geopend", clear: "Alarmgeheugen wissen", cleared: "Alarmgeheugen gewist", noRoom: "geen ruimte ingesteld", empty: "Geen sensor geopend (alleen de eerste melding).", steps: "{n} stappen", more: "Alleen de eerste {n} stappen worden bewaard." },
    practice: { chip: "Oefenmodus", title: "Oefenen en testen", text: "Oefenmodus: het alarm werkt als altijd (aftellen, afgaan, de panelen tonen het) maar er klinkt geen sirene en er gaat geen melding uit. Alles staat in het logboek, gemarkeerd als oefening. Het stopt na 30 minuten, of zodra je uitschakelt.", start: "Start oefenmodus", stop: "Stop oefenmodus", left: "Nog {n} min.", needsOff: "Schakel het alarm eerst uit.",
      walk: "Looptest: loop met het alarm uit langs de deuren, ramen en bewegingsmelders; elke sensor die reageert wordt afgevinkt. Alleen inbraaksensoren doen mee (brand-, gas-, water- en sabotagesensoren staan altijd aan en hebben hun eigen test).", walkStart: "Start looptest", walkTitle: "Looptest", walkRunning: "Open elke deur of raam en loop langs elke bewegingsmelder. {n} van {total} gezien.", walkStop: "Stop de test", walkDone: "Klaar: {seen} van {total} gezien.", walkAgain: "Opnieuw", walkMissing: "Niet gezien", walkReason: { no_response: "reageerde niet", unavailable: "is niet beschikbaar" }, walkSeen: "Gezien", walkNone: "Alle sensoren hebben gereageerd.", walkLast: "Laatste looptest: {seen} van {total} gezien ({time}).", close: "Sluiten" },
    wizard: {
      title: "Vigil instellen", button: "Installatiewizard", step: "Stap {n} van {total}", back: "Terug", next: "Volgende", skip: "Overslaan", finish: "Klaar", stop: "Later verder", resume: "Ga verder met de wizard",
      cardTitle: "Vigil instellen", cardText: "Nog niet alles is ingesteld. De wizard loopt er stap voor stap doorheen; je kunt elke stap overslaan en later terugkomen.", start: "Start de wizard",
      done: "Gedaan", todo: "Nog te doen", optional: "Aanbevolen",
      welcome: { title: "Welkom bij Vigil", text: "In een paar stappen stel je het alarm in: welke standen je gebruikt, welke sensoren meedoen, wie een code krijgt en hoe je een melding krijgt. Er wordt pas iets opgeslagen als je dat in een stap bevestigt, en elke wijziging is terug te zetten via het tabblad Back-up." },
      modes: { title: "Welke standen gebruik je?", text: "Thuis (je bent er, de buitenschil is bewaakt), Weg (niemand thuis), Nacht (je slaapt), Vakantie (lang weg) en Aangepast (een stand voor jezelf, bijvoorbeeld alleen de garage). Kies alleen wat je echt gebruikt; de uitlooptijden kun je later onder Instellingen aanpassen.", save: "Opslaan", saved: "Standen opgeslagen.", none: "Kies minstens één stand." },
      sensors: { title: "Sensoren", text: "Vigil zoekt deur-, raam-, beweging-, rook-, gas- en watersensoren in Home Assistant. Je kiest welke je toevoegt.", have: "{n} sensoren ingesteld.", none: "Nog geen sensoren.", find: "Sensoren zoeken", fresh: "{n} nieuw gevonden." },
      user: { title: "Wie mag het alarm bedienen?", text: "Een gebruiker heeft een code. Je kunt een gebruiker aanmaken van een Home Assistant-persoon of er een met de hand toevoegen.", have: "{n} gebruiker(s) met een code.", none: "Nog geen gebruiker met een code.", fromPerson: "Maak gebruiker van {name}", add: "Gebruiker toevoegen" },
      notification: { title: "Waar wil je een melding krijgen?", text: "Bij een alarm of storing stuurt Vigil een bericht. Een telefoon met de Home Assistant-app is het makkelijkst.", have: "{n} meldingskanaal(en).", none: "Nog geen meldingskanaal.", phone: "Voeg {name} toe", add: "Meldingskanaal toevoegen", added: "{name} is toegevoegd; er is een testmelding gestuurd." },
      siren: { title: "Sirene", text: "Een sirene is niet verplicht, maar zonder sirene hoor je een alarm alleen via meldingen.", have: "{n} sirene(s).", none: "Nog geen sirene.", add: "Sirene toevoegen" },
      panel: { title: "Paneel aan de muur", text: "Een ESPHome-scherm of een tablet of telefoon kan het alarm bedienen. Dit is niet verplicht.", have: "{n} paneel/panelen.", none: "Nog geen paneel.", add: "Paneel koppelen" },
      test: { title: "Klaar voor gebruik?", text: "Dit is wat Vigil nu nog mist. Alles wat 'probleem' heet, houdt het alarm nog van beschermen.", allGood: "Alles is in orde.", testSiren: "Test de sirene", sirenStarted: "De sirene klinkt kort." },
      end: { title: "Klaar", text: "Vigil is ingesteld. Een proefrondje: zet het alarm aan, open een deur en kijk of je melding komt. Daarna kun je automatiseringen toevoegen met de meegeleverde blueprints (automatisch inschakelen als iedereen weg is, lichten laten knipperen bij een alarm, een bericht uitspreken). Je vindt ze in de handleiding onder Automatiseringen en blueprints." },
    },
    newSensors: { title: "Nieuwe sensoren gevonden", text: "Deze sensoren zijn in Home Assistant bijgekomen sinds Vigil voor het laatst keek. Er is niets toegevoegd.", review: "Bekijk en voeg toe", later: "Niet nu", badge: "{n} nieuw", dismissed: "Oké, Vigil meldt deze niet opnieuw. Je kunt ze altijd nog toevoegen via Sensoren zoeken.", onlyNew: "Alleen de nieuwe sensoren worden getoond.", showAll: "Toon alle sensoren", showNew: "Toon alleen nieuwe" },
    find: {
      button: "Sensoren zoeken", title: "Sensoren zoeken",
      intro: "Deze sensoren zijn gevonden in Home Assistant. Kies welke je wilt toevoegen. Er wordt niets opgeslagen voordat je op de knop onderaan drukt.",
      none: "Er zijn geen nieuwe sensoren gevonden. Deur-, raam-, beweging-, rook-, gas-, water- en sabotagesensoren van een geïntegreerd apparaat worden getoond.",
      noGroups: "Voor sommige inbraaksensoren is nog geen sensorgroep ingesteld. Zet bij een sensorgroep 'Voorstellen voor nieuwe sensoren' op deuren/ramen of beweging; dan kun je ze hier toevoegen.",
      cols: { name: "Naam", cls: "Klasse", entrance: "Ingang", groups: "Sensorgroepen", extra: "Erbij" },
      entranceHelp: "Een ingang geeft vertraging bij binnenkomst (type 'vertraagd').",
      inUse: "al in gebruik", needsGroup: "geen sensorgroep", battery: "batterij", tamper: "sabotage",
      all: "Alles selecteren", nothing: "Niets selecteren", add: "{n} toevoegen", adding: "Toevoegen…",
      copy: "Kopieer ontdekkingsgegevens", copyHelp: "Een anonieme lijst zonder namen of adressen, voor een melding of om een integratie te helpen testen.",
      createGroups: "Standaardgroepen maken", added: "{n} sensoren toegevoegd", failed: "{name}: {error}",
    },
    confirmDelete: "Weet je zeker dat je '{name}' wilt verwijderen?",
    saved: "Opgeslagen", deleted: "Verwijderd", testSent: "Test verstuurd", loading: "Laden…", loadFailed: "Vigil Alarm kon niet geladen worden. Is de integratie actief?",
    retry: "Opnieuw proberen",
    sections: {
      alarm: ["Modi en vertragingen", "Welke modi je gebruikt en hoe lang je hebt om te vertrekken, binnen te komen en hoe lang het alarm duurt."],
      chime: ["Deurbel", "Een kort geluid als een sensor met het vinkje Deurbel opengaat terwijl het alarm uit is."],
      codes: ["Codes", "Of een code nodig is om in te schakelen en hoe lang een code minstens moet zijn."],
      startup: ["Opstarten", "Na een herstart van Home Assistant wacht Vigil tot al je sensoren beschikbaar zijn (bijvoorbeeld MQTT of Zigbee die nog opstarten) voordat het een sensor als weggevallen meldt of er een alarm van maakt. Zijn ze na deze tijd nog weg, dan volgt de melding wel."],
      lock: ["Vergrendeling", "Wat er gebeurt na foute codes, per paneel: eerst een korte vergrendeling, dan langere, en daarna een permanente die alleen weggaat met Blokkade opheffen bij Panelen. Een goede code begint weer bij nul."],
      screen: ["Scherm van de panelen", "Wanneer het scherm van een ESPHome-paneel uitgaat. Het scherm gaat alleen uit als het alarm uit of volledig ingeschakeld is, nooit tijdens het aftellen om in of uit te schakelen."],
      battery: ["Batterijen", "Vanaf welk niveau een batterij als bijna leeg geldt."],
      log: ["Logboek", "Hoe lang Vigil de gebeurtenissen bewaart."],
      backup: ["Back-up", "Hoeveel versies van je configuratie Vigil bewaart (tabblad Back-up). Een lagere waarde gooit de oudste versies weg."],
      selftest: ["Zelftest", "Vigil herinnert je eraan de sirene te testen. Zet het interval op 0 om de herinnering uit te zetten."],
      heartbeat: ["Hartslag", "Vigil roept dit adres regelmatig aan, zodat een dienst buiten je huis meldt als Home Assistant of je internet uitvalt."],
    },
    reloadNote: "Opslaan laadt Vigil Alarm opnieuw (de alarmstatus blijft behouden).",
    alarm: "Alarm", problems: "Aandachtspunten", noProblems: "Geen problemen", sensorsNow: "Sensoren nu",
    coverage: "Wat bewaakt elke modus", coverageNothing: "geen sensorgroep: er wordt niets bewaakt", alwaysOn: "Altijd actief", sensorsCount: "{n} sensoren",
    state: { disarmed: "Uit", arming: "Wordt ingeschakeld", armed: "Ingeschakeld", pending: "Inlooptijd", triggered: "ALARM" },
    mode: { home: "Thuis", away: "Weg", night: "Nacht", vacation: "Vakantie", custom: "Aangepast" },
    zstatus: { closed: "Dicht", open: "Open", unavailable: "Onbereikbaar", bypassed: "Omzeild", bypassed_at_arm: "Omzeild bij inschakelen", waiting: "Wacht tot dicht" },
    problem: { battery_low: "batterij bijna leeg", unavailable: "niet bereikbaar", on_battery: "geen netstroom" },
    cols: {
      name: "Naam", entity: "Entiteit", cls: "Klasse", type: "Type", groups: "Sensorgroepen", rule: "Bevestigingsregel", status: "Status", battery: "Batterij",
      modes: "Actief in modi", sensors: "Sensoren", suggest: "Voorstel voor", condition: "Voorwaarde", escalate: "Onbevestigd melden",
      code: "Code", duress: "Dwangcode", tags: "Tags", bypass: "Omzeilen", tamper: "Sabotage omzeilen",
      service: "Dienst", categories: "Categorieën", delay: "Vertraging",
      device: "Apparaat", causes: "Bij", maxdur: "Max. duur",
      panelId: "Paneel-id", conn: "Verbinding", allowed: "Beperkingen",
    },
    panel: { tablet: "Account", noUser: "gebruiker niet gevonden", connected: "Verbonden", offline: "Niet bereikbaar", noConnection: "Geen verbinding", noCard: "Geen Vigil-kaart gezien", cardSeen: "Vigil-kaart actief", notFound: "Niet gevonden in ESPHome", unlocked: "Ontgrendeld", locked: "Vergrendeld voor {s} s", lockedPermanent: "Permanent vergrendeld", blocked: "Geblokkeerd", notWatched: "Niet bewaakt", unlock: "Ontgrendelen", unlockedDone: "Ontgrendeld voor {s} seconden.", clear: "Blokkade opheffen", cleared: "Blokkade opgeheven.", nothingLocked: "Dit paneel had geen blokkade.", all: "alle modi", noDisarm: "niet uitschakelen", noBypass: "niet omzeilen", noSilence: "niet dempen", hint: "Ontgrendelen en blokkade opheffen kunnen alleen hier, niet als Home Assistant-actie.", refused: "Dit kan niet." },
    yes: "ja", no: "nee", none: "—", immediately: "direct",
    condition: "{n} binnen {s} s",
    fields: {
      name: "Naam", entity_id: "Entiteit (binary sensor)", cls: "Klasse", type: "Type", sensor_groups: "Sensorgroepen", at_arm_open: "Als open bij einde uitlooptijd",
      entry_delay: "Inlooptijd (leeg = standaard)", gas_type: "Soort gas", on_unavailable: "Als de sensor onbereikbaar wordt", battery_entity: "Batterijsensor", tamper_entity: "Sabotage-entiteit (optioneel)", chime: "Deurbel: laat een geluid horen als deze sensor opengaat terwijl het alarm uit is", permanent_bypass: "Omzeiling blijft staan na uitschakelen (permanent)", duress_code: "Dwangcode (optioneel)",
      "sensor_group.modes": "Actief in modi", suggest_for: "Voorstellen voor nieuwe sensoren",
      sensors: "Sensoren", required: "Benodigde sensoren", window: "Tijdvenster", escalate: "Melden als onbevestigd",
      code: "Code", tags: "Tags (komma-gescheiden)", allowed_modes: "Mag bedienen in modi (leeg = alle)", may_bypass: "Mag sensoren omzeilen", may_bypass_tamper: "Mag sabotage omzeilen",
      service: "Notify-dienst", categories: "Soorten meldingen", delay: "Vertraging", priority: "Hoge prioriteit",
      control: "Sirene (siren, schakelaar of lamp)", causes: "Laat klinken bij", max_duration: "Maximale duur (0 = tot uitschakelen)", repeat_every: "Herhaal elke (0 = niet)",
      light: "Flitslicht", tone_entity: "Toonkeuze-entiteit", volume_entity: "Volume-entiteit", power_entity: "Voedingsmodus-entiteit", power_battery_value: "Waarde bij batterijvoeding",
      tone: "Toon", volume: "Volume", preset: "Voorinstelling",
      device: "Soort apparaat", panel_id: "Naam van het ESPHome-apparaat (paneel-id)", ha_user: "Home Assistant-account (tablet of telefoon)", language: "Taal", can_disarm: "Mag uitschakelen (met code)", can_bypass: "Mag sensoren omzeilen (met code)", can_silence: "Mag dempen en bevestigen", sensor_list: "Sensorlijst tonen", unlock_seconds: "Ontgrendeld blijft (seconden)", watch: "Bewaken of dit paneel bereikbaar is (melding als het wegvalt)", blocked: "Paneel geblokkeerd", "panel.code": "Installateurscode van dit paneel (leeg = geen)", "panel.allowed_modes": "Mag inschakelen in modi (leeg = alle)",
      "s.modes": "Beschikbare modi", exit_delay_home: "Uitlooptijd thuis", exit_delay_away: "Uitlooptijd weg", exit_delay_night: "Uitlooptijd nacht", exit_delay_vacation: "Uitlooptijd vakantie", exit_delay_custom: "Uitlooptijd aangepast",
      default_entry_delay: "Standaard inlooptijd", trigger_time: "Alarmduur (0 = tot uitschakelen)", abort_seconds: "Annuleervenster na het afgaan van de sirene (seconden, 0 = uit)", chime_entity: "Deurbel: wat laat het geluid horen", chime_seconds: "Deurbel klinkt (seconden)", battery_threshold: "Batterijgrens", backup_versions: "Aantal bewaarde versies", code_arm_required: "Code nodig om in te schakelen", startup_wait_seconds: "Maximaal wachten op sensoren na een herstart (seconden)", lock_tries_1: "Foute codes voor de eerste vergrendeling", lock_wait_1: "Eerste vergrendeling duurt (minuten)", lock_tries_2: "Daarna foute codes voor de tweede vergrendeling", lock_wait_2: "Tweede vergrendeling duurt (minuten)", lock_tries_3: "Daarna foute codes voor de derde vergrendeling", lock_wait_3: "Derde vergrendeling duurt (minuten)", lock_tries_4: "Daarna foute codes voor de permanente vergrendeling", screen_off_seconds: "Scherm uit na (seconden zonder aanraking)", screen_off_on_alarm: "Scherm ook uit laten gaan tijdens een alarm", min_code_length: "Minimale codelengte (cijfers/tekens)", log_retention_days: "Logboek bewaren (dagen)", selftest_interval_days: "Herinnering sirenetest (dagen, 0 = uit)", selftest_siren_seconds: "Sirene klinkt bij test (seconden)", selftest_auto: "Sirene zelf laten klinken voor de test", selftest_window_start: "Test niet voor (uur)", selftest_window_end: "Test niet na (uur)", heartbeat_url: "Hartslag-adres (leeg = uit)", heartbeat_interval_minutes: "Minuten tussen hartslagen",
    },
    helpMore: {
      at_arm_open: "Wat er gebeurt als deze sensor nog open staat wanneer de uitlooptijd voorbij is:\n• Omzeilen met melding (standaard): het alarm gaat aan zonder deze sensor en je krijgt een melding. Zodra de sensor dicht gaat, bewaakt hij weer.\n• Wachten tot dicht: het alarm gaat aan en deze sensor wordt genegeerd tot hij één keer dicht is geweest, zonder melding. Daarna bewaakt hij weer.\n• Inschakelen weigeren: het alarm gaat niet aan en je ziet welke sensor open staat. Sluit hem eerst.\n• Inlooptijd starten: het alarm gaat aan en de open sensor telt meteen als geactiveerd. Een directe sensor geeft alarm, bij een vertraagde sensor start de inlooptijd.",
      tamper_entity: "Heeft dit apparaat ook een sabotagecontact (tamper)? Kies dat hier. Vigil maakt er vanzelf een sabotagesensor bij: altijd actief, met een eigen omzeilschakelaar. Je hoeft het niet apart toe te voegen.",
    },
    moreInfo: "Meer uitleg",
    help: {
      duress_code: "Een tweede code voor als iemand je dwingt het alarm uit te zetten. Hij zet het alarm gewoon uit en er is niets aan te zien: de sirene blijft stil. Ondertussen gaat er een stille melding naar de kanalen met de soort melding Dwang. Moet anders zijn dan alle andere codes.",
      permanent_bypass: "Omzeil je deze sensor met de hand, dan blijft hij omzeild ook nadat het alarm is uitgeschakeld, tot je hem zelf herstelt. Handig voor een sensor die al een tijd stuk is. Zonder dit vinkje vervalt de omzeiling bij het uitschakelen. Brand- en gassensoren kunnen nooit worden omzeild.",
      chime: "Gaat de sensor open terwijl het alarm uit staat, dan klinkt er kort een geluid via wat je bij de instellingen hebt gekozen. Geen alarm, geen melding, niets in het logboek. Is het alarm aan, dan gebeurt er niets.",
      abort_seconds: "Wie binnen zoveel seconden nadat de sirene is afgegaan een geldige code invoert, heeft een vals alarm veroorzaakt: de sirene stopt en er gaat een melding 'geannuleerd' uit. 0 zet dit uit. Geldt niet voor brand, gas en sabotage.",
      chime_entity: "Een sirene, schakelaar, lamp, knop of script dat een geluid laat horen. Leeg laten kan ook: de gebeurtenis Deurbel staat dan nog wel op de gebeurtenis-entiteit, voor een eigen automatisering (bijvoorbeeld een bericht op een speaker).",
      chime_seconds: "Hoe lang een sirene, schakelaar of lamp aan blijft. Bij een knop of script heeft dit geen effect.",
      may_bypass: "Zonder dit recht kan deze gebruiker een sensor niet omzeilen en ook niet terugzetten, ook niet met een goede code. Een beheerder in Home Assistant mag altijd.",
      screen_off_seconds: "Geldt voor alle ESPHome-panelen. Was er een half ingetikte code of een open lijst, dan gaat het paneel eerst na deze tijd terug naar het hoofdscherm en gaat het scherm pas na nog eens deze tijd uit.",
      screen_off_on_alarm: "Uit: het scherm blijft aan zolang er een alarm loopt, zodat het ALARM en de oorzaak zichtbaar blijven. Aan: het scherm gaat dan ook uit. Tijdens het aftellen om in te schakelen of binnen te komen gaat het scherm nooit uit.",
      entity_id: "Een binary sensor: aan betekent open of alarm.",
      tamper_entity: "Optioneel: het sabotagecontact van dit apparaat.",
      at_arm_open: "Wat er gebeurt met deze sensor als hij nog open staat bij het inschakelen.",
      type: "Direct: meteen alarm. Vertraagd: eerst inlooptijd. Volger: alleen alarm als er eerst een vertraagde sensor open was.",
      sensor_groups: "Een sensor kan in meerdere groepen zitten. Hij bewaakt in elke modus waarin één van zijn groepen actief is.",
      suggest_for: "Optioneel. Een nieuwe sensor van dit soort (deurcontact of beweging) wordt automatisch in deze groep gezet.",
      sensors: "Alleen directe inbraaksensoren.",
      code: "Leeg laten = ongewijzigd.",
      device: "ESPHome-paneel: een scherm met eigen firmware, herkend aan de naam van het ESPHome-apparaat. Tablet of telefoon: een apparaat met de Home Assistant-app of -browser, herkend aan het account waarmee het is ingelogd.",
      ha_user: "Voor een tablet of telefoon: het account waarmee het apparaat is ingelogd. Vigil herkent het apparaat aan dat account, niet aan een tekst, dus dat kan niet worden nagemaakt. Een beheerder mag ook, maar let op: de instellingen van dit paneel gelden dan voor alles wat dat account doet, op elk apparaat waar het is ingelogd, en Vigil geeft het account hier geen beheerdersrechten (een code is altijd nodig). Beter is een tweede, gewoon account voor dagelijks gebruik.",
      removeCode: "Code verwijderen", removeDuress: "Dwangcode verwijderen",
      tags: "Tags hebben geen functie: bedien het alarm met een code.",
      categories: "Kies welke berichten dit kanaal krijgt.",
      service: "Een notify-dienst (zoals mobile_app_telefoon of een groep uit YAML) of een notify-entiteit (zoals notify.gezin, een notify-groep die je als helper hebt gemaakt). Een notify-entiteit krijgt alleen een titel en een bericht: de kritieke melding van Hoge prioriteit werkt daar niet mee en de knop op het testbericht van de zelfcontrole ook niet. Wil je dat voor een telefoon, kies dan zijn eigen mobile_app_…-dienst.",
      priority: "Alleen voor telefoons met de Home Assistant-app (een mobile_app_…-dienst): een alarm wordt dan een kritieke melding op iOS en een melding met hoge prioriteit op Android. Bij een notify-entiteit of een andere dienst doet dit niets.",
      delay: "Alleen voor alarmen: eerst wachten, bijvoorbeeld om alleen na een tijd een tweede apparaat te melden.",
      profiles: "Toon en volume per oorzaak (optioneel)",
      preset: "Vult toon, volume en duur in voor een bekende sirene. Kies eerst bij \"Sirene\" de aan/uit-entiteit, dan zoekt Vigil de andere entiteiten van hetzelfde apparaat erbij. Alles blijft aanpasbaar.",
      presetFound: "Gevonden bij dit apparaat:", presetNoneFound: "Geen andere entiteiten gevonden bij dit apparaat; kies ze zelf.", presetNoControl: "Waarden ingevuld. Kies de sirene-entiteit en kies de voorinstelling opnieuw om de andere entiteiten te laten zoeken.",
      power_battery_value: "De waarde van de voedingsmodus als de sirene op batterij draait.",
    },
    opt: {
      preset: { "": "—", sonoff_snzb_09p_z2m: "Sonoff SNZB-09P (Zigbee2MQTT)" },
      cls: { intrusion: "Inbraak", fire: "Brand", gas: "Gas", tamper: "Sabotage", water: "Water", alarm24: "24 uur hoorbaar", silent24: "24 uur stil" },
      type: { instant: "Direct", delayed: "Vertraagd (inlooptijd)", follower: "Volger" },
      at_arm_open: { bypass: "Omzeilen met melding", wait_clear: "Wachten tot dicht", refuse: "Inschakelen weigeren", pending: "Inlooptijd starten" },
      gas_type: { co: "Koolmonoxide", natural_gas: "Aardgas", lpg: "LPG", other: "Anders" },
      on_unavailable: { default: "Standaard van de klasse", block: "Inschakelen blokkeren", notify: "Alleen melden", trigger: "Alarm geven", bypass: "Toch inschakelen (omzeilen)" },
      categories: { alarm: "Alarm", pending: "Inlooptijd", arming: "In- en uitschakelen", fault: "Storingen en meldingen", technical: "Technische alarmen (water)", duress: "Dwang (stil alarm)" },
      causes: { intrusion: "Inbraak", fire: "Brand", gas: "Gas", tamper: "Sabotage", fault: "Sensorstoring" },
      cause: { intrusion: "Inbraak", fire: "Brand", gas: "Gas", tamper: "Sabotage", alarm24: "24-uursalarm" },
      mode: { home: "Thuis", away: "Weg", night: "Nacht", vacation: "Vakantie", custom: "Aangepast" },
      suggest_for: { "": "Geen", contacts: "Deuren en ramen (contacten)", motion: "Beweging" },
      language: { nl: "Nederlands", en: "English", de: "Deutsch", fr: "Français", it: "Italiano", es: "Español" },
      device: { esphome: "ESPHome-paneel (zelfbouwscherm)", account: "Tablet of telefoon met Home Assistant" },
      sensor_list: { always: "Altijd tonen", code: "Pas na ontgrendelen", never: "Nooit tonen" },
    },
    why: {
      title: "Waarom kan ik niet inschakelen?", intro: "Dit houdt het inschakelen nu tegen:", modes: "bij {modes}", show: "Toon", bypass: "Omzeilen", bypassed: "Omzeild",
      neverBypass: "Brand- en gassensoren kun je niet omzeilen: eerst de oorzaak weghalen.",
      reason: { alarm_condition: "staat open (een alarmsituatie)", sensor_unavailable: "reageert niet (en is ingesteld om het inschakelen tegen te houden)", sensor_open: "staat open en moet dicht zijn om in te schakelen", not_disarmed: "het alarm staat al aan" },
      hint: "Op het paneel en in de Vigil-kaart kun je met de knop Omzeilen en inschakelen in één keer omzeilen en inschakelen, als je daar het recht voor hebt.",
    },
    backup: {
      intro: "Bij elke wijziging bewaart Vigil de configuratie van vóór die wijziging (de laatste 10 versies). Je kunt zo'n versie terugzetten; het terugzetten is zelf ook een wijziging en dus weer ongedaan te maken. Alleen de instellingen worden bewaard, niet de toestand van het alarm (ingeschakeld, omzeild).",
      list: "Bewaarde versies", none: "Nog geen versies. Ze komen zodra je iets wijzigt.", restore: "Terugzetten",
      reason: { edit: "Wijziging", restore: "Teruggezet", import: "Import", external: "Gewijzigd buiten het paneel", upgrade: "Update van Vigil" },
      colTime: "Tijdstip", colReason: "Reden", colVigil: "Vigil-versie", colChange: "Wijziging",
      view: "Bekijk", viewTitle: "Wijziging van {time}", viewText: "Deze versie bewaart de configuratie van vóór deze wijziging. De wijziging zelf was:", format: "opslagversie {v}",
      notRestorable: "Niet terug te zetten: gemaakt door een andere opslagversie ({v}, nu {now}). Wel te bekijken.", settingsList: "Instellingen: {names}",
      restoreTitle: "Deze versie terugzetten?", restoreText: "Terugzetten verandert dit ten opzichte van nu:", nothing: "Geen verschil met nu.", restored: "Teruggezet",
      fileTitle: "Exporteren en importeren", export: "Configuratie exporteren", import: "Configuratie importeren…",
      exportNote: "Het bestand bevat geen codes, wel de versleutelde codes (hashes), het heartbeat-adres en de namen van je meldingsdiensten. Bewaar het veilig.",
      importNote: "Importeren vervangt de hele configuratie. De huidige blijft als versie bewaard, dus een import is terug te zetten.",
      importTitle: "Dit bestand importeren?", importText: "Importeren verandert dit ten opzichte van nu:", imported: "Geïmporteerd", readFailed: "Dit bestand kan niet gelezen worden.",
      added: "toegevoegd", removed: "verwijderd", changed: "gewijzigd", settings: "Instellingen gewijzigd: {n}", undo: "Ongedaan maken", apply: "Doorvoeren",
    },
    errors: {
      backup_invalid: "Dit bestand of deze versie bevat geen bruikbare configuratie.", backup_unknown: "Deze versie bestaat niet meer.", import_not_vigil: "Dit is geen exportbestand van Vigil Alarm.", import_format_version: "Dit bestand heeft een onbekend formaat.", import_entry_version: "Dit bestand hoort bij een andere opslagversie ({found}, nodig: {expected}). Importeer het in dezelfde versie van Vigil als waarin het is gemaakt.",
      name_required: "Geef een naam op.", name_in_use: "Deze naam bestaat al.", required: "Verplicht.",
      invalid_config: "Ongeldig: {error}", sensor_not_instant: "Alleen directe sensoren kunnen in een bevestigingsregel. Aanpassen: {sensors}",
      entity_in_use: "Deze entiteit is al een sensor.", tamper_same_entity: "De sabotage-entiteit moet een andere zijn dan de sensor zelf.", tamper_entity_in_use: "Deze entiteit is al een sensor.",
      no_sensor_group: "Kies minstens één sensorgroep.", unknown_sensor_group: "Onbekende sensorgroep.",
      unknown_mode: "Onbekende modus.", unknown_suggestion: "Onbekende keuze.",
      backup_versions_range: "Kies een aantal van {min} tot {max}.", code_in_use: "Deze code is al in gebruik.", code_too_short: "De code moet minstens {min} tekens hebben (instelbaar bij Instellingen).", code_length_range: "Kies een waarde van {min} tot {max}.", screen_off_range: "Kies een aantal seconden van {min} tot {max}.", startup_wait_range: "Kies een aantal seconden van {min} tot {max}.", lock_tries_range: "Kies een aantal keren van {min} tot {max}.", lock_wait_range: "Kies een aantal minuten van {min} tot {max}.", log_retention_range: "Kies een aantal dagen van {min} tot {max}.", selftest_range: "Kies een waarde van {min} tot {max}.", selftest_window: "Het laatste uur moet na het vroegste uur liggen.", heartbeat_url_invalid: "Dit is geen webadres. Het moet beginnen met http:// of https://.", heartbeat_range: "Kies een aantal minuten van {min} tot {max}.", tag_in_use: "Deze tag is al in gebruik.", no_credential: "Geef een code of minstens één tag op.", duress_needs_code: "Een dwangcode hoort bij een gewone code: geef eerst een code op.", duress_no_channel: "Er is geen meldingskanaal met de soort melding Dwang. Zonder dat komt een stil alarm bij niemand aan. Voeg dat eerst toe.", seconds_range: "Kies een aantal seconden van {min} tot {max}.", chime_entity_domain: "Kies een sirene, schakelaar, lamp, knop of script.",
      service_not_found: "Deze notify-dienst bestaat niet (meer).", no_categories: "Kies minstens één soort melding.",
      no_causes: "Kies minstens één oorzaak.", tone_without_entity: "Een toon kan alleen met een toonkeuze-entiteit.", volume_without_entity: "Een volume kan alleen met een volume-entiteit.",
      sensor_in_rule: "Deze sensor zit nog in bevestigingsregel: {rules}. Haal hem daar eerst uit.",
      sensor_group_in_use: "Deze sensorgroep wordt nog gebruikt door: {sensors}. Haal de groep eerst bij die sensoren weg.",
      no_modes: "Kies minstens één modus.", unknown_kind: "Onbekend onderdeel.",
      panel_id_invalid: "Gebruik kleine letters, cijfers, - en _ (zoals de apparaatnaam in ESPHome).", panel_id_in_use: "Dit paneel-id is al geregistreerd.", unlock_range: "Kies een waarde van {low} tot {high}.", unknown_choice: "Onbekende keuze.", ha_user_unknown: "Deze gebruiker bestaat niet of is niet actief.",ha_user_in_use: "Deze gebruiker is al aan een ander paneel gekoppeld.",
      generic: "Er ging iets mis.",
    },
  },
  en: {
    title: "Vigil Alarm",
    tamperShort: "tamper",
    about: {
      details: "Details", aboutIntro: "A modular alarm system for Home Assistant.",
      version: "Version", license: "License", author: "Author", links: "Links",
      manual: "User guide", manualOther: "User guide (Nederlands)", repository: "GitHub project", releases: "Releases on GitHub",
      issues: "Report a problem or share an idea", panelDocs: "Touch panel (ESPHome)", licenseText: "License text",
      notes: "Release notes", notesOnlyEnglish: "", noNotes: "No release notes found.",
      system: "System", haVersion: "Home Assistant", python: "Python", alarmState: "Alarm state", items: "Items",
      copyInfo: "Copy details for a report", copied: "Copied", copyFailed: "Copying failed",
      disclaimer: "Vigil Alarm is not a certified alarm system. Test it regularly and do not rely on it as your only protection.",
      unreleased: "Not released yet", firstRelease: "first release",
    },
    tabs: { overview: "Overview", sensor: "Sensors", sensor_group: "Sensor groups", rule: "Confirmation rules", user: "Users", notification: "Notifications", siren: "Sirens", log: "Log", settings: "Settings", backup: "Backup", about: "About", panel: "Panels" },
    add: { sensor: "Add sensor", sensor_group: "Add sensor group", rule: "Add confirmation rule", user: "Add user", notification: "Add notification", siren: "Add siren", panel: "Add panel" },
    edit: { sensor: "Edit sensor", sensor_group: "Edit sensor group", rule: "Edit confirmation rule", user: "Edit user", notification: "Edit notification", siren: "Edit siren", panel: "Edit panel" },
    intro: {
      sensor: "One detector, such as a door contact, PIR or smoke detector. For an intrusion sensor you choose which sensor groups it is in. Fire, gas, water and tamper sensors always watch and need no sensor group. So do 24 hours, audible (a panic button, a shed door: an alarm with siren, also while the alarm is off) and 24 hours, silent (a freezer or a leak detector: only a message and a line in the log).",
      sensor_group: "A sensor group decides in which modes the sensors in it are watching. For example: Perimeter (doors and windows) for Home, Away and Night, and Interior (motion) for Away only.",
      rule: "An alarm follows only when the given number of different sensors trigger within the time window. Handy against a false alarm from a single PIR.",
      user: "People who can operate the alarm with a code. The code says who operates; which devices may operate is set under Panels.",
      notification: "Who gets messages and when. Each notification is one notify service.",
      siren: "Optional. Without a siren the alarm works with notifications.",
      panel: "A device on the wall: an ESPHome panel, or a tablet or phone with its own Home Assistant account Vigil decides what each panel may do and which data it gets; the panel itself decides nothing. The panel id is the name of the ESPHome device. As soon as one account is linked, other ordinary accounts can no longer operate the alarm.",
    },
    empty: {
      sensor: "No sensors yet. Add a sensor group first if there is none, then your sensors.",
      sensor_group: "No sensor groups yet. A sensor group decides in which modes sensors are watching.",
      rule: "No confirmation rules yet. Optional: an alarm only after several sensors.",
      user: "No users yet. Without a user no code is needed to operate the alarm.",
      notification: "No notifications yet. Add a notify service to receive messages.",
      siren: "No siren yet. This is optional; without a siren the alarm works with notifications.",
      panel: "No panels yet. Without a registered panel an ESPHome panel gets no profile and operates nothing.",
    },
    save: "Save", cancel: "Cancel", del: "Delete", dup: "Copy", editBtn: "Edit", testBtn: "Test", close: "Close",
    ready: {
      title: "Ready for use?", allGood: "Everything is set up. Still test the alarm regularly.", problem: "Fix first", advice: "Advice", go: "Go there",
      createGroups: "Create default groups", groupsMade: "Sensor groups created",
      addPhone: "Add phone: {name}", phoneAdded: "{name} added; a test notification was sent. Did it arrive?",
      text: {
        no_sensors: "There are no sensors yet. Add them or let Vigil find them.",
        no_sensor_groups: "There are no sensor groups yet. Without a group an intrusion sensor watches nothing. Vigil can propose two: Perimeter (doors and windows) and Interior (motion).",
        mode_unwatched: "No intrusion sensor is watching in this mode: {modes}.",
        no_user_code: "There is no user with a code yet, so nobody can operate the alarm.",
        no_notification: "There is no notification channel yet, so you will not hear anything when the alarm goes off. Use the app on your phone, for example.",
        no_siren: "There is no siren. The alarm then works with notifications only.",
        battery_missing: "{n} sensors have no battery sensor, so you will not hear when a battery runs low: {names}.",
        tamper_unlinked: "{n} sensors have a tamper contact on the same device that is not connected to anything: {names}.",
        panel_firmware: "The firmware of panel {name} understands profile version {seen}, Vigil uses version {wanted}. Update the firmware of the panel.",
      },
    },
    heartbeat: { title: "Heartbeat", off: "Off. Enter a heartbeat address under Settings to start.", lastOk: "Last succeeded", lastFail: "Last failed", never: "not yet", every: "Every {n} minutes", test: "Test now", ok: "The heartbeat arrived.", failed: "The heartbeat did not arrive ({reason}).", reason: { timeout: "no answer within 10 seconds", connection: "no connection" }, failing: "Failing: {reason}" },
    selftest: { title: "Self-test", last: "Last quiet check", lastSiren: "Last siren test", next: "Next siren test", never: "not yet", off: "Reminder is off (Settings)", noSiren: "No siren is set up.", overdue: "Overdue: the test was due {days} days ago.", test: "Test siren now", started: "The siren sounds for {seconds} seconds.", auto: "Vigil sounds the siren by itself within the set hours.", problems: "Missing notification channel: {name}" },
    dash: { title: "Dashboard", text: "A dashboard with this alarm's own entities. Copy it and paste it into a new dashboard (Settings > Dashboards > new dashboard > raw configuration editor).", copy: "Copy dashboard" },
    log: { intro: "Everything Vigil reports as an event. The log keeps {days} days (see Settings) and holds no codes. Times are in your time zone; in the downloads they are in UTC as RFC 3339.", empty: "Nothing in the log yet.",
      cols: { time: "Time", event: "Event", item: "Item", who: "User", via: "Via", result: "Result", noCode: "unknown (no code)", installer: "installer code", auto: "automatic" }, showing: "The newest {n} of {total}", jsonl: "Download (JSON Lines)", csv: "Download (CSV)", refresh: "Refresh" },
    summary: { always: "{cls}, always on", instant: "instant", delayed: "delayed ({s} s)", follower: "follower", and: "and", watching: "{type}, watching in {modes}", nowhere: "{type}, not watching in any mode" },
    whatsNew: "new", batteryLow: "low", batteryOk: "ok",
    copySuffix: " (copy)",
    permBypass: { title: "Permanently bypassed", intro: "These sensors are bypassed and not watching, also after disarming. Restore them as soon as they are repaired:", restore: "Restore", restored: "Restored" },
    memory: { title: "Last alarm", running: "The alarm is still going.", endedBy: "Disarmed at {time} by {who}.", cancelled: "Cancelled as a false alarm.", cause: "Cause", first: "First sensor", path: "Path through the house", pathIntro: "Every sensor that opened from the start of the alarm until it was disarmed, in order. Sensors that did not count in this mode, or were bypassed, are included: together they show where someone has been.", time: "Time", sensor: "Sensor", room: "Room", counted: "Counted", notCounted: "Did not count", times: "opened {n}×", clear: "Clear alarm memory", cleared: "Alarm memory cleared", noRoom: "no room set", empty: "No sensor opened (only the first report).", steps: "{n} steps", more: "Only the first {n} steps are kept." },
    practice: { chip: "Practice mode", title: "Practice and test", text: "Practice mode: the alarm works as always (it counts down, it triggers, the panels show it) but no siren sounds and no message goes out. Everything is in the log, marked as practice. It stops after 30 minutes, or as soon as you disarm.", start: "Start practice mode", stop: "Stop practice mode", left: "{n} min left.", needsOff: "Switch the alarm off first.",
      walk: "Walk test: with the alarm off, walk along the doors, windows and motion sensors; every sensor that reacts is ticked off. Only intrusion sensors take part (fire, gas, water and tamper sensors are always on and have their own test).", walkStart: "Start walk test", walkTitle: "Walk test", walkRunning: "Open each door or window and walk past each motion sensor. {n} of {total} seen.", walkStop: "Stop the test", walkDone: "Done: {seen} of {total} seen.", walkAgain: "Again", walkMissing: "Not seen", walkReason: { no_response: "did not react", unavailable: "is unavailable" }, walkSeen: "Seen", walkNone: "All sensors reacted.", walkLast: "Last walk test: {seen} of {total} seen ({time}).", close: "Close" },
    wizard: {
      title: "Set up Vigil", button: "Setup wizard", step: "Step {n} of {total}", back: "Back", next: "Next", skip: "Skip", finish: "Done", stop: "Continue later", resume: "Continue the wizard",
      cardTitle: "Set up Vigil", cardText: "Not everything is set up yet. The wizard goes through it step by step; you can skip any step and come back later.", start: "Start the wizard",
      done: "Done", todo: "To do", optional: "Recommended",
      welcome: { title: "Welcome to Vigil", text: "In a few steps you set up the alarm: which modes you use, which sensors take part, who gets a code and how you get a message. Nothing is saved until you confirm it in a step, and every change can be put back from the Backup tab." },
      modes: { title: "Which modes do you use?", text: "Home (you are in, the outer shell is watched), Away (nobody home), Night (you are asleep), Vacation (away for long) and Custom (a mode of your own, for example only the garage). Choose only what you really use; the exit delays can be changed later under Settings.", save: "Save", saved: "Modes saved.", none: "Choose at least one mode." },
      sensors: { title: "Sensors", text: "Vigil looks for door, window, motion, smoke, gas and water sensors in Home Assistant. You choose which ones to add.", have: "{n} sensors set up.", none: "No sensors yet.", find: "Find sensors", fresh: "{n} newly found." },
      user: { title: "Who may operate the alarm?", text: "A user has a code. You can create a user from a Home Assistant person or add one by hand.", have: "{n} user(s) with a code.", none: "No user with a code yet.", fromPerson: "Make a user of {name}", add: "Add a user" },
      notification: { title: "Where do you want a message?", text: "On an alarm or a fault Vigil sends a message. A phone with the Home Assistant app is the easiest.", have: "{n} notification channel(s).", none: "No notification channel yet.", phone: "Add {name}", add: "Add a notification channel", added: "{name} was added; a test message was sent." },
      siren: { title: "Siren", text: "A siren is not required, but without one you only hear an alarm through messages.", have: "{n} siren(s).", none: "No siren yet.", add: "Add a siren" },
      panel: { title: "Panel on the wall", text: "An ESPHome screen or a tablet or phone can operate the alarm. This is optional.", have: "{n} panel(s).", none: "No panel yet.", add: "Link a panel" },
      test: { title: "Ready for use?", text: "This is what Vigil still misses. Anything marked 'problem' still keeps the alarm from protecting.", allGood: "Everything is in order.", testSiren: "Test the siren", sirenStarted: "The siren sounds briefly." },
      end: { title: "Done", text: "Vigil is set up. A trial run: arm the alarm, open a door and see whether your message arrives. After that you can add automations with the included blueprints (arm automatically when everyone leaves, flash lights on an alarm, speak a message). You find them in the guide under Automations and blueprints." },
    },
    newSensors: { title: "New sensors found", text: "These sensors have appeared in Home Assistant since Vigil last looked. Nothing has been added.", review: "Review and add", later: "Not now", badge: "{n} new", dismissed: "OK, Vigil will not announce these again. You can still add them with Find sensors.", onlyNew: "Only the new sensors are shown.", showAll: "Show all sensors", showNew: "Show only new" },
    find: {
      button: "Find sensors", title: "Find sensors",
      intro: "These sensors were found in Home Assistant. Choose which ones to add. Nothing is saved until you press the button at the bottom.",
      none: "No new sensors were found. Door, window, motion, smoke, gas, water and tamper sensors of an integrated device are shown.",
      noGroups: "Some intrusion sensors have no sensor group yet. Set 'Suggest for new sensors' on a sensor group to contacts or motion; then you can add them here.",
      cols: { name: "Name", cls: "Class", entrance: "Entrance", groups: "Sensor groups", extra: "Included" },
      entranceHelp: "An entrance gets an entry delay (type 'delayed').",
      inUse: "already in use", needsGroup: "no sensor group", battery: "battery", tamper: "tamper",
      all: "Select all", nothing: "Select none", add: "Add {n}", adding: "Adding…",
      copy: "Copy discovery data", copyHelp: "An anonymous list without names or addresses, for a report or to help test an integration.",
      createGroups: "Create default groups", added: "{n} sensors added", failed: "{name}: {error}",
    },
    confirmDelete: "Are you sure you want to delete '{name}'?",
    saved: "Saved", deleted: "Deleted", testSent: "Test sent", loading: "Loading…", loadFailed: "Vigil Alarm could not be loaded. Is the integration running?",
    retry: "Try again",
    sections: {
      alarm: ["Modes and delays", "Which modes you use, and how long you have to leave, to come in, and how long the alarm lasts."],
      chime: ["Chime", "A short sound when a sensor with the Chime box ticked opens while the alarm is off."],
      codes: ["Codes", "Whether a code is needed to arm and how long a code must be at least."],
      startup: ["Start-up", "After Home Assistant restarts, Vigil waits until all your sensors are available (for example MQTT or Zigbee still starting) before it reports a sensor as lost or raises an alarm for it. If they are still gone after this time, the report follows."],
      lock: ["Locking", "What happens after wrong codes, per panel: first a short lock, then longer ones, then a permanent lock that only goes away with Clear lock under Panels. A right code starts again from zero."],
      screen: ["Panel screen", "When the screen of an ESPHome panel goes dark. It only goes dark while the alarm is off or fully armed, never during the countdown to arm or to disarm."],
      battery: ["Batteries", "From which level a battery counts as low."],
      log: ["Event log", "How long Vigil keeps the events."],
      backup: ["Backup", "How many versions of your configuration Vigil keeps (Backup tab). A lower value discards the oldest versions."],
      selftest: ["Self-test", "Vigil reminds you to test the siren. Set the interval to 0 to turn the reminder off."],
      heartbeat: ["Heartbeat", "Vigil calls this address regularly, so a service outside your house reports when Home Assistant or your internet stops."],
    },
    reloadNote: "Saving reloads Vigil Alarm (the alarm state is kept).",
    alarm: "Alarm", problems: "Attention", noProblems: "No problems", sensorsNow: "Sensors now",
    coverage: "What each mode watches", coverageNothing: "no sensor group: nothing is watched", alwaysOn: "Always on", sensorsCount: "{n} sensors",
    state: { disarmed: "Off", arming: "Arming", armed: "Armed", pending: "Entry delay", triggered: "ALARM" },
    mode: { home: "Home", away: "Away", night: "Night", vacation: "Vacation", custom: "Custom" },
    zstatus: { closed: "Closed", open: "Open", unavailable: "Unreachable", bypassed: "Bypassed", bypassed_at_arm: "Bypassed at arming", waiting: "Waiting to close" },
    problem: { battery_low: "battery low", unavailable: "unreachable", on_battery: "no mains power" },
    cols: {
      name: "Name", entity: "Entity", cls: "Class", type: "Type", groups: "Sensor groups", rule: "Confirmation rule", status: "Status", battery: "Battery",
      modes: "Active in modes", sensors: "Sensors", suggest: "Suggested for", condition: "Condition", escalate: "Report unconfirmed",
      code: "Code", duress: "Duress code", tags: "Tags", bypass: "Bypass", tamper: "May bypass tamper",
      service: "Service", categories: "Categories", delay: "Delay",
      device: "Device", causes: "For", maxdur: "Max. duration",
      panelId: "Panel id", conn: "Connection", allowed: "Restrictions",
    },
    panel: { tablet: "Account", noUser: "user not found", connected: "Connected", offline: "Not reachable", noConnection: "No connection", noCard: "No Vigil card seen", cardSeen: "Vigil card active", notFound: "Not found in ESPHome", unlocked: "Unlocked", locked: "Locked for {s} s", lockedPermanent: "Locked for good", blocked: "Blocked", notWatched: "Not monitored", unlock: "Unlock", unlockedDone: "Unlocked for {s} seconds.", clear: "Clear lock", cleared: "Lock cleared.", nothingLocked: "This panel was not locked.", all: "all modes", noDisarm: "no disarming", noBypass: "no bypass", noSilence: "no silencing", hint: "Unlocking and clearing the lock can only be done here, not as a Home Assistant action.", refused: "This is not possible." },
    yes: "yes", no: "no", none: "—", immediately: "immediately",
    condition: "{n} within {s} s",
    fields: {
      name: "Name", entity_id: "Entity (binary sensor)", cls: "Class", type: "Type", sensor_groups: "Sensor groups", at_arm_open: "If open when exit delay ends",
      entry_delay: "Entry delay (empty = default)", gas_type: "Type of gas", on_unavailable: "When the sensor becomes unreachable", battery_entity: "Battery sensor", tamper_entity: "Tamper entity (optional)", chime: "Chime: sound when this sensor opens while the alarm is off", permanent_bypass: "Keep the bypass after disarming (permanent)", duress_code: "Duress code (optional)",
      "sensor_group.modes": "Active in modes", suggest_for: "Suggest for new sensors",
      sensors: "Sensors", required: "Sensors needed", window: "Time window", escalate: "Report when unconfirmed",
      code: "Code", tags: "Tags (comma separated)", allowed_modes: "May operate in modes (empty = all)", may_bypass: "May bypass sensors", may_bypass_tamper: "May bypass tamper",
      service: "Notify service", categories: "Kinds of messages", delay: "Delay", priority: "High priority",
      control: "Siren (siren, switch or light)", causes: "Sound for", max_duration: "Maximum duration (0 = until disarmed)", repeat_every: "Repeat every (0 = no)",
      light: "Flash light", tone_entity: "Tone selection entity", volume_entity: "Volume entity", power_entity: "Power mode entity", power_battery_value: "Value when on battery",
      tone: "Tone", volume: "Volume", preset: "Preset",
      device: "Kind of device", panel_id: "Name of the ESPHome device (panel id)", ha_user: "Home Assistant account (tablet or phone)", language: "Language", can_disarm: "May disarm (with a code)", can_bypass: "May bypass sensors (with a code)", can_silence: "May silence and acknowledge", sensor_list: "Show the sensor list", unlock_seconds: "Stays unlocked for (seconds)", watch: "Watch whether this panel is reachable (notify when it drops out)", blocked: "Panel blocked", "panel.code": "Installer code of this panel (empty = none)", "panel.allowed_modes": "May arm in modes (empty = all)",
      "s.modes": "Available modes", exit_delay_home: "Exit delay home", exit_delay_away: "Exit delay away", exit_delay_night: "Exit delay night", exit_delay_vacation: "Exit delay vacation", exit_delay_custom: "Exit delay custom",
      default_entry_delay: "Default entry delay", trigger_time: "Alarm duration (0 = until disarmed)", abort_seconds: "Cancel window after the siren goes off (seconds, 0 = off)", chime_entity: "Chime: what makes the sound", chime_seconds: "Chime sounds for (seconds)", battery_threshold: "Battery threshold", backup_versions: "Number of versions kept", code_arm_required: "Code required to arm", startup_wait_seconds: "Longest wait for sensors after a restart (seconds)", lock_tries_1: "Wrong codes before the first lock", lock_wait_1: "First lock lasts (minutes)", lock_tries_2: "Then wrong codes before the second lock", lock_wait_2: "Second lock lasts (minutes)", lock_tries_3: "Then wrong codes before the third lock", lock_wait_3: "Third lock lasts (minutes)", lock_tries_4: "Then wrong codes before the permanent lock", screen_off_seconds: "Screen off after (seconds without touch)", screen_off_on_alarm: "Also let the screen go dark during an alarm", log_retention_days: "Keep the log (days)", selftest_interval_days: "Siren test reminder (days, 0 = off)", selftest_siren_seconds: "Siren sounds in a test (seconds)", selftest_auto: "Sound the siren by itself for the test", selftest_window_start: "Not before (hour)", selftest_window_end: "Not after (hour)", heartbeat_url: "Heartbeat address (empty = off)", heartbeat_interval_minutes: "Minutes between heartbeats", min_code_length: "Minimum code length (characters)",
    },
    helpMore: {
      at_arm_open: "What happens if this sensor is still open when the exit delay ends:\n• Bypass with a notice (default): the alarm arms without this sensor and you get a notice. As soon as the sensor closes, it is watched again.\n• Wait until closed: the alarm arms and this sensor is ignored until it has closed once, without a notice. After that it is watched again.\n• Refuse to arm: the alarm does not arm and you see which sensor is open. Close it first.\n• Start entry delay: the alarm arms and the open sensor counts as triggered right away. A direct sensor sounds the alarm, a delayed sensor starts the entry delay.",
      tamper_entity: "Does this device also have a tamper contact? Choose it here. Vigil adds a tamper sensor for it by itself: always watching, with its own bypass switch. You do not have to add it separately.",
    },
    moreInfo: "More information",
    help: {
      duress_code: "A second code for when someone forces you to switch the alarm off. It switches the alarm off as usual and nothing shows: the siren stays quiet. Meanwhile a silent message goes to the channels with the kind of message Duress. It must differ from every other code.",
      permanent_bypass: "If you bypass this sensor by hand, it stays bypassed after the alarm is disarmed, until you restore it yourself. Handy for a sensor that has been broken for a while. Without this tick the bypass ends at disarming. Fire and gas sensors can never be bypassed.",
      chime: "When the sensor opens while the alarm is off, a short sound plays through what you chose in the settings. No alarm, no message, nothing in the log. When the alarm is on, nothing happens.",
      abort_seconds: "Whoever enters a valid code within this many seconds after the siren went off has caused a false alarm: the siren stops and a 'cancelled' message goes out. 0 switches this off. Does not apply to fire, gas and tamper.",
      chime_entity: "A siren, switch, light, button or script that makes a sound. You can leave it empty: the Chime event is still on the event entity, for an automation of your own (for example a message on a speaker).",
      chime_seconds: "How long a siren, switch or light stays on. No effect for a button or script.",
      may_bypass: "Without this right the user can neither bypass nor restore a sensor, even with a right code. A Home Assistant administrator always may.",
      screen_off_seconds: "Applies to all ESPHome panels. With a half typed code or an open list the panel first returns to the main page after this time, and the screen goes dark after the same time again.",
      screen_off_on_alarm: "Off: the screen stays on while an alarm is going, so the ALARM and its cause stay visible. On: the screen goes dark then too. During the countdown to arm or to enter, the screen never goes dark.",
      entity_id: "A binary sensor: on means open or alarm.",
      tamper_entity: "Optional: the tamper contact of this device.",
      at_arm_open: "What happens to this sensor if it is still open when the alarm arms.",
      type: "Instant: alarm at once. Delayed: entry delay first. Follower: only alarms if a delayed sensor was opened first.",
      sensor_groups: "A sensor can be in several groups. It is watching in every mode in which one of its groups is active.",
      suggest_for: "Optional. A new sensor of this kind (door contact or motion) is put in this group automatically.",
      sensors: "Instant intrusion sensors only.",
      code: "Leave empty to keep it unchanged.",
      device: "ESPHome panel: a screen with its own firmware, recognised by the name of the ESPHome device. Tablet or phone: a device running the Home Assistant app or browser, recognised by the account it is logged in as.",
      ha_user: "For a tablet or phone: the account the device is logged in as. Vigil recognises the device by that account, not by a text, so it cannot be imitated. An administrator may be chosen too, but note: the settings of this panel then apply to everything that account does, on every device it is logged in on, and Vigil gives the account no administrator rights here (a code is always needed). A second, ordinary account for daily use is better.",
      removeCode: "Remove code", removeDuress: "Remove duress code",
      tags: "Tags have no function: operate the alarm with a code.",
      categories: "Choose which messages this channel receives.",
      service: "A notify service (such as mobile_app_phone or a group from YAML) or a notify entity (such as notify.family, a notify group you made as a helper). A notify entity gets a title and a message only: the critical alert of High priority does not work with it, and neither does the button on the self-check test message. For that on a phone, choose its own mobile_app_… service.",
      priority: "Only for phones with the Home Assistant app (a mobile_app_… service): an alarm is then sent as a critical alert on iOS and with high priority on Android. For a notify entity or another service this does nothing.",
      delay: "Alarms only: wait first, for example to notify a second device only after a while.",
      profiles: "Tone and volume per cause (optional)",
      preset: "Fills in tone, volume and duration for a known siren. Pick the on/off entity under \"Siren\" first and Vigil looks for the other entities of the same device. Everything stays editable.",
      presetFound: "Found on this device:", presetNoneFound: "No other entities found on this device; pick them yourself.", presetNoControl: "Values filled in. Pick the siren entity and choose the preset again to look up the other entities.",
      power_battery_value: "The value of the power mode entity when the siren runs on battery.",
    },
    opt: {
      preset: { "": "—", sonoff_snzb_09p_z2m: "Sonoff SNZB-09P (Zigbee2MQTT)" },
      cls: { intrusion: "Intrusion", fire: "Fire", gas: "Gas", tamper: "Tamper", water: "Water", alarm24: "24 hours, audible", silent24: "24 hours, silent" },
      type: { instant: "Instant", delayed: "Delayed (entry delay)", follower: "Follower" },
      at_arm_open: { bypass: "Bypass with a notice", wait_clear: "Wait until closed", refuse: "Refuse to arm", pending: "Start entry delay" },
      gas_type: { co: "Carbon monoxide", natural_gas: "Natural gas", lpg: "LPG", other: "Other" },
      on_unavailable: { default: "Class default", block: "Block arming", notify: "Notify only", trigger: "Raise alarm", bypass: "Arm anyway (bypass)" },
      categories: { alarm: "Alarm", pending: "Entry delay", arming: "Arming and disarming", fault: "Faults and notices", technical: "Technical alarms (water)", duress: "Duress (silent alarm)" },
      causes: { intrusion: "Intrusion", fire: "Fire", gas: "Gas", tamper: "Tamper", fault: "Sensor fault" },
      cause: { intrusion: "Intrusion", fire: "Fire", gas: "Gas", tamper: "Tamper", alarm24: "24-hour alarm" },
      mode: { home: "Home", away: "Away", night: "Night", vacation: "Vacation", custom: "Custom" },
      suggest_for: { "": "None", contacts: "Doors and windows (contacts)", motion: "Motion" },
      language: { nl: "Nederlands", en: "English", de: "Deutsch", fr: "Français", it: "Italiano", es: "Español" },
      device: { esphome: "ESPHome panel (DIY screen)", account: "Tablet or phone running Home Assistant" },
      sensor_list: { always: "Always show", code: "Only after unlocking", never: "Never show" },
    },
    why: {
      title: "Why can't I arm?", intro: "This stops arming right now:", modes: "in {modes}", show: "Show", bypass: "Bypass", bypassed: "Bypassed",
      neverBypass: "Fire and gas sensors cannot be bypassed: remove the cause first.",
      reason: { alarm_condition: "is open (an alarm condition)", sensor_unavailable: "does not respond (and is set to stop arming)", sensor_open: "is open and must be closed to arm", not_disarmed: "the alarm is already on" },
      hint: "On the panel and in the Vigil card the Bypass and arm button bypasses and arms in one go, if you have the right to.",
    },
    backup: {
      intro: "On every change Vigil keeps the configuration as it was before that change (the last 10 versions). You can put such a version back; restoring is a change too, so it can be undone the same way. Only the settings are kept, not the state of the alarm (armed, bypassed).",
      list: "Kept versions", none: "No versions yet. They appear as soon as you change something.", restore: "Restore",
      reason: { edit: "Change", restore: "Restored", import: "Import", external: "Changed outside the panel", upgrade: "Vigil update" },
      colTime: "Time", colReason: "Reason", colVigil: "Vigil version", colChange: "Change",
      view: "View", viewTitle: "Change of {time}", viewText: "This version keeps the configuration as it was before this change. The change itself was:", format: "storage version {v}",
      notRestorable: "Cannot be restored: made by another storage version ({v}, now {now}). It can still be viewed.", settingsList: "Settings: {names}",
      restoreTitle: "Restore this version?", restoreText: "Restoring changes this compared with now:", nothing: "No difference with now.", restored: "Restored",
      fileTitle: "Export and import", export: "Export configuration", import: "Import configuration…",
      exportNote: "The file holds no codes, but it does hold the hashed codes, the heartbeat address and the names of your notification services. Keep it safe.",
      importNote: "Importing replaces the whole configuration. The present one is kept as a version, so an import can be restored.",
      importTitle: "Import this file?", importText: "Importing changes this compared with now:", imported: "Imported", readFailed: "This file cannot be read.",
      added: "added", removed: "removed", changed: "changed", settings: "Settings changed: {n}", undo: "Undo", apply: "Apply",
    },
    errors: {
      backup_invalid: "This file or version holds no usable configuration.", backup_unknown: "This version no longer exists.", import_not_vigil: "This is not a Vigil Alarm export file.", import_format_version: "This file has an unknown format.", import_entry_version: "This file belongs to another storage version ({found}, needed: {expected}). Import it in the same version of Vigil it was made in.",
      name_required: "Enter a name.", name_in_use: "This name already exists.", required: "Required.",
      invalid_config: "Invalid: {error}", sensor_not_instant: "Only instant sensors can be in a confirmation rule. Change: {sensors}",
      entity_in_use: "This entity is already a sensor.", tamper_same_entity: "The tamper entity must be another one than the sensor itself.", tamper_entity_in_use: "This entity is already a sensor.",
      no_sensor_group: "Choose at least one sensor group.", unknown_sensor_group: "Unknown sensor group.",
      unknown_mode: "Unknown mode.", unknown_suggestion: "Unknown choice.",
      backup_versions_range: "Choose a number from {min} to {max}.", code_in_use: "This code is already in use.", code_too_short: "The code must have at least {min} characters (set under Settings).", code_length_range: "Choose a value from {min} to {max}.", screen_off_range: "Choose a number of seconds from {min} to {max}.", startup_wait_range: "Choose a number of seconds from {min} to {max}.", lock_tries_range: "Choose a number of times from {min} to {max}.", lock_wait_range: "Choose a number of minutes from {min} to {max}.", log_retention_range: "Choose a number of days from {min} to {max}.", selftest_range: "Choose a value from {min} to {max}.", selftest_window: "The latest hour must be after the earliest hour.", heartbeat_url_invalid: "That is not a web address. It must start with http:// or https://.", heartbeat_range: "Choose a number of minutes from {min} to {max}.", tag_in_use: "This tag is already in use.", no_credential: "Enter a code or at least one tag.", duress_needs_code: "A duress code goes with an ordinary code: enter a code first.", duress_no_channel: "There is no notification channel with the kind of message Duress. Without one a silent alarm reaches nobody. Add one first.", seconds_range: "Choose a number of seconds from {min} to {max}.", chime_entity_domain: "Choose a siren, switch, light, button or script.",
      service_not_found: "This notify service does not exist (any more).", no_categories: "Choose at least one kind of message.",
      no_causes: "Choose at least one cause.", tone_without_entity: "A tone needs a tone selection entity.", volume_without_entity: "A volume needs a volume entity.",
      sensor_in_rule: "This sensor is still in confirmation rule: {rules}. Remove it there first.",
      sensor_group_in_use: "This sensor group is still used by: {sensors}. Remove the group from those sensors first.",
      no_modes: "Choose at least one mode.", unknown_kind: "Unknown item.",
      panel_id_invalid: "Use lowercase letters, digits, - and _ (like the device name in ESPHome).", panel_id_in_use: "This panel id is already registered.", unlock_range: "Choose a value from {low} to {high}.", unknown_choice: "Unknown choice.", ha_user_unknown: "This user does not exist or is not active.",ha_user_in_use: "This user is already bound to another panel.",
      generic: "Something went wrong.",
    },
  },
  de: {
    "title": "Vigil Alarm",
    "tamperShort": "Sabotage",
    "about": {
      "details": "Details",
      "aboutIntro": "Eine modulare Alarmanlage für Home Assistant.",
      "version": "Version",
      "license": "Lizenz",
      "author": "Autor",
      "links": "Links",
      "manual": "Anleitung",
      "manualOther": "Anleitung (Nederlands)",
      "repository": "GitHub-Projekt",
      "releases": "Releases auf GitHub",
      "issues": "Problem melden oder Idee teilen",
      "panelDocs": "Touch-Bedienteil (ESPHome)",
      "licenseText": "Lizenztext",
      "notes": "Release Notes",
      "notesOnlyEnglish": "",
      "noNotes": "Keine Release Notes gefunden.",
      "system": "System",
      "haVersion": "Home Assistant",
      "python": "Python",
      "alarmState": "Alarmstatus",
      "items": "Elemente",
      "copyInfo": "Details für eine Meldung kopieren",
      "copied": "Kopiert",
      "copyFailed": "Kopieren fehlgeschlagen",
      "disclaimer": "Vigil Alarm ist keine zertifizierte Alarmanlage. Teste sie regelmäßig und verlasse dich nicht allein darauf.",
      "unreleased": "Noch nicht veröffentlicht",
      "firstRelease": "erste Version"
    },
    "tabs": {
      "overview": "Übersicht",
      "sensor": "Sensoren",
      "sensor_group": "Sensorgruppen",
      "rule": "Bestätigungsregeln",
      "user": "Benutzer",
      "notification": "Benachrichtigungen",
      "siren": "Sirenen",
      "log": "Protokoll",
      "settings": "Einstellungen",
      "backup": "Sicherung",
      "about": "Info",
      "panel": "Bedienteile"
    },
    "add": {
      "sensor": "Sensor hinzufügen",
      "sensor_group": "Sensorgruppe hinzufügen",
      "rule": "Bestätigungsregel hinzufügen",
      "user": "Benutzer hinzufügen",
      "notification": "Benachrichtigung hinzufügen",
      "siren": "Sirene hinzufügen",
      "panel": "Bedienteil hinzufügen"
    },
    "edit": {
      "sensor": "Sensor bearbeiten",
      "sensor_group": "Sensorgruppe bearbeiten",
      "rule": "Bestätigungsregel bearbeiten",
      "user": "Benutzer bearbeiten",
      "notification": "Benachrichtigung bearbeiten",
      "siren": "Sirene bearbeiten",
      "panel": "Bedienteil bearbeiten"
    },
    "intro": {
      "sensor": "Ein einzelner Melder, etwa ein Türkontakt, Bewegungsmelder oder Rauchmelder. Bei einem Einbruchsensor wählst du, in welchen Sensorgruppen er ist. Brand-, Gas-, Wasser- und Sabotagesensoren überwachen immer und brauchen keine Sensorgruppe. Das gilt auch für 24 Stunden, hörbar (ein Panikknopf, eine Schuppentür: Alarm mit Sirene, auch bei unscharfer Anlage) und 24 Stunden, still (eine Tiefkühltruhe oder ein Leckagemelder: nur eine Nachricht und ein Eintrag im Protokoll).",
      "sensor_group": "Eine Sensorgruppe bestimmt, in welchen Modi die darin enthaltenen Sensoren überwachen. Zum Beispiel: Außenhaut (Türen und Fenster) für Zuhause, Abwesend und Nacht, und Innenbereich (Bewegung) nur für Abwesend.",
      "rule": "Ein Alarm folgt erst, wenn die angegebene Anzahl verschiedener Sensoren innerhalb des Zeitfensters auslöst. Praktisch gegen Fehlalarm durch einen einzelnen Bewegungsmelder.",
      "user": "Personen, die die Alarmanlage mit einem Code bedienen können. Der Code bestimmt, wer bedient; welche Geräte bedienen dürfen, legst du unter Bedienteile fest.",
      "notification": "Wer wann Nachrichten erhält. Jede Benachrichtigung ist ein Notify-Dienst.",
      "siren": "Optional. Ohne Sirene arbeitet die Alarmanlage mit Benachrichtigungen.",
      "panel": "Ein Gerät an der Wand: ein ESPHome-Bedienteil oder ein Tablet oder Handy mit eigenem Home-Assistant-Konto. Vigil entscheidet, was jedes Bedienteil darf und welche Daten es bekommt; das Bedienteil selbst entscheidet nichts. Die Bedienteil-ID ist der Name des ESPHome-Geräts. Sobald ein Konto verknüpft ist, können andere gewöhnliche Konten die Alarmanlage nicht mehr bedienen."
    },
    "empty": {
      "sensor": "Noch keine Sensoren. Lege zuerst eine Sensorgruppe an, falls es noch keine gibt, dann deine Sensoren.",
      "sensor_group": "Noch keine Sensorgruppen. Eine Sensorgruppe bestimmt, in welchen Modi Sensoren überwachen.",
      "rule": "Noch keine Bestätigungsregeln. Optional: ein Alarm erst nach mehreren Sensoren.",
      "user": "Noch keine Benutzer. Ohne Benutzer ist kein Code zum Bedienen der Alarmanlage nötig.",
      "notification": "Noch keine Benachrichtigungen. Füge einen Notify-Dienst hinzu, um Nachrichten zu erhalten.",
      "siren": "Noch keine Sirene. Das ist optional; ohne Sirene arbeitet die Alarmanlage mit Benachrichtigungen.",
      "panel": "Noch keine Bedienteile. Ohne registriertes Bedienteil erhält ein ESPHome-Bedienteil kein Profil und bedient nichts."
    },
    "save": "Speichern",
    "cancel": "Abbrechen",
    "del": "Löschen",
    "dup": "Kopieren",
    "editBtn": "Bearbeiten",
    "testBtn": "Testen",
    "close": "Schließen",
    "ready": {
      "title": "Einsatzbereit?",
      "allGood": "Alles ist eingerichtet. Teste die Alarmanlage trotzdem regelmäßig.",
      "problem": "Zuerst beheben",
      "advice": "Empfehlung",
      "go": "Dorthin",
      "createGroups": "Standardgruppen anlegen",
      "groupsMade": "Sensorgruppen angelegt",
      "addPhone": "Handy hinzufügen: {name}",
      "phoneAdded": "{name} hinzugefügt; eine Testbenachrichtigung wurde gesendet. Ist sie angekommen?",
      "text": {
        "no_sensors": "Es gibt noch keine Sensoren. Füge welche hinzu oder lass Vigil sie suchen.",
        "no_sensor_groups": "Es gibt noch keine Sensorgruppen. Ohne Gruppe überwacht ein Einbruchsensor nichts. Vigil kann zwei vorschlagen: Außenhaut (Türen und Fenster) und Innenbereich (Bewegung).",
        "mode_unwatched": "Kein Einbruchsensor überwacht in diesem Modus: {modes}.",
        "no_user_code": "Es gibt noch keinen Benutzer mit Code, also kann niemand die Alarmanlage bedienen.",
        "no_notification": "Es gibt noch keinen Benachrichtigungskanal, also hörst du bei einem Alarm nichts. Nutze zum Beispiel die App auf deinem Handy.",
        "no_siren": "Es gibt keine Sirene. Die Alarmanlage arbeitet dann nur mit Benachrichtigungen.",
        "battery_missing": "{n} Sensoren haben keinen Batteriesensor, daher erfährst du nicht, wenn eine Batterie schwach wird: {names}.",
        "tamper_unlinked": "{n} Sensoren haben am selben Gerät einen Sabotagekontakt, der mit nichts verbunden ist: {names}.",
        "panel_firmware": "Die Firmware von Bedienteil {name} versteht Profilversion {seen}, Vigil verwendet Version {wanted}. Aktualisiere die Firmware des Bedienteils."
      }
    },
    "heartbeat": {
      "title": "Heartbeat",
      "off": "Aus. Gib unter Einstellungen eine Heartbeat-Adresse ein, um zu starten.",
      "lastOk": "Zuletzt erfolgreich",
      "lastFail": "Zuletzt fehlgeschlagen",
      "never": "noch nicht",
      "every": "Alle {n} Minuten",
      "test": "Jetzt testen",
      "ok": "Der Heartbeat ist angekommen.",
      "failed": "Der Heartbeat ist nicht angekommen ({reason}).",
      "reason": {
        "timeout": "keine Antwort innerhalb von 10 Sekunden",
        "connection": "keine Verbindung"
      },
      "failing": "Fehlgeschlagen: {reason}"
    },
    "selftest": {
      "title": "Selbsttest",
      "last": "Letzte stille Prüfung",
      "lastSiren": "Letzter Sirenentest",
      "next": "Nächster Sirenentest",
      "never": "noch nicht",
      "off": "Erinnerung ist aus (Einstellungen)",
      "noSiren": "Es ist keine Sirene eingerichtet.",
      "overdue": "Überfällig: der Test war vor {days} Tagen fällig.",
      "test": "Sirene jetzt testen",
      "started": "Die Sirene ertönt {seconds} Sekunden lang.",
      "auto": "Vigil lässt die Sirene innerhalb der eingestellten Zeiten selbst ertönen.",
      "problems": "Fehlender Benachrichtigungskanal: {name}"
    },
    "dash": {
      "title": "Dashboard",
      "text": "Ein Dashboard mit den eigenen Entitäten dieser Alarmanlage. Kopiere es und füge es in ein neues Dashboard ein (Einstellungen > Dashboards > neues Dashboard > Rohkonfigurationseditor).",
      "copy": "Dashboard kopieren"
    },
    "log": {
      "intro": "Alles, was Vigil als Ereignis meldet. Das Protokoll bewahrt {days} Tage auf (siehe Einstellungen) und enthält keine Codes. Zeiten erscheinen in deiner Zeitzone; in den Downloads sind sie in UTC als RFC 3339.",
      "empty": "Noch nichts im Protokoll.",
      "cols": {
        "time": "Zeit",
        "event": "Ereignis",
        "item": "Element",
        "who": "Benutzer",
        "via": "Über",
        "result": "Ergebnis",
        "noCode": "unbekannt (kein Code)",
        "installer": "Installateurcode",
        "auto": "automatisch"
      },
      "showing": "Die neuesten {n} von {total}",
      "jsonl": "Herunterladen (JSON Lines)",
      "csv": "Herunterladen (CSV)",
      "refresh": "Aktualisieren"
    },
    "summary": {
      "always": "{cls}, immer aktiv",
      "instant": "sofort",
      "delayed": "verzögert ({s} s)",
      "follower": "Folgesensor",
      "and": "und",
      "watching": "{type}, überwacht in {modes}",
      "nowhere": "{type}, überwacht in keinem Modus"
    },
    "whatsNew": "neu",
    "batteryLow": "schwach",
    "batteryOk": "ok",
    "copySuffix": " (Kopie)",
    "permBypass": {
      "title": "Dauerhaft überbrückt",
      "intro": "Diese Sensoren sind überbrückt und überwachen nicht, auch nach dem Unscharfschalten. Stelle sie wieder her, sobald sie repariert sind:",
      "restore": "Wiederherstellen",
      "restored": "Wiederhergestellt"
    },
    "memory": {
      "title": "Letzter Alarm",
      "running": "Der Alarm läuft noch.",
      "endedBy": "Um {time} von {who} unscharf geschaltet.",
      "cancelled": "Als Fehlalarm abgebrochen.",
      "cause": "Ursache",
      "first": "Erster Sensor",
      "path": "Weg durch das Haus",
      "pathIntro": "Jeder Sensor, der vom Beginn des Alarms bis zum Unscharfschalten geöffnet wurde, der Reihe nach. Sensoren, die in diesem Modus nicht zählten oder überbrückt waren, sind enthalten: zusammen zeigen sie, wo jemand gewesen ist.",
      "time": "Zeit",
      "sensor": "Sensor",
      "room": "Raum",
      "counted": "Gezählt",
      "notCounted": "Nicht gezählt",
      "times": "{n}× geöffnet",
      "clear": "Alarmspeicher löschen",
      "cleared": "Alarmspeicher gelöscht",
      "noRoom": "kein Raum festgelegt",
      "empty": "Kein Sensor wurde geöffnet (nur die erste Meldung).",
      "steps": "{n} Schritte",
      "more": "Nur die ersten {n} Schritte werden gespeichert."
    },
    "practice": {
      "chip": "Übungsmodus",
      "title": "Üben und testen",
      "text": "Übungsmodus: Die Alarmanlage arbeitet wie immer (sie zählt herunter, löst aus, die Bedienteile zeigen es an), aber es ertönt keine Sirene und es wird keine Nachricht gesendet. Alles steht im Protokoll, als Übung gekennzeichnet. Er endet nach 30 Minuten oder sobald du unscharf schaltest.",
      "start": "Übungsmodus starten",
      "stop": "Übungsmodus beenden",
      "left": "Noch {n} Min.",
      "needsOff": "Schalte die Alarmanlage zuerst aus.",
      "walk": "Begehungstest: Gehe bei unscharfer Anlage an den Türen, Fenstern und Bewegungsmeldern entlang; jeder Sensor, der reagiert, wird abgehakt. Nur Einbruchsensoren nehmen teil (Brand-, Gas-, Wasser- und Sabotagesensoren sind immer aktiv und haben einen eigenen Test).",
      "walkStart": "Begehungstest starten",
      "walkTitle": "Begehungstest",
      "walkRunning": "Öffne jede Tür und jedes Fenster und gehe an jedem Bewegungsmelder vorbei. {n} von {total} gesehen.",
      "walkStop": "Test beenden",
      "walkDone": "Fertig: {seen} von {total} gesehen.",
      "walkAgain": "Nochmal",
      "walkMissing": "Nicht gesehen",
      "walkReason": {
        "no_response": "hat nicht reagiert",
        "unavailable": "ist nicht verfügbar"
      },
      "walkSeen": "Gesehen",
      "walkNone": "Alle Sensoren haben reagiert.",
      "walkLast": "Letzter Begehungstest: {seen} von {total} gesehen ({time}).",
      "close": "Schließen"
    },
    "wizard": {
      "title": "Vigil einrichten",
      "button": "Einrichtungsassistent",
      "step": "Schritt {n} von {total}",
      "back": "Zurück",
      "next": "Weiter",
      "skip": "Überspringen",
      "finish": "Fertig",
      "stop": "Später fortsetzen",
      "resume": "Assistent fortsetzen",
      "cardTitle": "Vigil einrichten",
      "cardText": "Noch ist nicht alles eingerichtet. Der Assistent führt dich Schritt für Schritt durch; du kannst jeden Schritt überspringen und später zurückkommen.",
      "start": "Assistent starten",
      "done": "Fertig",
      "todo": "Zu erledigen",
      "optional": "Empfohlen",
      "welcome": {
        "title": "Willkommen bei Vigil",
        "text": "In wenigen Schritten richtest du die Alarmanlage ein: welche Modi du nutzt, welche Sensoren teilnehmen, wer einen Code bekommt und wie du benachrichtigt wirst. Nichts wird gespeichert, bis du es in einem Schritt bestätigst, und jede Änderung lässt sich über den Tab Sicherung zurücksetzen."
      },
      "modes": {
        "title": "Welche Modi nutzt du?",
        "text": "Zuhause (du bist da, die Außenhaut wird überwacht), Abwesend (niemand zuhause), Nacht (du schläfst), Urlaub (länger weg) und Benutzerdefiniert (ein eigener Modus, zum Beispiel nur die Garage). Wähle nur, was du wirklich nutzt; die Ausgangsverzögerungen kannst du später unter Einstellungen ändern.",
        "save": "Speichern",
        "saved": "Modi gespeichert.",
        "none": "Wähle mindestens einen Modus."
      },
      "sensors": {
        "title": "Sensoren",
        "text": "Vigil sucht in Home Assistant nach Tür-, Fenster-, Bewegungs-, Rauch-, Gas- und Wassersensoren. Du wählst, welche hinzugefügt werden.",
        "have": "{n} Sensoren eingerichtet.",
        "none": "Noch keine Sensoren.",
        "find": "Sensoren suchen",
        "fresh": "{n} neu gefunden."
      },
      "user": {
        "title": "Wer darf die Alarmanlage bedienen?",
        "text": "Ein Benutzer hat einen Code. Du kannst einen Benutzer aus einer Home-Assistant-Person erstellen oder von Hand hinzufügen.",
        "have": "{n} Benutzer mit Code.",
        "none": "Noch kein Benutzer mit Code.",
        "fromPerson": "{name} zum Benutzer machen",
        "add": "Benutzer hinzufügen"
      },
      "notification": {
        "title": "Wo möchtest du eine Nachricht erhalten?",
        "text": "Bei einem Alarm oder einer Störung sendet Vigil eine Nachricht. Ein Handy mit der Home-Assistant-App ist am einfachsten.",
        "have": "{n} Benachrichtigungskanal/-kanäle.",
        "none": "Noch kein Benachrichtigungskanal.",
        "phone": "{name} hinzufügen",
        "add": "Benachrichtigungskanal hinzufügen",
        "added": "{name} wurde hinzugefügt; eine Testnachricht wurde gesendet."
      },
      "siren": {
        "title": "Sirene",
        "text": "Eine Sirene ist nicht erforderlich, aber ohne sie hörst du einen Alarm nur über Nachrichten.",
        "have": "{n} Sirene(n).",
        "none": "Noch keine Sirene.",
        "add": "Sirene hinzufügen"
      },
      "panel": {
        "title": "Bedienteil an der Wand",
        "text": "Ein ESPHome-Display oder ein Tablet oder Handy kann die Alarmanlage bedienen. Das ist optional.",
        "have": "{n} Bedienteil(e).",
        "none": "Noch kein Bedienteil.",
        "add": "Bedienteil verknüpfen"
      },
      "test": {
        "title": "Einsatzbereit?",
        "text": "Das fehlt Vigil noch. Alles, was mit „Problem“ markiert ist, verhindert weiterhin den Schutz durch die Alarmanlage.",
        "allGood": "Alles in Ordnung.",
        "testSiren": "Sirene testen",
        "sirenStarted": "Die Sirene ertönt kurz."
      },
      "end": {
        "title": "Fertig",
        "text": "Vigil ist eingerichtet. Ein Probelauf: Schalte die Alarmanlage scharf, öffne eine Tür und sieh nach, ob deine Nachricht ankommt. Danach kannst du Automatisierungen mit den mitgelieferten Blueprints hinzufügen (automatisch scharf schalten, wenn alle gehen, bei Alarm Lichter blinken lassen, eine Nachricht sprechen). Du findest sie in der Anleitung unter Automatisierungen und Blueprints."
      }
    },
    "newSensors": {
      "title": "Neue Sensoren gefunden",
      "text": "Diese Sensoren sind in Home Assistant aufgetaucht, seit Vigil zuletzt nachgesehen hat. Es wurde nichts hinzugefügt.",
      "review": "Prüfen und hinzufügen",
      "later": "Jetzt nicht",
      "badge": "{n} neu",
      "dismissed": "OK, Vigil meldet diese nicht noch einmal. Du kannst sie weiterhin über „Sensoren suchen“ hinzufügen.",
      "onlyNew": "Es werden nur die neuen Sensoren angezeigt.",
      "showAll": "Alle Sensoren anzeigen",
      "showNew": "Nur neue anzeigen"
    },
    "find": {
      "button": "Sensoren suchen",
      "title": "Sensoren suchen",
      "intro": "Diese Sensoren wurden in Home Assistant gefunden. Wähle, welche hinzugefügt werden. Nichts wird gespeichert, bis du unten auf die Schaltfläche drückst.",
      "none": "Keine neuen Sensoren gefunden. Tür-, Fenster-, Bewegungs-, Rauch-, Gas-, Wasser- und Sabotagesensoren eines eingebundenen Geräts werden angezeigt.",
      "noGroups": "Einige Einbruchsensoren haben noch keine Sensorgruppe. Stelle bei einer Sensorgruppe „Für neue Sensoren vorschlagen“ auf Kontakte oder Bewegung; dann kannst du sie hier hinzufügen.",
      "cols": {
        "name": "Name",
        "cls": "Klasse",
        "entrance": "Eingang",
        "groups": "Sensorgruppen",
        "extra": "Aufgenommen"
      },
      "entranceHelp": "Ein Eingang bekommt eine Eingangsverzögerung (Typ „verzögert“).",
      "inUse": "bereits in Verwendung",
      "needsGroup": "keine Sensorgruppe",
      "battery": "Batterie",
      "tamper": "Sabotage",
      "all": "Alle auswählen",
      "nothing": "Keine auswählen",
      "add": "{n} hinzufügen",
      "adding": "Wird hinzugefügt…",
      "copy": "Suchdaten kopieren",
      "copyHelp": "Eine anonyme Liste ohne Namen oder Adressen, für eine Meldung oder um beim Testen einer Integration zu helfen.",
      "createGroups": "Standardgruppen anlegen",
      "added": "{n} Sensoren hinzugefügt",
      "failed": "{name}: {error}"
    },
    "confirmDelete": "Möchtest du „{name}“ wirklich löschen?",
    "saved": "Gespeichert",
    "deleted": "Gelöscht",
    "testSent": "Test gesendet",
    "loading": "Wird geladen…",
    "loadFailed": "Vigil Alarm konnte nicht geladen werden. Läuft die Integration?",
    "retry": "Erneut versuchen",
    "sections": {
      "alarm": {
        "0": "Modi und Verzögerungen",
        "1": "Welche Modi du nutzt, wie lange du zum Verlassen und Hereinkommen hast und wie lange der Alarm dauert."
      },
      "chime": {
        "0": "Türgong",
        "1": "Ein kurzer Ton, wenn sich ein Sensor mit gesetztem Türgong-Häkchen öffnet, während die Alarmanlage unscharf ist."
      },
      "codes": {
        "0": "Codes",
        "1": "Ob zum Scharfschalten ein Code nötig ist und wie lang ein Code mindestens sein muss."
      },
      "startup": {
        "0": "Start",
        "1": "Nach einem Neustart von Home Assistant wartet Vigil, bis alle deine Sensoren verfügbar sind (zum Beispiel MQTT oder Zigbee starten noch), bevor es einen Sensor als verloren meldet oder dafür Alarm auslöst. Sind sie nach dieser Zeit noch immer weg, folgt die Meldung."
      },
      "lock": {
        "0": "Sperren",
        "1": "Was nach falschen Codes pro Bedienteil geschieht: erst eine kurze Sperre, dann längere, dann eine dauerhafte Sperre, die nur über „Sperre aufheben“ unter Bedienteile verschwindet. Ein richtiger Code beginnt wieder bei null."
      },
      "screen": {
        "0": "Bedienteil-Display",
        "1": "Wann das Display eines ESPHome-Bedienteils dunkel wird. Es wird nur dunkel, solange die Alarmanlage unscharf oder voll scharf ist, nie während des Countdowns zum Scharf- oder Unscharfschalten."
      },
      "battery": {
        "0": "Batterien",
        "1": "Ab welchem Stand eine Batterie als schwach gilt."
      },
      "log": {
        "0": "Ereignisprotokoll",
        "1": "Wie lange Vigil die Ereignisse aufbewahrt."
      },
      "backup": {
        "0": "Sicherung",
        "1": "Wie viele Versionen deiner Konfiguration Vigil aufbewahrt (Tab Sicherung). Ein niedrigerer Wert verwirft die ältesten Versionen."
      },
      "selftest": {
        "0": "Selbsttest",
        "1": "Vigil erinnert dich daran, die Sirene zu testen. Setze das Intervall auf 0, um die Erinnerung auszuschalten."
      },
      "heartbeat": {
        "0": "Heartbeat",
        "1": "Vigil ruft diese Adresse regelmäßig auf, damit ein Dienst außerhalb deines Hauses meldet, wenn Home Assistant oder dein Internet ausfällt."
      }
    },
    "reloadNote": "Beim Speichern wird Vigil Alarm neu geladen (der Alarmstatus bleibt erhalten).",
    "alarm": "Alarm",
    "problems": "Achtung",
    "noProblems": "Keine Probleme",
    "sensorsNow": "Sensoren jetzt",
    "coverage": "Was jeder Modus überwacht",
    "coverageNothing": "keine Sensorgruppe: nichts wird überwacht",
    "alwaysOn": "Immer aktiv",
    "sensorsCount": "{n} Sensoren",
    "state": {
      "disarmed": "Aus",
      "arming": "Wird scharf",
      "armed": "Scharf",
      "pending": "Eingangsverzögerung",
      "triggered": "ALARM"
    },
    "mode": {
      "home": "Zuhause",
      "away": "Abwesend",
      "night": "Nacht",
      "vacation": "Urlaub",
      "custom": "Benutzerdefiniert"
    },
    "zstatus": {
      "closed": "Geschlossen",
      "open": "Offen",
      "unavailable": "Nicht erreichbar",
      "bypassed": "Überbrückt",
      "bypassed_at_arm": "Beim Scharfschalten überbrückt",
      "waiting": "Wartet auf Schließen"
    },
    "problem": {
      "battery_low": "Batterie schwach",
      "unavailable": "nicht erreichbar",
      "on_battery": "keine Netzspannung"
    },
    "cols": {
      "name": "Name",
      "entity": "Entität",
      "cls": "Klasse",
      "type": "Typ",
      "groups": "Sensorgruppen",
      "rule": "Bestätigungsregel",
      "status": "Status",
      "battery": "Batterie",
      "modes": "Aktiv in Modi",
      "sensors": "Sensoren",
      "suggest": "Vorgeschlagen für",
      "condition": "Bedingung",
      "escalate": "Unbestätigt melden",
      "code": "Code",
      "duress": "Zwangscode",
      "tags": "Tags",
      "bypass": "Überbrücken",
      "tamper": "Darf Sabotage überbrücken",
      "service": "Dienst",
      "categories": "Kategorien",
      "delay": "Verzögerung",
      "device": "Gerät",
      "causes": "Für",
      "maxdur": "Max. Dauer",
      "panelId": "Bedienteil-ID",
      "conn": "Verbindung",
      "allowed": "Einschränkungen"
    },
    "panel": {
      "tablet": "Konto",
      "noUser": "Benutzer nicht gefunden",
      "connected": "Verbunden",
      "offline": "Nicht erreichbar",
      "noConnection": "Keine Verbindung",
      "noCard": "Keine Vigil-Karte gesehen",
      "cardSeen": "Vigil-Karte aktiv",
      "notFound": "In ESPHome nicht gefunden",
      "unlocked": "Entsperrt",
      "locked": "Gesperrt für {s} s",
      "lockedPermanent": "Dauerhaft gesperrt",
      "blocked": "Gesperrt",
      "notWatched": "Nicht überwacht",
      "unlock": "Entsperren",
      "unlockedDone": "Für {s} Sekunden entsperrt.",
      "clear": "Sperre aufheben",
      "cleared": "Sperre aufgehoben.",
      "nothingLocked": "Dieses Bedienteil war nicht gesperrt.",
      "all": "alle Modi",
      "noDisarm": "kein Unscharfschalten",
      "noBypass": "kein Überbrücken",
      "noSilence": "kein Stummschalten",
      "hint": "Entsperren und Aufheben der Sperre ist nur hier möglich, nicht als Home-Assistant-Aktion.",
      "refused": "Das ist nicht möglich."
    },
    "yes": "ja",
    "no": "nein",
    "none": "—",
    "immediately": "sofort",
    "condition": "{n} innerhalb von {s} s",
    "fields": {
      "name": "Name",
      "entity_id": "Entität (Binärsensor)",
      "cls": "Klasse",
      "type": "Typ",
      "sensor_groups": "Sensorgruppen",
      "at_arm_open": "Wenn am Ende der Ausgangsverzögerung offen",
      "entry_delay": "Eingangsverzögerung (leer = Standard)",
      "gas_type": "Gasart",
      "on_unavailable": "Wenn der Sensor nicht mehr erreichbar ist",
      "battery_entity": "Batteriesensor",
      "tamper_entity": "Sabotage-Entität (optional)",
      "chime": "Türgong: Ton, wenn sich dieser Sensor bei unscharfer Anlage öffnet",
      "permanent_bypass": "Überbrückung nach dem Unscharfschalten beibehalten (dauerhaft)",
      "duress_code": "Zwangscode (optional)",
      "sensor_group.modes": "Aktiv in Modi",
      "suggest_for": "Für neue Sensoren vorschlagen",
      "sensors": "Sensoren",
      "required": "Benötigte Sensoren",
      "window": "Zeitfenster",
      "escalate": "Melden, wenn unbestätigt",
      "code": "Code",
      "tags": "Tags (durch Komma getrennt)",
      "allowed_modes": "Darf in Modi scharf schalten (leer = alle)",
      "may_bypass": "Darf Sensoren überbrücken",
      "may_bypass_tamper": "Darf Sabotage überbrücken",
      "service": "Notify-Dienst",
      "categories": "Nachrichtenarten",
      "delay": "Verzögerung",
      "priority": "Hohe Priorität",
      "control": "Sirene (Sirene, Schalter oder Licht)",
      "causes": "Ertönt bei",
      "max_duration": "Maximale Dauer (0 = bis zum Unscharfschalten)",
      "repeat_every": "Wiederholen alle (0 = nie)",
      "light": "Licht blinken lassen",
      "tone_entity": "Entität zur Tonauswahl",
      "volume_entity": "Lautstärke-Entität",
      "power_entity": "Entität für den Energiemodus",
      "power_battery_value": "Wert bei Batteriebetrieb",
      "tone": "Ton",
      "volume": "Lautstärke",
      "preset": "Voreinstellung",
      "device": "Art des Geräts",
      "panel_id": "Name des ESPHome-Geräts (Bedienteil-ID)",
      "ha_user": "Home-Assistant-Konto (Tablet oder Handy)",
      "language": "Sprache",
      "can_disarm": "Darf unscharf schalten (mit Code)",
      "can_bypass": "Darf Sensoren überbrücken (mit Code)",
      "can_silence": "Darf stummschalten und quittieren",
      "sensor_list": "Sensorliste anzeigen",
      "unlock_seconds": "Bleibt entsperrt für (Sekunden)",
      "watch": "Überwachen, ob dieses Bedienteil erreichbar ist (benachrichtigen bei Ausfall)",
      "blocked": "Bedienteil gesperrt",
      "panel.code": "Installateurcode dieses Bedienteils (leer = keiner)",
      "panel.allowed_modes": "Darf in Modi scharf schalten (leer = alle)",
      "s.modes": "Verfügbare Modi",
      "exit_delay_home": "Ausgangsverzögerung Zuhause",
      "exit_delay_away": "Ausgangsverzögerung Abwesend",
      "exit_delay_night": "Ausgangsverzögerung Nacht",
      "exit_delay_vacation": "Ausgangsverzögerung Urlaub",
      "exit_delay_custom": "Ausgangsverzögerung Benutzerdefiniert",
      "default_entry_delay": "Standard-Eingangsverzögerung",
      "trigger_time": "Alarmdauer (0 = bis zum Unscharfschalten)",
      "abort_seconds": "Abbruchfenster nach Sirenenstart (Sekunden, 0 = aus)",
      "chime_entity": "Türgong: was den Ton erzeugt",
      "chime_seconds": "Türgong ertönt für (Sekunden)",
      "battery_threshold": "Batterieschwelle",
      "backup_versions": "Anzahl aufbewahrter Versionen",
      "code_arm_required": "Code zum Scharfschalten erforderlich",
      "startup_wait_seconds": "Längste Wartezeit auf Sensoren nach einem Neustart (Sekunden)",
      "lock_tries_1": "Falsche Codes bis zur ersten Sperre",
      "lock_wait_1": "Erste Sperre dauert (Minuten)",
      "lock_tries_2": "Danach falsche Codes bis zur zweiten Sperre",
      "lock_wait_2": "Zweite Sperre dauert (Minuten)",
      "lock_tries_3": "Danach falsche Codes bis zur dritten Sperre",
      "lock_wait_3": "Dritte Sperre dauert (Minuten)",
      "lock_tries_4": "Danach falsche Codes bis zur dauerhaften Sperre",
      "screen_off_seconds": "Display aus nach (Sekunden ohne Berührung)",
      "screen_off_on_alarm": "Display auch bei einem Alarm dunkel werden lassen",
      "log_retention_days": "Protokoll aufbewahren (Tage)",
      "selftest_interval_days": "Erinnerung an den Sirenentest (Tage, 0 = aus)",
      "selftest_siren_seconds": "Sirene ertönt beim Test (Sekunden)",
      "selftest_auto": "Sirene für den Test selbst ertönen lassen",
      "selftest_window_start": "Nicht vor (Uhr)",
      "selftest_window_end": "Nicht nach (Uhr)",
      "heartbeat_url": "Heartbeat-Adresse (leer = aus)",
      "heartbeat_interval_minutes": "Minuten zwischen Heartbeats",
      "min_code_length": "Minimale Codelänge (Zeichen)"
    },
    "helpMore": {
      "at_arm_open": "Was geschieht, wenn dieser Sensor am Ende der Ausgangsverzögerung noch offen ist:\n• Überbrücken mit Hinweis (Standard): Die Alarmanlage wird ohne diesen Sensor scharf und du erhältst einen Hinweis. Sobald der Sensor schließt, wird er wieder überwacht.\n• Warten, bis geschlossen: Die Alarmanlage wird scharf und dieser Sensor wird ignoriert, bis er einmal geschlossen hat, ohne Hinweis. Danach wird er wieder überwacht.\n• Scharfschalten verweigern: Die Alarmanlage wird nicht scharf und du siehst, welcher Sensor offen ist. Schließe ihn zuerst.\n• Eingangsverzögerung starten: Die Alarmanlage wird scharf und der offene Sensor gilt sofort als ausgelöst. Ein direkter Sensor löst den Alarm aus, ein verzögerter Sensor startet die Eingangsverzögerung.",
      "tamper_entity": "Hat dieses Gerät auch einen Sabotagekontakt? Wähle ihn hier aus. Vigil legt dafür selbst einen Sabotagesensor an: immer überwachend, mit eigenem Überbrückungsschalter. Du musst ihn nicht separat hinzufügen."
    },
    "moreInfo": "Weitere Informationen",
    "help": {
      "duress_code": "Ein zweiter Code für den Fall, dass dich jemand zwingt, die Alarmanlage auszuschalten. Er schaltet die Anlage wie gewohnt unscharf und nichts ist zu sehen: Die Sirene bleibt still. Währenddessen geht eine stille Nachricht an die Kanäle mit der Nachrichtenart Zwang. Er muss sich von allen anderen Codes unterscheiden.",
      "permanent_bypass": "Wenn du diesen Sensor von Hand überbrückst, bleibt er auch nach dem Unscharfschalten überbrückt, bis du ihn selbst wiederherstellst. Praktisch für einen Sensor, der schon länger defekt ist. Ohne dieses Häkchen endet die Überbrückung beim Unscharfschalten. Brand- und Gassensoren können nie überbrückt werden.",
      "chime": "Wenn sich der Sensor bei unscharfer Anlage öffnet, ertönt ein kurzer Ton über das, was du in den Einstellungen gewählt hast. Kein Alarm, keine Nachricht, kein Protokolleintrag. Bei scharfer Anlage geschieht nichts.",
      "abort_seconds": "Wer innerhalb dieser Sekunden nach dem Ertönen der Sirene einen gültigen Code eingibt, hat einen Fehlalarm verursacht: Die Sirene stoppt und eine Nachricht „abgebrochen“ geht hinaus. 0 schaltet dies aus. Gilt nicht für Brand, Gas und Sabotage.",
      "chime_entity": "Eine Sirene, ein Schalter, ein Licht, eine Taste oder ein Skript, das einen Ton erzeugt. Du kannst es leer lassen: Das Türgong-Ereignis steht weiterhin an der Ereignis-Entität, für eine eigene Automatisierung (zum Beispiel eine Nachricht auf einem Lautsprecher).",
      "chime_seconds": "Wie lange eine Sirene, ein Schalter oder ein Licht eingeschaltet bleibt. Keine Wirkung bei einer Taste oder einem Skript.",
      "may_bypass": "Ohne dieses Recht kann der Benutzer einen Sensor weder überbrücken noch wiederherstellen, auch nicht mit einem richtigen Code. Ein Home-Assistant-Administrator darf es immer.",
      "screen_off_seconds": "Gilt für alle ESPHome-Bedienteile. Bei einem halb eingegebenen Code oder einer offenen Liste kehrt das Bedienteil nach dieser Zeit zuerst zur Hauptseite zurück, und nach derselben Zeit wird das Display dunkel.",
      "screen_off_on_alarm": "Aus: Das Display bleibt während eines Alarms an, sodass der ALARM und seine Ursache sichtbar bleiben. An: Das Display wird dann ebenfalls dunkel. Während des Countdowns zum Scharfschalten oder Eintreten wird das Display nie dunkel.",
      "entity_id": "Ein Binärsensor: „an“ bedeutet offen oder Alarm.",
      "tamper_entity": "Optional: der Sabotagekontakt dieses Geräts.",
      "at_arm_open": "Was mit diesem Sensor geschieht, wenn er beim Scharfschalten noch offen ist.",
      "type": "Sofort: Alarm sofort. Verzögert: erst Eingangsverzögerung. Folgesensor: löst nur aus, wenn zuvor ein verzögerter Sensor geöffnet wurde.",
      "sensor_groups": "Ein Sensor kann in mehreren Gruppen sein. Er überwacht in jedem Modus, in dem eine seiner Gruppen aktiv ist.",
      "suggest_for": "Optional. Ein neuer Sensor dieser Art (Türkontakt oder Bewegung) wird automatisch in diese Gruppe aufgenommen.",
      "sensors": "Nur sofortige Einbruchsensoren.",
      "code": "Leer lassen, um es unverändert zu lassen.",
      "device": "ESPHome-Bedienteil: ein Display mit eigener Firmware, erkannt am Namen des ESPHome-Geräts. Tablet oder Handy: ein Gerät mit der Home-Assistant-App oder dem Browser, erkannt am Konto, mit dem es angemeldet ist.",
      "ha_user": "Für ein Tablet oder Handy: das Konto, mit dem das Gerät angemeldet ist. Vigil erkennt das Gerät an diesem Konto, nicht an einem Text, deshalb kann es nicht nachgeahmt werden. Ein Administrator kann auch gewählt werden, aber beachte: Die Einstellungen dieses Bedienteils gelten dann für alles, was dieses Konto tut, auf jedem Gerät, auf dem es angemeldet ist, und Vigil gibt dem Konto hier keine Administratorrechte (ein Code ist immer nötig). Besser ist ein zweites, gewöhnliches Konto für den täglichen Gebrauch.",
      "removeCode": "Code entfernen",
      "removeDuress": "Zwangscode entfernen",
      "tags": "Tags haben keine Funktion: bediene die Alarmanlage mit einem Code.",
      "categories": "Wähle, welche Nachrichten dieser Kanal erhält.",
      "service": "Ein Notify-Dienst (etwa mobile_app_phone oder eine Gruppe aus YAML) oder eine Notify-Entität (etwa notify.family, eine Notify-Gruppe, die du als Helfer erstellt hast). Eine Notify-Entität erhält nur Titel und Nachricht: Der kritische Alarm der hohen Priorität funktioniert damit nicht, ebenso wenig die Schaltfläche in der Testnachricht der Selbstprüfung. Wähle dafür auf einem Handy den eigenen mobile_app_…-Dienst.",
      "priority": "Nur für Handys mit der Home-Assistant-App (ein mobile_app_…-Dienst): Ein Alarm wird dann auf iOS als kritische Meldung und auf Android mit hoher Priorität gesendet. Bei einer Notify-Entität oder einem anderen Dienst bewirkt dies nichts.",
      "delay": "Nur Alarme: erst warten, zum Beispiel um ein zweites Gerät erst nach einer Weile zu benachrichtigen.",
      "profiles": "Ton und Lautstärke pro Ursache (optional)",
      "preset": "Füllt Ton, Lautstärke und Dauer für eine bekannte Sirene aus. Wähle zuerst die An/Aus-Entität unter „Sirene“, dann sucht Vigil die anderen Entitäten desselben Geräts. Alles bleibt bearbeitbar.",
      "presetFound": "Auf diesem Gerät gefunden:",
      "presetNoneFound": "Keine weiteren Entitäten auf diesem Gerät gefunden; wähle sie selbst.",
      "presetNoControl": "Werte ausgefüllt. Wähle die Sirenen-Entität und wähle die Voreinstellung erneut, um die anderen Entitäten zu suchen.",
      "power_battery_value": "Der Wert der Entität für den Energiemodus, wenn die Sirene im Batteriebetrieb läuft."
    },
    "opt": {
      "preset": {
        "": "—",
        "sonoff_snzb_09p_z2m": "Sonoff SNZB-09P (Zigbee2MQTT)"
      },
      "cls": {
        "intrusion": "Einbruch",
        "fire": "Feuer",
        "gas": "Gas",
        "tamper": "Sabotage",
        "water": "Wasser",
        "alarm24": "24 Stunden, hörbar",
        "silent24": "24 Stunden, still"
      },
      "type": {
        "instant": "Sofort",
        "delayed": "Verzögert (Eingangsverzögerung)",
        "follower": "Folgesensor"
      },
      "at_arm_open": {
        "bypass": "Überbrücken mit Hinweis",
        "wait_clear": "Warten, bis geschlossen",
        "refuse": "Scharfschalten verweigern",
        "pending": "Eingangsverzögerung starten"
      },
      "gas_type": {
        "co": "Kohlenmonoxid",
        "natural_gas": "Erdgas",
        "lpg": "Flüssiggas",
        "other": "Andere"
      },
      "on_unavailable": {
        "default": "Klassenstandard",
        "block": "Scharfschalten blockieren",
        "notify": "Nur benachrichtigen",
        "trigger": "Alarm auslösen",
        "bypass": "Trotzdem scharf schalten (überbrücken)"
      },
      "categories": {
        "alarm": "Alarm",
        "pending": "Eingangsverzögerung",
        "arming": "Scharf- und Unscharfschalten",
        "fault": "Störungen und Hinweise",
        "technical": "Technische Alarme (Wasser)",
        "duress": "Zwang (stiller Alarm)"
      },
      "causes": {
        "intrusion": "Einbruch",
        "fire": "Feuer",
        "gas": "Gas",
        "tamper": "Sabotage",
        "fault": "Sensorstörung"
      },
      "cause": {
        "intrusion": "Einbruch",
        "fire": "Feuer",
        "gas": "Gas",
        "tamper": "Sabotage",
        "alarm24": "24-Stunden-Alarm"
      },
      "mode": {
        "home": "Zuhause",
        "away": "Abwesend",
        "night": "Nacht",
        "vacation": "Urlaub",
        "custom": "Benutzerdefiniert"
      },
      "suggest_for": {
        "": "Keine",
        "contacts": "Türen und Fenster (Kontakte)",
        "motion": "Bewegung"
      },
      "language": {
        "nl": "Nederlands",
        "en": "English",
        "de": "Deutsch",
        "fr": "Français",
        "it": "Italiano",
        "es": "Español"
      },
      "device": {
        "esphome": "ESPHome-Bedienteil (selbstgebautes Display)",
        "account": "Tablet oder Handy mit Home Assistant"
      },
      "sensor_list": {
        "always": "Immer anzeigen",
        "code": "Nur nach dem Entsperren",
        "never": "Nie anzeigen"
      }
    },
    "why": {
      "title": "Warum kann ich nicht scharf schalten?",
      "intro": "Das verhindert gerade das Scharfschalten:",
      "modes": "in {modes}",
      "show": "Anzeigen",
      "bypass": "Überbrücken",
      "bypassed": "Überbrückt",
      "neverBypass": "Brand- und Gassensoren können nicht überbrückt werden: Beseitige zuerst die Ursache.",
      "reason": {
        "alarm_condition": "ist offen (ein Alarmzustand)",
        "sensor_unavailable": "antwortet nicht (und ist so eingestellt, dass er das Scharfschalten verhindert)",
        "sensor_open": "ist offen und muss zum Scharfschalten geschlossen werden",
        "not_disarmed": "die Alarmanlage ist bereits scharf"
      },
      "hint": "Am Bedienteil und in der Vigil-Karte überbrückt und schaltet die Schaltfläche „Überbrücken und scharf schalten“ in einem Zug, wenn du das Recht dazu hast."
    },
    "backup": {
      "intro": "Bei jeder Änderung bewahrt Vigil die Konfiguration, wie sie vor dieser Änderung war (die letzten 10 Versionen). Du kannst eine solche Version zurückspielen; Wiederherstellen ist ebenfalls eine Änderung, lässt sich also auf dieselbe Weise rückgängig machen. Nur die Einstellungen werden aufbewahrt, nicht der Zustand der Alarmanlage (scharf, überbrückt).",
      "list": "Aufbewahrte Versionen",
      "none": "Noch keine Versionen. Sie erscheinen, sobald du etwas änderst.",
      "restore": "Wiederherstellen",
      "reason": {
        "edit": "Änderung",
        "restore": "Wiederhergestellt",
        "import": "Importieren",
        "external": "Außerhalb des Bedienfelds geändert",
        "upgrade": "Vigil-Update"
      },
      "colTime": "Zeit",
      "colReason": "Grund",
      "colVigil": "Vigil-Version",
      "colChange": "Änderung",
      "view": "Ansehen",
      "viewTitle": "Änderung vom {time}",
      "viewText": "Diese Version bewahrt die Konfiguration, wie sie vor dieser Änderung war. Die Änderung selbst war:",
      "format": "Speicherversion {v}",
      "notRestorable": "Kann nicht wiederhergestellt werden: von einer anderen Speicherversion erstellt ({v}, jetzt {now}). Sie kann weiterhin angesehen werden.",
      "settingsList": "Einstellungen: {names}",
      "restoreTitle": "Diese Version wiederherstellen?",
      "restoreText": "Das Wiederherstellen ändert im Vergleich zu jetzt Folgendes:",
      "nothing": "Kein Unterschied zu jetzt.",
      "restored": "Wiederhergestellt",
      "fileTitle": "Export und Import",
      "export": "Konfiguration exportieren",
      "import": "Konfiguration importieren…",
      "exportNote": "Die Datei enthält keine Codes, aber die gehashten Codes, die Heartbeat-Adresse und die Namen deiner Benachrichtigungsdienste. Bewahre sie sicher auf.",
      "importNote": "Beim Import wird die gesamte Konfiguration ersetzt. Die aktuelle wird als Version aufbewahrt, sodass ein Import wiederhergestellt werden kann.",
      "importTitle": "Diese Datei importieren?",
      "importText": "Der Import ändert im Vergleich zu jetzt Folgendes:",
      "imported": "Importiert",
      "readFailed": "Diese Datei kann nicht gelesen werden.",
      "added": "hinzugefügt",
      "removed": "entfernt",
      "changed": "geändert",
      "settings": "Geänderte Einstellungen: {n}",
      "undo": "Rückgängig",
      "apply": "Anwenden"
    },
    "errors": {
      "backup_invalid": "Diese Datei oder Version enthält keine verwendbare Konfiguration.",
      "backup_unknown": "Diese Version existiert nicht mehr.",
      "import_not_vigil": "Das ist keine Vigil-Alarm-Exportdatei.",
      "import_format_version": "Diese Datei hat ein unbekanntes Format.",
      "import_entry_version": "Diese Datei gehört zu einer anderen Speicherversion ({found}, benötigt: {expected}). Importiere sie in derselben Vigil-Version, in der sie erstellt wurde.",
      "name_required": "Gib einen Namen ein.",
      "name_in_use": "Dieser Name existiert bereits.",
      "required": "Erforderlich.",
      "invalid_config": "Ungültig: {error}",
      "sensor_not_instant": "Nur sofortige Sensoren können in einer Bestätigungsregel sein. Ändere: {sensors}",
      "entity_in_use": "Diese Entität ist bereits ein Sensor.",
      "tamper_same_entity": "Die Sabotage-Entität muss eine andere sein als der Sensor selbst.",
      "tamper_entity_in_use": "Diese Entität ist bereits ein Sensor.",
      "no_sensor_group": "Wähle mindestens eine Sensorgruppe.",
      "unknown_sensor_group": "Unbekannte Sensorgruppe.",
      "unknown_mode": "Unbekannter Modus.",
      "unknown_suggestion": "Unbekannte Auswahl.",
      "backup_versions_range": "Wähle eine Zahl von {min} bis {max}.",
      "code_in_use": "Dieser Code wird bereits verwendet.",
      "code_too_short": "Der Code muss mindestens {min} Zeichen haben (unter Einstellungen festgelegt).",
      "code_length_range": "Wähle einen Wert von {min} bis {max}.",
      "screen_off_range": "Wähle eine Anzahl Sekunden von {min} bis {max}.",
      "startup_wait_range": "Wähle eine Anzahl Sekunden von {min} bis {max}.",
      "lock_tries_range": "Wähle eine Anzahl von {min} bis {max}.",
      "lock_wait_range": "Wähle eine Anzahl Minuten von {min} bis {max}.",
      "log_retention_range": "Wähle eine Anzahl Tage von {min} bis {max}.",
      "selftest_range": "Wähle einen Wert von {min} bis {max}.",
      "selftest_window": "Die späteste Uhrzeit muss nach der frühesten liegen.",
      "heartbeat_url_invalid": "Das ist keine Webadresse. Sie muss mit http:// oder https:// beginnen.",
      "heartbeat_range": "Wähle eine Anzahl Minuten von {min} bis {max}.",
      "tag_in_use": "Dieser Tag wird bereits verwendet.",
      "no_credential": "Gib einen Code oder mindestens einen Tag ein.",
      "duress_needs_code": "Ein Zwangscode gehört zu einem gewöhnlichen Code: Gib zuerst einen Code ein.",
      "duress_no_channel": "Es gibt keinen Benachrichtigungskanal mit der Nachrichtenart Zwang. Ohne einen erreicht ein stiller Alarm niemanden. Lege zuerst einen an.",
      "seconds_range": "Wähle eine Anzahl Sekunden von {min} bis {max}.",
      "chime_entity_domain": "Wähle eine Sirene, einen Schalter, ein Licht, eine Taste oder ein Skript.",
      "service_not_found": "Dieser Notify-Dienst existiert (nicht mehr).",
      "no_categories": "Wähle mindestens eine Nachrichtenart.",
      "no_causes": "Wähle mindestens eine Ursache.",
      "tone_without_entity": "Ein Ton braucht eine Entität zur Tonauswahl.",
      "volume_without_entity": "Eine Lautstärke braucht eine Lautstärke-Entität.",
      "sensor_in_rule": "Dieser Sensor ist noch in Bestätigungsregel: {rules}. Entferne ihn zuerst dort.",
      "sensor_group_in_use": "Diese Sensorgruppe wird noch verwendet von: {sensors}. Entferne die Gruppe zuerst aus diesen Sensoren.",
      "no_modes": "Wähle mindestens einen Modus.",
      "unknown_kind": "Unbekanntes Element.",
      "panel_id_invalid": "Verwende Kleinbuchstaben, Ziffern, - und _ (wie der Gerätename in ESPHome).",
      "panel_id_in_use": "Diese Bedienteil-ID ist bereits registriert.",
      "unlock_range": "Wähle einen Wert von {low} bis {high}.",
      "unknown_choice": "Unbekannte Auswahl.",
      "ha_user_unknown": "Dieser Benutzer existiert nicht oder ist nicht aktiv.",
      "ha_user_in_use": "Dieser Benutzer ist bereits an ein anderes Bedienteil gebunden.",
      "generic": "Etwas ist schiefgegangen."
    }
  },
  fr: {
    "title": "Vigil Alarm",
    "tamperShort": "sabotage",
    "about": {
      "details": "Détails",
      "aboutIntro": "Un système d'alarme modulaire pour Home Assistant.",
      "version": "Version",
      "license": "Licence",
      "author": "Auteur",
      "links": "Liens",
      "manual": "Guide d'utilisation",
      "manualOther": "Guide d'utilisation (Nederlands)",
      "repository": "Projet GitHub",
      "releases": "Versions sur GitHub",
      "issues": "Signaler un problème ou partager une idée",
      "panelDocs": "Clavier tactile (ESPHome)",
      "licenseText": "Texte de la licence",
      "notes": "Notes de version",
      "notesOnlyEnglish": "",
      "noNotes": "Aucune note de version trouvée.",
      "system": "Système",
      "haVersion": "Home Assistant",
      "python": "Python",
      "alarmState": "État de l'alarme",
      "items": "Éléments",
      "copyInfo": "Copier les détails pour un signalement",
      "copied": "Copié",
      "copyFailed": "La copie a échoué",
      "disclaimer": "Vigil Alarm n'est pas un système d'alarme certifié. Testez-le régulièrement et ne vous y fiez pas comme seule protection.",
      "unreleased": "Pas encore publiée",
      "firstRelease": "première version"
    },
    "tabs": {
      "overview": "Aperçu",
      "sensor": "Capteurs",
      "sensor_group": "Groupes de capteurs",
      "rule": "Règles de confirmation",
      "user": "Utilisateurs",
      "notification": "Notifications",
      "siren": "Sirènes",
      "log": "Journal",
      "settings": "Paramètres",
      "backup": "Sauvegarde",
      "about": "À propos",
      "panel": "Claviers"
    },
    "add": {
      "sensor": "Ajouter un capteur",
      "sensor_group": "Ajouter un groupe de capteurs",
      "rule": "Ajouter une règle de confirmation",
      "user": "Ajouter un utilisateur",
      "notification": "Ajouter une notification",
      "siren": "Ajouter une sirène",
      "panel": "Ajouter un clavier"
    },
    "edit": {
      "sensor": "Modifier le capteur",
      "sensor_group": "Modifier le groupe de capteurs",
      "rule": "Modifier la règle de confirmation",
      "user": "Modifier l'utilisateur",
      "notification": "Modifier la notification",
      "siren": "Modifier la sirène",
      "panel": "Modifier le clavier"
    },
    "intro": {
      "sensor": "Un seul détecteur, comme un contact de porte, un détecteur de mouvement ou un détecteur de fumée. Pour un capteur d'intrusion, vous choisissez dans quels groupes de capteurs il se trouve. Les capteurs d'incendie, de gaz, d'eau et de sabotage surveillent toujours et n'ont pas besoin de groupe de capteurs. Il en va de même pour 24 heures, sonore (un bouton d'urgence, la porte d'un abri : une alarme avec sirène, même alarme désactivée) et 24 heures, silencieux (un congélateur ou un détecteur de fuite : seulement un message et une ligne dans le journal).",
      "sensor_group": "Un groupe de capteurs détermine dans quels modes les capteurs qu'il contient surveillent. Par exemple : Périmètre (portes et fenêtres) pour Maison, Absent et Nuit, et Intérieur (mouvement) pour Absent uniquement.",
      "rule": "Une alarme ne suit que si le nombre indiqué de capteurs différents se déclenche dans la fenêtre de temps. Utile contre une fausse alarme due à un seul détecteur de mouvement.",
      "user": "Les personnes qui peuvent utiliser l'alarme avec un code. Le code indique qui agit ; les appareils autorisés à agir se règlent sous Claviers.",
      "notification": "Qui reçoit des messages et quand. Chaque notification correspond à un service notify.",
      "siren": "Facultatif. Sans sirène, l'alarme fonctionne avec des notifications.",
      "panel": "Un appareil au mur : un clavier ESPHome, ou une tablette ou un téléphone avec son propre compte Home Assistant. Vigil décide de ce que chaque clavier peut faire et des données qu'il reçoit ; le clavier lui-même ne décide de rien. L'identifiant du clavier est le nom de l'appareil ESPHome. Dès qu'un compte est associé, les autres comptes ordinaires ne peuvent plus utiliser l'alarme."
    },
    "empty": {
      "sensor": "Aucun capteur pour l'instant. Ajoutez d'abord un groupe de capteurs s'il n'y en a pas, puis vos capteurs.",
      "sensor_group": "Aucun groupe de capteurs pour l'instant. Un groupe de capteurs détermine dans quels modes les capteurs surveillent.",
      "rule": "Aucune règle de confirmation pour l'instant. Facultatif : une alarme seulement après plusieurs capteurs.",
      "user": "Aucun utilisateur pour l'instant. Sans utilisateur, aucun code n'est nécessaire pour utiliser l'alarme.",
      "notification": "Aucune notification pour l'instant. Ajoutez un service notify pour recevoir des messages.",
      "siren": "Aucune sirène pour l'instant. C'est facultatif ; sans sirène, l'alarme fonctionne avec des notifications.",
      "panel": "Aucun clavier pour l'instant. Sans clavier enregistré, un clavier ESPHome ne reçoit aucun profil et ne commande rien."
    },
    "save": "Enregistrer",
    "cancel": "Annuler",
    "del": "Supprimer",
    "dup": "Copier",
    "editBtn": "Modifier",
    "testBtn": "Tester",
    "close": "Fermer",
    "ready": {
      "title": "Prêt à l'emploi ?",
      "allGood": "Tout est configuré. Testez quand même l'alarme régulièrement.",
      "problem": "À corriger d'abord",
      "advice": "Conseil",
      "go": "Y aller",
      "createGroups": "Créer les groupes par défaut",
      "groupsMade": "Groupes de capteurs créés",
      "addPhone": "Ajouter un téléphone : {name}",
      "phoneAdded": "{name} ajouté ; une notification de test a été envoyée. Est-elle arrivée ?",
      "text": {
        "no_sensors": "Il n'y a pas encore de capteurs. Ajoutez-en ou laissez Vigil les chercher.",
        "no_sensor_groups": "Il n'y a pas encore de groupes de capteurs. Sans groupe, un capteur d'intrusion ne surveille rien. Vigil peut en proposer deux : Périmètre (portes et fenêtres) et Intérieur (mouvement).",
        "mode_unwatched": "Aucun capteur d'intrusion ne surveille dans ce mode : {modes}.",
        "no_user_code": "Il n'y a pas encore d'utilisateur avec un code, donc personne ne peut utiliser l'alarme.",
        "no_notification": "Il n'y a pas encore de canal de notification, vous n'entendrez donc rien quand l'alarme se déclenche. Utilisez par exemple l'application sur votre téléphone.",
        "no_siren": "Il n'y a pas de sirène. L'alarme fonctionne alors uniquement avec des notifications.",
        "battery_missing": "{n} capteurs n'ont pas de capteur de batterie, vous ne saurez donc pas quand une batterie est faible : {names}.",
        "tamper_unlinked": "{n} capteurs ont un contact de sabotage sur le même appareil qui n'est relié à rien : {names}.",
        "panel_firmware": "Le firmware du clavier {name} comprend la version de profil {seen}, Vigil utilise la version {wanted}. Mettez à jour le firmware du clavier."
      }
    },
    "heartbeat": {
      "title": "Signal de vie",
      "off": "Désactivé. Saisissez une adresse de signal de vie sous Paramètres pour démarrer.",
      "lastOk": "Dernier succès",
      "lastFail": "Dernier échec",
      "never": "pas encore",
      "every": "Toutes les {n} minutes",
      "test": "Tester maintenant",
      "ok": "Le signal de vie est arrivé.",
      "failed": "Le signal de vie n'est pas arrivé ({reason}).",
      "reason": {
        "timeout": "aucune réponse en 10 secondes",
        "connection": "pas de connexion"
      },
      "failing": "En échec : {reason}"
    },
    "selftest": {
      "title": "Autotest",
      "last": "Dernier contrôle silencieux",
      "lastSiren": "Dernier test de sirène",
      "next": "Prochain test de sirène",
      "never": "pas encore",
      "off": "Le rappel est désactivé (Paramètres)",
      "noSiren": "Aucune sirène n'est configurée.",
      "overdue": "En retard : le test était dû il y a {days} jours.",
      "test": "Tester la sirène maintenant",
      "started": "La sirène retentit pendant {seconds} secondes.",
      "auto": "Vigil fait retentir la sirène lui-même pendant les heures réglées.",
      "problems": "Canal de notification manquant : {name}"
    },
    "dash": {
      "title": "Tableau de bord",
      "text": "Un tableau de bord avec les entités propres à cette alarme. Copiez-le et collez-le dans un nouveau tableau de bord (Paramètres > Tableaux de bord > nouveau tableau de bord > éditeur de configuration brute).",
      "copy": "Copier le tableau de bord"
    },
    "log": {
      "intro": "Tout ce que Vigil signale comme événement. Le journal conserve {days} jours (voir Paramètres) et ne contient aucun code. Les heures sont dans votre fuseau horaire ; dans les téléchargements, elles sont en UTC au format RFC 3339.",
      "empty": "Rien dans le journal pour l'instant.",
      "cols": {
        "time": "Heure",
        "event": "Événement",
        "item": "Élément",
        "who": "Utilisateur",
        "via": "Via",
        "result": "Résultat",
        "noCode": "inconnu (pas de code)",
        "installer": "code installateur",
        "auto": "automatique"
      },
      "showing": "Les {n} plus récents sur {total}",
      "jsonl": "Télécharger (JSON Lines)",
      "csv": "Télécharger (CSV)",
      "refresh": "Actualiser"
    },
    "summary": {
      "always": "{cls}, toujours actif",
      "instant": "immédiat",
      "delayed": "temporisé ({s} s)",
      "follower": "suiveur",
      "and": "et",
      "watching": "{type}, surveille en {modes}",
      "nowhere": "{type}, ne surveille dans aucun mode"
    },
    "whatsNew": "nouveau",
    "batteryLow": "faible",
    "batteryOk": "ok",
    "copySuffix": " (copie)",
    "permBypass": {
      "title": "Inhibé en permanence",
      "intro": "Ces capteurs sont inhibés et ne surveillent pas, même après la désactivation. Rétablissez-les dès qu'ils sont réparés :",
      "restore": "Rétablir",
      "restored": "Rétabli"
    },
    "memory": {
      "title": "Dernière alarme",
      "running": "L'alarme est toujours en cours.",
      "endedBy": "Désactivée à {time} par {who}.",
      "cancelled": "Annulée comme fausse alarme.",
      "cause": "Cause",
      "first": "Premier capteur",
      "path": "Parcours dans la maison",
      "pathIntro": "Chaque capteur qui s'est ouvert depuis le début de l'alarme jusqu'à sa désactivation, dans l'ordre. Les capteurs qui ne comptaient pas dans ce mode, ou qui étaient inhibés, sont inclus : ensemble, ils montrent où quelqu'un est passé.",
      "time": "Heure",
      "sensor": "Capteur",
      "room": "Pièce",
      "counted": "Compté",
      "notCounted": "Non compté",
      "times": "ouvert {n}×",
      "clear": "Effacer la mémoire d'alarme",
      "cleared": "Mémoire d'alarme effacée",
      "noRoom": "aucune pièce définie",
      "empty": "Aucun capteur ne s'est ouvert (seulement le premier signalement).",
      "steps": "{n} étapes",
      "more": "Seules les {n} premières étapes sont conservées."
    },
    "practice": {
      "chip": "Mode d'entraînement",
      "title": "Entraînement et test",
      "text": "Mode d'entraînement : l'alarme fonctionne comme d'habitude (elle décompte, se déclenche, les claviers l'affichent) mais aucune sirène ne retentit et aucun message n'est envoyé. Tout figure dans le journal, marqué comme entraînement. Il s'arrête après 30 minutes, ou dès que vous désactivez.",
      "start": "Démarrer le mode d'entraînement",
      "stop": "Arrêter le mode d'entraînement",
      "left": "Encore {n} min.",
      "needsOff": "Désactivez d'abord l'alarme.",
      "walk": "Test de parcours : alarme désactivée, longez les portes, les fenêtres et les détecteurs de mouvement ; chaque capteur qui réagit est coché. Seuls les capteurs d'intrusion participent (les capteurs d'incendie, de gaz, d'eau et de sabotage sont toujours actifs et ont leur propre test).",
      "walkStart": "Démarrer le test de parcours",
      "walkTitle": "Test de parcours",
      "walkRunning": "Ouvrez chaque porte ou fenêtre et passez devant chaque détecteur de mouvement. {n} sur {total} vus.",
      "walkStop": "Arrêter le test",
      "walkDone": "Terminé : {seen} sur {total} vus.",
      "walkAgain": "Recommencer",
      "walkMissing": "Non vu",
      "walkReason": {
        "no_response": "n'a pas réagi",
        "unavailable": "est indisponible"
      },
      "walkSeen": "Vu",
      "walkNone": "Tous les capteurs ont réagi.",
      "walkLast": "Dernier test de parcours : {seen} sur {total} vus ({time}).",
      "close": "Fermer"
    },
    "wizard": {
      "title": "Configurer Vigil",
      "button": "Assistant de configuration",
      "step": "Étape {n} sur {total}",
      "back": "Retour",
      "next": "Suivant",
      "skip": "Passer",
      "finish": "Terminé",
      "stop": "Continuer plus tard",
      "resume": "Continuer l'assistant",
      "cardTitle": "Configurer Vigil",
      "cardText": "Tout n'est pas encore configuré. L'assistant vous guide pas à pas ; vous pouvez passer n'importe quelle étape et y revenir plus tard.",
      "start": "Démarrer l'assistant",
      "done": "Terminé",
      "todo": "À faire",
      "optional": "Recommandé",
      "welcome": {
        "title": "Bienvenue dans Vigil",
        "text": "En quelques étapes, vous configurez l'alarme : quels modes vous utilisez, quels capteurs participent, qui reçoit un code et comment vous êtes prévenu. Rien n'est enregistré avant que vous le confirmiez dans une étape, et chaque modification peut être annulée depuis l'onglet Sauvegarde."
      },
      "modes": {
        "title": "Quels modes utilisez-vous ?",
        "text": "Maison (vous êtes là, le périmètre est surveillé), Absent (personne à la maison), Nuit (vous dormez), Vacances (absent longtemps) et Personnalisé (un mode à vous, par exemple seulement le garage). Ne choisissez que ce que vous utilisez vraiment ; les temporisations de sortie peuvent être modifiées plus tard sous Paramètres.",
        "save": "Enregistrer",
        "saved": "Modes enregistrés.",
        "none": "Choisissez au moins un mode."
      },
      "sensors": {
        "title": "Capteurs",
        "text": "Vigil cherche dans Home Assistant des capteurs de porte, de fenêtre, de mouvement, de fumée, de gaz et d'eau. Vous choisissez lesquels ajouter.",
        "have": "{n} capteurs configurés.",
        "none": "Aucun capteur pour l'instant.",
        "find": "Chercher des capteurs",
        "fresh": "{n} nouveaux trouvés."
      },
      "user": {
        "title": "Qui peut utiliser l'alarme ?",
        "text": "Un utilisateur a un code. Vous pouvez créer un utilisateur à partir d'une personne Home Assistant ou en ajouter un à la main.",
        "have": "{n} utilisateur(s) avec un code.",
        "none": "Aucun utilisateur avec un code pour l'instant.",
        "fromPerson": "Faire de {name} un utilisateur",
        "add": "Ajouter un utilisateur"
      },
      "notification": {
        "title": "Où voulez-vous recevoir un message ?",
        "text": "En cas d'alarme ou de défaut, Vigil envoie un message. Un téléphone avec l'application Home Assistant est le plus simple.",
        "have": "{n} canal(aux) de notification.",
        "none": "Aucun canal de notification pour l'instant.",
        "phone": "Ajouter {name}",
        "add": "Ajouter un canal de notification",
        "added": "{name} a été ajouté ; un message de test a été envoyé."
      },
      "siren": {
        "title": "Sirène",
        "text": "Une sirène n'est pas obligatoire, mais sans elle vous n'entendez une alarme que par les messages.",
        "have": "{n} sirène(s).",
        "none": "Aucune sirène pour l'instant.",
        "add": "Ajouter une sirène"
      },
      "panel": {
        "title": "Clavier au mur",
        "text": "Un écran ESPHome, une tablette ou un téléphone peut commander l'alarme. C'est facultatif.",
        "have": "{n} clavier(s).",
        "none": "Aucun clavier pour l'instant.",
        "add": "Associer un clavier"
      },
      "test": {
        "title": "Prêt à l'emploi ?",
        "text": "Voici ce qui manque encore à Vigil. Tout ce qui est marqué « problème » empêche encore l'alarme de protéger.",
        "allGood": "Tout est en ordre.",
        "testSiren": "Tester la sirène",
        "sirenStarted": "La sirène retentit brièvement."
      },
      "end": {
        "title": "Terminé",
        "text": "Vigil est configuré. Un essai : activez l'alarme, ouvrez une porte et voyez si votre message arrive. Ensuite, vous pouvez ajouter des automatisations avec les blueprints fournis (activer automatiquement quand tout le monde part, faire clignoter les lumières lors d'une alarme, énoncer un message). Vous les trouvez dans le guide sous Automatisations et blueprints."
      }
    },
    "newSensors": {
      "title": "Nouveaux capteurs trouvés",
      "text": "Ces capteurs sont apparus dans Home Assistant depuis le dernier passage de Vigil. Rien n'a été ajouté.",
      "review": "Examiner et ajouter",
      "later": "Pas maintenant",
      "badge": "{n} nouveaux",
      "dismissed": "OK, Vigil ne les signalera plus. Vous pouvez toujours les ajouter avec Chercher des capteurs.",
      "onlyNew": "Seuls les nouveaux capteurs sont affichés.",
      "showAll": "Afficher tous les capteurs",
      "showNew": "Afficher seulement les nouveaux"
    },
    "find": {
      "button": "Chercher des capteurs",
      "title": "Chercher des capteurs",
      "intro": "Ces capteurs ont été trouvés dans Home Assistant. Choisissez lesquels ajouter. Rien n'est enregistré avant que vous appuyiez sur le bouton en bas.",
      "none": "Aucun nouveau capteur trouvé. Les capteurs de porte, de fenêtre, de mouvement, de fumée, de gaz, d'eau et de sabotage d'un appareil intégré sont affichés.",
      "noGroups": "Certains capteurs d'intrusion n'ont pas encore de groupe de capteurs. Réglez « Proposer pour les nouveaux capteurs » d'un groupe de capteurs sur contacts ou mouvement ; vous pourrez alors les ajouter ici.",
      "cols": {
        "name": "Nom",
        "cls": "Classe",
        "entrance": "Entrée",
        "groups": "Groupes de capteurs",
        "extra": "Inclus"
      },
      "entranceHelp": "Une entrée reçoit une temporisation d'entrée (type « temporisé »).",
      "inUse": "déjà utilisé",
      "needsGroup": "aucun groupe de capteurs",
      "battery": "batterie",
      "tamper": "sabotage",
      "all": "Tout sélectionner",
      "nothing": "Tout désélectionner",
      "add": "Ajouter {n}",
      "adding": "Ajout en cours…",
      "copy": "Copier les données de détection",
      "copyHelp": "Une liste anonyme sans noms ni adresses, pour un signalement ou pour aider à tester une intégration.",
      "createGroups": "Créer les groupes par défaut",
      "added": "{n} capteurs ajoutés",
      "failed": "{name} : {error}"
    },
    "confirmDelete": "Voulez-vous vraiment supprimer « {name} » ?",
    "saved": "Enregistré",
    "deleted": "Supprimé",
    "testSent": "Test envoyé",
    "loading": "Chargement…",
    "loadFailed": "Vigil Alarm n'a pas pu être chargé. L'intégration fonctionne-t-elle ?",
    "retry": "Réessayer",
    "sections": {
      "alarm": {
        "0": "Modes et temporisations",
        "1": "Quels modes vous utilisez, combien de temps vous avez pour sortir et pour entrer, et combien de temps dure l'alarme."
      },
      "chime": {
        "0": "Carillon",
        "1": "Un bref son quand un capteur dont la case Carillon est cochée s'ouvre alors que l'alarme est désactivée."
      },
      "codes": {
        "0": "Codes",
        "1": "Si un code est nécessaire pour activer et quelle longueur minimale doit avoir un code."
      },
      "startup": {
        "0": "Démarrage",
        "1": "Après un redémarrage de Home Assistant, Vigil attend que tous vos capteurs soient disponibles (par exemple MQTT ou Zigbee encore en démarrage) avant de signaler un capteur comme perdu ou de déclencher une alarme pour lui. S'ils sont toujours absents après ce délai, le signalement suit."
      },
      "lock": {
        "0": "Verrouillage",
        "1": "Ce qui se passe après de mauvais codes, par clavier : d'abord un court verrouillage, puis de plus longs, puis un verrouillage permanent qui ne disparaît qu'avec Lever le verrouillage sous Claviers. Un bon code repart de zéro."
      },
      "screen": {
        "0": "Écran du clavier",
        "1": "Quand l'écran d'un clavier ESPHome s'éteint. Il ne s'éteint que lorsque l'alarme est désactivée ou entièrement activée, jamais pendant le décompte d'activation ou de désactivation."
      },
      "battery": {
        "0": "Batteries",
        "1": "À partir de quel niveau une batterie compte comme faible."
      },
      "log": {
        "0": "Journal des événements",
        "1": "Combien de temps Vigil conserve les événements."
      },
      "backup": {
        "0": "Sauvegarde",
        "1": "Combien de versions de votre configuration Vigil conserve (onglet Sauvegarde). Une valeur plus basse supprime les plus anciennes versions."
      },
      "selftest": {
        "0": "Autotest",
        "1": "Vigil vous rappelle de tester la sirène. Réglez l'intervalle sur 0 pour désactiver le rappel."
      },
      "heartbeat": {
        "0": "Signal de vie",
        "1": "Vigil appelle régulièrement cette adresse, afin qu'un service extérieur à votre maison signale quand Home Assistant ou votre internet s'arrête."
      }
    },
    "reloadNote": "L'enregistrement recharge Vigil Alarm (l'état de l'alarme est conservé).",
    "alarm": "Alarme",
    "problems": "Attention",
    "noProblems": "Aucun problème",
    "sensorsNow": "Capteurs en ce moment",
    "coverage": "Ce que surveille chaque mode",
    "coverageNothing": "aucun groupe de capteurs : rien n'est surveillé",
    "alwaysOn": "Toujours actif",
    "sensorsCount": "{n} capteurs",
    "state": {
      "disarmed": "Désactivée",
      "arming": "Activation",
      "armed": "Activée",
      "pending": "Temporisation d'entrée",
      "triggered": "ALARME"
    },
    "mode": {
      "home": "Maison",
      "away": "Absent",
      "night": "Nuit",
      "vacation": "Vacances",
      "custom": "Personnalisé"
    },
    "zstatus": {
      "closed": "Fermé",
      "open": "Ouvert",
      "unavailable": "Injoignable",
      "bypassed": "Inhibé",
      "bypassed_at_arm": "Inhibé à l'activation",
      "waiting": "Attend la fermeture"
    },
    "problem": {
      "battery_low": "batterie faible",
      "unavailable": "injoignable",
      "on_battery": "pas de courant secteur"
    },
    "cols": {
      "name": "Nom",
      "entity": "Entité",
      "cls": "Classe",
      "type": "Type",
      "groups": "Groupes de capteurs",
      "rule": "Règle de confirmation",
      "status": "Statut",
      "battery": "Batterie",
      "modes": "Actif dans les modes",
      "sensors": "Capteurs",
      "suggest": "Proposé pour",
      "condition": "Condition",
      "escalate": "Signaler si non confirmé",
      "code": "Code",
      "duress": "Code de contrainte",
      "tags": "Badges",
      "bypass": "Inhiber",
      "tamper": "Peut inhiber le sabotage",
      "service": "Service",
      "categories": "Catégories",
      "delay": "Temporisation",
      "device": "Appareil",
      "causes": "Pour",
      "maxdur": "Durée max.",
      "panelId": "ID du clavier",
      "conn": "Connexion",
      "allowed": "Restrictions"
    },
    "panel": {
      "tablet": "Compte",
      "noUser": "utilisateur introuvable",
      "connected": "Connecté",
      "offline": "Injoignable",
      "noConnection": "Pas de connexion",
      "noCard": "Aucune carte Vigil vue",
      "cardSeen": "Carte Vigil active",
      "notFound": "Introuvable dans ESPHome",
      "unlocked": "Déverrouillé",
      "locked": "Verrouillé pendant {s} s",
      "lockedPermanent": "Verrouillé définitivement",
      "blocked": "Bloqué",
      "notWatched": "Non surveillé",
      "unlock": "Déverrouiller",
      "unlockedDone": "Déverrouillé pendant {s} secondes.",
      "clear": "Lever le verrouillage",
      "cleared": "Verrouillage levé.",
      "nothingLocked": "Ce clavier n'était pas verrouillé.",
      "all": "tous les modes",
      "noDisarm": "pas de désactivation",
      "noBypass": "pas d'inhibition",
      "noSilence": "pas de mise en sourdine",
      "hint": "Déverrouiller et lever le verrouillage ne peut se faire qu'ici, pas comme action Home Assistant.",
      "refused": "Ce n'est pas possible."
    },
    "yes": "oui",
    "no": "non",
    "none": "—",
    "immediately": "immédiatement",
    "condition": "{n} en {s} s",
    "fields": {
      "name": "Nom",
      "entity_id": "Entité (capteur binaire)",
      "cls": "Classe",
      "type": "Type",
      "sensor_groups": "Groupes de capteurs",
      "at_arm_open": "Si ouvert à la fin de la temporisation de sortie",
      "entry_delay": "Temporisation d'entrée (vide = par défaut)",
      "gas_type": "Type de gaz",
      "on_unavailable": "Quand le capteur devient injoignable",
      "battery_entity": "Capteur de batterie",
      "tamper_entity": "Entité de sabotage (facultatif)",
      "chime": "Carillon : son quand ce capteur s'ouvre alors que l'alarme est désactivée",
      "permanent_bypass": "Conserver l'inhibition après la désactivation (permanent)",
      "duress_code": "Code de contrainte (facultatif)",
      "sensor_group.modes": "Actif dans les modes",
      "suggest_for": "Proposer pour les nouveaux capteurs",
      "sensors": "Capteurs",
      "required": "Capteurs nécessaires",
      "window": "Fenêtre de temps",
      "escalate": "Signaler si non confirmé",
      "code": "Code",
      "tags": "Badges (séparés par des virgules)",
      "allowed_modes": "Peut commander dans les modes (vide = tous)",
      "may_bypass": "Peut inhiber des capteurs",
      "may_bypass_tamper": "Peut inhiber le sabotage",
      "service": "Service notify",
      "categories": "Types de messages",
      "delay": "Temporisation",
      "priority": "Priorité haute",
      "control": "Sirène (sirène, interrupteur ou lumière)",
      "causes": "Retentit pour",
      "max_duration": "Durée maximale (0 = jusqu'à la désactivation)",
      "repeat_every": "Répéter toutes les (0 = non)",
      "light": "Faire clignoter la lumière",
      "tone_entity": "Entité de sélection du son",
      "volume_entity": "Entité du volume",
      "power_entity": "Entité du mode d'alimentation",
      "power_battery_value": "Valeur sur batterie",
      "tone": "Son",
      "volume": "Volume",
      "preset": "Préréglage",
      "device": "Type d'appareil",
      "panel_id": "Nom de l'appareil ESPHome (ID du clavier)",
      "ha_user": "Compte Home Assistant (tablette ou téléphone)",
      "language": "Langue",
      "can_disarm": "Peut désactiver (avec un code)",
      "can_bypass": "Peut inhiber des capteurs (avec un code)",
      "can_silence": "Peut couper le son et acquitter",
      "sensor_list": "Afficher la liste des capteurs",
      "unlock_seconds": "Reste déverrouillé pendant (secondes)",
      "watch": "Surveiller si ce clavier est joignable (notifier en cas de perte)",
      "blocked": "Clavier bloqué",
      "panel.code": "Code installateur de ce clavier (vide = aucun)",
      "panel.allowed_modes": "Peut activer dans les modes (vide = tous)",
      "s.modes": "Modes disponibles",
      "exit_delay_home": "Temporisation de sortie Maison",
      "exit_delay_away": "Temporisation de sortie Absent",
      "exit_delay_night": "Temporisation de sortie Nuit",
      "exit_delay_vacation": "Temporisation de sortie Vacances",
      "exit_delay_custom": "Temporisation de sortie Personnalisé",
      "default_entry_delay": "Temporisation d'entrée par défaut",
      "trigger_time": "Durée de l'alarme (0 = jusqu'à la désactivation)",
      "abort_seconds": "Fenêtre d'annulation après le déclenchement de la sirène (secondes, 0 = désactivé)",
      "chime_entity": "Carillon : ce qui produit le son",
      "chime_seconds": "Le carillon retentit pendant (secondes)",
      "battery_threshold": "Seuil de batterie",
      "backup_versions": "Nombre de versions conservées",
      "code_arm_required": "Code requis pour activer",
      "startup_wait_seconds": "Attente maximale des capteurs après un redémarrage (secondes)",
      "lock_tries_1": "Mauvais codes avant le premier verrouillage",
      "lock_wait_1": "Le premier verrouillage dure (minutes)",
      "lock_tries_2": "Puis mauvais codes avant le deuxième verrouillage",
      "lock_wait_2": "Le deuxième verrouillage dure (minutes)",
      "lock_tries_3": "Puis mauvais codes avant le troisième verrouillage",
      "lock_wait_3": "Le troisième verrouillage dure (minutes)",
      "lock_tries_4": "Puis mauvais codes avant le verrouillage permanent",
      "screen_off_seconds": "Extinction de l'écran après (secondes sans toucher)",
      "screen_off_on_alarm": "Éteindre aussi l'écran pendant une alarme",
      "log_retention_days": "Conserver le journal (jours)",
      "selftest_interval_days": "Rappel du test de sirène (jours, 0 = désactivé)",
      "selftest_siren_seconds": "La sirène retentit pendant un test (secondes)",
      "selftest_auto": "Faire retentir la sirène seul pour le test",
      "selftest_window_start": "Pas avant (heure)",
      "selftest_window_end": "Pas après (heure)",
      "heartbeat_url": "Adresse du signal de vie (vide = désactivé)",
      "heartbeat_interval_minutes": "Minutes entre les signaux de vie",
      "min_code_length": "Longueur minimale du code (caractères)"
    },
    "helpMore": {
      "at_arm_open": "Ce qui se passe si ce capteur est encore ouvert à la fin de la temporisation de sortie :\n• Inhiber avec un avis (par défaut) : l'alarme s'active sans ce capteur et vous recevez un avis. Dès que le capteur se ferme, il est de nouveau surveillé.\n• Attendre la fermeture : l'alarme s'active et ce capteur est ignoré jusqu'à ce qu'il se soit fermé une fois, sans avis. Ensuite, il est de nouveau surveillé.\n• Refuser l'activation : l'alarme ne s'active pas et vous voyez quel capteur est ouvert. Fermez-le d'abord.\n• Démarrer la temporisation d'entrée : l'alarme s'active et le capteur ouvert compte aussitôt comme déclenché. Un capteur direct déclenche l'alarme, un capteur temporisé démarre la temporisation d'entrée.",
      "tamper_entity": "Cet appareil a-t-il aussi un contact de sabotage ? Choisissez-le ici. Vigil ajoute de lui-même un capteur de sabotage : toujours à l'écoute, avec son propre interrupteur d'inhibition. Vous n'avez pas besoin de l'ajouter séparément."
    },
    "moreInfo": "Plus d'informations",
    "help": {
      "duress_code": "Un second code pour le cas où quelqu'un vous force à désactiver l'alarme. Il désactive l'alarme comme d'habitude et rien n'apparaît : la sirène reste silencieuse. Pendant ce temps, un message silencieux part vers les canaux avec le type de message Contrainte. Il doit différer de tous les autres codes.",
      "permanent_bypass": "Si vous inhibez ce capteur à la main, il reste inhibé après la désactivation de l'alarme, jusqu'à ce que vous le rétablissiez vous-même. Pratique pour un capteur en panne depuis un moment. Sans cette case, l'inhibition prend fin à la désactivation. Les capteurs d'incendie et de gaz ne peuvent jamais être inhibés.",
      "chime": "Quand le capteur s'ouvre alors que l'alarme est désactivée, un bref son est émis par ce que vous avez choisi dans les paramètres. Pas d'alarme, pas de message, rien dans le journal. Quand l'alarme est activée, rien ne se passe.",
      "abort_seconds": "Celui qui saisit un code valide dans ce nombre de secondes après le déclenchement de la sirène a causé une fausse alarme : la sirène s'arrête et un message « annulée » est envoyé. 0 désactive cette fonction. Ne s'applique pas à l'incendie, au gaz et au sabotage.",
      "chime_entity": "Une sirène, un interrupteur, une lumière, un bouton ou un script qui émet un son. Vous pouvez le laisser vide : l'événement Carillon reste sur l'entité d'événement, pour une automatisation à vous (par exemple un message sur un haut-parleur).",
      "chime_seconds": "Combien de temps une sirène, un interrupteur ou une lumière reste allumé. Sans effet pour un bouton ou un script.",
      "may_bypass": "Sans ce droit, l'utilisateur ne peut ni inhiber ni rétablir un capteur, même avec un bon code. Un administrateur Home Assistant le peut toujours.",
      "screen_off_seconds": "S'applique à tous les claviers ESPHome. Avec un code à moitié saisi ou une liste ouverte, le clavier revient d'abord à la page principale après ce délai, et l'écran s'éteint après le même délai.",
      "screen_off_on_alarm": "Désactivé : l'écran reste allumé pendant une alarme, afin que l'ALARME et sa cause restent visibles. Activé : l'écran s'éteint aussi alors. Pendant le décompte d'activation ou d'entrée, l'écran ne s'éteint jamais.",
      "entity_id": "Un capteur binaire : activé signifie ouvert ou alarme.",
      "tamper_entity": "Facultatif : le contact de sabotage de cet appareil.",
      "at_arm_open": "Ce qui arrive à ce capteur s'il est encore ouvert quand l'alarme s'active.",
      "type": "Immédiat : alarme aussitôt. Temporisé : d'abord la temporisation d'entrée. Suiveur : ne déclenche que si un capteur temporisé a été ouvert avant.",
      "sensor_groups": "Un capteur peut appartenir à plusieurs groupes. Il surveille dans chaque mode où l'un de ses groupes est actif.",
      "suggest_for": "Facultatif. Un nouveau capteur de ce type (contact de porte ou mouvement) est placé automatiquement dans ce groupe.",
      "sensors": "Capteurs d'intrusion immédiats uniquement.",
      "code": "Laissez vide pour ne rien changer.",
      "device": "Clavier ESPHome : un écran avec son propre firmware, reconnu par le nom de l'appareil ESPHome. Tablette ou téléphone : un appareil qui exécute l'application ou le navigateur Home Assistant, reconnu par le compte avec lequel il est connecté.",
      "ha_user": "Pour une tablette ou un téléphone : le compte avec lequel l'appareil est connecté. Vigil reconnaît l'appareil par ce compte, pas par un texte, il ne peut donc pas être imité. Un administrateur peut aussi être choisi, mais attention : les réglages de ce clavier s'appliquent alors à tout ce que fait ce compte, sur chaque appareil où il est connecté, et Vigil ne donne ici aucun droit d'administrateur au compte (un code est toujours nécessaire). Un second compte ordinaire pour l'usage quotidien est préférable.",
      "removeCode": "Supprimer le code",
      "removeDuress": "Supprimer le code de contrainte",
      "tags": "Les badges n'ont aucune fonction : commandez l'alarme avec un code.",
      "categories": "Choisissez les messages que ce canal reçoit.",
      "service": "Un service notify (comme mobile_app_phone ou un groupe issu de YAML) ou une entité notify (comme notify.family, un groupe notify créé comme entrée d'aide). Une entité notify reçoit seulement un titre et un message : l'alerte critique de la priorité haute ne fonctionne pas avec elle, ni le bouton du message de test de l'autocontrôle. Pour cela sur un téléphone, choisissez son propre service mobile_app_….",
      "priority": "Uniquement pour les téléphones avec l'application Home Assistant (un service mobile_app_…) : une alarme est alors envoyée comme alerte critique sur iOS et avec priorité haute sur Android. Pour une entité notify ou un autre service, cela ne change rien.",
      "delay": "Alarmes uniquement : attendre d'abord, par exemple pour ne notifier un second appareil qu'après un moment.",
      "profiles": "Son et volume par cause (facultatif)",
      "preset": "Remplit le son, le volume et la durée pour une sirène connue. Choisissez d'abord l'entité marche/arrêt sous « Sirène » et Vigil cherche les autres entités du même appareil. Tout reste modifiable.",
      "presetFound": "Trouvé sur cet appareil :",
      "presetNoneFound": "Aucune autre entité trouvée sur cet appareil ; choisissez-les vous-même.",
      "presetNoControl": "Valeurs remplies. Choisissez l'entité de la sirène et choisissez de nouveau le préréglage pour rechercher les autres entités.",
      "power_battery_value": "La valeur de l'entité du mode d'alimentation quand la sirène fonctionne sur batterie."
    },
    "opt": {
      "preset": {
        "": "—",
        "sonoff_snzb_09p_z2m": "Sonoff SNZB-09P (Zigbee2MQTT)"
      },
      "cls": {
        "intrusion": "Intrusion",
        "fire": "Incendie",
        "gas": "Gaz",
        "tamper": "Sabotage",
        "water": "Eau",
        "alarm24": "24 heures, sonore",
        "silent24": "24 heures, silencieux"
      },
      "type": {
        "instant": "Immédiat",
        "delayed": "Temporisé (temporisation d'entrée)",
        "follower": "Suiveur"
      },
      "at_arm_open": {
        "bypass": "Inhiber avec un avis",
        "wait_clear": "Attendre la fermeture",
        "refuse": "Refuser l'activation",
        "pending": "Démarrer la temporisation d'entrée"
      },
      "gas_type": {
        "co": "Monoxyde de carbone",
        "natural_gas": "Gaz naturel",
        "lpg": "GPL",
        "other": "Autre"
      },
      "on_unavailable": {
        "default": "Valeur par défaut de la classe",
        "block": "Bloquer l'activation",
        "notify": "Notifier seulement",
        "trigger": "Déclencher l'alarme",
        "bypass": "Activer quand même (inhiber)"
      },
      "categories": {
        "alarm": "Alarme",
        "pending": "Temporisation d'entrée",
        "arming": "Activation et désactivation",
        "fault": "Défauts et avis",
        "technical": "Alarmes techniques (eau)",
        "duress": "Contrainte (alarme silencieuse)"
      },
      "causes": {
        "intrusion": "Intrusion",
        "fire": "Incendie",
        "gas": "Gaz",
        "tamper": "Sabotage",
        "fault": "Défaut de capteur"
      },
      "cause": {
        "intrusion": "Intrusion",
        "fire": "Incendie",
        "gas": "Gaz",
        "tamper": "Sabotage",
        "alarm24": "Alarme 24 heures"
      },
      "mode": {
        "home": "Maison",
        "away": "Absent",
        "night": "Nuit",
        "vacation": "Vacances",
        "custom": "Personnalisé"
      },
      "suggest_for": {
        "": "Aucun",
        "contacts": "Portes et fenêtres (contacts)",
        "motion": "Mouvement"
      },
      "language": {
        "nl": "Nederlands",
        "en": "English",
        "de": "Deutsch",
        "fr": "Français",
        "it": "Italiano",
        "es": "Español"
      },
      "device": {
        "esphome": "Clavier ESPHome (écran DIY)",
        "account": "Tablette ou téléphone avec Home Assistant"
      },
      "sensor_list": {
        "always": "Toujours afficher",
        "code": "Seulement après déverrouillage",
        "never": "Ne jamais afficher"
      }
    },
    "why": {
      "title": "Pourquoi ne puis-je pas activer ?",
      "intro": "Ceci empêche l'activation en ce moment :",
      "modes": "en {modes}",
      "show": "Afficher",
      "bypass": "Inhiber",
      "bypassed": "Inhibé",
      "neverBypass": "Les capteurs d'incendie et de gaz ne peuvent pas être inhibés : supprimez d'abord la cause.",
      "reason": {
        "alarm_condition": "est ouvert (une condition d'alarme)",
        "sensor_unavailable": "ne répond pas (et est réglé pour empêcher l'activation)",
        "sensor_open": "est ouvert et doit être fermé pour activer",
        "not_disarmed": "l'alarme est déjà activée"
      },
      "hint": "Sur le clavier et dans la carte Vigil, le bouton Inhiber et activer inhibe et active d'un coup, si vous en avez le droit."
    },
    "backup": {
      "intro": "À chaque modification, Vigil conserve la configuration telle qu'elle était avant cette modification (les 10 dernières versions). Vous pouvez remettre une telle version ; la restauration est aussi une modification, elle peut donc être annulée de la même façon. Seuls les réglages sont conservés, pas l'état de l'alarme (activée, inhibée).",
      "list": "Versions conservées",
      "none": "Pas encore de versions. Elles apparaissent dès que vous modifiez quelque chose.",
      "restore": "Rétablir",
      "reason": {
        "edit": "Modification",
        "restore": "Rétabli",
        "import": "Importer",
        "external": "Modifié en dehors du panneau",
        "upgrade": "Mise à jour de Vigil"
      },
      "colTime": "Heure",
      "colReason": "Raison",
      "colVigil": "Version de Vigil",
      "colChange": "Modification",
      "view": "Voir",
      "viewTitle": "Modification du {time}",
      "viewText": "Cette version conserve la configuration telle qu'elle était avant cette modification. La modification elle-même était :",
      "format": "version de stockage {v}",
      "notRestorable": "Ne peut pas être restaurée : créée par une autre version de stockage ({v}, maintenant {now}). Elle peut toujours être consultée.",
      "settingsList": "Paramètres : {names}",
      "restoreTitle": "Restaurer cette version ?",
      "restoreText": "La restauration modifie ceci par rapport à maintenant :",
      "nothing": "Aucune différence avec maintenant.",
      "restored": "Rétabli",
      "fileTitle": "Exporter et importer",
      "export": "Exporter la configuration",
      "import": "Importer la configuration…",
      "exportNote": "Le fichier ne contient aucun code, mais il contient les codes hachés, l'adresse du signal de vie et les noms de vos services de notification. Conservez-le en lieu sûr.",
      "importNote": "L'import remplace toute la configuration. La configuration actuelle est conservée comme version, un import peut donc être restauré.",
      "importTitle": "Importer ce fichier ?",
      "importText": "L'import modifie ceci par rapport à maintenant :",
      "imported": "Importé",
      "readFailed": "Ce fichier ne peut pas être lu.",
      "added": "ajouté",
      "removed": "supprimé",
      "changed": "modifié",
      "settings": "Paramètres modifiés : {n}",
      "undo": "Annuler",
      "apply": "Appliquer"
    },
    "errors": {
      "backup_invalid": "Ce fichier ou cette version ne contient aucune configuration utilisable.",
      "backup_unknown": "Cette version n'existe plus.",
      "import_not_vigil": "Ce n'est pas un fichier d'export de Vigil Alarm.",
      "import_format_version": "Ce fichier a un format inconnu.",
      "import_entry_version": "Ce fichier appartient à une autre version de stockage ({found}, requise : {expected}). Importez-le dans la même version de Vigil que celle qui l'a créé.",
      "name_required": "Saisissez un nom.",
      "name_in_use": "Ce nom existe déjà.",
      "required": "Obligatoire.",
      "invalid_config": "Invalide : {error}",
      "sensor_not_instant": "Seuls les capteurs immédiats peuvent figurer dans une règle de confirmation. Modifiez : {sensors}",
      "entity_in_use": "Cette entité est déjà un capteur.",
      "tamper_same_entity": "L'entité de sabotage doit être différente du capteur lui-même.",
      "tamper_entity_in_use": "Cette entité est déjà un capteur.",
      "no_sensor_group": "Choisissez au moins un groupe de capteurs.",
      "unknown_sensor_group": "Groupe de capteurs inconnu.",
      "unknown_mode": "Mode inconnu.",
      "unknown_suggestion": "Choix inconnu.",
      "backup_versions_range": "Choisissez un nombre de {min} à {max}.",
      "code_in_use": "Ce code est déjà utilisé.",
      "code_too_short": "Le code doit comporter au moins {min} caractères (réglé sous Paramètres).",
      "code_length_range": "Choisissez une valeur de {min} à {max}.",
      "screen_off_range": "Choisissez un nombre de secondes de {min} à {max}.",
      "startup_wait_range": "Choisissez un nombre de secondes de {min} à {max}.",
      "lock_tries_range": "Choisissez un nombre de fois de {min} à {max}.",
      "lock_wait_range": "Choisissez un nombre de minutes de {min} à {max}.",
      "log_retention_range": "Choisissez un nombre de jours de {min} à {max}.",
      "selftest_range": "Choisissez une valeur de {min} à {max}.",
      "selftest_window": "L'heure la plus tardive doit être après l'heure la plus précoce.",
      "heartbeat_url_invalid": "Ce n'est pas une adresse web. Elle doit commencer par http:// ou https://.",
      "heartbeat_range": "Choisissez un nombre de minutes de {min} à {max}.",
      "tag_in_use": "Ce badge est déjà utilisé.",
      "no_credential": "Saisissez un code ou au moins un badge.",
      "duress_needs_code": "Un code de contrainte accompagne un code ordinaire : saisissez d'abord un code.",
      "duress_no_channel": "Aucun canal de notification n'a le type de message Contrainte. Sans lui, une alarme silencieuse n'atteint personne. Ajoutez-en un d'abord.",
      "seconds_range": "Choisissez un nombre de secondes de {min} à {max}.",
      "chime_entity_domain": "Choisissez une sirène, un interrupteur, une lumière, un bouton ou un script.",
      "service_not_found": "Ce service notify n'existe pas (ou plus).",
      "no_categories": "Choisissez au moins un type de message.",
      "no_causes": "Choisissez au moins une cause.",
      "tone_without_entity": "Un son nécessite une entité de sélection du son.",
      "volume_without_entity": "Un volume nécessite une entité de volume.",
      "sensor_in_rule": "Ce capteur figure encore dans la règle de confirmation : {rules}. Retirez-le d'abord de là.",
      "sensor_group_in_use": "Ce groupe de capteurs est encore utilisé par : {sensors}. Retirez d'abord le groupe de ces capteurs.",
      "no_modes": "Choisissez au moins un mode.",
      "unknown_kind": "Élément inconnu.",
      "panel_id_invalid": "Utilisez des minuscules, des chiffres, - et _ (comme le nom de l'appareil dans ESPHome).",
      "panel_id_in_use": "Cet ID de clavier est déjà enregistré.",
      "unlock_range": "Choisissez une valeur de {low} à {high}.",
      "unknown_choice": "Choix inconnu.",
      "ha_user_unknown": "Cet utilisateur n'existe pas ou n'est pas actif.",
      "ha_user_in_use": "Cet utilisateur est déjà lié à un autre clavier.",
      "generic": "Une erreur s'est produite."
    }
  },
  it: {
    "title": "Vigil Alarm",
    "tamperShort": "manomissione",
    "about": {
      "details": "Dettagli",
      "aboutIntro": "Un sistema di allarme modulare per Home Assistant.",
      "version": "Versione",
      "license": "Licenza",
      "author": "Autore",
      "links": "Link",
      "manual": "Guida",
      "manualOther": "Guida (Nederlands)",
      "repository": "Progetto GitHub",
      "releases": "Release su GitHub",
      "issues": "Segnala un problema o condividi un'idea",
      "panelDocs": "Pannello touch (ESPHome)",
      "licenseText": "Testo della licenza",
      "notes": "Note di rilascio",
      "notesOnlyEnglish": "",
      "noNotes": "Nessuna nota di rilascio trovata.",
      "system": "Sistema",
      "haVersion": "Home Assistant",
      "python": "Python",
      "alarmState": "Stato dell'allarme",
      "items": "Elementi",
      "copyInfo": "Copia i dettagli per una segnalazione",
      "copied": "Copiato",
      "copyFailed": "Copia non riuscita",
      "disclaimer": "Vigil Alarm non è un sistema di allarme certificato. Testalo regolarmente e non affidarti a lui come unica protezione.",
      "unreleased": "Non ancora rilasciata",
      "firstRelease": "prima versione"
    },
    "tabs": {
      "overview": "Panoramica",
      "sensor": "Sensori",
      "sensor_group": "Gruppi di sensori",
      "rule": "Regole di conferma",
      "user": "Utenti",
      "notification": "Notifiche",
      "siren": "Sirene",
      "log": "Registro",
      "settings": "Impostazioni",
      "backup": "Backup",
      "about": "Info",
      "panel": "Pannelli"
    },
    "add": {
      "sensor": "Aggiungi sensore",
      "sensor_group": "Aggiungi gruppo di sensori",
      "rule": "Aggiungi regola di conferma",
      "user": "Aggiungi utente",
      "notification": "Aggiungi notifica",
      "siren": "Aggiungi sirena",
      "panel": "Aggiungi pannello"
    },
    "edit": {
      "sensor": "Modifica sensore",
      "sensor_group": "Modifica gruppo di sensori",
      "rule": "Modifica regola di conferma",
      "user": "Modifica utente",
      "notification": "Modifica notifica",
      "siren": "Modifica sirena",
      "panel": "Modifica pannello"
    },
    "intro": {
      "sensor": "Un singolo rilevatore, come un contatto porta, un sensore di movimento o un rilevatore di fumo. Per un sensore di intrusione scegli in quali gruppi di sensori si trova. I sensori di incendio, gas, acqua e manomissione sorvegliano sempre e non hanno bisogno di un gruppo di sensori. Lo stesso vale per 24 ore, sonoro (un pulsante antipanico, la porta di un capanno: un allarme con sirena, anche ad allarme disinserito) e 24 ore, silenzioso (un congelatore o un rilevatore di perdite: solo un messaggio e una riga nel registro).",
      "sensor_group": "Un gruppo di sensori stabilisce in quali modalità i sensori al suo interno sorvegliano. Per esempio: Perimetro (porte e finestre) per Casa, Fuori casa e Notte, e Interno (movimento) solo per Fuori casa.",
      "rule": "Un allarme scatta solo quando il numero indicato di sensori diversi si attiva entro la finestra di tempo. Utile contro un falso allarme causato da un singolo sensore di movimento.",
      "user": "Le persone che possono usare l'allarme con un codice. Il codice dice chi opera; quali dispositivi possono operare si imposta sotto Pannelli.",
      "notification": "Chi riceve messaggi e quando. Ogni notifica è un servizio notify.",
      "siren": "Facoltativo. Senza sirena l'allarme funziona con le notifiche.",
      "panel": "Un dispositivo a parete: un pannello ESPHome, oppure un tablet o un telefono con un proprio account Home Assistant. Vigil decide cosa può fare ogni pannello e quali dati riceve; il pannello stesso non decide nulla. L'ID del pannello è il nome del dispositivo ESPHome. Non appena un account è collegato, gli altri account normali non possono più usare l'allarme."
    },
    "empty": {
      "sensor": "Ancora nessun sensore. Aggiungi prima un gruppo di sensori se non ce n'è, poi i tuoi sensori.",
      "sensor_group": "Ancora nessun gruppo di sensori. Un gruppo di sensori stabilisce in quali modalità i sensori sorvegliano.",
      "rule": "Ancora nessuna regola di conferma. Facoltativo: un allarme solo dopo più sensori.",
      "user": "Ancora nessun utente. Senza utente non serve alcun codice per usare l'allarme.",
      "notification": "Ancora nessuna notifica. Aggiungi un servizio notify per ricevere messaggi.",
      "siren": "Ancora nessuna sirena. È facoltativo; senza sirena l'allarme funziona con le notifiche.",
      "panel": "Ancora nessun pannello. Senza un pannello registrato, un pannello ESPHome non riceve alcun profilo e non comanda nulla."
    },
    "save": "Salva",
    "cancel": "Annulla",
    "del": "Elimina",
    "dup": "Copia",
    "editBtn": "Modifica",
    "testBtn": "Prova",
    "close": "Chiudi",
    "ready": {
      "title": "Pronto all'uso?",
      "allGood": "Tutto è configurato. Prova comunque l'allarme regolarmente.",
      "problem": "Da risolvere prima",
      "advice": "Consiglio",
      "go": "Vai",
      "createGroups": "Crea i gruppi predefiniti",
      "groupsMade": "Gruppi di sensori creati",
      "addPhone": "Aggiungi telefono: {name}",
      "phoneAdded": "{name} aggiunto; è stata inviata una notifica di prova. È arrivata?",
      "text": {
        "no_sensors": "Non ci sono ancora sensori. Aggiungili o lascia che Vigil li cerchi.",
        "no_sensor_groups": "Non ci sono ancora gruppi di sensori. Senza un gruppo un sensore di intrusione non sorveglia nulla. Vigil può proporne due: Perimetro (porte e finestre) e Interno (movimento).",
        "mode_unwatched": "Nessun sensore di intrusione sorveglia in questa modalità: {modes}.",
        "no_user_code": "Non c'è ancora nessun utente con un codice, quindi nessuno può usare l'allarme.",
        "no_notification": "Non c'è ancora un canale di notifica, quindi non sentirai nulla quando scatta l'allarme. Usa per esempio l'app sul telefono.",
        "no_siren": "Non c'è una sirena. L'allarme funziona quindi solo con le notifiche.",
        "battery_missing": "{n} sensori non hanno un sensore della batteria, quindi non saprai quando una batteria è scarica: {names}.",
        "tamper_unlinked": "{n} sensori hanno un contatto antimanomissione sullo stesso dispositivo che non è collegato a nulla: {names}.",
        "panel_firmware": "Il firmware del pannello {name} capisce la versione di profilo {seen}, Vigil usa la versione {wanted}. Aggiorna il firmware del pannello."
      }
    },
    "heartbeat": {
      "title": "Heartbeat",
      "off": "Disattivato. Inserisci un indirizzo heartbeat in Impostazioni per iniziare.",
      "lastOk": "Ultimo riuscito",
      "lastFail": "Ultimo fallito",
      "never": "non ancora",
      "every": "Ogni {n} minuti",
      "test": "Prova ora",
      "ok": "L'heartbeat è arrivato.",
      "failed": "L'heartbeat non è arrivato ({reason}).",
      "reason": {
        "timeout": "nessuna risposta entro 10 secondi",
        "connection": "nessuna connessione"
      },
      "failing": "Non riuscito: {reason}"
    },
    "selftest": {
      "title": "Autotest",
      "last": "Ultimo controllo silenzioso",
      "lastSiren": "Ultima prova della sirena",
      "next": "Prossima prova della sirena",
      "never": "non ancora",
      "off": "Il promemoria è disattivato (Impostazioni)",
      "noSiren": "Non è configurata alcuna sirena.",
      "overdue": "In ritardo: la prova era prevista {days} giorni fa.",
      "test": "Prova la sirena ora",
      "started": "La sirena suona per {seconds} secondi.",
      "auto": "Vigil fa suonare la sirena da solo entro le ore impostate.",
      "problems": "Canale di notifica mancante: {name}"
    },
    "dash": {
      "title": "Dashboard",
      "text": "Una dashboard con le entità proprie di questo allarme. Copiala e incollala in una nuova dashboard (Impostazioni > Dashboard > nuova dashboard > editor di configurazione grezza).",
      "copy": "Copia dashboard"
    },
    "log": {
      "intro": "Tutto ciò che Vigil segnala come evento. Il registro conserva {days} giorni (vedi Impostazioni) e non contiene codici. Gli orari sono nel tuo fuso orario; nei download sono in UTC come RFC 3339.",
      "empty": "Ancora nulla nel registro.",
      "cols": {
        "time": "Ora",
        "event": "Evento",
        "item": "Elemento",
        "who": "Utente",
        "via": "Tramite",
        "result": "Risultato",
        "noCode": "sconosciuto (nessun codice)",
        "installer": "codice installatore",
        "auto": "automatico"
      },
      "showing": "Gli ultimi {n} di {total}",
      "jsonl": "Scarica (JSON Lines)",
      "csv": "Scarica (CSV)",
      "refresh": "Aggiorna"
    },
    "summary": {
      "always": "{cls}, sempre attivo",
      "instant": "immediato",
      "delayed": "ritardato ({s} s)",
      "follower": "seguace",
      "and": "e",
      "watching": "{type}, sorveglia in {modes}",
      "nowhere": "{type}, non sorveglia in nessuna modalità"
    },
    "whatsNew": "nuovo",
    "batteryLow": "scarica",
    "batteryOk": "ok",
    "copySuffix": " (copia)",
    "permBypass": {
      "title": "Escluso in modo permanente",
      "intro": "Questi sensori sono esclusi e non sorvegliano, anche dopo il disinserimento. Ripristinali appena sono riparati:",
      "restore": "Ripristina",
      "restored": "Ripristinato"
    },
    "memory": {
      "title": "Ultimo allarme",
      "running": "L'allarme è ancora in corso.",
      "endedBy": "Disinserito alle {time} da {who}.",
      "cancelled": "Annullato come falso allarme.",
      "cause": "Causa",
      "first": "Primo sensore",
      "path": "Percorso in casa",
      "pathIntro": "Ogni sensore che si è aperto dall'inizio dell'allarme fino al disinserimento, in ordine. Sono inclusi i sensori che in questa modalità non contavano o erano esclusi: insieme mostrano dove è passato qualcuno.",
      "time": "Ora",
      "sensor": "Sensore",
      "room": "Stanza",
      "counted": "Conteggiato",
      "notCounted": "Non conteggiato",
      "times": "aperto {n}×",
      "clear": "Cancella la memoria allarmi",
      "cleared": "Memoria allarmi cancellata",
      "noRoom": "nessuna stanza impostata",
      "empty": "Nessun sensore si è aperto (solo la prima segnalazione).",
      "steps": "{n} passaggi",
      "more": "Vengono conservati solo i primi {n} passaggi."
    },
    "practice": {
      "chip": "Modalità di prova",
      "title": "Prova e test",
      "text": "Modalità di prova: l'allarme funziona come sempre (conta alla rovescia, scatta, i pannelli lo mostrano) ma non suona nessuna sirena e non parte nessun messaggio. Tutto è nel registro, contrassegnato come prova. Si interrompe dopo 30 minuti, o appena disinserisci.",
      "start": "Avvia la modalità di prova",
      "stop": "Ferma la modalità di prova",
      "left": "Ancora {n} min.",
      "needsOff": "Disinserisci prima l'allarme.",
      "walk": "Test del percorso: ad allarme disinserito, passa lungo porte, finestre e sensori di movimento; ogni sensore che reagisce viene spuntato. Partecipano solo i sensori di intrusione (i sensori di incendio, gas, acqua e manomissione sono sempre attivi e hanno un test proprio).",
      "walkStart": "Avvia il test del percorso",
      "walkTitle": "Test del percorso",
      "walkRunning": "Apri ogni porta o finestra e passa davanti a ogni sensore di movimento. {n} di {total} visti.",
      "walkStop": "Ferma il test",
      "walkDone": "Fatto: {seen} di {total} visti.",
      "walkAgain": "Ancora",
      "walkMissing": "Non visto",
      "walkReason": {
        "no_response": "non ha reagito",
        "unavailable": "non è disponibile"
      },
      "walkSeen": "Visto",
      "walkNone": "Tutti i sensori hanno reagito.",
      "walkLast": "Ultimo test del percorso: {seen} di {total} visti ({time}).",
      "close": "Chiudi"
    },
    "wizard": {
      "title": "Configura Vigil",
      "button": "Configurazione guidata",
      "step": "Passaggio {n} di {total}",
      "back": "Indietro",
      "next": "Avanti",
      "skip": "Salta",
      "finish": "Fatto",
      "stop": "Continua più tardi",
      "resume": "Continua la configurazione guidata",
      "cardTitle": "Configura Vigil",
      "cardText": "Non tutto è ancora configurato. La configurazione guidata procede passo dopo passo; puoi saltare qualsiasi passaggio e tornarci più tardi.",
      "start": "Avvia la configurazione guidata",
      "done": "Fatto",
      "todo": "Da fare",
      "optional": "Consigliato",
      "welcome": {
        "title": "Benvenuto in Vigil",
        "text": "In pochi passaggi configuri l'allarme: quali modalità usi, quali sensori partecipano, chi riceve un codice e come ricevi un messaggio. Non viene salvato nulla finché non lo confermi in un passaggio, e ogni modifica può essere ripristinata dalla scheda Backup."
      },
      "modes": {
        "title": "Quali modalità usi?",
        "text": "Casa (sei in casa, il perimetro è sorvegliato), Fuori casa (nessuno in casa), Notte (dormi), Vacanza (via a lungo) e Personalizzato (una modalità tua, per esempio solo il garage). Scegli solo ciò che usi davvero; i ritardi di uscita si possono cambiare più tardi in Impostazioni.",
        "save": "Salva",
        "saved": "Modalità salvate.",
        "none": "Scegli almeno una modalità."
      },
      "sensors": {
        "title": "Sensori",
        "text": "Vigil cerca in Home Assistant sensori di porta, finestra, movimento, fumo, gas e acqua. Tu scegli quali aggiungere.",
        "have": "{n} sensori configurati.",
        "none": "Ancora nessun sensore.",
        "find": "Cerca sensori",
        "fresh": "{n} nuovi trovati."
      },
      "user": {
        "title": "Chi può usare l'allarme?",
        "text": "Un utente ha un codice. Puoi creare un utente da una persona di Home Assistant o aggiungerne uno a mano.",
        "have": "{n} utente/i con un codice.",
        "none": "Ancora nessun utente con un codice.",
        "fromPerson": "Crea un utente da {name}",
        "add": "Aggiungi un utente"
      },
      "notification": {
        "title": "Dove vuoi ricevere un messaggio?",
        "text": "In caso di allarme o guasto Vigil invia un messaggio. Un telefono con l'app Home Assistant è la soluzione più semplice.",
        "have": "{n} canale/i di notifica.",
        "none": "Ancora nessun canale di notifica.",
        "phone": "Aggiungi {name}",
        "add": "Aggiungi un canale di notifica",
        "added": "{name} è stato aggiunto; è stato inviato un messaggio di prova."
      },
      "siren": {
        "title": "Sirena",
        "text": "Una sirena non è obbligatoria, ma senza di essa senti un allarme solo tramite i messaggi.",
        "have": "{n} sirena/e.",
        "none": "Ancora nessuna sirena.",
        "add": "Aggiungi una sirena"
      },
      "panel": {
        "title": "Pannello a parete",
        "text": "Uno schermo ESPHome, un tablet o un telefono può comandare l'allarme. È facoltativo.",
        "have": "{n} pannello/i.",
        "none": "Ancora nessun pannello.",
        "add": "Collega un pannello"
      },
      "test": {
        "title": "Pronto all'uso?",
        "text": "Questo è ciò che manca ancora a Vigil. Tutto ciò che è contrassegnato come «problema» impedisce ancora all'allarme di proteggere.",
        "allGood": "Tutto in ordine.",
        "testSiren": "Prova la sirena",
        "sirenStarted": "La sirena suona brevemente."
      },
      "end": {
        "title": "Fatto",
        "text": "Vigil è configurato. Una prova: inserisci l'allarme, apri una porta e verifica se arriva il tuo messaggio. Dopo puoi aggiungere automazioni con i blueprint inclusi (inserire automaticamente quando escono tutti, far lampeggiare le luci in caso di allarme, pronunciare un messaggio). Le trovi nella guida sotto Automazioni e blueprint."
      }
    },
    "newSensors": {
      "title": "Nuovi sensori trovati",
      "text": "Questi sensori sono comparsi in Home Assistant dall'ultima volta che Vigil ha controllato. Non è stato aggiunto nulla.",
      "review": "Controlla e aggiungi",
      "later": "Non ora",
      "badge": "{n} nuovi",
      "dismissed": "OK, Vigil non li segnalerà più. Puoi comunque aggiungerli con Cerca sensori.",
      "onlyNew": "Vengono mostrati solo i nuovi sensori.",
      "showAll": "Mostra tutti i sensori",
      "showNew": "Mostra solo i nuovi"
    },
    "find": {
      "button": "Cerca sensori",
      "title": "Cerca sensori",
      "intro": "Questi sensori sono stati trovati in Home Assistant. Scegli quali aggiungere. Non viene salvato nulla finché non premi il pulsante in fondo.",
      "none": "Nessun nuovo sensore trovato. Vengono mostrati i sensori di porta, finestra, movimento, fumo, gas, acqua e manomissione di un dispositivo integrato.",
      "noGroups": "Alcuni sensori di intrusione non hanno ancora un gruppo di sensori. Imposta «Suggerisci per i nuovi sensori» di un gruppo di sensori su contatti o movimento; poi puoi aggiungerli qui.",
      "cols": {
        "name": "Nome",
        "cls": "Classe",
        "entrance": "Ingresso",
        "groups": "Gruppi di sensori",
        "extra": "Incluso"
      },
      "entranceHelp": "Un ingresso riceve un ritardo d'ingresso (tipo «ritardato»).",
      "inUse": "già in uso",
      "needsGroup": "nessun gruppo di sensori",
      "battery": "batteria",
      "tamper": "manomissione",
      "all": "Seleziona tutto",
      "nothing": "Deseleziona tutto",
      "add": "Aggiungi {n}",
      "adding": "Aggiunta in corso…",
      "copy": "Copia i dati di rilevamento",
      "copyHelp": "Un elenco anonimo senza nomi o indirizzi, per una segnalazione o per aiutare a testare un'integrazione.",
      "createGroups": "Crea i gruppi predefiniti",
      "added": "{n} sensori aggiunti",
      "failed": "{name}: {error}"
    },
    "confirmDelete": "Vuoi davvero eliminare «{name}»?",
    "saved": "Salvato",
    "deleted": "Eliminato",
    "testSent": "Prova inviata",
    "loading": "Caricamento…",
    "loadFailed": "Impossibile caricare Vigil Alarm. L'integrazione è in esecuzione?",
    "retry": "Riprova",
    "sections": {
      "alarm": {
        "0": "Modalità e ritardi",
        "1": "Quali modalità usi, quanto tempo hai per uscire e per entrare, e quanto dura l'allarme."
      },
      "chime": {
        "0": "Campanello",
        "1": "Un breve suono quando si apre un sensore con la casella Campanello spuntata mentre l'allarme è disinserito."
      },
      "codes": {
        "0": "Codici",
        "1": "Se serve un codice per inserire e quanto deve essere lungo almeno un codice."
      },
      "startup": {
        "0": "Avvio",
        "1": "Dopo un riavvio di Home Assistant, Vigil attende che tutti i tuoi sensori siano disponibili (per esempio MQTT o Zigbee ancora in avvio) prima di segnalare un sensore come perso o di generare un allarme per esso. Se dopo questo tempo mancano ancora, segue la segnalazione."
      },
      "lock": {
        "0": "Blocco",
        "1": "Cosa succede dopo codici errati, per pannello: prima un blocco breve, poi più lunghi, poi un blocco permanente che sparisce solo con Rimuovi blocco sotto Pannelli. Un codice giusto riparte da zero."
      },
      "screen": {
        "0": "Schermo del pannello",
        "1": "Quando lo schermo di un pannello ESPHome si spegne. Si spegne solo ad allarme disinserito o completamente inserito, mai durante il conto alla rovescia per inserire o disinserire."
      },
      "battery": {
        "0": "Batterie",
        "1": "Da quale livello una batteria conta come scarica."
      },
      "log": {
        "0": "Registro eventi",
        "1": "Per quanto tempo Vigil conserva gli eventi."
      },
      "backup": {
        "0": "Backup",
        "1": "Quante versioni della tua configurazione Vigil conserva (scheda Backup). Un valore più basso scarta le versioni più vecchie."
      },
      "selftest": {
        "0": "Autotest",
        "1": "Vigil ti ricorda di provare la sirena. Imposta l'intervallo a 0 per disattivare il promemoria."
      },
      "heartbeat": {
        "0": "Heartbeat",
        "1": "Vigil chiama regolarmente questo indirizzo, così un servizio esterno alla tua casa segnala quando Home Assistant o il tuo internet si fermano."
      }
    },
    "reloadNote": "Il salvataggio ricarica Vigil Alarm (lo stato dell'allarme viene mantenuto).",
    "alarm": "Allarme",
    "problems": "Attenzione",
    "noProblems": "Nessun problema",
    "sensorsNow": "Sensori ora",
    "coverage": "Cosa sorveglia ogni modalità",
    "coverageNothing": "nessun gruppo di sensori: non si sorveglia nulla",
    "alwaysOn": "Sempre attivo",
    "sensorsCount": "{n} sensori",
    "state": {
      "disarmed": "Disattivato",
      "arming": "Inserimento",
      "armed": "Inserito",
      "pending": "Ritardo d'ingresso",
      "triggered": "ALLARME"
    },
    "mode": {
      "home": "Casa",
      "away": "Fuori casa",
      "night": "Notte",
      "vacation": "Vacanza",
      "custom": "Personalizzato"
    },
    "zstatus": {
      "closed": "Chiuso",
      "open": "Aperto",
      "unavailable": "Non raggiungibile",
      "bypassed": "Escluso",
      "bypassed_at_arm": "Escluso all'inserimento",
      "waiting": "In attesa di chiusura"
    },
    "problem": {
      "battery_low": "batteria scarica",
      "unavailable": "non raggiungibile",
      "on_battery": "nessuna alimentazione di rete"
    },
    "cols": {
      "name": "Nome",
      "entity": "Entità",
      "cls": "Classe",
      "type": "Tipo",
      "groups": "Gruppi di sensori",
      "rule": "Regola di conferma",
      "status": "Stato",
      "battery": "Batteria",
      "modes": "Attivo nelle modalità",
      "sensors": "Sensori",
      "suggest": "Suggerito per",
      "condition": "Condizione",
      "escalate": "Segnala se non confermato",
      "code": "Codice",
      "duress": "Codice di coercizione",
      "tags": "Tag",
      "bypass": "Escludi",
      "tamper": "Può escludere la manomissione",
      "service": "Servizio",
      "categories": "Categorie",
      "delay": "Ritardo",
      "device": "Dispositivo",
      "causes": "Per",
      "maxdur": "Durata max.",
      "panelId": "ID del pannello",
      "conn": "Connessione",
      "allowed": "Restrizioni"
    },
    "panel": {
      "tablet": "Account",
      "noUser": "utente non trovato",
      "connected": "Connesso",
      "offline": "Non raggiungibile",
      "noConnection": "Nessuna connessione",
      "noCard": "Nessuna scheda Vigil vista",
      "cardSeen": "Scheda Vigil attiva",
      "notFound": "Non trovato in ESPHome",
      "unlocked": "Sbloccato",
      "locked": "Bloccato per {s} s",
      "lockedPermanent": "Bloccato definitivamente",
      "blocked": "Bloccato",
      "notWatched": "Non monitorato",
      "unlock": "Sblocca",
      "unlockedDone": "Sbloccato per {s} secondi.",
      "clear": "Rimuovi blocco",
      "cleared": "Blocco rimosso.",
      "nothingLocked": "Questo pannello non era bloccato.",
      "all": "tutte le modalità",
      "noDisarm": "nessun disinserimento",
      "noBypass": "nessuna esclusione",
      "noSilence": "nessun silenziamento",
      "hint": "Sbloccare e rimuovere il blocco si può fare solo qui, non come azione di Home Assistant.",
      "refused": "Non è possibile."
    },
    "yes": "sì",
    "no": "no",
    "none": "—",
    "immediately": "immediatamente",
    "condition": "{n} entro {s} s",
    "fields": {
      "name": "Nome",
      "entity_id": "Entità (sensore binario)",
      "cls": "Classe",
      "type": "Tipo",
      "sensor_groups": "Gruppi di sensori",
      "at_arm_open": "Se aperto al termine del ritardo di uscita",
      "entry_delay": "Ritardo d'ingresso (vuoto = predefinito)",
      "gas_type": "Tipo di gas",
      "on_unavailable": "Quando il sensore diventa non raggiungibile",
      "battery_entity": "Sensore della batteria",
      "tamper_entity": "Entità antimanomissione (facoltativa)",
      "chime": "Campanello: suono quando questo sensore si apre ad allarme disinserito",
      "permanent_bypass": "Mantieni l'esclusione dopo il disinserimento (permanente)",
      "duress_code": "Codice di coercizione (facoltativo)",
      "sensor_group.modes": "Attivo nelle modalità",
      "suggest_for": "Suggerisci per i nuovi sensori",
      "sensors": "Sensori",
      "required": "Sensori necessari",
      "window": "Finestra di tempo",
      "escalate": "Segnala se non confermato",
      "code": "Codice",
      "tags": "Tag (separati da virgola)",
      "allowed_modes": "Può operare nelle modalità (vuoto = tutte)",
      "may_bypass": "Può escludere sensori",
      "may_bypass_tamper": "Può escludere la manomissione",
      "service": "Servizio notify",
      "categories": "Tipi di messaggi",
      "delay": "Ritardo",
      "priority": "Priorità alta",
      "control": "Sirena (sirena, interruttore o luce)",
      "causes": "Suona per",
      "max_duration": "Durata massima (0 = fino al disinserimento)",
      "repeat_every": "Ripeti ogni (0 = no)",
      "light": "Fai lampeggiare la luce",
      "tone_entity": "Entità di selezione del tono",
      "volume_entity": "Entità del volume",
      "power_entity": "Entità della modalità di alimentazione",
      "power_battery_value": "Valore a batteria",
      "tone": "Tono",
      "volume": "Volume",
      "preset": "Preimpostazione",
      "device": "Tipo di dispositivo",
      "panel_id": "Nome del dispositivo ESPHome (ID del pannello)",
      "ha_user": "Account Home Assistant (tablet o telefono)",
      "language": "Lingua",
      "can_disarm": "Può disinserire (con un codice)",
      "can_bypass": "Può escludere sensori (con un codice)",
      "can_silence": "Può silenziare e confermare",
      "sensor_list": "Mostra l'elenco dei sensori",
      "unlock_seconds": "Resta sbloccato per (secondi)",
      "watch": "Controlla se questo pannello è raggiungibile (notifica quando si disconnette)",
      "blocked": "Pannello bloccato",
      "panel.code": "Codice installatore di questo pannello (vuoto = nessuno)",
      "panel.allowed_modes": "Può inserire nelle modalità (vuoto = tutte)",
      "s.modes": "Modalità disponibili",
      "exit_delay_home": "Ritardo di uscita Casa",
      "exit_delay_away": "Ritardo di uscita Fuori casa",
      "exit_delay_night": "Ritardo di uscita Notte",
      "exit_delay_vacation": "Ritardo di uscita Vacanza",
      "exit_delay_custom": "Ritardo di uscita Personalizzato",
      "default_entry_delay": "Ritardo d'ingresso predefinito",
      "trigger_time": "Durata dell'allarme (0 = fino al disinserimento)",
      "abort_seconds": "Finestra di annullamento dopo l'avvio della sirena (secondi, 0 = disattivata)",
      "chime_entity": "Campanello: cosa produce il suono",
      "chime_seconds": "Il campanello suona per (secondi)",
      "battery_threshold": "Soglia della batteria",
      "backup_versions": "Numero di versioni conservate",
      "code_arm_required": "Codice richiesto per inserire",
      "startup_wait_seconds": "Attesa massima dei sensori dopo un riavvio (secondi)",
      "lock_tries_1": "Codici errati prima del primo blocco",
      "lock_wait_1": "Il primo blocco dura (minuti)",
      "lock_tries_2": "Poi codici errati prima del secondo blocco",
      "lock_wait_2": "Il secondo blocco dura (minuti)",
      "lock_tries_3": "Poi codici errati prima del terzo blocco",
      "lock_wait_3": "Il terzo blocco dura (minuti)",
      "lock_tries_4": "Poi codici errati prima del blocco permanente",
      "screen_off_seconds": "Schermo spento dopo (secondi senza tocco)",
      "screen_off_on_alarm": "Spegni lo schermo anche durante un allarme",
      "log_retention_days": "Conserva il registro (giorni)",
      "selftest_interval_days": "Promemoria della prova della sirena (giorni, 0 = disattivato)",
      "selftest_siren_seconds": "La sirena suona durante una prova (secondi)",
      "selftest_auto": "Fai suonare la sirena da sola per la prova",
      "selftest_window_start": "Non prima delle (ora)",
      "selftest_window_end": "Non dopo le (ora)",
      "heartbeat_url": "Indirizzo heartbeat (vuoto = disattivato)",
      "heartbeat_interval_minutes": "Minuti tra gli heartbeat",
      "min_code_length": "Lunghezza minima del codice (caratteri)"
    },
    "helpMore": {
      "at_arm_open": "Cosa succede se questo sensore è ancora aperto al termine del ritardo di uscita:\n• Escludi con avviso (predefinito): l'allarme si inserisce senza questo sensore e ricevi un avviso. Appena il sensore si chiude, torna a essere sorvegliato.\n• Attendi la chiusura: l'allarme si inserisce e questo sensore viene ignorato finché non si è chiuso una volta, senza avviso. Poi torna a essere sorvegliato.\n• Rifiuta l'inserimento: l'allarme non si inserisce e vedi quale sensore è aperto. Chiudilo prima.\n• Avvia il ritardo d'ingresso: l'allarme si inserisce e il sensore aperto conta subito come attivato. Un sensore diretto fa scattare l'allarme, un sensore ritardato avvia il ritardo d'ingresso.",
      "tamper_entity": "Questo dispositivo ha anche un contatto antimanomissione? Sceglilo qui. Vigil aggiunge da solo un sensore di manomissione: sempre in sorveglianza, con un proprio interruttore di esclusione. Non devi aggiungerlo separatamente."
    },
    "moreInfo": "Ulteriori informazioni",
    "help": {
      "duress_code": "Un secondo codice per quando qualcuno ti costringe a spegnere l'allarme. Disinserisce l'allarme come al solito e non si nota nulla: la sirena resta muta. Nel frattempo un messaggio silenzioso va ai canali con il tipo di messaggio Coercizione. Deve essere diverso da ogni altro codice.",
      "permanent_bypass": "Se escludi questo sensore a mano, resta escluso anche dopo il disinserimento dell'allarme, finché non lo ripristini tu. Utile per un sensore guasto da tempo. Senza questa spunta l'esclusione termina al disinserimento. I sensori di incendio e gas non possono mai essere esclusi.",
      "chime": "Quando il sensore si apre ad allarme disinserito, viene riprodotto un breve suono tramite ciò che hai scelto nelle impostazioni. Nessun allarme, nessun messaggio, nulla nel registro. Con l'allarme inserito non succede nulla.",
      "abort_seconds": "Chi inserisce un codice valido entro questo numero di secondi dopo che la sirena è partita ha causato un falso allarme: la sirena si ferma e parte un messaggio «annullato». 0 disattiva la funzione. Non vale per incendio, gas e manomissione.",
      "chime_entity": "Una sirena, un interruttore, una luce, un pulsante o uno script che emette un suono. Puoi lasciarlo vuoto: l'evento Campanello resta sull'entità evento, per un'automazione tua (per esempio un messaggio su un altoparlante).",
      "chime_seconds": "Per quanto tempo una sirena, un interruttore o una luce resta accesa. Nessun effetto per un pulsante o uno script.",
      "may_bypass": "Senza questo diritto l'utente non può né escludere né ripristinare un sensore, nemmeno con un codice giusto. Un amministratore di Home Assistant può sempre farlo.",
      "screen_off_seconds": "Vale per tutti i pannelli ESPHome. Con un codice digitato a metà o un elenco aperto, il pannello torna prima alla pagina principale dopo questo tempo, e lo schermo si spegne dopo lo stesso tempo.",
      "screen_off_on_alarm": "Disattivato: lo schermo resta acceso durante un allarme, così l'ALLARME e la sua causa restano visibili. Attivato: lo schermo si spegne anche allora. Durante il conto alla rovescia per inserire o per entrare, lo schermo non si spegne mai.",
      "entity_id": "Un sensore binario: acceso significa aperto o allarme.",
      "tamper_entity": "Facoltativo: il contatto antimanomissione di questo dispositivo.",
      "at_arm_open": "Cosa succede a questo sensore se è ancora aperto quando l'allarme si inserisce.",
      "type": "Immediato: allarme subito. Ritardato: prima il ritardo d'ingresso. Seguace: scatta solo se prima è stato aperto un sensore ritardato.",
      "sensor_groups": "Un sensore può stare in più gruppi. Sorveglia in ogni modalità in cui è attivo uno dei suoi gruppi.",
      "suggest_for": "Facoltativo. Un nuovo sensore di questo tipo (contatto porta o movimento) viene inserito automaticamente in questo gruppo.",
      "sensors": "Solo sensori di intrusione immediati.",
      "code": "Lascia vuoto per non cambiare nulla.",
      "device": "Pannello ESPHome: uno schermo con firmware proprio, riconosciuto dal nome del dispositivo ESPHome. Tablet o telefono: un dispositivo con l'app o il browser di Home Assistant, riconosciuto dall'account con cui è connesso.",
      "ha_user": "Per un tablet o un telefono: l'account con cui il dispositivo è connesso. Vigil riconosce il dispositivo da quell'account, non da un testo, quindi non può essere imitato. Si può scegliere anche un amministratore, ma attenzione: le impostazioni di questo pannello valgono allora per tutto ciò che quell'account fa, su ogni dispositivo in cui è connesso, e Vigil qui non dà all'account diritti di amministratore (serve sempre un codice). Meglio un secondo account normale per l'uso quotidiano.",
      "removeCode": "Rimuovi codice",
      "removeDuress": "Rimuovi codice di coercizione",
      "tags": "I tag non hanno alcuna funzione: usa l'allarme con un codice.",
      "categories": "Scegli quali messaggi riceve questo canale.",
      "service": "Un servizio notify (come mobile_app_phone o un gruppo da YAML) o un'entità notify (come notify.family, un gruppo notify creato come helper). Un'entità notify riceve solo titolo e messaggio: l'avviso critico della priorità alta non funziona con essa, e nemmeno il pulsante nel messaggio di prova dell'autocontrollo. Per questo, su un telefono scegli il suo servizio mobile_app_… dedicato.",
      "priority": "Solo per telefoni con l'app Home Assistant (un servizio mobile_app_…): un allarme viene allora inviato come avviso critico su iOS e con priorità alta su Android. Per un'entità notify o un altro servizio non ha effetto.",
      "delay": "Solo allarmi: attendi prima, per esempio per notificare un secondo dispositivo solo dopo un po'.",
      "profiles": "Tono e volume per causa (facoltativo)",
      "preset": "Compila tono, volume e durata per una sirena nota. Scegli prima l'entità on/off sotto «Sirena» e Vigil cerca le altre entità dello stesso dispositivo. Tutto resta modificabile.",
      "presetFound": "Trovato su questo dispositivo:",
      "presetNoneFound": "Nessun'altra entità trovata su questo dispositivo; sceglile tu.",
      "presetNoControl": "Valori compilati. Scegli l'entità della sirena e scegli di nuovo la preimpostazione per cercare le altre entità.",
      "power_battery_value": "Il valore dell'entità della modalità di alimentazione quando la sirena funziona a batteria."
    },
    "opt": {
      "preset": {
        "": "—",
        "sonoff_snzb_09p_z2m": "Sonoff SNZB-09P (Zigbee2MQTT)"
      },
      "cls": {
        "intrusion": "Intrusione",
        "fire": "Incendio",
        "gas": "Gas",
        "tamper": "Manomissione",
        "water": "Acqua",
        "alarm24": "24 ore, sonoro",
        "silent24": "24 ore, silenzioso"
      },
      "type": {
        "instant": "Immediato",
        "delayed": "Ritardato (ritardo d'ingresso)",
        "follower": "Seguace"
      },
      "at_arm_open": {
        "bypass": "Escludi con avviso",
        "wait_clear": "Attendi la chiusura",
        "refuse": "Rifiuta l'inserimento",
        "pending": "Avvia il ritardo d'ingresso"
      },
      "gas_type": {
        "co": "Monossido di carbonio",
        "natural_gas": "Gas naturale",
        "lpg": "GPL",
        "other": "Altro"
      },
      "on_unavailable": {
        "default": "Predefinito della classe",
        "block": "Blocca l'inserimento",
        "notify": "Solo notifica",
        "trigger": "Fai scattare l'allarme",
        "bypass": "Inserisci comunque (escludi)"
      },
      "categories": {
        "alarm": "Allarme",
        "pending": "Ritardo d'ingresso",
        "arming": "Inserimento e disinserimento",
        "fault": "Guasti e avvisi",
        "technical": "Allarmi tecnici (acqua)",
        "duress": "Coercizione (allarme silenzioso)"
      },
      "causes": {
        "intrusion": "Intrusione",
        "fire": "Incendio",
        "gas": "Gas",
        "tamper": "Manomissione",
        "fault": "Guasto del sensore"
      },
      "cause": {
        "intrusion": "Intrusione",
        "fire": "Incendio",
        "gas": "Gas",
        "tamper": "Manomissione",
        "alarm24": "Allarme 24 ore"
      },
      "mode": {
        "home": "Casa",
        "away": "Fuori casa",
        "night": "Notte",
        "vacation": "Vacanza",
        "custom": "Personalizzato"
      },
      "suggest_for": {
        "": "Nessuno",
        "contacts": "Porte e finestre (contatti)",
        "motion": "Movimento"
      },
      "language": {
        "nl": "Nederlands",
        "en": "English",
        "de": "Deutsch",
        "fr": "Français",
        "it": "Italiano",
        "es": "Español"
      },
      "device": {
        "esphome": "Pannello ESPHome (schermo fai da te)",
        "account": "Tablet o telefono con Home Assistant"
      },
      "sensor_list": {
        "always": "Mostra sempre",
        "code": "Solo dopo lo sblocco",
        "never": "Non mostrare mai"
      }
    },
    "why": {
      "title": "Perché non riesco a inserire?",
      "intro": "Questo impedisce l'inserimento in questo momento:",
      "modes": "in {modes}",
      "show": "Mostra",
      "bypass": "Escludi",
      "bypassed": "Escluso",
      "neverBypass": "I sensori di incendio e gas non possono essere esclusi: rimuovi prima la causa.",
      "reason": {
        "alarm_condition": "è aperto (una condizione di allarme)",
        "sensor_unavailable": "non risponde (ed è impostato per impedire l'inserimento)",
        "sensor_open": "è aperto e deve essere chiuso per inserire",
        "not_disarmed": "l'allarme è già inserito"
      },
      "hint": "Sul pannello e nella scheda Vigil il pulsante Escludi e inserisci esclude e inserisce in un colpo solo, se ne hai il diritto."
    },
    "backup": {
      "intro": "A ogni modifica Vigil conserva la configurazione com'era prima di quella modifica (le ultime 10 versioni). Puoi ripristinare una di queste versioni; anche il ripristino è una modifica, quindi si può annullare allo stesso modo. Vengono conservate solo le impostazioni, non lo stato dell'allarme (inserito, escluso).",
      "list": "Versioni conservate",
      "none": "Ancora nessuna versione. Compaiono appena cambi qualcosa.",
      "restore": "Ripristina",
      "reason": {
        "edit": "Modifica",
        "restore": "Ripristinato",
        "import": "Importa",
        "external": "Modificato fuori dal pannello",
        "upgrade": "Aggiornamento di Vigil"
      },
      "colTime": "Ora",
      "colReason": "Motivo",
      "colVigil": "Versione di Vigil",
      "colChange": "Modifica",
      "view": "Visualizza",
      "viewTitle": "Modifica del {time}",
      "viewText": "Questa versione conserva la configurazione com'era prima di questa modifica. La modifica stessa era:",
      "format": "versione di archiviazione {v}",
      "notRestorable": "Non può essere ripristinata: creata da un'altra versione di archiviazione ({v}, ora {now}). Può comunque essere visualizzata.",
      "settingsList": "Impostazioni: {names}",
      "restoreTitle": "Ripristinare questa versione?",
      "restoreText": "Il ripristino cambia questo rispetto a ora:",
      "nothing": "Nessuna differenza rispetto a ora.",
      "restored": "Ripristinato",
      "fileTitle": "Esporta e importa",
      "export": "Esporta la configurazione",
      "import": "Importa la configurazione…",
      "exportNote": "Il file non contiene codici, ma contiene i codici sotto forma di hash, l'indirizzo heartbeat e i nomi dei tuoi servizi di notifica. Conservalo al sicuro.",
      "importNote": "L'importazione sostituisce l'intera configurazione. Quella attuale viene conservata come versione, quindi un'importazione può essere ripristinata.",
      "importTitle": "Importare questo file?",
      "importText": "L'importazione cambia questo rispetto a ora:",
      "imported": "Importato",
      "readFailed": "Questo file non può essere letto.",
      "added": "aggiunto",
      "removed": "rimosso",
      "changed": "modificato",
      "settings": "Impostazioni modificate: {n}",
      "undo": "Annulla modifica",
      "apply": "Applica"
    },
    "errors": {
      "backup_invalid": "Questo file o questa versione non contiene una configurazione utilizzabile.",
      "backup_unknown": "Questa versione non esiste più.",
      "import_not_vigil": "Questo non è un file di esportazione di Vigil Alarm.",
      "import_format_version": "Questo file ha un formato sconosciuto.",
      "import_entry_version": "Questo file appartiene a un'altra versione di archiviazione ({found}, richiesta: {expected}). Importalo nella stessa versione di Vigil in cui è stato creato.",
      "name_required": "Inserisci un nome.",
      "name_in_use": "Questo nome esiste già.",
      "required": "Obbligatorio.",
      "invalid_config": "Non valido: {error}",
      "sensor_not_instant": "Solo i sensori immediati possono far parte di una regola di conferma. Modifica: {sensors}",
      "entity_in_use": "Questa entità è già un sensore.",
      "tamper_same_entity": "L'entità antimanomissione deve essere diversa dal sensore stesso.",
      "tamper_entity_in_use": "Questa entità è già un sensore.",
      "no_sensor_group": "Scegli almeno un gruppo di sensori.",
      "unknown_sensor_group": "Gruppo di sensori sconosciuto.",
      "unknown_mode": "Modalità sconosciuta.",
      "unknown_suggestion": "Scelta sconosciuta.",
      "backup_versions_range": "Scegli un numero da {min} a {max}.",
      "code_in_use": "Questo codice è già in uso.",
      "code_too_short": "Il codice deve avere almeno {min} caratteri (impostato in Impostazioni).",
      "code_length_range": "Scegli un valore da {min} a {max}.",
      "screen_off_range": "Scegli un numero di secondi da {min} a {max}.",
      "startup_wait_range": "Scegli un numero di secondi da {min} a {max}.",
      "lock_tries_range": "Scegli un numero di volte da {min} a {max}.",
      "lock_wait_range": "Scegli un numero di minuti da {min} a {max}.",
      "log_retention_range": "Scegli un numero di giorni da {min} a {max}.",
      "selftest_range": "Scegli un valore da {min} a {max}.",
      "selftest_window": "L'ora più tarda deve essere dopo l'ora più presto.",
      "heartbeat_url_invalid": "Questo non è un indirizzo web. Deve iniziare con http:// o https://.",
      "heartbeat_range": "Scegli un numero di minuti da {min} a {max}.",
      "tag_in_use": "Questo tag è già in uso.",
      "no_credential": "Inserisci un codice o almeno un tag.",
      "duress_needs_code": "Un codice di coercizione accompagna un codice normale: inserisci prima un codice.",
      "duress_no_channel": "Non esiste un canale di notifica con il tipo di messaggio Coercizione. Senza di esso un allarme silenzioso non raggiunge nessuno. Aggiungine prima uno.",
      "seconds_range": "Scegli un numero di secondi da {min} a {max}.",
      "chime_entity_domain": "Scegli una sirena, un interruttore, una luce, un pulsante o uno script.",
      "service_not_found": "Questo servizio notify non esiste (più).",
      "no_categories": "Scegli almeno un tipo di messaggio.",
      "no_causes": "Scegli almeno una causa.",
      "tone_without_entity": "Un tono richiede un'entità di selezione del tono.",
      "volume_without_entity": "Un volume richiede un'entità del volume.",
      "sensor_in_rule": "Questo sensore è ancora nella regola di conferma: {rules}. Rimuovilo prima da lì.",
      "sensor_group_in_use": "Questo gruppo di sensori è ancora usato da: {sensors}. Rimuovi prima il gruppo da quei sensori.",
      "no_modes": "Scegli almeno una modalità.",
      "unknown_kind": "Elemento sconosciuto.",
      "panel_id_invalid": "Usa lettere minuscole, cifre, - e _ (come il nome del dispositivo in ESPHome).",
      "panel_id_in_use": "Questo ID del pannello è già registrato.",
      "unlock_range": "Scegli un valore da {low} a {high}.",
      "unknown_choice": "Scelta sconosciuta.",
      "ha_user_unknown": "Questo utente non esiste o non è attivo.",
      "ha_user_in_use": "Questo utente è già associato a un altro pannello.",
      "generic": "Qualcosa è andato storto."
    }
  },
  es: {
    "title": "Vigil Alarm",
    "tamperShort": "sabotaje",
    "about": {
      "details": "Detalles",
      "aboutIntro": "Un sistema de alarma modular para Home Assistant.",
      "version": "Versión",
      "license": "Licencia",
      "author": "Autor",
      "links": "Enlaces",
      "manual": "Guía de uso",
      "manualOther": "Guía de uso (Nederlands)",
      "repository": "Proyecto en GitHub",
      "releases": "Versiones en GitHub",
      "issues": "Informar de un problema o compartir una idea",
      "panelDocs": "Panel táctil (ESPHome)",
      "licenseText": "Texto de la licencia",
      "notes": "Notas de la versión",
      "notesOnlyEnglish": "",
      "noNotes": "No se encontraron notas de la versión.",
      "system": "Sistema",
      "haVersion": "Home Assistant",
      "python": "Python",
      "alarmState": "Estado de la alarma",
      "items": "Elementos",
      "copyInfo": "Copiar los detalles para un informe",
      "copied": "Copiado",
      "copyFailed": "No se pudo copiar",
      "disclaimer": "Vigil Alarm no es un sistema de alarma certificado. Pruébalo con regularidad y no confíes en él como única protección.",
      "unreleased": "Aún no publicada",
      "firstRelease": "primera versión"
    },
    "tabs": {
      "overview": "Resumen",
      "sensor": "Sensores",
      "sensor_group": "Grupos de sensores",
      "rule": "Reglas de confirmación",
      "user": "Usuarios",
      "notification": "Notificaciones",
      "siren": "Sirenas",
      "log": "Registro",
      "settings": "Ajustes",
      "backup": "Copia de seguridad",
      "about": "Acerca de",
      "panel": "Paneles"
    },
    "add": {
      "sensor": "Añadir sensor",
      "sensor_group": "Añadir grupo de sensores",
      "rule": "Añadir regla de confirmación",
      "user": "Añadir usuario",
      "notification": "Añadir notificación",
      "siren": "Añadir sirena",
      "panel": "Añadir panel"
    },
    "edit": {
      "sensor": "Editar sensor",
      "sensor_group": "Editar grupo de sensores",
      "rule": "Editar regla de confirmación",
      "user": "Editar usuario",
      "notification": "Editar notificación",
      "siren": "Editar sirena",
      "panel": "Editar panel"
    },
    "intro": {
      "sensor": "Un solo detector, como un contacto de puerta, un detector de movimiento o un detector de humo. Para un sensor de intrusión eliges en qué grupos de sensores está. Los sensores de incendio, gas, agua y sabotaje vigilan siempre y no necesitan un grupo de sensores. Lo mismo vale para 24 horas, audible (un botón de pánico, la puerta de un cobertizo: una alarma con sirena, también con la alarma desactivada) y 24 horas, silenciosa (un congelador o un detector de fugas: solo un mensaje y una línea en el registro).",
      "sensor_group": "Un grupo de sensores decide en qué modos vigilan los sensores que contiene. Por ejemplo: Perímetro (puertas y ventanas) para En casa, Fuera y Noche, e Interior (movimiento) solo para Fuera.",
      "rule": "Una alarma solo se produce cuando el número indicado de sensores distintos se activa dentro de la ventana de tiempo. Útil contra una falsa alarma de un único detector de movimiento.",
      "user": "Las personas que pueden manejar la alarma con un código. El código indica quién opera; qué dispositivos pueden operar se define en Paneles.",
      "notification": "Quién recibe mensajes y cuándo. Cada notificación es un servicio notify.",
      "siren": "Opcional. Sin sirena, la alarma funciona con notificaciones.",
      "panel": "Un dispositivo en la pared: un panel ESPHome, o una tableta o un teléfono con su propia cuenta de Home Assistant. Vigil decide qué puede hacer cada panel y qué datos recibe; el propio panel no decide nada. El ID del panel es el nombre del dispositivo ESPHome. En cuanto se vincula una cuenta, las demás cuentas normales ya no pueden manejar la alarma."
    },
    "empty": {
      "sensor": "Aún no hay sensores. Añade primero un grupo de sensores si no hay ninguno, y después tus sensores.",
      "sensor_group": "Aún no hay grupos de sensores. Un grupo de sensores decide en qué modos vigilan los sensores.",
      "rule": "Aún no hay reglas de confirmación. Opcional: una alarma solo después de varios sensores.",
      "user": "Aún no hay usuarios. Sin usuario no hace falta código para manejar la alarma.",
      "notification": "Aún no hay notificaciones. Añade un servicio notify para recibir mensajes.",
      "siren": "Aún no hay sirena. Es opcional; sin sirena, la alarma funciona con notificaciones.",
      "panel": "Aún no hay paneles. Sin un panel registrado, un panel ESPHome no recibe perfil y no maneja nada."
    },
    "save": "Guardar",
    "cancel": "Cancelar",
    "del": "Eliminar",
    "dup": "Copiar",
    "editBtn": "Editar",
    "testBtn": "Probar",
    "close": "Cerrar",
    "ready": {
      "title": "¿Listo para usar?",
      "allGood": "Todo está configurado. Aun así, prueba la alarma con regularidad.",
      "problem": "Corregir primero",
      "advice": "Consejo",
      "go": "Ir allí",
      "createGroups": "Crear grupos predeterminados",
      "groupsMade": "Grupos de sensores creados",
      "addPhone": "Añadir teléfono: {name}",
      "phoneAdded": "{name} añadido; se envió una notificación de prueba. ¿Ha llegado?",
      "text": {
        "no_sensors": "Aún no hay sensores. Añádelos o deja que Vigil los busque.",
        "no_sensor_groups": "Aún no hay grupos de sensores. Sin un grupo, un sensor de intrusión no vigila nada. Vigil puede proponer dos: Perímetro (puertas y ventanas) e Interior (movimiento).",
        "mode_unwatched": "Ningún sensor de intrusión vigila en este modo: {modes}.",
        "no_user_code": "Aún no hay ningún usuario con código, así que nadie puede manejar la alarma.",
        "no_notification": "Aún no hay un canal de notificación, así que no oirás nada cuando salte la alarma. Usa, por ejemplo, la aplicación del teléfono.",
        "no_siren": "No hay sirena. La alarma funciona entonces solo con notificaciones.",
        "battery_missing": "{n} sensores no tienen sensor de batería, así que no te enterarás cuando una batería se agote: {names}.",
        "tamper_unlinked": "{n} sensores tienen un contacto de sabotaje en el mismo dispositivo que no está conectado a nada: {names}.",
        "panel_firmware": "El firmware del panel {name} entiende la versión de perfil {seen}, Vigil usa la versión {wanted}. Actualiza el firmware del panel."
      }
    },
    "heartbeat": {
      "title": "Latido",
      "off": "Desactivado. Introduce una dirección de latido en Ajustes para empezar.",
      "lastOk": "Último correcto",
      "lastFail": "Último fallido",
      "never": "aún no",
      "every": "Cada {n} minutos",
      "test": "Probar ahora",
      "ok": "El latido ha llegado.",
      "failed": "El latido no ha llegado ({reason}).",
      "reason": {
        "timeout": "sin respuesta en 10 segundos",
        "connection": "sin conexión"
      },
      "failing": "Fallando: {reason}"
    },
    "selftest": {
      "title": "Autoprueba",
      "last": "Último control silencioso",
      "lastSiren": "Última prueba de la sirena",
      "next": "Próxima prueba de la sirena",
      "never": "aún no",
      "off": "El recordatorio está desactivado (Ajustes)",
      "noSiren": "No hay ninguna sirena configurada.",
      "overdue": "Vencida: la prueba tocaba hace {days} días.",
      "test": "Probar la sirena ahora",
      "started": "La sirena suena durante {seconds} segundos.",
      "auto": "Vigil hace sonar la sirena por sí mismo dentro de las horas configuradas.",
      "problems": "Falta el canal de notificación: {name}"
    },
    "dash": {
      "title": "Panel de control",
      "text": "Un panel de control con las entidades propias de esta alarma. Cópialo y pégalo en un panel de control nuevo (Ajustes > Paneles de control > nuevo panel de control > editor de configuración sin procesar).",
      "copy": "Copiar el panel de control"
    },
    "log": {
      "intro": "Todo lo que Vigil informa como evento. El registro guarda {days} días (ver Ajustes) y no contiene códigos. Las horas están en tu zona horaria; en las descargas están en UTC como RFC 3339.",
      "empty": "Todavía no hay nada en el registro.",
      "cols": {
        "time": "Hora",
        "event": "Evento",
        "item": "Elemento",
        "who": "Usuario",
        "via": "Mediante",
        "result": "Resultado",
        "noCode": "desconocido (sin código)",
        "installer": "código de instalador",
        "auto": "automático"
      },
      "showing": "Los {n} más recientes de {total}",
      "jsonl": "Descargar (JSON Lines)",
      "csv": "Descargar (CSV)",
      "refresh": "Actualizar"
    },
    "summary": {
      "always": "{cls}, siempre activo",
      "instant": "instantáneo",
      "delayed": "retardado ({s} s)",
      "follower": "seguidor",
      "and": "y",
      "watching": "{type}, vigila en {modes}",
      "nowhere": "{type}, no vigila en ningún modo"
    },
    "whatsNew": "nuevo",
    "batteryLow": "baja",
    "batteryOk": "ok",
    "copySuffix": " (copia)",
    "permBypass": {
      "title": "Anulado permanentemente",
      "intro": "Estos sensores están anulados y no vigilan, tampoco después de desactivar. Restablécelos en cuanto estén reparados:",
      "restore": "Restablecer",
      "restored": "Restablecido"
    },
    "memory": {
      "title": "Última alarma",
      "running": "La alarma sigue activa.",
      "endedBy": "Desactivada a las {time} por {who}.",
      "cancelled": "Cancelada como falsa alarma.",
      "cause": "Causa",
      "first": "Primer sensor",
      "path": "Recorrido por la casa",
      "pathIntro": "Cada sensor que se abrió desde el inicio de la alarma hasta su desactivación, en orden. Se incluyen los sensores que no contaban en este modo o que estaban anulados: juntos muestran por dónde ha pasado alguien.",
      "time": "Hora",
      "sensor": "Sensor",
      "room": "Habitación",
      "counted": "Contado",
      "notCounted": "No contado",
      "times": "abierto {n}×",
      "clear": "Borrar la memoria de alarmas",
      "cleared": "Memoria de alarmas borrada",
      "noRoom": "sin habitación definida",
      "empty": "Ningún sensor se abrió (solo el primer aviso).",
      "steps": "{n} pasos",
      "more": "Solo se conservan los primeros {n} pasos."
    },
    "practice": {
      "chip": "Modo de prueba",
      "title": "Práctica y prueba",
      "text": "Modo de prueba: la alarma funciona como siempre (cuenta atrás, se dispara, los paneles lo muestran) pero no suena ninguna sirena y no sale ningún mensaje. Todo queda en el registro, marcado como prueba. Se detiene a los 30 minutos, o en cuanto desactives.",
      "start": "Iniciar el modo de prueba",
      "stop": "Detener el modo de prueba",
      "left": "Quedan {n} min.",
      "needsOff": "Desactiva primero la alarma.",
      "walk": "Prueba de recorrido: con la alarma desactivada, pasa junto a las puertas, ventanas y sensores de movimiento; cada sensor que reacciona se marca. Solo participan los sensores de intrusión (los sensores de incendio, gas, agua y sabotaje están siempre activos y tienen su propia prueba).",
      "walkStart": "Iniciar la prueba de recorrido",
      "walkTitle": "Prueba de recorrido",
      "walkRunning": "Abre cada puerta o ventana y pasa junto a cada sensor de movimiento. {n} de {total} vistos.",
      "walkStop": "Detener la prueba",
      "walkDone": "Hecho: {seen} de {total} vistos.",
      "walkAgain": "Otra vez",
      "walkMissing": "No visto",
      "walkReason": {
        "no_response": "no reaccionó",
        "unavailable": "no está disponible"
      },
      "walkSeen": "Visto",
      "walkNone": "Todos los sensores reaccionaron.",
      "walkLast": "Última prueba de recorrido: {seen} de {total} vistos ({time}).",
      "close": "Cerrar"
    },
    "wizard": {
      "title": "Configurar Vigil",
      "button": "Asistente de configuración",
      "step": "Paso {n} de {total}",
      "back": "Atrás",
      "next": "Siguiente",
      "skip": "Omitir",
      "finish": "Hecho",
      "stop": "Continuar más tarde",
      "resume": "Continuar el asistente",
      "cardTitle": "Configurar Vigil",
      "cardText": "Todavía no está todo configurado. El asistente te guía paso a paso; puedes omitir cualquier paso y volver más tarde.",
      "start": "Iniciar el asistente",
      "done": "Hecho",
      "todo": "Pendiente",
      "optional": "Recomendado",
      "welcome": {
        "title": "Te damos la bienvenida a Vigil",
        "text": "En unos pocos pasos configuras la alarma: qué modos usas, qué sensores participan, quién recibe un código y cómo te avisan. No se guarda nada hasta que lo confirmes en un paso, y cada cambio se puede deshacer desde la pestaña Copia de seguridad."
      },
      "modes": {
        "title": "¿Qué modos usas?",
        "text": "En casa (estás dentro, se vigila el perímetro), Fuera (nadie en casa), Noche (duermes), Vacaciones (fuera mucho tiempo) y Personalizado (un modo propio, por ejemplo solo el garaje). Elige solo lo que realmente usas; los retardos de salida se pueden cambiar después en Ajustes.",
        "save": "Guardar",
        "saved": "Modos guardados.",
        "none": "Elige al menos un modo."
      },
      "sensors": {
        "title": "Sensores",
        "text": "Vigil busca en Home Assistant sensores de puerta, ventana, movimiento, humo, gas y agua. Tú eliges cuáles añadir.",
        "have": "{n} sensores configurados.",
        "none": "Aún no hay sensores.",
        "find": "Buscar sensores",
        "fresh": "{n} nuevos encontrados."
      },
      "user": {
        "title": "¿Quién puede manejar la alarma?",
        "text": "Un usuario tiene un código. Puedes crear un usuario a partir de una persona de Home Assistant o añadir uno a mano.",
        "have": "{n} usuario(s) con código.",
        "none": "Aún no hay ningún usuario con código.",
        "fromPerson": "Convertir a {name} en usuario",
        "add": "Añadir un usuario"
      },
      "notification": {
        "title": "¿Dónde quieres recibir un mensaje?",
        "text": "Ante una alarma o una avería, Vigil envía un mensaje. Un teléfono con la aplicación de Home Assistant es lo más sencillo.",
        "have": "{n} canal(es) de notificación.",
        "none": "Aún no hay ningún canal de notificación.",
        "phone": "Añadir {name}",
        "add": "Añadir un canal de notificación",
        "added": "Se añadió {name}; se envió un mensaje de prueba."
      },
      "siren": {
        "title": "Sirena",
        "text": "Una sirena no es obligatoria, pero sin ella solo oyes una alarma a través de los mensajes.",
        "have": "{n} sirena(s).",
        "none": "Aún no hay ninguna sirena.",
        "add": "Añadir una sirena"
      },
      "panel": {
        "title": "Panel en la pared",
        "text": "Una pantalla ESPHome, una tableta o un teléfono puede manejar la alarma. Es opcional.",
        "have": "{n} panel(es).",
        "none": "Aún no hay ningún panel.",
        "add": "Vincular un panel"
      },
      "test": {
        "title": "¿Listo para usar?",
        "text": "Esto es lo que aún le falta a Vigil. Todo lo marcado como «problema» sigue impidiendo que la alarma proteja.",
        "allGood": "Todo en orden.",
        "testSiren": "Probar la sirena",
        "sirenStarted": "La sirena suena brevemente."
      },
      "end": {
        "title": "Hecho",
        "text": "Vigil está configurado. Una prueba: activa la alarma, abre una puerta y comprueba si llega tu mensaje. Después puedes añadir automatizaciones con los blueprints incluidos (activar automáticamente cuando todos se van, hacer parpadear las luces ante una alarma, decir un mensaje). Los encuentras en la guía, en Automatizaciones y blueprints."
      }
    },
    "newSensors": {
      "title": "Nuevos sensores encontrados",
      "text": "Estos sensores han aparecido en Home Assistant desde la última vez que Vigil miró. No se ha añadido nada.",
      "review": "Revisar y añadir",
      "later": "Ahora no",
      "badge": "{n} nuevos",
      "dismissed": "De acuerdo, Vigil no volverá a anunciarlos. Aún puedes añadirlos con Buscar sensores.",
      "onlyNew": "Solo se muestran los sensores nuevos.",
      "showAll": "Mostrar todos los sensores",
      "showNew": "Mostrar solo los nuevos"
    },
    "find": {
      "button": "Buscar sensores",
      "title": "Buscar sensores",
      "intro": "Estos sensores se encontraron en Home Assistant. Elige cuáles añadir. No se guarda nada hasta que pulses el botón de abajo.",
      "none": "No se encontraron sensores nuevos. Se muestran los sensores de puerta, ventana, movimiento, humo, gas, agua y sabotaje de un dispositivo integrado.",
      "noGroups": "Algunos sensores de intrusión aún no tienen grupo de sensores. Pon «Sugerir para sensores nuevos» de un grupo de sensores en contactos o movimiento; así podrás añadirlos aquí.",
      "cols": {
        "name": "Nombre",
        "cls": "Clase",
        "entrance": "Entrada",
        "groups": "Grupos de sensores",
        "extra": "Incluido"
      },
      "entranceHelp": "Una entrada recibe un retardo de entrada (tipo «retardado»).",
      "inUse": "ya en uso",
      "needsGroup": "sin grupo de sensores",
      "battery": "batería",
      "tamper": "sabotaje",
      "all": "Seleccionar todo",
      "nothing": "No seleccionar ninguno",
      "add": "Añadir {n}",
      "adding": "Añadiendo…",
      "copy": "Copiar los datos de detección",
      "copyHelp": "Una lista anónima sin nombres ni direcciones, para un informe o para ayudar a probar una integración.",
      "createGroups": "Crear grupos predeterminados",
      "added": "{n} sensores añadidos",
      "failed": "{name}: {error}"
    },
    "confirmDelete": "¿Seguro que quieres eliminar «{name}»?",
    "saved": "Guardado",
    "deleted": "Eliminado",
    "testSent": "Prueba enviada",
    "loading": "Cargando…",
    "loadFailed": "No se pudo cargar Vigil Alarm. ¿Está en marcha la integración?",
    "retry": "Reintentar",
    "sections": {
      "alarm": {
        "0": "Modos y retardos",
        "1": "Qué modos usas, cuánto tiempo tienes para salir y para entrar, y cuánto dura la alarma."
      },
      "chime": {
        "0": "Timbre",
        "1": "Un sonido breve cuando se abre un sensor con la casilla Timbre marcada mientras la alarma está desactivada."
      },
      "codes": {
        "0": "Códigos",
        "1": "Si hace falta un código para activar y qué longitud mínima debe tener un código."
      },
      "startup": {
        "0": "Arranque",
        "1": "Tras reiniciar Home Assistant, Vigil espera a que todos tus sensores estén disponibles (por ejemplo MQTT o Zigbee aún arrancando) antes de informar de que un sensor se ha perdido o de generar una alarma por él. Si siguen sin estar tras este tiempo, se informa."
      },
      "lock": {
        "0": "Bloqueo",
        "1": "Qué ocurre tras códigos erróneos, por panel: primero un bloqueo corto, luego otros más largos, y después un bloqueo permanente que solo desaparece con Quitar bloqueo en Paneles. Un código correcto vuelve a empezar de cero."
      },
      "screen": {
        "0": "Pantalla del panel",
        "1": "Cuándo se apaga la pantalla de un panel ESPHome. Solo se apaga con la alarma desactivada o totalmente activada, nunca durante la cuenta atrás para activar o desactivar."
      },
      "battery": {
        "0": "Baterías",
        "1": "A partir de qué nivel una batería cuenta como baja."
      },
      "log": {
        "0": "Registro de eventos",
        "1": "Cuánto tiempo guarda Vigil los eventos."
      },
      "backup": {
        "0": "Copia de seguridad",
        "1": "Cuántas versiones de tu configuración guarda Vigil (pestaña Copia de seguridad). Un valor más bajo descarta las versiones más antiguas."
      },
      "selftest": {
        "0": "Autoprueba",
        "1": "Vigil te recuerda probar la sirena. Pon el intervalo en 0 para desactivar el recordatorio."
      },
      "heartbeat": {
        "0": "Latido",
        "1": "Vigil llama a esta dirección con regularidad, para que un servicio fuera de tu casa avise cuando Home Assistant o tu internet se detengan."
      }
    },
    "reloadNote": "Al guardar se recarga Vigil Alarm (el estado de la alarma se conserva).",
    "alarm": "Alarma",
    "problems": "Atención",
    "noProblems": "Sin problemas",
    "sensorsNow": "Sensores ahora",
    "coverage": "Qué vigila cada modo",
    "coverageNothing": "sin grupo de sensores: no se vigila nada",
    "alwaysOn": "Siempre activo",
    "sensorsCount": "{n} sensores",
    "state": {
      "disarmed": "Apagada",
      "arming": "Activando",
      "armed": "Activada",
      "pending": "Retardo de entrada",
      "triggered": "ALARMA"
    },
    "mode": {
      "home": "En casa",
      "away": "Fuera",
      "night": "Noche",
      "vacation": "Vacaciones",
      "custom": "Personalizado"
    },
    "zstatus": {
      "closed": "Cerrado",
      "open": "Abierto",
      "unavailable": "Inaccesible",
      "bypassed": "Anulado",
      "bypassed_at_arm": "Anulado al activar",
      "waiting": "Esperando a cerrarse"
    },
    "problem": {
      "battery_low": "batería baja",
      "unavailable": "inaccesible",
      "on_battery": "sin corriente de red"
    },
    "cols": {
      "name": "Nombre",
      "entity": "Entidad",
      "cls": "Clase",
      "type": "Tipo",
      "groups": "Grupos de sensores",
      "rule": "Regla de confirmación",
      "status": "Estado",
      "battery": "Batería",
      "modes": "Activo en los modos",
      "sensors": "Sensores",
      "suggest": "Sugerido para",
      "condition": "Condición",
      "escalate": "Avisar si no se confirma",
      "code": "Código",
      "duress": "Código de coacción",
      "tags": "Etiquetas",
      "bypass": "Anular",
      "tamper": "Puede anular el sabotaje",
      "service": "Servicio",
      "categories": "Categorías",
      "delay": "Retardo",
      "device": "Dispositivo",
      "causes": "Para",
      "maxdur": "Duración máx.",
      "panelId": "ID del panel",
      "conn": "Conexión",
      "allowed": "Restricciones"
    },
    "panel": {
      "tablet": "Cuenta",
      "noUser": "usuario no encontrado",
      "connected": "Conectado",
      "offline": "Inaccesible",
      "noConnection": "Sin conexión",
      "noCard": "Ninguna tarjeta Vigil vista",
      "cardSeen": "Tarjeta Vigil activa",
      "notFound": "No encontrado en ESPHome",
      "unlocked": "Desbloqueado",
      "locked": "Bloqueado durante {s} s",
      "lockedPermanent": "Bloqueado de forma permanente",
      "blocked": "Bloqueado",
      "notWatched": "No supervisado",
      "unlock": "Desbloquear",
      "unlockedDone": "Desbloqueado durante {s} segundos.",
      "clear": "Quitar bloqueo",
      "cleared": "Bloqueo quitado.",
      "nothingLocked": "Este panel no estaba bloqueado.",
      "all": "todos los modos",
      "noDisarm": "sin desactivar",
      "noBypass": "sin anular",
      "noSilence": "sin silenciar",
      "hint": "Desbloquear y quitar el bloqueo solo se puede hacer aquí, no como acción de Home Assistant.",
      "refused": "Esto no es posible."
    },
    "yes": "sí",
    "no": "no",
    "none": "—",
    "immediately": "inmediatamente",
    "condition": "{n} en {s} s",
    "fields": {
      "name": "Nombre",
      "entity_id": "Entidad (sensor binario)",
      "cls": "Clase",
      "type": "Tipo",
      "sensor_groups": "Grupos de sensores",
      "at_arm_open": "Si está abierto al terminar el retardo de salida",
      "entry_delay": "Retardo de entrada (vacío = predeterminado)",
      "gas_type": "Tipo de gas",
      "on_unavailable": "Cuando el sensor pasa a ser inaccesible",
      "battery_entity": "Sensor de batería",
      "tamper_entity": "Entidad de sabotaje (opcional)",
      "chime": "Timbre: sonido cuando este sensor se abre con la alarma desactivada",
      "permanent_bypass": "Mantener la anulación tras desactivar (permanente)",
      "duress_code": "Código de coacción (opcional)",
      "sensor_group.modes": "Activo en los modos",
      "suggest_for": "Sugerir para sensores nuevos",
      "sensors": "Sensores",
      "required": "Sensores necesarios",
      "window": "Ventana de tiempo",
      "escalate": "Avisar si no se confirma",
      "code": "Código",
      "tags": "Etiquetas (separadas por comas)",
      "allowed_modes": "Puede operar en los modos (vacío = todos)",
      "may_bypass": "Puede anular sensores",
      "may_bypass_tamper": "Puede anular el sabotaje",
      "service": "Servicio notify",
      "categories": "Tipos de mensajes",
      "delay": "Retardo",
      "priority": "Prioridad alta",
      "control": "Sirena (sirena, interruptor o luz)",
      "causes": "Suena para",
      "max_duration": "Duración máxima (0 = hasta desactivar)",
      "repeat_every": "Repetir cada (0 = no)",
      "light": "Hacer parpadear la luz",
      "tone_entity": "Entidad de selección de tono",
      "volume_entity": "Entidad de volumen",
      "power_entity": "Entidad del modo de alimentación",
      "power_battery_value": "Valor con batería",
      "tone": "Tono",
      "volume": "Volumen",
      "preset": "Preajuste",
      "device": "Tipo de dispositivo",
      "panel_id": "Nombre del dispositivo ESPHome (ID del panel)",
      "ha_user": "Cuenta de Home Assistant (tableta o teléfono)",
      "language": "Idioma",
      "can_disarm": "Puede desactivar (con un código)",
      "can_bypass": "Puede anular sensores (con un código)",
      "can_silence": "Puede silenciar y confirmar",
      "sensor_list": "Mostrar la lista de sensores",
      "unlock_seconds": "Permanece desbloqueado durante (segundos)",
      "watch": "Vigilar si este panel es accesible (avisar cuando se pierda)",
      "blocked": "Panel bloqueado",
      "panel.code": "Código de instalador de este panel (vacío = ninguno)",
      "panel.allowed_modes": "Puede activar en los modos (vacío = todos)",
      "s.modes": "Modos disponibles",
      "exit_delay_home": "Retardo de salida En casa",
      "exit_delay_away": "Retardo de salida Fuera",
      "exit_delay_night": "Retardo de salida Noche",
      "exit_delay_vacation": "Retardo de salida Vacaciones",
      "exit_delay_custom": "Retardo de salida Personalizado",
      "default_entry_delay": "Retardo de entrada predeterminado",
      "trigger_time": "Duración de la alarma (0 = hasta desactivar)",
      "abort_seconds": "Ventana de cancelación tras sonar la sirena (segundos, 0 = desactivada)",
      "chime_entity": "Timbre: qué produce el sonido",
      "chime_seconds": "El timbre suena durante (segundos)",
      "battery_threshold": "Umbral de batería",
      "backup_versions": "Número de versiones guardadas",
      "code_arm_required": "Código necesario para activar",
      "startup_wait_seconds": "Espera máxima de los sensores tras un reinicio (segundos)",
      "lock_tries_1": "Códigos erróneos antes del primer bloqueo",
      "lock_wait_1": "El primer bloqueo dura (minutos)",
      "lock_tries_2": "Después, códigos erróneos antes del segundo bloqueo",
      "lock_wait_2": "El segundo bloqueo dura (minutos)",
      "lock_tries_3": "Después, códigos erróneos antes del tercer bloqueo",
      "lock_wait_3": "El tercer bloqueo dura (minutos)",
      "lock_tries_4": "Después, códigos erróneos antes del bloqueo permanente",
      "screen_off_seconds": "Apagar la pantalla tras (segundos sin tocar)",
      "screen_off_on_alarm": "Apagar la pantalla también durante una alarma",
      "log_retention_days": "Guardar el registro (días)",
      "selftest_interval_days": "Recordatorio de la prueba de la sirena (días, 0 = desactivado)",
      "selftest_siren_seconds": "La sirena suena en una prueba (segundos)",
      "selftest_auto": "Hacer sonar la sirena por sí sola para la prueba",
      "selftest_window_start": "No antes de (hora)",
      "selftest_window_end": "No después de (hora)",
      "heartbeat_url": "Dirección del latido (vacío = desactivado)",
      "heartbeat_interval_minutes": "Minutos entre latidos",
      "min_code_length": "Longitud mínima del código (caracteres)"
    },
    "helpMore": {
      "at_arm_open": "Qué ocurre si este sensor sigue abierto al terminar el retardo de salida:\n• Anular con aviso (predeterminado): la alarma se activa sin este sensor y recibes un aviso. En cuanto el sensor se cierra, vuelve a vigilarse.\n• Esperar a que se cierre: la alarma se activa y este sensor se ignora hasta que se haya cerrado una vez, sin aviso. Después vuelve a vigilarse.\n• Rechazar la activación: la alarma no se activa y ves qué sensor está abierto. Ciérralo primero.\n• Iniciar el retardo de entrada: la alarma se activa y el sensor abierto cuenta enseguida como disparado. Un sensor directo hace sonar la alarma, un sensor retardado inicia el retardo de entrada.",
      "tamper_entity": "¿Este dispositivo tiene también un contacto de sabotaje? Elígelo aquí. Vigil añade por sí mismo un sensor de sabotaje: siempre vigilando, con su propio interruptor de anulación. No tienes que añadirlo por separado."
    },
    "moreInfo": "Más información",
    "help": {
      "duress_code": "Un segundo código para cuando alguien te obliga a apagar la alarma. Desactiva la alarma como de costumbre y no se nota nada: la sirena permanece en silencio. Mientras tanto, un mensaje silencioso llega a los canales con el tipo de mensaje Coacción. Debe ser distinto de cualquier otro código.",
      "permanent_bypass": "Si anulas este sensor a mano, sigue anulado después de desactivar la alarma, hasta que lo restablezcas tú. Útil para un sensor averiado desde hace tiempo. Sin esta marca, la anulación termina al desactivar. Los sensores de incendio y gas nunca se pueden anular.",
      "chime": "Cuando el sensor se abre con la alarma desactivada, suena un sonido breve a través de lo que hayas elegido en los ajustes. Sin alarma, sin mensaje, nada en el registro. Con la alarma activada no ocurre nada.",
      "abort_seconds": "Quien introduzca un código válido dentro de estos segundos tras sonar la sirena ha causado una falsa alarma: la sirena se detiene y sale un mensaje de «cancelada». 0 lo desactiva. No se aplica a incendio, gas ni sabotaje.",
      "chime_entity": "Una sirena, un interruptor, una luz, un botón o un script que produce un sonido. Puedes dejarlo vacío: el evento Timbre sigue en la entidad de evento, para una automatización propia (por ejemplo un mensaje en un altavoz).",
      "chime_seconds": "Cuánto tiempo permanece encendida una sirena, un interruptor o una luz. Sin efecto en un botón o un script.",
      "may_bypass": "Sin este derecho, el usuario no puede anular ni restablecer un sensor, ni siquiera con un código correcto. Un administrador de Home Assistant siempre puede.",
      "screen_off_seconds": "Se aplica a todos los paneles ESPHome. Con un código a medio escribir o una lista abierta, el panel vuelve primero a la página principal pasado este tiempo, y la pantalla se apaga pasado el mismo tiempo.",
      "screen_off_on_alarm": "Desactivado: la pantalla sigue encendida durante una alarma, para que la ALARMA y su causa sigan visibles. Activado: la pantalla también se apaga entonces. Durante la cuenta atrás para activar o entrar, la pantalla nunca se apaga.",
      "entity_id": "Un sensor binario: encendido significa abierto o alarma.",
      "tamper_entity": "Opcional: el contacto de sabotaje de este dispositivo.",
      "at_arm_open": "Qué le ocurre a este sensor si sigue abierto cuando se activa la alarma.",
      "type": "Instantáneo: alarma de inmediato. Retardado: primero el retardo de entrada. Seguidor: solo salta si antes se abrió un sensor retardado.",
      "sensor_groups": "Un sensor puede estar en varios grupos. Vigila en todos los modos en los que esté activo alguno de sus grupos.",
      "suggest_for": "Opcional. Un sensor nuevo de este tipo (contacto de puerta o movimiento) se incluye automáticamente en este grupo.",
      "sensors": "Solo sensores de intrusión instantáneos.",
      "code": "Déjalo vacío para no cambiarlo.",
      "device": "Panel ESPHome: una pantalla con firmware propio, reconocida por el nombre del dispositivo ESPHome. Tableta o teléfono: un dispositivo con la aplicación o el navegador de Home Assistant, reconocido por la cuenta con la que ha iniciado sesión.",
      "ha_user": "Para una tableta o un teléfono: la cuenta con la que ha iniciado sesión el dispositivo. Vigil reconoce el dispositivo por esa cuenta, no por un texto, así que no se puede imitar. También se puede elegir un administrador, pero ojo: los ajustes de este panel se aplican entonces a todo lo que haga esa cuenta, en cada dispositivo en el que haya iniciado sesión, y Vigil no da aquí a la cuenta derechos de administrador (siempre hace falta un código). Es mejor una segunda cuenta normal para el uso diario.",
      "removeCode": "Quitar código",
      "removeDuress": "Quitar código de coacción",
      "tags": "Las etiquetas no tienen función: maneja la alarma con un código.",
      "categories": "Elige qué mensajes recibe este canal.",
      "service": "Un servicio notify (como mobile_app_phone o un grupo de YAML) o una entidad notify (como notify.family, un grupo notify que creaste como ayudante). Una entidad notify solo recibe un título y un mensaje: la alerta crítica de la prioridad alta no funciona con ella, ni tampoco el botón del mensaje de prueba del autocontrol. Para eso, en un teléfono elige su propio servicio mobile_app_….",
      "priority": "Solo para teléfonos con la aplicación de Home Assistant (un servicio mobile_app_…): una alarma se envía entonces como alerta crítica en iOS y con prioridad alta en Android. En una entidad notify u otro servicio no tiene efecto.",
      "delay": "Solo alarmas: esperar primero, por ejemplo para avisar a un segundo dispositivo solo después de un rato.",
      "profiles": "Tono y volumen por causa (opcional)",
      "preset": "Rellena tono, volumen y duración para una sirena conocida. Elige primero la entidad de encendido/apagado en «Sirena» y Vigil busca las demás entidades del mismo dispositivo. Todo sigue siendo editable.",
      "presetFound": "Encontrado en este dispositivo:",
      "presetNoneFound": "No se encontraron otras entidades en este dispositivo; elígelas tú.",
      "presetNoControl": "Valores rellenados. Elige la entidad de la sirena y vuelve a elegir el preajuste para buscar las demás entidades.",
      "power_battery_value": "El valor de la entidad del modo de alimentación cuando la sirena funciona con batería."
    },
    "opt": {
      "preset": {
        "": "—",
        "sonoff_snzb_09p_z2m": "Sonoff SNZB-09P (Zigbee2MQTT)"
      },
      "cls": {
        "intrusion": "Intrusión",
        "fire": "Incendio",
        "gas": "Gas",
        "tamper": "Sabotaje",
        "water": "Agua",
        "alarm24": "24 horas, audible",
        "silent24": "24 horas, silenciosa"
      },
      "type": {
        "instant": "Instantáneo",
        "delayed": "Retardado (retardo de entrada)",
        "follower": "Seguidor"
      },
      "at_arm_open": {
        "bypass": "Anular con aviso",
        "wait_clear": "Esperar a que se cierre",
        "refuse": "Rechazar la activación",
        "pending": "Iniciar el retardo de entrada"
      },
      "gas_type": {
        "co": "Monóxido de carbono",
        "natural_gas": "Gas natural",
        "lpg": "GLP",
        "other": "Otro"
      },
      "on_unavailable": {
        "default": "Predeterminado de la clase",
        "block": "Bloquear la activación",
        "notify": "Solo avisar",
        "trigger": "Disparar la alarma",
        "bypass": "Activar de todos modos (anular)"
      },
      "categories": {
        "alarm": "Alarma",
        "pending": "Retardo de entrada",
        "arming": "Activar y desactivar",
        "fault": "Averías y avisos",
        "technical": "Alarmas técnicas (agua)",
        "duress": "Coacción (alarma silenciosa)"
      },
      "causes": {
        "intrusion": "Intrusión",
        "fire": "Incendio",
        "gas": "Gas",
        "tamper": "Sabotaje",
        "fault": "Avería de sensor"
      },
      "cause": {
        "intrusion": "Intrusión",
        "fire": "Incendio",
        "gas": "Gas",
        "tamper": "Sabotaje",
        "alarm24": "Alarma de 24 horas"
      },
      "mode": {
        "home": "En casa",
        "away": "Fuera",
        "night": "Noche",
        "vacation": "Vacaciones",
        "custom": "Personalizado"
      },
      "suggest_for": {
        "": "Ninguno",
        "contacts": "Puertas y ventanas (contactos)",
        "motion": "Movimiento"
      },
      "language": {
        "nl": "Nederlands",
        "en": "English",
        "de": "Deutsch",
        "fr": "Français",
        "it": "Italiano",
        "es": "Español"
      },
      "device": {
        "esphome": "Panel ESPHome (pantalla casera)",
        "account": "Tableta o teléfono con Home Assistant"
      },
      "sensor_list": {
        "always": "Mostrar siempre",
        "code": "Solo tras desbloquear",
        "never": "No mostrar nunca"
      }
    },
    "why": {
      "title": "¿Por qué no puedo activar?",
      "intro": "Esto impide activar ahora mismo:",
      "modes": "en {modes}",
      "show": "Mostrar",
      "bypass": "Anular",
      "bypassed": "Anulado",
      "neverBypass": "Los sensores de incendio y gas no se pueden anular: elimina primero la causa.",
      "reason": {
        "alarm_condition": "está abierto (una condición de alarma)",
        "sensor_unavailable": "no responde (y está configurado para impedir la activación)",
        "sensor_open": "está abierto y debe cerrarse para activar",
        "not_disarmed": "la alarma ya está activada"
      },
      "hint": "En el panel y en la tarjeta Vigil, el botón Anular y activar anula y activa de una vez, si tienes el derecho."
    },
    "backup": {
      "intro": "En cada cambio, Vigil guarda la configuración tal como estaba antes de ese cambio (las últimas 10 versiones). Puedes restaurar una de esas versiones; restaurar también es un cambio, así que se puede deshacer de la misma manera. Solo se guardan los ajustes, no el estado de la alarma (activada, anulada).",
      "list": "Versiones guardadas",
      "none": "Aún no hay versiones. Aparecen en cuanto cambies algo.",
      "restore": "Restablecer",
      "reason": {
        "edit": "Cambio",
        "restore": "Restablecido",
        "import": "Importar",
        "external": "Cambiado fuera del panel",
        "upgrade": "Actualización de Vigil"
      },
      "colTime": "Hora",
      "colReason": "Motivo",
      "colVigil": "Versión de Vigil",
      "colChange": "Cambio",
      "view": "Ver",
      "viewTitle": "Cambio del {time}",
      "viewText": "Esta versión guarda la configuración tal como estaba antes de este cambio. El cambio en sí fue:",
      "format": "versión de almacenamiento {v}",
      "notRestorable": "No se puede restaurar: creada por otra versión de almacenamiento ({v}, ahora {now}). Aún se puede ver.",
      "settingsList": "Ajustes: {names}",
      "restoreTitle": "¿Restaurar esta versión?",
      "restoreText": "Restaurar cambia esto respecto a ahora:",
      "nothing": "Sin diferencias con ahora.",
      "restored": "Restablecido",
      "fileTitle": "Exportar e importar",
      "export": "Exportar la configuración",
      "import": "Importar la configuración…",
      "exportNote": "El archivo no contiene códigos, pero sí los códigos con hash, la dirección del latido y los nombres de tus servicios de notificación. Guárdalo en un lugar seguro.",
      "importNote": "Importar sustituye toda la configuración. La actual se guarda como versión, así que una importación se puede restaurar.",
      "importTitle": "¿Importar este archivo?",
      "importText": "Importar cambia esto respecto a ahora:",
      "imported": "Importado",
      "readFailed": "Este archivo no se puede leer.",
      "added": "añadido",
      "removed": "eliminado",
      "changed": "cambiado",
      "settings": "Ajustes cambiados: {n}",
      "undo": "Deshacer",
      "apply": "Aplicar"
    },
    "errors": {
      "backup_invalid": "Este archivo o esta versión no contiene una configuración utilizable.",
      "backup_unknown": "Esta versión ya no existe.",
      "import_not_vigil": "Este no es un archivo de exportación de Vigil Alarm.",
      "import_format_version": "Este archivo tiene un formato desconocido.",
      "import_entry_version": "Este archivo pertenece a otra versión de almacenamiento ({found}, necesaria: {expected}). Impórtalo en la misma versión de Vigil en la que se creó.",
      "name_required": "Introduce un nombre.",
      "name_in_use": "Este nombre ya existe.",
      "required": "Obligatorio.",
      "invalid_config": "No válido: {error}",
      "sensor_not_instant": "Solo los sensores instantáneos pueden estar en una regla de confirmación. Cambia: {sensors}",
      "entity_in_use": "Esta entidad ya es un sensor.",
      "tamper_same_entity": "La entidad de sabotaje debe ser distinta del propio sensor.",
      "tamper_entity_in_use": "Esta entidad ya es un sensor.",
      "no_sensor_group": "Elige al menos un grupo de sensores.",
      "unknown_sensor_group": "Grupo de sensores desconocido.",
      "unknown_mode": "Modo desconocido.",
      "unknown_suggestion": "Opción desconocida.",
      "backup_versions_range": "Elige un número de {min} a {max}.",
      "code_in_use": "Este código ya está en uso.",
      "code_too_short": "El código debe tener al menos {min} caracteres (definido en Ajustes).",
      "code_length_range": "Elige un valor de {min} a {max}.",
      "screen_off_range": "Elige un número de segundos de {min} a {max}.",
      "startup_wait_range": "Elige un número de segundos de {min} a {max}.",
      "lock_tries_range": "Elige un número de veces de {min} a {max}.",
      "lock_wait_range": "Elige un número de minutos de {min} a {max}.",
      "log_retention_range": "Elige un número de días de {min} a {max}.",
      "selftest_range": "Elige un valor de {min} a {max}.",
      "selftest_window": "La hora más tardía debe ser posterior a la más temprana.",
      "heartbeat_url_invalid": "Esto no es una dirección web. Debe empezar por http:// o https://.",
      "heartbeat_range": "Elige un número de minutos de {min} a {max}.",
      "tag_in_use": "Esta etiqueta ya está en uso.",
      "no_credential": "Introduce un código o al menos una etiqueta.",
      "duress_needs_code": "Un código de coacción acompaña a un código normal: introduce primero un código.",
      "duress_no_channel": "No hay ningún canal de notificación con el tipo de mensaje Coacción. Sin él, una alarma silenciosa no llega a nadie. Añade uno primero.",
      "seconds_range": "Elige un número de segundos de {min} a {max}.",
      "chime_entity_domain": "Elige una sirena, un interruptor, una luz, un botón o un script.",
      "service_not_found": "Este servicio notify no existe (ya).",
      "no_categories": "Elige al menos un tipo de mensaje.",
      "no_causes": "Elige al menos una causa.",
      "tone_without_entity": "Un tono necesita una entidad de selección de tono.",
      "volume_without_entity": "Un volumen necesita una entidad de volumen.",
      "sensor_in_rule": "Este sensor sigue en la regla de confirmación: {rules}. Quítalo primero de allí.",
      "sensor_group_in_use": "Este grupo de sensores aún lo usan: {sensors}. Quita primero el grupo de esos sensores.",
      "no_modes": "Elige al menos un modo.",
      "unknown_kind": "Elemento desconocido.",
      "panel_id_invalid": "Usa minúsculas, dígitos, - y _ (como el nombre del dispositivo en ESPHome).",
      "panel_id_in_use": "Este ID de panel ya está registrado.",
      "unlock_range": "Elige un valor de {low} a {high}.",
      "unknown_choice": "Opción desconocida.",
      "ha_user_unknown": "Este usuario no existe o no está activo.",
      "ha_user_in_use": "Este usuario ya está vinculado a otro panel.",
      "generic": "Algo ha salido mal."
    }
  },
};

// "de-AT", "fr_CA", "es-419" ... -> one of the six languages; English for everything else.
function panelLanguage(code) {
  const l = String(code || "en").toLowerCase().slice(0, 2);
  return TXT[l] ? l : "en";
}

const LOGO_URL = "/vigil_alarm_static/logo.png";

// Small stroke icons (24x24, Lucide style), drawn as SVG without innerHTML.
const ICONS = {
  edit: ["M12 20h9", "M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"],
  copy: ["M9 9h11a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H11a2 2 0 0 1-2-2V9Z", "M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"],
  trash: ["M3 6h18", "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6", "M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2", "M10 11v6", "M14 11v6"],
  play: ["M6 3l14 9-14 9Z"],
  book: ["M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2Z", "M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7Z"],
  github: ["M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4", "M9 18c-4.51 2-5-2-7-2"],
  tag: ["M12 2H2v10l9.29 9.29a1 1 0 0 0 1.42 0l6.58-6.58a1 1 0 0 0 0-1.42Z", "M7 7h.01"],
  alert: ["M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Z", "M12 8v4", "M12 16h.01"],
  unlock: ["M7 11V7a5 5 0 0 1 9.9-1", "M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2Z"],
  eye: ["M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z", "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"],
  reset: ["M3 12a9 9 0 1 0 3-6.7", "M3 4v5h5"],
  tablet: ["M6 2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z", "M12 18h.01"],
  file: ["M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2Z", "M14 2v6h6"],
};

function icon(name) {
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  for (const [k, v] of Object.entries({ viewBox: "0 0 24 24", width: "16", height: "16", fill: "none", stroke: "currentColor",
    "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true", class: "icon" })) svg.setAttribute(k, v);
  for (const d of ICONS[name] || []) {
    const path = document.createElementNS(NS, "path");
    path.setAttribute("d", d);
    svg.append(path);
  }
  return svg;
}

// A button with only an icon; the text is the tooltip and the label for screen readers.
function iconButton(name, label, cls, onclick) {
  return el("button", { class: "btn small icon-only " + (cls || ""), title: label, "aria-label": label, onclick }, icon(name));
}

// Which option list belongs to which field.
const OPTION_GROUP = { modes: "mode", allowed_modes: "mode" };
const CONTACT_CLASSES = ["door", "window", "opening", "garage_door"];
const MOTION_CLASSES = ["motion", "occupancy", "presence", "moving"];
const KINDS = ["sensor", "sensor_group", "rule", "user", "notification", "siren", "panel"];
const TABS = ["overview", ...KINDS, "log", "settings", "backup", "about"];

const CSS = `
:host { display: block; height: 100%; background: var(--primary-background-color, #fafafa); color: var(--primary-text-color, #212121);
  font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
* { box-sizing: border-box; }
header { display: flex; align-items: center; gap: 12px; padding: 0 16px; height: 56px; background: var(--app-header-background-color, var(--primary-color, #03a9f4));
  color: var(--app-header-text-color, #fff); position: sticky; top: 0; z-index: 2; }
header h1 { font-size: 20px; font-weight: 400; margin: 0; flex: 1; }
.menu { background: none; border: none; color: inherit; font-size: 24px; cursor: pointer; padding: 4px 8px; }
.chip { padding: 4px 12px; border-radius: 14px; background: rgba(255,255,255,.2); font-size: 13px; }
.chip.alarm { background: var(--error-color, #db4437); font-weight: 600; }
nav { display: flex; gap: 4px; overflow-x: auto; padding: 0 8px; background: var(--card-background-color, #fff); border-bottom: 1px solid var(--divider-color, #e0e0e0); position: sticky; top: 56px; z-index: 1; }
nav button { background: none; border: none; border-bottom: 3px solid transparent; padding: 14px 14px 11px; cursor: pointer; font-size: 14px;
  color: var(--secondary-text-color, #727272); white-space: nowrap; font-family: inherit; }
nav button.active { color: var(--primary-color, #03a9f4); border-bottom-color: var(--primary-color, #03a9f4); }
nav .count { opacity: .7; margin-left: 4px; font-size: 12px; }
main { padding: 16px; max-width: 1200px; margin: 0 auto; }
main.wide { max-width: none; }
.card { background: var(--card-background-color, #fff); border-radius: var(--ha-card-border-radius, 12px); box-shadow: var(--ha-card-box-shadow, 0 1px 3px rgba(0,0,0,.15));
  padding: 16px; margin-bottom: 16px; }
.card h2 { margin: 0 0 12px; font-size: 16px; font-weight: 500; }
.bar { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 12px; gap: 16px; }
.bar .intro { flex: 1; margin: 0; color: var(--secondary-text-color, #727272); font-size: 13px; }
button.btn { font-family: inherit; font-size: 14px; border-radius: 8px; padding: 8px 16px; cursor: pointer; border: 1px solid var(--divider-color, #ccc);
  background: transparent; color: var(--primary-text-color, #212121); }
button.btn.primary { background: var(--primary-color, #03a9f4); color: var(--text-primary-color, #fff); border-color: transparent; }
button.btn.danger { color: var(--error-color, #db4437); }
button.btn.small { padding: 4px 10px; font-size: 13px; }
button.btn.icon-only { padding: 6px 8px; line-height: 0; margin-left: 4px; }
button.btn.icon-only svg { display: block; }
button.btn:disabled { opacity: .5; cursor: default; }
.tablewrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { text-align: left; font-weight: 500; color: var(--secondary-text-color, #727272); padding: 8px 12px; border-bottom: 1px solid var(--divider-color, #e0e0e0); white-space: nowrap; }
td { padding: 10px 12px; border-bottom: 1px solid var(--divider-color, #eee); vertical-align: middle; }
tr.row:hover td { background: var(--secondary-background-color, #f5f5f5); }
td.actions { text-align: right; white-space: nowrap; }
td .sub { display: block; color: var(--secondary-text-color, #727272); font-size: 12px; }
.empty { padding: 32px 16px; text-align: center; color: var(--secondary-text-color, #727272); }
.badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; background: var(--secondary-background-color, #eee); }
.readyrow { margin-bottom: 10px; line-height: 1.9; }
.badge.ok { background: color-mix(in srgb, var(--success-color, #43a047) 18%, transparent); color: var(--success-color, #2e7d32); }
.badge.warn { background: color-mix(in srgb, var(--warning-color, #ffa600) 22%, transparent); color: var(--warning-color, #b26a00); }
.badge.bad { background: color-mix(in srgb, var(--error-color, #db4437) 18%, transparent); color: var(--error-color, #db4437); }
.tags span { margin-right: 4px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.stat { font-size: 26px; font-weight: 500; overflow-wrap: anywhere; }
.muted { color: var(--secondary-text-color, #727272); font-size: 13px; }
.about th { text-align: left; font-weight: 500; width: 40%; padding: 4px 8px 4px 0; color: var(--secondary-text-color, #727272); }
.about td { padding: 4px 0; }
.card > ul.links { list-style: none; padding: 0; margin: 0; }
.links li { padding: 5px 0; display: flex; align-items: center; gap: 10px; }
.links svg { color: var(--secondary-text-color, #727272); flex: none; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
@media (max-width: 700px) { .cols { grid-template-columns: 1fr; gap: 16px; } }
.brand { display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }
.brand img { border-radius: 14px; }
.brand h2 { margin: 0 0 2px; }
a { color: var(--primary-color, #03a9f4); }
.release h3 { margin: 16px 0 4px; font-size: 14px; font-weight: 600; }
.release ul, .card > ul { margin: 0; padding-left: 20px; }
.release li, .card > ul li { margin: 3px 0; font-size: 14px; }
.note { color: var(--secondary-text-color, #727272); font-size: 13px; margin: 8px 0 0; }
ul.plain { margin: 0; padding-left: 18px; }
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 10; padding: 16px; }
.dialog { background: var(--card-background-color, #fff); color: var(--primary-text-color, #212121); border-radius: 16px; width: 100%; max-width: 560px; max-height: 92vh;
  display: flex; flex-direction: column; box-shadow: 0 8px 32px rgba(0,0,0,.4); }
.dialog h2 { margin: 0; padding: 20px 24px 8px; font-size: 20px; font-weight: 500; }
.dialog .body { padding: 8px 24px 8px; overflow-y: auto; }
.dialog .foot { padding: 12px 24px 20px; display: flex; justify-content: flex-end; gap: 8px; }
.field { margin-bottom: 14px; }
.field label.lbl { display: block; font-size: 13px; color: var(--secondary-text-color, #727272); margin-bottom: 4px; }
.field input[type=text], .field input[type=password], .field input[type=number], .field select, .field input.ent {
  width: 100%; box-sizing: border-box; height: 40px; padding: 0 12px; font-size: 15px; line-height: 20px; border-radius: 8px; border: 1px solid var(--divider-color, #bbb);
  background: var(--secondary-background-color, #fff); color: var(--primary-text-color, #212121); font-family: inherit; }
.field.err input, .field.err select { border-color: var(--error-color, #db4437); }
.overlay.top { z-index: 20; }
.dialog.wide { max-width: min(1100px, 96vw); }
.dialog.wide input[type="text"] { min-width: 180px; }
.morelist { margin: 4px 0 8px; padding-left: 20px; }
.morelist li { margin: 8px 0; }
.field .help button.info { flex: none; width: 18px; height: 18px; border-radius: 50%; border: 1px solid var(--secondary-text-color, #727272); background: none; color: var(--secondary-text-color, #727272); font: italic 600 12px/16px serif; cursor: pointer; padding: 0; margin-left: 8px; vertical-align: middle; }
.field .help button.info:hover { color: var(--primary-color, #03a9f4); border-color: var(--primary-color, #03a9f4); }
.field .help { white-space: pre-line; font-size: 12px; color: var(--secondary-text-color, #727272); margin-top: 4px; }
.field .error, .baseerror { font-size: 13px; color: var(--error-color, #db4437); margin-top: 4px; }
.baseerror { padding: 10px 12px; border-radius: 8px; background: color-mix(in srgb, var(--error-color, #db4437) 12%, transparent); margin-bottom: 14px; }
.checks { display: flex; flex-wrap: wrap; gap: 6px 16px; }
.checks label { display: flex; align-items: center; gap: 6px; font-size: 14px; cursor: pointer; }
.inline { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; }
details { margin: 8px 0 14px; border: 1px solid var(--divider-color, #ddd); border-radius: 8px; padding: 8px 12px; }
details summary { cursor: pointer; font-size: 14px; }
details h3 { font-size: 13px; margin: 12px 0 6px; font-weight: 500; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.toastbtn { margin-left: 10px; background: none; border: 0; color: #8ab4f8; font: inherit; font-weight: 600; cursor: pointer; padding: 0; }
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #323232; color: #fff; padding: 10px 20px; border-radius: 8px; z-index: 20; font-size: 14px; }
@media (max-width: 700px) {
  main { padding: 8px; } .pair { grid-template-columns: 1fr; }
  .tablewrap table, .tablewrap tbody, .tablewrap tr, .tablewrap td { display: block; width: 100%; }
  .tablewrap thead { display: none; }
  .tablewrap tr.row { padding: 8px 0; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
  .tablewrap td { border: none; padding: 4px 8px; display: flex; gap: 12px; justify-content: space-between; text-align: right; }
  .tablewrap td::before { content: attr(data-label); color: var(--secondary-text-color, #727272); text-align: left; flex: none; }
  .tablewrap td:first-child { font-weight: 500; font-size: 16px; justify-content: flex-start; }
  .tablewrap td:first-child::before { content: none; }
  .tablewrap td.actions { justify-content: flex-end; flex-wrap: wrap; padding-top: 8px; }
  .tablewrap td.actions::before { content: none; }
  .tablewrap tr:not(.row) td { display: flex; }
}
`;

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (k === "value") node.value = v;
    else if (k === "checked" || k === "disabled" || k === "selected") node[k] = !!v;
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) {
    if (c === undefined || c === null || c === false) continue;
    node.append(c.nodeType ? c : document.createTextNode(String(c)));
  }
  return node;
}

function fill(template, values) {
  return String(template).replace(/\{(\w+)\}/g, (_, k) => (values && values[k] !== undefined ? values[k] : ""));
}

class VigilPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = "overview";
    this._data = null;
    this._live = null;
    this._loadError = false;
    this._sig = "";
    this._unsub = null;
    this._narrow = false;
    this._root = null;
  }

  // ---- properties set by Home Assistant
  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) {
      this._start();
      return;
    }
    const sig = this._signature();
    if (sig !== this._sig) {
      this._sig = sig;
      this._renderBody();
    }
  }
  set narrow(v) { this._narrow = v; this._renderHeader(); }
  set panel(_) {}
  set route(_) {}

  get t() { return TXT[panelLanguage(this._hass && this._hass.language)]; }

  connectedCallback() {
    if (this._hass && this._data) this._subscribe();
  }

  disconnectedCallback() {
    if (this._unsub) { this._unsub.then((u) => u && u()).catch(() => {}); this._unsub = null; }
  }

  // ---- loading
  async _start() {
    this.shadowRoot.innerHTML = "";
    this.shadowRoot.append(el("style", { text: CSS }));
    this._root = el("div");
    this.shadowRoot.append(this._root);
    await this._load();
    this._subscribe();
  }

  async _load(retries = 4) {
    try {
      this._data = await this._hass.callWS({ type: "vigil_alarm/get" });
      const ready = await this._call({ type: "vigil_alarm/readiness" });
      this._ready = ready && ready.findings ? ready.findings : [];
      try { this._heartbeat = await this._hass.callWS({ type: "vigil_alarm/heartbeat" }); } catch (err) { this._heartbeat = null; }
      try { this._selftest = await this._hass.callWS({ type: "vigil_alarm/selftest" }); } catch (err) { this._selftest = null; }
      this._loadError = false;
    } catch (err) {
      if (retries > 0) {
        // The integration reloads after every save; give it a moment.
        await new Promise((r) => setTimeout(r, 1000));
        return this._load(retries - 1);
      }
      this._loadError = true;
    }
    this._sig = this._signature();
    this._render();
  }

  _subscribe() {
    if (this._unsub) return;
    this._unsub = this._hass.connection.subscribeMessage((live) => {
      this._live = live;
      this._renderHeader();
      this._renderBody();
      if (this._walkUpdate) this._walkUpdate();
    }, { type: "vigil_alarm/subscribe" }).catch(() => null);
  }

  // A cheap fingerprint of the Home Assistant states we show, so we only redraw when one changed.
  _signature() {
    if (!this._data || !this._hass) return "";
    const s = this._hass.states;
    const ids = [];
    for (const z of this._data.items.sensor) {
      ids.push(z.data.entity_id, z.data.battery_entity);
    }
    for (const x of this._data.items.siren) ids.push(x.data.control);
    return ids.filter(Boolean).map((id) => (s[id] ? s[id].state : "?")).join("|");
  }

  // ---- rendering
  _render() {
    // An open dialog stays open when the data is reloaded (the wizard goes on after a save).
    const layer = this._root.querySelector("#layer") || el("div", { id: "layer" });
    this._root.replaceChildren(el("div", { id: "header" }), el("div", { id: "nav" }), el("div", { id: "body" }), layer);
    this._renderHeader();
    this._renderBody();
    if (this._wizardShown) this._openWizard();
  }

  _q(id) { return this._root.querySelector(`#${id}`); }

  _renderHeader() {
    if (!this._root || !this._q("header")) return;
    const t = this.t;
    const live = this._live;
    const header = el("header", {},
      this._narrow ? el("button", { class: "menu", "aria-label": "menu", text: "☰", onclick: () => this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true })) }) : null,
      el("h1", { text: t.title }),
      live ? el("span", { class: "chip" + (live.state === "triggered" ? " alarm" : ""),
        text: this._stateText(live) + (live.mode && live.state !== "disarmed" ? " · " + (t.mode[live.mode] || live.mode) : "") }) : null,
      live && live.practice_until ? el("span", { class: "chip alarm", style: "margin-left:8px", text: t.practice.chip }) : null);
    this._q("header").replaceChildren(header);
    this._renderNav();
  }

  // "What's new": a badge on About until the person has looked at it after an update.
  _newVersion() {
    const v = this._data && this._data.version;
    if (!v) return false;
    try {
      const seen = localStorage.getItem("vigil_alarm_seen_version");
      if (seen === null) { localStorage.setItem("vigil_alarm_seen_version", v); return false; }  // first visit: nothing is new
      return seen !== v;
    } catch (err) { return false; }
  }
  _markVersionSeen() {
    try { if (this._data && this._data.version) localStorage.setItem("vigil_alarm_seen_version", this._data.version); } catch (err) { /* private window */ }
  }

  _renderNav() {
    const t = this.t;
    const nav = el("nav", {}, TABS.map((tab) => {
      const count = KINDS.includes(tab) && this._data ? this._shown(tab).length : null;
      const fresh = tab === "about" && this._tab !== "about" && this._newVersion();
      return el("button", { class: tab === this._tab ? "active" : "", onclick: () => { this._tab = tab; if (tab === "log") this._logNode = null; if (tab === "about") { this._about = null; this._markVersionSeen(); } this._renderNav(); this._renderBody(); } },
        t.tabs[tab], count !== null ? el("span", { class: "count", text: `(${count})` }) : null,
        fresh ? el("span", { class: "badge ok", style: "margin-left:6px", text: t.whatsNew }) : null,
        tab === "sensor" && this._newSensors().length ? el("span", { class: "badge warn", style: "margin-left:6px", text: fill(t.newSensors.badge, { n: this._newSensors().length }) }) : null);
    }));
    this._q("nav").replaceChildren(nav);
  }

  _renderBody() {
    if (!this._root || !this._q("body")) return;
    const t = this.t;
    const body = this._q("body");
    if (this._loadError) {
      body.replaceChildren(el("main", {}, el("div", { class: "card empty" }, t.loadFailed, el("div", {}, el("button", { class: "btn primary", text: t.retry, onclick: () => this._load() })))));
      return;
    }
    if (!this._data) {
      body.replaceChildren(el("main", {}, el("div", { class: "empty", text: t.loading })));
      return;
    }
    let content;
    if (this._tab === "overview") content = this._overview();
    else if (this._tab === "log") content = this._logNode || (this._logNode = this._logTab());  // not rebuilt on every live update
    else if (this._tab === "settings") content = this._settings();
    else if (this._tab === "backup") content = this._backupTab();
    else if (this._tab === "about") content = this._aboutTab();
    else content = this._list(this._tab);
    body.replaceChildren(el("main", { class: KINDS.includes(this._tab) || this._tab === "log" ? "wide" : "" }, content));
    this._renderNav();
  }

  // ---- helpers for names and states
  _friendly(entityId) {
    const st = this._hass.states[entityId];
    return st && st.attributes.friendly_name ? st.attributes.friendly_name : entityId;
  }
  _sensorName(id) {
    const z = this._data.items.sensor.find((x) => x.id === id);
    return z ? z.title : id;
  }
  _groupName(id) {
    const g = this._data.items.sensor_group.find((x) => x.id === id);
    return g ? g.title : id;
  }
  // Sensors that watch in a mode: intrusion sensors through their groups, the other classes always.
  _coverage(mode) {
    const groups = this._data.items.sensor_group.filter((g) => (g.data.modes || []).includes(mode));
    return groups.map((g) => ({
      group: g,
      sensors: this._data.items.sensor.filter((s) => (s.data.sensor_groups || []).includes(g.id)),
    }));
  }
  _opt(field, value) {
    const group = OPTION_GROUP[field] || field;
    return (this.t.opt[group] && this.t.opt[group][value]) || value;
  }
  _optList(field, list) {
    return (list || []).map((v) => this._opt(field, v)).join(", ") || this.t.none;
  }
  // The battery level of a sensor as a number, or null if it has no (readable) battery sensor.
  // The items of a kind that have a row in the tables. The tamper contact of a sensor is kept as a
  // sensor of its own, but it is edited with the sensor it belongs to.
  _shown(kind) {
    return this._data.items[kind].filter((i) => !(i.data && i.data.companion_of));
  }
  _batteryLevel(sensor) {
    const battery = sensor.data.battery_entity && this._hass.states[sensor.data.battery_entity];
    const level = battery ? parseFloat(battery.state) : NaN;
    return isNaN(level) ? null : level;
  }
  _batteryCell(sensor) {
    const level = this._batteryLevel(sensor);
    const flag = sensor.data.battery_entity && this._hass.states[sensor.data.battery_entity];
    if (level === null && flag && (flag.state === "on" || flag.state === "off")) {  // only "battery low", no percentage
      return el("span", { class: flag.state === "on" ? "badge warn" : "badge ok", text: flag.state === "on" ? this.t.batteryLow : this.t.batteryOk });
    }
    if (level === null) return this.t.none;
    const low = level <= Number(this._data.entry.data.battery_threshold ?? 20);
    return el("span", { class: low ? "badge warn" : "", text: `${level}%` });
  }
  _sensorBadge(sensor, withBattery = true) {
    const t = this.t;
    const status = this._live && this._live.sensors[sensor.id];
    if (!status) return el("span", { class: "badge", text: t.none });
    const cls = status === "closed" ? "ok" : status === "open" ? "bad" : "warn";
    const badge = el("span", { class: `badge ${cls}`, text: t.zstatus[status] || status });
    const level = this._batteryLevel(sensor);
    return withBattery && level !== null ? el("span", {}, badge, el("span", { class: "muted", text: ` 🔋 ${level}%` })) : badge;
  }
  // One sentence per sensor: how it reacts and when it is watching.
  _sensorSummary(sensor) {
    const t = this.t;
    const d = sensor.data;
    if (d.cls !== "intrusion") return fill(t.summary.always, { cls: String(this._opt("cls", d.cls)).toLowerCase() });
    const modes = [...new Set((d.sensor_groups || []).flatMap((gid) => {
      const g = this._data.items.sensor_group.find((x) => x.id === gid);
      return g ? g.data.modes || [] : [];
    }))];
    const order = this._data.entry.data.modes || [];
    modes.sort((a, b) => order.indexOf(a) - order.indexOf(b));
    const list = modes.map((m) => t.mode[m] || m);
    const names = list.length > 1 ? `${list.slice(0, -1).join(", ")} ${t.summary.and} ${list[list.length - 1]}` : list[0];
    const delay = d.entry_delay !== undefined ? d.entry_delay : this._data.entry.data.default_entry_delay;
    const type = d.type === "delayed" ? fill(t.summary.delayed, { s: delay }) : d.type === "follower" ? t.summary.follower : t.summary.instant;
    return names ? fill(t.summary.watching, { type, modes: names }) : fill(t.summary.nowhere, { type });
  }
  _rulesOfSensor(sensorId) {
    return this._data.items.rule.filter((g) => (g.data.sensors || []).includes(sensorId)).map((g) => g.title);
  }

  // ---- overview
  _coverageCard() {
    const t = this.t;
    const modes = this._data.entry.data.modes || [];
    const always = this._data.items.sensor.filter((x) => x.data.cls !== "intrusion");
    const rows = modes.map((mode) => {
      const cover = this._coverage(mode);
      return el("tr", {},
        el("td", { text: t.mode[mode] || mode }),
        el("td", {}, cover.length
          ? cover.map((c) => el("div", {}, el("strong", { text: c.group.title }), " ",
              el("span", { class: "muted", text: c.sensors.length ? c.sensors.map((x) => x.title).join(", ") : fill(t.sensorsCount, { n: 0 }) })))
          : el("span", { class: "badge warn", text: t.coverageNothing })));
    });
    if (always.length) {
      rows.push(el("tr", {}, el("td", { text: t.alwaysOn }),
        el("td", {}, el("span", { class: "muted", text: always.map((x) => x.title).join(", ") }))));
    }
    return el("div", { class: "card" }, el("h2", { text: t.coverage }),
      el("div", { class: "tablewrap" }, el("table", {}, el("tbody", {}, rows))));
  }

  // The alarm reports armed_home, armed_away, armed_night; the mode is shown next to the state.
  _stateText(live) {
    const key = live.state.startsWith("armed_") ? "armed" : live.state;
    return this.t.state[key] || live.state;
  }

  _readyCard() {
    const t = this.t;
    const r = t.ready;
    const findings = this._ready || [];
    const go = (f) => {
      if (f.go === "add_phone") {
        return el("span", {}, (f.phones || []).map((ph) => el("button", { class: "btn", text: fill(r.addPhone, { name: ph.title }), onclick: async () => {
          const res = await this._call({ type: "vigil_alarm/add_phone", service: ph.service });
          if (!res.ok) { this._toast(this._errorText(Object.keys(res.errors || {})[0] || "base", res)); return; }
          await this._load();
          try { await this._hass.callService("vigil_alarm", "test_notification", { channel: res.title }); } catch (err) { /* shown by the toast below */ }
          this._toast(fill(r.phoneAdded, { name: res.title }));
        } })), el("button", { class: "btn", text: r.go, onclick: () => { this._tab = "notification"; this._renderBody(); } }));
      }
      if (f.go === "create_groups") {
        return el("button", { class: "btn", text: r.createGroups, onclick: async () => {
          const res = await this._call({ type: "vigil_alarm/create_default_groups" });
          if (res.ok) { this._toast(r.groupsMade); await this._load(); }
        } });
      }
      return el("button", { class: "btn", text: r.go, onclick: () => { this._tab = f.go; this._renderBody(); } });
    };
    const row = (f) => el("li", { class: "readyrow" },
      el("span", { class: "badge " + (f.level === "problem" ? "bad" : "warn"), text: f.level === "problem" ? r.problem : r.advice }),
      " ", fill(r.text[f.code] || f.code, f.params), " ", go(f));
    return el("div", { class: "card" }, el("h2", { text: r.title }),
      findings.length ? el("button", { class: "btn", text: t.wizard.button, onclick: () => this._openWizard() }) : null,
      findings.length ? el("ul", { class: "plain" }, findings.map(row)) : el("div", { class: "muted", text: r.allGood }));
  }

  _selftestCard() {
    const t = this.t.selftest;
    const st = this._selftest;
    if (!st) return null;
    const when = (iso) => { if (!iso) return t.never; const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleString(); };
    const row = (label, value) => el("tr", {}, el("td", { text: label }), el("td", { text: value }));
    const rows = [row(t.last, when(st.last_check))];
    if (st.siren) rows.push(row(t.lastSiren, when(st.last_siren_test)));
    if (st.siren && st.enabled) rows.push(row(t.next, when(st.due)));
    return el("div", { class: "card" }, el("h2", { text: t.title }),
      el("div", { class: "tablewrap" }, el("table", {}, el("tbody", {}, rows))),
      ...(st.problems || []).map((p) => el("div", { class: "muted", text: fill(t.problems, { name: p.name }) })),
      st.overdue_days != null ? el("div", { class: "badge bad", text: fill(t.overdue, { days: st.overdue_days }) }) : null,
      !st.siren ? el("div", { class: "muted", text: t.noSiren }) : (!st.enabled ? el("div", { class: "muted", text: t.off }) : null),
      st.siren && st.auto ? el("div", { class: "muted", text: t.auto }) : null,
      st.siren ? el("button", { class: "btn", text: t.test, onclick: async () => {
        try {
          await this._hass.callService("vigil_alarm", "test_siren", { duration: st.seconds });
          this._toast(fill(t.started, { seconds: st.seconds }));
          await this._load();
          this._renderBody();
        } catch (err) { this._toast(String((err && err.message) || err)); }
      } }) : null);
  }

  _heartbeatCard(status) {
    const t = this.t.heartbeat;
    const st = status || this._heartbeat;
    if (!st) return null;
    const when = (iso) => { if (!iso) return t.never; const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleString(); };
    const why = (r) => (t.reason[r] || (String(r).startsWith("http_") ? "HTTP " + String(r).slice(5) : r));
    const row = (label, value) => el("tr", {}, el("td", { text: label }), el("td", { text: value }));
    if (!st.enabled) return el("div", { class: "card" }, el("h2", { text: t.title }), el("div", { class: "muted", text: t.off }));
    return el("div", { class: "card" }, el("h2", { text: t.title }),
      el("div", { class: "muted", text: fill(t.every, { n: st.interval }) }),
      el("div", { class: "tablewrap" }, el("table", {}, el("tbody", {}, [row(t.lastOk, when(st.last_ok)), row(t.lastFail, when(st.last_failure))]))),
      st.failures ? el("div", { class: "badge bad", text: fill(t.failing, { reason: why(st.reason) }) }) : null,
      el("button", { class: "btn", text: t.test, onclick: async () => {
        try {
          const res = await this._hass.callWS({ type: "vigil_alarm/heartbeat", test: true });
          this._heartbeat = res;
          this._toast(res.failures ? fill(t.failed, { reason: why(res.reason) }) : t.ok);
          this._renderBody();
        } catch (err) { this._toast(String((err && err.message) || err)); }
      } }));
  }

  // Why arming is refused now, per sensor, with what can be done about it (the live view says what stops each mode).
  _whyCard() {
    const t = this.t, w = t.why;
    const blockers = this._live && this._live.blockers ? this._live.blockers : {};
    const rows = new Map();
    for (const [mode, list] of Object.entries(blockers)) {
      for (const b of list) {
        const key = `${b.sensor || ""}|${b.reason}`;
        if (!rows.has(key)) rows.set(key, { ...b, modes: [] });
        rows.get(key).modes.push(t.mode[mode] || mode);
      }
    }
    if (!rows.size) return null;
    const list = [...rows.values()].map((r) => {
      const call = (service) => this._hass.callService("vigil_alarm", service, { sensor: r.entity_id });
      return el("li", {},
        el("strong", { text: r.name || "" }), r.name ? " " : "", w.reason[r.reason] || r.reason, " ",
        el("span", { class: "muted", text: fill(w.modes, { modes: r.modes.join(", ") }) }), " ",
        r.entity_id ? el("button", { class: "btn", text: w.show, onclick: () => this.dispatchEvent(new CustomEvent("hass-more-info", { bubbles: true, composed: true, detail: { entityId: r.entity_id } })) }) : null,
        r.bypassable && r.entity_id ? el("button", { class: "btn", text: w.bypass, onclick: async () => { try { await call("bypass"); this._toast(w.bypassed); } catch (err) { this._toast(String((err && err.message) || err)); } } }) : null);
    });
    const never = [...rows.values()].some((r) => r.sensor && !r.bypassable);
    return el("div", { class: "card" }, el("h2", { text: w.title }), el("p", { class: "muted", text: w.intro }),
      el("ul", { class: "plain" }, list), never ? el("p", { class: "note", text: w.neverBypass }) : null, el("p", { class: "note", text: w.hint }));
  }

  // ---- the last alarm and the path through the house
  _permBypassCard() {
    const t = this.t.permBypass;
    const list = (this._live && this._live.permanent_bypassed) || [];
    if (!list.length) return null;
    return el("div", { class: "card" }, el("h2", { text: t.title }), el("p", { class: "muted", text: t.intro }),
      el("ul", { class: "plain" }, list.map((r) => el("li", {},
        el("strong", { text: r.name }), " ",
        r.entity_id ? el("button", { class: "btn", text: t.restore, onclick: async () => {
          try { await this._hass.callService("vigil_alarm", "unbypass", { sensor: r.entity_id }); this._toast(t.restored); }
          catch (err) { this._toast(String((err && err.message) || err)); }
        } }) : null))));
  }
  _memoryCard() {
    const t = this.t.memory;
    const m = this._live && this._live.alarm_memory;
    if (!m) return null;
    const when = (ts) => new Date(ts * 1000).toLocaleString();
    const clock = (ts) => new Date(ts * 1000).toLocaleTimeString();
    const status = m.recording ? t.running
      : m.cancelled ? t.cancelled
      : m.ended ? fill(t.endedBy, { time: clock(m.ended), who: m.ended_by || "—" }) : "";
    const cause = (this.t.opt.cause || {})[m.cause] || m.cause || "—";
    const rows = (m.path || []).map((p) => el("tr", {},
      el("td", { text: clock(p.t) }),
      el("td", { text: p.name + (p.n > 1 ? " (" + fill(t.times, { n: p.n }) + ")" : "") }),
      el("td", { text: p.area || t.noRoom }),
      el("td", { text: p.counted ? t.counted : t.notCounted })));
    const clear = async () => {
      await this._call({ type: "vigil_alarm/alarm_memory_clear" });
      this._toast(t.cleared);
    };
    return el("div", { class: "card" }, el("h2", { text: t.title }),
      el("p", { class: m.recording ? "badge warn" : "muted", text: when(m.started) + " · " + cause + " · " + (m.sensor_name || "—") }),
      status ? el("p", { class: "muted", text: status }) : null,
      el("p", { class: "muted", text: t.pathIntro }),
      rows.length ? el("div", { class: "tablewrap" }, el("table", {},
        el("thead", {}, el("tr", {}, [t.time, t.sensor, t.room, ""].map((x) => el("th", { text: x })))),
        el("tbody", {}, rows))) : el("p", { class: "muted", text: t.empty }),
      m.steps >= 200 ? el("p", { class: "note", text: fill(t.more, { n: 200 }) }) : null,
      m.recording ? null : el("button", { class: "btn", style: "margin-top:12px", text: t.clear, onclick: clear }));
  }

  // ---- practice mode and walk test
  _practiceCard() {
    const t = this.t.practice;
    const live = this._live;
    if (!live) return null;
    const on = !!live.practice_until;
    const left = on ? Math.max(1, Math.ceil((live.practice_until - Date.now() / 1000) / 60)) : 0;
    const walk = live.walktest || {};
    const last = walk.last;
    const toggle = async () => {
      try { await this._hass.callWS({ type: "vigil_alarm/practice", enable: !on }); } catch (err) { this._toast(live.state !== "disarmed" ? t.needsOff : String((err && err.message) || err)); }
    };
    return el("div", { class: "card" }, el("h2", { text: t.title }),
      el("p", { class: "muted", text: t.text }),
      on ? el("p", { class: "badge warn", text: t.chip + " · " + fill(t.left, { n: left }) }) : null,
      el("button", { class: "btn" + (on ? "" : " primary"), text: on ? t.stop : t.start, onclick: toggle }),
      el("p", { class: "muted", style: "margin-top:16px", text: t.walk }),
      last && !walk.active ? el("p", { class: "muted", text: fill(t.walkLast, { seen: last.total - last.missing.length, total: last.total, time: new Date(last.time).toLocaleString() }) }) : null,
      el("button", { class: "btn", text: t.walkStart, onclick: () => this._openWalkTest() }));
  }

  _openWalkTest() {
    const t = this.t.practice;
    const body = el("div");
    let close = () => {};
    const draw = () => {
      const walk = (this._live && this._live.walktest) || {};
      const nodes = [];
      if (walk.active) {
        const seen = walk.sensors.filter((s) => s.seen).length;
        nodes.push(el("p", { text: fill(t.walkRunning, { n: seen, total: walk.sensors.length }) }),
          el("ul", { class: "plain" }, walk.sensors.map((s) => el("li", {},
            el("span", { class: "badge " + (s.seen ? "ok" : ""), text: s.seen ? t.walkSeen : "…" }), " ", s.name))));
      } else if (this._walkStarted && walk.last) {
        const l = walk.last, seen = l.total - l.missing.length;
        nodes.push(el("p", { text: fill(t.walkDone, { seen, total: l.total }) }),
          l.missing.length
            ? el("div", {}, el("h3", { text: t.walkMissing }), el("ul", { class: "plain" }, l.missing.map((m) => el("li", {}, el("strong", { text: m.name }), " ", t.walkReason[m.reason] || m.reason))))
            : el("p", { class: "badge ok", text: t.walkNone }));
      }
      body.replaceChildren(...nodes);
      stopBtn.style.display = walk.active ? "" : "none";
      againBtn.style.display = walk.active ? "none" : "";
    };
    this._walkUpdate = draw;
    const stopBtn = el("button", { class: "btn danger", text: t.walkStop });
    const againBtn = el("button", { class: "btn primary", text: t.walkAgain });
    stopBtn.addEventListener("click", async () => { try { await this._hass.callWS({ type: "vigil_alarm/walktest", action: "stop" }); } catch (err) { /* nothing was running */ } draw(); });
    const start = async () => {
      try { await this._hass.callWS({ type: "vigil_alarm/walktest", action: "start" }); this._walkStarted = true; }
      catch (err) { this._toast(t.needsOff); }
      draw();
    };
    againBtn.addEventListener("click", start);
    this._walkStarted = false;
    this._dialog(t.walkTitle, [el("p", { class: "muted", text: t.walk }), body], (closeDialog) => {
      close = () => { this._walkUpdate = null; closeDialog(); };
      return [stopBtn, againBtn, el("button", { class: "btn", text: t.close, onclick: close })];
    }, true);
    start();
  }

  // ---- setup wizard: steps that use the same forms as the tabs; every step can be skipped and the wizard can be reopened
  _wizardStatus() {
    const d = this._data, n = (k) => this._shown(k).length;
    return {
      modes: (d.entry.data.modes || []).length > 0,
      sensors: n("sensor") > 0,
      user: d.items.user.some((u) => u.has_code),
      notification: n("notification") > 0,
      siren: n("siren") > 0,
      panel: n("panel") > 0,
    };
  }

  _wizardNeeded() {
    return (this._ready || []).some((f) => f.level === "problem");
  }

  _openWizard() {
    if (!this._data || !this._root || !this._q("layer")) return;
    const t = this.t, w = t.wizard;
    const steps = ["welcome", "modes", "sensors", "user", "notification", "siren", "panel", "test", "end"];
    const at = Math.min(Math.max(this._wizard ? this._wizard.step : 0, 0), steps.length - 1);
    this._wizard = { step: at };
    this._wizardShown = true;
    const id = steps[at];
    const status = this._wizardStatus();
    const sub = w[id];
    const go = (step) => { this._wizard.step = step; this._openWizard(); };
    // Open one of the normal forms on top of the wizard; closing it brings the wizard back.
    const via = (open) => () => { this._wizardResume = true; this._wizardShown = false; open(); };
    const badge = (done, optional) => el("span", { class: "badge " + (done ? "ok" : optional ? "" : "warn"), text: done ? w.done : optional ? w.optional : w.todo });
    const body = [el("p", { class: "muted", text: fill(w.step, { n: at + 1, total: steps.length }) }), el("p", { text: sub.text })];
    const row = (label, done, optional) => el("p", {}, badge(done, optional), " ", label);
    const btn = (text, onclick, primary = true) => el("button", { class: "btn" + (primary ? " primary" : ""), text, onclick });
    const count = (k) => this._shown(k).length;

    if (id === "modes") {
      const have = new Set(this._data.entry.data.modes || []);
      const boxes = ["home", "away", "night", "vacation", "custom"].map((m) => {
        const input = el("input", { type: "checkbox", checked: have.has(m), "aria-label": t.mode[m] || m });
        return { m, input, node: el("label", { class: "check" }, input, " ", t.mode[m] || m) };
      });
      const msg = el("div");
      body.push(el("div", {}, boxes.map((b) => el("div", {}, b.node))), msg,
        btn(sub.save, async () => {
          const modes = boxes.filter((b) => b.input.checked).map((b) => b.m);
          if (!modes.length) { msg.replaceChildren(el("div", { class: "baseerror", text: sub.none })); return; }
          const res = await this._call({ type: "vigil_alarm/save_settings", data: { ...this._data.entry.data, modes } });
          if (res.ok) { this._toast(sub.saved); await this._load(); } else msg.replaceChildren(el("div", { class: "baseerror", text: this._errorText(Object.keys(res.errors || {})[0] || "base", res) }));
        }, false));
    } else if (id === "sensors") {
      const fresh = this._newSensors().length;
      body.push(row(count("sensor") ? fill(sub.have, { n: count("sensor") }) : sub.none, status.sensors),
        fresh ? el("p", { class: "muted", text: fill(sub.fresh, { n: fresh }) }) : null,
        btn(sub.find, via(() => this._openFind({ onlyNew: false }))));
    } else if (id === "user") {
      const users = this._data.items.user.filter((u) => u.has_code).length;
      body.push(row(users ? fill(sub.have, { n: users }) : sub.none, status.user));
      const have = new Set(this._data.items.user.map((u) => u.title.toLowerCase()));
      const people = Object.values(this._hass.states).filter((x) => x.entity_id.startsWith("person.") && !have.has(String((x.attributes || {}).friendly_name || "").toLowerCase()));
      body.push(el("div", {}, people.slice(0, 6).map((x) => btn(fill(sub.fromPerson, { name: x.attributes.friendly_name || x.entity_id }), via(() => this._openForm("user", null, false, { name: x.attributes.friendly_name || x.entity_id })), false))),
        btn(sub.add, via(() => this._openForm("user"))));
    } else if (id === "notification") {
      body.push(row(count("notification") ? fill(sub.have, { n: count("notification") }) : sub.none, status.notification));
      const phones = ((this._ready || []).find((f) => f.go === "add_phone") || {}).phones || [];
      body.push(el("div", {}, phones.map((ph) => btn(fill(sub.phone, { name: ph.title }), async () => {
        const res = await this._call({ type: "vigil_alarm/add_phone", service: ph.service });
        if (!res.ok) { this._toast(this._errorText(Object.keys(res.errors || {})[0] || "base", res)); return; }
        await this._load();
        try { await this._hass.callService("vigil_alarm", "test_notification", { channel: res.title }); } catch (err) { /* the toast says enough */ }
        this._toast(fill(sub.added, { name: res.title }));
      }, false))), btn(sub.add, via(() => this._openForm("notification"))));
    } else if (id === "siren") {
      body.push(row(count("siren") ? fill(sub.have, { n: count("siren") }) : sub.none, status.siren, true), btn(sub.add, via(() => this._openForm("siren"))));
    } else if (id === "panel") {
      body.push(row(count("panel") ? fill(sub.have, { n: count("panel") }) : sub.none, status.panel, true), btn(sub.add, via(() => this._openForm("panel"))));
    } else if (id === "test") {
      const findings = this._ready || [];
      body.push(findings.length
        ? el("ul", { class: "plain" }, findings.map((f) => el("li", { class: "readyrow" },
            el("span", { class: "badge " + (f.level === "problem" ? "bad" : "warn"), text: f.level === "problem" ? t.ready.problem : t.ready.advice }), " ", fill(t.ready.text[f.code] || f.code, f.params))))
        : el("p", { class: "badge ok", text: sub.allGood }),
        count("siren") ? btn(sub.testSiren, async () => {
          try { await this._hass.callService("vigil_alarm", "test_siren", { duration: 3 }); this._toast(sub.sirenStarted); } catch (err) { this._toast(String((err && err.message) || err)); }
        }, false) : null);
    }

    const last = at === steps.length - 1;
    const stop = () => { this._wizardShown = false; this._wizard = last ? null : this._wizard; this._q("layer").replaceChildren(); this._renderBody(); };
    this._dialog(w.title + ": " + sub.title, body, () => [
      last ? null : el("button", { class: "btn", text: w.stop, onclick: stop }),
      at > 0 ? el("button", { class: "btn", text: w.back, onclick: () => go(at - 1) }) : null,
      last ? el("button", { class: "btn primary", text: w.finish, onclick: stop })
        : el("button", { class: "btn primary", text: (at > 0 && at < steps.length - 2 && !status[id]) ? w.skip : w.next, onclick: () => go(at + 1) }),
    ], true, true);
  }

  _wizardCard() {
    const t = this.t.wizard;
    if (!this._wizardNeeded() && !this._wizard) return null;
    return el("div", { class: "card" }, el("h2", { text: t.cardTitle }), el("p", { class: "muted", text: t.cardText }),
      el("button", { class: "btn primary", text: this._wizard ? t.resume : t.start, onclick: () => this._openWizard() }));
  }

  _newSensors() { return (this._live && this._live.new_sensors) || []; }

  // "New sensors found": the discovery found sensors Vigil has not offered before. Nothing is added by itself.
  _newSensorsCard() {
    const t = this.t, n = t.newSensors;
    const found = this._newSensors();
    if (!found.length) return null;
    const names = found.slice(0, 5).map((e) => e.name).join(", ") + (found.length > 5 ? ` +${found.length - 5}` : "");
    return el("div", { class: "card" }, el("h2", { text: `${n.title} (${found.length})` }), el("p", { class: "muted", text: n.text }),
      el("p", { text: names }),
      el("button", { class: "btn primary", text: n.review, onclick: () => this._openFind({ onlyNew: true }) }),
      el("button", { class: "btn", text: n.later, onclick: async () => {
        try { await this._hass.callWS({ type: "vigil_alarm/new_sensors_dismiss" }); this._toast(n.dismissed); } catch (err) { this._toast(String((err && err.message) || err)); }
      } }));
  }

  _overview() {
    const t = this.t;
    const live = this._live;
    const problems = live ? live.problems : [];
    const sensors = this._data.items.sensor;
    return el("div", {},
      el("div", { class: "grid" },
        el("div", { class: "card" }, el("h2", { text: t.alarm }),
          el("div", { class: "stat", text: live ? this._stateText(live) : t.none }),
          el("div", { class: "muted", text: live && live.mode ? (t.mode[live.mode] || live.mode) : "" })),
        ...KINDS.map((k) => el("div", { class: "card", style: "cursor:pointer", onclick: () => { this._tab = k; this._renderBody(); } },
          el("h2", { text: t.tabs[k] }), el("div", { class: "stat", text: String(this._shown(k).length) })))),
      this._wizardCard(),
      this._newSensorsCard(),
      this._permBypassCard(),
      this._memoryCard(),
      this._practiceCard(),
      this._whyCard(),
      this._readyCard(),
      this._selftestCard(),
      this._heartbeatCard(),
      el("div", { class: "card" }, el("h2", { text: t.dash.title }), el("p", { class: "muted", text: t.dash.text }),
        el("button", { class: "btn", text: t.dash.copy, onclick: async () => {
          const res = await this._call({ type: "vigil_alarm/dashboard" });
          try { await navigator.clipboard.writeText(res.yaml); this._toast(t.about.copied); }
          catch (err) { this._toast(t.about.copyFailed); }
        } })),
      el("div", { class: "card" }, el("h2", { text: t.problems }),
        problems.length
          ? el("ul", { class: "plain" }, problems.map((p) => el("li", { text: `${p.name}: ${t.problem[p.problem] || p.problem}${p.level !== undefined ? ` (${p.level}%)` : ""}` })))
          : el("div", { class: "muted", text: t.noProblems })),
      this._coverageCard(),
      el("div", { class: "card" }, el("h2", { text: t.sensorsNow }),
        sensors.length
          ? el("div", { class: "tablewrap" }, el("table", {}, el("tbody", {}, sensors.map((z) =>
              el("tr", {}, el("td", { text: z.title }), el("td", {}, this._sensorBadge(z)))))))
          : el("div", { class: "muted", text: t.empty.sensor })));
  }

  // ---- list tabs
  _columns(kind) {
    const t = this.t;
    const C = t.cols;
    const state = (id) => (this._hass.states[id] || {}).state;
    const named = (id) => (id ? el("span", {}, this._friendly(id), el("span", { class: "sub", text: id })) : t.none);
    switch (kind) {
      case "sensor": return [
        [C.name, (i) => el("span", {}, i.title, el("span", { class: "sub", text: this._sensorSummary(i) }))],
        [C.entity, (i) => el("span", {}, named(i.data.entity_id),
          i.data.tamper_entity ? el("span", { class: "sub", text: `${t.tamperShort}: ${i.data.tamper_entity}` }) : null)],
        [C.cls, (i) => this._opt("cls", i.data.cls)],
        [C.type, (i) => (i.data.cls === "intrusion" ? this._opt("type", i.data.type || "instant") : t.none)],
        [C.groups, (i) => (i.data.cls === "intrusion" ? (i.data.sensor_groups || []).map((g) => this._groupName(g)).join(", ") || t.none : t.alwaysOn)],
        [C.rule, (i) => this._rulesOfSensor(i.id).join(", ") || t.none],
        [C.status, (i) => this._sensorBadge(i, false)],
        [C.battery, (i) => this._batteryCell(i)],
      ];
      case "sensor_group": return [
        [C.name, (i) => i.title],
        [C.modes, (i) => this._optList("modes", i.data.modes)],
        [C.sensors, (i) => this._data.items.sensor.filter((s) => (s.data.sensor_groups || []).includes(i.id)).map((s) => s.title).join(", ") || t.none],
        [C.suggest, (i) => this._opt("suggest_for", i.data.suggest_for || "")],
      ];
      case "rule": return [
        [C.name, (i) => i.title],
        [C.sensors, (i) => (i.data.sensors || []).map((z) => this._sensorName(z)).join(", ")],
        [C.condition, (i) => fill(t.condition, { n: i.data.required, s: i.data.window })],
        [C.escalate, (i) => (i.data.escalate ? t.yes : t.no)],
      ];
      case "user": return [
        [C.name, (i) => i.title],
        [C.code, (i) => (i.has_code ? "✓" : t.none)],
        [C.duress, (i) => (i.has_duress ? "✓" : t.none)],
        [C.tags, (i) => (i.data.tags && i.data.tags.length ? i.data.tags.length : t.none)],
        [C.modes, (i) => (i.data.allowed_modes && i.data.allowed_modes.length ? this._optList("allowed_modes", i.data.allowed_modes) : "*")],
        [C.bypass, (i) => (i.data.may_bypass !== false ? t.yes : t.no)],
        [C.tamper, (i) => (i.data.may_bypass_tamper ? t.yes : t.no)],
      ];
      case "notification": return [
        [C.name, (i) => i.title],
        [C.service, (i) => String(i.data.service).includes(".") ? i.data.service : `notify.${i.data.service}`],
        [C.categories, (i) => this._optList("categories", i.data.categories)],
        [C.delay, (i) => (i.data.delay ? `${i.data.delay} s` : t.immediately)],
      ];
      case "panel": return [
        [C.name, (i) => i.title],
        [C.panelId, (i) => i.data.panel_id],
        [C.conn, (i) => this._panelBadges(i)],
        [C.allowed, (i) => this._panelLimits(i)],
      ];
      case "siren": return [
        [C.name, (i) => i.title],
        [C.device, (i) => named(i.data.control)],
        [C.causes, (i) => this._optList("causes", i.data.causes)],
        [C.maxdur, (i) => (i.data.max_duration ? `${i.data.max_duration} s` : t.none)],
        [C.status, (i) => {
          const s = state(i.data.control);
          return el("span", { class: "badge " + (s === undefined || s === "unavailable" ? "bad" : "ok"), text: s === undefined ? "?" : s });
        }],
      ];
    }
    return [];
  }

  // The live state of one register entry, from the subscription.
  _panelLive(item) {
    return ((this._live && this._live.panels) || []).find((p) => p.id === item.id) || null;
  }
  _panelBadges(item) {
    const P = this.t.panel;
    const live = this._panelLive(item);
    const badge = (cls, text) => el("span", { class: "badge " + cls, text });
    const out = [];
    if (item.data.blocked) out.push(badge("bad", P.blocked));
    else if (item.data.watch === false) {
      // Not watched on purpose (a phone): no "not reachable" and no Repair, so say that it is not monitored.
      out.push(badge("", P.notWatched));
      if (item.data.ha_user) {
        const who = ((this._data.ha_users || []).find((u) => u.id === item.data.ha_user) || {}).name;
        out.push(badge(who ? "ok" : "warn", who ? `${P.tablet}: ${who}` : `${P.tablet}: ${P.noUser}`));
        if (live && live.card) out.push(badge("ok", P.cardSeen));
      } else if (live) out.push(badge(live.connected ? "ok" : "", live.connected ? P.connected : P.noConnection));
    }
    else if (item.data.ha_user) {
      const who = ((this._data.ha_users || []).find((u) => u.id === item.data.ha_user) || {}).name;
      out.push(badge(who ? "ok" : "warn", who ? `${P.tablet}: ${who}` : `${P.tablet}: ${P.noUser}`));
      // Only the Vigil card says hello, so only then can Vigil tell that the tablet has gone quiet.
      if (live && live.card) out.push(badge(live.offline ? "bad" : "ok", live.offline ? P.offline : P.cardSeen));
      else out.push(badge("", P.noCard));
    }
    else if (!live) out.push(badge("", this.t.none));
    else if (live.connected === null) out.push(badge("warn", P.notFound));
    else if (live.connected) out.push(badge("ok", P.connected));
    else out.push(badge(live.offline ? "bad" : "warn", live.offline ? P.offline : P.noConnection));
    if (live && live.unlocked) out.push(badge("", P.unlocked));
    if (live && live.locked_permanent) out.push(badge("bad", P.lockedPermanent));
    else if (live && live.locked_for > 0) out.push(badge("warn", fill(P.locked, { s: Math.ceil(live.locked_for) })));
    const seen = (live && live.reported) || {};
    const about = [seen.hardware, seen.firmware ? "v" + seen.firmware : null].filter(Boolean).join(" · ");
    return el("span", { class: "tags" }, out, about ? el("span", { class: "sub", text: about }) : null);
  }
  _panelLimits(item) {
    const P = this.t.panel;
    const d = item.data;
    const modes = d.allowed_modes && d.allowed_modes.length ? this._optList("allowed_modes", d.allowed_modes) : P.all;
    const no = [d.can_disarm === false ? P.noDisarm : null, d.can_bypass === false ? P.noBypass : null, d.can_silence === false ? P.noSilence : null].filter(Boolean);
    return [modes, ...no].join(", ");
  }
  async _panelAction(item, type, doneText) {
    const P = this.t.panel;
    const res = await this._call({ type, subentry_id: item.id });
    if (!res || !res.ok) { this._toast(P.refused); return; }
    if (type === "vigil_alarm/panel_clear_lock" && !res.was_locked) { this._toast(P.nothingLocked); return; }
    this._toast(doneText);
  }

  _list(kind) {
    const t = this.t;
    const items = this._shown(kind);
    const cols = this._columns(kind);
    const canTest = kind === "notification" || kind === "siren";
    const table = items.length
      ? el("div", { class: "tablewrap" }, el("table", {},
          el("thead", {}, el("tr", {}, cols.map(([h]) => el("th", { text: h })), el("th", {}))),
          el("tbody", {}, items.map((item) => el("tr", { class: "row" },
            cols.map(([h, render]) => el("td", { "data-label": h }, render(item))),
            el("td", { class: "actions" },
              canTest ? iconButton("play", t.testBtn, "", () => this._test(kind, item)) : null,
              kind === "panel" ? iconButton("unlock", t.panel.unlock, "", () => this._panelAction(item, "vigil_alarm/panel_unlock", fill(t.panel.unlockedDone, { s: item.data.unlock_seconds || 60 }))) : null,
              kind === "panel" ? iconButton("reset", t.panel.clear, "", () => this._panelAction(item, "vigil_alarm/panel_clear_lock", t.panel.cleared)) : null,
              iconButton("edit", t.editBtn, "", () => this._openForm(kind, item)),
              kind === "user" ? null : iconButton("copy", t.dup, "", () => this._openForm(kind, item, true)),
              iconButton("trash", t.del, "danger", () => this._confirmDelete(item))))))))
      : el("div", { class: "empty", text: t.empty[kind] });
    return el("div", {},
      el("div", { class: "bar" }, el("p", { class: "intro", text: t.intro[kind] }),
        kind === "sensor" ? el("button", { class: "btn", text: t.practice.walkTitle, onclick: () => this._openWalkTest() }) : null,
        kind === "sensor" ? el("button", { class: "btn", text: t.find.button, onclick: () => this._openFind() }) : null,
        el("button", { class: "btn primary", text: t.add[kind], onclick: () => this._openForm(kind) })),
      kind === "panel" ? el("p", { class: "muted", text: t.panel.hint }) : null,
      el("div", { class: "card" }, table));
  }

  // ---- settings tab
  // ---- log tab: filled in after the entries arrive
  _logTab() {
    const t = this.t;
    const l = t.log;
    const host = el("div", {});
    const load = async () => {
      const res = await this._call({ type: "vigil_alarm/log", limit: 200 });
      if (!res || !res.entries) { host.replaceChildren(el("div", { class: "empty", text: t.errors.generic })); return; }
      const when = (iso) => { const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleString(); };
      // Done on a panel or device without a code: there is no name to show.
      const byPerson = ["armed", "disarmed", "sensor_bypassed", "sensor_unbypassed", "alarm_silenced", "alarm_acknowledged"];
      const installerCode = (e) => e.event === "panel_unlocked" && !e.user && e.detail && ["installer", "code"].includes(e.detail.by);
      const who = (e) => (e.user ? el("span", { text: e.user })
        : e.event === "sensor_unbypassed" && e.result === "closed" ? el("span", { class: "muted", text: l.cols.auto })
        : installerCode(e) ? el("span", { class: "muted", text: l.cols.installer })
        : e.source && byPerson.includes(e.event) ? el("span", { class: "muted", text: l.cols.noCode }) : el("span", { text: t.none }));
      const table = res.entries.length
        ? el("div", { class: "tablewrap" }, el("table", {},
            el("thead", {}, el("tr", {}, ["time", "event", "item", "who", "via", "result"].map((k) => el("th", { text: l.cols[k] })))),
            el("tbody", {}, res.entries.map((e) => el("tr", { class: "row", title: e.detail ? JSON.stringify(e.detail) : "" },
              el("td", { "data-label": l.cols.time, text: when(e.time) }),
              el("td", { "data-label": l.cols.event, text: res.labels[e.event] || e.event }),
              el("td", { "data-label": l.cols.item, text: e.item || t.none }),
              el("td", { "data-label": l.cols.who }, who(e)),
              el("td", { "data-label": l.cols.via, text: e.source || t.none }),
              el("td", { "data-label": l.cols.result, text: e.result || t.none }))))))
        : el("div", { class: "empty", text: l.empty });
      host.replaceChildren(
        el("p", { class: "intro", text: fill(l.intro, { days: res.retention_days }) }),
        res.entries.length ? el("p", { class: "muted", text: fill(l.showing, { n: res.entries.length, total: res.total }) }) : null,
        table);
    };
    const download = (format) => async () => {
      const res = await this._call({ type: "vigil_alarm/log_export", format });
      if (!res || res.text === undefined) { this._toast(t.errors.generic); return; }
      const url = URL.createObjectURL(new Blob([res.text], { type: res.media_type + ";charset=utf-8" }));
      const link = el("a", { href: url, download: res.filename });
      this._root.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    };
    load();
    return el("div", {},
      el("div", { class: "bar" }, el("span", {}),
        el("button", { class: "btn", text: l.refresh, onclick: load }),
        el("button", { class: "btn", text: l.csv, onclick: download("csv") }),
        el("button", { class: "btn primary", text: l.jsonl, onclick: download("jsonl") })),
      el("div", { class: "card" }, host));
  }

  _settings() {
    const t = this.t;
    const form = this._makeForm(this._data.settings_form, { ...this._data.entry.data }, { ctx: "s", kind: "settings", sections: true });
    const base = el("div");
    const saveBtn = el("button", { class: "btn primary", text: t.save });
    saveBtn.addEventListener("click", async () => {
      saveBtn.disabled = true;
      const res = await this._call({ type: "vigil_alarm/save_settings", data: form.values() });
      saveBtn.disabled = false;
      if (res.ok) { this._savedToast(t.saved); await this._load(); } else form.showErrors(res, base);
    });
    return el("div", {}, base, form.node,
      el("div", { class: "card" }, el("div", { class: "bar" }, saveBtn), el("p", { class: "note", text: t.reloadNote })),
      this._coverageCard());
  }

  // ---- backup tab: kept versions, export and import
  _changeNode(change) {
    const b = this.t.backup;
    const kindOf = { zone: "sensor", group: "rule", sensor_group: "sensor_group", user: "user", notification: "notification", siren: "siren", panel: "panel" };
    const lines = [];
    for (const [type, counts] of Object.entries(change.counts || {})) {
      const parts = ["added", "changed", "removed"].filter((a) => counts[a]).map((a) => `${counts[a]} ${b[a]}`);
      const names = change.items.filter((i) => i.type === type).slice(0, 12).map((i) => i.name).join(", ");
      lines.push(el("li", {}, el("strong", { text: `${this.t.tabs[kindOf[type]] || type}: ` }), parts.join(", "), names ? el("div", { class: "note", text: names }) : null));
    }
    if ((change.settings || []).length) {
      const names = change.settings.map((k) => (this.t.fields && this.t.fields[k]) || k).join(", ");
      lines.push(el("li", {}, fill(b.settings, { n: change.settings.length }), el("div", { class: "note", text: names })));
    }
    return lines.length ? el("ul", { class: "morelist" }, lines) : el("p", { text: b.nothing });
  }

  _summaryText(change) {
    const b = this.t.backup;
    const kindOf = { zone: "sensor", group: "rule", sensor_group: "sensor_group", user: "user", notification: "notification", siren: "siren", panel: "panel" };
    const parts = [];
    for (const [type, counts] of Object.entries(change.counts || {})) {
      parts.push(`${this.t.tabs[kindOf[type]] || type}: ` + ["added", "changed", "removed"].filter((a) => counts[a]).map((a) => `${counts[a]} ${b[a]}`).join(", "));
    }
    if ((change.settings || []).length) parts.push(fill(b.settings, { n: change.settings.length }));
    return parts.join(" · ") || b.nothing;
  }

  _backupTab() {
    const t = this.t, b = t.backup;
    const host = el("div", {});
    const when = (iso) => { const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleString(); };
    const confirm = (title, text, change, applyMsg, doneText) => this._dialog(title, [el("p", { text }), this._changeNode(change), el("div", {})], (close) => [
      el("button", { class: "btn", text: t.cancel, onclick: close }),
      el("button", { class: "btn primary", text: b.apply, onclick: async () => {
        const res = await this._call(applyMsg);
        if (res.ok) { close(); this._toast(doneText); await this._load(); load(); } else { close(); this._toast(this._errorText("base", res)); }
      } }),
    ]);
    const load = async () => {
      const res = await this._call({ type: "vigil_alarm/backups" });
      const versions = res.versions || [];
      host.replaceChildren(versions.length ? el("div", { class: "tablewrap" }, el("table", {},
        el("thead", {}, el("tr", {}, ["colTime", "colReason", "colVigil", "colChange"].map((k) => el("th", { text: b[k] })), el("th", {}))),
        el("tbody", {}, versions.map((v) => {
          const restoreBtn = iconButton("reset", v.restorable ? b.restore : fill(b.notRestorable, { v: v.entry_version, now: res.entry_version }), "", async () => {
            const pre = await this._call({ type: "vigil_alarm/backup_restore", version_id: v.id, preview: true });
            if (!pre.ok) { this._toast(this._errorText("base", pre)); return; }
            confirm(b.restoreTitle, b.restoreText, pre.change, { type: "vigil_alarm/backup_restore", version_id: v.id }, b.restored);
          });
          restoreBtn.disabled = !v.restorable;
          return el("tr", { class: "row" },
            el("td", { text: when(v.time) }), el("td", { text: b.reason[v.reason] || v.reason }),
            el("td", {}, v.integration_version || t.none, v.restorable ? null : el("div", { class: "note", text: fill(b.format, { v: v.entry_version }) })),
            el("td", {}, this._summaryText(v.summary), v.restorable ? null : el("div", { class: "note", text: fill(b.notRestorable, { v: v.entry_version, now: res.entry_version }) })),
            el("td", { class: "actions" },
              iconButton("eye", b.view, "", () => this._dialog(fill(b.viewTitle, { time: when(v.time) }), [el("p", { text: b.viewText }), this._changeNode(v.summary)], (close) => [el("button", { class: "btn primary", text: t.close, onclick: close })])),
              restoreBtn));
        })))) : el("div", { class: "empty", text: b.none }));
    };
    const picker = el("input", { type: "file", accept: "application/json,.json", style: "display:none" });
    picker.addEventListener("change", async () => {
      const file = picker.files && picker.files[0];
      picker.value = "";
      if (!file) return;
      let payload;
      try { payload = JSON.parse(await file.text()); } catch (err) { this._toast(b.readFailed); return; }
      if (!payload || typeof payload !== "object" || Array.isArray(payload)) { this._toast(b.readFailed); return; }
      const pre = await this._call({ type: "vigil_alarm/import", payload, preview: true });
      if (!pre.ok) { this._toast(this._errorText("base", pre)); return; }
      confirm(b.importTitle, b.importText, pre.change, { type: "vigil_alarm/import", payload }, b.imported);
    });
    const exportFile = async () => {
      const payload = await this._call({ type: "vigil_alarm/export" });
      if (!payload || payload.format === undefined) { this._toast(t.errors.generic); return; }
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = el("a", { href: url, download: `vigil-alarm-${(() => { const d = new Date(payload.changed_at || Date.now()), p = (n) => String(n).padStart(2, "0"); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}-${p(d.getHours())}-${p(d.getMinutes())}-${p(d.getSeconds())}`; })()}.json` });
      this._root.append(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
    };
    load();
    return el("div", {},
      el("p", { class: "intro", text: b.intro }),
      el("div", { class: "card" }, el("h2", { text: b.list }), host),
      el("div", { class: "card" }, el("h2", { text: b.fileTitle }),
        el("div", { class: "bar" }, el("button", { class: "btn", text: b.export, onclick: exportFile }),
          el("button", { class: "btn", text: b.import, onclick: () => picker.click() }), picker),
        el("p", { class: "note", text: b.exportNote }), el("p", { class: "note", text: b.importNote })));
  }

  // ---- about tab
  _aboutTab() {
    const t = this.t, a = t.about;
    if (!this._about) {
      if (!this._aboutLoading) {
        this._aboutLoading = true;
        this._call({ type: "vigil_alarm/about" }).then((res) => {
          this._aboutLoading = false;
          this._about = res && res.version ? res : { failed: true };
          if (this._tab === "about") this._renderBody();
        });
      }
      return el("div", { class: "empty", text: t.loading });
    }
    const info = this._about;
    if (info.failed) return el("div", { class: "card empty" }, t.loadFailed);
    const link = (href, text) => el("a", { href, target: "_blank", rel: "noopener noreferrer", text });
    const row = (label, value) => el("tr", {}, el("th", { text: label }), el("td", {}, value));
    const nl = (this._hass.language || "en").startsWith("nl");
    const L = info.links;
    const counts = Object.entries((info.system && info.system.counts) || {})
      .map(([kind, n]) => `${t.tabs[kind] || kind}: ${n}`).join(", ");
    const report = [
      `Vigil Alarm ${info.version}`,
      `Home Assistant ${info.system.home_assistant}`,
      `Python ${info.system.python}`,
      `${a.alarmState}: ${info.system.alarm_state || "-"}`,
      `${a.items}: ${counts}`,
    ].join("\n");
    const copyBtn = el("button", { class: "btn", text: a.copyInfo });
    copyBtn.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(report); this._toast(a.copied); }
      catch (err) { this._toast(a.copyFailed); }
    });
    const notes = info.notes.length
      ? info.notes.map((r) => el("div", { class: "release" },
          el("h3", {}, r.version === "Unreleased" ? a.unreleased : "v" + r.version,
            r.note ? el("span", { class: "count", text: ` (${r.note})` }) : null),
          el("ul", {}, r.items.map((item) => el("li", { text: item })))))
      : [el("p", { class: "note", text: a.noNotes })];
    const links = [
      ["book", nl ? L.manual_nl : L.manual_en, a.manual],
      ["book", nl ? L.manual_en : L.manual_nl, a.manualOther],
      ["github", L.repository, a.repository],
      ["tablet", L.panel_docs, a.panelDocs],
      ["tag", L.releases, a.releases],
      ["alert", L.new_issue, a.issues],
    ];
    return el("div", {},
      el("div", { class: "card" },
        el("div", { class: "brand" },
          el("img", { src: LOGO_URL, alt: "", width: "64", height: "64" }),
          el("div", {}, el("h2", { text: "Vigil Alarm" }), el("p", { class: "note", style: "margin:0", text: a.aboutIntro }))),
        el("div", { class: "cols" },
          el("div", {},
            el("h2", { text: a.details }),
            el("table", { class: "about" },
              row(a.version, info.version),
              row(a.author, info.author),
              row(a.license, link(L.license, info.license)))),
          el("div", {},
            el("h2", { text: a.system }),
            el("table", { class: "about" },
              row(a.haVersion, info.system.home_assistant),
              row(a.python, info.system.python)))),
        el("div", { class: "bar", style: "justify-content:flex-start;margin:12px 0 0" }, copyBtn),
        el("p", { class: "note", text: a.disclaimer })),
      el("div", { class: "card" }, el("h2", { text: a.links }),
        el("ul", { class: "links" }, links.map(([name, href, text]) =>
          el("li", {}, icon(name), link(href, text))))),
      el("div", { class: "card" }, el("h2", { text: a.notes }),
        nl && a.notesOnlyEnglish ? el("p", { class: "note", text: a.notesOnlyEnglish }) : null, ...notes));
  }

  // ---- websocket helpers
  async _call(msg) {
    try {
      return await this._hass.callWS(msg);
    } catch (err) {
      return { ok: false, errors: { base: "generic" }, placeholders: { error: (err && err.message) || "" } };
    }
  }

  _toast(text, action = null) {
    const node = el("div", { class: "toast", text });
    if (action) node.append(" ", el("button", { class: "toastbtn", text: action.label, onclick: () => { node.remove(); action.run(); } }));
    this.shadowRoot.append(node);  // not in the root: a reload of the data redraws that and would wipe it
    setTimeout(() => node.remove(), action ? 8000 : 2500);
  }

  // After a change: say so, and offer to undo it (the version before it is the newest one kept).
  _savedToast(text) {
    this._toast(text, { label: this.t.backup.undo, run: async () => {
      const list = await this._call({ type: "vigil_alarm/backups" });
      const latest = list.versions && list.versions[0];
      if (!latest) return;
      const res = await this._call({ type: "vigil_alarm/backup_restore", version_id: latest.id });
      if (res.ok) { this._toast(this.t.backup.restored); await this._load(); } else this._toast(this._errorText("base", res));
    } });
  }

  async _test(kind, item) {
    if (kind === "notification") await this._hass.callService("vigil_alarm", "test_notification", { channel: item.title });
    else await this._hass.callService("vigil_alarm", "test_siren", { siren: item.title, duration: 3 });
    this._toast(this.t.testSent);
  }

  // ---- dialogs
  _dialog(title, body, buttons, wide = false, keep = false) {
    const layer = this._q("layer");
    const close = () => {
      layer.replaceChildren();
      this._wizardShown = false;
      if (this._wizardResume && !keep) { this._wizardResume = false; this._openWizard(); }
    };
    const overlay = el("div", { class: "overlay", onmousedown: (e) => { if (e.target === overlay) close(); } },
      el("div", { class: "dialog" + (wide ? " wide" : ""), role: "dialog" }, el("h2", { text: title }), el("div", { class: "body" }, body), el("div", { class: "foot" }, buttons(close))));
    layer.replaceChildren(overlay);
    return close;
  }

  // Explanation in a small window on top of the form; closing it leaves the form as it is.
  _infoPopup(title, text) {
    const layer = this._q("layer");
    const [intro, ...rest] = text.split("\n");
    const bullets = rest.filter((l) => l.startsWith("• ")).map((l) => {
      const [head, ...tail] = l.slice(2).split(": ");
      return tail.length ? el("li", {}, el("strong", { text: head + ": " }), tail.join(": ")) : el("li", { text: head });
    });
    const close = () => { overlay.remove(); document.removeEventListener("keydown", onKey); };
    const onKey = (e) => { if (e.key === "Escape") close(); };
    const overlay = el("div", { class: "overlay top", onmousedown: (e) => { if (e.target === overlay) close(); } },
      el("div", { class: "dialog", role: "dialog" }, el("h2", { text: title }),
        el("div", { class: "body" }, el("p", { text: intro }), bullets.length ? el("ul", { class: "morelist" }, bullets) : null),
        el("div", { class: "foot" }, el("button", { class: "btn primary", text: this.t.close, onclick: close }))));
    document.addEventListener("keydown", onKey);
    layer.append(overlay);
  }

  _confirmDelete(item) {
    const t = this.t;
    const base = el("div");
    this._dialog(t.del, [el("p", { text: fill(t.confirmDelete, { name: item.title }) }), base], (close) => [
      el("button", { class: "btn", text: t.cancel, onclick: close }),
      el("button", { class: "btn danger", text: t.del, onclick: async () => {
        const res = await this._call({ type: "vigil_alarm/delete", subentry_id: item.id });
        if (res.ok) { close(); this._savedToast(t.deleted); await this._load(); }
        else base.replaceChildren(el("div", { class: "baseerror", text: this._errorText("base", res) }));
      } }),
    ]);
  }

  // ---- find sensors: a proposal from the entity registry, nothing is saved until the person confirms
  async _openFind(opts = {}) {
    const t = this.t;
    const f = t.find;
    const res = await this._call({ type: "vigil_alarm/discover" });
    if (!res || !res.candidates) { this._toast(t.errors.generic); return; }
    const groupName = (id) => this._groupName(id);
    const newIds = new Set(this._newSensors().map((e) => e.entity_id));
    const rows = [
      ...res.candidates.map((c) => ({ c, tamperOnly: false })),
      ...(res.tamper_only || []).map((c) => ({ c: { ...c, cls: "tamper", groups: [], entrance: false }, tamperOnly: true })),
    ].map((r) => {
      const intrusion = r.c.cls === "intrusion";
      r.blocked = r.c.in_use ? f.inUse : intrusion && !(r.c.groups || []).length ? f.needsGroup : "";
      r.on = !r.blocked;
      r.name = r.c.name;
      r.entrance = !!r.c.entrance && intrusion;
      r.nameInput = null;
      r.isNew = newIds.has(r.c.entity_id);
      return r;
    });
    let onlyNew = !!opts.onlyNew && newIds.size > 0;
    const shown = () => rows.filter((r) => !onlyNew || r.isNew);
    const base = el("div");
    const tableHost = el("div");
    let close = () => {};
    const addBtn = el("button", { class: "btn primary" });
    const count = () => shown().filter((r) => r.on && !r.blocked).length;
    const refresh = () => {
      const n = count();
      addBtn.textContent = fill(f.add, { n });
      addBtn.disabled = n === 0;
    };
    const build = () => {
      const missingGroup = shown().some((r) => r.blocked === f.needsGroup);
      if (!shown().length) { tableHost.replaceChildren(el("div", { class: "empty", text: f.none })); refresh(); return; }
      const table = el("div", { class: "tablewrap" }, el("table", {},
        el("thead", {}, el("tr", {}, el("th", {}), ...["name", "cls", "entrance", "groups", "extra"].map((k) => el("th", { text: f.cols[k] })))),
        el("tbody", {}, shown().map((r) => {
          const check = el("input", { type: "checkbox", checked: r.on && !r.blocked, disabled: !!r.blocked, "aria-label": r.name });
          check.addEventListener("change", () => { r.on = check.checked; refresh(); });
          const nameInput = el("input", { type: "text", value: r.name, disabled: !!r.blocked, "aria-label": f.cols.name });
          nameInput.addEventListener("input", () => { r.name = nameInput.value; });
          const entrance = r.c.entrance && r.c.cls === "intrusion"
            ? (() => { const b = el("input", { type: "checkbox", checked: r.entrance, disabled: !!r.blocked, "aria-label": f.cols.entrance, title: f.entranceHelp });
                b.addEventListener("change", () => { r.entrance = b.checked; }); return b; })()
            : t.none;
          const extras = [r.c.battery_entity ? f.battery : null, r.c.tamper_entity ? f.tamper : null].filter(Boolean).join(", ") || t.none;
          return el("tr", { class: "row" },
            el("td", { "data-label": "" }, check),
            el("td", { "data-label": f.cols.name }, nameInput, el("span", { class: "sub", text: r.c.platform ? `${r.c.entity_id} · ${r.c.platform}` : r.c.entity_id }),
              r.blocked ? el("span", { class: "badge warn", text: r.blocked }) : null),
            el("td", { "data-label": f.cols.cls }, this._opt("cls", r.c.cls)),
            el("td", { "data-label": f.cols.entrance }, entrance),
            el("td", { "data-label": f.cols.groups }, r.c.cls === "intrusion" ? (r.c.groups || []).map(groupName).join(", ") || t.none : t.alwaysOn),
            el("td", { "data-label": f.cols.extra }, extras));
        }))));
      const makeGroups = el("button", { class: "btn", text: f.createGroups, onclick: async () => {
        const made = await this._call({ type: "vigil_alarm/create_default_groups" });
        if (made.ok) { close(); await this._load(); this._openFind(); }
      } });
      tableHost.replaceChildren(missingGroup ? el("div", {}, el("p", { class: "intro", text: f.noGroups }), makeGroups) : null, table);
      refresh();
    };
    const setAll = (on) => { shown().forEach((r) => { r.on = on && !r.blocked; }); build(); };
    const copy = el("button", { class: "btn", text: f.copy, title: f.copyHelp });
    copy.addEventListener("click", async () => {
      const report = await this._call({ type: "vigil_alarm/discover_report" });
      try { await navigator.clipboard.writeText(JSON.stringify(report.entities || [], null, 1)); this._toast(t.about.copied); }
      catch (err) { this._toast(t.about.copyFailed); }
    });
    const filterNote = el("p", { class: "muted" });
    const filterBtn = el("button", { class: "btn" });
    const syncFilter = () => {
      filterNote.textContent = onlyNew ? t.newSensors.onlyNew : "";
      filterBtn.textContent = onlyNew ? t.newSensors.showAll : t.newSensors.showNew;
      filterBtn.style.display = newIds.size ? "" : "none";
    };
    filterBtn.addEventListener("click", () => { onlyNew = !onlyNew; syncFilter(); build(); });
    syncFilter();
    build();
    this._dialog(f.title, [el("p", { class: "intro", text: f.intro }), filterNote, base,
      el("div", { class: "bar" }, el("button", { class: "btn", text: f.all, onclick: () => setAll(true) }),
        el("button", { class: "btn", text: f.nothing, onclick: () => setAll(false) }), filterBtn, copy),
      tableHost], (closeDialog) => {
      close = closeDialog;
      addBtn.addEventListener("click", async () => {
        const chosen = shown().filter((r) => r.on && !r.blocked);
        const items = chosen.map((r) => {
          const c = r.c;
          const data = { name: (r.name || "").trim() || c.name, entity_id: c.entity_id, cls: c.cls };
          if (c.cls === "intrusion") Object.assign(data, { type: r.entrance ? "delayed" : "instant", sensor_groups: c.groups, at_arm_open: "bypass" });
          if (c.battery_entity) data.battery_entity = c.battery_entity;
          if (c.tamper_entity) data.tamper_entity = c.tamper_entity;
          return data;
        });
        addBtn.disabled = true;
        const result = await this._call({ type: "vigil_alarm/save_many", items });
        if (result.ok) { close(); this._savedToast(fill(f.added, { n: items.length })); await this._load(); return; }
        refresh();
        const field = Object.keys(result.errors || {})[0] || "base";
        const who = result.index !== undefined && items[result.index] ? items[result.index].name : "";
        base.replaceChildren(el("div", { class: "baseerror", text: fill(f.failed, { name: who, error: this._errorText(field, result) }) }));
      });
      refresh();
      return [el("button", { class: "btn", text: t.cancel, onclick: close }), addBtn];
    }, true);
  }

  _openForm(kind, item, copy = false, prefill = null) {
    const t = this.t;
    const schema = this._data.forms[kind];
    const initial = item ? { name: item.title, ...item.data } : {};
    if (copy) initial.name = item.title + t.copySuffix;
    if (prefill) Object.assign(initial, prefill);
    const editing = item && !copy;
    const form = this._makeForm(schema, initial, { ctx: kind, kind, editing: !!editing, hasCode: !!(item && item.has_code && editing), hasDuress: !!(item && item.has_duress && editing) });
    const base = el("div");
    this._dialog(editing ? t.edit[kind] : t.add[kind], [base, form.node], (close) => {
      const saveBtn = el("button", { class: "btn primary", text: t.save });
      saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        const msg = { type: "vigil_alarm/save", kind, data: form.values() };
        if (editing) msg.subentry_id = item.id;
        const res = await this._call(msg);
        saveBtn.disabled = false;
        if (res.ok) { close(); this._savedToast(t.saved); await this._load(); } else form.showErrors(res, base);
      });
      return [el("button", { class: "btn", text: t.cancel, onclick: close }), saveBtn];
    });
  }

  // A new intrusion sensor joins the group meant for its kind (door contact or motion), until the person chooses.
  _suggestGroups(state, opts) {
    if (opts.editing || state.__groups_touched || state.cls !== "intrusion") return false;
    const st = this._hass.states[state.entity_id];
    const deviceClass = st && st.attributes.device_class;
    const kind = CONTACT_CLASSES.includes(deviceClass) ? "contacts" : MOTION_CLASSES.includes(deviceClass) ? "motion" : null;
    if (!kind) return false;
    const ids = this._data.items.sensor_group.filter((g) => g.data.suggest_for === kind).map((g) => g.id);
    if (!ids.length || JSON.stringify(ids) === JSON.stringify(state.sensor_groups)) return false;
    state.sensor_groups = ids;
    return true;
  }

  _errorText(field, res) {
    const code = res.errors && res.errors[field];
    const t = this.t;
    const text = t.errors[code] || t.errors.generic;
    return fill(text, res.placeholders || {});
  }

  // ---- form builder: returns {node, values(), showErrors(res, baseNode)}
  _makeForm(schema, initial, opts) {
    const t = this.t;
    const state = {};
    const rows = [];
    const container = el("div");
    const listId = (key) => `vigil-dl-${opts.kind}-${key.replace(/\W/g, "_")}`;

    const get = (key) => state[key];
    const matches = (cond) => !cond || Object.entries(cond).every(([k, allowed]) => {
      const v = get(k);
      return Array.isArray(v) ? v.some((x) => allowed.includes(x)) : allowed.includes(v);
    });

    // initial values (profiles arrive nested: {intrusion: {tone, volume}})
    for (const f of schema) {
      if (f.key.includes(".")) {
        const [a, b] = f.key.split(".");
        state[f.key] = initial[a] ? initial[a][b] : undefined;
      } else if (f.type === "preset") {
        state[f.key] = "";
      } else {
        state[f.key] = initial[f.key] !== undefined ? initial[f.key] : f.default;
      }
    }
    if (opts.ctx === "panel") state.device = initial.device || (initial.ha_user ? "account" : "esphome");
    // A panel always has a language: that of the person who is logged in, English if there is no match.
    if (opts.ctx === "panel" && (!opts.editing || !Object.keys(TXT).includes(state.language))) {
      state.language = panelLanguage((this._hass.locale && this._hass.locale.language) || this._hass.language);
    }
    if (opts.kind === "settings") {
      for (const f of schema) if (state[f.key] === undefined) state[f.key] = f.type === "number" ? 0 : f.default;
    }
    const label = (f) => t.fields[`${opts.ctx}.${f.key}`] || t.fields[f.key] || f.key;
    const profileGroups = {};

    // A tablet or phone is not always there, so it is not watched unless you say so; an ESPHome panel is. The
    // choice follows the kind of device as long as you have not touched it yourself.
    let autoWatch = null;
    const renderAll = () => {
      if (opts.ctx === "panel" && !opts.editing) {
        const want = state.device !== "account";
        if (autoWatch === null) {
          if (initial.watch === undefined) state.watch = want;
        } else if (want !== autoWatch && state.watch === autoWatch) state.watch = want;
        autoWatch = want;
      }
      rows.length = 0;
      const nodes = [];
      for (const f of schema) {
        if (!matches(f.show_if)) continue;
        if (f.group) {
          (profileGroups[f.group] = profileGroups[f.group] || []).push(f);
          continue;
        }
        nodes.push(this._field(f, state, label(f), opts, listId, renderAll));
      }
      const groups = Object.keys(profileGroups);
      if (groups.length) {
        const det = el("details", { open: groups.some((g) => profileGroups[g].some((f) => state[f.key])) },
          el("summary", { text: t.help.profiles }),
          groups.map((g) => el("div", {}, el("h3", { text: this._opt("cause", g) }),
            el("div", { class: "pair" }, profileGroups[g].map((f) => this._field(f, state, t.fields[f.key.split(".")[1]], opts, listId, renderAll, true))))));
        nodes.push(det);
        for (const k of groups) profileGroups[k] = [];
      }
      if (opts.sections) {
        // Settings: one card per section, in the order the fields arrive.
        const order = [];
        const bySection = {};
        schema.forEach((f, i) => { if (!bySection[f.section]) { bySection[f.section] = []; order.push(f.section); } });
        const placed = new Map(schema.filter((f) => matches(f.show_if)).map((f, i) => [f.key, nodes[i]]));
        const cards = order.map((s) => {
          const [title, intro] = t.sections[s] || [s, ""];
          const inner = schema.filter((f) => f.section === s && placed.has(f.key)).map((f) => placed.get(f.key));
          return el("div", { class: "card" }, el("h2", { text: title }), intro ? el("p", { class: "muted", text: intro }) : null, ...inner);
        });
        container.replaceChildren(...cards);
        return;
      }
      container.replaceChildren(...nodes);
    };
    renderAll();

    return {
      node: container,
      values: () => {
        const out = {};
        for (const f of schema) {
          if (!matches(f.show_if) || f.type === "preset") continue;
          let v = state[f.key];
          if (f.type === "number") v = v === "" || v === undefined || v === null ? undefined : Number(v);
          if (f.type === "tags") v = Array.isArray(v) ? v : String(v || "").split(",").map((x) => x.trim()).filter(Boolean);
          if (f.key.includes(".")) {
            const [a, b] = f.key.split(".");
            out[a] = out[a] || {};
            if (v !== undefined && v !== "") out[a][b] = v;
          } else if (v !== undefined) out[f.key] = v;
        }
        if (state.__remove_code) out.remove_code = true;
        if (state.__remove_duress) out.remove_duress = true;
        return out;
      },
      showErrors: (res, baseNode) => {
        container.querySelectorAll(".field").forEach((n) => {
          n.classList.remove("err");
          n.querySelectorAll(".error").forEach((e) => e.remove());
        });
        const errs = res.errors || {};
        const baseText = [];
        for (const [field, code] of Object.entries(errs)) {
          const row = container.querySelector(`[data-field="${field}"]`);
          if (field !== "base" && row) {
            row.classList.add("err");
            row.append(el("div", { class: "error", text: this._errorText(field, res) }));
          } else baseText.push(this._errorText(field, res));
        }
        baseNode.replaceChildren(...baseText.map((x) => el("div", { class: "baseerror", text: x })));
      },
    };
  }

  _field(f, state, labelText, opts, listId, rerender, compact = false) {
    const t = this.t;
    const key = f.key;
    const more = t.helpMore && t.helpMore[key];
    const help = t.help[key] && !compact
      ? el("div", { class: "help" }, el("span", { text: t.help[key] }),
          more ? el("button", { type: "button", class: "info", title: t.moreInfo, "aria-label": t.moreInfo,
            onclick: () => this._infoPopup(labelText, more), text: "i" }) : null)
      : null;
    const wrap = (...inner) => el("div", { class: "field", "data-field": key },
      compact ? el("label", { class: "lbl", text: labelText }) : (f.type === "boolean" ? null : el("label", { class: "lbl", text: labelText + (f.required ? " *" : "") })),
      ...inner, help);

    switch (f.type) {
      case "text":
      case "password": {
        const input = el("input", { type: f.type === "password" ? "password" : "text", value: state[key] || "", autocomplete: "off",
          oninput: (e) => { state[key] = e.target.value; } });
        if (f.type === "password") {
          if (key === "duress_code") {
            return wrap(input, opts.hasDuress ? el("label", { class: "inline", style: "margin-top:6px" },
              el("input", { type: "checkbox", onchange: (e) => { state.__remove_duress = e.target.checked; } }), t.help.removeDuress) : null);
          }
          return wrap(input, opts.hasCode ? el("label", { class: "inline", style: "margin-top:6px" },
            el("input", { type: "checkbox", onchange: (e) => { state.__remove_code = e.target.checked; } }), t.help.removeCode) : null);
        }
        return wrap(input);
      }
      case "number": {
        const input = el("input", { type: "number", min: f.min, max: f.max, step: "any", value: state[key] === undefined || state[key] === null ? "" : state[key],
          oninput: (e) => { state[key] = e.target.value; } });
        return wrap(f.unit ? el("div", { class: "inline" }, input, f.unit) : input);
      }
      case "boolean": {
        return wrap(el("label", { class: "inline" },
          el("input", { type: "checkbox", checked: !!state[key], onchange: (e) => { state[key] = e.target.checked; rerender(); } }), labelText));
      }
      case "select": {
        const select = el("select", { onchange: (e) => { state[key] = e.target.value; rerender(); } },
          f.options.map((o) => el("option", { value: o, selected: state[key] === o, text: this._opt(key, o) })));
        return wrap(select);
      }
      case "multiselect": {
        const current = new Set(state[key] || []);
        return wrap(el("div", { class: "checks" }, f.options.map((o) => el("label", {},
          el("input", { type: "checkbox", checked: current.has(o), onchange: (e) => {
            if (e.target.checked) current.add(o); else current.delete(o);
            state[key] = f.options.filter((x) => current.has(x));
            rerender();
          } }), this._opt(key, o)))));
      }
      case "sensors": {
        const choices = this._data.items.sensor.filter((z) => z.data.cls === "intrusion" && (z.data.type || "instant") === "instant");
        const current = new Set(state[key] || []);
        return wrap(choices.length
          ? el("div", { class: "checks" }, choices.map((z) => el("label", {},
              el("input", { type: "checkbox", checked: current.has(z.id), onchange: (e) => {
                if (e.target.checked) current.add(z.id); else current.delete(z.id);
                state[key] = choices.map((c) => c.id).filter((id) => current.has(id));
              } }), z.title)))
          : el("div", { class: "muted", text: t.empty.sensor }));
      }
      case "sensor_groups": {
        const choices = this._data.items.sensor_group;
        const current = new Set(state[key] || []);
        return wrap(choices.length
          ? el("div", { class: "checks" }, choices.map((g) => el("label", {},
              el("input", { type: "checkbox", checked: current.has(g.id), onchange: (e) => {
                if (e.target.checked) current.add(g.id); else current.delete(g.id);
                state[key] = choices.map((c) => c.id).filter((id) => current.has(id));
                state.__groups_touched = true;
              } }), g.title)))
          : el("div", { class: "muted", text: t.empty.sensor_group }));
      }
      case "preset": {
        const note = el("div", { class: "help" });
        const select = el("select", { onchange: async (e) => {
          const id = e.target.value;
          state[key] = id;
          if (!id) { note.textContent = ""; return; }
          const res = await this._hass.callWS({ type: "vigil_alarm/siren_preset", preset: id, control: state.control || undefined });
          for (const [k, v] of Object.entries(res.values)) {
            if (v && typeof v === "object") for (const [k2, v2] of Object.entries(v)) state[`${k}.${k2}`] = v2;
            else state[k] = v;
          }
          const found = res.found.map((r) => t.fields[r] || r);
          state.__presetNote = !state.control ? t.help.presetNoControl
            : found.length ? `${t.help.presetFound} ${found.join(", ")}` : t.help.presetNoneFound;
          rerender();
        } }, ["", ...(this._data.siren_presets || [])].map((o) => el("option", { value: o, selected: state[key] === o, text: this._opt("preset", o) })));
        return wrap(select, state.__presetNote ? el("div", { class: "help", text: state.__presetNote }) : null);
      }
      case "tags": {
        const v = Array.isArray(state[key]) ? state[key].join(", ") : state[key] || "";
        return wrap(el("input", { type: "text", value: v, autocomplete: "off", oninput: (e) => { state[key] = e.target.value; } }));
      }
      case "ha_user": {
        const users = [...(this._data.ha_users || [])];
        const select = el("select", { onchange: (e) => { state[key] = e.target.value; } },
          el("option", { value: "", text: "—" }),
          users.map((u) => el("option", { value: u.id, selected: state[key] === u.id, text: u.name })));
        return wrap(select);
      }
      case "notify": {
        const services = [...this._data.notify_services];
        if (state[key] && !services.includes(state[key])) services.push(state[key]);
        const select = el("select", { onchange: (e) => { state[key] = e.target.value; } },
          el("option", { value: "", text: "—" }),
          services.map((s) => el("option", { value: s, selected: state[key] === s, text: s.includes(".") ? s : `notify.${s}` })));
        return wrap(select);
      }
      case "entity": {
        const id = listId(key);
        const options = Object.keys(this._hass.states).filter((e) => f.domains.includes(e.split(".")[0])).sort();
        const input = el("input", { type: "text", class: "ent", list: id, value: state[key] || "", autocomplete: "off", placeholder: f.domains.map((d) => d + ".…").join(", "),
          oninput: (e) => { state[key] = e.target.value.trim(); },
          onchange: () => { if (opts.kind === "sensor" && key === "entity_id" && this._suggestGroups(state, opts)) rerender(); } });
        const list = el("datalist", { id }, options.map((e) => el("option", { value: e, label: this._friendly(e) })));
        return wrap(input, list);
      }
    }
    return wrap();
  }
}

customElements.define("vigil-panel", VigilPanel);
