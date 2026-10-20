// Copies the guides from ../docs into the Starlight content folder and makes them fit the site:
// a title in the front matter instead of the first heading, links between pages that stay inside the site,
// links to files that are not pages (the examples, the README) that go to GitHub, and the images.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { landing } from "./landing.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const site = path.resolve(here, "..");
const repo = path.resolve(site, "..");
const BASE = "/vigil-alarm";
const BLOB = "https://github.com/lightyearcoder/vigil-alarm/blob/main/";
const LANGS = ["nl", "de", "fr", "it", "es"];
const out = path.join(site, "src/content/docs");

fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
fs.mkdirSync(path.join(site, "src/assets"), { recursive: true });
fs.mkdirSync(path.join(site, "public"), { recursive: true });
fs.copyFileSync(path.join(repo, "custom_components/vigil_alarm/brand/icon@2x.png"), path.join(site, "src/assets/logo.png"));
fs.copyFileSync(path.join(repo, "custom_components/vigil_alarm/brand/icon.png"), path.join(site, "public/favicon.png"));
fs.rmSync(path.join(site, "public/images"), { recursive: true, force: true });
fs.cpSync(path.join(repo, "docs/images"), path.join(site, "public/images"), { recursive: true });

const pageUrl = (name, lang) => `${BASE}/${lang === "en" ? "" : lang + "/"}${name}/`;

function fromFile(file) {
  const m = /^(.+?)(?:\.(nl|de|fr|it|es))?\.md$/.exec(file);
  return { name: m[1], lang: m[2] || "en" };
}

// A guide that has no translation in `lang` is read in English (Starlight shows a notice on such a page).
const known = new Set(fs.readdirSync(path.join(repo, "docs")).filter((f) => f.endsWith(".md")));
const pages = new Set([...known, "esphome-panel.md", "changelog.md"]);

function convert(text, lang, name) {
  let title = name;
  const heading = /^# (.+)\n/m.exec(text);
  if (heading) { title = heading[1].trim(); text = text.replace(heading[0], ""); }
  text = text
    // a guide in the docs folder: the same language when it exists, else English
    .replace(/\]\(([a-z-]+)(?:\.(nl|de|fr|it|es))?\.md(#[^)]*)?\)/g, (all, target, tl, hash) => {
      const wanted = tl || (lang === "en" ? "en" : null);
      if (tl) return `](${pageUrl(target, tl)}${hash || ""})`;
      return `](${pageUrl(target, wanted || "en")}${hash || ""})`;
    })
    // images that belong to the guides
    .replace(/\]\(images\//g, `](${BASE}/images/`)
    // the repository's own files: GitHub
    .replace(/\]\(\.\.\/(esphome\/README\.md)(#[^)]*)?\)/g, (a, f, h) => `](${pageUrl("esphome-panel", "en")}${h || ""})`)
    .replace(/\]\(\.\.\/CHANGELOG\.md(#[^)]*)?\)/g, (a, h) => `](${pageUrl("changelog", "en")}${h || ""})`)
    .replace(/\]\(\.\.\/([^)]+)\)/g, (a, p) => `](${BLOB}${p})`);
  return `---\ntitle: ${JSON.stringify(title)}\n---\n\n${text}`;
}

function write(lang, name, body, ext = "md") {
  const dir = lang === "en" ? out : path.join(out, lang);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, name + "." + ext), body);
}

for (const file of known) {
  const { name, lang } = fromFile(file);
  write(lang, name, convert(fs.readFileSync(path.join(repo, "docs", file), "utf8"), lang, name));
}
// The ESPHome README and the changelog are in English only.
write("en", "esphome-panel", convert(
  fs.readFileSync(path.join(repo, "esphome/README.md"), "utf8").replace(/\]\(\.\.\/docs\/images\//g, "](images/"), "en", "esphome-panel"));
write("en", "changelog", convert(fs.readFileSync(path.join(repo, "CHANGELOG.md"), "utf8"), "en", "changelog"));
// The front pages, one per language, come from scripts/landing.mjs.
for (const lang of ["en", ...LANGS]) write(lang, "index", landing(lang, BASE), "mdx");
console.log("synced", fs.readdirSync(out).length, "entries");
