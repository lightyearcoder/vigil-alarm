// Vigil Alarm touch panel: the texts and the display logic.
//
// This file is plain C++ without any ESPHome or LVGL calls, so it can be tested on a computer.
// The YAML (vigil-panel.yaml) only holds the layout and the wiring; everything that decides
// what the panel shows is here.
//
// Adding a language: add a column to TEXTS and an entry to LANGUAGES. Keep the texts to plain
// ASCII, the built-in LVGL fonts do not contain accented letters.
#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace vigil {

// ----------------------------------------------------------------------------------- texts

enum Language { NL = 0, EN = 1, LANGUAGE_COUNT = 2 };

struct Text {
  const char *key;
  const char *text[LANGUAGE_COUNT];  // in the order of enum Language
};

static const Text TEXTS[] = {
    {"disarmed", {"Uitgeschakeld", "Disarmed"}},
    {"armed_home", {"Thuis", "Home"}},
    {"armed_away", {"Weg", "Away"}},
    {"armed_night", {"Nacht", "Night"}},
    {"armed_vacation", {"Vakantie", "Vacation"}},
    {"armed_custom_bypass", {"Aangepast", "Custom"}},
    {"arming", {"Inschakelen", "Arming"}},
    {"pending", {"Binnenkomst", "Entry"}},
    {"triggered", {"ALARM", "ALARM"}},
    {"offline", {"Geen verbinding", "No connection"}},
    {"home", {"Thuis", "Home"}},
    {"away", {"Weg", "Away"}},
    {"night", {"Nacht", "Night"}},
    {"vacation", {"Vakantie", "Vacation"}},
    {"custom", {"Aangepast", "Custom"}},
    {"disarm", {"Uitschakelen", "Disarm"}},
    {"arm_home", {"Thuis inschakelen", "Arm home"}},
    {"arm_away", {"Weg inschakelen", "Arm away"}},
    {"arm_night", {"Nacht inschakelen", "Arm night"}},
    {"arm_vacation", {"Vakantie inschakelen", "Arm vacation"}},
    {"arm_custom", {"Aangepast inschakelen", "Arm custom"}},
    {"last_alarm", {"Laatste alarm: ", "Last alarm: "}},
    {"bypass", {"Omzeilen", "Bypass"}},
    {"force", {"Omzeilen en inschakelen", "Bypass and arm"}},
    {"force_title", {"Omzeilen en inschakelen: ", "Bypass and arm: "}},
    {"refuse_alarm_condition", {"Inschakelen kan niet: %s staat open", "Cannot arm: %s is open"}},
    {"refuse_sensor_unavailable", {"Inschakelen kan niet: %s reageert niet", "Cannot arm: %s does not respond"}},
    {"refuse_sensor_open", {"Inschakelen kan niet: %s staat open", "Cannot arm: %s is open"}},
    {"refuse_not_disarmed", {"Het alarm staat al aan", "The alarm is already on"}},
    {"unbypass", {"Herstellen", "Restore"}},
    {"bypass_title", {"Omzeilen: ", "Bypass: "}},
    {"unbypass_title", {"Herstellen: ", "Restore: "}},
    {"unlock_title", {"Sensoren bekijken", "View sensors"}},
    {"admin_code", {"Installateurscode", "Installer code"}},
    {"hint_user", {"Voer uw gebruikerscode in", "Enter your user code"}},
    {"hint_admin", {"Voer de installateurscode in", "Enter the installer code"}},
    {"sensors", {"Sensoren", "Sensors"}},
    {"sensors_open", {"open", "open"}},
    {"all_closed", {"Alles dicht", "All closed"}},
    {"open", {"Open: ", "Open: "}},
    {"problems", {"Storingen: ", "Problems: "}},
    {"leave_now", {"Verlaat nu het huis", "Leave the house now"}},
    {"enter_now", {"Schakel uit met uw code", "Disarm with your code"}},
    {"seconds_short", {" s", " s"}},
    {"by", {"Door ", "By "}},
    {"by_unknown", {"Door: onbekend", "By: unknown"}},
    {"via", {"Via ", "Via "}},
    {"no_sensors", {"Geen sensoren", "No sensors"}},
    {"info", {"Paneelinfo", "Panel info"}},
    {"info_title", {"Paneelinfo bekijken", "View panel info"}},
    {"connected", {"Verbonden met Home Assistant", "Connected to Home Assistant"}},
    {"not_connected", {"Niet verbonden", "Not connected"}},
    {"signal", {"Wifi-signaal: ", "Wi-Fi signal: "}},
    {"uptime", {"Aan sinds: ", "Uptime: "}},
    {"minutes", {" min", " min"}},
    {"firmware", {"Firmware: ", "Firmware: "}},
    {"panel_id", {"Paneel: ", "Panel: "}},
    {"profile", {"Profiel: ", "Profile: "}},
    {"n_open", {" open", " open"}},
    {"blocked", {"Geblokkeerd", "Blocked"}},
    {"blocked_sub", {"Dit paneel is geblokkeerd in Vigil", "This panel is blocked in Vigil"}},
    {"not_linked", {"Niet gekoppeld", "Not linked"}},
    {"not_linked_sub", {"Voeg dit paneel toe in Vigil (paneel-id: ", "Add this panel in Vigil (panel id: "}},
    {"not_linked_entity", {"Of controleer of deze sensor bestaat: ", "Or check that this sensor exists: "}},
    {"old_profile", {"Update de firmware of Vigil", "Update the firmware or Vigil"}},
    {"no_admin_code", {"Stel eerst een installateurscode in Vigil in", "Set an installer code in Vigil first"}},
    {"page", {"Pagina ", "Page "}},
    // what Vigil answers when a code or an action is refused (see localize_error)
    {"err_invalid_code", {"Ongeldige code", "Invalid code"}},
    {"err_code_required", {"Voer een code in", "A code is required"}},
    {"err_locked_pre", {"Te veel foute codes. Probeer het over ", "Too many wrong codes. Try again in "}},
    {"err_locked_post", {" min opnieuw", " min"}},
    {"err_locked", {"Te veel foute codes. Even wachten", "Too many wrong codes. Wait a moment"}},
    {"err_locked_permanent", {"Te veel foute codes. Vergrendeld totdat een beheerder dit in Vigil opheft", "Too many wrong codes. Locked until an administrator unlocks it in Vigil"}},
    {"err_bypass_tamper", {"U mag sabotage niet omzeilen of terugzetten", "You may not bypass or restore tamper"}},
    {"err_bypass", {"U mag sensoren niet omzeilen of terugzetten", "You may not bypass or restore sensors"}},
    {"err_blocked", {"Dit paneel is geblokkeerd", "This panel is blocked"}},
    {"err_not_allowed", {"Dit paneel mag dit niet", "This panel may not do this"}},
    {"err_no_installer_code", {"Stel eerst een installateurscode in Vigil in", "Set an installer code in Vigil first"}},
    {"err_not_bypassable", {"Deze sensor kan niet worden omzeild", "This sensor cannot be bypassed"}},
    // sensor states
    {"st_closed", {"dicht", "closed"}},
    {"st_open", {"open", "open"}},
    {"st_waiting", {"wacht", "waiting"}},
    {"st_bypassed", {"omzeild", "bypassed"}},
    {"st_bypassed_at_arm", {"omzeild bij inschakelen", "bypassed at arming"}},
    {"st_unavailable", {"storing", "fault"}},
    // causes of an alarm
    {"cause_intrusion", {"Inbraak", "Intrusion"}},
    {"cause_fire", {"Brand", "Fire"}},
    {"cause_gas", {"Gas", "Gas"}},
    {"cause_tamper", {"Sabotage", "Tamper"}},
    {"cause_alarm24", {"24-uursalarm", "24-hour alarm"}},
    {"cause_silent24", {"Stil alarm", "Silent alarm"}},
    {"cause_water", {"Water", "Water"}},
    {"cause_fault", {"Sensorstoring", "Sensor fault"}},
    // codes
    {"nav_alarm", {"Alarm", "Alarm"}},
    {"nav_info", {"Info", "Info"}},
    {"code_hint", {"Code", "Code"}},
};

// The version of the profile this firmware understands (PROFILE_VERSION in Vigil) and of this firmware.
constexpr int PROFILE_VERSION = 1;

inline int parse_language(const std::string &s) { return s.rfind("nl", 0) == 0 ? NL : EN; }

// -------------------------------------------------------------------------------- the state

// Who may see the list of sensors on the panel: everyone, only after a code, or nobody.
enum SensorList { LIST_ALWAYS = 0, LIST_CODE = 1, LIST_NEVER = 2 };

inline int parse_sensor_list(const std::string &s) {
  if (s == "always") return LIST_ALWAYS;
  if (s == "never") return LIST_NEVER;
  return LIST_CODE;  // anything else, a typo too, is the safe choice
}

// What Home Assistant told us. The YAML fills this in; nothing here talks to the network.
struct Context {
  int lang = NL;
  bool ha_connected = false;
  std::string state;      // alarm_control_panel state
  std::string mode;       // home / away / night / vacation / custom: the armed mode, or the target while arming
  // From the profile entity of this panel in Vigil:
  int profile_version = 0;  // 0 until the profile is there (not added in Vigil yet, or Vigil is too old)
  std::string panel_id;
  bool blocked = false;
  int modes_mask = 0;       // 1 home, 2 away, 4 night, 8 vacation, 16 custom; 0 if blocked
  bool can_disarm = true;
  bool can_bypass = true;
  bool has_admin_code = false;
  bool profile_unlocked = false;  // Vigil unlocked this panel (by the installer code) and still does
  int open_total = 0;       // number of open sensors, also when the names are hidden
  int faults_total = 0;
  bool code_arm_required = true;
  bool screen_off_on_alarm = false;  // may the screen go dark while the alarm is going off
  double delay_end = NAN;  // epoch seconds of the end of the exit or entry delay
  int delay_total = 0;     // the length of the running delay in seconds, for the ring (see ring_percent)
  std::string delay_for;   // the state `delay_total` is for
  double now = NAN;        // the time in epoch seconds, NAN until the clock is set
  std::string changed_by;   // the user
  std::string changed_via;  // the panel or device it was done on
  std::string cause;
  std::string cause_sensor;
  std::string last_alarm;  // the alarm memory in one line ("14:03 Front door > Hall"), empty if there is none
  std::string open_now;   // names of the sensors that are open at all
  std::string open_mode;  // names of the sensors that are open in the current mode
  std::string faults;
  int problems = 0;       // number of problems (alarm entity or profile)
  std::string sensors;    // one "name|entity|status|bypassable" line per sensor
  std::string message;    // an error to show for a while
  int refused_action = 0; // an arm action that Vigil refused because something stops it: the button "bypass and arm" repeats it
  bool force = false;     // the keypad is open for "bypass and arm"
  int sensor_list = LIST_CODE;     // see SensorList
  bool sensors_unlocked = false;   // a code (user or installer) was entered a moment ago, on this panel
  bool installer_unlocked = false; // the installer code was entered a moment ago: the info page may open
  std::string device_name;        // the ESPHome name: the panel id and the source of every call
};

inline Context ctx;

inline std::string tr(const char *key) {
  for (const Text &t : TEXTS) {
    if (std::strcmp(t.key, key) == 0) return t.text[ctx.lang >= 0 && ctx.lang < LANGUAGE_COUNT ? ctx.lang : EN];
  }
  return key;  // a missing text is visible instead of blank
}

// Home Assistant answers a refused action with a text in ITS language (often English), while the panel speaks
// the language of the panel. Texts Vigil is known to send, in English and in Dutch, are replaced by the same
// text in the panel's language; anything else is shown as it came. The phrases must keep matching the
// `exceptions` in translations/en.json and nl.json (a test checks that). The order matters: the first row
// that fits wins.
struct ErrorRow {
  const char *en;
  const char *nl;
  const char *key;
};

inline const ErrorRow *error_rows(size_t &count) {
  static const ErrorRow rows[] = {
      {"until an administrator", "totdat een beheerder", "err_locked_permanent"},
      {"Too many wrong codes", "Te veel foute codes", "err_locked"},
      {"Invalid code", "Ongeldige code", "err_invalid_code"},
      {"A code is required", "Een code is vereist", "err_code_required"},
      {"right to bypass tamper", "recht om sabotage te omzeilen", "err_bypass_tamper"},
      {"right to bypass", "recht om te omzeilen", "err_bypass"},
      {"is blocked", "is geblokkeerd", "err_blocked"},
      {"may not do this", "mag dit niet", "err_not_allowed"},
      {"no installer code", "geen installateurscode", "err_no_installer_code"},
      {"cannot be bypassed", "kan niet worden omzeild", "err_not_bypassable"},
  };
  count = sizeof(rows) / sizeof(rows[0]);
  return rows;
}

// ---------------------------------------------------------------------------- small helpers

inline std::string localize_error(const std::string &raw) {
  size_t count = 0;
  const ErrorRow *rows = error_rows(count);
  for (size_t i = 0; i < count; i++) {
    if (raw.find(rows[i].en) == std::string::npos && raw.find(rows[i].nl) == std::string::npos) continue;
    std::string key = rows[i].key;
    if (key != "err_locked") return tr(rows[i].key);
    // "Try again in 5 min": the number of minutes is the first number in the text
    size_t start = raw.find_first_of("0123456789");
    if (start == std::string::npos) return tr("err_locked");
    size_t end = raw.find_first_not_of("0123456789", start);
    return tr("err_locked_pre") + raw.substr(start, end == std::string::npos ? std::string::npos : end - start) + tr("err_locked_post");
  }
  return raw;
}

// "Arming refused: alarm_condition (Front door)." (or the Dutch text): the same in the panel's language, and
// whether bypassing the sensor could help. An empty text means: this is not a refusal of that kind.
struct Refusal {
  std::string text;
  bool forceable = false;
};

inline Refusal parse_refusal(const std::string &raw) {
  Refusal out;
  size_t at = raw.find("Arming refused: ");
  size_t skip = 16;
  if (at == std::string::npos) {
    at = raw.find("Inschakelen geweigerd: ");
    skip = 23;
  }
  if (at == std::string::npos) return out;
  size_t from = at + skip;
  size_t space = raw.find(' ', from);
  std::string reason = raw.substr(from, space == std::string::npos ? std::string::npos : space - from);
  std::string names;
  size_t open = raw.find('(', from), close = raw.find(')', from);
  if (open != std::string::npos && close != std::string::npos && close > open) names = raw.substr(open + 1, close - open - 1);
  std::string key = "refuse_" + reason;
  std::string text = tr(key.c_str());
  if (text == key) return out;  // a reason this firmware does not know: shown as it came
  size_t pct = text.find("%s");
  if (pct != std::string::npos) text.replace(pct, 2, names.empty() ? "?" : names);
  out.text = text;
  out.forceable = reason != "not_disarmed";
  return out;
}

// Home Assistant sends "None", "unknown" and so on for an attribute that has no value.
inline std::string clean(const std::string &s) {
  if (s == "None" || s == "unknown" || s == "unavailable") return "";
  return s;
}

inline bool truthy(const std::string &s) {
  return s == "on" || s == "On" || s == "true" || s == "True" || s == "1";
}

inline double parse_number(const std::string &s) {
  if (s.empty() || s == "None" || s == "unknown" || s == "unavailable") return NAN;
  char *end = nullptr;
  double v = std::strtod(s.c_str(), &end);
  return end == s.c_str() ? NAN : v;
}

// A whole number from an attribute, or `fallback` if there is none.
inline int to_int(const std::string &s, int fallback) {
  double v = parse_number(s);
  return std::isnan(v) ? fallback : (int) v;
}

// ------------------------------------------------------------------------- linked and allowed

inline bool state_known() {
  return ctx.ha_connected && !ctx.state.empty() && ctx.state != "unknown" && ctx.state != "unavailable";
}

// Is there a profile this firmware understands? Without one this panel is not (yet) known to Vigil.
inline bool linked() { return ctx.profile_version == PROFILE_VERSION; }

// May the panel work at all: connected, known to Vigil, a profile it understands, not blocked.
inline bool usable() { return state_known() && linked() && !ctx.blocked; }

// The colours of Vigil, the same on the card and on the panel. One colour per state: the ring, the icon and the
// active tab use it; `state_tint` is the dark version for the background of the icon.
constexpr uint32_t COL_OK = 0x4CCB8F;       // disarmed and everything closed
constexpr uint32_t COL_WARN = 0xF2B84B;     // arming, or something open
constexpr uint32_t COL_ENTRY = 0xFF9F43;    // entry delay
constexpr uint32_t COL_ALARM = 0xF0605D;    // alarm
constexpr uint32_t COL_HOME = 0x5B9BF0;
constexpr uint32_t COL_AWAY = 0xFF8A5B;
constexpr uint32_t COL_NIGHT = 0x9A8CF2;
constexpr uint32_t COL_VACATION = 0x4FC3C9;
constexpr uint32_t COL_CUSTOM = 0xD58BDD;
constexpr uint32_t COL_OFF = 0x8A94A6;      // no connection, not linked, blocked

// ---------------------------------------------------------------------------------- sensors

struct SensorRow {
  std::string name, entity, status;
  bool bypassable = false;
};

inline std::vector<SensorRow> sensor_rows() {
  std::vector<SensorRow> rows;
  const std::string &text = ctx.sensors;
  size_t start = 0;
  while (start <= text.size()) {
    size_t end = text.find('\n', start);
    if (end == std::string::npos) end = text.size();
    std::string line = text.substr(start, end - start);
    start = end + 1;
    if (line.empty()) continue;
    std::string parts[4];
    size_t from = 0;
    int n = 0;
    while (n < 3) {
      size_t bar = line.find('|', from);
      if (bar == std::string::npos) break;
      parts[n++] = line.substr(from, bar - from);
      from = bar + 1;
    }
    if (n < 3) continue;  // not a line we understand
    parts[3] = line.substr(from);
    rows.push_back({parts[0], parts[1], parts[2], parts[3] == "1"});
  }
  return rows;
}

constexpr int ROWS_PER_PAGE = 5;

inline int sensor_count() { return (int) sensor_rows().size(); }

inline int page_count() {
  int n = sensor_count();
  return n <= 0 ? 1 : (n + ROWS_PER_PAGE - 1) / ROWS_PER_PAGE;
}

inline std::string status_text(const std::string &status) {
  std::string key = "st_" + status;
  for (const Text &t : TEXTS)
    if (key == t.key) return tr(key.c_str());
  return status;
}

inline uint32_t status_color(const std::string &status) {
  if (status == "open" || status == "waiting") return COL_WARN;
  if (status == "unavailable") return COL_ALARM;
  if (status == "bypassed" || status == "bypassed_at_arm") return COL_OFF;
  return COL_OK;
}

inline bool is_bypassed(const std::string &status) { return status == "bypassed"; }

// The row at a position on a page (page counts from 0); an empty row if there is none.
inline SensorRow row_at(int page, int slot) {
  std::vector<SensorRow> rows = sensor_rows();
  size_t i = (size_t) page * ROWS_PER_PAGE + slot;
  return i < rows.size() ? rows[i] : SensorRow{};
}

inline int open_count() {
  int n = 0;
  for (const SensorRow &r : sensor_rows())
    if (r.status == "open" || r.status == "waiting") n++;
  return n;
}

// How many sensors are open: counted from the list when Vigil sent the names, otherwise the number
// Vigil sent. The number is always there; the names are only there while this panel may show them.
inline int open_total_count() { return sensor_rows().empty() ? ctx.open_total : open_count(); }

// Did the installer code unlock this panel, and does Vigil still agree?
inline bool unlocked_now() { return ctx.sensors_unlocked && ctx.profile_unlocked; }

// May the list of sensors be shown right now?
inline bool sensors_visible() { return ctx.sensor_list == LIST_ALWAYS || (ctx.sensor_list == LIST_CODE && unlocked_now()); }

// Is there a button for the list at all?
inline bool show_sensors_button() { return ctx.sensor_list != LIST_NEVER && usable(); }

// Names of sensors and of people on the main page while the alarm is on: only when the list is
// open to everyone. Otherwise someone standing at the panel would learn what is being watched.
inline bool details_visible() { return ctx.sensor_list == LIST_ALWAYS || unlocked_now(); }

inline std::string sensors_button_text() {
  std::string text = tr("sensors");
  int open = open_total_count();
  // The number of open sensors is no secret; the names are.
  if (open > 0) text += "  (" + std::to_string(open) + " " + tr("sensors_open") + ")";
  return text;
}

// ---------------------------------------------------------------------------- the main page

inline bool is_armed_state(const std::string &s) {
  return s == "armed_home" || s == "armed_away" || s == "armed_night" || s == "armed_vacation" || s == "armed_custom_bypass";
}

inline std::string mode_name(const std::string &mode) {
  if (mode == "home") return tr("home");
  if (mode == "away") return tr("away");
  if (mode == "night") return tr("night");
  if (mode == "vacation") return tr("vacation");
  if (mode == "custom") return tr("custom");
  return "";
}

inline std::string state_title() {
  if (!state_known()) return tr("offline");
  if (ctx.profile_version == 0 || !linked()) return tr("not_linked");
  if (ctx.blocked) return tr("blocked");
  if (ctx.state == "disarmed" || ctx.state == "arming" || ctx.state == "pending" || ctx.state == "triggered" ||
      is_armed_state(ctx.state)) {
    return tr(ctx.state.c_str());
  }
  return ctx.state;
}

inline uint32_t state_color() {
  if (!usable()) return COL_OFF;
  if (ctx.state == "disarmed") return COL_OK;
  if (ctx.state == "armed_home") return COL_HOME;
  if (ctx.state == "armed_away") return COL_AWAY;
  if (ctx.state == "armed_night") return COL_NIGHT;
  if (ctx.state == "armed_vacation") return COL_VACATION;
  if (ctx.state == "armed_custom_bypass") return COL_CUSTOM;
  if (ctx.state == "arming") return COL_WARN;
  if (ctx.state == "pending") return COL_ENTRY;
  if (ctx.state == "triggered") return COL_ALARM;
  return COL_OFF;
}

// The dark background that belongs to a colour above (for the circle behind an icon, and the alarm screen).
inline uint32_t tint_of(uint32_t color) {
  switch (color) {
    case COL_OK: return 0x14281F;
    case COL_WARN: return 0x2A2314;
    case COL_ENTRY: return 0x2C2014;
    case COL_ALARM: return 0x3A1519;
    case COL_HOME: return 0x17233A;
    case COL_AWAY: return 0x2E1E17;
    case COL_NIGHT: return 0x211E3A;
    case COL_VACATION: return 0x14282B;
    case COL_CUSTOM: return 0x2D1E33;
    default: return 0x1B232D;
  }
}
inline uint32_t state_tint() { return tint_of(state_color()); }

// The icons: Material Design Icons (the font `font_icons` in the YAML holds exactly these). The strings are UTF-8.
#define VIGIL_ICON_SHIELD_CHECK "\U000F0CC8"
#define VIGIL_ICON_SHIELD_ALERT "\U000F0ECD"
#define VIGIL_ICON_SHIELD_LOCK "\U000F099D"
#define VIGIL_ICON_SHIELD_HOME "\U000F0CCB"
#define VIGIL_ICON_HOME "\U000F06A1"
#define VIGIL_ICON_AWAY "\U000F0A48"
#define VIGIL_ICON_NIGHT "\U000F0594"
#define VIGIL_ICON_VACATION "\U000F001D"  // airplane
#define VIGIL_ICON_CUSTOM "\U000F062E"    // tune
#define VIGIL_ICON_UNLOCK "\U000F0FC7"
#define VIGIL_ICON_LOCK "\U000F0341"
#define VIGIL_ICON_GRID "\U000F11D9"
#define VIGIL_ICON_INFO "\U000F02FD"
#define VIGIL_ICON_WIFI "\U000F05A9"
#define VIGIL_ICON_WIFI_OFF "\U000F05AA"
#define VIGIL_ICON_BACKSPACE "\U000F0B5C"
#define VIGIL_ICON_CHECK "\U000F012C"
#define VIGIL_ICON_CLOSE "\U000F0156"
#define VIGIL_ICON_BACK "\U000F0141"
#define VIGIL_ICON_BELL "\U000F009F"
#define VIGIL_ICON_TIMER "\U000F051F"
#define VIGIL_ICON_LINK_OFF "\U000F0338"
#define VIGIL_ICON_CANCEL "\U000F073A"
#define VIGIL_ICON_ALERT "\U000F002A"
#define VIGIL_ICON_SHIELD_OFF "\U000F099C"

// The icon in the ring: what the state is, at a glance.
inline std::string state_icon() {
  if (!state_known()) return VIGIL_ICON_WIFI_OFF;
  if (!linked()) return VIGIL_ICON_LINK_OFF;
  if (ctx.blocked) return VIGIL_ICON_CANCEL;
  const std::string &s = ctx.state;
  if (s == "disarmed") return open_total_count() > 0 || ctx.faults_total > 0 || ctx.problems > 0 ? VIGIL_ICON_SHIELD_ALERT : VIGIL_ICON_SHIELD_CHECK;
  if (s == "armed_home") return VIGIL_ICON_HOME;
  if (s == "armed_away") return VIGIL_ICON_AWAY;
  if (s == "armed_night") return VIGIL_ICON_NIGHT;
  if (s == "armed_vacation") return VIGIL_ICON_VACATION;
  if (s == "armed_custom_bypass") return VIGIL_ICON_CUSTOM;
  if (s == "arming" || s == "pending") return VIGIL_ICON_TIMER;
  if (s == "triggered") return VIGIL_ICON_BELL;
  return VIGIL_ICON_SHIELD_OFF;
}

// The colour of the ring and the icon. A disarmed panel with something open is amber, not green: it is not ready.
inline uint32_t ring_color() {
  if (usable() && ctx.state == "disarmed" && (open_total_count() > 0 || ctx.faults_total > 0 || ctx.problems > 0)) return COL_WARN;
  return state_color();
}

// Seconds left of the running delay, or -1 if there is none. `now` is the time in epoch seconds,
// or NAN if the clock is not set yet.
inline int seconds_left(double now) {
  if (std::isnan(ctx.delay_end) || std::isnan(now)) return -1;
  double left = ctx.delay_end - now;
  if (left < 0) left = 0;
  return (int) std::ceil(left);
}

// Does the ring count down? During the exit and the entry delay, if the clock and the end of the delay are known.
inline bool counting(double now) {
  return (ctx.state == "arming" || ctx.state == "pending") && usable() && seconds_left(now) >= 0;
}

// The number in the ring while it counts down: the seconds left.
inline std::string ring_text(double now) { return counting(now) ? std::to_string(seconds_left(now)) : std::string(); }

// How full the ring is, 0 to 100. A delay counts down from the full ring to empty; the length of the delay is the
// first number of seconds seen after the state changed (Vigil sends only the end of the delay). Outside a delay
// the ring is full: it is the colour that tells what the state is.
inline int ring_percent(double now) {
  if (!counting(now)) {
    ctx.delay_total = 0;
    ctx.delay_for.clear();
    return 100;
  }
  int left = seconds_left(now);
  if (ctx.delay_for != ctx.state || left > ctx.delay_total) {
    ctx.delay_for = ctx.state;
    ctx.delay_total = left;
  }
  if (ctx.delay_total <= 0) return 0;
  int pct = (int) std::lround(100.0 * left / ctx.delay_total);
  return pct < 0 ? 0 : (pct > 100 ? 100 : pct);
}

inline std::string cause_text() {
  if (ctx.cause.empty()) return "";
  std::string key = "cause_" + ctx.cause;
  for (const Text &t : TEXTS)
    if (key == t.key) return tr(key.c_str());
  return ctx.cause;
}

inline void add_line(std::string &out, const std::string &line) {
  if (line.empty()) return;
  if (!out.empty()) out += "\n";
  out += line;
}

// The small text under the title. An error message wins from everything else.
inline std::string state_sub(double /*now: the ring shows the countdown*/) {
  if (!ctx.message.empty()) return ctx.message;
  if (!state_known()) return "";
  if (ctx.profile_version == 0) {
    // The firmware reads sensor.<panel id with underscores>_profile; show it, so a mismatch is easy to see.
    std::string id = ctx.device_name;
    for (auto &c : id) if (c == '-') c = '_';
    return tr("not_linked_sub") + ctx.device_name + "). " + tr("not_linked_entity") + "sensor." + id + "_profile";
  }
  if (!linked()) return tr("old_profile");
  if (ctx.blocked) return tr("blocked_sub");
  std::string out;
  const std::string &s = ctx.state;
  if (s == "disarmed") {
    // Only how many are open: the names are on the sensor list, also after that list was unlocked.
    int open = open_total_count();
    if (open > 0) add_line(out, tr("open") + std::to_string(open));
    else add_line(out, tr("all_closed"));
    if (details_visible() && !ctx.last_alarm.empty()) add_line(out, tr("last_alarm") + ctx.last_alarm);
    if (!ctx.faults.empty()) add_line(out, tr("problems") + ctx.faults);
    else if (ctx.faults_total > 0 || ctx.problems > 0) add_line(out, tr("problems") + std::to_string(ctx.faults_total > 0 ? ctx.faults_total : ctx.problems));
  } else if (is_armed_state(s)) {
    if (details_visible()) {
      if (!ctx.changed_by.empty()) add_line(out, tr("by") + ctx.changed_by);
      else if (!ctx.changed_via.empty()) add_line(out, tr("by_unknown"));  // done on a panel or device, without a code
      if (!ctx.changed_via.empty()) add_line(out, tr("via") + ctx.changed_via);
      if (!ctx.open_mode.empty()) add_line(out, tr("open") + ctx.open_mode);
    }
  } else if (s == "arming") {
    add_line(out, mode_name(ctx.mode));
    add_line(out, tr("leave_now"));
    if (!ctx.open_mode.empty()) add_line(out, tr("open") + ctx.open_mode);
  } else if (s == "pending") {
    add_line(out, tr("enter_now"));
    if (details_visible()) add_line(out, ctx.cause_sensor);
  } else if (s == "triggered") {
    add_line(out, cause_text());
    if (details_visible()) add_line(out, ctx.cause_sensor);
  }
  return out;
}

// Which buttons are there? Only the modes that are switched on in Vigil, and while the alarm is
// off. As soon as it is on, there is one button: disarm.
inline bool show_home() { return usable() && ctx.state == "disarmed" && (ctx.modes_mask & 1); }
inline bool show_away() { return usable() && ctx.state == "disarmed" && (ctx.modes_mask & 2); }
inline bool show_night() { return usable() && ctx.state == "disarmed" && (ctx.modes_mask & 4); }
inline bool show_vacation() { return usable() && ctx.state == "disarmed" && (ctx.modes_mask & 8); }
inline bool show_custom() { return usable() && ctx.state == "disarmed" && (ctx.modes_mask & 16); }
// More than three buttons in one row: the texts get smaller so they fit.
inline int mode_count() {
  return (show_home() ? 1 : 0) + (show_away() ? 1 : 0) + (show_night() ? 1 : 0) + (show_vacation() ? 1 : 0) +
         (show_custom() ? 1 : 0);
}
// After a refused arm that bypassing could solve: one button instead of the tiles, until the message is gone.
inline bool show_force() { return usable() && ctx.state == "disarmed" && ctx.refused_action != 0 && ctx.can_bypass; }
inline bool show_disarm() { return usable() && ctx.state != "disarmed" && ctx.can_disarm; }

// May sensors be bypassed from this panel? Only a panel that is allowed to, and only while it works.
inline bool bypass_allowed() { return usable() && ctx.can_bypass; }

// Does an action on the keypad need a code? Disarming and bypassing always do (the profile of a
// panel says so), the installer code of the panel unlocks the list and the info. Arming only
// when Vigil asks for a code to arm, the same as in Home Assistant itself.
enum Action {
  NONE = 0, ARM_HOME = 1, ARM_AWAY = 2, ARM_NIGHT = 3, DISARM = 4, BYPASS = 5, UNBYPASS = 6, UNLOCK = 7, INFO = 8,
  ARM_VACATION = 9, ARM_CUSTOM = 10
};

inline bool is_arm_action(int a) { return (a >= ARM_HOME && a <= ARM_NIGHT) || a == ARM_VACATION || a == ARM_CUSTOM; }
// The mode name the vigil_alarm.arm service takes.
inline const char *arm_mode_name(int a) {
  switch (a) {
    case ARM_HOME: return "home";
    case ARM_AWAY: return "away";
    case ARM_VACATION: return "vacation";
    case ARM_CUSTOM: return "custom";
    default: return "night";
  }
}

inline bool needs_code(int action) {
  if (ctx.force) return true;  // bypassing always needs a code, like bypassing a sensor by hand
  if (action == DISARM || action == UNLOCK || action == INFO || action == BYPASS || action == UNBYPASS) return true;
  return ctx.code_arm_required;
}

// Only the info page needs the installer code. The list of sensors opens with the code of any Vigil user (or the
// installer code); both are sent to Vigil with the action `unlock_panel`, which then says what it was for.
inline bool is_admin_action(int action) { return action == INFO; }
inline bool is_unlock_action(int action) { return action == UNLOCK || action == INFO; }

// Which code is expected: the code of a user, or the installer code of this panel.
inline std::string keypad_hint(int action) { return tr(is_admin_action(action) ? "hint_admin" : "hint_user"); }

inline std::string keypad_title(int action, const std::string &sensor_name) {
  switch (action) {
    case ARM_HOME: return ctx.force ? tr("force_title") + tr("home") : tr("arm_home");
    case ARM_AWAY: return ctx.force ? tr("force_title") + tr("away") : tr("arm_away");
    case ARM_NIGHT: return ctx.force ? tr("force_title") + tr("night") : tr("arm_night");
    case ARM_VACATION: return ctx.force ? tr("force_title") + tr("vacation") : tr("arm_vacation");
    case ARM_CUSTOM: return ctx.force ? tr("force_title") + tr("custom") : tr("arm_custom");
    case DISARM: return tr("disarm");
    case BYPASS: return tr("bypass_title") + sensor_name;
    case UNBYPASS: return tr("unbypass_title") + sensor_name;
    case UNLOCK: return tr("unlock_title");
    case INFO: return tr("info_title");
  }
  return "";
}

// May the screen go dark now? Only in a steady state: disarmed or fully armed. Never while the alarm counts down
// (arming, entry delay): somebody is busy with the panel. During an alarm it is a setting of Vigil. Without a
// connection there is no alarm to look at, so it may.
inline bool screen_may_sleep() {
  if (!ctx.ha_connected) return true;
  const std::string &s = ctx.state;
  if (s == "arming" || s == "pending") return false;
  if (s == "triggered") return ctx.screen_off_on_alarm;
  return true;
}

// What to do with the keypad when something changed: 0 nothing, 2 close it. It never opens by itself, not even
// during the entry delay or an alarm: whoever sees what is going on presses Disarm. `action` is the action the
// open keypad is for (0 if it is closed).
inline int keypad_route(bool keypad_open, int action) {
  if (!keypad_open) return 0;
  if (action == DISARM) return ctx.state == "disarmed" ? 2 : 0;  // nobody has to disarm any more
  if (is_arm_action(action) && ctx.state != "disarmed") return 2;
  return 0;
}

}  // namespace vigil
