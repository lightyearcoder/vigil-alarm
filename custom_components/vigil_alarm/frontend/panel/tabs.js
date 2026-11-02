/* Vigil Alarm: admin panel, part "tabs": methods of VigilPanel. ../vigil-panel.js adds them to the class;
 * the helpers of that file come in as `core`. */
export default function install(core) {
  const { LOGO_URL, el, fill, icon, iconButton } = core;
  return {
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
            el("thead", {}, el("tr", {}, ["time", "event", "partition", "item", "who", "via", "result"].map((k) => el("th", { text: l.cols[k] })))),
            el("tbody", {}, res.entries.map((e) => el("tr", { class: "row", title: e.detail ? JSON.stringify(e.detail) : "" },
              el("td", { "data-label": l.cols.time, text: when(e.time) }),
              el("td", { "data-label": l.cols.event, text: res.labels[e.event] || e.event }),
              el("td", { "data-label": l.cols.partition, text: e.partition || t.none }),
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
  },

  _settings() {
    const t = this.t;
    const schema = this._data.settings_form;
    const form = this._makeForm(schema, { ...this._data.entry.data }, { ctx: "s", kind: "settings", sections: true });
    const base = el("div");
    const saveBtn = el("button", { class: "btn primary", text: t.save });
    saveBtn.addEventListener("click", async () => {
      saveBtn.disabled = true;
      const res = await this._call({ type: "vigil_alarm/save_settings", data: form.values() });
      saveBtn.disabled = false;
      if (res.ok) { this._savedToast(t.saved); await this._load(); } else form.showErrors(res, base);
    });
    return el("div", {}, base, form.node,
      el("div", { class: "card" }, el("div", { class: "bar" }, saveBtn), el("p", { class: "note", text: t.reloadNote })));
  },

  // ---- backup tab: kept versions, export and import
  _changeNode(change) {
    const b = this.t.backup;
    const kindOf = { zone: "sensor", group: "rule", sensor_group: "sensor_group", user: "user", notification: "notification", siren: "siren", panel: "panel", partition: "partition" };
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
  },

  _summaryText(change) {
    const b = this.t.backup;
    const kindOf = { zone: "sensor", group: "rule", sensor_group: "sensor_group", user: "user", notification: "notification", siren: "siren", panel: "panel" };
    const parts = [];
    for (const [type, counts] of Object.entries(change.counts || {})) {
      parts.push(`${this.t.tabs[kindOf[type]] || type}: ` + ["added", "changed", "removed"].filter((a) => counts[a]).map((a) => `${counts[a]} ${b[a]}`).join(", "));
    }
    if ((change.settings || []).length) parts.push(fill(b.settings, { n: change.settings.length }));
    return parts.join(" · ") || b.nothing;
  },

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
  },

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
    const lang = (this._hass.language || "en").slice(0, 2);
    const nl = lang === "nl";
    const L = info.links;
    const own = L["manual_" + lang] ? lang : "en";  // the guide in the language of the panel, English if there is none
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
    // Three links: the guide on the documentation website (in the language of the panel), the project and the issues.
    const links = [
      ["book", L["manual_" + own], a.manual],
      ["github", L.repository, a.repository],
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
  },
  };
}
