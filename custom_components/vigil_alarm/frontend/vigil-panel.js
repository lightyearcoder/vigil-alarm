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
    await Promise.all([TEXTS_READY, PARTS_READY]);
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
      this._liveAt = Date.now();
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
}

// The module can be loaded twice (a refresh, or the panel registered again): a name may be defined only once.
// The rest of the methods of the class is in panel/<part>.js, loaded with the same ?v= fingerprint as this file
// (an update never mixes old parts with a new panel). Like the texts they are not awaited at the top of the module:
// the element has to be defined as soon as this script has loaded; `_start` waits for them before it draws.
const PARTS = ["overview", "lists", "tabs", "dialogs", "forms"];
const CORE = { KINDS, LOGO_URL, el, fill, icon, iconButton, panelLanguage, TXT, CONTACT_CLASSES, MOTION_CLASSES };
const PARTS_READY = Promise.all(PARTS.map(async (name) => {
  const part = (await import(`/vigil_alarm_static/panel/${name}.js${FINGERPRINT}`)).default(CORE);
  Object.defineProperties(VigilPanel.prototype, Object.getOwnPropertyDescriptors(part));
}));

if (!customElements.get("vigil-panel")) customElements.define("vigil-panel", VigilPanel);
