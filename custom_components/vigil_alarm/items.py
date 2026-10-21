"""The parts of an alarm (sensors, groups, rules, users, notifications, sirens) and where they are kept.

They are stored in the options of the config entry, not as Home Assistant config subentries:
Home Assistant lists every subentry under the integration on the Devices & services page, and
all editing happens in the Vigil panel anyway. An item keeps the attribute names of a subentry
(`subentry_id`, `subentry_type`, `title`, `data`) because the rest of the code reads them that way.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import ulid as ulid_util

OPTION_KEY = "items"


@dataclass(frozen=True)
class Item:
    subentry_id: str
    subentry_type: str
    title: str
    data: Mapping[str, Any]


def items_of(entry: Any) -> dict[str, Item]:
    """All items of an entry (or of anything with an `options` mapping), in stored order."""
    stored = (entry.options or {}).get(OPTION_KEY) or {}
    return {
        item_id: Item(item_id, body["type"], body["title"], body.get("data") or {})
        for item_id, body in stored.items()
    }


def new_id() -> str:
    return ulid_util.ulid_now()


def stored(item_type: str, title: str, data: Mapping[str, Any]) -> dict[str, Any]:
    return {"type": item_type, "title": title, "data": dict(data)}


def save_stored(hass: HomeAssistant, entry: ConfigEntry, items: dict[str, dict[str, Any]]) -> None:
    """Write the items; the entry reloads itself because its options changed."""
    hass.config_entries.async_update_entry(entry, options={**entry.options, OPTION_KEY: items})


def stored_items(entry: ConfigEntry) -> dict[str, dict[str, Any]]:
    """A copy of the stored form, to change and give to `save_stored`."""
    return {k: dict(v) for k, v in ((entry.options or {}).get(OPTION_KEY) or {}).items()}


def channel_services(data: Any) -> list[str]:
    """The notify services of a notification channel: the list `services` (0.6.10), or the one `service` an older
    channel was saved with."""
    services = data.get("services")
    if isinstance(services, (list, tuple)):
        return [str(x) for x in services if x]
    single = data.get("service")
    return [str(single)] if single else []
