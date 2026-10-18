"""Shared base classes for the Vigil entities."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .manager import SIGNAL_UPDATE, VigilManager


def alarm_device(manager: VigilManager) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, manager.entry.entry_id)},
        name=manager.entry.title,
        manufacturer="Vigil Alarm",
    )


def _load_english_names() -> dict[str, dict[str, str]]:
    data = json.loads((Path(__file__).parent / "translations" / "en.json").read_text(encoding="utf-8"))
    return {
        platform: {key: item["name"] for key, item in entities.items() if "name" in item}
        for platform, entities in data.get("entity", {}).items()
    }


_ENGLISH_NAMES = _load_english_names()  # at import, which Home Assistant does outside the event loop


class EnglishEntityId:
    """Entity ids end on the English name, whatever language Home Assistant runs in.

    The displayed name stays translated. Without this a Dutch installation would get
    `..._brandalarm` and an English one `..._fire_alarm`, and the documentation, the example
    dashboard and the blueprints could not name the entities.
    """

    @property
    def suggested_object_id(self) -> str | None:
        platform = getattr(getattr(self, "platform_data", None), "domain", None)
        key = getattr(self, "_attr_translation_key", None)
        return _ENGLISH_NAMES.get(platform, {}).get(key) or super().suggested_object_id  # type: ignore[misc]


class VigilEntity(EnglishEntityId, Entity):
    """Updates whenever the manager reports a change."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager: VigilManager) -> None:
        self._manager = manager

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE.format(self._manager.entry.entry_id), self._refresh
            )
        )

    @callback
    def _refresh(self) -> None:
        self.async_write_ha_state()


class VigilSensorEntity(VigilEntity):
    """An entity that belongs to one sensor (and so to the sensor's device)."""

    def __init__(self, manager: VigilManager, sensor_id: str, title: str) -> None:
        super().__init__(manager)
        self._sensor_id = sensor_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{manager.entry.entry_id}_{sensor_id}")},
            name=title,
            via_device=(DOMAIN, manager.entry.entry_id),
        )
