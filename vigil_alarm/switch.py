"""One bypass switch per sensor that may be bypassed."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import VigilConfigEntry
from .entity import VigilSensorEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: VigilConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    manager = entry.runtime_data
    for sub in manager.sensor_items():
        if manager.config.sensors[sub.subentry_id].cls in ("fire", "gas"):
            continue  # life safety sensors cannot be bypassed
        async_add_entities(
            [VigilBypassSwitch(manager, sub.subentry_id, sub.title)],
        )


class VigilBypassSwitch(VigilSensorEntity, SwitchEntity):
    """On = the sensor is ignored until the alarm is disarmed.

    Switching needs a Home Assistant administrator in the UI. Anyone else (a
    user with only a code, an automation) uses the `vigil_alarm.bypass` service,
    which asks for a code.
    """

    _attr_translation_key = "bypass"

    def __init__(self, manager, sensor_id: str, title: str) -> None:
        super().__init__(manager, sensor_id, title)
        self._attr_unique_id = f"{manager.entry.entry_id}_{sensor_id}_bypass"

    @property
    def is_on(self) -> bool:
        return self._manager.sensor_is_bypassed(self._sensor_id)

    async def _set(self, bypass: bool) -> None:
        manager = self._manager
        is_admin = await manager.async_is_admin(self._context)
        user_id = self._context.user_id if self._context else None
        await manager.async_bypass(self._sensor_id, None, is_admin=is_admin, bypass=bypass, user_id=user_id)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
