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
from homeassistant.util import dt as dt_util

from . import VigilConfigEntry
from .const import CONF_CODE_HASH, DOMAIN, PRIMARY_PARTITION
from .manager import SIGNAL_UPDATE, VigilManager

_FEATURE = {
    "home": AlarmControlPanelEntityFeature.ARM_HOME,
    "away": AlarmControlPanelEntityFeature.ARM_AWAY,
    "night": AlarmControlPanelEntityFeature.ARM_NIGHT,
    "vacation": AlarmControlPanelEntityFeature.ARM_VACATION,
    "custom": AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS,
}
_ARMED = {
    "armed_home": AlarmControlPanelState.ARMED_HOME,
    "armed_away": AlarmControlPanelState.ARMED_AWAY,
    "armed_night": AlarmControlPanelState.ARMED_NIGHT,
    "armed_vacation": AlarmControlPanelState.ARMED_VACATION,
    "armed_custom": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
}
ALL = "all"
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
    manager = entry.runtime_data
    entities = [VigilAlarmPanel(manager, pid) for pid in manager.partitions]
    if manager.multiple:
        entities.append(VigilAlarmPanel(manager, ALL))  # arms and disarms every partition together
    async_add_entities(entities)


class VigilAlarmPanel(AlarmControlPanelEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "alarm"  # for the translated attribute values (cause, refuse_reason)
    _attr_should_poll = False

    def __init__(self, manager: VigilManager, partition: str = PRIMARY_PARTITION) -> None:
        """One partition, or (`partition` "all") the entity of all partitions together."""
        self._manager = manager
        self._pid = partition
        entry_id = manager.entry.entry_id
        # The first partition keeps the unique id the alarm always had, so an update changes nothing.
        self._attr_unique_id = (
            f"{entry_id}_all" if partition == ALL else entry_id if partition == PRIMARY_PARTITION
            else f"{entry_id}_partition_{partition}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, manager.entry.entry_id)},
            name=manager.entry.title,
            manufacturer="Vigil Alarm",
        )
        features = AlarmControlPanelEntityFeature(0)
        for part in self._parts():
            for mode in part.config.modes:
                features |= _FEATURE[mode]
        self._attr_supported_features = features

    def _parts(self):
        if self._pid == ALL:
            return list(self._manager.partitions.values())
        return [self._manager.partitions[self._pid]]

    @property
    def _arg(self) -> str | None:
        """The `partition` argument for the manager: none for the first partition (what it always was)."""
        return None if self._pid == PRIMARY_PARTITION else self._pid

    @property
    def _arg_all(self) -> str | None:
        return ALL if self._pid == ALL else self._arg

    @property
    def name(self) -> str | None:
        if self._pid == ALL:
            return self._manager.all_name()
        if self._pid == PRIMARY_PARTITION and not self._manager.multiple:
            return None  # one partition: the entity is the alarm itself, named after the device
        return self._manager.partitions[self._pid].name

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
        if self._pid == ALL:
            return _STATE[self._manager.combined().ha_state]
        return _STATE[self._manager.partitions[self._pid].engine.state]

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
        if self._pid == ALL:
            return self._all_attributes()
        snap = self._manager.snapshot(self._arg)
        return {
            "partition": snap["partition"],
            "partition_name": snap["partition_name"],
            "open_now_count": snap["open_now_count"],  # a number: a panel shows "3 open" without naming sensors
            "mode": snap["mode"],  # the armed mode (home, away, night, vacation or custom), or the target while arming
            "practice": self._manager.practice.active,  # no siren and no messages while on
            "changed_via": self._manager.changed_via,  # the panel or device (`changed_by` is the user)
            "cause": snap["cause"],
            "cause_sensor": snap["cause_sensor"],
            "open_sensors": snap["open_sensors"],
            "faults": snap["faults"],
            "technical_alarms": snap["technical_alarms"],
            "bypassed_sensors": snap["bypassed_sensors"],
            "problems": snap["problems"],
            "delay_end": snap["delay_end"],
            # Seconds left at the moment this state was written. Displays count down from this on their own
            # clock, so a clock that is a few seconds off does not show.
            "delay_left": (
                round(max(0.0, snap["delay_end"] - dt_util.utcnow().timestamp()), 1)
                if snap["delay_end"]
                else None
            ),
            "refuse_reason": snap["refuse_reason"],
            # A plain number for displays such as the ESPHome panel. The names of sensors for a panel are in
            # its profile entity, and only while it may show them.
            "problems_count": len(snap["problems"]),
            **self._manager.alarmmemory.attributes(),  # what the last alarm was, and which sensors it passed
        }

    def _all_attributes(self) -> dict[str, Any]:
        combined = self._manager.combined()
        return {
            "status": combined.state,  # the common state, or "mixed" when the partitions differ
            "mixed": combined.mixed,
            "partitions": {
                self._manager.partitions[pid].name: state for pid, state in combined.partitions.items()
            },
            "practice": self._manager.practice.active,
            "changed_via": self._manager.changed_via,
            "problems": self._manager.supervisor.problems(),
            "problems_count": len(self._manager.supervisor.problems()),
        }

    @property
    def _user_id(self) -> str | None:
        """The Home Assistant user behind the call (a tablet is recognised by it), if any."""
        return self._context.user_id if self._context else None

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._manager.async_disarm(code, user_id=self._user_id, partition=self._arg_all)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._manager.async_arm("home", code, user_id=self._user_id, partition=self._arg_all)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._manager.async_arm("away", code, user_id=self._user_id, partition=self._arg_all)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._manager.async_arm("night", code, user_id=self._user_id, partition=self._arg_all)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        await self._manager.async_arm("vacation", code, user_id=self._user_id, partition=self._arg_all)

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        await self._manager.async_arm("custom", code, user_id=self._user_id, partition=self._arg_all)
