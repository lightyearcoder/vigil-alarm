/* Vigil card: the alarm on a dashboard, mostly for a tablet on the wall.
 *
 * Add it to a dashboard as:  type: custom:vigil-card
 *
 * It is a dumb terminal, like the ESPHome panel. It asks Vigil which panel of the register belongs to the
 * logged-in Home Assistant user, and then follows that panel's profile (the sensor Vigil makes for it): the
 * modes it may arm in, whether it may disarm or bypass, whether it may show the sensors, the language.
 * It only reads. What the tablet may really do is enforced by Vigil on the server, whatever this card shows.
 * Narrow (a phone): one column. Wide (a tablet, 640 px and up): the state on the left, the modes or the keypad on the right.
 *
 * Optional setting:  idle_timeout: 30   (seconds without touch before a half typed code is forgotten)
 *
 * The logic mirrors esphome/vigil_alarm/vigil_panel.h; keep the two in step.
 */
(() => {
  if (customElements.get("vigil-card")) return;

  const TEXTS = {
    nl: {
      disarmed: "Uitgeschakeld", armed_home: "Thuis", armed_away: "Weg", armed_night: "Nacht", arming: "Inschakelen",
      pending: "Binnenkomst", triggered: "ALARM", offline: "Geen verbinding",
      home: "Thuis", away: "Weg", night: "Nacht", disarm: "Uitschakelen",
      home_sub: "Iemand is thuis", away_sub: "Iedereen vertrekt", night_sub: "Naar bed", countdown: "Nog {n} seconden",
      arm_home: "Thuis inschakelen", arm_away: "Weg inschakelen", arm_night: "Nacht inschakelen",
      bypass: "Omzeilen", unbypass: "Herstellen", bypass_title: "Omzeilen: ", unbypass_title: "Herstellen: ",
      unlock_title: "Sensoren bekijken", admin_code: "Installateurscode", hint_user: "Voer uw gebruikerscode in", hint_admin: "Voer de installateurscode in", sensors: "Sensoren", sensors_open: "open",
      all_closed: "Alles dicht", open: "Open: ", problems: "Storingen: ", leave_in: "Verlaat het huis: ",
      enter_in: "Schakel uit binnen: ", by: "Door ", by_unknown: "Door: onbekend", via: "Via ", practice: "Oefenmodus: geen sirene, geen meldingen", last_alarm: "Laatste alarm: ", false_alarm: " (vals alarm)", no_sensors: "Geen sensoren", back: "Terug", cancel: "Annuleren",
      blocked: "Geblokkeerd", blocked_sub: "Dit paneel is geblokkeerd in Vigil",
      refuse_alarm_condition: "Inschakelen kan niet: {s} staat open", refuse_sensor_unavailable: "Inschakelen kan niet: {s} reageert niet", refuse_sensor_open: "Inschakelen kan niet: {s} staat open", refuse_not_disarmed: "Het alarm staat al aan", force: "Omzeilen en inschakelen",
      not_linked: "Niet gekoppeld",
      not_linked_sub: "Voeg dit Home Assistant-account toe in Vigil onder Panelen. Account: ",
      err_invalid_code: "Ongeldige code", err_code_required: "Voer een code in", err_locked_pre: "Te veel foute codes. Probeer het over ", err_locked_post: " min opnieuw", err_locked: "Te veel foute codes. Even wachten", err_locked_permanent: "Te veel foute codes. Vergrendeld totdat een beheerder dit in Vigil opheft", err_bypass_tamper: "U mag sabotage niet omzeilen of terugzetten", err_bypass: "U mag sensoren niet omzeilen of terugzetten", err_blocked: "Dit paneel is geblokkeerd", err_not_allowed: "Dit paneel mag dit niet", err_no_installer_code: "Stel eerst een installateurscode in Vigil in", err_not_bypassable: "Deze sensor kan niet worden omzeild",
      old_profile: "Update Vigil of de kaart", no_admin_code: "Stel eerst een installateurscode in Vigil in",
      st_closed: "dicht", st_open: "open", st_waiting: "wacht", st_bypassed: "omzeild",
      st_bypassed_at_arm: "omzeild bij inschakelen", st_unavailable: "storing",
      cause_intrusion: "Inbraak", cause_fire: "Brand", cause_gas: "Gas", cause_tamper: "Sabotage",
      cause_fault: "Sensorstoring", ok: "OK", delete: "Wis", code: "Code",
    },
    en: {
      disarmed: "Disarmed", armed_home: "Home", armed_away: "Away", armed_night: "Night", arming: "Arming",
      pending: "Entry", triggered: "ALARM", offline: "No connection",
      home: "Home", away: "Away", night: "Night", disarm: "Disarm",
      home_sub: "Someone is home", away_sub: "Everyone is leaving", night_sub: "Going to bed", countdown: "{n} seconds left",
      arm_home: "Arm home", arm_away: "Arm away", arm_night: "Arm night",
      bypass: "Bypass", unbypass: "Restore", bypass_title: "Bypass: ", unbypass_title: "Restore: ",
      unlock_title: "View sensors", admin_code: "Installer code", hint_user: "Enter your user code", hint_admin: "Enter the installer code", sensors: "Sensors", sensors_open: "open",
      all_closed: "All closed", open: "Open: ", problems: "Problems: ", leave_in: "Leave within: ",
      enter_in: "Disarm within: ", by: "By ", by_unknown: "By: unknown", via: "Via ", practice: "Practice mode: no siren, no messages", last_alarm: "Last alarm: ", false_alarm: " (false alarm)", no_sensors: "No sensors", back: "Back", cancel: "Cancel",
      blocked: "Blocked", blocked_sub: "This panel is blocked in Vigil",
      refuse_alarm_condition: "Cannot arm: {s} is open", refuse_sensor_unavailable: "Cannot arm: {s} does not respond", refuse_sensor_open: "Cannot arm: {s} is open", refuse_not_disarmed: "The alarm is already on", force: "Bypass and arm",
      not_linked: "Not linked",
      not_linked_sub: "Add this Home Assistant account in Vigil under Panels. Account: ",
      err_invalid_code: "Invalid code", err_code_required: "A code is required", err_locked_pre: "Too many wrong codes. Try again in ", err_locked_post: " min", err_locked: "Too many wrong codes. Wait a moment", err_locked_permanent: "Too many wrong codes. Locked until an administrator unlocks it in Vigil", err_bypass_tamper: "You may not bypass or restore tamper", err_bypass: "You may not bypass or restore sensors", err_blocked: "This panel is blocked", err_not_allowed: "This panel may not do this", err_no_installer_code: "Set an installer code in Vigil first", err_not_bypassable: "This sensor cannot be bypassed",
      old_profile: "Update Vigil or the card", no_admin_code: "Set an installer code in Vigil first",
      st_closed: "closed", st_open: "open", st_waiting: "waiting", st_bypassed: "bypassed",
      st_bypassed_at_arm: "bypassed at arming", st_unavailable: "fault",
      cause_intrusion: "Intrusion", cause_fire: "Fire", cause_gas: "Gas", cause_tamper: "Tamper",
      cause_fault: "Sensor fault", ok: "OK", delete: "Delete", code: "Code",
    },
  };
  const PROFILE_VERSION = 1;
  // One colour per situation; the same set is used by the ESPHome panel (vigil_panel.h). Modes have their own colour.
  const COLORS = {
    none: "#8A94A6", disarmed: "#4CCB8F", notready: "#F2B84B", armed_home: "#5B9BF0", armed_away: "#FF8A5B",
    armed_night: "#9A8CF2", arming: "#F2B84B", pending: "#FF9F43", triggered: "#F0605D",
  };
  const MODE_COLORS = { home: "#5B9BF0", away: "#FF8A5B", night: "#9A8CF2" };
  const ICONS = {
    shield: '<path d="M12 3l7 3v5c0 5-3.2 8.2-7 10-3.8-1.8-7-5-7-10V6z"/>',
    check: '<path d="M9 12l2.2 2.2L15.5 10"/>',
    alert: '<path d="M12 8v4M12 15.5h.01"/>',
    siren: '<path d="M7 18v-5a5 5 0 0110 0v5"/><path d="M5 18h14M12 3v2M4.5 6.5l1.4 1.4M19.5 6.5l-1.4 1.4"/>',
    exit: '<path d="M10 4H5v16h5"/><path d="M15 8l4 4-4 4M19 12H9"/>',
    home: '<path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z"/>',
    moon: '<path d="M20 14.5A8 8 0 019.5 4 8 8 0 1020 14.5z"/>',
    unlock: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 017.5-2"/>',
    grid: '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',
    close: '<path d="M6 6l12 12M18 6L6 18"/>',
    back: '<path d="M15 6l-6 6 6 6"/>',
    chevron: '<path d="M9 6l6 6-6 6"/>',
    erase: '<path d="M9 6h11v12H9l-5-6z"/><path d="M12.5 9.5l5 5M17.5 9.5l-5 5"/>',
    tick: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  };
  const icon = (name, size = 24, extra = "") =>
    `<svg viewBox="0 0 24 24" width="${size}" height="${size}" aria-hidden="true" ${extra}>${ICONS[name] || ""}</svg>`;
  const RING = 364.4;  // circumference of the ring (radius 58)
  const ERROR_ROWS = [
    ["until an administrator", "totdat een beheerder", "err_locked_permanent"],
    ["Too many wrong codes", "Te veel foute codes", "err_locked"],
    ["Invalid code", "Ongeldige code", "err_invalid_code"],
    ["A code is required", "Een code is vereist", "err_code_required"],
    ["right to bypass tamper", "recht om sabotage te omzeilen", "err_bypass_tamper"],
    ["right to bypass", "recht om te omzeilen", "err_bypass"],
    ["is blocked", "is geblokkeerd", "err_blocked"],
    ["may not do this", "mag dit niet", "err_not_allowed"],
    ["no installer code", "geen installateurscode", "err_no_installer_code"],
    ["cannot be bypassed", "kan niet worden omzeild", "err_not_bypassable"],
  ];
  const ADMIN_ACTIONS = [];  // the sensor list opens with any user code (or the installer code); the card has no info page
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const clean = (v) => (v === null || v === undefined || v === "None" || v === "unknown" || v === "unavailable" ? "" : String(v));

  class VigilCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._ui = { keypad: null, view: "main", unlocked: false, message: "", busy: false };
      this._key = "";
      this._info = null; // the answer of Vigil: which panel is this user
      this._failed = false;
      this._config = {};
    }

    setConfig(config) {
      this._config = config || {};
    }
    getCardSize() {
      return 8;
    }
    static getStubConfig() {
      return {};
    }

    connectedCallback() {
      this._hello();
      this._helloTimer = setInterval(() => this._hello(), 60000);
      this._tick = setInterval(() => this._countdown(), 1000);
      this.addEventListener("pointerdown", () => this._touch());
      // A real keyboard works on the keypad too (a tablet with a keyboard, or a computer).
      this._onKey = (ev) => this._keyPressed(ev);
      window.addEventListener("keydown", this._onKey);
      this._touch();
    }
    disconnectedCallback() {
      window.removeEventListener("keydown", this._onKey);
      clearInterval(this._helloTimer);
      clearInterval(this._tick);
      clearTimeout(this._idle);
      clearTimeout(this._msgTimer);
    }

    set hass(hass) {
      this._hass = hass;
      if (!this._info && !this._asked) this._hello();
      const key = this._snapshotKey();
      if (key === this._key) return;
      this._key = key;
      if (!this._p() || this._p().unlocked === false) this._ui.unlocked = false;
      this._route();
      this._render();
    }

    // ----------------------------------------------------------- talking to Vigil
    async _hello() {
      if (!this._hass) return;
      this._asked = true;
      try {
        const info = await this._hass.callWS({ type: "vigil_alarm/tablet" });
        this._info = info;
        this._failed = false;
      } catch (err) {
        this._failed = true;
      }
      this._key = "";
      this.hass = this._hass;
    }

    _alarm() {
      const id = this._info && this._info.alarm_entity;
      return id && this._hass ? this._hass.states[id] : null;
    }
    _profile() {
      const id = this._info && this._info.profile_entity;
      return id && this._hass ? this._hass.states[id] : null;
    }
    _p() {
      const s = this._profile();
      return s ? s.attributes : null;
    }
    _snapshotKey() {
      const a = this._alarm();
      const p = this._profile();
      return JSON.stringify([this._info, this._failed, a && [a.state, a.attributes], p && [p.state, p.attributes],
        this._hass && this._hass.language]);
    }

    // -------------------------------------------------------------------- texts
    _lang() {
      const p = this._p();
      const l = (p && p.language) || (this._hass && this._hass.language) || "en";
      return String(l).startsWith("nl") ? "nl" : "en";
    }
    tr(key) {
      return (TEXTS[this._lang()] || TEXTS.en)[key] || key;
    }

    // ---------------------------------------------------------------- the logic
    _stateKnown() {
      const a = this._alarm();
      return !!a && !this._failed && !["unknown", "unavailable", ""].includes(a.state);
    }
    _linked() {
      const p = this._p();
      return !!p && Number(p.profile_version) === PROFILE_VERSION;
    }
    _usable() {
      const p = this._p();
      return !!this._info && this._info.linked && this._stateKnown() && this._linked() && !p.blocked;
    }
    _unlockedNow() {
      const p = this._p();
      return this._ui.unlocked && !!p && !!p.unlocked;
    }
    _sensorsVisible() {
      const p = this._p();
      return !!p && (p.sensor_list === "always" || (p.sensor_list === "code" && this._unlockedNow()));
    }
    _detailsVisible() {
      const p = this._p();
      return !!p && (p.sensor_list === "always" || this._unlockedNow());
    }
    _showSensorsButton() {
      const p = this._p();
      return this._usable() && p.sensor_list !== "never";
    }
    _rows() {
      const p = this._p();
      return String((p && p.sensors) || "")
        .split("\n")
        .map((line) => line.split("|"))
        .filter((f) => f.length >= 4)
        .map((f) => ({ name: f[0], entity: f[1], status: f[2], bypassable: f.slice(3).join("|") === "1" }));
    }
    _openTotal() {
      const rows = this._rows();
      if (rows.length) return rows.filter((r) => r.status === "open" || r.status === "waiting").length;
      const p = this._p();
      return Number((p && p.open_count) || 0);
    }
    _bypassAllowed() {
      return this._usable() && !!this._p().can_bypass;
    }
    _needsCode(action) {
      if (["disarm", "unlock", "bypass", "unbypass"].includes(action)) return true;
      const p = this._p();
      return !p || p.code_arm_required !== false;
    }
    _secondsLeft() {
      const a = this._alarm();
      const at = a && a.attributes;
      if (!at || !at.delay_end) { this._delayKey = null; return -1; }
      // Count from the seconds left on this device's own clock, so a clock that is off does not show.
      if (this._delayKey !== at.delay_end) {
        this._delayKey = at.delay_end;
        const left = Number(at.delay_left);
        this._delayLocal = Number.isFinite(left) ? Date.now() / 1000 + left : Number(at.delay_end);
        this._delayTotal = Math.max(1, this._delayLocal - Date.now() / 1000);
      }
      return Math.max(0, Math.ceil(this._delayLocal - Date.now() / 1000));
    }
    _title() {
      if (this._info && !this._info.linked && !this._failed) return this.tr("not_linked");
      if (!this._info || this._failed || !this._stateKnown()) return this.tr("offline");
      if (!this._p()) return this.tr("not_linked");
      if (!this._linked()) return this.tr("not_linked");
      if (this._p().blocked) return this.tr("blocked");
      const s = this._alarm().state;
      return TEXTS.en[s] ? this.tr(s) : s;
    }
    // What the ring shows: one of the keys of COLORS.
    _kind() {
      if (!this._usable()) return "none";
      const state = this._alarm().state;
      if (state === "disarmed" && this._openTotal() > 0) return "notready";
      return COLORS[state] ? state : "none";
    }
    _color() {
      return COLORS[this._kind()];
    }
    _fraction() {
      const left = this._secondsLeft();
      return left < 0 ? 1 : Math.min(1, left / (this._delayTotal || left || 1));
    }
    _sub() {
      if (this._ui.message) return this._ui.message;
      if (this._info && !this._info.linked) return this.tr("not_linked_sub") + (this._info.user || "");
      if (!this._stateKnown()) return "";
      if (!this._p()) return "";
      if (!this._linked()) return this.tr("old_profile");
      const p = this._p();
      if (p.blocked) return this.tr("blocked_sub");
      const a = this._alarm();
      const s = a.state;
      const at = a.attributes;
      const out = [];
      const add = (t) => t && out.push(t);
      const left = this._secondsLeft();
      const armed = ["armed_home", "armed_away", "armed_night"].includes(s);
      if (s === "disarmed") {
        if (Number(p.open_count) > 0) add(this.tr("open") + p.open_count);
        else add(this.tr("all_closed"));
        if (this._detailsVisible()) add(this._lastAlarm(at));
        if (clean(p.faults_text)) add(this.tr("problems") + clean(p.faults_text));
        else if (Number(p.faults_count) > 0 || Number(p.problems_count) > 0) {
          add(this.tr("problems") + (Number(p.faults_count) > 0 ? p.faults_count : p.problems_count));
        }
      } else if (armed) {
        if (this._detailsVisible()) {
          if (clean(at.changed_by)) add(this.tr("by") + clean(at.changed_by));
          else if (clean(at.changed_via)) add(this.tr("by_unknown"));
          if (clean(at.changed_via)) add(this.tr("via") + clean(at.changed_via));
          if (clean(p.open_sensors_text)) add(this.tr("open") + clean(p.open_sensors_text));
        }
      } else if (s === "arming") {
        const m = clean(at.mode);
        if (TEXTS.en[m]) add(this.tr(m));
        if (left >= 0) add(this.tr("leave_in") + left + " s");
        if (clean(p.open_sensors_text)) add(this.tr("open") + clean(p.open_sensors_text));
      } else if (s === "pending") {
        if (left >= 0) add(this.tr("enter_in") + left + " s");
        if (this._detailsVisible()) add(clean(at.cause_sensor));
      } else if (s === "triggered") {
        const c = clean(at.cause);
        if (c) add(TEXTS.en["cause_" + c] ? this.tr("cause_" + c) : c);
        if (this._detailsVisible()) add(clean(at.cause_sensor));
      }
      if (at.practice === true) out.unshift(this.tr("practice"));
      return out.join("\n");
    }
    // "Last alarm: 14:03 Front door → Hall → Living room": the path the intruder took, from the alarm memory.
    _lastAlarm(at) {
      const m = at && at.last_alarm;
      if (!m || !m.time) return "";
      const time = new Date(m.time * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const path = Array.isArray(m.path) ? m.path.map(clean).filter(Boolean).join(" → ") : "";
      return this.tr("last_alarm") + time + (path ? " " + path : clean(m.sensor) ? " " + clean(m.sensor) : "") + (m.cancelled ? this.tr("false_alarm") : "");
    }
    _modeButtons() {
      const p = this._p();
      if (!this._usable() || this._alarm().state !== "disarmed") return [];
      const mask = Number(p.modes_mask) || 0;
      return [["home", 1], ["away", 2], ["night", 4]].filter(([, bit]) => mask & bit).map(([m]) => m);
    }
    _showDisarm() {
      return this._usable() && this._alarm().state !== "disarmed" && !!this._p().can_disarm;
    }
    _sensorsButtonText() {
      const open = this._openTotal();
      return this.tr("sensors") + (open > 0 ? `  (${open} ${this.tr("sensors_open")})` : "");
    }

    // --------------------------------------------------------------------- keypad
    _touch() {
      clearTimeout(this._idle);
      const seconds = Number(this._config.idle_timeout) || 30;
      this._idle = setTimeout(() => {
        // Nobody touched the card: forget the code and go back to the main page. Is someone still supposed to
        // disarm, then the keypad comes back by itself.
        this._ui.keypad = null;
        this._ui.view = "main";
        this._ui.unlocked = false;
        this._route();
        this._render();
      }, seconds * 1000);
    }
    _openKeypad(action, extra = {}) {
      this._ui.keypad = { action, code: "", error: "", ...extra };
      this._render();
    }
    _closeKeypad() {
      this._ui.keypad = null;
      this._render();
    }
    // The keypad never opens by itself: whoever sees the alarm presses Disarm. It does close when it has become pointless.
    _route() {
      const k = this._ui.keypad;
      if (!k) return;
      const s = this._stateKnown() ? this._alarm().state : "";
      if (k.action === "disarm" && s === "disarmed") this._ui.keypad = null;
      else if (k.action.startsWith("arm_") && s !== "disarmed") this._ui.keypad = null;
    }
    _start(action, extra = {}) {
      if (ADMIN_ACTIONS.includes(action) && !this._p().has_admin_code) {
        this._flash(this.tr("no_admin_code"));
        return;
      }
      if (this._needsCode(action) || extra.force) this._openKeypad(action, extra);
      else this._run(action, "", extra);
    }
    _flash(text) {
      this._ui.message = text;
      clearTimeout(this._msgTimer);
      this._msgTimer = setTimeout(() => {
        this._ui.message = "";
        this._ui.force = null;
        this._render();
      }, 8000);
      this._render();
    }
    async _run(action, code, extra = {}) {
      const source = this._info.panel_id;
      const call = (service, data) => this._hass.callService("vigil_alarm", service, data);
      const withCode = (data) => (code ? { ...data, code } : data);
      this._ui.busy = true;
      try {
        if (action.startsWith("arm_")) await call("arm", withCode({ mode: action.slice(4), source, ...(extra.force ? { bypass_open: true } : {}) }));
        else if (action === "disarm") await call("disarm", { code, source });
        else if (action === "bypass") await call("bypass", { sensor: extra.entity, code, source });
        else if (action === "unbypass") await call("unbypass", { sensor: extra.entity, code, source });
        else if (action === "unlock") await call("unlock_panel", { code, source, scope: "sensors" });
        this._ui.busy = false;
        this._done(action);
      } catch (err) {
        this._ui.busy = false;
        const raw = (err && (err.message || err.error)) || String(err);
        const refused = action.startsWith("arm_") ? this._refusal(raw) : null;
        if (refused) {
          // Not a wrong code: something stops arming. Say what, and offer to bypass it and arm if that is allowed.
          this._ui.keypad = null;
          this._ui.force = !extra.force && refused.reason !== "not_disarmed" && this._bypassAllowed() ? { action } : null;
          this._flash(refused.text);
          return;
        }
        const text = this._localError(raw);
        if (this._ui.keypad) {
          this._ui.keypad.code = "";
          this._ui.keypad.error = text;
          this._render();
        } else this._flash(text);
      }
    }
    // "Arming refused: alarm_condition (Front door)." in the language of the panel.
    _refusal(raw) {
      const m = raw.match(/(?:Arming refused|Inschakelen geweigerd): (\w+) \(([^)]*)\)/);
      if (!m || !this.tr("refuse_" + m[1])) return null;
      return { reason: m[1], text: this.tr("refuse_" + m[1]).replace("{s}", m[2] || "?") };
    }
    // Home Assistant answers in its own language; Vigil's known refusals are shown in the language of the panel.
    // The phrases must keep matching translations/en.json and nl.json (a test checks that).
    _localError(raw) {
      for (const [en, nl, key] of ERROR_ROWS) {
        if (!raw.includes(en) && !raw.includes(nl)) continue;
        if (key !== "err_locked") return this.tr(key);
        const m = raw.match(/\d+/);
        return m ? this.tr("err_locked_pre") + m[0] + this.tr("err_locked_post") : this.tr("err_locked");
      }
      return raw;
    }
    _done(action) {
      this._ui.message = "";
      this._ui.force = null;
      this._ui.keypad = null;
      if (action === "unlock") {
        this._ui.unlocked = true;
        this._ui.view = "sensors";
      }
      this._render();
    }
    // Digits type the code, Backspace deletes, Enter confirms, Escape closes the keypad. Only while the keypad is open,
    // and never when you are typing in a field somewhere else on the dashboard.
    _keyPressed(ev) {
      if (!this._ui.keypad || ev.ctrlKey || ev.metaKey || ev.altKey || ev.defaultPrevented) return;
      const typing = ev.composedPath().some((n) => n.tagName && (/^(INPUT|TEXTAREA|SELECT)$/.test(n.tagName) || n.isContentEditable));
      if (typing) return;
      if (/^[0-9]$/.test(ev.key)) this._digit(ev.key);
      else if (ev.key === "Backspace" || ev.key === "Delete") this._backspace();
      else if (ev.key === "Enter") this._submit();
      else if (ev.key === "Escape") this._closeKeypad();
      else return;
      ev.preventDefault();
      this._touch();
    }
    _digit(d) {
      const k = this._ui.keypad;
      if (!k || k.code.length >= 12) return;
      k.code += d;
      this._renderCode();
    }
    _backspace() {
      const k = this._ui.keypad;
      if (!k) return;
      k.code = k.code.slice(0, -1);
      this._renderCode();
    }
    _submit() {
      const k = this._ui.keypad;
      if (!k || !k.code || this._ui.busy) return;
      const { action, code, entity, force } = k;
      k.error = "";
      this._run(action, code, { entity, force });
    }

    _keypadTitle(k) {
      switch (k.action) {
        case "arm_home": case "arm_away": case "arm_night": case "disarm": return this.tr(k.action);
        case "bypass": return this.tr("bypass_title") + (k.name || "");
        case "unbypass": return this.tr("unbypass_title") + (k.name || "");
        case "unlock": return this.tr("unlock_title");
      }
      return "";
    }

    // ------------------------------------------------------------------ rendering
    _countdown() {
      const a = this._alarm();
      if (a && (a.state === "arming" || a.state === "pending")) {
        const root = this.shadowRoot;
        const sub = root.querySelector(".subs");
        if (sub) sub.innerHTML = this._subHtml();
        const left = this._secondsLeft();
        const num = root.querySelector(".ring-num");
        if (num && left >= 0) num.textContent = String(left);
        const arc = root.querySelector(".ring-arc");
        if (arc) arc.setAttribute("stroke-dasharray", `${(RING * this._fraction()).toFixed(1)} ${RING}`);
      }
    }
    _renderCode() {
      const k = this._ui.keypad;
      const el = this.shadowRoot.querySelector(".dots");
      if (el && k) el.innerHTML = this._dotsHtml(k);
    }

    _render() {
      const root = this.shadowRoot;
      const keypad = this._ui.keypad;
      const sensorsView = this._ui.view === "sensors" && this._sensorsVisible() && this._usable();
      if (this._ui.view === "sensors" && !sensorsView) this._ui.view = "main";
      const kind = this._kind();
      const c = COLORS[kind];
      const name = this._info && this._info.name ? esc(this._info.name) : "";
      const header = `<header class="top"><img class="logo" src="/vigil_alarm_static/logo.png" alt=""><span class="brand">Vigil</span><span class="pname">${name}</span></header>`;
      let body;
      if (sensorsView && !keypad) body = this._sensorsHtml();
      else body = `<div class="grid ${keypad ? "has-keypad" : ""}">
        <section class="status">${this._ringHtml(kind, c)}<div class="title">${esc(this._title())}</div><div class="subs">${this._subHtml()}</div></section>
        <section class="side">${keypad ? this._keypadHtml(keypad) : this._sideHtml()}</section></div>`;
      root.innerHTML = `<style>${STYLE}</style><ha-card class="k-${kind}" style="--c:${c}">${header}${body}</ha-card>`;
      root.querySelectorAll("[data-act]").forEach((el) =>
        el.addEventListener("click", (ev) => this._click(el, ev)));
    }

    _ringHtml(kind, c) {
      const counting = kind === "arming" || kind === "pending";
      const left = this._secondsLeft();
      let inner;
      if (counting && left >= 0) {
        inner = `<text class="ring-num" x="66" y="66" text-anchor="middle" dominant-baseline="central">${left}</text>`;
      } else {
        const a = this._alarm();
        const state = this._usable() && a ? a.state : "";
        const glyph = kind === "triggered" ? "siren" : kind === "notready" ? "shield" : state === "armed_home" ? "home"
          : state === "armed_away" ? "exit" : state === "armed_night" ? "moon" : "shield";
        const extra = kind === "disarmed" ? ICONS.check : kind === "notready" ? ICONS.alert : "";
        inner = `<g transform="translate(33 33) scale(2.75)" class="ring-icon">${ICONS[glyph]}${extra}</g>`;
      }
      const dash = counting && left >= 0 ? `${(RING * this._fraction()).toFixed(1)} ${RING}` : `${RING} ${RING}`;
      const label = counting && left >= 0 ? this.tr("countdown").replace("{n}", left) : this._title();
      return `<svg class="ring" viewBox="0 0 132 132" role="img" aria-label="${esc(label)}">
        <circle class="ring-track" cx="66" cy="66" r="58"/>
        <circle class="ring-arc" cx="66" cy="66" r="58" transform="rotate(-90 66 66)" stroke-dasharray="${dash}"/>
        <circle class="ring-core" cx="66" cy="66" r="46"/>${inner}</svg>`;
    }

    // The first line of the text under the title is the one that matters; the rest is detail.
    _subHtml() {
      const lines = this._sub().split("\n").filter((l) => l);
      return lines.map((l, i) => `<div class="${i === 0 ? "s1" : "s2"}">${esc(l)}</div>`).join("");
    }

    _sideHtml() {
      const modes = this._modeButtons().map((m) => `<button class="mode" style="--m:${MODE_COLORS[m]}" data-act="arm" data-mode="${m}">
          <span class="dot">${icon(m === "away" ? "exit" : m === "home" ? "home" : "moon", 26)}</span>
          <span class="mt"><span class="mn">${esc(this.tr(m))}</span><span class="ms">${esc(this.tr(m + "_sub"))}</span></span>
          ${icon("chevron", 22, 'class="chev"')}</button>`).join("");
      const disarm = this._showDisarm()
        ? `<button class="disarm" data-act="disarm">${icon("unlock", 28)}<span>${esc(this.tr("disarm"))}</span></button>` : "";
      const force = this._ui.force && this._bypassAllowed()
        ? `<button class="force" data-act="force">${icon("exit", 24)}<span>${esc(this.tr("force"))}</span></button>` : "";
      const sensors = this._showSensorsButton()
        ? `<button class="sensors" data-act="sensors"><span class="dot s">${icon("grid", 22)}</span><span class="mn">${esc(this.tr("sensors"))}</span>${this._openTotal() > 0 ? `<span class="badge">${this._openTotal()}</span>` : ""}${icon("chevron", 20, 'class="chev"')}</button>` : "";
      return `<div class="modes">${modes}${disarm}${force}</div>${sensors}`;
    }

    _dotsHtml(k) {
      const n = Math.max(4, k.code.length);
      let out = "";
      for (let i = 0; i < n; i++) out += `<i class="${i < k.code.length ? "on" : ""}"></i>`;
      return out;
    }

    _keypadHtml(k) {
      const keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        .map((d) => `<button class="key" data-act="digit" data-d="${d}">${d}</button>`).join("");
      const placeholder = ADMIN_ACTIONS.includes(k.action) ? this.tr("admin_code") : this.tr("code");
      const placeholder_hint = this.tr(ADMIN_ACTIONS.includes(k.action) ? "hint_admin" : "hint_user");
      const glyph = k.action === "disarm" ? "unlock" : k.action.startsWith("arm_") ? "shield" : "grid";
      return `<div class="kp-head"><span class="dot">${icon(glyph, 24)}</span>
          <span class="mt"><span class="mn">${esc(this._keypadTitle(k))}</span><span class="ms err ${k.error ? "bad" : ""}">${esc(k.error || placeholder_hint)}</span></span></div>
        <div class="dots" aria-label="${esc(placeholder)}">${this._dotsHtml(k)}</div>
        <div class="keys">${keys}
          <button class="key sec" data-act="backspace" aria-label="${esc(this.tr("delete"))}">${icon("erase", 28)}</button>
          <button class="key" data-act="digit" data-d="0">0</button>
          <button class="key ok" data-act="submit" aria-label="${esc(this.tr("ok"))}">${icon("tick", 30, 'style="stroke-width:2.4"')}</button>
        </div>
        <button class="cancel" data-act="cancel">${icon("close", 20)}<span>${esc(this.tr("cancel"))}</span></button>`;
    }

    _sensorsHtml() {
      const rows = this._rows();
      const canBypass = this._bypassAllowed();
      const list = rows.length
        ? rows.map((r, i) => {
          const status = TEXTS.en["st_" + r.status] ? this.tr("st_" + r.status) : r.status;
          const color = r.status === "open" || r.status === "waiting" ? "#F2B84B" : r.status === "unavailable" ? "#F0605D"
            : r.status === "bypassed" || r.status === "bypassed_at_arm" ? "#8A94A6" : "#4CCB8F";
          const btn = canBypass && r.bypassable
            ? `<button class="small" data-act="${r.status === "bypassed" ? "unbypass" : "bypass"}" data-i="${i}">${esc(this.tr(r.status === "bypassed" ? "unbypass" : "bypass"))}</button>` : "";
          return `<div class="row" style="--s:${color}"><span class="sdot"></span><div class="rt"><div class="rname">${esc(r.name)}</div><div class="rstate">${esc(status)}</div></div>${btn}</div>`;
        }).join("")
        : `<div class="empty">${esc(this.tr("no_sensors"))}</div>`;
      return `<div class="sens-head"><button class="back" data-act="back">${icon("back", 22)}<span>${esc(this.tr("back"))}</span></button>
          <span class="kp-title">${esc(this.tr("sensors"))}</span></div>
        <div class="list">${list}</div>`;
    }

    _click(el, ev) {
      ev.stopPropagation();
      this._touch();
      const act = el.dataset.act;
      if (act === "arm") this._start("arm_" + el.dataset.mode);
      else if (act === "disarm") this._start("disarm");
      else if (act === "force") this._ui.force && this._start(this._ui.force.action, { force: true });
      else if (act === "sensors") {
        if (this._sensorsVisible()) {
          this._ui.view = "sensors";
          this._render();
        } else this._start("unlock");
      } else if (act === "back") {
        this._ui.view = "main";
        this._ui.unlocked = false; // leaving the list forgets the unlock, like the panel does
        this._render();
      } else if (act === "cancel") this._closeKeypad();
      else if (act === "digit") this._digit(el.dataset.d);
      else if (act === "backspace") this._backspace();
      else if (act === "submit") this._submit();
      else if (act === "bypass" || act === "unbypass") {
        const r = this._rows()[Number(el.dataset.i)];
        if (r) this._start(act, { entity: r.entity, name: r.name });
      }
    }
  }

  const STYLE = `
    :host { display: block; }
    ha-card { display: block; box-sizing: border-box; padding: 16px; container-type: inline-size; user-select: none;
      -webkit-user-select: none; color: var(--primary-text-color, #E8ECF2);
      --surface: var(--secondary-background-color, #151A22); --line: var(--divider-color, #2C3542);
      --muted: var(--secondary-text-color, #8A94A6); }
    ha-card.k-triggered { border: 2px solid var(--c);
      background: color-mix(in srgb, var(--c) 12%, var(--ha-card-background, var(--card-background-color, #0E1116))); }
    button { font: inherit; color: inherit; border: 0; cursor: pointer; touch-action: manipulation; background: none; padding: 0; text-align: left; }
    svg { fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; flex: none; }
    .top { display: flex; align-items: center; gap: 10px; min-height: 34px; margin-bottom: 12px; }
    .logo { width: 28px; height: 28px; border-radius: 8px; }
    .brand { font-size: 18px; font-weight: 700; }
    .pname { margin-left: auto; font-size: 14px; color: var(--muted); }
    .grid { display: grid; gap: 14px; grid-template-columns: minmax(0, 1fr); }
    .grid.has-keypad .status { display: none; }
    .status { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; text-align: center;
      padding: 26px 16px 24px; border-radius: 26px; background: var(--surface); border: 1px solid var(--line); }
    .ring { width: 150px; height: 150px; }
    .ring-track { stroke: var(--line); stroke-width: 8; }
    .ring-arc { stroke: var(--c); stroke-width: 8; }
    .ring-core { fill: color-mix(in srgb, var(--c) 16%, var(--surface)); stroke: none; }
    .ring-icon { stroke: var(--c); stroke-width: 1.4; }
    .ring-num { fill: var(--primary-text-color, #E8ECF2); stroke: none; font-size: 50px; font-weight: 700; }
    .title { font-size: 30px; font-weight: 800; line-height: 1.15; margin-top: 8px; }
    .s1 { font-size: 17px; font-weight: 600; opacity: .9; }
    .s2 { font-size: 14px; color: var(--muted); }
    .side { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
    .modes { display: flex; flex-direction: column; gap: 12px; }
    .mode, .sensors { display: flex; align-items: center; gap: 14px; min-height: 72px; padding: 0 18px; border-radius: 22px;
      background: var(--surface); border: 1px solid var(--line); }
    .sensors { min-height: 60px; }
    .dot { display: flex; align-items: center; justify-content: center; width: 46px; height: 46px; border-radius: 50%;
      color: var(--m, var(--c)); background: color-mix(in srgb, var(--m, var(--c)) 18%, var(--surface)); flex: none; }
    .dot.s { width: 38px; height: 38px; --m: var(--muted); }
    .mt { flex: 1; display: flex; flex-direction: column; min-width: 0; }
    .mn { font-size: 20px; font-weight: 800; flex: 1; }
    .mt .mn { flex: none; }
    .ms { font-size: 14px; color: var(--muted); }
    .chev { color: var(--muted); opacity: .7; }
    .badge { min-width: 26px; height: 26px; padding: 0 7px; box-sizing: border-box; border-radius: 13px; background: #F2B84B; color: #2A1D00;
      font-size: 14px; font-weight: 800; display: flex; align-items: center; justify-content: center; }
    .disarm { display: flex; align-items: center; justify-content: center; gap: 12px; min-height: 76px; border-radius: 22px;
      background: #4CCB8F; color: #07251A; font-size: 22px; font-weight: 800; }
    .force { display: flex; align-items: center; justify-content: center; gap: 10px; min-height: 60px; border-radius: 20px;
      border: 2px solid #F2B84B; color: #F2B84B; background: transparent; font-size: 19px; font-weight: 800; }
    .kp-head { display: flex; align-items: center; gap: 14px; }
    .kp-head .dot { color: #4CCB8F; background: color-mix(in srgb, #4CCB8F 18%, var(--surface)); --m: #4CCB8F; }
    .err.bad { color: #F0605D; }
    .dots { display: flex; justify-content: center; align-items: center; gap: 16px; height: 30px; }
    .dots i { width: 14px; height: 14px; box-sizing: border-box; border-radius: 50%; border: 2px solid var(--line); }
    .dots i.on { background: var(--primary-text-color, #E8ECF2); border-color: var(--primary-text-color, #E8ECF2); }
    .keys { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
    .key { display: flex; align-items: center; justify-content: center; min-height: 64px; border-radius: 18px; font-size: 28px;
      font-weight: 600; text-align: center; background: var(--surface); border: 1px solid var(--line); }
    .key.ok { background: #4CCB8F; border-color: #4CCB8F; color: #07251A; } .key.sec { color: var(--muted); }
    .cancel, .back { display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 52px; border-radius: 18px;
      font-size: 17px; font-weight: 600; background: var(--surface); border: 1px solid var(--line); }
    .back { padding: 0 18px; }
    .sens-head { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }
    .kp-title { font-size: 22px; font-weight: 800; }
    .list { display: grid; gap: 10px; grid-template-columns: minmax(0, 1fr); max-height: 520px; overflow-y: auto; }
    .row { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 20px; background: var(--surface); border: 1px solid var(--line); }
    .sdot { width: 12px; height: 12px; border-radius: 50%; background: var(--s); flex: none; }
    .rt { flex: 1; min-width: 0; } .rname { font-size: 18px; font-weight: 700; } .rstate { font-size: 14px; color: var(--s); }
    .small { min-height: 44px; padding: 0 16px; border-radius: 14px; font-weight: 700; background: var(--line); }
    .empty { padding: 20px; text-align: center; color: var(--muted); }
    @container (min-width: 640px) {
      .grid { grid-template-columns: minmax(0, 1fr) minmax(300px, 380px); align-items: stretch; }
      .grid.has-keypad .status { display: flex; }
      .side .modes { flex: 1; } .side .mode, .side .disarm { flex: 1; }
      .list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .title { font-size: 34px; }
      .ring { width: 180px; height: 180px; }
    }
  `;

  customElements.define("vigil-card", VigilCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "vigil-card",
    name: "Vigil",
    description: "The Vigil alarm for a tablet: state, modes, keypad and sensors, following the profile of the tablet.",
  });
})();
