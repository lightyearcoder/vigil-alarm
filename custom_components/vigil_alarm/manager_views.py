"""What the manager shows: the status of sensors, the rows of the panels and the snapshot."""

from __future__ import annotations

import logging
from typing import Any

from .const import (
    CONF_ENTITY_ID,
    SUBENTRY_SENSOR,
)
from .items import Item, items_of
from .manager_config import _bypass_rank

_LOGGER = logging.getLogger(f"{__package__}.manager")


class ViewsMixin:
    """The views of VigilManager (status of sensors, panel rows, snapshot)."""


    def sensor_status(self, sensor_id: str) -> str:
        return self.engine_for_sensor(sensor_id).sensor_status(sensor_id)

    def sensor_is_bypassed(self, sensor_id: str) -> bool:
        return self.engine_for_sensor(sensor_id).is_bypassed(sensor_id)

    def sensor_items(self) -> list[Item]:
        return [s for s in items_of(self.entry).values() if s.subentry_type == SUBENTRY_SENSOR]

    def panel_rows(self, partitions: list[str], scope: str = "all") -> str:
        """The sensor list of a panel that may use several partitions: "name|entity|status|1 or 0|partition" per
        line. A safety sensor watches in every partition and is listed once, with no partition. `scope` "partition"
        leaves those always-on sensors out and "always" lists only them (0.6.10: they are shown apart, not under
        every partition)."""
        rows = []
        seen: set[str] = set()
        for pid in partitions:
            part = self.partitions[pid]
            for s in self.sensor_items():
                sid = s.subentry_id
                sensor = part.config.sensors.get(sid)
                if sensor is None or sid in seen:
                    continue
                if sensor.cls != "intrusion":
                    seen.add(sid)
                status = part.engine.sensor_status(sid)
                bypassable = sensor.cls not in ("fire", "gas")
                homes = [q for q in self.partitions.values() if sid in q.config.sensors]  # a tamper contact has one
                rows.append((
                    _bypass_rank(status, bypassable), s.title.lower(),
                    "|".join((s.title.replace("|", "/").replace("\n", " "), s.data[CONF_ENTITY_ID], status,
                              "1" if bypassable else "0", pid if sensor.cls == "intrusion" or len(homes) == 1 else "")),
                ))
        if scope != "all":
            keep_always = scope == "always"
            rows = [r for r in rows if (r[2].rsplit("|", 1)[-1] == "") == keep_always]
        return "\n".join(row for _rank, _name, row in sorted(rows))

    def snapshot(self, partition: str | None = None) -> dict[str, Any]:
        """The state of one partition (none: the first) for entities, panels and dashboards."""
        part = self.partition(partition)
        engine, config = part.engine, part.config
        snap = engine.snapshot()
        names = self._sensor_name
        for key in ("open_sensors", "faults", "technical_alarms"):
            snap[key] = [names.get(z, z) for z in snap[key]]
        snap["cause_sensor"] = names.get(snap["cause_sensor"], snap["cause_sensor"])
        snap["problems"] = self.supervisor.problems()
        snap["last_event"] = self.last_event
        snap["partition"] = part.id
        snap["partition_name"] = part.name
        snap["open_now"] = [
            names.get(z, z) for z in config.sensors if engine.sensor_status(z) in ("open", "waiting")
        ]
        snap["open_now_count"] = len(snap["open_now"])
        # One line per sensor, "name|entity|status|1 or 0 (bypassable)": plain text, because a display
        # (ESPHome) only reads plain attribute values, not lists. The sensors that come first for a bypass come
        # first in the list, so nobody has to page through closed doors to find the open one.
        rows = []
        for s in self.sensor_items():
            if s.subentry_id not in config.sensors:
                continue
            status = engine.sensor_status(s.subentry_id)
            bypassable = config.sensors[s.subentry_id].cls not in ("fire", "gas")
            rows.append((
                _bypass_rank(status, bypassable), s.title.lower(),
                "|".join((s.title.replace("|", "/").replace("\n", " "), s.data[CONF_ENTITY_ID], status,
                          "1" if bypassable else "0")),
            ))
        snap["panel_sensors"] = "\n".join(row for _rank, _name, row in sorted(rows))
        snap["bypassed_sensors"] = [
            names.get(z, z) for z in config.sensors
            if engine.sensor_status(z) in ("bypassed", "bypassed_at_arm")
        ]
        return snap

