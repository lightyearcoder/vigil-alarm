"""The repository is publishable: links in the docs point at real files, metadata is filled in."""

from __future__ import annotations

import json
import pathlib
import re
from urllib.parse import parse_qs, unquote, urlparse

ROOT = pathlib.Path(__file__).parents[1]
DOCS = [ROOT / "README.md", ROOT / "docs" / "user-guide.md", ROOT / "docs" / "user-guide.nl.md",
        *(ROOT / "docs" / f"{name}.{lang}.md" for name in ("user-guide", "tablet", "troubleshooting") for lang in ("de", "fr", "it", "es")),
        ROOT / "docs" / "installation-and-testing.md", ROOT / "docs" / "installation-and-testing.nl.md",
        ROOT / "docs" / "tablet.md", ROOT / "docs" / "tablet.nl.md"]
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
        assert (ROOT / LINKS[key].split("/blob/main/")[1]).is_file(), lang


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
    assert len(rows) == 10
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
const s = fs.readFileSync(process.argv[1], "utf8");
const i = s.indexOf("const TXT = {");
const end = s.indexOf("\n};\n", i);
const T = eval("(" + s.slice(i + 12, end + 2) + ")");
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
    path = pathlib.Path(__file__).parent.parent / "custom_components" / "vigil_alarm" / "frontend" / "vigil-panel.js"
    out = subprocess.run([node, "-e", script, str(path)], capture_output=True, text=True, check=True).stdout
    result = json.loads(out)
    assert sorted(result["languages"]) == sorted(["nl", "en", "de", "fr", "it", "es"])
    assert result["count"] > 600
    assert result["problems"] == [], result["problems"][:10]
