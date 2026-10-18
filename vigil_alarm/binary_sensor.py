"""'Alarm active' per class, plus the technical (water) alarm."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import VigilConfigEntry
from .entity import VigilEntity, alarm_device


async def async_setup_entry(
    hass: HomeAssistant, entry: VigilConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    manager = entry.runtime_data
    # Always all of them, so dashboards and automations never point at an entity that is missing.
    entities = [VigilAlarmActive(manager, c) for c in ("intrusion", "fire", "gas", "tamper")]
    entities.append(VigilTechnicalActive(manager))
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
        engine = self._manager.engine
        return engine.state == "triggered" and engine.cause == self._cls


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
