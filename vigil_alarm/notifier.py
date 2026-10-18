"""Sends alarm events to `notify` services.

A channel is a notification item: a notify service, the categories it
wants and, for alarm messages, an optional delay. A delayed channel only sends
if the alarm is still active after the delay, which makes it an escalation
channel (for example a second phone, or a service that rings the phone).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .items import items_of
from .const import (
    CONF_CATEGORIES,
    CONF_DELAY,
    CONF_PRIORITY,
    CONF_SERVICE,
    DEFAULT_CATEGORIES,
    SUBENTRY_NOTIFICATION,
)
from .messages import render, text

if TYPE_CHECKING:
    from .manager import VigilManager

_LOGGER = logging.getLogger(__name__)

# event type -> (category, message key)
EVENT_MESSAGES = {
    "triggered": ("alarm", "triggered"),
    "trigger_cause_changed": ("alarm", "cause_changed"),
    "pending_started": ("pending", "pending"),
    "armed": ("arming", "armed"),
    "disarmed": ("arming", "disarmed"),
    "arm_refused": ("arming", "arm_refused"),
    "supervision_lost": ("fault", "supervision_lost"),
    "supervision_restored": ("fault", "supervision_restored"),
    "sensor_unconfirmed": ("fault", "unconfirmed"),
    "sensor_unconfirmed_escalated": ("fault", "unconfirmed_escalated"),
    "sensor_bypassed_at_arm": ("fault", "bypassed_at_arm"),
    "technical_alarm_started": ("technical", "technical_started"),
    "technical_alarm_ended": ("technical", "technical_ended"),
    "state_restore_failed": ("fault", "restore_failed"),
    "siren_failed": ("fault", "siren_failed"),
    "siren_unavailable": ("fault", "siren_unavailable"),
    "siren_available": ("fault", "siren_available"),
    "siren_power_lost": ("fault", "siren_power_lost"),
    "siren_power_restored": ("fault", "siren_power_restored"),
    "battery_low": ("fault", "battery_low"),
    "battery_ok": ("fault", "battery_ok"),
    "code_locked": ("fault", "code_locked"),
    "code_locked_permanent": ("fault", "code_locked_permanent"),
    "panel_offline": ("fault", "panel_offline"),
    "panel_online": ("fault", "panel_online"),
    "alarm_silenced": ("arming", "silenced"),
    "alarm_acknowledged": ("arming", "acknowledged"),
}
# Events that end an alarm: pending escalations are cancelled.
ENDING = {"disarmed", "trigger_ended"}


@dataclass
class Channel:
    id: str
    name: str
    service: str
    categories: frozenset[str]
    delay: float
    priority: bool


class Notifier:
    def __init__(self, hass: HomeAssistant, manager: VigilManager) -> None:
        self.hass = hass
        self.manager = manager
        self.channels: list[Channel] = []
        for sid, sub in items_of(manager.entry).items():
            if sub.subentry_type != SUBENTRY_NOTIFICATION:
                continue
            d = sub.data
            self.channels.append(
                Channel(
                    sid,
                    sub.title,
                    d[CONF_SERVICE],
                    frozenset(d.get(CONF_CATEGORIES, DEFAULT_CATEGORIES)),
                    float(d.get(CONF_DELAY, 0)),
                    bool(d.get(CONF_PRIORITY, False)),
                )
            )
        self._pending: list[CALLBACK_TYPE] = []

    # ---------------------------------------------------------------- input

    @callback
    def handle(self, event: dict[str, Any]) -> None:
        if event["type"] in ENDING:
            self._cancel_pending()
        spec = EVENT_MESSAGES.get(event["type"])
        if spec is None or not self.channels:
            return
        category, key = spec
        message = self._message(key, event)
        for channel in self.channels:
            if category not in channel.categories:
                continue
            if category == "alarm" and channel.delay > 0:
                self._schedule(channel, message, category)
            else:
                self._send(channel, message, category)

    @callback
    def resume_after_restart(self) -> None:
        """The alarm is still triggered after a restart: restart the escalation timers.

        Channels without a delay already got the message before the restart.
        """
        engine = self.manager.engine
        if engine.state != "triggered" or engine.cause is None:
            return
        event = {
            "type": "triggered",
            "cause": engine.cause,
            "sensor": engine.cause_sensor,
            "sensor_name": self.manager._sensor_name.get(engine.cause_sensor or "", engine.cause_sensor),
        }
        message = self._message("triggered", event)
        for channel in self.channels:
            if "alarm" in channel.categories and channel.delay > 0:
                self._schedule(channel, message, "alarm")

    @callback
    def async_stop(self) -> None:
        self._cancel_pending()

    @callback
    def cancel_escalations(self) -> None:
        self._cancel_pending()

    def _cancel_pending(self) -> None:
        for cancel in self._pending:
            cancel()
        self._pending.clear()

    # --------------------------------------------------------------- output

    def _lang(self) -> str:
        return self.hass.config.language

    def _names(self, ids: list[str]) -> str:
        return ", ".join(self.manager._sensor_name.get(z, z) for z in ids) or "-"

    def _message(self, key: str, event: dict[str, Any]) -> str:
        lang = self._lang()
        by = render(lang, "by", user=event["user"]) if event.get("user") else ""
        params: dict[str, Any] = {
            "sensor": event.get("sensor_name") or "-",
            "siren": event.get("siren", "-"),
            "name": event.get("name", "-"),
            "level": f"{event['level']:g}" if "level" in event else "-",
            "error": event.get("error", "-"),
            "sensors": self._names(event.get("sensors", [])),
            "rule": event.get("rule", "-"),
            "mode": event.get("mode", "-"),
            "by": by,
            "source": event.get("source") or "-",
            "panel": event.get("panel") or event.get("source") or "-",
            "minutes": event.get("minutes", "-"),
            "end": self._time(event.get("end")),
            "cause": self._translated(f"cause.{event.get('cause')}", event.get("cause")),
            "reason": self._translated(f"reason.{event.get('reason')}", event.get("reason")),
        }
        if key == "battery_low" and "level" not in event:  # a device that only says "battery low"
            key = "battery_low_flag"
        if key == "unconfirmed":
            params["rule"] = self.manager.rule_name(event.get("rule"))
        if key == "unconfirmed_escalated":
            params["rule"] = self.manager.rule_name(event.get("rule"))
        message = render(lang, key, **params)
        if key == "triggered" and not self.manager.siren_configured:
            message += " " + text(lang, "no_siren")
        return message

    def _translated(self, key: str, fallback: Any) -> str:
        try:
            return text(self._lang(), key)
        except KeyError:
            return str(fallback) if fallback is not None else "-"

    def _time(self, ts: float | None) -> str:
        if ts is None:
            return "-"
        return dt_util.as_local(dt_util.utc_from_timestamp(ts)).strftime("%H:%M:%S")

    @callback
    def _schedule(self, channel: Channel, message: str, category: str) -> None:
        @callback
        def fire(_now: datetime) -> None:
            # Disarming or the end of the alarm cancels this timer (ENDING),
            # so reaching it means the alarm is still active: escalate.
            self._pending.remove(cancel)
            self._send(channel, message, category)

        cancel = async_call_later(self.hass, channel.delay, fire)
        self._pending.append(cancel)

    @callback
    def _send(self, channel: Channel, message: str, category: str) -> None:
        self.hass.async_create_task(self._async_send(channel, message, category))

    async def _async_send(self, channel: Channel, message: str, category: str) -> None:
        data: dict[str, Any] = {"title": text(self._lang(), "title"), "message": message}
        if channel.priority and category == "alarm":
            # Companion app format: critical on iOS, high priority on Android.
            data["data"] = {
                "push": {"interruption-level": "critical", "sound": {"name": "default", "critical": 1, "volume": 1.0}},
                "ttl": 0,
                "priority": "high",
            }
        try:
            await self.hass.services.async_call("notify", channel.service, data, blocking=True)
        except Exception as err:  # noqa: BLE001 - any failing service must not break the alarm
            _LOGGER.error("Notification via notify.%s failed: %s", channel.service, err)
            self.manager.publish("notification_failed", channel=channel.name, error=str(err))

    async def async_send_reminder(self, key: str) -> int:
        """The test reminder, to every channel that gets fault messages.

        On a phone with the Home Assistant app the message has a button that sounds the siren briefly.
        Returns how many channels were tried.
        """
        lang = self._lang()
        sent = 0
        for channel in self.channels:
            if "fault" not in channel.categories:
                continue
            data: dict[str, Any] = {"title": text(lang, "title"), "message": text(lang, key)}
            if channel.service.startswith("mobile_app_"):
                data["data"] = {"tag": "vigil_selftest", "actions": [{"action": "VIGIL_TEST_SIREN", "title": text(lang, "selftest_action")}]}
            sent += 1
            try:
                await self.hass.services.async_call("notify", channel.service, data, blocking=True)
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Notification via notify.%s failed: %s", channel.service, err)
                self.manager.publish("notification_failed", channel=channel.name, error=str(err))
        return sent

    async def async_send_problem(self, problems: str) -> None:
        """A message to every channel that gets fault messages."""
        for channel in self.channels:
            if "fault" in channel.categories:
                await self._async_send(channel, render(self._lang(), "selftest_problem", problems=problems), "fault")

    async def async_test(self, channel_name: str | None = None) -> int:
        """Send a test message to all channels (or one). Returns how many were tried."""
        chosen = [c for c in self.channels if channel_name in (None, c.name)]
        for channel in chosen:
            await self._async_send(channel, text(self._lang(), "test"), "test")
        return len(chosen)
