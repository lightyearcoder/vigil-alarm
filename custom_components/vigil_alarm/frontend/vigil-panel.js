/* Vigil Alarm: admin panel.
 *
 * A plain web component (no build step). It talks only to the vigil_alarm/* websocket
 * commands, which are admin-only and share their validation with the config
 * flows. All text that comes from the user is added as text nodes, never as HTML.
 */

// The texts live in texts/<language>.js, loaded next to this file with the same ?v= fingerprint, so an
// update never mixes an old text file with a new panel.
const LANGUAGES = ["nl", "en", "de", "fr", "it", "es"];
const FINGERPRINT = new URL(import.meta.url).search;
// Not awaited at the top of the module: Home Assistant makes the element as soon as the script has loaded, and a
// module that waits for its texts would not have defined it yet (the page stayed empty after a reload).
const TXT = {};
const TEXTS_READY = Promise.all(LANGUAGES.map(
  async (lang) => { TXT[lang] = (await import(`/vigil_alarm_static/texts/${lang}.js${FINGERPRINT}`)).default; }
));

// "de-AT", "fr_CA", "es-419" ... -> one of the six languages; English for everything else.
function panelLanguage(code) {
  const l = String(code || "en").toLowerCase().slice(0, 2);
  return TXT[l] ? l : "en";
}

const LOGO_URL = "/vigil_alarm_static/logo.png";

// Small stroke icons (24x24, Lucide style), drawn as SVG without innerHTML.
const ICONS = {
  edit: ["M12 20h9", "M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"],
  copy: ["M9 9h11a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H11a2 2 0 0 1-2-2V9Z", "M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"],
  trash: ["M3 6h18", "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6", "M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2", "M10 11v6", "M14 11v6"],
  play: ["M6 3l14 9-14 9Z"],
  book: ["M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2Z", "M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7Z"],
  github: ["M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4", "M9 18c-4.51 2-5-2-7-2"],
  tag: ["M12 2H2v10l9.29 9.29a1 1 0 0 0 1.42 0l6.58-6.58a1 1 0 0 0 0-1.42Z", "M7 7h.01"],
  alert: ["M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Z", "M12 8v4", "M12 16h.01"],
  unlock: ["M7 11V7a5 5 0 0 1 9.9-1", "M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2Z"],
  eye: ["M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z", "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"],
  reset: ["M3 12a9 9 0 1 0 3-6.7", "M3 4v5h5"],
  tablet: ["M6 2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z", "M12 18h.01"],
  key: ["M21 2l-2 2", "M15.5 7.5l3 3L22 7l-3-3", "M11.4 11.6a5.5 5.5 0 1 1-7.8 7.8 5.5 5.5 0 0 1 7.8-7.8Z", "M11.4 11.6 15.5 7.5"],
  file: ["M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2Z", "M14 2v6h6"],
};

function icon(name) {
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  for (const [k, v] of Object.entries({ viewBox: "0 0 24 24", width: "16", height: "16", fill: "none", stroke: "currentColor",
    "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true", class: "icon" })) svg.setAttribute(k, v);
  for (const d of ICONS[name] || []) {
    const path = document.createElementNS(NS, "path");
    path.setAttribute("d", d);
    svg.append(path);
  }
  return svg;
}

// A button with only an icon; the text is the tooltip and the label for screen readers.
function iconButton(name, label, cls, onclick) {
  return el("button", { class: "btn small icon-only " + (cls || ""), title: label, "aria-label": label, onclick }, icon(name));
}

// Which option list belongs to which field.
const OPTION_GROUP = { modes: "mode", allowed_modes: "mode" };
const CONTACT_CLASSES = ["door", "window", "opening", "garage_door"];
const MOTION_CLASSES = ["motion", "occupancy", "presence", "moving"];
const KINDS = ["partition", "sensor_group", "sensor", "rule", "user", "notification", "siren", "panel"];
const TABS = ["overview", ...KINDS, "log", "settings", "backup", "about"];

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
main.wide { max-width: none; }
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
button.btn.icon-only { padding: 6px 8px; line-height: 0; margin-left: 4px; }
button.btn.icon-only svg { display: block; }
button.btn:disabled { opacity: .5; cursor: default; }
.tablewrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { text-align: left; font-weight: 500; color: var(--secondary-text-color, #727272); padding: 8px 12px; border-bottom: 1px solid var(--divider-color, #e0e0e0); white-space: nowrap; }
td { padding: 10px 12px; border-bottom: 1px solid var(--divider-color, #eee); vertical-align: middle; }
tr.row:hover td { background: var(--secondary-background-color, #f5f5f5); }
td.actions { text-align: right; white-space: nowrap; }
table.even { table-layout: fixed; }
table.even th.act { width: 140px; }
table.even td { overflow-wrap: anywhere; }
table.even.cover td:first-child { width: 160px; }
td .sub { display: block; color: var(--secondary-text-color, #727272); font-size: 12px; }
.empty { padding: 32px 16px; text-align: center; color: var(--secondary-text-color, #727272); }
.badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; background: var(--secondary-background-color, #eee); }
.readyrow { margin-bottom: 10px; line-height: 1.9; }
.badge.ok { background: color-mix(in srgb, var(--success-color, #43a047) 18%, transparent); color: var(--success-color, #2e7d32); }
.badge.warn { background: color-mix(in srgb, var(--warning-color, #ffa600) 22%, transparent); color: var(--warning-color, #b26a00); }
.badge.bad { background: color-mix(in srgb, var(--error-color, #db4437) 18%, transparent); color: var(--error-color, #db4437); }
.tags span { margin-right: 4px; }
.ptile { background: color-mix(in srgb, var(--tone) 12%, var(--card-background-color, #fff));
  --tone: var(--success-color, #43a047); }
.ptile.armed { --tone: var(--primary-color, #03a9f4); }
.ptile.warn { --tone: var(--warning-color, #ffa600); }
.ptile.bad { --tone: var(--error-color, #db4437); }
.ptile .pname { font-size: 14px; color: var(--secondary-text-color, #727272); overflow-wrap: anywhere; }
.ptile .pstate { font-size: 18px; margin: 2px 0; font-weight: 500; color: var(--tone); }
.ptile.single .pstate { font-size: 20px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; margin-bottom: 16px; }
.grid > .card { margin-bottom: 0; }
.grid.ptiles { margin-bottom: 12px; }
/* The partition tiles and the count tiles share one set of columns (one per kind), so they stay lined up. */
.grid.cols8 { grid-template-columns: repeat(8, minmax(0, 1fr)); }
.grid.cols8 > .card { padding: 12px; }
.grid.cols8 > .card h2 { font-size: 13px; overflow-wrap: anywhere; hyphens: auto; }
.grid.cols8 > .ptile.single { grid-column: span 2; }
.grid.cols8 .pstate { font-size: 15px; overflow-wrap: anywhere; }
.grid.cols8 .ptile.single .pstate { font-size: 17px; }
@media (max-width: 1180px) { .grid.cols8 { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
@media (max-width: 560px) { .grid.cols8 { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.keybox { width: 100%; box-sizing: border-box; font-family: monospace; font-size: 13px; padding: 8px; border: 1px solid var(--divider-color, #ccc); border-radius: 8px; background: var(--secondary-background-color, #f4f4f4); color: var(--primary-text-color, #000); resize: none; }
.stat { font-size: 26px; font-weight: 500; overflow-wrap: anywhere; }
.muted { color: var(--secondary-text-color, #727272); font-size: 13px; }
.about th { text-align: left; font-weight: 500; width: 40%; padding: 4px 8px 4px 0; color: var(--secondary-text-color, #727272); }
.about td { padding: 4px 0; }
.card > ul.links { list-style: none; padding: 0; margin: 0; }
.links li { padding: 5px 0; display: flex; align-items: center; gap: 10px; }
.links svg { color: var(--secondary-text-color, #727272); flex: none; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
@media (max-width: 700px) { .cols { grid-template-columns: 1fr; gap: 16px; } }
.brand { display: flex; align-items: center; gap: 16px; margin: 4px 0 16px; }
.brand img { border-radius: 14px; }
.brand h2 { margin: 0 0 2px; }
a { color: var(--primary-color, #03a9f4); }
.release h3 { margin: 16px 0 4px; font-size: 14px; font-weight: 600; }
.release ul, .card > ul { margin: 0; padding-left: 20px; }
.release li, .card > ul li { margin: 3px 0; font-size: 14px; }
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
  width: 100%; box-sizing: border-box; height: 40px; padding: 0 12px; font-size: 15px; line-height: 20px; border-radius: 8px; border: 1px solid var(--divider-color, #bbb);
  background: var(--secondary-background-color, #fff); color: var(--primary-text-color, #212121); font-family: inherit; }
.field.err input, .field.err select { border-color: var(--error-color, #db4437); }
.overlay.top { z-index: 20; }
.dialog.wide { max-width: min(1100px, 96vw); }
.dialog.wide input[type="text"] { min-width: 180px; }
.morelist { margin: 4px 0 8px; padding-left: 20px; }
.morelist li { margin: 8px 0; }
.field .help button.info { flex: none; width: 18px; height: 18px; border-radius: 50%; border: 1px solid var(--secondary-text-color, #727272); background: none; color: var(--secondary-text-color, #727272); font: italic 600 12px/16px serif; cursor: pointer; padding: 0; margin-left: 8px; vertical-align: middle; }
.field .help button.info:hover { color: var(--primary-color, #03a9f4); border-color: var(--primary-color, #03a9f4); }
.field .help { white-space: pre-line; font-size: 12px; color: var(--secondary-text-color, #727272); margin-top: 4px; }
.field .error, .baseerror { font-size: 13px; color: var(--error-color, #db4437); margin-top: 4px; }
.baseerror { padding: 10px 12px; border-radius: 8px; background: color-mix(in srgb, var(--error-color, #db4437) 12%, transparent); margin-bottom: 14px; }
.checks { display: flex; flex-wrap: wrap; gap: 6px 16px; }
.checks label { display: flex; align-items: center; gap: 6px; font-size: 14px; cursor: pointer; }
.inline { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; }
details { margin: 8px 0 14px; border: 1px solid var(--divider-color, #ddd); border-radius: 8px; padding: 8px 12px; }
details summary { cursor: pointer; font-size: 14px; }
details h3 { font-size: 13px; margin: 12px 0 6px; font-weight: 500; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.toastbtn { margin-left: 10px; background: none; border: 0; color: #8ab4f8; font: inherit; font-weight: 600; cursor: pointer; padding: 0; }
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
    // The element can be made before this class is defined; what Home Assistant set on it by then are plain
    // properties that would hide the setters below. Take them off and set them again.
    for (const name of ["hass", "narrow", "panel", "route"]) {
      if (Object.prototype.hasOwnProperty.call(this, name)) {
        const value = this[name];
        delete this[name];
        this[name] = value;
      }
    }
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
  // Home Assistant tells which part of the address is ours ("/vigil_alarm/sensor": prefix and path); that is the tab.
  set route(route) {
    this._route = route;
    this._showTabOfAddress(route && typeof route.path === "string" ? route.path : null);
  }

  // Every tab has an address of its own (/vigil_alarm/sensor), so the browser's back and forward buttons switch
  // between the tabs you looked at.
  _tabOfPath(path) {
    const name = String(path || "").split("/").filter(Boolean).pop();
    return TABS.includes(name) ? name : "overview";
  }
  _basePath() {
    const prefix = this._route && typeof this._route.prefix === "string" && this._route.prefix ? this._route.prefix : "/vigil_alarm";
    return prefix.replace(/\/+$/, "");
  }
  _showTabOfAddress(path) {
    // Back or forward to a page of Home Assistant that is not ours: nothing to do here (the panel is being replaced).
    if (path === null && !location.pathname.startsWith(this._basePath())) return;
    const now = path !== null ? path : location.pathname.slice(this._basePath().length);
    const tab = this._tabOfPath(now);
    if (tab === this._tab) return;
    this._applyTab(tab);
  }
  _applyTab(tab) {
    this._tab = tab;
    if (tab === "log") this._logNode = null;
    if (tab === "about") { this._about = null; this._markVersionSeen(); }
    if (this._root && this._data) { this._renderNav(); this._renderBody(); }
  }
  _setTab(tab) {
    const url = this._basePath() + (tab === "overview" ? "" : "/" + tab);
    if (location.pathname !== url) {
      try {
        history.pushState(null, "", url);
        window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));  // like Home Assistant's own navigation
      } catch (err) { /* no history: the tab still switches */ }
    }
    this._applyTab(tab);
  }

  get t() { return TXT[panelLanguage(this._hass && this._hass.language)]; }

  connectedCallback() {
    this._onPop = () => this._showTabOfAddress(null);
    window.addEventListener("popstate", this._onPop);
    if (this._hass && this._data) this._subscribe();
  }

  disconnectedCallback() {
    window.removeEventListener("popstate", this._onPop);
    if (this._unsub) { this._unsub.then((u) => u && u()).catch(() => {}); this._unsub = null; }
  }

  // ---- loading
  async _start() {
    await TEXTS_READY;
    this.shadowRoot.innerHTML = "";
    this.shadowRoot.append(el("style", { text: CSS }));
    this._root = el("div");
    this.shadowRoot.append(this._root);
    await this._load();
    this._subscribe();
  }

  async _load(retries = 4) {
    try {
      this._data = await this._hass.callWS({ type: "vigil_alarm/get" });
      const ready = await this._call({ type: "vigil_alarm/readiness" });
      this._ready = ready && ready.findings ? ready.findings : [];
      try { this._heartbeat = await this._hass.callWS({ type: "vigil_alarm/heartbeat" }); } catch (err) { this._heartbeat = null; }
      try { this._selftest = await this._hass.callWS({ type: "vigil_alarm/selftest" }); } catch (err) { this._selftest = null; }
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
      if (this._walkUpdate) this._walkUpdate();
    }, { type: "vigil_alarm/subscribe" }).catch(() => null);
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
    // An open dialog stays open when the data is reloaded (the wizard goes on after a save).
    const layer = this._root.querySelector("#layer") || el("div", { id: "layer" });
    this._root.replaceChildren(el("div", { id: "header" }), el("div", { id: "nav" }), el("div", { id: "body" }), layer);
    this._renderHeader();
    this._renderBody();
    if (this._wizardShown) this._openWizard();
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
        text: this._stateText(live) + (live.mode && live.state !== "disarmed" ? " · " + (t.mode[live.mode] || live.mode) : "") }) : null,
      live && live.practice_until ? el("span", { class: "chip alarm", style: "margin-left:8px", text: t.practice.chip }) : null);
    this._q("header").replaceChildren(header);
    this._renderNav();
  }

  // "What's new": a badge on About until the person has looked at it after an update.
  _newVersion() {
    const v = this._data && this._data.version;
    if (!v) return false;
    try {
      const seen = localStorage.getItem("vigil_alarm_seen_version");
      if (seen === null) { localStorage.setItem("vigil_alarm_seen_version", v); return false; }  // first visit: nothing is new
      return seen !== v;
    } catch (err) { return false; }
  }
  _markVersionSeen() {
    try { if (this._data && this._data.version) localStorage.setItem("vigil_alarm_seen_version", this._data.version); } catch (err) { /* private window */ }
  }

  _renderNav() {
    const t = this.t;
    const nav = el("nav", {}, TABS.map((tab) => {
      const count = KINDS.includes(tab) && this._data ? this._shown(tab).length : null;
      const fresh = tab === "about" && this._tab !== "about" && this._newVersion();
      return el("button", { class: tab === this._tab ? "active" : "", onclick: () => this._setTab(tab) },
        t.tabs[tab], count !== null ? el("span", { class: "count", text: `(${count})` }) : null,
        fresh ? el("span", { class: "badge ok", style: "margin-left:6px", text: t.whatsNew }) : null,
        tab === "sensor" && this._newSensors().length ? el("span", { class: "badge warn", style: "margin-left:6px", text: fill(t.newSensors.badge, { n: this._newSensors().length }) }) : null);
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
    else if (this._tab === "log") content = this._logNode || (this._logNode = this._logTab());  // not rebuilt on every live update
    else if (this._tab === "settings") content = this._settings();
    else if (this._tab === "backup") content = this._backupTab();
    else if (this._tab === "about") content = this._aboutTab();
    else content = this._list(this._tab);
    body.replaceChildren(el("main", { class: KINDS.includes(this._tab) || this._tab === "log" ? "wide" : "" }, content));
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
  // The groups a sensor of a partition can use: the groups of that partition.
  _groupsFor(pid) {
    const mine = pid || "main";
    return this._data.items.sensor_group.filter((g) => (g.data.partition || "main") === mine).sort(this._byName((g) => g.title));
  }
  // The modes of a partition (null: not known, so all of them).
  _partitionModes(pid) {
    if (!pid) return null;
    const p = (this._data.partitions || []).find((x) => x.id === pid);
    return p && p.modes && p.modes.length ? p.modes : null;
  }
  // The modes a user or panel can be given: those of the partitions chosen (none chosen: all partitions).
  _modesOfPartitions(list) {
    const parts = this._data.partitions || [];
    const chosen = list && list.length ? parts.filter((p) => list.includes(p.id)) : parts;
    const all = new Set();
    for (const p of chosen) for (const m of (p.modes && p.modes.length ? p.modes : null) || []) all.add(m);
    return all.size ? all : null;
  }
  _groupName(id) {
    const g = this._data.items.sensor_group.find((x) => x.id === id);
    return g ? g.title : id;
  }
  // Sensors that watch in a mode: intrusion sensors through their groups, the other classes always.
  _coverage(mode, pid = "main") {
    const groups = this._data.items.sensor_group.filter((g) => (g.data.modes || []).includes(mode) && (g.data.partition || "main") === pid);
    return groups.map((g) => ({
      group: g,
      sensors: this._data.items.sensor.filter((s) => (s.data.sensor_groups || []).includes(g.id) && (s.data.partition || "main") === pid),
    }));
  }
  _opt(field, value) {
    const group = OPTION_GROUP[field] || field;
    return (this.t.opt[group] && this.t.opt[group][value]) || value;
  }
  _optList(field, list) {
    return (list || []).map((v) => this._opt(field, v)).join(", ") || this.t.none;
  }
  // The battery level of a sensor as a number, or null if it has no (readable) battery sensor.
  // The items of a kind that have a row in the tables. The tamper contact of a sensor is kept as a
  // sensor of its own, but it is edited with the sensor it belongs to.
  // Lists are sorted by name (numbers by value: "Door 2" before "Door 10"), in the language of Home Assistant.
  _byName(key = (x) => x) {
    const lang = (this._hass && this._hass.language) || undefined;
    return (a, b) => String(key(a)).localeCompare(String(key(b)), lang, { numeric: true, sensitivity: "base" });
  }
  // The partitions keep their order (the first is the alarm itself, and the panel shows them in this order); the rest is sorted by name.
  _shown(kind) {
    if (kind === "partition") return this._partitionItems();
    return this._data.items[kind].filter((i) => !(i.data && i.data.companion_of)).sort(this._byName((i) => i.title));
  }
  // The first partition is the alarm itself, so it has no item of its own: a row is made from the settings.
  _partitionItems() {
    const first = ((this._data.partitions || []).find((p) => p.primary)) || { id: "main", name: "" };
    const main = { id: "main", primary: true, title: first.name, has_code: false, data: { ...this._data.entry.data } };
    return [main, ...this._data.items.partition];
  }
  // More than one partition: the forms and tables show which partition something belongs to.
  _multiple() { return ((this._data && this._data.partitions) || []).length > 1; }
  _partitionName(id) {
    const p = ((this._data && this._data.partitions) || []).find((x) => x.id === (id || "main"));
    return p ? p.name : String(id || "");
  }
  _partitionList(ids) {
    return ids && ids.length ? ids.map((x) => this._partitionName(x)).join(", ") : "*";
  }
  _batteryLevel(sensor) {
    const battery = sensor.data.battery_entity && this._hass.states[sensor.data.battery_entity];
    const level = battery ? parseFloat(battery.state) : NaN;
    return isNaN(level) ? null : level;
  }
  _batteryCell(sensor) {
    const level = this._batteryLevel(sensor);
    const flag = sensor.data.battery_entity && this._hass.states[sensor.data.battery_entity];
    if (level === null && flag && (flag.state === "on" || flag.state === "off")) {  // only "battery low", no percentage
      return el("span", { class: flag.state === "on" ? "badge warn" : "badge ok", text: flag.state === "on" ? this.t.batteryLow : this.t.batteryOk });
    }
    if (level === null) return sensor.data.mains_powered && !sensor.data.battery_entity ? this.t.mainsPowered : this.t.none;
    const low = level <= Number(this._data.entry.data.battery_threshold ?? 20);
    return el("span", { class: low ? "badge warn" : "", text: `${level}%` });
  }
  _sensorBadge(sensor, withBattery = true) {
    const t = this.t;
    const status = this._live && this._live.sensors[sensor.id];
    if (!status) return el("span", { class: "badge", text: t.none });
    const cls = status === "closed" ? "ok" : status === "open" ? "bad" : "warn";
    const badge = el("span", { class: `badge ${cls}`, text: t.zstatus[status] || status });
    const level = this._batteryLevel(sensor);
    return withBattery && level !== null ? el("span", {}, badge, el("span", { class: "muted", text: ` 🔋 ${level}%` })) : badge;
  }
  // One sentence per sensor: how it reacts and when it is watching.
  _sensorSummary(sensor) {
    const t = this.t;
    const d = sensor.data;
    if (d.cls !== "intrusion") return fill(t.summary.always, { cls: String(this._opt("cls", d.cls)).toLowerCase() });
    const modes = [...new Set((d.sensor_groups || []).flatMap((gid) => {
      const g = this._data.items.sensor_group.find((x) => x.id === gid);
      return g ? g.data.modes || [] : [];
    }))];
    const order = this._data.entry.data.modes || [];
    modes.sort((a, b) => order.indexOf(a) - order.indexOf(b));
    const list = modes.map((m) => t.mode[m] || m);
    const names = list.length > 1 ? `${list.slice(0, -1).join(", ")} ${t.summary.and} ${list[list.length - 1]}` : list[0];
    const delay = d.entry_delay !== undefined ? d.entry_delay : this._data.entry.data.default_entry_delay;
    const type = d.type === "delayed" ? fill(t.summary.delayed, { s: delay }) : d.type === "follower" ? t.summary.follower : t.summary.instant;
    return names ? fill(t.summary.watching, { type, modes: names }) : fill(t.summary.nowhere, { type });
  }
  _rulesOfSensor(sensorId) {
    return this._data.items.rule.filter((g) => (g.data.sensors || []).includes(sensorId)).map((g) => g.title);
  }

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
  }
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
  }

  // The alarm reports armed_home, armed_away, armed_night; the mode is shown next to the state.
  // The colour of a state on the overview: green disarmed, blue armed, amber counting down, red alarm.
  _stateTone(state) {
    if (state === "triggered") return "bad";
    if (state === "arming" || state === "pending") return "warn";
    if (String(state).startsWith("armed")) return "armed";
    return "ok";
  }

  _stateText(live) {
    const key = live.state.startsWith("armed_") ? "armed" : live.state;
    return this.t.state[key] || live.state;
  }

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
  }

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
  }

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
  }

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
  }

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
  }
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
  }

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
  }

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
  }

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
  }

  _wizardNeeded() {
    return (this._ready || []).some((f) => f.level === "problem");
  }

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
  }

  _wizardCard() {
    const t = this.t.wizard;
    if (!this._wizardNeeded() && !this._wizard) return null;
    return el("div", { class: "card" }, el("h2", { text: t.cardTitle }), el("p", { class: "muted", text: t.cardText }),
      el("button", { class: "btn primary", text: this._wizard ? t.resume : t.start, onclick: () => this._openWizard() }));
  }

  _newSensors() { return (this._live && this._live.new_sensors) || []; }

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
  }

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
  }

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
          return el("span", { class: "badge " + (s === undefined || s === "unavailable" ? "bad" : "ok"), text: s === undefined ? "?" : s });
        }],
      ];
    }
    return [];
  }

  // The live state of one register entry, from the subscription.
  _panelLive(item) {
    return ((this._live && this._live.panels) || []).find((p) => p.id === item.id) || null;
  }
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
    else if (live && live.locked_for > 0) out.push(badge("warn", fill(P.locked, { s: Math.ceil(live.locked_for) })));
    const seen = (live && live.reported) || {};
    const about = [seen.hardware, seen.firmware ? "v" + seen.firmware : null].filter(Boolean).join(" · ");
    return el("span", { class: "tags" }, out, about ? el("span", { class: "sub", text: about }) : null);
  }
  _panelLimits(item) {
    const P = this.t.panel;
    const d = item.data;
    const modes = d.allowed_modes && d.allowed_modes.length ? this._optList("allowed_modes", d.allowed_modes) : P.all;
    const no = [d.can_disarm === false ? P.noDisarm : null, d.can_bypass === false ? P.noBypass : null, d.can_silence === false ? P.noSilence : null].filter(Boolean);
    return [modes, ...no].join(", ");
  }
  async _panelAction(item, type, doneText) {
    const P = this.t.panel;
    const res = await this._call({ type, subentry_id: item.id });
    if (!res || !res.ok) { this._toast(P.refused); return; }
    if (type === "vigil_alarm/panel_clear_lock" && !res.was_locked) { this._toast(P.nothingLocked); return; }
    this._toast(doneText);
  }

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
  }

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
  }

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
  }

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
  }

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
  }

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
  }

  _summaryText(change) {
    const b = this.t.backup;
    const kindOf = { zone: "sensor", group: "rule", sensor_group: "sensor_group", user: "user", notification: "notification", siren: "siren", panel: "panel" };
    const parts = [];
    for (const [type, counts] of Object.entries(change.counts || {})) {
      parts.push(`${this.t.tabs[kindOf[type]] || type}: ` + ["added", "changed", "removed"].filter((a) => counts[a]).map((a) => `${counts[a]} ${b[a]}`).join(", "));
    }
    if ((change.settings || []).length) parts.push(fill(b.settings, { n: change.settings.length }));
    return parts.join(" · ") || b.nothing;
  }

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
  }

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
  }

  // ---- websocket helpers
  async _call(msg) {
    try {
      return await this._hass.callWS(msg);
    } catch (err) {
      return { ok: false, errors: { base: "generic" }, placeholders: { error: (err && err.message) || "" } };
    }
  }

  _toast(text, action = null) {
    const node = el("div", { class: "toast", text });
    if (action) node.append(" ", el("button", { class: "toastbtn", text: action.label, onclick: () => { node.remove(); action.run(); } }));
    this.shadowRoot.append(node);  // not in the root: a reload of the data redraws that and would wipe it
    setTimeout(() => node.remove(), action ? 8000 : 2500);
  }

  // After a change: say so, and offer to undo it (the version before it is the newest one kept).
  _savedToast(text) {
    this._toast(text, { label: this.t.backup.undo, run: async () => {
      const list = await this._call({ type: "vigil_alarm/backups" });
      const latest = list.versions && list.versions[0];
      if (!latest) return;
      const res = await this._call({ type: "vigil_alarm/backup_restore", version_id: latest.id });
      if (res.ok) { this._toast(this.t.backup.restored); await this._load(); } else this._toast(this._errorText("base", res));
    } });
  }

  async _test(kind, item) {
    if (kind === "notification") await this._hass.callService("vigil_alarm", "test_notification", { channel: item.title });
    else await this._hass.callService("vigil_alarm", "test_siren", { siren: item.title, duration: 3 });
    this._toast(this.t.testSent);
  }

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
  }

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
  }

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
  }

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
  }

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
  }

  // The notify services of a channel: the list, or the one service an older channel was saved with.
  _channelServices(data) {
    if (Array.isArray(data.services)) return data.services.filter(Boolean);
    return data.service ? [data.service] : [];
  }

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
  }

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
    if (opts.ctx === "panel") state.device = initial.device || (initial.ha_user ? "account" : "esphome");
    // A panel always has a language: that of the person who is logged in, English if there is no match.
    if (opts.ctx === "panel" && (!opts.editing || !Object.keys(TXT).includes(state.language))) {
      state.language = panelLanguage((this._hass.locale && this._hass.locale.language) || this._hass.language);
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
  }

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
        return wrap(el("div", { class: "checks" }, shown.map((o) => el("label", {},
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
  }
}

// The module can be loaded twice (a refresh, or the panel registered again): a name may be defined only once.
if (!customElements.get("vigil-panel")) customElements.define("vigil-panel", VigilPanel);
