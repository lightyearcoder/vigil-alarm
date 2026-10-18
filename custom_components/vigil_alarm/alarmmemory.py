"""The alarm memory: what the last alarm was, and the path the intruder took.

From the moment an entry delay starts (or an alarm goes off) until the alarm is disarmed, every sensor that opens is
written down with the time, the room it is in and whether it counted for the alarm. That includes sensors that do
not count in the armed mode, and sensors that are bypassed: for the path through the house all of them tell
something. The memory stays until someone clears it (no code needed) or until the next alarm replaces it.

An entry delay that ends in a disarm is not an alarm: that record is thrown away.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store

from .const import ALARM_PATH_MAX, DOMAIN

if TYPE_CHECKING:
    from .manager import VigilManager

STORAGE_VERSION = 1
SAVE_DELAY = 1.0
SAME_SENSOR_WITHIN = 10.0  # seconds: a motion sensor that flickers is one step in the path, with a count


def alarmmemory_store_key(entry_id: str) -> str:
    return f"{DOMAIN}.alarmmemory.{entry_id}"


class AlarmMemory:
    def __init__(self, hass: HomeAssistant, manager: VigilManager) -> None:
        self.hass = hass
        self.manager = manager
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, alarmmemory_store_key(manager.entry.entry_id))
        self.record: dict[str, Any] | None = None  # the alarm that is remembered
        self._draft: dict[str, Any] | None = None  # an entry delay that may still become an alarm
        self._faulted: str | None = None  # the sensor whose `sensor_faulted` was just seen (it counted)

    # ------------------------------------------------------------- storing
    async def async_load(self) -> None:
        stored = await self._store.async_load()
        self.record = (stored or {}).get("record")
        engine = self.manager.engine
        if self.record and self.record.get("recording") and engine.state == "disarmed":
            self.record["recording"] = False  # it was disarmed while Home Assistant was off

    async def async_flush(self) -> None:
        await self._store.async_save({"record": self.record})

    async def async_remove(self) -> None:
        await self._store.async_remove()

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"record": self.record}, SAVE_DELAY)

    @callback
    def stop(self) -> None:
        pass

    # ------------------------------------------------------------- reading
    @property
    def recording(self) -> bool:
        return bool(self.record and self.record.get("recording"))

    @property
    def started(self) -> float | None:
        return self.record["started"] if self.record else None

    def view(self, *, path: bool = True) -> dict[str, Any] | None:
        """For the panel and the card. The path is in the order it happened."""
        if not self.record:
            return None
        out = {k: v for k, v in self.record.items() if k != "path"}
        out["path"] = list(self.record["path"]) if path else []
        out["steps"] = len(self.record["path"])
        return out

    def attributes(self) -> dict[str, Any]:
        """A short version for the state attributes: the full path would make every state change large."""
        rec = self.record
        if not rec:
            return {"last_alarm": None}
        tail = rec["path"][-8:]
        return {
            "last_alarm": {
                "time": rec["started"],
                "cause": rec.get("cause"),
                "sensor": rec.get("sensor_name"),
                "recording": bool(rec.get("recording")),
                "cancelled": bool(rec.get("cancelled")),
                "steps": len(rec["path"]),
                "path": [f"{s['name']} ({s['area']})" if s.get("area") else s["name"] for s in tail],
            }
        }

    # ------------------------------------------------------------- feeding
    def on_event(self, event: dict[str, Any]) -> None:
        """Every engine event (not during practice)."""
        kind = event.get("type")
        now = event.get("t") or self.manager._wall()
        if kind == "sensor_faulted":
            self._faulted = event.get("sensor")
        elif kind == "pending_started" and not self.recording and self._draft is None:
            self._draft = self._new(now, event)
        elif kind == "triggered":
            if self.recording:
                self.record["retriggers"] = self.record.get("retriggers", 0) + 1  # type: ignore[index]
            else:
                self.record = self._draft or self._new(now, event)
                self._draft = None
                self.record.update(
                    started=now, cause=event.get("cause"), sensor=event.get("sensor"),
                    sensor_name=event.get("sensor_name"), recording=True, cancelled=False,
                )
            self._save()
        elif kind == "disarmed":
            self._draft = None
            if self.recording:
                self.record.update(recording=False, ended=now, ended_by=event.get("user"))  # type: ignore[union-attr]
                self._save()

    def _new(self, now: float, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "started": now, "cause": None, "sensor": event.get("sensor"), "sensor_name": event.get("sensor_name"),
            "recording": False, "cancelled": False, "ended": None, "ended_by": None, "path": [],
        }

    def note(self, sensor_id: str, value: str) -> None:
        """A sensor changed. Called right after the engine has seen it."""
        counted = self._faulted == sensor_id
        self._faulted = None
        if value != "open":
            return
        rec = self.record if self.recording else self._draft
        if rec is None:
            return
        now = self.manager._wall()
        path: list[dict[str, Any]] = rec["path"]
        for step in reversed(path):
            if step["sensor"] == sensor_id:
                if now - step["last"] <= SAME_SENSOR_WITHIN:
                    step["last"] = now
                    step["n"] = step.get("n", 1) + 1
                    self._save()
                    return
                break
        if len(path) >= ALARM_PATH_MAX:
            return
        name = self.manager._sensor_name.get(sensor_id, sensor_id)
        path.append({
            "t": now, "last": now, "n": 1, "sensor": sensor_id, "name": name,
            "area": self.area_of(sensor_id), "counted": counted,
        })
        if rec is self.record:
            self._save()
            if not counted:  # a sensor that counted is in the log as `sensor_faulted` already
                self.manager.publish(
                    "alarm_sensor_seen", sensor=sensor_id, sensor_name=name, area=path[-1]["area"],
                )

    def area_of(self, sensor_id: str) -> str | None:
        """The room of the sensor, from Home Assistant's own areas."""
        entity_id = self.manager._sensor_entity.get(sensor_id)
        if not entity_id:
            return None
        entity = er.async_get(self.hass).async_get(entity_id)
        if entity is None:
            return None
        area_id = entity.area_id
        if not area_id and entity.device_id:
            device = dr.async_get(self.hass).async_get(entity.device_id)
            area_id = device.area_id if device else None
        area = ar.async_get(self.hass).async_get_area(area_id) if area_id else None
        return area.name if area else None

    def mark_cancelled(self) -> None:
        if self.record:
            self.record["cancelled"] = True
            self._save()

    def clear(self) -> bool:
        """Forget the last alarm. While an alarm is still going on the record is kept."""
        if self.recording or self.record is None:
            return False
        self.record = None
        self._save()
        return True
