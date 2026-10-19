"""State machine of the alarm core.

Pure Python, no Home Assistant imports, no real clock: time is an input
(`advance(t)`), so every scenario is deterministic and testable.

The engine only decides and publishes events (facts). It never calls a
service; the Home Assistant layer (or a future device) turns events into actions.
"""

from __future__ import annotations

from typing import Any, Callable

from .model import TECHNICAL_CLASSES, Config, Sensor

# Higher wins when a trigger is already running.
PRIORITY = {"fire": 5, "gas": 4, "tamper": 3, "alarm24": 3, "fault": 2, "intrusion": 1}

SENSOR_VALUES = ("closed", "open", "unavailable")
TIMER_KINDS = ("exit", "entry", "trigger_end", "rule")
STATE_VERSION = 1


class _SensorRuntime:
    __slots__ = ("value", "manual_bypass", "auto_bypass", "waiting")

    def __init__(self) -> None:
        self.value = "closed"
        self.manual_bypass = False  # set by the user, cleared at disarm
        self.auto_bypass = False  # set at the end of arming, cleared when the sensor closes
        self.waiting = False  # open at arming: becomes active after the first close


class Engine:
    def __init__(
        self,
        config: Config,
        now: float = 0.0,
        on_event: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.config = config
        self.now = now
        self.state = "disarmed"
        self.mode: str | None = None  # armed mode, or target mode while arming
        self.cause: str | None = None
        self.cause_sensor: str | None = None
        self.refuse_reason: str | None = None
        self.events: list[dict[str, Any]] = []
        self._on_event = on_event
        self._rt = {zid: _SensorRuntime() for zid in config.sensors}
        self._timers: list[tuple[float, int, str, str | None]] = []
        self._seq = 0
        self._protected = False  # intrusion protection is active (armed, possibly triggered)
        self._arm_user: str | None = None
        self._pending_sensor: str | None = None
        self._delay_end: float | None = None
        self._rules: dict[str, list[str]] = {}
        # Technical alarms (water) do not change the alarm state; they are active
        # while the sensor reports the problem and are tracked independently.
        self._technical: list[str] = []

    # ------------------------------------------------------------------ time

    def advance(self, t: float) -> None:
        """Move time forward, firing due timers in order (timers at t fire first)."""
        if t < self.now:
            raise ValueError(f"time cannot go backwards ({t} < {self.now})")
        while self._timers:
            due = min(self._timers, key=lambda x: (x[0], x[1]))
            if due[0] > t:
                break
            self._timers.remove(due)
            self.now = due[0]
            self._fire(due[2], due[3])
        self.now = t

    def _set_timer(self, kind: str, due: float, key: str | None = None) -> None:
        self._seq += 1
        self._timers.append((due, self._seq, kind, key))

    def _cancel(self, kind: str, key: str | None = None) -> None:
        self._timers = [
            tm for tm in self._timers if not (tm[2] == kind and tm[3] == key)
        ]

    def _fire(self, kind: str, key: str | None) -> None:
        if kind == "exit":
            self._finish_arming()
        elif kind == "entry":
            if self._pending_sensor is not None:
                self._trigger("intrusion", self._pending_sensor)
        elif kind == "trigger_end":
            self._end_trigger()
        elif kind == "rule" and key is not None:
            self._expire_rule(key)

    # ---------------------------------------------------------------- events

    def _emit(self, type_: str, **fields: Any) -> None:
        event = {"t": self.now, "type": type_, **fields}
        self.events.append(event)
        if self._on_event:
            self._on_event(event)

    # -------------------------------------------------------------- commands

    def arm(self, mode: str, user: str | None = None) -> bool:
        """Start arming. Returns False (and emits arm_refused) if refused."""
        if mode not in self.config.modes:
            raise ValueError(f"unknown mode {mode!r}")
        self.refuse_reason = None
        if self.state != "disarmed":
            self._refuse("not_disarmed", [], mode)
            return False
        open_alarm = [
            z.id
            for z in self.config.sensors.values()
            if z.blocks_arming_when_open
            and self._rt[z.id].value == "open"
            and not self._rt[z.id].manual_bypass
        ]
        if open_alarm:
            self._refuse("alarm_condition", open_alarm, mode)
            return False
        blocked = self._blocking_unavailable(mode)
        if blocked:
            self._refuse("sensor_unavailable", blocked, mode)
            return False

        self.mode = mode
        self._arm_user = user
        exit_delay = self.config.modes[mode].exit_delay
        if exit_delay > 0:
            self.state = "arming"
            self._delay_end = self.now + exit_delay
            self._emit("arming_started", mode=mode, user=user, end=self._delay_end)
            self._set_timer("exit", self._delay_end)
        else:
            self.state = "arming"
            self._finish_arming()
        return True

    def arm_check(self, mode: str) -> list[dict[str, Any]]:
        """Why arming `mode` would be refused right now; an empty list means it would start.

        Same conditions as `arm` and the end of the exit delay, without changing anything. Each entry says the
        reason, the sensor (None when it is not about one) and whether bypassing that sensor would remove it:
        an open fire or gas sensor never can be bypassed.
        """
        if mode not in self.config.modes:
            raise ValueError(f"unknown mode {mode!r}")
        if self.state != "disarmed":
            return [{"reason": "not_disarmed", "sensor": None, "bypassable": False}]
        found: list[dict[str, Any]] = []
        for z in self.config.sensors.values():
            rt = self._rt[z.id]
            if rt.manual_bypass:
                continue
            if z.blocks_arming_when_open and rt.value == "open":
                found.append({"reason": "alarm_condition", "sensor": z.id, "bypassable": z.cls not in ("fire", "gas")})
        for sid in self._blocking_unavailable(mode):
            found.append({"reason": "sensor_unavailable", "sensor": sid, "bypassable": True})
        for z in self.config.sensors.values():
            rt = self._rt[z.id]
            if (z.cls == "intrusion" and mode in z.modes and rt.value == "open"
                    and not rt.manual_bypass and z.at_arm_open == "refuse"):
                found.append({"reason": "sensor_open", "sensor": z.id, "bypassable": True})
        return found

    def disarm(self, user: str | None = None) -> None:
        if self.state == "disarmed":
            return
        if self.state == "triggered":
            self._emit("trigger_ended")
        self._timers.clear()
        resume: list[Sensor] = []
        for zid, rt in self._rt.items():
            if rt.manual_bypass and not self.config.sensors[zid].permanent_bypass:
                rt.manual_bypass = False
                self._emit("sensor_unbypassed", sensor=zid, reason="disarm", user=user)
                resume.append(self.config.sensors[zid])
            rt.auto_bypass = False
            rt.waiting = False
        self._rules.clear()
        self._protected = False
        self.mode = None
        self.cause = None
        self.cause_sensor = None
        self._pending_sensor = None
        self._delay_end = None
        self.refuse_reason = None
        self.state = "disarmed"
        self._emit("disarmed", user=user)
        for sensor in resume:
            self._technical_resume(sensor)

    def bypass(self, sensor_id: str, user: str | None = None) -> bool:
        sensor = self._sensor(sensor_id)
        if sensor.cls in ("fire", "gas"):
            self._emit("bypass_refused", sensor=sensor_id, reason="not_bypassable")
            return False
        self._rt[sensor_id].manual_bypass = True
        self._emit("sensor_bypassed", sensor=sensor_id, user=user)
        self._technical_end(sensor, "bypassed")
        return True

    def unbypass(self, sensor_id: str, user: str | None = None) -> None:
        sensor = self._sensor(sensor_id)
        rt = self._rt[sensor_id]
        if not rt.manual_bypass:
            return
        rt.manual_bypass = False
        if sensor.cls == "intrusion" and rt.value == "open":
            rt.waiting = True  # must clear once before it is monitored again
        self._emit("sensor_unbypassed", sensor=sensor_id, reason="manual", user=user)
        self._technical_resume(sensor)

    def set_sensor(self, sensor_id: str, value: str) -> None:
        """Report the state of a sensor: closed, open or unavailable."""
        if value not in SENSOR_VALUES:
            raise ValueError(f"unknown sensor value {value!r}")
        sensor = self._sensor(sensor_id)
        rt = self._rt[sensor_id]
        prev = rt.value
        if prev == value:
            return
        rt.value = value

        if value == "unavailable":
            self._emit("supervision_lost", sensor=sensor_id)
            if sensor.on_unavailable == "trigger" and self._is_active(sensor):
                self._trigger("fault", sensor_id)
            return

        if prev == "unavailable":
            self._emit("supervision_restored", sensor=sensor_id)

        if value == "closed":
            self._technical_end(sensor, "closed")
            rt.waiting = False
            if rt.auto_bypass:
                rt.auto_bypass = False
                self._emit("sensor_unbypassed", sensor=sensor_id, reason="closed")
            return

        # value == "open": a fault if the sensor is monitored right now
        if self._is_active(sensor):
            self._emit("sensor_faulted", sensor=sensor_id)
            self._on_fault(sensor)

    # ----------------------------------------------------------- persistence

    def next_due(self) -> float | None:
        """Time of the earliest pending timer, so the host can schedule a wake-up."""
        return min((tm[0] for tm in self._timers), default=None)

    def export_state(self) -> dict[str, Any]:
        """JSON-serialisable runtime state (not the config, not the event log).

        Timers are stored with absolute times, so after a restart the host can
        `restore_state` and `advance(now)`: timers that expired during the
        downtime fire then, with their original due time as event time.
        """
        return {
            "version": STATE_VERSION,
            "now": self.now,
            "state": self.state,
            "mode": self.mode,
            "cause": self.cause,
            "cause_sensor": self.cause_sensor,
            "refuse_reason": self.refuse_reason,
            "protected": self._protected,
            "arm_user": self._arm_user,
            "pending_sensor": self._pending_sensor,
            "delay_end": self._delay_end,
            "sensors": {
                zid: {
                    "value": rt.value,
                    "manual_bypass": rt.manual_bypass,
                    "auto_bypass": rt.auto_bypass,
                    "waiting": rt.waiting,
                }
                for zid, rt in self._rt.items()
            },
            "rules": {rid: list(m) for rid, m in self._rules.items()},
            "technical": list(self._technical),
            "timers": [list(tm) for tm in self._timers],
            "seq": self._seq,
        }

    def restore_state(self, data: dict[str, Any]) -> None:
        """Load a state from `export_state`. Raises ValueError if it is unusable;
        the engine is left untouched in that case."""
        try:
            parsed = self._parse_state(_upgrade_legacy_state(data))
        except (KeyError, TypeError, AttributeError) as err:
            raise ValueError(f"invalid state: {err!r}") from None
        (self.now, self.state, self.mode, self.cause, self.cause_sensor,
         self.refuse_reason, self._protected, self._arm_user, self._pending_sensor,
         self._delay_end, sensors, self._rules, self._technical, self._timers,
         self._seq) = parsed
        for zid, rt in self._rt.items():  # sensors missing from the state start closed
            saved = sensors.get(zid)
            rt.value, rt.manual_bypass, rt.auto_bypass, rt.waiting = (
                saved if saved else ("closed", False, False, False)
            )

    def _parse_state(self, data: dict[str, Any]) -> tuple:
        if data["version"] != STATE_VERSION:
            raise ValueError(f"unsupported state version {data['version']}")
        state, mode = data["state"], data["mode"]
        if mode is not None and mode not in self.config.modes:
            raise ValueError(f"unknown mode {mode!r}")
        valid = {"disarmed", "arming", "pending", "triggered"} | {
            f"armed_{m}" for m in self.config.modes
        }
        if state not in valid:
            raise ValueError(f"unknown state {state!r}")
        sensors = {}
        for zid, z in data["sensors"].items():
            if zid not in self.config.sensors:
                continue  # sensor removed from the config since the export
            if z["value"] not in SENSOR_VALUES:
                raise ValueError(f"unknown sensor value {z['value']!r}")
            sensors[zid] = (z["value"], bool(z["manual_bypass"]),
                          bool(z["auto_bypass"]), bool(z["waiting"]))
        rules = {
            rid: [z for z in members if z in self.config.sensors]
            for rid, members in data["rules"].items()
            if rid in self.config.rules
        }
        timers = []
        for due, seq, kind, key in data["timers"]:
            if kind not in TIMER_KINDS:
                raise ValueError(f"unknown timer kind {kind!r}")
            if kind == "rule" and key not in self.config.rules:
                continue
            timers.append((float(due), int(seq), kind, key))
        technical = [z for z in data["technical"] if z in self.config.sensors]
        pending_sensor = data["pending_sensor"]
        if pending_sensor not in self.config.sensors:
            pending_sensor = None
        return (
            float(data["now"]), state, mode, data["cause"], data["cause_sensor"],
            data["refuse_reason"], bool(data["protected"]), data["arm_user"],
            pending_sensor, data["delay_end"], sensors, rules, technical, timers,
            int(data["seq"]),
        )

    # ------------------------------------------------------------- read-only

    def sensor_status(self, sensor_id: str) -> str:
        rt = self._rt[self._sensor(sensor_id).id]
        if rt.value == "unavailable":
            return "unavailable"
        if rt.manual_bypass:
            return "bypassed"
        if rt.auto_bypass:
            return "bypassed_at_arm"
        if rt.waiting:
            return "waiting"
        return rt.value

    def is_bypassed(self, sensor_id: str) -> bool:
        """True if the sensor was bypassed by hand (not automatically at arming)."""
        return self._rt[self._sensor(sensor_id).id].manual_bypass

    def snapshot(self) -> dict[str, Any]:
        mode = self.mode
        return {
            "state": self.state,
            "mode": mode,
            "cause": self.cause,
            "cause_sensor": self.cause_sensor,
            "delay_end": self._delay_end,
            "refuse_reason": self.refuse_reason,
            "open_sensors": [
                z.id
                for z in self.config.sensors.values()
                if self._rt[z.id].value == "open" and z.active_in(mode)
            ],
            "faults": [
                z.id
                for z in self.config.sensors.values()
                if self._rt[z.id].value == "unavailable"
            ],
            "technical_alarms": [
                z.id for z in self.config.sensors.values() if z.id in self._technical
            ],
        }

    # -------------------------------------------------------------- internals

    def _sensor(self, sensor_id: str) -> Sensor:
        try:
            return self.config.sensors[sensor_id]
        except KeyError:
            raise ValueError(f"unknown sensor {sensor_id!r}") from None

    def _is_active(self, sensor: Sensor) -> bool:
        rt = self._rt[sensor.id]
        if rt.manual_bypass or rt.auto_bypass:
            return False
        if sensor.always_on:
            return True
        return self._protected and self.mode in sensor.modes and not rt.waiting

    def _blocking_unavailable(self, mode: str) -> list[str]:
        return [
            z.id
            for z in self.config.sensors.values()
            if z.active_in(mode)
            and self._rt[z.id].value == "unavailable"
            and z.on_unavailable == "block"
            and not self._rt[z.id].manual_bypass
        ]

    def _refuse(self, reason: str, sensors: list[str], mode: str) -> None:
        self.refuse_reason = reason
        self._emit("arm_refused", reason=reason, sensors=sensors, mode=mode)

    def _abort_arming(self, reason: str, sensors: list[str]) -> None:
        mode = self.mode
        self.state = "disarmed"
        self.mode = None
        self._delay_end = None
        self._refuse(reason, sensors, mode or "")

    def _finish_arming(self) -> None:
        mode = self.mode
        assert mode is not None
        blocked = self._blocking_unavailable(mode)
        if blocked:
            self._abort_arming("sensor_unavailable", blocked)
            return

        open_sensors = [
            z
            for z in self.config.sensors.values()
            if z.cls == "intrusion"
            and mode in z.modes
            and self._rt[z.id].value == "open"
            and not self._rt[z.id].manual_bypass
        ]
        refused = [z.id for z in open_sensors if z.at_arm_open == "refuse"]
        if refused:
            self._abort_arming("sensor_open", refused)
            return

        faults: list[Sensor] = []
        for z in open_sensors:
            rt = self._rt[z.id]
            if z.at_arm_open == "bypass":
                rt.auto_bypass = True
                self._emit("sensor_bypassed_at_arm", sensor=z.id, reason="open")
            elif z.at_arm_open == "wait_clear":
                rt.waiting = True
            else:  # pending: treat as a fault right after arming
                faults.append(z)

        # Sensors that are unavailable and configured with on_unavailable: bypass are
        # armed around: bypassed with a notice, monitored again once they close.
        for z in self.config.sensors.values():
            rt = self._rt[z.id]
            if (
                z.on_unavailable == "bypass"
                and z.active_in(mode)
                and rt.value == "unavailable"
                and not rt.manual_bypass
                and not rt.auto_bypass
            ):
                rt.auto_bypass = True
                self._emit("sensor_bypassed_at_arm", sensor=z.id, reason="unavailable")

        self.state = f"armed_{mode}"
        self._protected = True
        self._delay_end = None
        self._emit("armed", mode=mode, user=self._arm_user)
        for z in faults:
            self._emit("sensor_faulted", sensor=z.id)
            self._on_fault(z)

    def _on_fault(self, sensor: Sensor) -> None:
        if sensor.cls in ("fire", "gas"):
            self._trigger(sensor.cls, sensor.id)
            return
        if sensor.cls == "tamper":
            self._trigger("tamper", sensor.id)
            return
        if sensor.cls == "alarm24":
            self._trigger("alarm24", sensor.id)
            return
        if sensor.cls in TECHNICAL_CLASSES:
            self._technical_start(sensor)
            return

        if sensor.rule:
            self._rule_fault(sensor)
            return
        if sensor.type == "instant":
            self._trigger("intrusion", sensor.id)
        elif sensor.type == "delayed":
            self._start_pending(sensor)
        elif self.state != "pending":  # follower: only alarms if it goes first
            self._trigger("intrusion", sensor.id)

    def _technical_start(self, sensor: Sensor) -> None:
        if sensor.id in self._technical:
            return  # already active (e.g. the sensor came back as open)
        self._technical.append(sensor.id)
        self._emit("technical_alarm_started", sensor=sensor.id, cause=sensor.cls)

    def _technical_end(self, sensor: Sensor, reason: str) -> None:
        if sensor.id not in self._technical:
            return
        self._technical.remove(sensor.id)
        self._emit("technical_alarm_ended", sensor=sensor.id, cause=sensor.cls, reason=reason)

    def _technical_resume(self, sensor: Sensor) -> None:
        """A bypass was lifted while the sensor still reports the problem."""
        if sensor.cls in TECHNICAL_CLASSES and self._rt[sensor.id].value == "open":
            self._technical_start(sensor)

    def _rule_fault(self, sensor: Sensor) -> None:
        rule = self.config.rules[sensor.rule]  # type: ignore[index]
        members = self._rules.get(rule.id)
        if members is None:
            members = self._rules[rule.id] = []
            self._set_timer("rule", self.now + rule.window, rule.id)
        if sensor.id in members:
            return  # the same sensor twice does not count as two
        members.append(sensor.id)
        if len(members) >= rule.required:
            confirmed = list(members)
            self._clear_rule(rule.id)
            self._trigger("intrusion", sensor.id, confirmed_by=confirmed)
        else:
            self._emit("sensor_unconfirmed", rule=rule.id, sensor=sensor.id)

    def _clear_rule(self, rule_id: str) -> None:
        self._rules.pop(rule_id, None)
        self._cancel("rule", rule_id)

    def _expire_rule(self, rule_id: str) -> None:
        members = self._rules.pop(rule_id, [])
        if members and self.config.rules[rule_id].escalate:
            self._emit("sensor_unconfirmed_escalated", rule=rule_id, sensors=members)

    def _start_pending(self, sensor: Sensor) -> None:
        if not (self.state.startswith("armed_") or self.state == "pending"):
            return
        delay = sensor.entry_delay_for(self.mode, self.config.default_entry_delay)
        if delay <= 0:
            self._trigger("intrusion", sensor.id)
            return
        end = self.now + delay
        if self.state == "pending":
            assert self._delay_end is not None
            if end < self._delay_end:  # the shortest running delay wins
                self._delay_end = end
                self._pending_sensor = sensor.id
                self._cancel("entry")
                self._set_timer("entry", end)
            return
        self.state = "pending"
        self._delay_end = end
        self._pending_sensor = sensor.id
        self._emit("pending_started", sensor=sensor.id, end=end)
        self._set_timer("entry", end)

    def _trigger(
        self, cause: str, sensor_id: str, confirmed_by: list[str] | None = None
    ) -> None:
        if self.state == "triggered":
            if PRIORITY[cause] > PRIORITY[self.cause or "intrusion"]:
                self.cause = cause
                self.cause_sensor = sensor_id
                self._emit("trigger_cause_changed", cause=cause, sensor=sensor_id)
            return
        self._cancel("entry")
        self._cancel("exit")  # an alarm during arming aborts the arming
        self._pending_sensor = None
        self._delay_end = None
        if not self._protected:
            self.mode = None
        self.state = "triggered"
        self.cause = cause
        self.cause_sensor = sensor_id
        fields: dict[str, Any] = {"cause": cause, "sensor": sensor_id}
        if confirmed_by:
            fields["confirmed_by"] = confirmed_by
        self._emit("triggered", **fields)
        if self.config.trigger_time is not None:
            self._set_timer("trigger_end", self.now + self.config.trigger_time)

    def _end_trigger(self) -> None:
        self._emit("trigger_ended")
        self.cause = None
        self.cause_sensor = None
        self.state = f"armed_{self.mode}" if self._protected else "disarmed"


def _upgrade_legacy_state(data: dict[str, Any]) -> dict[str, Any]:
    """States saved before sensors and rules got their names used "zones" and "groups"."""
    if "zones" not in data:
        return data
    out = dict(data)
    out["sensors"] = out.pop("zones")
    out["rules"] = out.pop("groups", {})
    out["cause_sensor"] = out.pop("cause_zone", None)
    out["pending_sensor"] = out.pop("pending_zone", None)
    out["timers"] = [
        [due, seq, "rule" if kind == "group" else kind, key] for due, seq, kind, key in out.get("timers", [])
    ]
    return out
