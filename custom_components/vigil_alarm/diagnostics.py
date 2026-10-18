"""Diagnostics: what a person can attach to a problem report (Settings > Devices & services > Download diagnostics).

Codes, tags and the secrets derived from them never leave Home Assistant, and neither do
the names of people.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import SUBENTRY_USER
from .items import items_of

REDACT = {"code_hash", "code_salt", "duress_hash", "duress_salt", "tags", "code"}
SECRET_SETTINGS = {"heartbeat_url"}


def _clean(data: dict[str, Any]) -> dict[str, Any]:
    return {k: ("**redacted**" if k in REDACT else v) for k, v in data.items()}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    manager = getattr(entry, "runtime_data", None)
    items = [
        {
            "id": item_id,
            "type": item.subentry_type,
            "title": "**redacted**" if item.subentry_type == SUBENTRY_USER else item.title,
            "data": _clean(dict(item.data)),
        }
        for item_id, item in items_of(entry).items()
    ]
    return {
        "settings": {k: ("**redacted**" if k in SECRET_SETTINGS and v else v) for k, v in entry.data.items()},
        "items": items,
        "state": manager.snapshot() if manager is not None else None,
    }
