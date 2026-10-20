"""Partitions: pure helpers, no Home Assistant imports.

A partition is a part of the house with its own modes, delays and arm state. Every partition runs its own
engine on its own `Config`. These helpers

* split one raw config into one `Config` per partition (`split_config`): the intrusion sensors of a partition,
  plus every safety sensor (fire, gas, water, tamper, 24 hour), which watch in every partition;
* combine the states of all partitions into the state of the "Alles" (all) entity (`aggregate`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .model import Config, ConfigError

# Highest first. The Home Assistant state of the combined entity is the highest state of any partition.
PRIORITY = ("triggered", "pending", "arming", "armed", "disarmed")
MIXED = "mixed"


def _rank(state: str) -> int:
    base = "armed" if state.startswith("armed") else state
    try:
        return PRIORITY.index(base)
    except ValueError:
        return len(PRIORITY)


@dataclass(frozen=True)
class Combined:
    state: str  # the common state, or "mixed"
    ha_state: str  # the highest state of any partition (armed_away, ...)
    mixed: bool
    partitions: Mapping[str, str]


def aggregate(states: Mapping[str, str]) -> Combined:
    """The combined state of partition id -> engine state."""
    if not states:
        return Combined("disarmed", "disarmed", False, {})
    values = set(states.values())
    mixed = len(values) > 1
    top = min(states.values(), key=_rank)  # the first of the highest rank: an armed state keeps its mode
    return Combined(MIXED if mixed else top, top, mixed, dict(states))


def split_config(raw: Mapping[str, Any], partition_of: Mapping[str, str], partitions: Iterable[str]) -> dict[str, Config]:
    """One `Config` per partition from the raw config dict.

    `raw` is the dict `Config.from_dict` takes, with the sensors of all partitions. `partition_of` maps an
    intrusion sensor id to its partition (a sensor that is missing belongs to the first partition). Per
    partition, `raw["partitions"][pid]` may override `modes`, `default_entry_delay` and `trigger_time`.
    A confirmation rule must keep all its sensors in one partition."""
    ids = list(partitions)
    if not ids:
        raise ConfigError("at least one partition is required")
    sensors = raw.get("sensors") or {}
    overrides = raw.get("partitions") or {}
    first = ids[0]

    def home(sid: str) -> str | None:
        if (sensors.get(sid) or {}).get("cls", "intrusion") != "intrusion":
            return None  # a safety sensor: in every partition
        pid = partition_of.get(sid, first)
        return pid if pid in ids else first

    for rid, body in (raw.get("rules") or {}).items():
        homes = {home(s) for s in body.get("sensors", [])}
        if len(homes) > 1:
            raise ConfigError(f"rule {rid}: its sensors must be in one partition")

    out: dict[str, Config] = {}
    for pid in ids:
        part = dict(raw)
        part.pop("partitions", None)
        part.update(overrides.get(pid) or {})
        modes = set(part.get("modes") or {})
        mine: dict[str, Any] = {}
        for sid, body in sensors.items():
            if home(sid) not in (None, pid):
                continue
            body = dict(body or {})
            if body.get("cls", "intrusion") == "intrusion":
                # a partition can have fewer modes than the house: the sensor only watches in the modes it has
                body["modes"] = [m for m in body.get("modes", ()) if m in modes]
                if not body["modes"]:
                    continue
                if isinstance(body.get("entry_delay"), Mapping):
                    body["entry_delay"] = {m: v for m, v in body["entry_delay"].items() if m in modes}
            mine[sid] = body
        part["sensors"] = mine
        part["rules"] = {r: b for r, b in (raw.get("rules") or {}).items()
                         if b.get("sensors") and all(s in mine for s in b["sensors"])}
        out[pid] = Config.from_dict(part)
    return out
