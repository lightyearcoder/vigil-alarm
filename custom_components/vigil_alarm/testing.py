"""Practice mode and the walk test: two ways to try the alarm without a real alarm.

Practice mode: for a limited time the alarm works as always (it counts down, it triggers, the panels show it),
but no siren sounds and no message goes out. Everything is in the log, marked as practice. It ends by itself.

Walk test: with the alarm off, you walk along the doors, windows and motion sensors; each one that reacts is
ticked off, live in the panel. Only intrusion sensors take part: those do nothing while the alarm is off. Fire,
gas, water and tamper sensors are always watching, so opening one would start a real alarm; they have their own
test. A sensor that does not react does not stop the test: the list at the end says which ones were missed.

Both live in memory only: after a restart of Home Assistant neither is running.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, callback
from .errors import VigilError
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .const import DOMAIN

if TYPE_CHECKING:
    from .manager import VigilManager

PRACTICE_MINUTES = 30
WALKTEST_MINUTES = 15


def _needs_disarmed(manager: VigilManager, key: str) -> None:
    if not manager.all_disarmed:
        raise VigilError(translation_domain=DOMAIN, translation_key=key)


class Practice:
    def __init__(self, hass: Any, manager: VigilManager) -> None:
        self.hass = hass
        self.manager = manager
        self.until: float | None = None
        self.muted_trigger: dict[str, Any] | None = None  # the alarm that went off while the siren was muted
        self._timer: CALLBACK_TYPE | None = None

    @property
    def active(self) -> bool:
        return self.until is not None

    @callback
    def start(self) -> None:
        if self.active:
            return
        _needs_disarmed(self.manager, "practice_needs_disarmed")
        self.muted_trigger = None
        self.manager.publish("practice_started", minutes=PRACTICE_MINUTES)  # still a normal event
        self.until = dt_util.utcnow().timestamp() + PRACTICE_MINUTES * 60
        self._timer = async_call_later(self.hass, PRACTICE_MINUTES * 60, self._expire)
        self.manager.notify_changed()

    @callback
    def _expire(self, _now: Any) -> None:
        self._timer = None
        self.stop("expired")

    @callback
    def stop(self, reason: str = "manual") -> None:
        if not self.active:
            return
        if self._timer:
            self._timer()
            self._timer = None
        self.until = None
        self.manager.publish("practice_ended", reason=reason)
        # Practice ends while the alarm is still going off (it ran out, or was stopped): from now on it is real,
        # so the siren and the messages that were held back are let through now.
        held, self.muted_trigger = self.muted_trigger, None
        if held is not None and self.manager.any_triggered:
            self.manager.sirens.handle(held)
            self.manager.notifier.handle(held)
        self.manager.notify_changed()

    @callback
    def shutdown(self) -> None:
        if self._timer:
            self._timer()
            self._timer = None
        self.until = None


class WalkTest:
    def __init__(self, hass: Any, manager: VigilManager) -> None:
        self.hass = hass
        self.manager = manager
        self.until: float | None = None
        self.seen: set[str] = set()
        self.last: dict[str, Any] | None = None  # the result of the last walk test
        self._timer: CALLBACK_TYPE | None = None

    @property
    def active(self) -> bool:
        return self.until is not None

    def _sensors(self) -> list[str]:
        """The sensors that take part: the intrusion sensors."""
        return [sid for sid, s in self.manager.config.sensors.items() if s.cls == "intrusion"]

    @callback
    def start(self) -> None:
        if self.active:
            return
        _needs_disarmed(self.manager, "walktest_needs_disarmed")
        if not self._sensors():
            raise VigilError(translation_domain=DOMAIN, translation_key="walktest_no_sensors")
        self.seen = set()
        self.until = dt_util.utcnow().timestamp() + WALKTEST_MINUTES * 60
        self._timer = async_call_later(self.hass, WALKTEST_MINUTES * 60, self._expire)
        self.manager.publish("walktest_started", total=len(self._sensors()))
        self.manager.notify_changed()

    @callback
    def note(self, sensor_id: str, value: str) -> None:
        """A sensor reported a state: an open one is ticked off."""
        if not self.active or value != "open" or sensor_id in self.seen or sensor_id not in self._sensors():
            return
        self.seen.add(sensor_id)
        if len(self.seen) == len(self._sensors()):
            self.stop("done")
        else:
            self.manager.notify_changed()

    @callback
    def _expire(self, _now: Any) -> None:
        self._timer = None
        self.stop("expired")

    @callback
    def stop(self, reason: str = "stopped") -> None:
        if not self.active:
            return
        if self._timer:
            self._timer()
            self._timer = None
        names = self.manager._sensor_name
        missing = [
            {
                "id": sid,
                "name": names.get(sid, sid),
                "reason": "unavailable" if self.manager.sensor_status(sid) == "unavailable" else "no_response",
            }
            for sid in self._sensors()
            if sid not in self.seen
        ]
        total = len(self._sensors())
        self.last = {
            "time": dt_util.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reason": reason,
            "total": total,
            "seen": [names.get(s, s) for s in self._sensors() if s in self.seen],
            "missing": missing,
        }
        self.until = None
        self.seen = set()
        self.manager.publish("walktest_finished", seen=total - len(missing), total=total, reason=reason,
                             missing=[m["name"] for m in missing])
        self.manager.notify_changed()

    @callback
    def shutdown(self) -> None:
        if self._timer:
            self._timer()
            self._timer = None
        self.until = None

    def status(self) -> dict[str, Any]:
        names = self.manager._sensor_name
        return {
            "active": self.active,
            "until": self.until,
            "sensors": [{"id": sid, "name": names.get(sid, sid), "seen": sid in self.seen} for sid in self._sensors()] if self.active else [],
            "last": self.last,
        }
