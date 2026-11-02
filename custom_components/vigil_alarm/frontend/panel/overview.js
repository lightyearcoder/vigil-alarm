/* Vigil Alarm: admin panel, part "overview": methods of VigilPanel. ../vigil-panel.js adds them to the class;
 * the helpers of that file come in as `core`. */
export default function install(core) {
  const { KINDS, LOGO_URL, el, fill } = core;
  return {
  // ---- overview
  // One card per partition: what each of its modes watches.
  _coverageCards() {
    const always = this._data.items.sensor.filter((x) => x.data.cls !== "intrusion");
    return [
      ...(this._data.partitions || [{ id: "main", name: "" }]).map((p) => this._coverageCard(p.id)),
      // the safety sensors watch in every mode of every partition: one card of their own, last
      ...(always.length ? [el("div", { class: "card" }, el("h2", { text: this.t.alwaysOn }),
        el("div", { class: "muted", text: always.map((x) => x.title).join(", ") }))] : []),
    ];
  },
  _coverageCard(pid = "main") {
    const t = this.t;
    const item = pid === "main" ? null : this._data.items.partition.find((x) => x.id === pid);
    const modes = (pid === "main" ? this._data.entry.data.modes : item && item.data.modes) || [];
    const C = t.cols;
    const rows = modes.flatMap((mode) => {
      const cover = this._coverage(mode, pid);
      if (!cover.length) {
        return [el("tr", {}, el("td", { text: t.mode[mode] || mode }),
          el("td", { colspan: "2" }, el("span", { class: "badge warn", text: t.coverageNothing })))];
      }
      return cover.map((c, n) => el("tr", {},
        ...(n === 0 ? [el("td", { rowspan: String(cover.length), text: t.mode[mode] || mode })] : []),
        el("td", { text: c.group.title }),
        el("td", { class: "muted", text: c.sensors.length ? c.sensors.map((x) => x.title).join(", ") : fill(t.sensorsCount, { n: 0 }) })));
    });
    const head = el("thead", {}, el("tr", {}, el("th", { text: C.mode }), el("th", { text: C.groups }), el("th", { text: C.sensors })));
    return el("div", { class: "card" }, el("h2", { text: this._partitionName(pid) }),
      el("div", { class: "tablewrap" }, el("table", { class: "even cover" }, head, el("tbody", {}, rows))));
  },

  // The alarm reports armed_home, armed_away, armed_night; the mode is shown next to the state.
  // The colour of a state on the overview: green disarmed, blue armed, amber counting down, red alarm.
  _stateTone(state) {
    if (state === "triggered") return "bad";
    if (state === "arming" || state === "pending") return "warn";
    if (String(state).startsWith("armed")) return "armed";
    return "ok";
  },

  _stateText(live) {
    const key = live.state.startsWith("armed_") ? "armed" : live.state;
    return this.t.state[key] || live.state;
  },

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
        } })), el("button", { class: "btn", text: r.go, onclick: () => this._setTab("notification") }));
      }
      if (f.go === "create_groups") {
        return el("button", { class: "btn", text: r.createGroups, onclick: async () => {
          const res = await this._call({ type: "vigil_alarm/create_default_groups" });
          if (res.ok) { this._toast(r.groupsMade); await this._load(); }
        } });
      }
      return el("button", { class: "btn", text: r.go, onclick: () => this._setTab(f.go) });
    };
    const row = (f) => el("li", { class: "readyrow" },
      el("span", { class: "badge " + (f.level === "problem" ? "bad" : "warn"), text: f.level === "problem" ? r.problem : r.advice }),
      " ", fill(r.text[f.code] || f.code, f.params), " ", go(f));
    return el("div", { class: "card" }, el("h2", { text: r.title }),
      findings.length ? el("button", { class: "btn", text: t.wizard.button, onclick: () => this._openWizard() }) : null,
      findings.length ? el("ul", { class: "plain" }, findings.map(row)) : el("div", { class: "muted", text: r.allGood }));
  },

  _selftestCard() {
    const t = this.t.selftest;
    const st = this._selftest;
    if (!st) return null;
    const when = (iso) => { if (!iso) return t.never; const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleString(); };
    const row = (label, value) => el("tr", {}, el("td", { text: label }), el("td", { text: value }));
    const rows = [row(t.last, when(st.last_check))];
    if (st.siren) rows.push(row(t.lastSiren, when(st.last_siren_test)));
    if (st.siren && st.enabled) rows.push(row(t.next, when(st.due)));
    // What the last start of each siren came to: confirmed on, command sent only, or failed.
    const starts = st.siren_starts || [];
    for (const s of starts) rows.push(row(fill(t.lastStart, { name: s.name }), `${t.startResult[s.result] || s.result} (${when(s.at)})`));
    // The automations that react to the alarm: how many, the last test, what is wrong, and the two test buttons.
    const hd = st.handlers;
    let handlerBlock = null;
    if (hd) {
      const last = hd.last_test;
      const ok = last ? Object.values(last.result).filter((r) => r === "ok").length : 0;
      const total = last ? Object.keys(last.result).length : 0;
      const line = hd.handlers
        ? fill(t.handlersLine, { n: hd.handlers, when: last ? when(new Date(last.at * 1000).toISOString()) : t.never, ok, total })
        : t.handlersNone;
      const test = (quiet) => async () => {
        try {
          await this._hass.callService("vigil_alarm", "test_handlers", { quiet });
          this._toast(quiet ? t.startedQuiet : t.startedReal);
          for (const wait of [5000, 65000]) setTimeout(async () => { await this._load(); this._renderBody(); }, wait);
        } catch (err) { this._toast(String((err && err.message) || err)); }
      };
      handlerBlock = el("div", {},
        el("div", { style: "font-weight:600;margin:14px 0 4px", text: t.handlers }),
        el("div", { class: "muted", text: line }),
        ...(hd.problems || []).map((p) => el("div", { class: "badge bad", text: fill(t.handlerProblem, { name: p.name || p.automation, why: (t.handlerWhy || {})[p.code] || p.code }) })),
        st.handlers_weekly ? el("div", { class: "muted", text: t.handlerWeekly }) : null,
        hd.handlers ? el("button", { class: "btn", style: "margin-top:8px", text: t.testQuiet, disabled: hd.testing, onclick: test(true) }) : null,
        hd.handlers ? el("button", { class: "btn", text: t.testReal, disabled: hd.testing, onclick: test(false) }) : null);
    }
    return el("div", { class: "card" }, el("h2", { text: t.title }),
      el("div", { class: "tablewrap" }, el("table", {}, el("tbody", {}, rows))),
      handlerBlock,
      ...(st.problems || []).map((p) => el("div", { class: "muted", text: fill(t.problems, { name: p.name }) })),
      st.overdue_days != null ? el("div", { class: "badge bad", text: fill(t.overdue, { days: st.overdue_days }) }) : null,
      !st.siren ? el("div", { class: "muted", text: t.noSiren }) : (!st.enabled ? el("div", { class: "muted", text: t.off }) : null),
      st.siren && st.auto ? el("div", { class: "muted", text: t.auto }) : null,
      starts.some((s) => s.result === "sent") ? el("div", { class: "muted", text: t.unconfirmed }) : null,
      st.siren ? el("button", { class: "btn", text: t.test, onclick: async () => {
        try {
          await this._hass.callService("vigil_alarm", "test_siren", { duration: st.seconds });
          this._toast(fill(t.started, { seconds: st.seconds }));
          await this._load();
          this._renderBody();
        } catch (err) { this._toast(String((err && err.message) || err)); }
      } }) : null);
  },

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
  },

  // Why arming is refused now, per sensor, with what can be done about it (the live view says what stops each mode).
  _whyCard() {
    const t = this.t, w = t.why;
    // [label, blockers] per mode; with more than one partition the label says which partition too.
    const found = [];
    const live = this._live || {};
    if (live.partitions) {
      for (const p of Object.values(live.partitions)) {
        for (const [mode, list] of Object.entries(p.blockers || {})) found.push([this._multiple() ? `${p.name}: ${t.mode[mode] || mode}` : (t.mode[mode] || mode), list]);
      }
    } else {
      for (const [mode, list] of Object.entries(live.blockers || {})) found.push([t.mode[mode] || mode, list]);
    }
    const rows = new Map();
    for (const [label, list] of found) {
      for (const b of list) {
        const key = `${b.sensor || ""}|${b.reason}`;
        if (!rows.has(key)) rows.set(key, { ...b, modes: [] });
        rows.get(key).modes.push(label);
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
  },

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
  },
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
      el("p", { class: m.recording ? "badge warn" : "muted", text: when(m.started) + (m.partition_name ? " · " + m.partition_name : "") + " · " + cause + " · " + (m.sensor_name || "—") }),
      status ? el("p", { class: "muted", text: status }) : null,
      el("p", { class: "muted", text: t.pathIntro }),
      rows.length ? el("div", { class: "tablewrap" }, el("table", {},
        el("thead", {}, el("tr", {}, [t.time, t.sensor, t.room, ""].map((x) => el("th", { text: x })))),
        el("tbody", {}, rows))) : el("p", { class: "muted", text: t.empty }),
      m.steps >= 200 ? el("p", { class: "note", text: fill(t.more, { n: 200 }) }) : null,
      m.recording ? null : el("button", { class: "btn", style: "margin-top:12px", text: t.clear, onclick: clear }));
  },

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
  },

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
  },

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
  },

  _wizardNeeded() {
    return (this._ready || []).some((f) => f.level === "problem");
  },

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
  },

  _wizardCard() {
    const t = this.t.wizard;
    if (!this._wizardNeeded() && !this._wizard) return null;
    return el("div", { class: "card" }, el("h2", { text: t.cardTitle }), el("p", { class: "muted", text: t.cardText }),
      el("button", { class: "btn primary", text: this._wizard ? t.resume : t.start, onclick: () => this._openWizard() }));
  },

  _newSensors() { return (this._live && this._live.new_sensors) || []; },

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
  },

  _overview() {
    const t = this.t;
    const live = this._live;
    const problems = live ? live.problems : [];
    const sensors = this._data.items.sensor;
    return el("div", {},
      el("div", { class: "brand" },
        el("img", { src: LOGO_URL, alt: "", width: "48", height: "48" }),
        el("div", {}, el("h2", { text: "Vigil Alarm" }), el("div", { class: "muted", text: t.alarm }))),
      el("div", { class: "grid cols8 ptiles" },
        ...(live && this._multiple() && live.partitions
          ? Object.values(live.partitions).map((p) => el("div", { class: `card ptile ${this._stateTone(p.state)}` },
              el("div", { class: "pname", text: p.name }),
              el("div", { class: "pstate", text: this._stateText(p) }),
              el("div", { class: "muted", text: p.mode ? (t.mode[p.mode] || p.mode) : "\u00a0" })))
          : [el("div", { class: `card ptile single ${this._stateTone(live ? live.state : "")}` },
              el("div", { class: "pstate", text: live ? this._stateText(live) : t.none }),
              el("div", { class: "muted", text: live && live.mode ? (t.mode[live.mode] || live.mode) : "\u00a0" }))])),
      el("div", { class: "grid cols8" },
        ...KINDS.map((k) => el("div", { class: "card", style: "cursor:pointer", onclick: () => this._setTab(k) },
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
      ...this._coverageCards(),
      el("div", { class: "card" }, el("h2", { text: t.sensorsNow }),
        sensors.length
          ? el("div", { class: "tablewrap" }, el("table", {}, el("tbody", {}, sensors.map((z) =>
              el("tr", {}, el("td", { text: z.title }), el("td", {}, this._sensorBadge(z)))))))
          : el("div", { class: "muted", text: t.empty.sensor })));
  },
  };
}
