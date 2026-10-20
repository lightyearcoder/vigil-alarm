"""The event log: everything Vigil publishes as an event, kept for a while and exportable.

Home Assistant's own logbook keeps ten days by default; this log keeps what the settings say
(90 days to start with). It holds no codes. Times are RFC 3339 in UTC, one entry per line when
exported as JSON Lines, or a table as CSV (RFC 4180), so any standard tool can read it.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import CONF_LOG_RETENTION_DAYS, DEFAULT_LOG_RETENTION_DAYS, DOMAIN

if TYPE_CHECKING:
    from .manager import VigilManager

STORAGE_VERSION = 1
SAVE_DELAY = 15  # seconds; Home Assistant also writes it when it stops
MAX_ENTRIES = 50_000  # a safety limit next to the number of days
FIELDS = ("time", "event", "partition", "source", "user", "item", "result", "detail")
_NEVER = {"code", "code_hash", "code_salt", "duress_hash", "duress_salt", "tags", "tag"}  # events hold none of these; belt and braces
_SHOWN = {"t", "type", "source", "user", "sensor", "sensor_name", "siren", "name", "rule", "reason", "error", "cause", "mode"}


def _plain(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple, set)):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    return str(value)


def rfc3339(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class EventLog:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, manager: VigilManager) -> None:
        self.hass = hass
        self.entry = entry
        self.manager = manager
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.log.{entry.entry_id}")
        self.entries: list[dict[str, Any]] = []  # oldest first

    # -------------------------------------------------------------- storing
    async def async_load(self) -> None:
        data = await self._store.async_load()
        stored = list((data or {}).get("entries", []))
        self.entries = stored + self.entries  # events that came in while loading come after
        self._prune()

    async def async_flush(self) -> None:
        await self._store.async_save({"entries": self.entries})

    async def async_remove(self) -> None:
        await self._store.async_remove()

    def _schedule_save(self) -> None:
        self._store.async_delay_save(lambda: {"entries": self.entries}, SAVE_DELAY)

    @property
    def retention_days(self) -> int:
        return int(self.entry.data.get(CONF_LOG_RETENTION_DAYS, DEFAULT_LOG_RETENTION_DAYS))

    def _prune(self) -> None:
        cutoff = rfc3339((datetime.now(UTC) - timedelta(days=self.retention_days)).timestamp())
        start = 0
        while start < len(self.entries) and self.entries[start]["time"] < cutoff:  # RFC 3339 UTC sorts as text
            start += 1
        if start or len(self.entries) > MAX_ENTRIES:
            self.entries = self.entries[max(start, len(self.entries) - MAX_ENTRIES):]

    # --------------------------------------------------------------- adding
    def _entry(self, event: dict[str, Any]) -> dict[str, Any]:
        names = self.manager._sensor_name
        item = event.get("sensor_name") or event.get("siren") or event.get("name")
        if not item and event.get("rule"):
            item = self.manager.rule_name(event["rule"])
        extra = {k: _plain(v) for k, v in event.items() if k not in _SHOWN and k not in _NEVER
                 and k not in ("partition", "partition_name")}
        partition = None
        if pid := event.get("partition"):  # the events of an alarm say which partition they are about
            part = self.manager.partitions.get(pid)
            partition = event.get("partition_name") or (part.name if part else None)
            sensor = self.manager.config.sensors.get(event.get("sensor") or "")
            if sensor is not None and sensor.cls != "intrusion" and sum(
                    event["sensor"] in q.config.sensors for q in self.manager.partitions.values()) > 1:
                partition = None  # a safety sensor that watches in every partition
        if event.get("sensors"):
            extra["sensors"] = [names.get(s, s) for s in event["sensors"]]
        # "Edwin (vigil-panel-garage)" is kept as two facts: the user and where it was done
        user, via = self.manager._actor_parts.get(event.get("user") or "", (event.get("user"), None))
        return {
            "time": rfc3339(event.get("t") or datetime.now(UTC).timestamp()),
            "event": event.get("type"),
            "partition": partition,
            "source": event.get("source") or via,
            "user": user,
            "item": item,
            "result": event.get("reason") or event.get("error") or event.get("cause") or event.get("mode"),
            "detail": extra or None,
        }

    def add(self, event: dict[str, Any]) -> None:
        self.entries.append(self._entry(event))
        self._prune()
        self._schedule_save()

    # -------------------------------------------------------------- reading
    def recent(self, limit: int = 200) -> list[dict[str, Any]]:
        return list(reversed(self.entries[-limit:]))  # newest first

    def export(self, fmt: str) -> tuple[str, str, str]:
        """(file name, media type, text) of the whole log, oldest first."""
        stamp = datetime.now(UTC).strftime("%Y%m%d")
        if fmt == "csv":
            out = io.StringIO(newline="")
            writer = csv.writer(out, lineterminator="\r\n")  # RFC 4180
            writer.writerow(FIELDS)
            for e in self.entries:
                writer.writerow(
                    [json.dumps(e["detail"], ensure_ascii=False) if k == "detail" and e.get(k) else (e.get(k) or "") for k in FIELDS]
                )
            return f"vigil-alarm-log-{stamp}.csv", "text/csv", out.getvalue()
        lines = [json.dumps({k: e.get(k) for k in FIELDS if e.get(k) is not None}, ensure_ascii=False) for e in self.entries]
        return f"vigil-alarm-log-{stamp}.jsonl", "application/x-ndjson", "\n".join(lines) + ("\n" if lines else "")
