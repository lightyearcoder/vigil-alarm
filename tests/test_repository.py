"""The repository is publishable: links in the docs point at real files, metadata is filled in."""

from __future__ import annotations

import json
import pathlib
import re

import pytest
from urllib.parse import parse_qs, unquote, urlparse

ROOT = pathlib.Path(__file__).parents[1]
DOCS = [ROOT / "README.md", ROOT / "docs" / "user-guide.md", ROOT / "docs" / "user-guide.nl.md",
        *(ROOT / "docs" / f"{name}.{lang}.md" for name in ("user-guide", "tablet", "troubleshooting") for lang in ("de", "fr", "it", "es")),
        ROOT / "docs" / "installation-and-testing.md", ROOT / "docs" / "installation-and-testing.nl.md",
        ROOT / "docs" / "tablet.md", ROOT / "docs" / "tablet.nl.md",
        ROOT / "docs" / "failure-behaviour.md", ROOT / "docs" / "failure-behaviour.nl.md"]
OWNER_REPO = "lightyearcoder/vigil-alarm"


def test_no_placeholders_are_left():
    for path in [*DOCS, ROOT / "custom_components/vigil_alarm/manifest.json", ROOT / "hacs.json"]:
        assert "YOUR_GITHUB_USERNAME" not in path.read_text(), path


def test_manifest_points_at_the_repository():
    manifest = json.loads((ROOT / "custom_components/vigil_alarm/manifest.json").read_text())
    assert manifest["documentation"] == f"https://github.com/{OWNER_REPO}"
    assert manifest["issue_tracker"] == f"https://github.com/{OWNER_REPO}/issues"
    assert manifest["codeowners"] == ["@lightyearcoder"]
    assert list(manifest)[:2] == ["domain", "name"] and list(manifest)[2:] == sorted(list(manifest)[2:])  # hassfest order
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])


def test_hacs_metadata():
    hacs = json.loads((ROOT / "hacs.json").read_text())
    assert hacs["name"] == "Vigil Alarm" and hacs["homeassistant"] == "2026.2.3"
    for name in ("icon.png", "icon@2x.png"):
        assert (ROOT / "custom_components/vigil_alarm/brand" / name).is_file()


def test_relative_links_point_at_files():
    for path in DOCS:
        text = path.read_text()
        for target in re.findall(r"\]\((?!https?:|#|mailto:)([^)\s]+)\)", text):
            file = target.split("#")[0]
            assert (path.parent / file).exists(), f"{path.name}: {target}"
        for src in re.findall(r'src="(?!https?:)([^"]+)"', text):
            assert (path.parent / src).exists(), f"{path.name}: {src}"


def test_blueprint_import_buttons_match_the_files():
    text = (ROOT / "README.md").read_text()
    urls = re.findall(r"blueprint_url=([^)\s]+)\)", text)
    found = set()
    for url in urls:
        target = unquote(parse_qs(urlparse("https://x/?blueprint_url=" + url).query)["blueprint_url"][0])
        prefix = f"https://github.com/{OWNER_REPO}/blob/main/"
        assert target.startswith(prefix), target
        assert (ROOT / target[len(prefix):]).is_file(), target
        found.add(pathlib.Path(target).name)
    assert found == {p.name for p in (ROOT / "blueprints/automation/vigil_alarm").glob("*.yaml")}


def test_every_event_is_documented_in_the_readme():
    from custom_components.vigil_alarm.const import EVENT_TYPES

    text = (ROOT / "README.md").read_text()
    missing = [e for e in EVENT_TYPES if f"`{e}`" not in text]
    assert not missing, missing


def test_the_guides_cover_the_same_sections():
    en = re.findall(r"^## ", (ROOT / "docs/user-guide.md").read_text(), re.M)
    nl = re.findall(r"^## ", (ROOT / "docs/user-guide.nl.md").read_text(), re.M)
    assert len(en) == len(nl)
    for lang in ("de", "fr", "it", "es"):
        other = re.findall(r"^## ", (ROOT / f"docs/user-guide.{lang}.md").read_text(), re.M)
        assert len(en) == len(other), lang


def test_the_translated_guides_cover_the_same_sections():
    for name in ("tablet", "troubleshooting"):
        base = re.findall(r"^#+ ", (ROOT / f"docs/{name}.md").read_text(), re.M)
        for lang in ("de", "fr", "it", "es"):
            other = re.findall(r"^#+ ", (ROOT / f"docs/{name}.{lang}.md").read_text(), re.M)
            assert len(base) == len(other), (name, lang)


def test_the_about_tab_links_a_guide_in_every_language():
    from custom_components.vigil_alarm.about import LINKS
    from custom_components.vigil_alarm.languages import LANGUAGES

    for lang in LANGUAGES:
        key = "manual_" + lang
        assert key in LINKS, lang
        # the documentation website (GitHub Pages): English at the root, the others in a folder of their own
        expected = "https://lightyearcoder.github.io/vigil-alarm/" + ("" if lang == "en" else lang + "/")
        assert LINKS[key] == expected, lang
    config = (ROOT / "site/astro.config.mjs").read_text()  # the site is built for exactly that address
    assert 'site: "https://lightyearcoder.github.io"' in config and 'base: "/vigil-alarm"' in config


def test_the_vigil_card_is_shipped_and_registered():
    card = (ROOT / "custom_components" / "vigil_alarm" / "frontend" / "vigil-card.js").read_text()
    assert 'customElements.define("vigil-card"' in card and "vigil_alarm/tablet" in card
    panel = (ROOT / "custom_components" / "vigil_alarm" / "panel.py").read_text()
    assert "vigil-card.js" in panel and "add_extra_js_url" in panel  # loaded for every user, not only administrators


def test_the_card_keypad_can_be_used_with_a_real_keyboard():
    """Digits, Backspace, Enter and Escape work while the keypad is open, and a field elsewhere is left alone.
    (`_key` is already the name of the snapshot key in the card: the handler must not use it.)"""
    from pathlib import Path

    js = (Path(__file__).parent.parent / "custom_components" / "vigil_alarm" / "frontend" / "vigil-card.js").read_text()
    assert 'window.addEventListener("keydown", this._onKey)' in js and 'window.removeEventListener("keydown", this._onKey)' in js
    handler = js[js.index("_keyPressed(ev) {"):js.index("    _digit(d) {")]
    for needle in ("this._ui.keypad", "INPUT|TEXTAREA|SELECT", "Backspace", '"Enter"', '"Escape"', "ev.ctrlKey"):
        assert needle in handler, needle
    assert js.count("    _key(") == 0


def _card_source() -> str:
    from pathlib import Path

    return (Path(__file__).parent.parent / "custom_components" / "vigil_alarm" / "frontend" / "vigil-card.js").read_text(encoding="utf-8")


def test_the_card_has_every_text_in_every_language():
    import re

    from custom_components.vigil_alarm.languages import LANGUAGES

    js = _card_source()
    start = js.index("const TEXTS = {")
    block = js[start:js.index("const PROFILE_VERSION")]
    keys = {}
    for lang in LANGUAGES:
        m = re.search(rf"\n    {lang}: \{{\n(.*?)\n    \}},", block, re.S)
        assert m, lang
        keys[lang] = re.findall(r"(?:^|,)\s*(\w+): \"", m.group(1), re.M)
        assert len(keys[lang]) == len(set(keys[lang])), lang
    for lang in LANGUAGES:
        assert set(keys[lang]) == set(keys["en"]), (lang, set(keys[lang]) ^ set(keys["en"]))
    for lang in LANGUAGES:  # {n} and {s} placeholders survive
        m = re.search(rf"\n    {lang}: \{{\n(.*?)\n    \}},", block, re.S).group(1)
        assert "{n}" in m and "{s}" in m, lang


def test_the_card_error_phrases_occur_in_the_translations_of_each_language():
    """The card recognises Home Assistant's own error text by phrase, so each phrase must be in that language's file."""
    import json
    import re
    from pathlib import Path

    from custom_components.vigil_alarm.languages import LANGUAGES

    js = _card_source()
    rows = re.findall(r"\[\[((?:\"[^\"]+\",? ?)+)\], \"(err_\w+)\"\]", js)
    assert len(rows) == 11
    order = ("en", "nl", "de", "fr", "it", "es")
    assert set(order) == set(LANGUAGES)
    texts = {}
    for lang in order:
        data = json.loads((Path(__file__).parent.parent / "custom_components/vigil_alarm/translations" / f"{lang}.json").read_text(encoding="utf-8"))
        texts[lang] = " ".join(v["message"] for v in data["exceptions"].values())
    for phrases, key in rows:
        items = re.findall(r"\"([^\"]+)\"", phrases)
        assert len(items) == 6, key
        for lang, phrase in zip(order, items):
            assert phrase in texts[lang], (key, lang, phrase)
    for lang, phrase in zip(order, ("Arming refused", "Inschakelen geweigerd", "Scharfschalten abgelehnt", "Activation refusée", "Inserimento rifiutato", "Activación rechazada")):
        assert phrase in texts[lang], (lang, phrase)


def test_the_admin_panel_has_every_text_in_every_language():
    """Same keys and the same {placeholders} in all six languages; a missing text would show as `undefined`."""
    import json
    import shutil
    import subprocess

    import pytest

    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    script = r"""
const fs = require("fs");
const dir = process.argv[1];
const T = {};
for (const lang of ["nl", "en", "de", "fr", "it", "es"]) {
  const s = fs.readFileSync(dir + "/texts/" + lang + ".js", "utf8");
  T[lang] = eval("(" + s.slice(s.indexOf("export default") + 14).replace(/;\s*$/, "") + ")");
}
const leaves = (o, p = "", out = {}) => { for (const [k, v] of Object.entries(o)) { const q = p ? p + "." + k : k; if (v && typeof v === "object") leaves(v, q, out); else out[q] = v; } return out; };
const ph = (t) => (String(t).match(/\{\w+\}/g) || []).sort().join(",");
const en = leaves(T.en), problems = [];
for (const lang of ["nl", "de", "fr", "it", "es"]) {
  const x = leaves(T[lang]);
  for (const k of Object.keys(en)) {
    if (!(k in x)) problems.push(lang + " missing " + k);
    else if (typeof x[k] !== "string" || (en[k].trim() && !x[k].trim())) problems.push(lang + " empty " + k);
    else if (ph(x[k]) !== ph(en[k])) problems.push(lang + " placeholders " + k);
  }
  for (const k of Object.keys(x)) if (!(k in en)) problems.push(lang + " extra " + k);
}
console.log(JSON.stringify({ languages: Object.keys(T), count: Object.keys(en).length, problems }));
"""
    path = pathlib.Path(__file__).parent.parent / "custom_components" / "vigil_alarm" / "frontend"
    out = subprocess.run([node, "-e", script, str(path)], capture_output=True, text=True, check=True).stdout
    result = json.loads(out)
    assert sorted(result["languages"]) == sorted(["nl", "en", "de", "fr", "it", "es"])
    assert result["count"] > 600
    assert result["problems"] == [], result["problems"][:10]


def test_the_panel_texts_are_one_file_per_language_and_are_served():
    """The panel imports its texts from texts/<language>.js; each of the six exists, is a plain default export,
    is served from the address the panel imports from, and is part of the fingerprint of the script address."""
    import re

    from custom_components.vigil_alarm import panel as panel_module

    frontend = pathlib.Path(__file__).parent.parent / "custom_components" / "vigil_alarm" / "frontend"
    js = (frontend / "vigil-panel.js").read_text(encoding="utf-8")
    languages = re.search(r"const LANGUAGES = \[([^\]]+)\]", js).group(1)
    languages = re.findall(r'"(\w+)"', languages)
    assert sorted(languages) == ["de", "en", "es", "fr", "it", "nl"]
    assert sorted(p.stem for p in (frontend / "texts").glob("*.js")) == sorted(languages)
    for lang in languages:
        text = (frontend / "texts" / f"{lang}.js").read_text(encoding="utf-8")
        assert "export default {" in text and text.rstrip().endswith("};"), lang
    assert f"`{panel_module.TEXTS_URL}/" in js  # the address the panel imports from is the one that is served
    assert "FINGERPRINT" in js  # and it carries the same ?v= as the panel itself
    digest_before = panel_module._asset_version("x")
    assert digest_before == panel_module._asset_version("x") and digest_before.startswith("x-")


def test_the_panel_script_has_no_texts_of_its_own():
    """All wording lives in texts/; the script only has the loader (a text added to the script would be missed by
    the translation check)."""
    frontend = pathlib.Path(__file__).parent.parent / "custom_components" / "vigil_alarm" / "frontend"
    js = (frontend / "vigil-panel.js").read_text(encoding="utf-8")
    assert js.count("const TXT = {};") == 1 and "TEXTS_READY" in js
    assert len(js.splitlines()) < 2500


def test_every_version_field_says_the_same():
    """pyproject.toml had been left at 0.4.1 while the integration moved on."""
    manifest = json.loads((ROOT / "custom_components/vigil_alarm/manifest.json").read_text())["version"]
    pyproject = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M).group(1)
    assert pyproject == manifest
    assert re.search(rf"^## {re.escape(manifest)}$", (ROOT / "CHANGELOG.md").read_text(), re.M)


def test_the_two_copies_of_the_changelog_are_identical():
    # One in the repository root and one inside the integration (HACS shows that one); they are kept by hand.
    root = (ROOT / "CHANGELOG.md").read_text()
    inside = (ROOT / "custom_components" / "vigil_alarm" / "CHANGELOG.md").read_text()
    assert root == inside


def test_the_logo_of_the_firmware_and_the_icons_are_the_same_logo():
    pil = pytest.importorskip("PIL.Image")
    import importlib.util

    spec = importlib.util.spec_from_file_location("make_logo", ROOT / "tools" / "make_logo.py")
    make_logo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(make_logo)
    brand = ROOT / "custom_components" / "vigil_alarm" / "brand"
    text = (ROOT / "esphome" / "vigil_alarm" / "vigil_logo.h").read_text()
    start = text.index("LOGO_DATA[] = {") + len("LOGO_DATA[] = {")
    data = text[start:text.index("};", start)]
    assert data.split() == make_logo.header(pil.open(brand / "icon.png")).split()
    # the middle of the left edge is the blue of the Home icon as it looks on the panel (#6897E6)
    side = pil.open(brand / "icon.png").convert("RGBA").getpixel((20, 128))[:3]
    assert all(abs(a - b) <= 3 for a, b in zip(side, (104, 151, 230)))
    assert (brand / "icon.png").read_bytes() == (brand / "dark_icon.png").read_bytes()
    assert (brand / "icon@2x.png").read_bytes() == (brand / "dark_icon@2x.png").read_bytes()


def test_the_panel_script_is_usable_the_moment_it_has_loaded():
    # Home Assistant makes the element as soon as the script's load event fires. A top-level await would delay
    # customElements.define() and the panel stayed empty after a reload, so nothing may wait at the top.
    for name in ("vigil-panel.js", "vigil-card.js"):
        text = (ROOT / "custom_components/vigil_alarm/frontend" / name).read_text(encoding="utf-8")
        top_level = [l for l in text.splitlines() if re.match(r"(await\b|(const|let|var)\s[^=]*=\s*await\b)", l)]
        assert top_level == [], f"{name} waits at the top level: {top_level}"
    panel = (ROOT / "custom_components/vigil_alarm/frontend/vigil-panel.js").read_text(encoding="utf-8")
    assert "hasOwnProperty.call(this, name)" in panel  # properties set before the element was defined are set again


def test_the_overview_tiles_have_one_column_per_kind():
    # The partition tiles and the count tiles share the columns of .cols8, one per kind (one row on a wide screen).
    js = (ROOT / "custom_components/vigil_alarm/frontend/vigil-panel.js").read_text(encoding="utf-8")
    kinds = re.search(r"const KINDS = \[([^\]]*)\]", js).group(1)
    assert len(re.findall(r'"[^"]+"', kinds)) == 8
    assert "repeat(8, minmax(0, 1fr))" in js
    assert js.count('class: "grid cols8') == 2  # the partition tiles and the count tiles


def test_the_card_keeps_the_unlock_while_home_assistant_is_still_answering():
    # After the code the list must open, also when the state with `unlocked` arrives a moment later: the card
    # waits for it (max 5 s) instead of going back to the main page and forgetting what it knew.
    card = (ROOT / "custom_components" / "vigil_alarm" / "frontend" / "vigil-card.js").read_text()
    assert "_waitingForUnlock()" in card and "waitUnlock = Date.now()" in card
    assert "!sensorsView && !this._waitingForUnlock()" in card
    assert "if (!this._waitingForUnlock() && (!this._p() || this._p().unlocked === false))" in card


def test_every_tab_of_the_admin_panel_has_an_address_of_its_own():
    # 0.6.10: /vigil_alarm/<tab>, so back and forward switch between tabs (checked in a test browser: click, back, forward,
    # a route from Home Assistant, an unknown tab = overview). Every tab change goes through one function.
    panel = (ROOT / "custom_components" / "vigil_alarm" / "frontend" / "vigil-panel.js").read_text()
    assert "history.pushState(null" in panel and '"location-changed"' in panel and 'addEventListener("popstate"' in panel
    assert "removeEventListener(\"popstate\"" in panel and "set route(route)" in panel
    assert "this._tab = " not in panel.replace("this._tab = tab;", "").replace('this._tab = "overview";', "")


def test_find_sensors_shows_the_title_of_a_sensor_group():
    """A sensor group item has a `title` (not a `name`): the tick in Find sensors must show it."""
    js = (ROOT / "custom_components/vigil_alarm/frontend/vigil-panel.js").read_text(encoding="utf-8")
    start = js.index("const groupPicker")
    block = js[start : js.index("const build = () =>", start)]
    assert "g.title" in block and "g.name" not in block
    assert "text: g.title" in js and "text: g.name" not in js
