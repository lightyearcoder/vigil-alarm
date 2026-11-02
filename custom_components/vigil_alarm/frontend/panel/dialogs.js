/* Vigil Alarm: admin panel, part "dialogs": methods of VigilPanel. ../vigil-panel.js adds them to the class;
 * the helpers of that file come in as `core`. */
export default function install(core) {
  const { CONTACT_CLASSES, MOTION_CLASSES, el, fill } = core;
  return {
  // ---- websocket helpers
  async _call(msg) {
    try {
      return await this._hass.callWS(msg);
    } catch (err) {
      return { ok: false, errors: { base: "generic" }, placeholders: { error: (err && err.message) || "" } };
    }
  },

  _toast(text, action = null) {
    const node = el("div", { class: "toast", text });
    if (action) node.append(" ", el("button", { class: "toastbtn", text: action.label, onclick: () => { node.remove(); action.run(); } }));
    this.shadowRoot.append(node);  // not in the root: a reload of the data redraws that and would wipe it
    setTimeout(() => node.remove(), action ? 8000 : 2500);
  },

  // After a change: say so, and offer to undo it (the version before it is the newest one kept).
  _savedToast(text) {
    this._toast(text, { label: this.t.backup.undo, run: async () => {
      const list = await this._call({ type: "vigil_alarm/backups" });
      const latest = list.versions && list.versions[0];
      if (!latest) return;
      const res = await this._call({ type: "vigil_alarm/backup_restore", version_id: latest.id });
      if (res.ok) { this._toast(this.t.backup.restored); await this._load(); } else this._toast(this._errorText("base", res));
    } });
  },

  async _test(kind, item) {
    if (kind === "notification") await this._hass.callService("vigil_alarm", "test_notification", { channel: item.title });
    else await this._hass.callService("vigil_alarm", "test_siren", { siren: item.title, duration: 3 });
    this._toast(this.t.testSent);
  },

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
  },

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
  },

  // The key of an ESPHome panel: made here, shown once, and only a digest is kept.
  _openKey(item) {
    const P = this.t.panel;
    const body = el("div");
    let makeBtn = null, removeBtn = null, shown = false, armed = false;
    const showKey = (res) => {
      const id = String(res.panel_id).replace(/-/g, "_");
      const line = `${id}_key: "${res.key}"`;
      const box = el("textarea", { class: "keybox", readonly: "", rows: "2", spellcheck: "false" });
      box.value = line;
      // Once the key is shown, "New key" stays but needs a second press (it would cancel the key being copied), and
      // "Remove key" goes away.
      armed = false;
      if (removeBtn) removeBtn.hidden = true;
      if (makeBtn) { makeBtn.textContent = P.keyReplace; makeBtn.classList.add("primary"); makeBtn.classList.remove("danger"); }
      shown = true;
      body.replaceChildren(
        el("p", { class: "muted", text: P.keyShown }),
        box,
        el("p", { class: "muted", text: fill(P.keyDevice, { id }) }),
        el("p", { class: "muted", text: P.keyAgain }),
        el("button", { class: "btn", text: P.keyCopy, onclick: async () => {
          try { await navigator.clipboard.writeText(line); this._toast(P.keyCopied); } catch (e) { box.select(); }
        } }));
    };
    const make = async () => {
      const res = await this._call({ type: "vigil_alarm/panel_key", subentry_id: item.id, action: "create" });
      if (!res || !res.ok) { this._toast(P.refused); return; }
      showKey(res);
      this._load();  // the table behind the dialog shows "Key set"; not awaited, the dialog stays as it is
    };
    body.append(el("p", { text: P.keyIntro }), el("p", { class: "muted", text: item.has_key ? P.keyHave + " " + P.keyReplaceWarn : P.keyNone }));
    this._dialog(P.keyTitle + ": " + item.title, [body], (close) => {
      removeBtn = item.has_key ? el("button", { class: "btn danger", text: P.keyRemove, onclick: async () => {
        const res = await this._call({ type: "vigil_alarm/panel_key", subentry_id: item.id, action: "remove" });
        if (!res || !res.ok) { this._toast(P.refused); return; }
        close(); this._toast(P.keyRemoved); await this._load();
      } }) : null;
      makeBtn = el("button", { class: "btn primary", text: item.has_key ? P.keyReplace : P.keyMake, onclick: () => {
        if (shown && !armed) {  // a key is on the screen: ask once more before it is replaced
          armed = true;
          makeBtn.textContent = P.keyReplaceConfirm; makeBtn.classList.remove("primary"); makeBtn.classList.add("danger");
          return;
        }
        make();
      } });
      return [el("button", { class: "btn", text: this.t.close, onclick: close }), removeBtn, makeBtn];
    });
  },

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
  },

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
    ].filter((r) => !r.c.in_use).map((r) => {  // what is already in the list is not offered again
      const intrusion = r.c.cls === "intrusion";
      r.blocked = intrusion && !(r.c.groups || []).length ? f.needsGroup : "";
      r.on = false;  // nothing is ticked at the start: you choose what you want (not the door of the car)
      r.name = r.c.name;
      r.entrance = !!r.c.entrance && intrusion;
      r.nameInput = null;
      r.isNew = newIds.has(r.c.entity_id);
      return r;
    }).sort((x, y) => String(x.name).localeCompare(String(y.name), this._hass.language || undefined, { numeric: true, sensitivity: "base" }));
    let onlyNew = !!opts.onlyNew && newIds.size > 0;
    // With more than one partition the intrusion sensors found go to the partition chosen here (the first at the start).
    let part = "main";
    // The groups of a sensor: what the person ticked in the row (r.manual), otherwise the proposal; only groups of this partition count.
    const groupsOf = (r) => { const ok = new Set(this._groupsFor(part).map((g) => g.id)); return (r.manual || r.c.groups || []).filter((g) => ok.has(g)); };
    const recheck = (r) => { if (r.c.cls !== "intrusion") return; r.blocked = groupsOf(r).length ? "" : f.needsGroup; r.on = r.on && !r.blocked; };
    let showIgnored = false;
    const shown = () => rows.filter((r) => (!onlyNew || r.isNew) && (showIgnored || !r.c.ignored));
    const base = el("div");
    const tableHost = el("div");
    let close = () => {};
    const addBtn = el("button", { class: "btn primary" });
    const count = () => shown().filter((r) => r.on && !r.blocked && !r.c.ignored).length;
    const refresh = () => {
      const n = count();
      addBtn.textContent = fill(f.add, { n });
      addBtn.disabled = n === 0;
    };
    // A tick per sensor group of the chosen partition; it starts at the proposal.
    const groupPicker = (r) => {
      const all = this._groupsFor(part);
      if (!all.length) return t.none;
      const have = new Set(groupsOf(r));
      return el("div", { class: "groupticks" }, all.map((g) => {
        const box = el("input", { type: "checkbox", checked: have.has(g.id), disabled: !!r.c.ignored, "aria-label": g.title });
        box.addEventListener("change", () => {
          if (box.checked) have.add(g.id); else have.delete(g.id);
          r.manual = all.map((x) => x.id).filter((id) => have.has(id));
          recheck(r); build();
        });
        return el("label", { style: "display:block;white-space:nowrap" }, box, " ", g.title);
      }));
    };
    const build = () => {
      const missingGroup = shown().some((r) => r.blocked === f.needsGroup);
      if (!shown().length) { tableHost.replaceChildren(el("div", { class: "empty", text: f.none })); refresh(); return; }
      const table = el("div", { class: "tablewrap" }, el("table", {},
        el("thead", {}, el("tr", {}, el("th", {}), ...["name", "cls", "entrance", "groups", "extra"].map((k) => el("th", { text: f.cols[k] })), el("th", {}))),
        el("tbody", {}, shown().map((r) => {
          const check = el("input", { type: "checkbox", checked: r.on && !r.blocked && !r.c.ignored, disabled: !!r.blocked || !!r.c.ignored, "aria-label": r.name });
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
              r.blocked ? el("span", { class: "badge warn", text: r.blocked }) : null,
              r.c.ignored ? el("span", { class: "badge", text: f.ignored }) : null),
            el("td", { "data-label": f.cols.cls }, this._opt("cls", r.c.cls)),
            el("td", { "data-label": f.cols.entrance }, entrance),
            el("td", { "data-label": f.cols.groups }, r.c.cls === "intrusion" ? groupPicker(r) : t.alwaysOn),
            el("td", { "data-label": f.cols.extra }, extras),
            el("td", { "data-label": "" }, el("button", { class: "btn", text: r.c.ignored ? f.unignore : f.ignore, title: f.ignoreHelp, onclick: async () => {
              const res = await this._call({ type: "vigil_alarm/discover_ignore", entity_ids: [r.c.entity_id], ignore: !r.c.ignored });
              if (!res || !res.ok) return;
              r.c.ignored = !r.c.ignored;
              r.on = false;
              if (!rows.some((x) => x.c.ignored)) showIgnored = false;
              syncIgnored(); build();
            } })));
        }))));
      const makeGroups = el("button", { class: "btn", text: f.createGroups, onclick: async () => {
        const made = await this._call({ type: "vigil_alarm/create_default_groups", partition: part });
        if (made.ok) { close(); await this._load(); this._openFind(); }
      } });
      const groupsHere = this._groupsFor(part);
      const bulk = groupsHere.length && shown().some((r) => r.c.cls === "intrusion")
        ? el("div", { class: "field" }, el("select", { "aria-label": f.setGroup, onchange: (e) => {
            const id = e.target.value;
            if (!id) return;
            shown().filter((r) => r.on && !r.c.ignored && r.c.cls === "intrusion").forEach((r) => { r.manual = [id]; recheck(r); });
            build();
          } }, el("option", { value: "", text: f.setGroup }), ...groupsHere.map((g) => el("option", { value: g.id, text: g.title }))))
        : null;
      tableHost.replaceChildren(...[missingGroup ? el("div", {}, el("p", { class: "intro", text: f.noGroups }), makeGroups) : null, bulk, table].filter(Boolean));
      refresh();
    };
    const setAll = (on) => { shown().forEach((r) => { r.on = on && !r.blocked && !r.c.ignored; }); build(); };
    const ignoredBtn = el("button", { class: "btn" });
    const syncIgnored = () => {
      const n = rows.filter((r) => r.c.ignored).length;
      ignoredBtn.textContent = showIgnored ? f.hideIgnored : fill(f.showIgnored, { n });
      ignoredBtn.style.display = n ? "" : "none";
    };
    ignoredBtn.addEventListener("click", () => { showIgnored = !showIgnored; syncIgnored(); build(); });
    const copy = el("button", { class: "btn", text: f.copy, title: f.copyHelp });
    copy.addEventListener("click", async () => {
      const report = await this._call({ type: "vigil_alarm/discover_report" });
      try { await navigator.clipboard.writeText(JSON.stringify(report.entities || [], null, 1)); this._toast(t.about.copied); }
      catch (err) { this._toast(t.about.copyFailed); }
    });
    const partitionPick = this._multiple()
      ? el("div", { class: "field" }, el("label", { text: t.fields.partition }),
          el("select", { onchange: (e) => {
            part = e.target.value;
            for (const r of rows) { r.manual = null; recheck(r); }  // another partition has other groups: back to the proposal
            build();
          } }, (this._data.partitions || []).map((p) => el("option", { value: p.id, text: p.name }))),
          el("div", { class: "help", text: f.partitionHelp }))
      : null;
    const filterNote = el("p", { class: "muted" });
    const filterBtn = el("button", { class: "btn" });
    const syncFilter = () => {
      filterNote.textContent = onlyNew ? t.newSensors.onlyNew : "";
      filterBtn.textContent = onlyNew ? t.newSensors.showAll : t.newSensors.showNew;
      filterBtn.style.display = newIds.size ? "" : "none";
    };
    filterBtn.addEventListener("click", () => { onlyNew = !onlyNew; syncFilter(); build(); });
    syncFilter();
    syncIgnored();
    build();
    this._dialog(f.title, [el("p", { class: "intro", text: f.intro }), partitionPick, filterNote, base,
      el("div", { class: "bar" }, el("button", { class: "btn", text: f.all, onclick: () => setAll(true) }),
        el("button", { class: "btn", text: f.nothing, onclick: () => setAll(false) }), filterBtn, ignoredBtn, copy),
      tableHost], (closeDialog) => {
      close = closeDialog;
      addBtn.addEventListener("click", async () => {
        const chosen = shown().filter((r) => r.on && !r.blocked && !r.c.ignored);
        const items = chosen.map((r) => {
          const c = r.c;
          const data = { name: (r.name || "").trim() || c.name, entity_id: c.entity_id, cls: c.cls };
          if (c.cls === "intrusion") Object.assign(data, { type: r.entrance ? "delayed" : "instant", sensor_groups: groupsOf(r), at_arm_open: "bypass", ...(this._multiple() ? { partition: part } : {}) });
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
  },

  // The notify services of a channel: the list, or the one service an older channel was saved with.
  _channelServices(data) {
    if (Array.isArray(data.services)) return data.services.filter(Boolean);
    return data.service ? [data.service] : [];
  },

  _openForm(kind, item, copy = false, prefill = null) {
    const t = this.t;
    // Without a second partition the fields about partitions are left out: there is nothing to choose.
    const schema = this._data.forms[kind].filter((f) => !["partition", "partitions", "default_partition"].includes(f.type) || this._multiple());
    const initial = item ? { name: item.title, ...item.data } : {};
    if (item && item.data && item.data.cls === "tamper") initial.tamper_partition = item.data.partition || "all";
    if (kind === "notification") { initial.services = this._channelServices(initial); delete initial.service; }
    if (copy) initial.name = item.title + t.copySuffix;
    if (prefill) Object.assign(initial, prefill);
    const editing = item && !copy;
    const form = this._makeForm(schema, initial, { ctx: kind, kind, partition: prefill && prefill.partition, editing: !!editing, existing: !!item, hasCode: !!(item && item.has_code && editing), hasDuress: !!(item && item.has_duress && editing) });
    const base = el("div");
    this._dialog(editing ? t.edit[kind] : t.add[kind], [base, form.node], (close) => {
      const saveBtn = el("button", { class: "btn primary", text: t.save });
      saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        let msg = { type: "vigil_alarm/save", kind, data: form.values() };
        if (editing) msg.subentry_id = item.id;
        if (item && item.primary) {
          // The first partition is the alarm itself: its name, modes and times are kept with the settings.
          const { name, ...values } = msg.data;
          const kept = {};
          for (const f of this._data.settings_form) if (this._data.entry.data[f.key] !== undefined) kept[f.key] = this._data.entry.data[f.key];
          for (const k of ["trigger_time", "chime_entity", "default_entry_delay"]) if (!(k in values)) delete kept[k];
          msg = { type: "vigil_alarm/save_settings", data: { ...kept, ...values, partition_name: name } };
        }
        const res = await this._call(msg);
        saveBtn.disabled = false;
        if (res.ok) { close(); this._savedToast(t.saved); await this._load(); }
        else {
          if (item && item.primary && res.errors && res.errors.partition_name) res.errors = { ...res.errors, name: res.errors.partition_name };
          form.showErrors(res, base);
        }
      });
      return [el("button", { class: "btn", text: t.cancel, onclick: close }), saveBtn];
    });
  },

  // A new intrusion sensor joins the group meant for its kind (door contact or motion), until the person chooses.
  _suggestGroups(state, opts) {
    if (opts.editing || state.__groups_touched || state.cls !== "intrusion") return false;
    const st = this._hass.states[state.entity_id];
    const deviceClass = st && st.attributes.device_class;
    const kind = CONTACT_CLASSES.includes(deviceClass) ? "contacts" : MOTION_CLASSES.includes(deviceClass) ? "motion" : null;
    if (!kind) return false;
    const ids = this._groupsFor(state.partition).filter((g) => g.data.suggest_for === kind).map((g) => g.id);
    if (!ids.length || JSON.stringify(ids) === JSON.stringify(state.sensor_groups)) return false;
    state.sensor_groups = ids;
    return true;
  },

  _errorText(field, res) {
    const code = res.errors && res.errors[field];
    const t = this.t;
    const text = t.errors[code] || t.errors.generic;
    return fill(text, res.placeholders || {});
  },
  };
}
