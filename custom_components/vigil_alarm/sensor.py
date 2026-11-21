"""Sensor status sensors and the last-event sensor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import VigilConfigEntry
from .alarm_control_panel import _STATE
from .const import ALL_PARTITIONS, EVENT_TYPES
from .entity import VigilEntity, VigilSensorEntity
from .items import items_of
from .panels import profile_object_id, reader_state_object_id

SENSOR_STATUSES = ["closed", "open", "unavailable", "bypassed", "bypassed_at_arm", "waiting"]


async def async_setup_entry(
    hass: HomeAssistant, entry: VigilConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    manager = entry.runtime_data
    async_add_entities([VigilLastEvent(manager)])
    async_add_entities([VigilPanelProfile(manager, p.subentry_id, p.title) for p in manager.panels.items() if not manager.panels.is_reader(p)])
    async_add_entities([VigilReaderState(manager, p.subentry_id, p.title) for p in manager.panels.items() if manager.panels.is_reader(p)])
    for sub in manager.sensor_items():
        async_add_entities(
            [VigilSensorStatus(manager, sub.subentry_id, sub.title)],
        )


class VigilReaderState(VigilSensorEntity, SensorEntity):
    """The state of the alarm that a tag reader shows with its leds: the partition (or all) of that reader, as Home
    Assistant names it (disarmed, arming, armed_home, ...). The reader finds this sensor from its own device name, so
    which partition it belongs to is set in Vigil, in one place, and not again in the firmware."""

    _attr_has_entity_name = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager, item_id: str, title: str) -> None:
        super().__init__(manager, item_id, title)
        self._attr_unique_id = f"{manager.entry.entry_id}_{item_id}_state"
        self._attr_name = f"{title} state"
        panel = items_of(manager.entry).get(item_id)
        self._object_id = reader_state_object_id(panel.data["panel_id"]) if panel else None

    @property
    def suggested_object_id(self) -> str | None:
        return self._object_id

    @property
    def extra_state_attributes(self) -> dict[str, float | int | None]:
        """The seconds left of an exit or entry delay at the moment this state was written (as the alarm entity has
        them): the reader counts down on its own clock, and flashes faster in the last seconds."""
        panel = items_of(self._manager.entry).get(self._sensor_id)
        if panel is None:
            return {"delay_left": None, "refused": 0}
        pid = self._manager.panels.default_partition(panel)
        ids = list(self._manager.partitions) if pid == ALL_PARTITIONS else [pid]
        ends = [e for e in (self._manager.snapshot(i)["delay_end"] for i in ids) if e]
        left = round(max(0.0, min(ends) - dt_util.utcnow().timestamp()), 1) if ends else None
        # `refused` counts the scans Vigil refused since it started: the reader flashes red when it goes up.
        return {"delay_left": left, "refused": self._manager.tags.refused.get(panel.data["panel_id"], 0)}

    @property
    def native_value(self) -> str | None:
        panel = items_of(self._manager.entry).get(self._sensor_id)
        if panel is None:
            return None
        pid = self._manager.panels.default_partition(panel)
        engine_state = (
            self._manager.combined().ha_state if pid == ALL_PARTITIONS else self._manager.partitions[pid].engine.state
        )
        return str(_STATE[engine_state].value)


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


class VigilPanelProfile(VigilSensorEntity, SensorEntity):
    """What one registered panel may do and show. The panel reads this entity; the value is the profile version.

    The sensor names and the unlocked flag are kept out of the recorder, so they never reach the history.
    The profile never holds a code, a hash or a key."""

    _attr_translation_key = "panel_profile"
    _attr_has_entity_name = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _unrecorded_attributes = frozenset({"sensors", "unlocked", "open_now_text", "open_sensors_text", "faults_text", "last_alarm_text", "bypassed_text", "partitions", "sensors_all", "sensors_always", "partition_list"})

    def __init__(self, manager, item_id: str, title: str) -> None:
        super().__init__(manager, item_id, title)
        self._attr_unique_id = f"{manager.entry.entry_id}_{item_id}_profile"
        self._attr_name = f"{title} profile"
        panel = items_of(manager.entry).get(item_id)
        self._object_id = profile_object_id(panel.data["panel_id"]) if panel else None

    @property
    def suggested_object_id(self) -> str | None:
        """The same entity id whatever the panel is called, so the firmware can find it from its device name."""
        return self._object_id

    @property
    def _panel(self):
        return items_of(self._manager.entry).get(self._sensor_id)

    @property
    def native_value(self) -> int | None:
        panel = self._panel
        return self._manager.panels.profile(panel)["profile_version"] if panel else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        panel = self._panel
        return self._manager.panels.profile(panel) if panel else {}
