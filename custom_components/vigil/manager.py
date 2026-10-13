"""Glue between the pure core (vigil_core) and Home Assistant.

Owns one Engine per config entry: builds its config from the entry and its
subentries, feeds it sensor states, schedules its timers, persists its state and
publishes its events.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import CALLBACK_TYPE, Context, Event, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_point_in_utc_time,
    async_track_state_change_event,
)
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .items import Item, items_of
from .const import (
    CONF_AT_ARM_OPEN,
    CONF_CLS,
    CONF_CODE_ARM_REQUIRED,
    CONF_DEFAULT_ENTRY_DELAY,
    CONF_ENTITY_ID,
    CONF_ENTRY_DELAY,
    CONF_ESCALATE,
    CONF_EXIT_DELAY,
    CONF_GAS_TYPE,
    CONF_ALLOWED_MODES,
    CONF_MAY_BYPASS_TAMPER,
    CONF_MODES,
    CONF_ON_UNAVAILABLE,
    CONF_REQUIRED,
    CONF_TRIGGER_TIME,
    CONF_TYPE,
    CONF_WINDOW,
    CONF_GROUP_MODES,
    CONF_SENSOR_GROUPS,
    CONF_SENSORS,
    DEFAULT_EXIT_DELAY,
    DOMAIN,
    SAVE_DELAY,
    STARTUP_GRACE,
    STORAGE_VERSION,
    SUBENTRY_RULE,
    SUBENTRY_NOTIFICATION,
    SUBENTRY_USER,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
)
from .credentials import find_user_by_code
from .notifier import Notifier
from .sirens import SirenController
from .supervisor import Supervisor
from .vigil_core import Config, ConfigError, Engine

_LOGGER = logging.getLogger(__name__)

SIGNAL_UPDATE = f"{DOMAIN}_update_{{}}"
SIGNAL_EVENT = f"{DOMAIN}_event_{{}}"


def build_config(entry: ConfigEntry, extra: dict[str, Item] | None = None) -> Config:
    """Build the core configuration from a config entry and its items.

    `extra` can hold a subentry that is not saved yet (used to validate a flow).
    Raises ConfigError.
    """
    enabled = list(entry.data.get(CONF_MODES, []))
    modes = {
        m: {"exit_delay": entry.data.get(CONF_EXIT_DELAY.format(mode=m), DEFAULT_EXIT_DELAY.get(m, 0))}
        for m in enabled
    }
    subentries = dict(items_of(entry))
    subentries.update(extra or {})
    sensors: dict[str, Any] = {}
    rules: dict[str, Any] = {}
    # A sensor group says in which modes its sensors are watching; the core only sees the result.
    group_modes = {
        gid: set(sub.data.get(CONF_GROUP_MODES, []))
        for gid, sub in subentries.items()
        if sub.subentry_type == SUBENTRY_SENSOR_GROUP
    }
    for sid, sub in subentries.items():
        d = sub.data
        if sub.subentry_type == SUBENTRY_SENSOR:
            body: dict[str, Any] = {
                "cls": d[CONF_CLS],
                "on_unavailable": d.get(CONF_ON_UNAVAILABLE) or None,
            }
            if d[CONF_CLS] == "intrusion":
                body["type"] = d.get(CONF_TYPE, "instant")
                groups = d.get(CONF_SENSOR_GROUPS, [])
                body["modes"] = [m for m in modes if any(m in group_modes.get(g, ()) for g in groups)]
                body["at_arm_open"] = d.get(CONF_AT_ARM_OPEN, "bypass")
                if d.get(CONF_ENTRY_DELAY) is not None:
                    body["entry_delay"] = d[CONF_ENTRY_DELAY]
            if d[CONF_CLS] == "gas":
                body["gas_type"] = d.get(CONF_GAS_TYPE, "other")
            body = {k: v for k, v in body.items() if v is not None}
            sensors[sid] = body
        elif sub.subentry_type == SUBENTRY_RULE:
            rules[sid] = {
                "sensors": list(d[CONF_SENSORS]),
                "required": d.get(CONF_REQUIRED, 2),
                "window": d.get(CONF_WINDOW, 60),
                "escalate": d.get(CONF_ESCALATE, False),
            }
    raw: dict[str, Any] = {
        "version": 1,
        "default_entry_delay": entry.data.get(CONF_DEFAULT_ENTRY_DELAY, 30),
        "modes": modes,
        "sensors": sensors,
        "rules": rules,
    }
    if entry.data.get(CONF_TRIGGER_TIME):
        raw["trigger_time"] = entry.data[CONF_TRIGGER_TIME]
    return Config.from_dict(raw)


def sensor_value(state: Any) -> str:
    if state is None:
        return "unavailable"
    if state.state == STATE_ON:
        return "open"
    if state.state == STATE_OFF:
        return "closed"
    return "unavailable"


class VigilManager:
    """Runs the engine of one config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.config = build_config(entry)  # raises ConfigError
        self.engine = Engine(self.config, now=self._wall(), on_event=self._handle_event)
        self.ready = False
        self.early_events: list[dict[str, Any]] = []
        self.last_event: dict[str, Any] | None = None
        self.changed_by: str | None = None
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        self._unsub_timer: CALLBACK_TYPE | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._sensor_entity: dict[str, str] = {
            sid: sub.data[CONF_ENTITY_ID]
            for sid, sub in items_of(entry).items()
            if sub.subentry_type == SUBENTRY_SENSOR
        }
        self._sensor_name: dict[str, str] = {
            sid: sub.title
            for sid, sub in items_of(entry).items()
            if sub.subentry_type == SUBENTRY_SENSOR
        }
        self.notifier = Notifier(hass, self)
        self.sirens = SirenController(hass, self)
        self.supervisor = Supervisor(hass, self)
        self.users: list[Item] = [
            sub for sub in items_of(entry).values() if sub.subentry_type == SUBENTRY_USER
        ]

    # ------------------------------------------------------------ lifecycle

    @staticmethod
    def _wall() -> float:
        return dt_util.utcnow().timestamp()

    @property
    def numeric_codes(self) -> bool:
        """True if every user's code is numeric (decides the keypad type)."""
        return all(u.data.get("code_numeric", True) for u in self.users)

    @property
    def code_arm_required(self) -> bool:
        return bool(self.users) and self.entry.data.get(CONF_CODE_ARM_REQUIRED, True)

    async def async_setup(self) -> None:
        await self._async_restore()
        self._sync()
        if self.hass.is_running:
            self._start_feeding()
        else:
            async_at_started(self.hass, self._started)

    @callback
    def _started(self, _hass: HomeAssistant) -> None:
        self._unsubs.append(async_call_later(self.hass, STARTUP_GRACE, self._after_grace))

    @callback
    def _after_grace(self, _now: datetime) -> None:
        self._start_feeding()

    @callback
    def _start_feeding(self) -> None:
        """Trust the sensor entities from now on: take their states and follow them."""
        if self.ready:
            return
        self._sync()
        for sid, entity_id in self._sensor_entity.items():
            self.engine.set_sensor(sid, sensor_value(self.hass.states.get(entity_id)))
        if self._sensor_entity:
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass, list(self._sensor_entity.values()), self._sensor_changed
                )
            )
        self.ready = True
        self.notifier.resume_after_restart()
        self.sirens.resume_after_restart()
        self.supervisor.start()
        self._after()

    async def async_unload(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self.notifier.async_stop()
        self.sirens.async_stop()
        self.supervisor.stop()
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        await self._store.async_save(self.engine.export_state())

    # ---------------------------------------------------------- persistence

    async def _async_restore(self) -> None:
        saved = await self._store.async_load()
        if not saved:
            return
        try:
            self.engine.restore_state(saved)
        except ValueError as err:
            _LOGGER.warning("Saved alarm state is unusable, starting disarmed: %s", err)
            self.engine = Engine(self.config, now=self._wall(), on_event=self._handle_event)
            self._emit_manager_event("state_restore_failed", reason=str(err))

    @callback
    def _data_to_save(self) -> dict[str, Any]:
        return self.engine.export_state()

    # ----------------------------------------------------------- engine I/O

    @callback
    def _sync(self) -> None:
        """Bring the engine's clock up to the wall clock (fires due timers)."""
        self.engine.advance(max(self._wall(), self.engine.now))

    @callback
    def _after(self) -> None:
        """Reschedule the wake-up, persist and tell the entities."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        due = self.engine.next_due()
        if due is not None:
            self._unsub_timer = async_track_point_in_utc_time(
                self.hass, self._timer_fired, datetime.fromtimestamp(due, timezone.utc)
            )
        self._store.async_delay_save(self._data_to_save, SAVE_DELAY)
        async_dispatcher_send(self.hass, SIGNAL_UPDATE.format(self.entry.entry_id))

    @callback
    def _timer_fired(self, _now: datetime) -> None:
        self._unsub_timer = None
        self._sync()
        self._after()

    @callback
    def _sensor_changed(self, event: Event) -> None:
        entity_id = event.data["entity_id"]
        value = sensor_value(event.data.get("new_state"))
        self._sync()
        for sid, eid in self._sensor_entity.items():
            if eid == entity_id:
                self.engine.set_sensor(sid, value)
        self._after()

    def _handle_event(self, event: dict[str, Any]) -> None:
        data = dict(event)
        if sensor := data.get("sensor"):
            data["sensor_name"] = self._sensor_name.get(sensor, sensor)
        if data.get("type") in ("armed", "disarmed"):
            self.changed_by = data.get("user")
        self.last_event = data
        async_dispatcher_send(self.hass, SIGNAL_EVENT.format(self.entry.entry_id), data)
        self.sirens.handle(data)
        self.notifier.handle(data)

    @callback
    def publish(self, type_: str, **fields: Any) -> None:
        """Publish an event of the glue layer (not sent to the notifier)."""
        data = {"t": self._wall(), "type": type_, **fields}
        self.last_event = data
        async_dispatcher_send(self.hass, SIGNAL_EVENT.format(self.entry.entry_id), data)
        self.notifier.handle(data)  # ignores everything but the events it has a text for

    @property
    def siren_configured(self) -> bool:
        return self.sirens.configured

    def rule_name(self, rule_id: str | None) -> str:
        sub = items_of(self.entry).get(rule_id) if rule_id else None
        return sub.title if sub else str(rule_id)

    def _emit_manager_event(self, type_: str, **fields: Any) -> None:
        """An event of the glue layer. Kept until the event entity exists."""
        event = {"t": self._wall(), "type": type_, **fields}
        self.last_event = event
        self.early_events.append(event)
        self.notifier.handle(event)

    # ------------------------------------------------------------- commands

    async def _authenticate(self, code: str | None, *, required: bool) -> Item | None:
        """Find the user for a code. No users configured: everything is allowed."""
        if not self.users:
            return None
        if not code:
            if required:
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="code_required"
                )
            return None
        user = await self.hass.async_add_executor_job(find_user_by_code, code, self.users)
        if user is None:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_code")
        return user

    def _sensor_names(self, ids: list[str]) -> str:
        return ", ".join(self._sensor_name.get(z, z) for z in ids) or "-"

    async def async_arm(self, mode: str, code: str | None) -> None:
        if not self.ready:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_ready")
        user = await self._authenticate(code, required=self.code_arm_required)
        if user is not None:
            allowed = user.data.get(CONF_ALLOWED_MODES) or list(self.config.modes)
            if mode not in allowed:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="mode_not_allowed",
                    translation_placeholders={"user": user.title, "mode": mode},
                )
        name = user.title if user else None
        self._sync()
        ok = self.engine.arm(mode, user=name)
        self._after()
        if not ok:
            event = next(e for e in reversed(self.engine.events) if e["type"] == "arm_refused")
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="arm_refused",
                translation_placeholders={
                    "reason": event["reason"],
                    "sensors": self._sensor_names(event["sensors"]),
                },
            )

    async def async_disarm(self, code: str | None) -> None:
        user = await self._authenticate(code, required=True)
        self._sync()
        self.engine.disarm(user=user.title if user else None)
        self._after()

    async def async_bypass(
        self, sensor_id: str, code: str | None, *, is_admin: bool, bypass: bool
    ) -> None:
        if sensor_id not in self.config.sensors:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="unknown_sensor")
        sensor = self.config.sensors[sensor_id]
        user = await self._authorize(code, is_admin)
        if bypass and sensor.cls == "tamper" and not is_admin:
            if user is None or not user.data.get(CONF_MAY_BYPASS_TAMPER, False):
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="tamper_bypass_not_allowed"
                )
        name = user.title if user else None
        self._sync()
        if bypass:
            ok = self.engine.bypass(sensor_id, user=name)
        else:
            self.engine.unbypass(sensor_id, user=name)
            ok = True
        self._after()
        if not ok:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="sensor_not_bypassable"
            )

    async def _authorize(self, code: str | None, is_admin: bool) -> Item | None:
        """An administrator in the UI, or a user with a valid code."""
        if not is_admin:
            return await self._authenticate(code, required=True)
        return await self._authenticate(code, required=False) if code else None

    async def async_silence(self, code: str | None, *, is_admin: bool) -> None:
        """Stop the sirens; the alarm itself stays triggered."""
        user = await self._authorize(code, is_admin)
        name = user.title if user else None
        self.sirens.silence()
        self.publish("alarm_silenced", user=name)

    async def async_acknowledge(self, code: str | None, *, is_admin: bool) -> None:
        """Confirm that the alarm has been seen: pending escalations are cancelled."""
        user = await self._authorize(code, is_admin)
        name = user.title if user else None
        self.notifier.cancel_escalations()
        self.publish("alarm_acknowledged", user=name)

    async def async_is_admin(self, context: Context | None) -> bool:
        """Calls from the UI carry a user; automations and scripts do not."""
        if context is None or not context.user_id:
            return False
        user = await self.hass.auth.async_get_user(context.user_id)
        return bool(user and user.is_admin)

    def sensor_id_for_entity(self, entity_id: str) -> str | None:
        for sid, eid in self._sensor_entity.items():
            if eid == entity_id:
                return sid
        return None

    # ---------------------------------------------------------------- views

    def sensor_status(self, sensor_id: str) -> str:
        return self.engine.sensor_status(sensor_id)

    def sensor_is_bypassed(self, sensor_id: str) -> bool:
        return self.engine.is_bypassed(sensor_id)

    def sensor_items(self) -> list[Item]:
        return [s for s in items_of(self.entry).values() if s.subentry_type == SUBENTRY_SENSOR]

    def classes_present(self) -> set[str]:
        return {z.cls for z in self.config.sensors.values()}

    def snapshot(self) -> dict[str, Any]:
        snap = self.engine.snapshot()
        names = self._sensor_name
        for key in ("open_sensors", "faults", "technical_alarms"):
            snap[key] = [names.get(z, z) for z in snap[key]]
        snap["cause_sensor"] = names.get(snap["cause_sensor"], snap["cause_sensor"])
        snap["problems"] = self.supervisor.problems()
        snap["last_event"] = self.last_event
        snap["bypassed_sensors"] = [
            names.get(z, z) for z in self.config.sensors
            if self.engine.sensor_status(z) in ("bypassed", "bypassed_at_arm")
        ]
        return snap
