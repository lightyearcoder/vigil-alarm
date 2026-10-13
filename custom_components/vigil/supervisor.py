"""Self-monitoring of the devices around the alarm.

Watches the battery of sensor sensors and sirens, the availability of sirens and
the power mode of sirens (mains or battery). Problems are published as events
when they start and end, and listed in the `problems` attribute of the alarm.
Sensor availability is not watched here: the core handles it (`supervision_lost`).
The tamper contact of a siren is best added as a tamper sensor.

At startup the current problems are taken over silently (they show up in the
attribute); events follow when something changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event

from .items import items_of
from .const import (
    CONF_BATTERY_ENTITY,
    CONF_BATTERY_THRESHOLD,
    CONF_CONTROL,
    CONF_POWER_BATTERY_VALUE,
    CONF_POWER_ENTITY,
    DEFAULT_BATTERY_THRESHOLD,
    SUBENTRY_SIREN,
    SUBENTRY_SENSOR,
)

if TYPE_CHECKING:
    from .manager import VigilManager

_UNKNOWN = ("unknown", "unavailable")


@dataclass(frozen=True)
class Watch:
    kind: str  # battery | available | power
    name: str
    entity: str
    is_siren: bool
    battery_value: str = "battery"

    @property
    def key(self) -> tuple[str, str]:
        return (self.kind, self.entity)


class Supervisor:
    def __init__(self, hass: HomeAssistant, manager: VigilManager) -> None:
        self.hass = hass
        self.manager = manager
        self.threshold = float(manager.entry.data.get(CONF_BATTERY_THRESHOLD, DEFAULT_BATTERY_THRESHOLD))
        self.watches: list[Watch] = []
        for sub in items_of(manager.entry).values():
            d = sub.data
            if sub.subentry_type == SUBENTRY_SENSOR and d.get(CONF_BATTERY_ENTITY):
                self.watches.append(Watch("battery", sub.title, d[CONF_BATTERY_ENTITY], False))
            elif sub.subentry_type == SUBENTRY_SIREN:
                self.watches.append(Watch("available", sub.title, d[CONF_CONTROL], True))
                if d.get(CONF_BATTERY_ENTITY):
                    self.watches.append(Watch("battery", sub.title, d[CONF_BATTERY_ENTITY], True))
                if d.get(CONF_POWER_ENTITY):
                    self.watches.append(
                        Watch("power", sub.title, d[CONF_POWER_ENTITY], True, d.get(CONF_POWER_BATTERY_VALUE) or "battery")
                    )
        self._problems: dict[tuple[str, str], dict[str, Any]] = {}
        self._unsub: CALLBACK_TYPE | None = None

    # ------------------------------------------------------------ lifecycle

    @callback
    def start(self) -> None:
        for watch in self.watches:
            self._evaluate(watch, silent=True)
        entities = sorted({w.entity for w in self.watches})
        if entities:
            self._unsub = async_track_state_change_event(self.hass, entities, self._changed)

    @callback
    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    # ---------------------------------------------------------------- views

    def problems(self) -> list[dict[str, Any]]:
        return list(self._problems.values())

    # ----------------------------------------------------------- evaluation

    @callback
    def _changed(self, event: Event) -> None:
        entity = event.data["entity_id"]
        for watch in self.watches:
            if watch.entity == entity:
                self._evaluate(watch, silent=False)

    def _judge(self, watch: Watch, state: State | None) -> tuple[bool | None, dict[str, Any]]:
        """Return (problem?, details); problem None means 'cannot tell, keep as is'."""
        if watch.kind == "available":
            return (state is None or state.state == "unavailable"), {}
        if state is None or state.state in _UNKNOWN:
            return None, {}
        if watch.kind == "battery":
            try:
                level = float(state.state)
            except ValueError:
                return None, {}
            return level <= self.threshold, {"level": level}
        return state.state.lower() == watch.battery_value.lower(), {}  # power

    @callback
    def _evaluate(self, watch: Watch, *, silent: bool) -> None:
        problem, details = self._judge(watch, self.hass.states.get(watch.entity))
        if problem is None:
            return
        was = watch.key in self._problems
        if problem == was:
            return
        if problem:
            self._problems[watch.key] = {"name": watch.name, "problem": _PROBLEM[watch.kind], **details}
        else:
            self._problems.pop(watch.key, None)
        async_dispatcher_send(self.hass, f"vigil_update_{self.manager.entry.entry_id}")
        if not silent:
            event_type, fields = _EVENT[(watch.kind, problem)]
            data = {("siren" if watch.is_siren and "siren" in event_type else "name"): watch.name}
            data.update(details)
            self.manager.publish(event_type, **data)


_PROBLEM = {"battery": "battery_low", "available": "unavailable", "power": "on_battery"}
_EVENT: dict[tuple[str, bool], tuple[str, dict[str, Any]]] = {
    ("battery", True): ("battery_low", {}),
    ("battery", False): ("battery_ok", {}),
    ("available", True): ("siren_unavailable", {}),
    ("available", False): ("siren_available", {}),
    ("power", True): ("siren_power_lost", {}),
    ("power", False): ("siren_power_restored", {}),
}
