/* Vigil card: the alarm on a dashboard, mostly for a tablet on the wall.
 *
 * Add it to a dashboard as:  type: custom:vigil-card
 *
 * It is a dumb terminal, like the ESPHome panel. It asks Vigil which panel of the register belongs to the
 * logged-in Home Assistant user, and then follows that panel's profile (the sensor Vigil makes for it): the
 * modes it may arm in, whether it may disarm or bypass, whether it may show the sensors, the language.
 * It only reads. What the tablet may really do is enforced by Vigil on the server, whatever this card shows.
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
      arm_home: "Thuis inschakelen", arm_away: "Weg inschakelen", arm_night: "Nacht inschakelen",
      bypass: "Omzeilen", unbypass: "Herstellen", bypass_title: "Omzeilen: ", unbypass_title: "Herstellen: ",
      unlock_title: "Sensoren bekijken", admin_code: "Installateurscode", hint_user: "Voer uw gebruikerscode in", hint_admin: "Voer de installateurscode in", sensors: "Sensoren", sensors_open: "open",
      all_closed: "Alles dicht", open: "Open: ", problems: "Storingen: ", leave_in: "Verlaat het huis: ",
      enter_in: "Schakel uit binnen: ", by: "Door ", no_sensors: "Geen sensoren", back: "Terug", cancel: "Annuleren",
      blocked: "Geblokkeerd", blocked_sub: "Dit paneel is geblokkeerd in Vigil",
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
      arm_home: "Arm home", arm_away: "Arm away", arm_night: "Arm night",
      bypass: "Bypass", unbypass: "Restore", bypass_title: "Bypass: ", unbypass_title: "Restore: ",
      unlock_title: "View sensors", admin_code: "Installer code", hint_user: "Enter your user code", hint_admin: "Enter the installer code", sensors: "Sensors", sensors_open: "open",
      all_closed: "All closed", open: "Open: ", problems: "Problems: ", leave_in: "Leave within: ",
      enter_in: "Disarm within: ", by: "By ", no_sensors: "No sensors", back: "Back", cancel: "Cancel",
      blocked: "Blocked", blocked_sub: "This panel is blocked in Vigil",
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
  const COLORS = {
    disarmed: "#16A34A", armed_home: "#0D9488", armed_away: "#2563EB", armed_night: "#7C3AED",
    arming: "#D97706", pending: "#EA580C", triggered: "#DC2626", none: "#475569",
  };
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
      this._touch();
    }
    disconnectedCallback() {
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
    _color() {
      if (!this._usable()) return COLORS.none;
      return COLORS[this._alarm().state] || COLORS.none;
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
        if (clean(p.faults_text)) add(this.tr("problems") + clean(p.faults_text));
        else if (Number(p.faults_count) > 0 || Number(p.problems_count) > 0) {
          add(this.tr("problems") + (Number(p.faults_count) > 0 ? p.faults_count : p.problems_count));
        }
      } else if (armed) {
        if (this._detailsVisible()) {
          if (clean(at.changed_by)) add(this.tr("by") + clean(at.changed_by));
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
      return out.join("\n");
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
      if (this._needsCode(action)) this._openKeypad(action, extra);
      else this._run(action, "", extra);
    }
    _flash(text) {
      this._ui.message = text;
      clearTimeout(this._msgTimer);
      this._msgTimer = setTimeout(() => {
        this._ui.message = "";
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
        if (action.startsWith("arm_")) await call("arm", withCode({ mode: action.slice(4), source }));
        else if (action === "disarm") await call("disarm", { code, source });
        else if (action === "bypass") await call("bypass", { sensor: extra.entity, code, source });
        else if (action === "unbypass") await call("unbypass", { sensor: extra.entity, code, source });
        else if (action === "unlock") await call("unlock_panel", { code, source, scope: "sensors" });
        this._ui.busy = false;
        this._done(action);
      } catch (err) {
        this._ui.busy = false;
        const text = this._localError((err && (err.message || err.error)) || String(err));
        if (this._ui.keypad) {
          this._ui.keypad.code = "";
          this._ui.keypad.error = text;
          this._render();
        } else this._flash(text);
      }
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
      this._ui.keypad = null;
      if (action === "unlock") {
        this._ui.unlocked = true;
        this._ui.view = "sensors";
      }
      this._render();
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
      const { action, code, entity } = k;
      k.error = "";
      this._run(action, code, { entity });
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
        const sub = this.shadowRoot.querySelector(".sub");
        if (sub) sub.textContent = this._sub();
      }
    }
    _renderCode() {
      const k = this._ui.keypad;
      const el = this.shadowRoot.querySelector(".dots");
      if (el && k) el.textContent = "●".repeat(k.code.length) || " ";
    }

    _render() {
      const root = this.shadowRoot;
      const keypad = this._ui.keypad;
      const sensorsView = this._ui.view === "sensors" && this._sensorsVisible() && this._usable();
      if (this._ui.view === "sensors" && !sensorsView) this._ui.view = "main";
      let body;
      if (keypad) body = this._keypadHtml(keypad);
      else if (sensorsView) body = this._sensorsHtml();
      else body = this._mainHtml();
      root.innerHTML = `<style>${STYLE}</style><ha-card>${body}</ha-card>`;
      root.querySelectorAll("[data-act]").forEach((el) =>
        el.addEventListener("click", (ev) => this._click(el, ev)));
    }

    _mainHtml() {
      const buttons = this._modeButtons()
        .map((m) => `<button class="mode m-${m}" data-act="arm" data-mode="${m}">${esc(this.tr(m))}</button>`)
        .join("");
      const disarm = this._showDisarm() ? `<button class="mode m-disarm" data-act="disarm">${esc(this.tr("disarm"))}</button>` : "";
      const sensors = this._showSensorsButton()
        ? `<button class="sensors" data-act="sensors">${esc(this._sensorsButtonText())}</button>` : "";
      const name = this._info && this._info.name ? esc(this._info.name) : "";
      return `<div class="top">${name}</div>
        <div class="state" style="background:${this._color()}">
          <div class="title">${esc(this._title())}</div>
          <div class="sub">${esc(this._sub())}</div>
        </div>
        <div class="modes">${buttons}${disarm}</div>${sensors}`;
    }

    _keypadHtml(k) {
      const keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        .map((d) => `<button class="key" data-act="digit" data-d="${d}">${d}</button>`).join("");
      const placeholder = ADMIN_ACTIONS.includes(k.action) ? this.tr("admin_code") : this.tr("code");
      const placeholder_hint = this.tr(ADMIN_ACTIONS.includes(k.action) ? "hint_admin" : "hint_user");
      return `<div class="kp-title">${esc(this._keypadTitle(k))}</div>
        <div class="dots" aria-label="${esc(placeholder)}">${"●".repeat(k.code.length) || " "}</div>
        <div class="err ${k.error ? "" : "hint"}">${esc(k.error || placeholder_hint)}</div>
        <div class="keys">${keys}
          <button class="key sec" data-act="backspace">⌫</button>
          <button class="key" data-act="digit" data-d="0">0</button>
          <button class="key ok" data-act="submit">${esc(this.tr("ok"))}</button>
        </div>
        <button class="sensors" data-act="cancel">${esc(this.tr("cancel"))}</button>`;
    }

    _sensorsHtml() {
      const rows = this._rows();
      const canBypass = this._bypassAllowed();
      const list = rows.length
        ? rows.map((r, i) => {
          const status = TEXTS.en["st_" + r.status] ? this.tr("st_" + r.status) : r.status;
          const color = r.status === "open" || r.status === "waiting" ? "#F59E0B" : r.status === "unavailable" ? "#EF4444"
            : r.status === "bypassed" || r.status === "bypassed_at_arm" ? "#8A94A3" : "#22C55E";
          const btn = canBypass && r.bypassable
            ? `<button class="small" data-act="${r.status === "bypassed" ? "unbypass" : "bypass"}" data-i="${i}">${esc(this.tr(r.status === "bypassed" ? "unbypass" : "bypass"))}</button>` : "";
          return `<div class="row"><div><div class="rname">${esc(r.name)}</div><div class="rstate" style="color:${color}">${esc(status)}</div></div>${btn}</div>`;
        }).join("")
        : `<div class="empty">${esc(this.tr("no_sensors"))}</div>`;
      return `<button class="back" data-act="back">‹ ${esc(this.tr("back"))}</button>
        <div class="kp-title">${esc(this.tr("sensors"))}</div>
        <div class="list">${list}</div>`;
    }

    _click(el, ev) {
      ev.stopPropagation();
      this._touch();
      const act = el.dataset.act;
      if (act === "arm") this._start("arm_" + el.dataset.mode);
      else if (act === "disarm") this._start("disarm");
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
    ha-card { display: block; padding: 14px; box-sizing: border-box; user-select: none; -webkit-user-select: none;
      color: var(--primary-text-color, #e6eaf0); }
    button { font: inherit; color: inherit; border: 0; cursor: pointer; touch-action: manipulation; }
    .top { min-height: 20px; font-size: 14px; color: var(--secondary-text-color, #8a94a3); margin: 0 4px 8px; }
    .state { border-radius: 24px; padding: 28px 16px; text-align: center; color: #fff; min-height: 150px;
      display: flex; flex-direction: column; justify-content: center; gap: 12px; }
    .title { font-size: 40px; font-weight: 600; line-height: 1.1; }
    .sub { font-size: 18px; white-space: pre-line; opacity: .95; }
    .modes { display: flex; gap: 12px; margin-top: 14px; }
    .mode { flex: 1; min-height: 88px; border-radius: 20px; font-size: 26px; color: #fff; }
    .m-home { background: #0D9488; } .m-away { background: #2563EB; } .m-night { background: #7C3AED; }
    .m-disarm { background: transparent; border: 2px solid #475569; color: var(--primary-text-color, #fff); }
    .sensors, .back { width: 100%; margin-top: 12px; min-height: 56px; border-radius: 18px; font-size: 18px;
      background: var(--secondary-background-color, #1c2430); }
    .back { width: auto; padding: 0 18px; margin: 0 0 8px; }
    .kp-title { font-size: 24px; text-align: center; margin: 4px 0 10px; }
    .dots { height: 56px; line-height: 56px; border-radius: 16px; text-align: center; font-size: 30px; letter-spacing: 6px;
      background: var(--secondary-background-color, #141a22); }
    .err.hint { color: #94a3b8; }
    .err { min-height: 22px; margin: 6px 0; text-align: center; font-size: 14px; color: #f87171; }
    .keys { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .key { min-height: 66px; border-radius: 16px; font-size: 30px; background: var(--secondary-background-color, #1c2430); }
    .key.ok { background: #16A34A; color: #fff; font-size: 24px; } .key.sec { color: var(--secondary-text-color, #aab4c3); }
    .list { display: flex; flex-direction: column; gap: 8px; max-height: 460px; overflow-y: auto; }
    .row { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 14px;
      border-radius: 16px; background: var(--secondary-background-color, #141a22); }
    .rname { font-size: 18px; } .rstate { font-size: 14px; }
    .small { min-height: 44px; padding: 0 16px; border-radius: 14px; background: var(--card-background-color, #263041); }
    .empty { padding: 20px; text-align: center; color: var(--secondary-text-color, #8a94a3); }
  `;

  customElements.define("vigil-card", VigilCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "vigil-card",
    name: "Vigil",
    description: "The Vigil alarm for a tablet: state, modes, keypad and sensors, following the profile of the tablet.",
  });
})();
