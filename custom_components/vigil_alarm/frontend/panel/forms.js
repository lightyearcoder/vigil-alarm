/* Vigil Alarm: admin panel, part "forms": methods of VigilPanel. ../vigil-panel.js adds them to the class;
 * the helpers of that file come in as `core`. */
export default function install(core) {
  const { TXT, el, panelLanguage } = core;
  return {
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
    // The modes a person or panel may use: nothing stored meant "all", and that is what the form shows now, every mode ticked.
    if (["user", "panel"].includes(opts.ctx) && !(state.allowed_modes || []).length) {
      const field = schema.find((f) => f.key === "allowed_modes");
      if (field) state.allowed_modes = [...field.options];
    }
    if (schema.some((f) => f.type === "partitions")) {
      // The choice is always made: an item from before (nothing chosen meant all) starts with every partition ticked,
      // a new one with none.
      const ids = (this._data.partitions || []).map((x) => x.id);
      state.partitions = opts.existing && !(state.partitions || []).length ? ids : [...(state.partitions || [])];
      if (opts.ctx === "panel") state.default_partition = state.default_partition || (opts.existing ? state.partitions[0] || "" : "");
    }
    if (opts.kind === "settings") {
      for (const f of schema) if (state[f.key] === undefined) state[f.key] = f.type === "number" ? 0 : f.default;
    }
    const label = (f) => t.fields[`${opts.ctx}.${f.key}`] || t.fields[f.key] || (f.key === "tamper_partition" && t.fields.partition) || f.key;
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
          if (f.key === "allowed_modes" && ["user", "panel"].includes(opts.ctx)) {
            // Every mode that can be chosen ticked: stored as "all" (nothing), so a mode added later is allowed too.
            // Nothing ticked is not "all": a mode that does not exist makes Vigil say that one has to be chosen.
            const set = this._modesOfPartitions(state.partitions);
            const shown = set ? f.options.filter((o) => set.has(o)) : f.options;
            const ticked = (v || []).filter((o) => shown.includes(o));
            v = !ticked.length ? ["-"] : ticked.length === shown.length ? [] : ticked;
          }
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
  },

  _field(f, state, labelText, opts, listId, rerender, compact = false) {
    const t = this.t;
    const key = f.key;
    const more = t.helpMore && t.helpMore[key];
    const helpText = (opts && t.help[`${opts.ctx}.${key}`]) || t.help[key] || (key === "tamper_partition" && t.help.partition) || "";
    const help = helpText && !compact
      ? el("div", { class: "help" }, el("span", { text: helpText }),
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
        let have = opts.ctx === "sensor_group" && key === "modes" ? this._partitionModes(state.partition) : null;
        if (!have && key === "allowed_modes" && ["user", "panel"].includes(opts.ctx)) {
          const set = this._modesOfPartitions(state.partitions);
          have = set ? [...set] : null;
        }
        const shown = have ? f.options.filter((o) => have.includes(o)) : f.options;
        // "All" first, as with the partitions: it ticks everything, or clears everything.
        const allText = { allowed_modes: t.partitions.allModes, modes: t.partitions.allModes, causes: t.partitions.allCauses, categories: t.partitions.allCategories }[key];
        const everyone = allText && shown.length > 1 ? el("label", {}, el("input", { type: "checkbox", checked: shown.every((o) => current.has(o)), onchange: (e) => {
          for (const o of shown) { if (e.target.checked) current.add(o); else current.delete(o); }
          state[key] = f.options.filter((x) => current.has(x));
          rerender();
        } }), allText) : null;
        return wrap(el("div", { class: "checks" }, everyone, shown.map((o) => el("label", {},
          el("input", { type: "checkbox", checked: current.has(o), onchange: (e) => {
            if (e.target.checked) current.add(o); else current.delete(o);
            state[key] = f.options.filter((x) => current.has(x));
            rerender();
          } }), this._opt(key, o)))));
      }
      case "sensors": {
        let choices = this._data.items.sensor.filter((z) => z.data.cls === "intrusion" && (z.data.type || "instant") === "instant").sort(this._byName((z) => z.title));
        const homeOf = (z) => z.data.partition || "main";
        const first = choices.find((z) => (state[key] || []).includes(z.id));
        const pid = this._multiple() ? (first ? homeOf(first) : opts.partition) : null;
        if (pid) choices = choices.filter((z) => homeOf(z) === pid);  // a rule stays within one partition
        const current = new Set(state[key] || []);
        return wrap(choices.length
          ? el("div", { class: "checks" }, choices.map((z) => el("label", {},
              el("input", { type: "checkbox", checked: current.has(z.id), onchange: (e) => {
                if (e.target.checked) current.add(z.id); else current.delete(z.id);
                state[key] = choices.map((c) => c.id).filter((id) => current.has(id));
                rerender();
              } }), z.title)))
          : el("div", { class: "muted", text: t.empty.sensor }));
      }
      case "partition": {
        const choices = this._data.partitions || [];
        const options = choices.map((p) => el("option", { value: p.id, selected: (state[key] || "main") === p.id, text: p.name }));
        // a tamper sensor can watch in all partitions: "All partitions" first (that is also what it has when it has none)
        if (key === "tamper_partition") options.unshift(el("option", { value: "all", selected: !state[key] || state[key] === "all", text: t.partitions.allOption }));
        return wrap(el("select", { onchange: (e) => {
          state[key] = e.target.value;
          if (opts.ctx === "sensor" && key === "partition") {  // only the groups of that partition (and of all) can stay
            const ok = new Set(this._groupsFor(state[key]).map((g) => g.id));
            state.sensor_groups = (state.sensor_groups || []).filter((g) => ok.has(g));
          }
          if (opts.ctx === "sensor_group") {  // only the modes that partition has
            const have = this._partitionModes(state[key]);
            if (have) state.modes = (state.modes || []).filter((m) => have.includes(m));
          }
          rerender();
        } }, options));
      }
      case "default_partition": {
        const choices = this._data.partitions || [];
        const chosen = state.partitions && state.partitions.length ? choices.filter((x) => state.partitions.includes(x.id)) : [];
        const options = chosen.map((x) => ({ id: x.id, name: x.name }));
        if (chosen.length > 1) options.push({ id: "all", name: t.partitions.allOption });
        if (!options.some((o) => o.id === state[key])) state[key] = options.length ? options[0].id : "";
        return wrap(el("select", { onchange: (e) => { state[key] = e.target.value; } },
          options.map((o) => el("option", { value: o.id, selected: state[key] === o.id, text: o.name }))));
      }
      case "partitions": {
        const choices = this._data.partitions || [];
        const current = new Set(state[key] || []);
        const everyone = el("label", {}, el("input", { type: "checkbox", checked: choices.length > 0 && current.size === choices.length, onchange: (e) => {
          state[key] = e.target.checked ? choices.map((c) => c.id) : [];
          const set = this._modesOfPartitions(state[key]);
          if (set && state.allowed_modes) state.allowed_modes = state.allowed_modes.filter((m) => set.has(m));
          rerender();
        } }), t.partitions.allOption);
        return wrap(el("div", { class: "checks" }, everyone, choices.map((p) => el("label", {},
          el("input", { type: "checkbox", checked: current.has(p.id), onchange: (e) => {
            if (e.target.checked) current.add(p.id); else current.delete(p.id);
            state[key] = choices.map((c) => c.id).filter((id) => current.has(id));
            const set = this._modesOfPartitions(state[key]);  // only the modes those partitions have can stay
            if (set && state.allowed_modes) state.allowed_modes = state.allowed_modes.filter((m) => set.has(m));
            rerender();
          } }), p.name))));
      }
      case "sensor_groups": {
        const choices = this._groupsFor(state.partition);
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
        const users = [...(this._data.ha_users || [])].sort(this._byName((u) => u.name));
        const select = el("select", { onchange: (e) => { state[key] = e.target.value; } },
          el("option", { value: "", text: "—" }),
          users.map((u) => el("option", { value: u.id, selected: state[key] === u.id, text: u.name })));
        return wrap(select);
      }
      case "notify": {
        // One or more services: several people get the same message from one channel. A service that is not in the
        // list (gone, or a notify group chosen in an older version) stays visible so it can be unticked.
        const services = [...this._data.notify_services];
        for (const s of state[key] || []) if (!services.includes(s)) services.push(s);
        const current = new Set(state[key] || []);
        return wrap(el("div", { class: "checks" }, services.map((s) => el("label", {},
          el("input", { type: "checkbox", checked: current.has(s), onchange: (e) => {
            if (e.target.checked) current.add(s); else current.delete(s);
            state[key] = services.filter((x) => current.has(x));
          } }), s.includes(".") ? s : `notify.${s}`))));
      }
      case "entity": {
        const id = listId(key);
        const options = Object.keys(this._hass.states).filter((e) => f.domains.includes(e.split(".")[0])).sort(this._byName((e) => this._friendly(e)));
        const input = el("input", { type: "text", class: "ent", list: id, value: state[key] || "", autocomplete: "off", placeholder: f.domains.map((d) => d + ".…").join(", "),
          oninput: (e) => { state[key] = e.target.value.trim(); },
          onchange: () => { if (opts.kind === "sensor" && key === "entity_id" && this._suggestGroups(state, opts)) rerender(); } });
        const list = el("datalist", { id }, options.map((e) => el("option", { value: e, label: this._friendly(e) })));
        return wrap(input, list);
      }
    }
    return wrap();
  },
  };
}
