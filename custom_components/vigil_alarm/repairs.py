"""Repairs: real faults show up under Settings > System > Repairs and go away by themselves.

Only faults that need someone to do something: a sensor that cannot be reached, a battery that is
low, a siren that is unavailable or has lost mains power. Missing settings are not repairs; the
"Ready for use?" card in the panel shows those, so that setting up is not interrupted.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .heartbeat import SIGNAL_HEARTBEAT
from .manager import SIGNAL_EVENT, VigilManager
from .selftest import SIGNAL_SELFTEST

# What the supervisor calls a problem -> the issue text (translation key).
_PROBLEM_KEY = {"battery_low": "battery_low", "unavailable": "siren_unavailable", "on_battery": "siren_on_battery"}


class VigilRepairs:
    def __init__(self, hass: HomeAssistant, manager: VigilManager) -> None:
        self.hass = hass
        self.manager = manager
        self._open: set[str] = set()

    def _wanted(self) -> dict[str, tuple[str, dict[str, str]]]:
        """issue id -> (translation key, placeholders) for everything wrong right now."""
        snap = self.manager.snapshot()
        entry_id = self.manager.entry.entry_id
        wanted: dict[str, tuple[str, dict[str, str]]] = {}
        for name in snap["faults"]:
            wanted[f"{entry_id}_unreachable_{name}"] = ("sensor_unreachable", {"name": name})
        for problem in snap["problems"]:
            key = _PROBLEM_KEY.get(problem["problem"])
            if key:
                placeholders: dict[str, Any] = {"name": problem["name"]}
                if "level" in problem:
                    placeholders["level"] = f"{problem['level']:g}"
                wanted[f"{entry_id}_{problem['problem']}_{problem['name']}"] = (
                    key + ("_level" if key == "battery_low" and "level" in problem else ""),
                    {k: str(v) for k, v in placeholders.items()},
                )
        wanted.update(self.manager.selftest.issues())
        wanted.update(self.manager.heartbeat.issues())
        return wanted

    @callback
    def sync(self, *_: Any) -> None:
        wanted = self._wanted()
        for issue_id, (key, placeholders) in wanted.items():
            ir.async_create_issue(
                self.hass, DOMAIN, issue_id, is_fixable=False, severity=ir.IssueSeverity.WARNING,
                translation_key=key, translation_placeholders=placeholders,
            )
        for issue_id in self._open - set(wanted):
            ir.async_delete_issue(self.hass, DOMAIN, issue_id)
        self._open = set(wanted)

    @callback
    def start(self):
        """Follow the alarm's events; returns the function that stops and removes the issues."""
        entry_id = self.manager.entry.entry_id
        unsubs = [
            async_dispatcher_connect(self.hass, SIGNAL_EVENT.format(entry_id), self.sync),
            async_dispatcher_connect(self.hass, SIGNAL_SELFTEST.format(entry_id), self.sync),
            async_dispatcher_connect(self.hass, SIGNAL_HEARTBEAT.format(entry_id), self.sync),
        ]
        self.sync()

        @callback
        def stop() -> None:
            for unsub in unsubs:
                unsub()
            for issue_id in self._open:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
            self._open = set()

        return stop
