"""Glue between the pure core (vigil_core) and Home Assistant.

Owns one Engine per config entry: builds its config from the entry and its
subentries, feeds it sensor states, schedules its timers, persists its state and
publishes its events.
"""

from __future__ import annotations

import logging
import time
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
    CONF_ABORT_SECONDS,
    CONF_AT_ARM_OPEN,
    CONF_CHIME,
    CONF_CHIME_ENTITY,
    CONF_CHIME_SECONDS,
    DEFAULT_ABORT_SECONDS,
    DEFAULT_CHIME_SECONDS,
    CONF_CLS,
    CONF_CODE_ARM_REQUIRED,
    CONF_HA_USER,
    CONF_DEFAULT_ENTRY_DELAY,
    CONF_ENTITY_ID,
    CONF_ENTRY_DELAY,
    CONF_ESCALATE,
    CONF_EXIT_DELAY,
    CONF_GAS_TYPE,
    CONF_ALLOWED_MODES,
    CONF_MAY_BYPASS,
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
    CONF_STARTUP_WAIT,
    DEFAULT_STARTUP_WAIT,
    STARTUP_GRACE,
    STORAGE_VERSION,
    SUBENTRY_RULE,
    SUBENTRY_NOTIFICATION,
    SUBENTRY_USER,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
)
from .credentials import find_user_and_kind
from .eventlog import EventLog
from .notifier import Notifier
from .heartbeat import Heartbeat
from .lockout import CodeLockout
from .panels import PanelRegistry
from .selftest import SelfTest
from .sirens import SirenController
from .supervisor import Supervisor
from .vigil_core import Config, ConfigError, Engine

_LOGGER = logging.getLogger(__name__)

SIGNAL_UPDATE = f"{DOMAIN}_update_{{}}"
SIGNAL_EVENT = f"{DOMAIN}_event_{{}}"
ROUTINE_EVENTS = {"selftest_checked", "selftest_reminder", "selftest_siren_tested", "startup_settled"}


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


def _bypass_rank(status: str, bypassable: bool) -> int:
    """Order of the sensor list on a panel: what is most likely to be bypassed comes first."""
    if status in ("open", "waiting"):
        return 0 if bypassable else 2
    if status == "unavailable":
        return 1 if bypassable else 3
    if status in ("bypassed", "bypassed_at_arm"):
        return 4  # next in line: the ones to restore
    return 5  # closed and fine


class VigilManager:
    """Runs the engine of one config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.config = build_config(entry)  # raises ConfigError
        self.engine = Engine(self.config, now=self._wall(), on_event=self._handle_event)
        self.ready = False
        self._settling = False  # after a restart: sensors that are not there yet are not reported as lost yet
        self._settle_timer: CALLBACK_TYPE | None = None
        self._started_at = 0.0
        self.early_events: list[dict[str, Any]] = []
        self.eventlog = EventLog(hass, entry, self)
        self.panels = PanelRegistry(hass, self)
        self.lockout = CodeLockout(hass, entry, lambda: self._clock(), self.panels.ids)
        self.last_event: dict[str, Any] | None = None
        self.changed_by: str | None = None  # the user who armed or disarmed last (None: no code, or automatic)
        self.changed_via: str | None = None  # the panel or device it was done on
        self._actor_parts: dict[str, tuple[str | None, str | None]] = {}
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
        self.selftest = SelfTest(hass, entry, self)
        self.heartbeat = Heartbeat(hass, entry)
        from .backups import ConfigBackups  # here: backups.py reads build_config from this module
        self.backups = ConfigBackups(hass, entry)
        from .newsensors import NewSensors  # here: it reads from discovery, which reads from items
        self.new_sensors = NewSensors(hass, entry, self)
        from .alarmmemory import AlarmMemory
        self.alarmmemory = AlarmMemory(hass, self)
        self._chime_sensors = {
            sid for sid, sub in items_of(entry).items()
            if sub.subentry_type == SUBENTRY_SENSOR and sub.data.get(CONF_CHIME)
        }
        self._chime_last: dict[str, float] = {}
        self.auth_duress = False  # the last code that was checked was a duress code
        from .testing import Practice, WalkTest
        self.practice = Practice(hass, self)
        self.walktest = WalkTest(hass, self)
        self.supervisor = Supervisor(hass, self)
        self.users: list[Item] = [
            sub for sub in items_of(entry).values() if sub.subentry_type == SUBENTRY_USER
        ]

    # ------------------------------------------------------------ lifecycle

    @staticmethod
    def _clock() -> float:
        """Wall-clock seconds, for the wrong-code lockout (a test can replace it)."""
        return dt_util.utcnow().timestamp()

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

    @property
    def only_registered(self) -> bool:
        """Is the list of Home Assistant accounts in use? As soon as one panel is bound to an account (a tablet, a
        phone), every other ordinary account is refused. With no such account nothing changes, so an update from
        an older version changes nothing."""
        return any(p.data.get(CONF_HA_USER) for p in self.panels.items())

    async def async_setup(self) -> None:
        await self.backups.async_start()
        await self.new_sensors.async_start()
        await self.eventlog.async_load()
        await self.lockout.async_load()
        await self.panels.async_load()
        await self._async_restore()
        await self.alarmmemory.async_load()  # after the restore: it looks at the state the alarm is in
        self._sync()
        if self.hass.is_running:
            self._start_feeding()
        else:
            async_at_started(self.hass, self._started)

    @callback
    def _started(self, _hass: HomeAssistant) -> None:
        self._started_at = self._clock()
        self._unsubs.append(async_call_later(self.hass, STARTUP_GRACE, self._after_grace))

    @callback
    def _after_grace(self, _now: datetime) -> None:
        self._start_feeding(settle=True)

    @callback
    def _unavailable_sensors(self) -> list[str]:
        return [sid for sid, eid in self._sensor_entity.items()
                if sensor_value(self.hass.states.get(eid)) == "unavailable"]

    @callback
    def _start_feeding(self, settle: bool = False) -> None:
        """Trust the sensor entities from now on: take their states and follow them.

        `settle`: Home Assistant has just started. A sensor that is not available yet (MQTT or Zigbee still starting)
        is left alone, neither lost nor an alarm, until all sensors are there or the wait is over."""
        if self.ready:
            return
        self._sync()
        self._settling = settle and bool(self._sensor_entity)
        for sid, entity_id in self._sensor_entity.items():
            value = sensor_value(self.hass.states.get(entity_id))
            if value == "unavailable" and self._settling:
                continue
            self.engine.set_sensor(sid, value)
        if self._sensor_entity:
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass, list(self._sensor_entity.values()), self._sensor_changed
                )
            )
        self.ready = True
        if self._settling:
            if self._unavailable_sensors():
                wait = max(0, int(self.entry.data.get(CONF_STARTUP_WAIT, DEFAULT_STARTUP_WAIT)) - STARTUP_GRACE)
                self._settle_timer = async_call_later(self.hass, wait, self._settle_timeout)
            else:
                self._finish_settle()
        self.notifier.resume_after_restart()
        self.sirens.resume_after_restart()
        self.supervisor.start()
        self.panels.start()
        self._after()

    @callback
    def _settle_timeout(self, _now: datetime) -> None:
        self._settle_timer = None
        self._finish_settle()

    @callback
    def _finish_settle(self) -> None:
        """All sensors are there, or the wait is over: from now on a missing sensor is a real problem."""
        if not self._settling:
            return
        self._settling = False
        if self._settle_timer:
            self._settle_timer()
            self._settle_timer = None
        gone = self._unavailable_sensors()
        self.publish("startup_settled", waited=round(self._clock() - self._started_at), unavailable=len(gone),
                     sensors=", ".join(self._sensor_name.get(s, s) for s in gone))
        for sid in gone:
            self.engine.set_sensor(sid, "unavailable")  # now it is reported (and may trigger)
        self._after()

    async def async_unload(self) -> None:
        if self._settle_timer:
            self._settle_timer()
            self._settle_timer = None
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self.notifier.async_stop()
        self.sirens.async_stop()
        self.supervisor.stop()
        self.new_sensors.stop()
        self.practice.shutdown()
        self.walktest.shutdown()
        self.panels.stop()
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        await self._store.async_save(self.engine.export_state())
        await self.eventlog.async_flush()
        await self.alarmmemory.async_flush()
        await self.lockout.async_flush()
        await self.panels.async_flush()

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
    def notify_changed(self) -> None:
        """Tell the panel something changed that is not the alarm itself (for example new sensors found)."""
        async_dispatcher_send(self.hass, SIGNAL_UPDATE.format(self.entry.entry_id))

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
        if self._settling and value == "unavailable":
            return  # still starting up: wait for the end of the wait before calling it lost
        self._sync()
        for sid, eid in self._sensor_entity.items():
            if eid == entity_id:
                self.engine.set_sensor(sid, value)
                self.walktest.note(sid, value)
                if not self.practice.active:
                    self.alarmmemory.note(sid, value)
                if value == "open" and sid in self._chime_sensors and not self._settling:
                    self._chime(sid)
        if self._settling and not self._unavailable_sensors():
            self._finish_settle()
        self._after()

    def _handle_event(self, event: dict[str, Any]) -> None:
        data = dict(event)
        if sensor := data.get("sensor"):
            data["sensor_name"] = self._sensor_name.get(sensor, sensor)
        if data.get("type") in ("armed", "disarmed"):
            self.changed_by, self.changed_via = self._actor_parts.get(data.get("user"), (data.get("user"), None))
        if self.practice.active:
            data["practice"] = True  # in the log as practice; no siren, no message
        self.last_event = data
        self.eventlog.add(data)
        async_dispatcher_send(self.hass, SIGNAL_EVENT.format(self.entry.entry_id), data)
        if not self.practice.active:
            self.alarmmemory.on_event(data)
            self.sirens.handle(data)
            self.notifier.handle(data)
        elif data.get("type") in ("triggered", "trigger_cause_changed"):
            self.practice.muted_trigger = data  # if practice ends while this alarm is still on, it is let through
        elif data.get("type") == "disarmed":
            self.practice.stop("disarmed")  # one round: a forgotten practice mode must not keep a real alarm silent

    @callback
    def publish(self, type_: str, *, quiet: bool = False, **fields: Any) -> None:
        """Publish an event of the glue layer (not sent to the notifier).

        `quiet`: for the log and the notifier only. It does not become "the last event" and does not reach the event
        entity, so nothing on a dashboard or a panel shows it (the duress code)."""
        data = {"t": self._wall(), "type": type_, **fields}
        if self.practice.active:
            data["practice"] = True
        if type_ not in ROUTINE_EVENTS and not quiet:  # the daily check must not replace "the last thing the alarm reported"
            self.last_event = data
        self.eventlog.add(data)
        if not quiet:
            async_dispatcher_send(self.hass, SIGNAL_EVENT.format(self.entry.entry_id), data)
        if not self.practice.active:
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
        self.eventlog.add(event)
        self.notifier.handle(event)

    # ------------------------------------------------------------- commands

    async def _operator(self, source: str | None, user_id: str | None, action: str) -> str | None:
        """Who is calling? Returns the source (the panel id of a registered account wins over a made-up text).

        Once an account is registered, a Home Assistant account that is neither registered nor an administrator
        is refused here, before any code is looked at and without counting towards a lockout. A call without a
        user (an automation, a script, an ESPHome panel) is not touched: those are your own."""
        source = self.panels.source_for(source, user_id)
        if not user_id or self.panels.for_user(user_id) or not self.only_registered:
            return source
        account = await self.hass.auth.async_get_user(user_id)
        if account is not None and not account.is_admin and not account.system_generated:
            self.publish("user_refused", user=account.name, source=source, action=action)
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="user_not_registered")
        return source

    async def _authenticate(
        self, code: str | None, *, required: bool, source: str | None = None, action: str | None = None,
    ) -> Item | None:
        """Find the user for a code. No users configured: everything is allowed."""
        if not self.users:
            return None
        if not code:
            if required:
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="code_required"
                )
            return None
        if self.lockout.refusal(source):  # before hashing: a locked control point also costs no CPU
            raise self.lock_error(source)
        user, duress = await self.hass.async_add_executor_job(find_user_and_kind, code, self.users)
        self.auth_duress = duress and user is not None
        if user is not None:
            self.lockout.record_success(source)
            if duress:  # works like the normal code, and tells the channels quietly
                self.publish("duress_used", quiet=True, user=user.title, source=source, action=action)
        else:
            if locked := self.lockout.record_failure(source):
                self.publish_lock(locked, source, action)
            # Never log the code itself; the source (for example a panel) and the action are enough.
            self.publish("code_rejected", source=source, action=action)
            if locked:  # this wrong code started a lock: say so at once, not only at the next try
                raise self.lock_error(source, started=locked)
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_code")
        return user

    def lock_error(self, source: str | None, bucket: str | None = None, started=None) -> ServiceValidationError:
        """The error for a locked control point: for good, or for so many more minutes (rounded up)."""
        if started is not None:
            permanent, seconds = started.minutes is None, (started.minutes or 0) * 60
        else:
            permanent, seconds = self.lockout.is_permanent(source, bucket), self.lockout.remaining(source, bucket)
        return ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="code_locked_permanent" if permanent else "code_locked",
            translation_placeholders={"minutes": str(max(1, -(-int(seconds) // 60)))},
        )

    def publish_lock(self, locked, source: str | None, action: str | None) -> None:
        """Tell that a lock has just started: for a while, or for good."""
        if locked.minutes is None:
            self.publish("code_locked_permanent", source=source, action=action, timer=locked.bucket)
        else:
            self.publish("code_locked", source=source, action=action, timer=locked.bucket, minutes=locked.minutes)

    def _actor(self, user: Item | None, source: str | None) -> str | None:
        """Who or what did it: the user, the control point (a panel), or both. The two parts are remembered, so
        `changed_by` (the user) and `changed_via` (the panel or device) can be told apart."""
        name = user.title if user else None
        combined = (f"{name} ({source})" if name else source) if source else name
        if combined:
            self._actor_parts[combined] = (name, source)
        return combined

    def _sensor_names(self, ids: list[str]) -> str:
        return ", ".join(self._sensor_name.get(z, z) for z in ids) or "-"

    def arm_blockers(self, mode: str, *, sync: bool = True) -> list[dict[str, Any]]:
        """What stops arming `mode` now, with the name of the sensor: the answer to "why can't I arm?".
        `sync=False` takes the engine as it is (the live view must not trigger a sync of its own)."""
        if sync:
            self._sync()
        return [
            {**b, "name": self._sensor_names([b["sensor"]]) if b["sensor"] else "",
             "entity_id": self._sensor_entity.get(b["sensor"]) if b["sensor"] else None}
            for b in self.engine.arm_check(mode)
        ]

    async def async_arm(
        self, mode: str, code: str | None, source: str | None = None, user_id: str | None = None,
        *, bypass_open: bool = False,
    ) -> None:
        """Arm. With `bypass_open` what stops it (an open tamper contact, a sensor that does not answer) is bypassed
        first: for someone who may bypass, with the same rules as bypassing by hand, and never a fire or gas sensor."""
        self.walktest.stop("stopped")  # arming ends a walk test
        source = await self._operator(source, user_id, "arm")
        if not self.ready:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_ready")
        if mode not in self.config.modes:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="mode_not_enabled",
                translation_placeholders={"mode": mode},
            )
        self.panels.check(source, "arm", mode)
        panel = self.panels.check(source, "bypass") if bypass_open else None
        # From a registered panel a bypass always needs a code, like bypassing by hand.
        user = await self._authenticate(
            code, required=self.code_arm_required or panel is not None, source=source, action="arm"
        )
        if user is not None:
            allowed = user.data.get(CONF_ALLOWED_MODES) or list(self.config.modes)
            if mode not in allowed:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="mode_not_allowed",
                    translation_placeholders={"user": user.title, "mode": mode},
                )
        name = self._actor(user, source)
        self._sync()
        bypassed: list[str] = []
        if bypass_open:
            blockers = self.engine.arm_check(mode)
            is_admin = user_id is not None and await self.async_is_admin_id(user_id)
            if blockers and not is_admin and user is not None and not user.data.get(CONF_MAY_BYPASS, True):
                raise ServiceValidationError(translation_domain=DOMAIN, translation_key="bypass_not_allowed")
            for b in blockers:
                if b["sensor"] and self.config.sensors[b["sensor"]].cls == "tamper" and not is_admin \
                        and (user is None or not user.data.get(CONF_MAY_BYPASS_TAMPER, False)):
                    raise ServiceValidationError(translation_domain=DOMAIN, translation_key="tamper_bypass_not_allowed")
            if all(b["bypassable"] for b in blockers):  # one that cannot be bypassed: it is refused as usual
                for b in blockers:
                    if self.engine.bypass(b["sensor"], user=name):
                        bypassed.append(b["sensor"])
        ok = self.engine.arm(mode, user=name)
        if not ok:
            for sid in bypassed:  # it did not start after all: put them back
                self.engine.unbypass(sid, user=name)
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

    async def async_check_code(self, code: str | None, source: str | None = None, user_id: str | None = None) -> None:
        """Is this a valid code? Counts as a try for the lockout. For a panel that hides things behind a code."""
        source = await self._operator(source, user_id, "check_code")
        self.panels.check(source, "check_code")
        await self._authenticate(code, required=True, source=source, action="check_code")

    async def async_disarm(self, code: str | None, source: str | None = None, user_id: str | None = None) -> None:
        source = await self._operator(source, user_id, "disarm")
        self.panels.check(source, "disarm")
        user = await self._authenticate(code, required=True, source=source, action="disarm")
        duress = self.auth_duress
        self._sync()
        cancelled = not duress and self._within_abort_window()
        name = self._actor(user, source)
        self.engine.disarm(user=name)
        if cancelled:
            self.alarmmemory.mark_cancelled()
            self.publish("alarm_cancelled", user=name, source=source)
        self._after()

    def _within_abort_window(self) -> bool:
        """Is this a disarm soon enough after the siren went off to call it a false alarm?"""
        seconds = int(self.entry.data.get(CONF_ABORT_SECONDS, DEFAULT_ABORT_SECONDS))
        engine = self.engine
        if seconds <= 0 or engine.state != "triggered" or engine.cause != "intrusion":
            return False
        started = self.alarmmemory.started
        return bool(self.alarmmemory.recording and started and self._wall() - started <= seconds)

    # ----------------------------------------------------------------- chime

    @callback
    def _chime(self, sensor_id: str) -> None:
        """A door or window with the chime opened while the alarm is off: a short sound. No alarm, no message and no
        line in the log; the event entity gets it, so an automation can do more (play a sound on a speaker)."""
        if self.engine.state != "disarmed" or not self.ready:
            return
        now = self._wall()
        if now - self._chime_last.get(sensor_id, 0) < 3:  # a contact that flickers rings once
            return
        self._chime_last[sensor_id] = now
        async_dispatcher_send(
            self.hass, SIGNAL_EVENT.format(self.entry.entry_id),
            {"t": now, "type": "chime", "sensor": sensor_id, "sensor_name": self._sensor_name.get(sensor_id, sensor_id)},
        )
        if entity_id := self.entry.data.get(CONF_CHIME_ENTITY):
            self.hass.async_create_task(self._async_ring(entity_id))

    async def _async_ring(self, entity_id: str) -> None:
        domain = entity_id.split(".")[0]
        try:
            if domain in ("button", "input_button"):
                await self.hass.services.async_call(domain, "press", {"entity_id": entity_id}, blocking=True)
            elif domain == "script":
                await self.hass.services.async_call("script", "turn_on", {"entity_id": entity_id}, blocking=True)
            else:
                await self.hass.services.async_call(domain, "turn_on", {"entity_id": entity_id}, blocking=True)

                @callback
                def off(_now: datetime) -> None:
                    self.hass.async_create_task(
                        self.hass.services.async_call(domain, "turn_off", {"entity_id": entity_id})
                    )

                seconds = float(self.entry.data.get(CONF_CHIME_SECONDS, DEFAULT_CHIME_SECONDS))
                async_call_later(self.hass, seconds, off)
        except Exception as err:  # noqa: BLE001 - a chime that fails must never matter
            _LOGGER.warning("Chime via %s failed: %s", entity_id, err)

    async def async_clear_alarm_memory(self, source: str | None = None, user: str | None = None) -> None:
        """Forget the last alarm. No code: it only wipes a note, it changes nothing in the alarm."""
        if self.alarmmemory.clear():
            self.publish("alarm_memory_cleared", user=user, source=source)
            self._after()

    async def async_bypass(
        self, sensor_id: str, code: str | None, *, is_admin: bool, bypass: bool, source: str | None = None,
        user_id: str | None = None,
    ) -> None:
        source = await self._operator(source, user_id, "bypass" if bypass else "unbypass")
        if sensor_id not in self.config.sensors:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="unknown_sensor")
        sensor = self.config.sensors[sensor_id]
        action = "bypass" if bypass else "unbypass"
        panel = self.panels.check(source, action)
        # Like arming: a code is only needed when arming needs one (`code_arm_required`). From a registered
        # panel a code is always needed: that is part of the standard profile.
        user = await self._authorize(
            code, is_admin, required=self.code_arm_required or panel is not None, source=source,
            action="bypass" if bypass else "unbypass",
        )
        # Putting a sensor back follows the same rules as bypassing it: who may bypass it may restore it.
        if not is_admin and user is not None and not user.data.get(CONF_MAY_BYPASS, True):
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="bypass_not_allowed")
        if sensor.cls == "tamper" and not is_admin:
            if user is None or not user.data.get(CONF_MAY_BYPASS_TAMPER, False):
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="tamper_bypass_not_allowed"
                )
        name = self._actor(user, source)
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

    async def _authorize(
        self, code: str | None, is_admin: bool, *, required: bool = True,
        source: str | None = None, action: str | None = None,
    ) -> Item | None:
        """An administrator in the UI, or a user with a valid code (when one is needed)."""
        if not is_admin:
            return await self._authenticate(code, required=required, source=source, action=action)
        if code:
            return await self._authenticate(code, required=False, source=source, action=action)
        return None

    async def async_silence(
        self, code: str | None, *, is_admin: bool, source: str | None = None, user_id: str | None = None
    ) -> None:
        """Stop the sirens; the alarm itself stays triggered."""
        source = await self._operator(source, user_id, "silence")
        self.panels.check(source, "silence")
        user = await self._authorize(code, is_admin, source=source, action="silence")
        name = self._actor(user, source)
        self.sirens.silence()
        self.publish("alarm_silenced", user=name)

    async def async_acknowledge(
        self, code: str | None, *, is_admin: bool, source: str | None = None, user_id: str | None = None
    ) -> None:
        """Confirm that the alarm has been seen: pending escalations are cancelled."""
        source = await self._operator(source, user_id, "acknowledge")
        self.panels.check(source, "acknowledge")
        user = await self._authorize(code, is_admin, source=source, action="acknowledge")
        name = self._actor(user, source)
        self.notifier.cancel_escalations()
        self.publish("alarm_acknowledged", user=name)

    async def async_is_admin_id(self, user_id: str) -> bool:
        if self.panels.for_user(user_id):  # a tablet is never an administrator for Vigil
            return False
        user = await self.hass.auth.async_get_user(user_id)
        return bool(user and user.is_admin)

    async def async_is_admin(self, context: Context | None) -> bool:
        """Calls from the UI carry a user; automations and scripts do not."""
        if context is None or not context.user_id:
            return False
        if self.panels.for_user(context.user_id):  # a tablet is never an administrator for Vigil
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

    def snapshot(self) -> dict[str, Any]:
        snap = self.engine.snapshot()
        names = self._sensor_name
        for key in ("open_sensors", "faults", "technical_alarms"):
            snap[key] = [names.get(z, z) for z in snap[key]]
        snap["cause_sensor"] = names.get(snap["cause_sensor"], snap["cause_sensor"])
        snap["problems"] = self.supervisor.problems()
        snap["last_event"] = self.last_event
        snap["open_now"] = [
            names.get(z, z) for z in self.config.sensors if self.engine.sensor_status(z) in ("open", "waiting")
        ]
        # One line per sensor, "name|entity|status|1 or 0 (bypassable)": plain text, because a display
        # (ESPHome) only reads plain attribute values, not lists. The sensors that come first for a bypass come
        # first in the list, so nobody has to page through closed doors to find the open one.
        rows = []
        for s in self.sensor_items():
            if s.subentry_id not in self.config.sensors:
                continue
            status = self.engine.sensor_status(s.subentry_id)
            bypassable = self.config.sensors[s.subentry_id].cls not in ("fire", "gas")
            rows.append((
                _bypass_rank(status, bypassable), s.title.lower(),
                "|".join((s.title.replace("|", "/").replace("\n", " "), s.data[CONF_ENTITY_ID], status,
                          "1" if bypassable else "0")),
            ))
        snap["panel_sensors"] = "\n".join(row for _rank, _name, row in sorted(rows))
        snap["bypassed_sensors"] = [
            names.get(z, z) for z in self.config.sensors
            if self.engine.sensor_status(z) in ("bypassed", "bypassed_at_arm")
        ]
        return snap
