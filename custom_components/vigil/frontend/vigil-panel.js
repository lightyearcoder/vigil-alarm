/* Vigil Alarm: admin panel.
 *
 * A plain web component (no build step). It talks only to the vigil/* websocket
 * commands, which are admin-only and share their validation with the config
 * flows. All text that comes from the user is added as text nodes, never as HTML.
 */

const TXT = {
  nl: {
    title: "Vigil Alarm",
    tabs: { overview: "Overzicht", sensor: "Sensoren", sensor_group: "Sensorgroepen", rule: "Bevestigingsregels", user: "Gebruikers", notification: "Meldingen", siren: "Sirenes", settings: "Instellingen" },
    add: { sensor: "Sensor toevoegen", sensor_group: "Sensorgroep toevoegen", rule: "Bevestigingsregel toevoegen", user: "Gebruiker toevoegen", notification: "Melding toevoegen", siren: "Sirene toevoegen" },
    edit: { sensor: "Sensor bewerken", sensor_group: "Sensorgroep bewerken", rule: "Bevestigingsregel bewerken", user: "Gebruiker bewerken", notification: "Melding bewerken", siren: "Sirene bewerken" },
    intro: {
      sensor: "Eén melder, zoals een deurcontact, PIR of rookmelder. Bij een inbraaksensor kies je in welke sensorgroepen hij zit. Brand-, gas-, water- en sabotagesensoren bewaken altijd en hebben geen sensorgroep nodig.",
      sensor_group: "Een sensorgroep bepaalt in welke modi de sensoren erin bewaken. Bijvoorbeeld: Buitenschil (deuren en ramen) bij Thuis, Weg en Nacht, en Binnen (beweging) alleen bij Weg.",
      rule: "Een alarm volgt pas als het opgegeven aantal verschillende sensoren binnen het tijdvenster afgaat. Handig tegen een vals alarm door één PIR.",
      user: "Wie het alarm met een code kan bedienen.",
      notification: "Naar wie en wanneer berichten gaan. Elke melding is één notify-dienst.",
      siren: "Optioneel. Zonder sirene werkt het alarm met meldingen.",
    },
    empty: {
      sensor: "Nog geen sensoren. Voeg eerst een sensorgroep toe als er nog geen is, en daarna je sensoren.",
      sensor_group: "Nog geen sensorgroepen. Een sensorgroep bepaalt in welke modi sensoren bewaken.",
      rule: "Nog geen bevestigingsregels. Optioneel: een alarm pas na meerdere sensoren.",
      user: "Nog geen gebruikers. Zonder gebruiker is er geen code nodig om te bedienen.",
      notification: "Nog geen meldingen. Voeg een notify-dienst toe om berichten te krijgen.",
      siren: "Nog geen sirene. Dit is optioneel; zonder sirene werkt het alarm met meldingen.",
    },
    save: "Opslaan", cancel: "Annuleren", del: "Verwijderen", dup: "Kopiëren", editBtn: "Bewerken", testBtn: "Test", close: "Sluiten",
    copySuffix: " (kopie)",
    confirmDelete: "Weet je zeker dat je '{name}' wilt verwijderen?",
    saved: "Opgeslagen", deleted: "Verwijderd", testSent: "Test verstuurd", loading: "Laden…", loadFailed: "Vigil Alarm kon niet geladen worden. Is de integratie actief?",
    retry: "Opnieuw proberen",
    reloadNote: "Opslaan laadt Vigil Alarm opnieuw (de alarmstatus blijft behouden).",
    alarm: "Alarm", problems: "Aandachtspunten", noProblems: "Geen problemen", sensorsNow: "Sensoren nu",
    coverage: "Wat bewaakt elke modus", coverageNothing: "geen sensorgroep: er wordt niets bewaakt", alwaysOn: "Altijd actief", sensorsCount: "{n} sensoren",
    state: { disarmed: "Uit", arming: "Wordt ingeschakeld", armed: "Ingeschakeld", pending: "Inlooptijd", triggered: "ALARM" },
    mode: { home: "Thuis", away: "Weg", night: "Nacht" },
    zstatus: { closed: "Dicht", open: "Open", unavailable: "Onbereikbaar", bypassed: "Omzeild", bypassed_at_arm: "Omzeild bij inschakelen", waiting: "Wacht tot dicht" },
    problem: { battery_low: "batterij bijna leeg", unavailable: "niet bereikbaar", on_battery: "geen netstroom" },
    cols: {
      name: "Naam", entity: "Entiteit", cls: "Klasse", type: "Type", groups: "Sensorgroepen", rule: "Bevestigingsregel", status: "Status",
      modes: "Actief in modi", sensors: "Sensoren", suggest: "Voorstel voor", condition: "Voorwaarde", escalate: "Onbevestigd melden",
      code: "Code", tags: "Tags", tamper: "Sabotage omzeilen",
      service: "Dienst", categories: "Categorieën", delay: "Vertraging",
      device: "Apparaat", causes: "Bij", maxdur: "Max. duur",
    },
    yes: "ja", no: "nee", none: "—", immediately: "direct",
    condition: "{n} binnen {s} s",
    fields: {
      name: "Naam", entity_id: "Entiteit (binary sensor)", cls: "Klasse", type: "Type", sensor_groups: "Sensorgroepen", at_arm_open: "Als open bij einde uitlooptijd",
      entry_delay: "Inlooptijd (leeg = standaard)", gas_type: "Soort gas", on_unavailable: "Als de sensor onbereikbaar wordt", battery_entity: "Batterijsensor",
      "sensor_group.modes": "Actief in modi", suggest_for: "Voorstellen voor nieuwe sensoren",
      sensors: "Sensoren", required: "Benodigde sensoren", window: "Tijdvenster", escalate: "Melden als onbevestigd",
      code: "Code", tags: "Tags (komma-gescheiden)", allowed_modes: "Mag bedienen in modi (leeg = alle)", may_bypass_tamper: "Mag sabotage omzeilen",
      service: "Notify-dienst", categories: "Soorten meldingen", delay: "Vertraging", priority: "Hoge prioriteit",
      control: "Sirene (siren, schakelaar of lamp)", causes: "Laat klinken bij", max_duration: "Maximale duur (0 = tot uitschakelen)", repeat_every: "Herhaal elke (0 = niet)",
      light: "Flitslicht", tone_entity: "Toonkeuze-entiteit", volume_entity: "Volume-entiteit", power_entity: "Voedingsmodus-entiteit", power_battery_value: "Waarde bij batterijvoeding",
      tone: "Toon", volume: "Volume", preset: "Voorinstelling",
      "s.modes": "Beschikbare modi", exit_delay_home: "Uitlooptijd thuis", exit_delay_away: "Uitlooptijd weg", exit_delay_night: "Uitlooptijd nacht",
      default_entry_delay: "Standaard inlooptijd", trigger_time: "Alarmduur (0 = tot uitschakelen)", battery_threshold: "Batterijgrens", code_arm_required: "Code nodig om in te schakelen",
    },
    help: {
      entity_id: "Een binary sensor: aan betekent open of alarm.",
      type: "Direct: meteen alarm. Vertraagd: eerst inlooptijd. Volger: alleen alarm als er eerst een vertraagde sensor open was.",
      sensor_groups: "Een sensor kan in meerdere groepen zitten. Hij bewaakt in elke modus waarin één van zijn groepen actief is.",
      suggest_for: "Optioneel. Een nieuwe sensor van dit soort (deurcontact of beweging) wordt automatisch in deze groep gezet.",
      sensors: "Alleen directe inbraaksensoren.",
      code: "Leeg laten = ongewijzigd.",
      removeCode: "Code verwijderen",
      tags: "Voor een tag-lezer, die komt met het touchpaneel (release 2). Nu nog zonder functie: bedien het alarm met een code.",
      categories: "Kies welke berichten dit kanaal krijgt.",
      delay: "Alleen voor alarmen: eerst wachten, bijvoorbeeld om alleen na een tijd een tweede apparaat te melden.",
      profiles: "Toon en volume per oorzaak (optioneel)",
      preset: "Vult toon, volume en duur in voor een bekende sirene. Kies eerst bij \"Sirene\" de aan/uit-entiteit, dan zoekt Vigil de andere entiteiten van hetzelfde apparaat erbij. Alles blijft aanpasbaar.",
      presetFound: "Gevonden bij dit apparaat:", presetNoneFound: "Geen andere entiteiten gevonden bij dit apparaat; kies ze zelf.", presetNoControl: "Waarden ingevuld. Kies de sirene-entiteit en kies de voorinstelling opnieuw om de andere entiteiten te laten zoeken.",
      power_battery_value: "De waarde van de voedingsmodus als de sirene op batterij draait.",
    },
    opt: {
      preset: { "": "—", sonoff_snzb_09p_z2m: "Sonoff SNZB-09P (Zigbee2MQTT)" },
      cls: { intrusion: "Inbraak", fire: "Brand", gas: "Gas", tamper: "Sabotage", water: "Water" },
      type: { instant: "Direct", delayed: "Vertraagd (inlooptijd)", follower: "Volger" },
      at_arm_open: { bypass: "Omzeilen met melding", wait_clear: "Wachten tot dicht", refuse: "Inschakelen weigeren", pending: "Inlooptijd starten" },
      gas_type: { co: "Koolmonoxide", natural_gas: "Aardgas", lpg: "LPG", other: "Anders" },
      on_unavailable: { default: "Standaard van de klasse", block: "Inschakelen blokkeren", notify: "Alleen melden", trigger: "Alarm geven", bypass: "Toch inschakelen (omzeilen)" },
      categories: { alarm: "Alarm", pending: "Inlooptijd", arming: "In- en uitschakelen", fault: "Storingen en meldingen", technical: "Technische alarmen (water)" },
      causes: { intrusion: "Inbraak", fire: "Brand", gas: "Gas", tamper: "Sabotage", fault: "Sensorstoring" },
      cause: { intrusion: "Inbraak", fire: "Brand", gas: "Gas", tamper: "Sabotage" },
      mode: { home: "Thuis", away: "Weg", night: "Nacht" },
      suggest_for: { "": "Geen", contacts: "Deuren en ramen (contacten)", motion: "Beweging" },
    },
    errors: {
      name_required: "Geef een naam op.", name_in_use: "Deze naam bestaat al.", required: "Verplicht.",
      invalid_config: "Ongeldig: {error}", sensor_not_instant: "Alleen directe sensoren kunnen in een bevestigingsregel. Aanpassen: {sensors}",
      no_sensor_group: "Kies minstens één sensorgroep.", unknown_sensor_group: "Onbekende sensorgroep.",
      unknown_mode: "Onbekende modus.", unknown_suggestion: "Onbekende keuze.",
      code_in_use: "Deze code is al in gebruik.", tag_in_use: "Deze tag is al in gebruik.", no_credential: "Geef een code of minstens één tag op.",
      service_not_found: "Deze notify-dienst bestaat niet (meer).", no_categories: "Kies minstens één soort melding.",
      no_causes: "Kies minstens één oorzaak.", tone_without_entity: "Een toon kan alleen met een toonkeuze-entiteit.", volume_without_entity: "Een volume kan alleen met een volume-entiteit.",
      sensor_in_rule: "Deze sensor zit nog in bevestigingsregel: {rules}. Haal hem daar eerst uit.",
      sensor_group_in_use: "Deze sensorgroep wordt nog gebruikt door: {sensors}. Haal de groep eerst bij die sensoren weg.",
      no_modes: "Kies minstens één modus.", unknown_kind: "Onbekend onderdeel.",
      generic: "Er ging iets mis.",
    },
  },
  en: {
    title: "Vigil Alarm",
    tabs: { overview: "Overview", sensor: "Sensors", sensor_group: "Sensor groups", rule: "Confirmation rules", user: "Users", notification: "Notifications", siren: "Sirens", settings: "Settings" },
    add: { sensor: "Add sensor", sensor_group: "Add sensor group", rule: "Add confirmation rule", user: "Add user", notification: "Add notification", siren: "Add siren" },
    edit: { sensor: "Edit sensor", sensor_group: "Edit sensor group", rule: "Edit confirmation rule", user: "Edit user", notification: "Edit notification", siren: "Edit siren" },
    intro: {
      sensor: "One detector, such as a door contact, PIR or smoke detector. For an intrusion sensor you choose which sensor groups it is in. Fire, gas, water and tamper sensors always watch and need no sensor group.",
      sensor_group: "A sensor group decides in which modes the sensors in it are watching. For example: Perimeter (doors and windows) for Home, Away and Night, and Interior (motion) for Away only.",
      rule: "An alarm follows only when the given number of different sensors trigger within the time window. Handy against a false alarm from a single PIR.",
      user: "Who can operate the alarm with a code.",
      notification: "Who gets messages and when. Each notification is one notify service.",
      siren: "Optional. Without a siren the alarm works with notifications.",
    },
    empty: {
      sensor: "No sensors yet. Add a sensor group first if there is none, then your sensors.",
      sensor_group: "No sensor groups yet. A sensor group decides in which modes sensors are watching.",
      rule: "No confirmation rules yet. Optional: an alarm only after several sensors.",
      user: "No users yet. Without a user no code is needed to operate the alarm.",
      notification: "No notifications yet. Add a notify service to receive messages.",
      siren: "No siren yet. This is optional; without a siren the alarm works with notifications.",
    },
    save: "Save", cancel: "Cancel", del: "Delete", dup: "Copy", editBtn: "Edit", testBtn: "Test", close: "Close",
    copySuffix: " (copy)",
    confirmDelete: "Are you sure you want to delete '{name}'?",
    saved: "Saved", deleted: "Deleted", testSent: "Test sent", loading: "Loading…", loadFailed: "Vigil Alarm could not be loaded. Is the integration running?",
    retry: "Try again",
    reloadNote: "Saving reloads Vigil Alarm (the alarm state is kept).",
    alarm: "Alarm", problems: "Attention", noProblems: "No problems", sensorsNow: "Sensors now",
    coverage: "What each mode watches", coverageNothing: "no sensor group: nothing is watched", alwaysOn: "Always on", sensorsCount: "{n} sensors",
    state: { disarmed: "Off", arming: "Arming", armed: "Armed", pending: "Entry delay", triggered: "ALARM" },
    mode: { home: "Home", away: "Away", night: "Night" },
    zstatus: { closed: "Closed", open: "Open", unavailable: "Unreachable", bypassed: "Bypassed", bypassed_at_arm: "Bypassed at arming", waiting: "Waiting to close" },
    problem: { battery_low: "battery low", unavailable: "unreachable", on_battery: "no mains power" },
    cols: {
      name: "Name", entity: "Entity", cls: "Class", type: "Type", groups: "Sensor groups", rule: "Confirmation rule", status: "Status",
      modes: "Active in modes", sensors: "Sensors", suggest: "Suggested for", condition: "Condition", escalate: "Report unconfirmed",
      code: "Code", tags: "Tags", tamper: "May bypass tamper",
      service: "Service", categories: "Categories", delay: "Delay",
      device: "Device", causes: "For", maxdur: "Max. duration",
    },
    yes: "yes", no: "no", none: "—", immediately: "immediately",
    condition: "{n} within {s} s",
    fields: {
      name: "Name", entity_id: "Entity (binary sensor)", cls: "Class", type: "Type", sensor_groups: "Sensor groups", at_arm_open: "If open when exit delay ends",
      entry_delay: "Entry delay (empty = default)", gas_type: "Type of gas", on_unavailable: "When the sensor becomes unreachable", battery_entity: "Battery sensor",
      "sensor_group.modes": "Active in modes", suggest_for: "Suggest for new sensors",
      sensors: "Sensors", required: "Sensors needed", window: "Time window", escalate: "Report when unconfirmed",
      code: "Code", tags: "Tags (comma separated)", allowed_modes: "May operate in modes (empty = all)", may_bypass_tamper: "May bypass tamper",
      service: "Notify service", categories: "Kinds of messages", delay: "Delay", priority: "High priority",
      control: "Siren (siren, switch or light)", causes: "Sound for", max_duration: "Maximum duration (0 = until disarmed)", repeat_every: "Repeat every (0 = no)",
      light: "Flash light", tone_entity: "Tone selection entity", volume_entity: "Volume entity", power_entity: "Power mode entity", power_battery_value: "Value when on battery",
      tone: "Tone", volume: "Volume", preset: "Preset",
      "s.modes": "Available modes", exit_delay_home: "Exit delay home", exit_delay_away: "Exit delay away", exit_delay_night: "Exit delay night",
      default_entry_delay: "Default entry delay", trigger_time: "Alarm duration (0 = until disarmed)", battery_threshold: "Battery threshold", code_arm_required: "Code required to arm",
    },
    help: {
      entity_id: "A binary sensor: on means open or alarm.",
      type: "Instant: alarm at once. Delayed: entry delay first. Follower: only alarms if a delayed sensor was opened first.",
      sensor_groups: "A sensor can be in several groups. It is watching in every mode in which one of its groups is active.",
      suggest_for: "Optional. A new sensor of this kind (door contact or motion) is put in this group automatically.",
      sensors: "Instant intrusion sensors only.",
      code: "Leave empty to keep it unchanged.",
      removeCode: "Remove code",
      tags: "For a tag reader, which comes with the touch panel (release 2). Has no function yet: operate the alarm with a code.",
      categories: "Choose which messages this channel receives.",
      delay: "Alarms only: wait first, for example to notify a second device only after a while.",
      profiles: "Tone and volume per cause (optional)",
      preset: "Fills in tone, volume and duration for a known siren. Pick the on/off entity under \"Siren\" first and Vigil looks for the other entities of the same device. Everything stays editable.",
      presetFound: "Found on this device:", presetNoneFound: "No other entities found on this device; pick them yourself.", presetNoControl: "Values filled in. Pick the siren entity and choose the preset again to look up the other entities.",
      power_battery_value: "The value of the power mode entity when the siren runs on battery.",
    },
    opt: {
      preset: { "": "—", sonoff_snzb_09p_z2m: "Sonoff SNZB-09P (Zigbee2MQTT)" },
      cls: { intrusion: "Intrusion", fire: "Fire", gas: "Gas", tamper: "Tamper", water: "Water" },
      type: { instant: "Instant", delayed: "Delayed (entry delay)", follower: "Follower" },
      at_arm_open: { bypass: "Bypass with a notice", wait_clear: "Wait until closed", refuse: "Refuse to arm", pending: "Start entry delay" },
      gas_type: { co: "Carbon monoxide", natural_gas: "Natural gas", lpg: "LPG", other: "Other" },
      on_unavailable: { default: "Class default", block: "Block arming", notify: "Notify only", trigger: "Raise alarm", bypass: "Arm anyway (bypass)" },
      categories: { alarm: "Alarm", pending: "Entry delay", arming: "Arming and disarming", fault: "Faults and notices", technical: "Technical alarms (water)" },
      causes: { intrusion: "Intrusion", fire: "Fire", gas: "Gas", tamper: "Tamper", fault: "Sensor fault" },
      cause: { intrusion: "Intrusion", fire: "Fire", gas: "Gas", tamper: "Tamper" },
      mode: { home: "Home", away: "Away", night: "Night" },
      suggest_for: { "": "None", contacts: "Doors and windows (contacts)", motion: "Motion" },
    },
    errors: {
      name_required: "Enter a name.", name_in_use: "This name already exists.", required: "Required.",
      invalid_config: "Invalid: {error}", sensor_not_instant: "Only instant sensors can be in a confirmation rule. Change: {sensors}",
      no_sensor_group: "Choose at least one sensor group.", unknown_sensor_group: "Unknown sensor group.",
      unknown_mode: "Unknown mode.", unknown_suggestion: "Unknown choice.",
      code_in_use: "This code is already in use.", tag_in_use: "This tag is already in use.", no_credential: "Enter a code or at least one tag.",
      service_not_found: "This notify service does not exist (any more).", no_categories: "Choose at least one kind of message.",
      no_causes: "Choose at least one cause.", tone_without_entity: "A tone needs a tone selection entity.", volume_without_entity: "A volume needs a volume entity.",
      sensor_in_rule: "This sensor is still in confirmation rule: {rules}. Remove it there first.",
      sensor_group_in_use: "This sensor group is still used by: {sensors}. Remove the group from those sensors first.",
      no_modes: "Choose at least one mode.", unknown_kind: "Unknown item.",
      generic: "Something went wrong.",
    },
  },
};

// Which option list belongs to which field.
const OPTION_GROUP = { modes: "mode", allowed_modes: "mode" };
const CONTACT_CLASSES = ["door", "window", "opening", "garage_door"];
const MOTION_CLASSES = ["motion", "occupancy", "presence", "moving"];
const KINDS = ["sensor", "sensor_group", "rule", "user", "notification", "siren"];
const TABS = ["overview", ...KINDS, "settings"];

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
.badge.ok { background: color-mix(in srgb, var(--success-color, #43a047) 18%, transparent); color: var(--success-color, #2e7d32); }
.badge.warn { background: color-mix(in srgb, var(--warning-color, #ffa600) 22%, transparent); color: var(--warning-color, #b26a00); }
.badge.bad { background: color-mix(in srgb, var(--error-color, #db4437) 18%, transparent); color: var(--error-color, #db4437); }
.tags span { margin-right: 4px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.stat { font-size: 26px; font-weight: 500; overflow-wrap: anywhere; }
.muted { color: var(--secondary-text-color, #727272); font-size: 13px; }
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
  width: 100%; padding: 10px 12px; font-size: 15px; border-radius: 8px; border: 1px solid var(--divider-color, #bbb);
  background: var(--secondary-background-color, #fff); color: var(--primary-text-color, #212121); font-family: inherit; }
.field.err input, .field.err select { border-color: var(--error-color, #db4437); }
.field .help { font-size: 12px; color: var(--secondary-text-color, #727272); margin-top: 4px; }
.field .error, .baseerror { font-size: 13px; color: var(--error-color, #db4437); margin-top: 4px; }
.baseerror { padding: 10px 12px; border-radius: 8px; background: color-mix(in srgb, var(--error-color, #db4437) 12%, transparent); margin-bottom: 14px; }
.checks { display: flex; flex-wrap: wrap; gap: 6px 16px; }
.checks label { display: flex; align-items: center; gap: 6px; font-size: 14px; cursor: pointer; }
.inline { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; }
details { margin: 8px 0 14px; border: 1px solid var(--divider-color, #ddd); border-radius: 8px; padding: 8px 12px; }
details summary { cursor: pointer; font-size: 14px; }
details h3 { font-size: 13px; margin: 12px 0 6px; font-weight: 500; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
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

  get t() { return TXT[(this._hass && this._hass.language || "en").startsWith("nl") ? "nl" : "en"]; }

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
      this._data = await this._hass.callWS({ type: "vigil/get" });
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
    }, { type: "vigil/subscribe" }).catch(() => null);
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
    this._root.replaceChildren(el("div", { id: "header" }), el("div", { id: "nav" }), el("div", { id: "body" }), el("div", { id: "layer" }));
    this._renderHeader();
    this._renderBody();
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
        text: this._stateText(live) + (live.mode && live.state !== "disarmed" ? " · " + (t.mode[live.mode] || live.mode) : "") }) : null);
    this._q("header").replaceChildren(header);
    this._renderNav();
  }

  _renderNav() {
    const t = this.t;
    const nav = el("nav", {}, TABS.map((tab) => {
      const count = KINDS.includes(tab) && this._data ? this._data.items[tab].length : null;
      return el("button", { class: tab === this._tab ? "active" : "", onclick: () => { this._tab = tab; this._renderNav(); this._renderBody(); } },
        t.tabs[tab], count !== null ? el("span", { class: "count", text: `(${count})` }) : null);
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
    else if (this._tab === "settings") content = this._settings();
    else content = this._list(this._tab);
    body.replaceChildren(el("main", {}, content));
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
  _sensorBadge(sensor) {
    const t = this.t;
    const status = this._live && this._live.sensors[sensor.id];
    if (!status) return el("span", { class: "badge", text: t.none });
    const cls = status === "closed" ? "ok" : status === "open" ? "bad" : "warn";
    const badge = el("span", { class: `badge ${cls}`, text: t.zstatus[status] || status });
    const battery = sensor.data.battery_entity && this._hass.states[sensor.data.battery_entity];
    const level = battery && !isNaN(parseFloat(battery.state)) ? ` ${parseFloat(battery.state)}%` : "";
    return level ? el("span", {}, badge, el("span", { class: "muted", text: " 🔋" + level })) : badge;
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
          el("h2", { text: t.tabs[k] }), el("div", { class: "stat", text: String(this._data.items[k].length) })))),
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
        [C.name, (i) => i.title],
        [C.entity, (i) => named(i.data.entity_id)],
        [C.cls, (i) => this._opt("cls", i.data.cls)],
        [C.type, (i) => (i.data.cls === "intrusion" ? this._opt("type", i.data.type || "instant") : t.none)],
        [C.groups, (i) => (i.data.cls === "intrusion" ? (i.data.sensor_groups || []).map((g) => this._groupName(g)).join(", ") || t.none : t.alwaysOn)],
        [C.rule, (i) => this._rulesOfSensor(i.id).join(", ") || t.none],
        [C.status, (i) => this._sensorBadge(i)],
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
        [C.tags, (i) => (i.data.tags && i.data.tags.length ? i.data.tags.length : t.none)],
        [C.modes, (i) => (i.data.allowed_modes && i.data.allowed_modes.length ? this._optList("allowed_modes", i.data.allowed_modes) : "*")],
        [C.tamper, (i) => (i.data.may_bypass_tamper ? t.yes : t.no)],
      ];
      case "notification": return [
        [C.name, (i) => i.title],
        [C.service, (i) => `notify.${i.data.service}`],
        [C.categories, (i) => this._optList("categories", i.data.categories)],
        [C.delay, (i) => (i.data.delay ? `${i.data.delay} s` : t.immediately)],
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

  _list(kind) {
    const t = this.t;
    const items = this._data.items[kind];
    const cols = this._columns(kind);
    const canTest = kind === "notification" || kind === "siren";
    const table = items.length
      ? el("div", { class: "tablewrap" }, el("table", {},
          el("thead", {}, el("tr", {}, cols.map(([h]) => el("th", { text: h })), el("th", {}))),
          el("tbody", {}, items.map((item) => el("tr", { class: "row" },
            cols.map(([h, render]) => el("td", { "data-label": h }, render(item))),
            el("td", { class: "actions" },
              canTest ? el("button", { class: "btn small", text: t.testBtn, onclick: () => this._test(kind, item) }) : null,
              " ",
              el("button", { class: "btn small", text: t.editBtn, onclick: () => this._openForm(kind, item) }),
              " ",
              el("button", { class: "btn small", text: t.dup, onclick: () => this._openForm(kind, item, true) }),
              " ",
              el("button", { class: "btn small danger", text: t.del, onclick: () => this._confirmDelete(item) })))))))
      : el("div", { class: "empty", text: t.empty[kind] });
    return el("div", {},
      el("div", { class: "bar" }, el("p", { class: "intro", text: t.intro[kind] }),
        el("button", { class: "btn primary", text: t.add[kind], onclick: () => this._openForm(kind) })),
      el("div", { class: "card" }, table));
  }

  // ---- settings tab
  _settings() {
    const t = this.t;
    const form = this._makeForm(this._data.settings_form, { ...this._data.entry.data }, { ctx: "s", kind: "settings" });
    const base = el("div");
    const saveBtn = el("button", { class: "btn primary", text: t.save });
    saveBtn.addEventListener("click", async () => {
      saveBtn.disabled = true;
      const res = await this._call({ type: "vigil/save_settings", data: form.values() });
      saveBtn.disabled = false;
      if (res.ok) { this._toast(t.saved); await this._load(); } else form.showErrors(res, base);
    });
    return el("div", {},
      el("div", { class: "card" }, el("h2", { text: t.tabs.settings }), base, form.node,
        el("div", { class: "bar" }, saveBtn), el("p", { class: "note", text: t.reloadNote })),
      this._coverageCard());
  }

  // ---- websocket helpers
  async _call(msg) {
    try {
      return await this._hass.callWS(msg);
    } catch (err) {
      return { ok: false, errors: { base: "generic" }, placeholders: { error: (err && err.message) || "" } };
    }
  }

  _toast(text) {
    const node = el("div", { class: "toast", text });
    this._root.append(node);
    setTimeout(() => node.remove(), 2500);
  }

  async _test(kind, item) {
    if (kind === "notification") await this._hass.callService("vigil", "test_notification", { channel: item.title });
    else await this._hass.callService("vigil", "test_siren", { siren: item.title, duration: 3 });
    this._toast(this.t.testSent);
  }

  // ---- dialogs
  _dialog(title, body, buttons) {
    const layer = this._q("layer");
    const close = () => layer.replaceChildren();
    const overlay = el("div", { class: "overlay", onmousedown: (e) => { if (e.target === overlay) close(); } },
      el("div", { class: "dialog", role: "dialog" }, el("h2", { text: title }), el("div", { class: "body" }, body), el("div", { class: "foot" }, buttons(close))));
    layer.replaceChildren(overlay);
    return close;
  }

  _confirmDelete(item) {
    const t = this.t;
    const base = el("div");
    this._dialog(t.del, [el("p", { text: fill(t.confirmDelete, { name: item.title }) }), base], (close) => [
      el("button", { class: "btn", text: t.cancel, onclick: close }),
      el("button", { class: "btn danger", text: t.del, onclick: async () => {
        const res = await this._call({ type: "vigil/delete", subentry_id: item.id });
        if (res.ok) { close(); this._toast(t.deleted); await this._load(); }
        else base.replaceChildren(el("div", { class: "baseerror", text: this._errorText("base", res) }));
      } }),
    ]);
  }

  _openForm(kind, item, copy = false) {
    const t = this.t;
    const schema = this._data.forms[kind];
    const initial = item ? { name: item.title, ...item.data } : {};
    if (copy) initial.name = item.title + t.copySuffix;
    const editing = item && !copy;
    const form = this._makeForm(schema, initial, { ctx: kind, kind, editing: !!editing, hasCode: !!(item && item.has_code && editing) });
    const base = el("div");
    this._dialog(editing ? t.edit[kind] : t.add[kind], [base, form.node], (close) => {
      const saveBtn = el("button", { class: "btn primary", text: t.save });
      saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        const msg = { type: "vigil/save", kind, data: form.values() };
        if (editing) msg.subentry_id = item.id;
        const res = await this._call(msg);
        saveBtn.disabled = false;
        if (res.ok) { close(); this._toast(t.saved); await this._load(); } else form.showErrors(res, base);
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
    if (opts.kind === "settings") {
      for (const f of schema) if (state[f.key] === undefined) state[f.key] = f.type === "number" ? 0 : f.default;
    }
    const label = (f) => t.fields[`${opts.ctx}.${f.key}`] || t.fields[f.key] || f.key;
    const profileGroups = {};

    const renderAll = () => {
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
    const help = t.help[key] && !compact ? el("div", { class: "help", text: t.help[key] }) : null;
    const wrap = (...inner) => el("div", { class: "field", "data-field": key },
      compact ? el("label", { class: "lbl", text: labelText }) : (f.type === "boolean" ? null : el("label", { class: "lbl", text: labelText + (f.required ? " *" : "") })),
      ...inner, help);

    switch (f.type) {
      case "text":
      case "password": {
        const input = el("input", { type: f.type === "password" ? "password" : "text", value: state[key] || "", autocomplete: "off",
          oninput: (e) => { state[key] = e.target.value; } });
        if (f.type === "password") {
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
          el("input", { type: "checkbox", checked: !!state[key], onchange: (e) => { state[key] = e.target.checked; } }), labelText));
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
          const res = await this._hass.callWS({ type: "vigil/siren_preset", preset: id, control: state.control || undefined });
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
      case "notify": {
        const services = [...this._data.notify_services];
        if (state[key] && !services.includes(state[key])) services.push(state[key]);
        const select = el("select", { onchange: (e) => { state[key] = e.target.value; } },
          el("option", { value: "", text: "—" }),
          services.map((s) => el("option", { value: s, selected: state[key] === s, text: `notify.${s}` })));
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
