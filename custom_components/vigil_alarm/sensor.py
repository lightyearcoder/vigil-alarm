"""Sensor status sensors and the last-event sensor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import VigilConfigEntry
from .const import EVENT_TYPES
from .entity import VigilEntity, VigilSensorEntity

SENSOR_STATUSES = ["closed", "open", "unavailable", "bypassed", "bypassed_at_arm", "waiting"]


async def async_setup_entry(
    hass: HomeAssistant, entry: VigilConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    manager = entry.runtime_data
    async_add_entities([VigilLastEvent(manager)])
    for sub in manager.sensor_items():
        async_add_entities(
            [VigilSensorStatus(manager, sub.subentry_id, sub.title)],
        )


class VigilSensorStatus(VigilSensorEntity, SensorEntity):
    _attr_translation_key = "sensor_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = SENSOR_STATUSES
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager, sensor_id: str, title: str) -> None:
        super().__init__(manager, sensor_id, title)
        self._attr_unique_id = f"{manager.entry.entry_id}_{sensor_id}_status"

    @property
    def native_value(self) -> str:
        return self._manager.sensor_status(self._sensor_id)


class VigilLastEvent(VigilEntity, SensorEntity):
    """The last thing the alarm reported: handy for panels and dashboards."""

    _attr_translation_key = "last_event"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    # The value stays the event type (automations rely on it); Home Assistant shows the translated text.
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = EVENT_TYPES

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_last_event"
        from .entity import alarm_device

        self._attr_device_info = alarm_device(manager)

    @property
    def native_value(self) -> str | None:
        event = self._manager.last_event
        return event["type"] if event else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        event = self._manager.last_event or {}
        return {k: v for k, v in event.items() if k != "type"}
