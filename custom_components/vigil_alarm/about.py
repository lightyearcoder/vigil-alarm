"""The data for the About tab of the panel: version, links and release notes."""

from __future__ import annotations

import platform
import re
from pathlib import Path
from typing import Any

from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

REPOSITORY = "https://github.com/lightyearcoder/vigil-alarm"
LINKS = {
    "repository": REPOSITORY,
    "manual_nl": f"{REPOSITORY}/blob/main/docs/gebruikershandleiding.nl.md",
    "manual_en": f"{REPOSITORY}/blob/main/docs/user-guide.md",
    "panel_docs": f"{REPOSITORY}/blob/main/esphome/README.md",
    "releases": f"{REPOSITORY}/releases",
    "issues": f"{REPOSITORY}/issues",
    "new_issue": f"{REPOSITORY}/issues/new/choose",
    "license": f"{REPOSITORY}/blob/main/LICENSE",
}
LICENSE = "GPL-3.0-or-later"
AUTHOR = "lightyearcoder"

_CHANGELOG = Path(__file__).parent / "CHANGELOG.md"
_HEADING = re.compile(r"^##\s+(?P<name>\S+)(?:\s+\((?P<note>[^)]*)\))?\s*$")


def _sort_key(version: str) -> tuple[int, tuple[int, ...]]:
    """Unreleased first, then the highest version number."""
    parts = re.findall(r"\d+", version)
    if not parts:
        return (1, ())  # "Unreleased" and anything else without numbers
    return (0, tuple(int(p) for p in parts))


def parse_release_notes(text: str) -> list[dict[str, Any]]:
    """The changelog as [{"version", "note", "items"}], newest first."""
    releases: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading:
            current = {"version": heading["name"], "note": heading["note"] or "", "items": []}
            releases.append(current)
        elif current is not None and line.startswith("- "):
            current["items"].append(line[2:].strip())
        elif current is not None and line.startswith("  ") and current["items"] and line.strip():
            current["items"][-1] += " " + line.strip()  # a wrapped line
    unreleased = [r for r in releases if not re.search(r"\d", r["version"])]
    numbered = [r for r in releases if re.search(r"\d", r["version"])]
    numbered.sort(key=lambda r: _sort_key(r["version"])[1], reverse=True)
    return unreleased + numbered


def release_notes() -> list[dict[str, Any]]:
    try:
        return parse_release_notes(_CHANGELOG.read_text(encoding="utf-8"))
    except OSError:
        return []


async def async_about(hass: HomeAssistant, counts: dict[str, int], alarm_state: str | None) -> dict[str, Any]:
    integration = await async_get_integration(hass, DOMAIN)
    notes = await hass.async_add_executor_job(release_notes)
    return {
        "version": str(integration.version),
        "license": LICENSE,
        "author": AUTHOR,
        "links": LINKS,
        "notes": notes,
        "system": {
            "home_assistant": HA_VERSION,
            "python": platform.python_version(),
            "alarm_state": alarm_state,
            "counts": counts,
        },
    }
