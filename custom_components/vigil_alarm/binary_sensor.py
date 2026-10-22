"""'Alarm active' per class, the technical (water) alarm, and per sensor whether it is bypassed."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import VigilConfigEntry
from .entity import VigilEntity, VigilSensorEntity, alarm_device


async def async_setup_entry(
    hass: HomeAssistant, entry: VigilConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    manager = entry.runtime_data
    # Always all of them, so dashboards and automations never point at an entity that is missing.
    entities = [VigilAlarmActive(manager, c) for c in ("intrusion", "fire", "gas", "tamper", "alarm24")]
    entities.append(VigilTechnicalActive(manager))
    for sub in manager.sensor_items():
        if manager.config.sensors[sub.subentry_id].cls in ("fire", "gas"):
            continue  # life safety sensors cannot be bypassed
        entities.append(VigilSensorBypassed(manager, sub.subentry_id, sub.title))
    async_add_entities(entities)


class VigilAlarmActive(VigilEntity, BinarySensorEntity):
    """On while the alarm is triggered with this cause."""

    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, manager, cls: str) -> None:
        super().__init__(manager)
        self._cls = cls
        self._attr_translation_key = f"active_{cls}"
        self._attr_unique_id = f"{manager.entry.entry_id}_active_{cls}"
        self._attr_device_info = alarm_device(manager)

    @property
    def is_on(self) -> bool:
        return any(e.state == "triggered" and e.cause == self._cls for e in self._manager.engines)


class VigilTechnicalActive(VigilEntity, BinarySensorEntity):
    """On while any water sensor reports a problem. Independent of arming."""

    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_translation_key = "technical_alarm"

    def __init__(self, manager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_technical"
        self._attr_device_info = alarm_device(manager)

    @property
    def is_on(self) -> bool:
        return bool(self._manager.engine.snapshot()["technical_alarms"])

    @property
    def extra_state_attributes(self) -> dict[str, list[str]]:
        return {"sensors": self._manager.snapshot()["technical_alarms"]}


class VigilSensorBypassed(VigilSensorEntity, BinarySensorEntity):
    """On = the sensor is bypassed (ignored until the alarm is disarmed). Read only: bypassing is done from the Vigil
    card, a panel or the `vigil_alarm.bypass` service, with a code or as an administrator, never by a switch."""

    _attr_translation_key = "sensor_bypassed"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, manager, sensor_id: str, title: str) -> None:
        super().__init__(manager, sensor_id, title)
        self._attr_unique_id = f"{manager.entry.entry_id}_{sensor_id}_bypassed"

    @property
    def is_on(self) -> bool:
        return self._manager.sensor_is_bypassed(self._sensor_id)
