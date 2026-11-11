/* Vigil Alarm: admin panel, part "lists": methods of VigilPanel. ../vigil-panel.js adds them to the class;
 * the helpers of that file come in as `core`. */
export default function install(core) {
  const { el, fill, iconButton } = core;
  return {
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
        ...(this._multiple() ? [[C.partition, (i) => (i.data.cls === "intrusion" ? this._partitionName(i.data.partition) : t.alwaysOn)]] : []),
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
      case "partition": return [
        [C.name, (i) => i.title],
        [C.modes, (i) => this._optList("modes", i.data.modes)],
        [C.sensors, (i) => this._data.items.sensor.filter((s) => s.data.cls === "intrusion" && (s.data.partition || "main") === i.id).map((s) => s.title).join(", ") || t.none],
        [t.fields.chime_entity, (i) => (i.data.chime_entity ? this._friendly(i.data.chime_entity) : t.none)],
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
        ...(this._multiple() ? [[C.partitions, (i) => this._partitionList(i.data.partitions)]] : []),
      ];
      case "notification": return [
        [C.name, (i) => i.title],
        [C.service, (i) => this._channelServices(i.data).map((x) => (x.includes(".") ? x : `notify.${x}`)).join(", ")],
        [C.categories, (i) => this._optList("categories", i.data.categories)],
        [C.delay, (i) => (i.data.delay ? `${i.data.delay} s` : t.immediately)],
        ...(this._multiple() ? [[C.partitions, (i) => this._partitionList(i.data.partitions)]] : []),
      ];
      case "panel": return [
        [C.name, (i) => i.title],
        [C.panelId, (i) => i.data.panel_id],
        [C.conn, (i) => this._panelBadges(i)],
        [C.allowed, (i) => this._panelLimits(i)],
        ...(this._multiple() ? [[C.partitions, (i) => this._partitionList(i.data.partitions)]] : []),
      ];
      case "siren": return [
        [C.name, (i) => i.title],
        [C.device, (i) => named(i.data.control)],
        [C.causes, (i) => this._optList("causes", i.data.causes)],
        [C.maxdur, (i) => (i.data.max_duration ? `${i.data.max_duration} s` : t.none)],
        ...(this._multiple() ? [[C.partitions, (i) => this._partitionList(i.data.partitions)]] : []),
        [C.status, (i) => {
          const s = state(i.data.control);
          return el("span", { class: "badge " + (s === undefined || s === "unavailable" ? "bad" : "ok"), text: s === undefined ? "?" : this._entityStateText(i.data.control, s) });
        }],
      ];
    }
    return [];
  },

  // The state of an entity in the language Home Assistant is set to (its own translation of "unknown", "on", "idle" ...),
  // else our own words for the common ones, else the state as it is.
  _entityStateText(entityId, raw) {
    const stateObj = this._hass.states[entityId];
    try {
      if (stateObj && typeof this._hass.formatEntityState === "function") return this._hass.formatEntityState(stateObj);
    } catch (err) { /* an older Home Assistant: use our own words */ }
    return (this.t.entityState && this.t.entityState[raw]) || raw;
  },

  // The live state of one register entry, from the subscription.
  _panelLive(item) {
    return ((this._live && this._live.panels) || []).find((p) => p.id === item.id) || null;
  },
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
    if (!item.data.ha_user && !item.data.blocked) out.push(badge(item.has_key ? "ok" : "warn", item.has_key ? P.keyYes : P.keyNo));
    if (live && live.unlocked) out.push(badge("", P.unlocked));
    if (live && live.locked_permanent) out.push(badge("bad", P.lockedPermanent));
    else if (live && live.locked_for > 0) {
      // The end as a time of day: it stays right without the badge having to count down.
      const end = new Date((this._liveAt || Date.now()) + live.locked_for * 1000);
      out.push(badge("warn", fill(P.locked, { n: live.lock_phase || 1, t: end.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) })));
    } else if (live && live.lock_tries > 0) out.push(badge("", fill(P.tries, { n: live.lock_tries, max: live.lock_tries_max })));
    const seen = (live && live.reported) || {};
    // What the panel runs, and what Vigil needs of it: the major number of the firmware is the profile version.
    const wrong = live && seen.profile_supported && live.profile_required && Number(seen.profile_supported) !== live.profile_required;
    if (wrong) out.push(badge("bad", fill(P.fwWrong, { n: live.profile_required })));
    const about = [seen.hardware, seen.firmware ? "v" + seen.firmware : null,
      seen.firmware && live && live.profile_required ? fill(P.fwNeeds, { n: live.profile_required }) : null].filter(Boolean).join(" · ");
    return el("span", { class: "tags" }, out, about ? el("span", { class: "sub", text: about }) : null);
  },
  _panelLimits(item) {
    const P = this.t.panel;
    const d = item.data;
    const modes = d.allowed_modes && d.allowed_modes.length ? this._optList("allowed_modes", d.allowed_modes) : P.all;
    const no = [d.can_disarm === false ? P.noDisarm : null, d.can_bypass === false ? P.noBypass : null, d.can_silence === false ? P.noSilence : null].filter(Boolean);
    return [modes, ...no].join(", ");
  },
  async _panelAction(item, type, doneText) {
    const P = this.t.panel;
    const res = await this._call({ type, subentry_id: item.id });
    if (!res || !res.ok) { this._toast(P.refused); return; }
    if (type === "vigil_alarm/panel_clear_lock" && !res.was_locked) { this._toast(P.nothingLocked); return; }
    this._toast(type === "vigil_alarm/panel_unlock" && res.was_locked ? `${doneText} ${P.lockLifted}` : doneText);
  },

  _table(kind, items, cols, emptyText) {
    const t = this.t;
    const canTest = kind === "notification" || kind === "siren";
    // The tables that come one per partition keep equal columns, so they line up from one partition to the next.
    const even = ["partition", "sensor_group", "sensor", "rule"].includes(kind);
    return items.length
      ? el("div", { class: "tablewrap" }, el("table", { class: even ? "even" : "" },
          el("thead", {}, el("tr", {}, cols.map(([h]) => el("th", { text: h })), el("th", { class: "act" }))),
          el("tbody", {}, items.map((item) => el("tr", { class: "row" },
            cols.map(([h, render]) => el("td", { "data-label": h }, render(item))),
            el("td", { class: "actions" },
              canTest ? iconButton("play", t.testBtn, "", () => this._test(kind, item)) : null,
              kind === "panel" ? iconButton("unlock", t.panel.unlock, "", () => this._panelAction(item, "vigil_alarm/panel_unlock", fill(t.panel.unlockedDone, { s: item.data.unlock_seconds || 60 }))) : null,
              kind === "panel" && !item.data.ha_user ? iconButton("key", t.panel.keyBtn, "", () => this._openKey(item)) : null,
              kind === "panel" ? iconButton("reset", t.panel.clear, "", () => this._panelAction(item, "vigil_alarm/panel_clear_lock", t.panel.cleared)) : null,
              iconButton("edit", t.editBtn, "", () => this._openForm(kind, item)),
              kind === "user" || item.primary ? null : iconButton("copy", t.dup, "", () => this._openForm(kind, item, true)),
              item.primary ? null : iconButton("trash", t.del, "danger", () => this._confirmDelete(item))))))))
      : el("div", { class: "empty", text: emptyText });
  },

  // Sensors and sensor groups, one table per partition. Last come the ones that belong to no partition: the groups
  // for all partitions, and the safety sensors, which watch everywhere.
  _partitionTables(kind) {
    const t = this.t;
    const cols = this._columns(kind).filter(([h]) => h !== t.cols.partition);  // the table says it
    const rows = this._shown(kind);
    // A rule is in the partition of its sensors (they must all be in one).
    const ruleHome = (r) => { const z = this._data.items.sensor.find((x) => x.id === (r.data.sensors || [])[0]); return (z && z.data.partition) || "main"; };
    const mine = kind === "sensor"
      ? (pid) => rows.filter((r) => r.data.cls === "intrusion" && (r.data.partition || "main") === pid)
      : kind === "rule" ? (pid) => rows.filter((r) => ruleHome(r) === pid)
      : (pid) => rows.filter((r) => (r.data.partition || "main") === pid);
    const rest = kind === "sensor" ? rows.filter((r) => r.data.cls !== "intrusion") : [];
    const sections = [
      ...(this._data.partitions || []).map((p) => ({ id: p.id, title: p.name, items: mine(p.id), empty: kind === "sensor" ? t.empty.sensor : kind === "rule" ? t.empty.rule : t.partitions.noGroups })),
      ...(rest.length ? [{ id: "", title: t.alwaysOn, items: rest, empty: t.empty[kind] }] : []),
    ];
    return sections.map((sec) => el("div", { class: "card" },
      el("div", { class: "bar" }, el("h2", { text: sec.title, style: "margin:0 auto 0 0" }),
        el("button", { class: "btn small", text: t.add[kind], onclick: () => this._openForm(kind, null, false,
          kind === "sensor" ? (sec.id ? { partition: sec.id } : { cls: "fire" }) : { partition: sec.id }) })),
      this._table(kind, sec.items, cols, sec.empty),
      kind === "sensor_group" && !sec.items.length
        ? el("button", { class: "btn", text: t.find.createGroups, onclick: async () => {
            const made = await this._call({ type: "vigil_alarm/create_default_groups", partition: sec.id });
            if (made.ok) await this._load();
          } })
        : null));
  },

  _list(kind) {
    const t = this.t;
    const grouped = ["sensor_group", "sensor", "rule"].includes(kind) && this._multiple();
    return el("div", {},
      el("div", { class: "bar" }, el("p", { class: "intro", text: t.intro[kind] }),
        kind === "sensor" ? el("button", { class: "btn", text: t.practice.walkTitle, onclick: () => this._openWalkTest() }) : null,
        kind === "sensor" ? el("button", { class: "btn", text: t.find.button, onclick: () => this._openFind() }) : null,
        grouped ? null : el("button", { class: "btn primary", text: t.add[kind], onclick: () => this._openForm(kind) })),
      kind === "panel" ? el("p", { class: "muted", text: t.panel.hint }) : null,
      grouped ? el("div", {}, this._partitionTables(kind))
        : el("div", { class: "card" }, this._table(kind, this._shown(kind), this._columns(kind), t.empty[kind])),
      kind === "partition" ? el("div", {}, this._coverageCards()) : null);
  },
  };
}
