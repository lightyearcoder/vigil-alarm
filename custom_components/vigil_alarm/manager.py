"""Glue between the pure core (vigil_core) and Home Assistant.

Owns one Engine per config entry: builds its config from the entry and its
subentries, feeds it sensor states, schedules its timers, persists its state and
publishes its events.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from functools import partial
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_point_in_utc_time,
    async_track_state_change_event,
)
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CHIME,
    CONF_CODE_ARM_REQUIRED,
    CONF_ENTITY_ID,
    CONF_HA_USER,
    CONF_PARTITION_NAME,
    CONF_PARTITIONS,
    CONF_STARTUP_WAIT,
    DEFAULT_STARTUP_WAIT,
    DOMAIN,
    PRIMARY_PARTITION,
    SAVE_DELAY,
    STARTUP_GRACE,
    STORAGE_VERSION,
    SUBENTRY_SENSOR,
    SUBENTRY_USER,
)
from .errors import VigilError
from .eventlog import EventLog
from .heartbeat import Heartbeat
from .items import Item, items_of
from .languages import ALL_NAMES, HOME_NAMES, language_of
from .lockout import CodeLockout
from .manager_commands import CommandsMixin
from .manager_config import (  # noqa: F401 - also the place these are imported from
    ROUTINE_EVENTS,
    SIGNAL_EVENT,
    SIGNAL_UPDATE,
    Partition,
    all_enabled_modes,
    build_config,
    build_configs,
    partition_data,
    partition_ids,
    sensor_value,
)
from .manager_views import ViewsMixin
from .notifier import Notifier
from .panels import PanelRegistry
from .selftest import SelfTest
from .sirens import SirenController
from .supervisor import Supervisor
from .valuewatch import Range, ValueWatch
from .vigil_core import Config, Engine, aggregate

_LOGGER = logging.getLogger(__name__)

class VigilManager(CommandsMixin, ViewsMixin):
    """Runs the engine of one config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        configs = build_configs(entry)  # raises ConfigError
        self.partitions: dict[str, Partition] = {}
        for pid, cfg in configs.items():
            self.partitions[pid] = Partition(
                pid, self._partition_name(pid), cfg,
                Engine(cfg, now=self._wall(), on_event=partial(self._handle_event, pid=pid)),
                primary=pid == PRIMARY_PARTITION,
            )
        first = configs[PRIMARY_PARTITION]
        sensors: dict[str, Any] = {}
        rules: dict[str, Any] = {}
        for cfg in configs.values():
            for sid, sensor in cfg.sensors.items():
                sensors.setdefault(sid, sensor)
            rules.update(cfg.rules)
        # All sensors and rules of the house, for lookups; the modes and delays are those of the first partition.
        self.config = Config(first.modes, sensors, rules, first.default_entry_delay, first.trigger_time)
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
        self._ranges: dict[str, Range] = {
            sid: rng
            for sid, sub in items_of(entry).items()
            if sub.subentry_type == SUBENTRY_SENSOR and (rng := Range.from_data(sub.data)) is not None
        }
        self._values = ValueWatch(hass)
        self._sensor_name: dict[str, str] = {
            sid: sub.title
            for sid, sub in items_of(entry).items()
            if sub.subentry_type == SUBENTRY_SENSOR
        }
        self.notifier = Notifier(hass, self)
        self.sirens = SirenController(hass, self)
        self.selftest = SelfTest(hass, entry, self)
        self.heartbeat = Heartbeat(hass, entry)
        from .handlers import HandlerMonitor
        self.handlers = HandlerMonitor(hass, entry, self)
        from .backups import (
            ConfigBackups,  # here: backups.py reads build_config from this module
        )
        self.backups = ConfigBackups(hass, entry)
        from .newsensors import (
            NewSensors,  # here: it reads from discovery, which reads from items
        )
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

    # ----------------------------------------------------------- partitions

    @property
    def engine(self) -> Engine:
        """The engine of the first partition: what an installation with one partition has."""
        return self.partitions[PRIMARY_PARTITION].engine

    @property
    def engines(self) -> list[Engine]:
        return [p.engine for p in self.partitions.values()]

    @property
    def multiple(self) -> bool:
        return len(self.partitions) > 1

    def _partition_name(self, pid: str) -> str:
        if pid == PRIMARY_PARTITION:
            return self.entry.data.get(CONF_PARTITION_NAME) or HOME_NAMES[language_of(self.hass.config.language)]
        sub = items_of(self.entry).get(pid)
        return sub.title if sub else pid

    def all_name(self) -> str:
        return ALL_NAMES[language_of(self.hass.config.language)]

    def partition(self, pid: str | None) -> Partition:
        """The partition with this id; no id means the first. Raises for an id that does not exist."""
        part = self.partitions.get(pid or PRIMARY_PARTITION)
        if part is None:
            raise VigilError(translation_domain=DOMAIN, translation_key="unknown_partition")
        return part

    def partition_of_sensor(self, sensor_id: str) -> Partition:
        """The partition that owns a sensor: its own for an intrusion sensor, the first for a safety sensor."""
        for part in self.partitions.values():
            if sensor_id in part.config.sensors:
                return part
        return self.partitions[PRIMARY_PARTITION]

    def engine_for_sensor(self, sensor_id: str) -> Engine:
        return self.partition_of_sensor(sensor_id).engine

    @property
    def any_triggered(self) -> bool:
        return any(e.state == "triggered" for e in self.engines)

    @property
    def all_disarmed(self) -> bool:
        return all(e.state == "disarmed" for e in self.engines)

    def combined(self):
        """The state of all partitions together (the "all" entity)."""
        return aggregate({pid: p.engine.state for pid, p in self.partitions.items()})

    @staticmethod
    def allowed_partitions(item: Item | None, pids: list[str]) -> list[str]:
        """The partitions a user or a panel may use; the list on the item, empty (or none) means all of them."""
        chosen = list(item.data.get(CONF_PARTITIONS) or []) if item is not None else []
        return [p for p in pids if p in chosen] if chosen else list(pids)

    def alarming(self, exclude: str | None = None) -> list[Partition]:
        """The partitions that are the source of an alarm: triggered by an intrusion, or the first partition for an
        alarm from a safety sensor (those sensors watch in every partition, but the alarm is one)."""
        return [p for p in self.partitions.values() if p.id != exclude and p.engine.state == "triggered"
                and (p.primary or p.engine.cause == "intrusion")]

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
    def _feed(self, sensor_id: str, value: str) -> None:
        """Give a sensor state to every partition that has the sensor (a safety sensor is in all of them)."""
        for part in self.partitions.values():
            if sensor_id in part.config.sensors:
                part.engine.set_sensor(sensor_id, value)

    @callback
    def _unavailable_sensors(self) -> list[str]:
        return [sid for sid, eid in self._sensor_entity.items()
                if self._raw(sid, self.hass.states.get(eid)) == "unavailable"]

    def _raw(self, sid: str, state: Any) -> str:
        """open, closed or unavailable; for a sensor that watches a number: outside, inside or no number."""
        rng = self._ranges.get(sid)
        return rng.classify(state) if rng else sensor_value(state)

    @callback
    def _value_for(self, sid: str, state: Any) -> str | None:
        """What the engine gets for this state. None: a number outside its limits that has not been so long enough."""
        raw = self._raw(sid, state)
        rng = self._ranges.get(sid)
        if rng is None:
            return raw
        return self._values.apply(sid, rng, raw, partial(self._range_time_up, sid))

    @callback
    def _range_time_up(self, sid: str) -> None:
        eid = self._sensor_entity.get(sid)
        if eid is None or self._raw(sid, self.hass.states.get(eid)) != "open":
            return
        self._values.confirm(sid)
        self._sync()
        self._feed(sid, "open")
        self._after()

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
            value = self._value_for(sid, self.hass.states.get(entity_id))
            if value is None or (value == "unavailable" and self._settling):
                continue
            self._feed(sid, value)
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
            self._feed(sid, "unavailable")  # now it is reported (and may trigger)
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
        self._values.shutdown()
        self.walktest.shutdown()
        self.panels.stop()
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        await self._store.async_save(self._data_to_save())
        await self.eventlog.async_flush()
        await self.alarmmemory.async_flush()
        await self.lockout.async_flush()
        await self.panels.async_flush()

    # ---------------------------------------------------------- persistence

    async def _async_restore(self) -> None:
        saved = await self._store.async_load()
        if not saved:
            return
        # Since 0.6.0 {"partitions": {id: state}}; before, the state of the one engine itself.
        states = saved["partitions"] if isinstance(saved.get("partitions"), dict) else {PRIMARY_PARTITION: saved}
        self.changed_by, self.changed_via = saved.get("changed_by"), saved.get("changed_via")
        for pid, part in self.partitions.items():
            state = states.get(pid)
            if not state:
                continue
            try:
                part.engine.restore_state(state)
            except ValueError as err:
                _LOGGER.warning("Saved alarm state is unusable, starting disarmed: %s", err)
                part.engine = Engine(part.config, now=self._wall(), on_event=partial(self._handle_event, pid=pid))
                self._emit_manager_event("state_restore_failed", reason=str(err), partition=pid)

    @callback
    def _data_to_save(self) -> dict[str, Any]:
        return {
            "partitions": {pid: p.engine.export_state() for pid, p in self.partitions.items()},
            "changed_by": self.changed_by,  # who armed or disarmed last: still known after a restart
            "changed_via": self.changed_via,
        }

    # ----------------------------------------------------------- engine I/O

    @callback
    def _sync(self) -> None:
        """Bring the engine's clock up to the wall clock (fires due timers)."""
        for engine in self.engines:
            engine.advance(max(self._wall(), engine.now))

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
        dues = [d for d in (e.next_due() for e in self.engines) if d is not None]
        due = min(dues) if dues else None
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
        new_state = event.data.get("new_state")
        if self._settling and self._raw(next((s for s, e in self._sensor_entity.items() if e == entity_id), ""), new_state) == "unavailable":
            return  # still starting up: wait for the end of the wait before calling it lost
        self._sync()
        for sid, eid in self._sensor_entity.items():
            if eid == entity_id:
                value = self._value_for(sid, new_state)
                if value is None:
                    continue  # a number outside its limits, not long enough yet
                self._feed(sid, value)
                self.walktest.note(sid, value)
                if not self.practice.active:
                    self.alarmmemory.note(sid, value)
                if value == "open" and sid in self._chime_sensors and not self._settling:
                    self._chime(sid)
        if self._settling and not self._unavailable_sensors():
            self._finish_settle()
        self._after()

    def _duplicate(self, part: Partition, event: dict[str, Any]) -> bool:
        """A safety sensor watches in every partition, so every engine reports it. The first partition speaks for
        all: what the other engines say about a safety sensor or a safety alarm is dropped."""
        if part.primary:
            return False
        kind = event.get("type")
        if kind in ("triggered", "trigger_cause_changed"):
            part.safety_trigger = event.get("cause") != "intrusion"
            return part.safety_trigger
        if kind == "trigger_ended":
            ended, part.safety_trigger = part.safety_trigger, False
            return ended
        sensor = part.config.sensors.get(event.get("sensor") or "")
        return bool(sensor and sensor.cls != "intrusion")

    def _handle_event(self, event: dict[str, Any], pid: str = PRIMARY_PARTITION) -> None:
        part = self.partitions.get(pid) or self.partitions[PRIMARY_PARTITION]
        if self._duplicate(part, event):
            return
        data = dict(event)
        data["partition"] = pid
        if self.multiple:
            data["partition_name"] = part.name
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
