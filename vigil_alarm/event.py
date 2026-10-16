"""The event entity: the public hook for automations."""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import VigilConfigEntry
from .const import DOMAIN, EVENT_TYPES
from .entity import EnglishEntityId
from .manager import SIGNAL_EVENT, VigilManager


async def async_setup_entry(
    hass: HomeAssistant, entry: VigilConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([VigilEvents(entry.runtime_data)])


class VigilEvents(EnglishEntityId, EventEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "alarm_events"
    _attr_event_types = EVENT_TYPES
    _attr_should_poll = False

    def __init__(self, manager: VigilManager) -> None:
        self._manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_events"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, manager.entry.entry_id)}, name=manager.entry.title
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_EVENT.format(self._manager.entry.entry_id), self._on_event
            )
        )
        early, self._manager.early_events = self._manager.early_events, []
        for event in early:  # events from before this entity existed (e.g. a failed restore)
            self._on_event(event)

    @callback
    def _on_event(self, event: dict[str, Any]) -> None:
        data = {k: v for k, v in event.items() if k != "type"}
        self._trigger_event(event["type"], data)
        self.async_write_ha_state()
