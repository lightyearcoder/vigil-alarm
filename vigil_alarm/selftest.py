"""The self-test of the alarm: a quiet daily check and a regular test of the siren.

Daily, by itself and silently: do the notification channels still exist, and can the sirens be
reached? Nothing sounds and nothing is sent unless something is wrong.

Regularly (monthly to start with), the person is reminded on their phone to let the siren sound
briefly. The reminder itself shows that notifications arrive. On a phone with the Home Assistant app
a button in the message sounds the siren. If nobody does, there is a second reminder after a few
days and after a week a repair appears. The siren can also sound by itself, on a chosen time of day,
if the person turns that on; that only shows that the command was carried out, not that it was heard.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_SELFTEST_AUTO,
    CONF_SELFTEST_FROM,
    CONF_SELFTEST_INTERVAL,
    CONF_SELFTEST_SECONDS,
    CONF_SELFTEST_TO,
    DEFAULT_SELFTEST,
    DOMAIN,
    SUBENTRY_NOTIFICATION,
    SUBENTRY_SIREN,
)
from .eventlog import rfc3339
from .items import items_of

if TYPE_CHECKING:
    from .manager import VigilManager

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1
DAY = 86400.0
CHECK_EVERY = DAY
SECOND_REMINDER_AFTER = 3 * DAY
OVERDUE_AFTER = 7 * DAY  # after the test was due
FIRST_RUN_DELAY = 600  # seconds after start
ACTION = "VIGIL_TEST_SIREN"
SIGNAL_SELFTEST = f"{DOMAIN}_selftest_{{}}"  # the repairs follow it; time alone can make a test overdue


class SelfTest:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, manager: VigilManager) -> None:
        self.hass = hass
        self.entry = entry
        self.manager = manager
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.selftest.{entry.entry_id}")
        self.state: dict[str, Any] = {}
        self._unsubs: list[CALLBACK_TYPE] = []
        self._checking = False

    # ------------------------------------------------------------- settings
    def setting(self, key: str) -> Any:
        return self.entry.data.get(key, DEFAULT_SELFTEST[key])

    # ---------------------------------------------------------- life cycle
    async def async_start(self) -> None:
        self.state = await self._store.async_load() or {}
        if "first_seen" not in self.state:
            self.state["first_seen"] = self._now()
            self._save()
        self._unsubs.append(async_call_later(self.hass, FIRST_RUN_DELAY, self._tick))
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(hours=1)))
        self._unsubs.append(self.hass.bus.async_listen("mobile_app_notification_action", self._on_action))

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    async def async_remove(self) -> None:
        await self._store.async_remove()

    @staticmethod
    def _now() -> float:
        return dt_util.utcnow().timestamp()

    def _save(self) -> None:
        self._store.async_delay_save(lambda: self.state, 10)

    # ---------------------------------------------------------------- check
    def check(self) -> list[dict[str, str]]:
        """The quiet check: what is wrong right now. Nothing sounds, nothing is sent."""
        from .editing import notify_services  # here: editing imports the manager, which imports this module

        problems: list[dict[str, str]] = []
        services = set(notify_services(self.hass))
        for item in items_of(self.entry).values():
            if item.subentry_type == SUBENTRY_NOTIFICATION and item.data.get("service") not in services:
                problems.append({"code": "channel_missing", "name": item.title})
            elif item.subentry_type == SUBENTRY_SIREN:
                st = self.hass.states.get(item.data.get("control", ""))
                if st is None or st.state == "unavailable":
                    problems.append({"code": "siren_unavailable", "name": item.title})
        return problems

    async def async_run_check(self) -> None:
        problems = self.check()
        previous = {(p["code"], p["name"]) for p in self.state.get("problems", [])}
        self.state["last_check"] = self._now()
        self.state["problems"] = problems
        self._save()
        self.manager.publish(
            "selftest_checked", result="problems" if problems else "ok", problems=[f"{p['code']}: {p['name']}" for p in problems]
        )
        # A channel that stopped existing is news; a siren that is unreachable is already reported by the supervisor.
        fresh = [p for p in problems if p["code"] == "channel_missing" and (p["code"], p["name"]) not in previous]
        if fresh:
            await self.manager.notifier.async_send_problem(", ".join(p["name"] for p in fresh))

    # ------------------------------------------------------- the siren test
    def due_at(self) -> float | None:
        days = int(self.setting(CONF_SELFTEST_INTERVAL))
        if days <= 0 or not self.manager.sirens.configured:
            return None
        return (self.state.get("last_siren_test") or self.state.get("first_seen") or self._now()) + days * DAY

    def _in_window(self) -> bool:
        hour = dt_util.as_local(dt_util.utcnow()).hour
        return int(self.setting(CONF_SELFTEST_FROM)) <= hour < int(self.setting(CONF_SELFTEST_TO))

    @callback
    def record_siren_test(self, how: str) -> None:
        """The siren was tested (by the person, by a button in a message, or by itself)."""
        self.state["last_siren_test"] = self._now()
        self.state["reminders"] = 0
        self.state["last_reminder"] = None
        self._save()
        self.manager.publish("selftest_siren_tested", how=how)

    async def async_sound(self, how: str) -> int:
        sounded = await self.manager.sirens.async_test(None, float(self.setting(CONF_SELFTEST_SECONDS)))
        if sounded:
            self.record_siren_test(how)
        return sounded

    async def _on_action(self, event: Event) -> None:
        if event.data.get("action") == ACTION and self.manager.engine.state != "triggered":
            await self.async_sound("notification")

    async def _tick(self, _now: datetime | None = None) -> None:
        if self._checking:
            return
        self._checking = True
        try:
            now = self._now()
            if now - float(self.state.get("last_check") or 0) >= CHECK_EVERY:
                await self.async_run_check()
            due = self.due_at()
            if due is None or now < due or not self._in_window():
                return
            if self.setting(CONF_SELFTEST_AUTO):
                if self.manager.engine.state != "triggered":
                    await self.async_sound("auto")
                return
            reminders = int(self.state.get("reminders", 0))
            last = float(self.state.get("last_reminder") or 0)
            if reminders == 0 or (reminders == 1 and now - last >= SECOND_REMINDER_AFTER):
                await self.manager.notifier.async_send_reminder("selftest_reminder" if reminders == 0 else "selftest_reminder_again")
                self.state["reminders"] = reminders + 1
                self.state["last_reminder"] = now
                self._save()
                self.manager.publish("selftest_reminder", number=reminders + 1)
        finally:
            self._checking = False
            async_dispatcher_send(self.hass, SIGNAL_SELFTEST.format(self.entry.entry_id))

    # ------------------------------------------------------------ reporting
    def overdue_days(self) -> int | None:
        due = self.due_at()
        if due is None:
            return None
        late = self._now() - due
        return int((self._now() - (self.state.get("last_siren_test") or self.state.get("first_seen") or self._now())) // DAY) if late >= OVERDUE_AFTER else None

    def status(self) -> dict[str, Any]:
        due = self.due_at()
        iso = lambda ts: rfc3339(ts) if ts else None  # noqa: E731
        return {
            "last_check": iso(self.state.get("last_check")),
            "problems": self.state.get("problems", []),
            "last_siren_test": iso(self.state.get("last_siren_test")),
            "due": iso(due),
            "reminders": int(self.state.get("reminders", 0)),
            "overdue_days": self.overdue_days(),
            "siren": self.manager.sirens.configured,
            "enabled": due is not None,
            "seconds": float(self.setting(CONF_SELFTEST_SECONDS)),
            "auto": bool(self.setting(CONF_SELFTEST_AUTO)),
        }

    def issues(self) -> dict[str, tuple[str, dict[str, str]]]:
        """For the repairs: id -> (text key, placeholders)."""
        entry_id = self.entry.entry_id
        out: dict[str, tuple[str, dict[str, str]]] = {}
        for problem in self.state.get("problems", []):
            if problem["code"] == "channel_missing":
                out[f"{entry_id}_selftest_channel_{problem['name']}"] = ("selftest_channel_missing", {"name": problem["name"]})
        days = self.overdue_days()
        if days is not None:
            out[f"{entry_id}_selftest_overdue"] = ("selftest_overdue", {"days": str(days)})
        return out
