"""Configuration model of the alarm core.

Pure Python, no Home Assistant imports. The configuration is serialisable
(`Config.to_dict`) and versioned, so a future device implementation (ESPHome)
can read the same data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA_VERSION = 1

CLASSES = ("intrusion", "fire", "gas", "tamper", "water")
SENSOR_TYPES = ("instant", "delayed", "follower")
GAS_TYPES = ("co", "natural_gas", "lpg", "other")
AT_ARM_OPEN = ("wait_clear", "bypass", "refuse", "pending")
ON_UNAVAILABLE = ("block", "notify", "trigger", "bypass")
# Default reaction when a sensor becomes unavailable, per class. A broken smoke
# or gas detector says nothing about intrusion, so it must not block arming.
DEFAULT_ON_UNAVAILABLE = {
    "intrusion": "block",
    "tamper": "block",
    "fire": "notify",
    "gas": "notify",
    "water": "notify",
}


class ConfigError(ValueError):
    """The configuration is invalid."""


@dataclass(frozen=True)
class Sensor:
    id: str
    cls: str = "intrusion"
    type: str = "instant"  # only meaningful for the intrusion class
    modes: tuple[str, ...] = ()  # modes in which an intrusion sensor is active
    entry_delay: float | Mapping[str, float] | None = None
    at_arm_open: str = "bypass"
    on_unavailable: str = "block"
    gas_type: str | None = None
    rule: str | None = None

    @property
    def always_on(self) -> bool:
        return self.cls != "intrusion"

    @property
    def blocks_arming_when_open(self) -> bool:
        """An open fire, gas or tamper sensor is an alarm condition; water is not."""
        return self.cls in ("fire", "gas", "tamper")

    def active_in(self, mode: str | None) -> bool:
        """Is this sensor part of the given mode (always-on sensors always are)?"""
        return self.always_on or (mode is not None and mode in self.modes)

    def entry_delay_for(self, mode: str | None, default: float) -> float:
        if self.entry_delay is None:
            return default
        if isinstance(self.entry_delay, Mapping):
            return float(self.entry_delay.get(mode, default))
        return float(self.entry_delay)


@dataclass(frozen=True)
class Rule:
    id: str
    sensors: tuple[str, ...]
    required: int = 2
    window: float = 60.0
    escalate: bool = False


@dataclass(frozen=True)
class ModeConfig:
    name: str
    exit_delay: float = 0.0


@dataclass(frozen=True)
class Config:
    modes: Mapping[str, ModeConfig]
    sensors: Mapping[str, Sensor]
    rules: Mapping[str, Rule]
    default_entry_delay: float = 30.0
    trigger_time: float | None = None  # None: stays triggered until disarmed

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Config":
        version = data.get("version", SCHEMA_VERSION)
        if version != SCHEMA_VERSION:
            raise ConfigError(f"unsupported config version {version}")

        modes = _parse_modes(data.get("modes") or {})
        rules_raw = data.get("rules") or {}
        sensor_rule = _sensor_rule_map(rules_raw)
        sensors = _parse_sensors(data.get("sensors") or {}, modes, sensor_rule)
        rules = _parse_rules(rules_raw, sensors)

        default_entry = _non_negative(
            data.get("default_entry_delay", 30.0), "default_entry_delay"
        )
        trigger_time = data.get("trigger_time")
        if trigger_time is not None:
            trigger_time = _non_negative(trigger_time, "trigger_time")
            if trigger_time == 0:
                raise ConfigError("trigger_time must be > 0 (or omitted)")
        return cls(modes, sensors, rules, default_entry, trigger_time)

    def to_dict(self) -> dict[str, Any]:
        sensors: dict[str, Any] = {}
        for z in self.sensors.values():
            entry: dict[str, Any] = {"cls": z.cls}
            if z.cls == "intrusion":
                entry.update(
                    type=z.type,
                    modes=list(z.modes),
                    at_arm_open=z.at_arm_open,
                )
                if z.entry_delay is not None:
                    entry["entry_delay"] = (
                        dict(z.entry_delay)
                        if isinstance(z.entry_delay, Mapping)
                        else z.entry_delay
                    )
            if z.gas_type:
                entry["gas_type"] = z.gas_type
            entry["on_unavailable"] = z.on_unavailable
            sensors[z.id] = entry
        out: dict[str, Any] = {
            "version": SCHEMA_VERSION,
            "default_entry_delay": self.default_entry_delay,
            "modes": {m.name: {"exit_delay": m.exit_delay} for m in self.modes.values()},
            "sensors": sensors,
            "rules": {
                g.id: {
                    "sensors": list(g.sensors),
                    "required": g.required,
                    "window": g.window,
                    "escalate": g.escalate,
                }
                for g in self.rules.values()
            },
        }
        if self.trigger_time is not None:
            out["trigger_time"] = self.trigger_time
        return out


def _non_negative(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ConfigError(f"{name} must be a number") from None
    if number < 0:
        raise ConfigError(f"{name} must be >= 0")
    return number


def _parse_modes(raw: Mapping[str, Any]) -> dict[str, ModeConfig]:
    if not raw:
        raise ConfigError("at least one mode is required")
    modes: dict[str, ModeConfig] = {}
    for name, body in raw.items():
        body = body or {}
        exit_delay = _non_negative(body.get("exit_delay", 0), f"modes.{name}.exit_delay")
        modes[name] = ModeConfig(name, exit_delay)
    return modes


def _sensor_rule_map(rules_raw: Mapping[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for rid, body in rules_raw.items():
        for zid in body.get("sensors", []):
            if zid in mapping:
                raise ConfigError(
                    f"sensor {zid} is in more than one rule ({mapping[zid]}, {rid})"
                )
            mapping[zid] = rid
    return mapping


def _parse_sensors(
    raw: Mapping[str, Any],
    modes: Mapping[str, ModeConfig],
    sensor_rule: Mapping[str, str],
) -> dict[str, Sensor]:
    sensors: dict[str, Sensor] = {}
    for zid, body in raw.items():
        body = body or {}
        cls = body.get("cls", "intrusion")
        if cls not in CLASSES:
            raise ConfigError(f"sensor {zid}: unknown class {cls!r}")
        ztype = body.get("type", "instant")
        if cls == "intrusion" and ztype not in SENSOR_TYPES:
            raise ConfigError(f"sensor {zid}: unknown type {ztype!r}")
        sensor_modes = tuple(body.get("modes", ()))
        if cls == "intrusion":
            if not sensor_modes:
                raise ConfigError(f"sensor {zid}: an intrusion sensor needs at least one mode")
            for m in sensor_modes:
                if m not in modes:
                    raise ConfigError(f"sensor {zid}: unknown mode {m!r}")
        at_arm_open = body.get("at_arm_open", "bypass")
        if at_arm_open not in AT_ARM_OPEN:
            raise ConfigError(f"sensor {zid}: unknown at_arm_open {at_arm_open!r}")
        on_unavailable = body.get("on_unavailable", DEFAULT_ON_UNAVAILABLE[cls])
        if on_unavailable not in ON_UNAVAILABLE:
            raise ConfigError(f"sensor {zid}: unknown on_unavailable {on_unavailable!r}")
        if on_unavailable == "bypass" and cls in ("fire", "gas"):
            raise ConfigError(
                f"sensor {zid}: fire and gas sensors cannot be bypassed (on_unavailable: bypass)"
            )
        gas_type = body.get("gas_type")
        if cls == "gas":
            gas_type = gas_type or "other"
            if gas_type not in GAS_TYPES:
                raise ConfigError(f"sensor {zid}: unknown gas_type {gas_type!r}")
        elif gas_type is not None:
            raise ConfigError(f"sensor {zid}: gas_type is only valid for class gas")
        entry_delay = body.get("entry_delay")
        if isinstance(entry_delay, Mapping):
            for m, v in entry_delay.items():
                if m not in modes:
                    raise ConfigError(f"sensor {zid}: entry_delay for unknown mode {m!r}")
                _non_negative(v, f"sensor {zid} entry_delay.{m}")
            entry_delay = dict(entry_delay)
        elif entry_delay is not None:
            entry_delay = _non_negative(entry_delay, f"sensor {zid} entry_delay")
        sensors[zid] = Sensor(
            id=zid,
            cls=cls,
            type=ztype if cls == "intrusion" else "instant",
            modes=sensor_modes if cls == "intrusion" else (),
            entry_delay=entry_delay,
            at_arm_open=at_arm_open,
            on_unavailable=on_unavailable,
            gas_type=gas_type,
            rule=sensor_rule.get(zid),
        )
    return sensors


def _parse_rules(raw: Mapping[str, Any], sensors: Mapping[str, Sensor]) -> dict[str, Rule]:
    rules: dict[str, Rule] = {}
    for rid, body in raw.items():
        members = tuple(body.get("sensors", ()))
        for zid in members:
            sensor = sensors.get(zid)
            if sensor is None:
                raise ConfigError(f"rule {rid}: unknown sensor {zid!r}")
            if sensor.cls != "intrusion":
                raise ConfigError(
                    f"rule {rid}: sensor {zid} is class {sensor.cls}; "
                    "confirmation rules are intrusion-only (life safety and technical alarms must not wait)"
                )
            if sensor.type != "instant":
                raise ConfigError(f"rule {rid}: sensor {zid} must be of type instant")
        required = int(body.get("required", 2))
        if required < 2 or required > len(members):
            raise ConfigError(
                f"rule {rid}: required must be between 2 and the number of sensors"
            )
        window = float(body.get("window", 60))
        if window <= 0:
            raise ConfigError(f"rule {rid}: window must be > 0")
        rules[rid] = Rule(rid, members, required, window, bool(body.get("escalate", False)))
    return rules
