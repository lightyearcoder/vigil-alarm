"""Building the engine configuration from the entry, and the parts of the house (partitions)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_OFF

from .items import Item, items_of
from .const import (
    CONF_AT_ARM_OPEN,
    CONF_PERMANENT_BYPASS,
    CONF_CLS,
    CONF_DEFAULT_ENTRY_DELAY,
    CONF_ENTRY_DELAY,
    CONF_ESCALATE,
    CONF_EXIT_DELAY,
    CONF_GAS_TYPE,
    CONF_MODES,
    CONF_COMPANION_OF,
    CONF_PARTITION,
    PRIMARY_PARTITION,
    SUBENTRY_PARTITION,
    DEFAULT_MODES,
    MODES,
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
    SUBENTRY_RULE,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
)
from .vigil_core import Config, ConfigError, Engine


SIGNAL_UPDATE = f"{DOMAIN}_update_{{}}"
SIGNAL_EVENT = f"{DOMAIN}_event_{{}}"
ROUTINE_EVENTS = {"selftest_checked", "selftest_reminder", "selftest_siren_tested", "startup_settled", "handler_test", "handler_test_done"}


def partition_ids(entry: ConfigEntry, extra: dict[str, Item] | None = None) -> list[str]:
    """The first (implicit) partition, then the partition items in stored order."""
    subentries = dict(items_of(entry))
    subentries.update(extra or {})
    return [PRIMARY_PARTITION] + [i for i, sub in subentries.items() if sub.subentry_type == SUBENTRY_PARTITION]


def partition_data(entry: ConfigEntry, pid: str, extra: dict[str, Item] | None = None) -> Mapping[str, Any]:
    """The settings of a partition: the entry data for the first one, the item data for the others."""
    if pid == PRIMARY_PARTITION:
        return entry.data
    subentries = dict(items_of(entry))
    subentries.update(extra or {})
    return subentries[pid].data


def all_enabled_modes(entry: Any, extra: dict[str, Item] | None = None) -> list[str]:
    """The modes any partition has, in the usual order: what a sensor group, a user or a panel can pick from."""
    chosen: set[str] = set()
    for pid in partition_ids(entry, extra):
        chosen.update(partition_data(entry, pid, extra).get(CONF_MODES, []) if pid == PRIMARY_PARTITION
                      else partition_data(entry, pid, extra).get(CONF_MODES, DEFAULT_MODES))
    return [m for m in MODES if m in chosen]


def build_configs(entry: ConfigEntry, extra: dict[str, Item] | None = None) -> dict[str, Config]:
    """Build the core configuration of every partition from a config entry and its items.

    A partition has the intrusion sensors that say so (a sensor that names no partition is in the first), and
    every safety sensor (fire, gas, water, tamper, 24 hour): those watch in every partition.
    `extra` can hold an item that is not saved yet (used to validate a flow). Raises ConfigError.
    """
    subentries = dict(items_of(entry))
    subentries.update(extra or {})
    pids = partition_ids(entry, extra)
    # A sensor group says in which modes its sensors are watching; the core only sees the result.
    group_modes = {
        gid: set(sub.data.get(CONF_GROUP_MODES, []))
        for gid, sub in subentries.items()
        if sub.subentry_type == SUBENTRY_SENSOR_GROUP
    }
    all_sensor_ids = {sid for sid, sub in subentries.items() if sub.subentry_type == SUBENTRY_SENSOR}
    out: dict[str, Config] = {}
    for pid in pids:
        pdata = partition_data(entry, pid, extra)
        enabled = list(pdata.get(CONF_MODES, DEFAULT_MODES if pid != PRIMARY_PARTITION else []))
        modes = {
            m: {"exit_delay": pdata.get(CONF_EXIT_DELAY.format(mode=m), DEFAULT_EXIT_DELAY.get(m, 0))}
            for m in enabled
        }
        sensors: dict[str, Any] = {}
        rules: dict[str, Any] = {}
        for sid, sub in subentries.items():
            d = sub.data
            if sub.subentry_type == SUBENTRY_SENSOR:
                owner = d
                parent = subentries.get(d.get(CONF_COMPANION_OF))
                if d[CONF_CLS] == "tamper" and parent is not None and parent.subentry_type == SUBENTRY_SENSOR:
                    owner = parent.data  # the tamper contact of a sensor is in its partition (one of a siren watches everywhere)
                # an intrusion sensor is in one partition; so is a tamper contact (of a sensor, or one that was given a
                # partition); every other safety sensor watches in all of them
                bound = owner[CONF_CLS] == "intrusion" or (owner[CONF_CLS] == "tamper" and bool(owner.get(CONF_PARTITION)))
                if bound and (owner.get(CONF_PARTITION) or PRIMARY_PARTITION) not in pids:
                    home = PRIMARY_PARTITION  # its partition was removed
                else:
                    home = owner.get(CONF_PARTITION) or PRIMARY_PARTITION
                if bound and home != pid:
                    continue
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
                if d.get(CONF_PERMANENT_BYPASS) and d[CONF_CLS] not in ("fire", "gas"):
                    body["permanent_bypass"] = True
                if d[CONF_CLS] == "gas":
                    body["gas_type"] = d.get(CONF_GAS_TYPE, "other")
                body = {k: v for k, v in body.items() if v is not None}
                sensors[sid] = body
        for sid, sub in subentries.items():
            d = sub.data
            unknown = pid == PRIMARY_PARTITION and sub.subentry_type == SUBENTRY_RULE and any(
                z not in all_sensor_ids for z in d[CONF_SENSORS])  # left in, so the core names the missing sensor
            if sub.subentry_type == SUBENTRY_RULE and (unknown or all(z in sensors for z in d[CONF_SENSORS])):
                rules[sid] = {
                    "sensors": list(d[CONF_SENSORS]),
                    "required": d.get(CONF_REQUIRED, 2),
                    "window": d.get(CONF_WINDOW, 60),
                    "escalate": d.get(CONF_ESCALATE, False),
                }
            elif sub.subentry_type == SUBENTRY_RULE and any(z in sensors for z in d[CONF_SENSORS]):
                raise ConfigError(f"rule {sub.title}: its sensors must be in one partition")
        raw: dict[str, Any] = {
            "version": 1,
            "default_entry_delay": pdata.get(CONF_DEFAULT_ENTRY_DELAY, 30),
            "modes": modes,
            "sensors": sensors,
            "rules": rules,
        }
        if pdata.get(CONF_TRIGGER_TIME):
            raw["trigger_time"] = pdata[CONF_TRIGGER_TIME]
        try:
            out[pid] = Config.from_dict(raw)
        except ConfigError as err:
            if pid != PRIMARY_PARTITION:
                raise ConfigError(f"partition {subentries[pid].title}: {err}") from err
            raise
    return out


def build_config(entry: ConfigEntry, extra: dict[str, Item] | None = None) -> Config:
    """The configuration of the first partition (all partitions are checked). Raises ConfigError."""
    return build_configs(entry, extra)[PRIMARY_PARTITION]


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


@dataclass
class Partition:
    """One part of the house: its own config and its own engine."""

    id: str
    name: str
    config: Config
    engine: Engine
    primary: bool = False
    safety_trigger: bool = False  # the alarm it is in came from a safety sensor (reported by the first partition)


