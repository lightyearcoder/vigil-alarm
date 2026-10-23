"""Sensors that appeared in Home Assistant after Vigil last looked: "new sensors found".

Vigil keeps the entities it has already offered (added, or set aside with *Not now*). What the discovery
finds beyond that is new. The first time (an update, or a first start) everything that exists is the
baseline when the alarm already has sensors, so an update does not announce your whole house; with no
sensors at all everything counts as new, and the set-up wizard shows it.

Nothing is added by itself: this only counts, and the panel opens the list of new ones.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store

from .const import DOMAIN, SUBENTRY_SENSOR
from .discovery import async_discover
from .items import items_of

if TYPE_CHECKING:
    from .manager import VigilManager

STORAGE_VERSION = 1
DEBOUNCE = 5  # seconds: a registry event comes in bursts when an integration adds a device


def newsensors_store_key(entry_id: str) -> str:
    return f"{DOMAIN}.newsensors.{entry_id}"


class NewSensors:
    def __init__(self, hass: HomeAssistant, entry: Any, manager: VigilManager) -> None:
        self.hass = hass
        self.entry = entry
        self.manager = manager
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, newsensors_store_key(entry.entry_id))
        self._seen: set[str] = set()
        self._ignored: set[str] = set()  # entities the person never wants to see again (a room, a duplicate)
        self._timer: CALLBACK_TYPE | None = None
        self._unsub: CALLBACK_TYPE | None = None
        self.entities: list[dict[str, str]] = []  # what is new now: entity_id and name

    @property
    def count(self) -> int:
        return len(self.entities)

    def _everything(self) -> list[dict[str, Any]]:
        found = async_discover(self.hass, self.entry)
        return [*found["candidates"], *found["tamper_only"]]

    async def async_start(self) -> None:
        stored = await self._store.async_load()
        if stored is None:
            has_sensors = any(i.subentry_type == SUBENTRY_SENSOR for i in items_of(self.entry).values())
            self._seen = {c["entity_id"] for c in self._everything()} if has_sensors else set()
            await self._save()
        else:
            self._seen = set(stored.get("seen") or [])
            self._ignored = set(stored.get("ignored") or [])
        self.recompute(notify=False)
        self._unsub = self.hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, self._registry_changed)

    @callback
    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        if self._timer:
            self._timer()
            self._timer = None

    @callback
    def _registry_changed(self, event: Event) -> None:
        if event.data.get("action") == "remove" or self._timer is not None:
            return
        entity_id = event.data.get("entity_id", "")
        if not entity_id.startswith(("binary_sensor.", "sensor.")):
            return

        @callback
        def later(_now: Any) -> None:
            self._timer = None
            self.recompute()

        self._timer = async_call_later(self.hass, DEBOUNCE, later)

    @callback
    def recompute(self, *, notify: bool = True) -> None:
        """Count what is new now. Whatever is in use by a sensor counts as seen from then on."""
        everything = self._everything()
        used = {c["entity_id"] for c in everything if c.get("in_use")}
        if used - self._seen:
            self._seen |= used
            self.hass.async_create_task(self._save())
        before = [e["entity_id"] for e in self.entities]
        self.entities = [
            {"entity_id": c["entity_id"], "name": c["name"]}
            for c in everything
            if not c.get("in_use") and c["entity_id"] not in self._seen and c["entity_id"] not in self._ignored
        ]
        if notify and before != [e["entity_id"] for e in self.entities]:
            self.manager.notify_changed()

    async def async_dismiss(self) -> None:
        """*Not now*: what is new now is not announced again (it stays on the list of sensors that can be added)."""
        self._seen |= {e["entity_id"] for e in self.entities}
        await self._save()
        self.recompute()

    @property
    def ignored(self) -> set[str]:
        return set(self._ignored)

    async def async_set_ignored(self, entity_ids: list[str], ignored: bool) -> None:
        """*Ignore* hides entities from Find sensors and from the "new sensors" notice; *restore* brings them back."""
        if ignored:
            self._ignored |= set(entity_ids)
        else:
            self._ignored -= set(entity_ids)
        await self._save()
        self.recompute()

    async def _save(self) -> None:
        await self._store.async_save({"seen": sorted(self._seen), "ignored": sorted(self._ignored)})

    async def async_remove(self) -> None:
        await self._store.async_remove()
