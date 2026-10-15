"""The alarm control panel entity."""

from __future__ import annotations

from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import VigilConfigEntry
from .const import CONF_CODE_HASH, DOMAIN
from .manager import SIGNAL_UPDATE, VigilManager

_FEATURE = {
    "home": AlarmControlPanelEntityFeature.ARM_HOME,
    "away": AlarmControlPanelEntityFeature.ARM_AWAY,
    "night": AlarmControlPanelEntityFeature.ARM_NIGHT,
}
_ARMED = {
    "armed_home": AlarmControlPanelState.ARMED_HOME,
    "armed_away": AlarmControlPanelState.ARMED_AWAY,
    "armed_night": AlarmControlPanelState.ARMED_NIGHT,
}
_STATE = {
    "disarmed": AlarmControlPanelState.DISARMED,
    "arming": AlarmControlPanelState.ARMING,
    "pending": AlarmControlPanelState.PENDING,
    "triggered": AlarmControlPanelState.TRIGGERED,
    **_ARMED,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: VigilConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([VigilAlarmPanel(entry.runtime_data)])


class VigilAlarmPanel(AlarmControlPanelEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "alarm"  # for the translated attribute values (cause, refuse_reason)
    _attr_should_poll = False

    def __init__(self, manager: VigilManager) -> None:
        self._manager = manager
        self._attr_unique_id = manager.entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, manager.entry.entry_id)},
            name=manager.entry.title,
            manufacturer="Vigil Alarm",
        )
        features = AlarmControlPanelEntityFeature(0)
        for mode in manager.config.modes:
            features |= _FEATURE[mode]
        self._attr_supported_features = features

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE.format(self._manager.entry.entry_id), self._refresh
            )
        )

    @callback
    def _refresh(self) -> None:
        self.async_write_ha_state()

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        return _STATE[self._manager.engine.state]

    @property
    def code_arm_required(self) -> bool:
        return self._manager.code_arm_required

    @property
    def code_format(self) -> CodeFormat | None:
        if not self._manager.users:
            return None
        return CodeFormat.NUMBER if self._manager.numeric_codes else CodeFormat.TEXT

    @property
    def changed_by(self) -> str | None:
        return self._manager.changed_by

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        snap = self._manager.snapshot()
        return {
            "mode": snap["mode"],  # home/away/night: the armed mode, or the target while arming
            "cause": snap["cause"],
            "cause_sensor": snap["cause_sensor"],
            "open_sensors": snap["open_sensors"],
            "faults": snap["faults"],
            "technical_alarms": snap["technical_alarms"],
            "bypassed_sensors": snap["bypassed_sensors"],
            "problems": snap["problems"],
            "delay_end": snap["delay_end"],
            "refuse_reason": snap["refuse_reason"],
            # For displays such as the ESPHome panel, which can only read plain text attributes.
            "open_sensors_text": ", ".join(snap["open_sensors"]),  # open in the current mode
            "open_now_text": ", ".join(snap["open_now"]),  # open at all, whatever the mode
            "faults_text": ", ".join(snap["faults"]),
            "problems_count": len(snap["problems"]),
            "panel_sensors": snap["panel_sensors"],
        }

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._manager.async_disarm(code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._manager.async_arm("home", code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._manager.async_arm("away", code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._manager.async_arm("night", code)
