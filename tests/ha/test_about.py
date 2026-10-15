"""The About tab: version, links and release notes."""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.vigil_alarm.about import LINKS, parse_release_notes

from .common import make_entry
from .test_panel import _client, _ws

ROOT = Path(__file__).parents[2]


def test_release_notes_are_newest_first():
    text = (
        "# Changelog\n\n## 0.2.0\n\n- B\n  wrapped\n\n## Unreleased\n\n- U\n\n"
        "## 0.10.0 (later)\n\n- C\n\n## 0.1.0 (first release)\n\n- A\n"
    )
    notes = parse_release_notes(text)
    assert [n["version"] for n in notes] == ["Unreleased", "0.10.0", "0.2.0", "0.1.0"]  # 0.10 is above 0.2
    assert notes[1]["note"] == "later" and notes[2]["items"] == ["B wrapped"]


def test_the_copy_of_the_changelog_in_the_integration_is_the_same():
    # The integration ships without the repository root, so the panel reads its own copy.
    assert (ROOT / "CHANGELOG.md").read_text() == (ROOT / "custom_components/vigil_alarm/CHANGELOG.md").read_text()


def test_the_current_version_has_release_notes():
    manifest = json.loads((ROOT / "custom_components/vigil_alarm/manifest.json").read_text())
    notes = parse_release_notes((ROOT / "custom_components/vigil_alarm/CHANGELOG.md").read_text())
    assert manifest["version"] in [n["version"] for n in notes]


def test_the_links_point_at_the_repository():
    assert all(url.startswith("https://github.com/lightyearcoder/vigil-alarm") for url in LINKS.values())


async def test_the_about_command(hass, hass_ws_client):
    _, client = await _client(hass, hass_ws_client)
    res = await _ws(client, type="vigil_alarm/about")
    info = res["result"]
    manifest = json.loads((ROOT / "custom_components/vigil_alarm/manifest.json").read_text())
    assert info["version"] == manifest["version"]
    assert info["license"] == "GPL-3.0-or-later"
    assert info["notes"][0]["items"]
    assert info["system"]["counts"]["sensor"] > 0
    assert info["system"]["alarm_state"] == "disarmed"
    assert "1234" not in json.dumps(info)  # nothing secret in the details people paste into a bug report
