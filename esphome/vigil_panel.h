// Vigil Alarm touch panel: the texts and the display logic.
//
// This file is plain C++ without any ESPHome or LVGL calls, so it can be tested on a computer.
// The YAML (vigil-panel.yaml) only holds the layout and the wiring; everything that decides
// what the panel shows is here.
//
// Adding a language: add a column to TEXTS and an entry to LANGUAGES. Keep the texts to plain
// ASCII, the built-in LVGL fonts do not contain accented letters.
#pragma once

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
    {"arming", {"Inschakelen", "Arming"}},
    {"pending", {"Voer code in", "Enter code"}},
    {"triggered", {"ALARM", "ALARM"}},
    {"offline", {"Geen verbinding", "No connection"}},
    {"home", {"Thuis", "Home"}},
    {"away", {"Weg", "Away"}},
    {"night", {"Nacht", "Night"}},
    {"disarm", {"Uitschakelen", "Disarm"}},
    {"arm_home", {"Thuis inschakelen", "Arm home"}},
    {"arm_away", {"Weg inschakelen", "Arm away"}},
    {"arm_night", {"Nacht inschakelen", "Arm night"}},
    {"bypass", {"Omzeilen", "Bypass"}},
    {"unbypass", {"Herstellen", "Restore"}},
    {"bypass_title", {"Omzeilen: ", "Bypass: "}},
    {"unbypass_title", {"Herstellen: ", "Restore: "}},
    {"unlock_title", {"Sensoren bekijken", "View sensors"}},
    {"sensors", {"Sensoren", "Sensors"}},
    {"sensors_open", {"open", "open"}},
    {"all_closed", {"Alles dicht", "All closed"}},
    {"open", {"Open: ", "Open: "}},
    {"problems", {"Storingen: ", "Problems: "}},
    {"leave_in", {"Verlaat het huis: ", "Leave within: "}},
    {"enter_in", {"Schakel uit binnen: ", "Disarm within: "}},
    {"by", {"Door ", "By "}},
    {"no_sensors", {"Geen sensoren", "No sensors"}},
    {"settings", {"Instellingen", "Settings"}},
    {"language", {"Taal", "Language"}},
    {"info", {"Info", "Info"}},
    {"connected", {"Verbonden met Home Assistant", "Connected to Home Assistant"}},
    {"not_connected", {"Niet verbonden", "Not connected"}},
    {"signal", {"Wifi-signaal: ", "Wi-Fi signal: "}},
    {"uptime", {"Aan sinds: ", "Uptime: "}},
    {"minutes", {" min", " min"}},
    {"page", {"Pagina ", "Page "}},
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
    {"cause_fault", {"Sensorstoring", "Sensor fault"}},
    // codes
    {"code_hint", {"Code", "Code"}},
};

// The name shown on the settings page, in the language itself.
static const char *const LANGUAGES[LANGUAGE_COUNT] = {"Nederlands", "English"};

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
  std::string mode;       // home / away / night: the armed mode, or the target while arming
  int features = 0;       // supported_features bitmask: 1 home, 2 away, 4 night
  bool code_arm_required = true;
  double delay_end = NAN;  // epoch seconds of the end of the exit or entry delay
  double now = NAN;        // the time in epoch seconds, NAN until the clock is set
  std::string changed_by;
  std::string cause;
  std::string cause_sensor;
  std::string open_now;   // names of the sensors that are open at all
  std::string open_mode;  // names of the sensors that are open in the current mode
  std::string faults;
  int problems = 0;
  std::string sensors;    // one "name|entity|status|bypassable" line per sensor
  std::string message;    // an error to show for a while
  int sensor_list = LIST_CODE;     // see SensorList
  bool sensors_unlocked = false;   // a code was entered a moment ago
};

inline Context ctx;

inline std::string tr(const char *key) {
  for (const Text &t : TEXTS) {
    if (std::strcmp(t.key, key) == 0) return t.text[ctx.lang >= 0 && ctx.lang < LANGUAGE_COUNT ? ctx.lang : EN];
  }
  return key;  // a missing text is visible instead of blank
}

// ---------------------------------------------------------------------------- small helpers

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
  if (status == "open" || status == "waiting") return 0xF59E0B;
  if (status == "unavailable") return 0xEF4444;
  if (status == "bypassed" || status == "bypassed_at_arm") return 0x8A94A3;
  return 0x22C55E;
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

// May the list of sensors be shown right now?
inline bool sensors_visible() { return ctx.sensor_list == LIST_ALWAYS || (ctx.sensor_list == LIST_CODE && ctx.sensors_unlocked); }

// Is there a button for the list at all?
inline bool show_sensors_button() { return ctx.sensor_list != LIST_NEVER; }

// Names of sensors and of people on the main page while the alarm is on: only when the list is
// open to everyone. Otherwise someone standing at the panel would learn what is being watched.
inline bool details_visible() { return ctx.sensor_list == LIST_ALWAYS || ctx.sensors_unlocked; }

inline std::string sensors_button_text() {
  std::string text = tr("sensors");
  int open = open_count();
  // With the alarm off the open sensors are what keeps you from arming, so those may be shown.
  if (open > 0 && (ctx.state == "disarmed" || sensors_visible())) text += "  (" + std::to_string(open) + " " + tr("sensors_open") + ")";
  return text;
}

// ---------------------------------------------------------------------------- the main page

inline bool state_known() {
  return ctx.ha_connected && !ctx.state.empty() && ctx.state != "unknown" && ctx.state != "unavailable";
}

inline bool is_armed_state(const std::string &s) {
  return s == "armed_home" || s == "armed_away" || s == "armed_night";
}

inline std::string mode_name(const std::string &mode) {
  if (mode == "home") return tr("home");
  if (mode == "away") return tr("away");
  if (mode == "night") return tr("night");
  return "";
}

inline std::string state_title() {
  if (!state_known()) return tr("offline");
  if (ctx.state == "disarmed" || ctx.state == "arming" || ctx.state == "pending" || ctx.state == "triggered" ||
      is_armed_state(ctx.state)) {
    return tr(ctx.state.c_str());
  }
  return ctx.state;
}

inline uint32_t state_color() {
  if (!state_known()) return 0x475569;
  if (ctx.state == "disarmed") return 0x16A34A;
  if (ctx.state == "armed_home") return 0x0D9488;
  if (ctx.state == "armed_away") return 0x2563EB;
  if (ctx.state == "armed_night") return 0x7C3AED;
  if (ctx.state == "arming") return 0xD97706;
  if (ctx.state == "pending") return 0xEA580C;
  if (ctx.state == "triggered") return 0xDC2626;
  return 0x475569;
}

// Seconds left of the running delay, or -1 if there is none. `now` is the time in epoch seconds,
// or NAN if the clock is not set yet.
inline int seconds_left(double now) {
  if (std::isnan(ctx.delay_end) || std::isnan(now)) return -1;
  double left = ctx.delay_end - now;
  if (left < 0) left = 0;
  return (int) std::ceil(left);
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
inline std::string state_sub(double now) {
  if (!ctx.message.empty()) return ctx.message;
  if (!state_known()) return "";
  std::string out;
  const std::string &s = ctx.state;
  int left = seconds_left(now);
  if (s == "disarmed") {
    add_line(out, ctx.open_now.empty() ? tr("all_closed") : tr("open") + ctx.open_now);
    if (!ctx.faults.empty() || ctx.problems > 0) {
      add_line(out, tr("problems") + (ctx.faults.empty() ? std::to_string(ctx.problems) : ctx.faults));
    }
  } else if (is_armed_state(s)) {
    if (details_visible()) {
      if (!ctx.changed_by.empty()) add_line(out, tr("by") + ctx.changed_by);
      if (!ctx.open_mode.empty()) add_line(out, tr("open") + ctx.open_mode);
    }
  } else if (s == "arming") {
    add_line(out, mode_name(ctx.mode));
    if (left >= 0) add_line(out, tr("leave_in") + std::to_string(left) + " s");
    if (!ctx.open_mode.empty()) add_line(out, tr("open") + ctx.open_mode);
  } else if (s == "pending") {
    if (left >= 0) add_line(out, tr("enter_in") + std::to_string(left) + " s");
    if (details_visible()) add_line(out, ctx.cause_sensor);
  } else if (s == "triggered") {
    add_line(out, cause_text());
    if (details_visible()) add_line(out, ctx.cause_sensor);
  }
  return out;
}

// Which buttons are there? Only the modes that are switched on in Vigil, and while the alarm is
// off. As soon as it is on, there is one button: disarm.
inline bool show_home() { return state_known() && ctx.state == "disarmed" && (ctx.features & 1); }
inline bool show_away() { return state_known() && ctx.state == "disarmed" && (ctx.features & 2); }
inline bool show_night() { return state_known() && ctx.state == "disarmed" && (ctx.features & 4); }
inline bool show_disarm() { return state_known() && ctx.state != "disarmed"; }

// Does an action on the keypad need a code? Disarming always does. Arming and bypassing only
// when Vigil asks for a code to arm, the same as in Home Assistant itself.
enum Action { NONE = 0, ARM_HOME = 1, ARM_AWAY = 2, ARM_NIGHT = 3, DISARM = 4, BYPASS = 5, UNBYPASS = 6, UNLOCK = 7 };

inline bool needs_code(int action) {
  if (action == DISARM || action == UNLOCK) return true;
  // Bypassing right after the list was unlocked with a code: that code is used, no second question.
  if ((action == BYPASS || action == UNBYPASS) && ctx.sensors_unlocked) return false;
  return ctx.code_arm_required;
}

inline std::string keypad_title(int action, const std::string &sensor_name) {
  switch (action) {
    case ARM_HOME: return tr("arm_home");
    case ARM_AWAY: return tr("arm_away");
    case ARM_NIGHT: return tr("arm_night");
    case DISARM: return tr("disarm");
    case BYPASS: return tr("bypass_title") + sensor_name;
    case UNBYPASS: return tr("unbypass_title") + sensor_name;
    case UNLOCK: return tr("unlock_title");
  }
  return "";
}

// Should the keypad open by itself? Yes, as soon as someone has to disarm within the delay.
inline bool wants_disarm_keypad() {
  return state_known() && (ctx.state == "pending" || ctx.state == "triggered");
}

// What to do with the keypad when something changed: 0 nothing, 1 open it to disarm, 2 close it.
// `action` is the action the open keypad is for (0 if it is closed).
inline int keypad_route(bool keypad_open, int action) {
  if (wants_disarm_keypad()) return (keypad_open && action == DISARM) ? 0 : 1;
  if (!keypad_open) return 0;
  if (action == DISARM) return 2;  // nobody has to disarm any more
  if ((action == ARM_HOME || action == ARM_AWAY || action == ARM_NIGHT) && ctx.state != "disarmed") return 2;
  return 0;
}

}  // namespace vigil
