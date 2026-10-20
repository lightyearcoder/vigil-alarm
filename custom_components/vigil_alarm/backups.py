"""Back-ups of the configuration, a list of changes, and export and import.

Everything you set up in Vigil (settings, sensors, groups, rules, users, notifications, sirens, panels) is
the `data` and `options` of the config entry. Whenever either changes, whatever the cause (an edit in the
panel, an import, a restore, a restart that found another state), the state *before* the change is kept as a
version with a summary of what the change was. The last `KEEP` versions are kept; "Restore" puts one back,
and that restore is itself a change, so it can be undone the same way.

Nothing here touches the live state of the alarm (armed, triggered, bypassed): only the configuration.
The back-ups contain what the configuration contains: code hashes (never codes), the heartbeat address and
notification service names. They live next to the configuration in Home Assistant's own storage.
"""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.loader import async_get_integration

from .const import (
    BACKUP_VERSIONS_RANGE,
    CONF_BACKUP_VERSIONS,
    CONF_COMPANION_OF,
    DEFAULT_BACKUP_VERSIONS,
    DOMAIN,
    SUBENTRY_NOTIFICATION,
    SUBENTRY_PANEL,
    SUBENTRY_PARTITION,
    SUBENTRY_RULE,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
    SUBENTRY_SIREN,
    SUBENTRY_USER,
)
from .items import OPTION_KEY
from .manager import build_config
from .migration import ENTRY_VERSION
from .vigil_core import ConfigError

STORAGE_VERSION = 1
KEEP = DEFAULT_BACKUP_VERSIONS  # the default; the setting `backup_versions` decides
EXPORT_FORMAT = "vigil_alarm_configuration"
EXPORT_FORMAT_VERSION = 1
_KNOWN_TYPES = {
    SUBENTRY_SENSOR, SUBENTRY_SENSOR_GROUP, SUBENTRY_RULE, SUBENTRY_USER,
    SUBENTRY_NOTIFICATION, SUBENTRY_SIREN, SUBENTRY_PANEL, SUBENTRY_PARTITION,
}
_PENDING = f"{DOMAIN}_backup_reason"


class BackupError(Exception):
    """A file or version that cannot be used. `code` is a message code for the panel."""

    def __init__(self, code: str, placeholders: dict[str, Any] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.placeholders = placeholders or {}


def capture(entry: Any) -> dict[str, Any]:
    """The configuration of an entry as plain data (a deep copy that can be stored)."""
    return json.loads(json.dumps({"data": dict(entry.data), "options": dict(entry.options or {})}))


def diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """What changes going from `old` to `new`: items added, removed or changed, and the settings that differ.

    Values are never part of the result (a code hash or an address is not shown), only names and keys. A tamper
    contact follows its sensor and is left out so a sensor is counted once.
    """
    old_items = (old["options"].get(OPTION_KEY) or {})
    new_items = (new["options"].get(OPTION_KEY) or {})

    def companion(body: dict[str, Any]) -> bool:
        return bool((body.get("data") or {}).get(CONF_COMPANION_OF))

    items: list[dict[str, str]] = []
    for item_id, body in new_items.items():
        if companion(body):
            continue
        before = old_items.get(item_id)
        if before is None:
            items.append({"type": body["type"], "action": "added", "name": body["title"]})
        elif before != body:
            items.append({"type": body["type"], "action": "changed", "name": body["title"]})
    for item_id, body in old_items.items():
        if item_id not in new_items and not companion(body):
            items.append({"type": body["type"], "action": "removed", "name": body["title"]})
    keys = set(old["data"]) | set(new["data"])
    settings = sorted(k for k in keys if old["data"].get(k) != new["data"].get(k))
    other = (set(old["options"]) | set(new["options"])) - {OPTION_KEY}
    settings += sorted(k for k in other if old["options"].get(k) != new["options"].get(k))
    counts: dict[str, dict[str, int]] = {}
    for it in items:
        counts.setdefault(it["type"], {}).setdefault(it["action"], 0)
        counts[it["type"]][it["action"]] += 1
    return {"items": items, "settings": settings, "counts": counts, "empty": not items and not settings}


def mark_reason(hass: HomeAssistant, entry: ConfigEntry, reason: str) -> None:
    """Say why the next change happens ("restore" or "import"); without it a change is an "edit"."""
    hass.data.setdefault(_PENDING, {})[entry.entry_id] = reason


def check_state(state: Any) -> dict[str, Any]:
    """Check that `state` ({"data", "options"}) is a configuration this version can run; return it cleaned.

    Raises BackupError for the shape and ConfigError-based `invalid_config` for what the engine refuses.
    """
    if not isinstance(state, dict) or not isinstance(state.get("data"), dict) or not isinstance(state.get("options"), dict):
        raise BackupError("backup_invalid")
    items = state["options"].get(OPTION_KEY) or {}
    if not isinstance(items, dict):
        raise BackupError("backup_invalid")
    for body in items.values():
        if (
            not isinstance(body, dict)
            or body.get("type") not in _KNOWN_TYPES
            or not isinstance(body.get("title"), str)
            or not isinstance(body.get("data", {}), dict)
        ):
            raise BackupError("backup_invalid")
    clean = json.loads(json.dumps({"data": state["data"], "options": state["options"]}))
    try:
        build_config(SimpleNamespace(data=clean["data"], options=clean["options"]))  # type: ignore[arg-type]
    except ConfigError as err:
        raise BackupError("invalid_config", {"error": str(err)}) from err
    except (KeyError, TypeError, ValueError) as err:
        raise BackupError("backup_invalid") from err
    return clean


def export_payload(entry: ConfigEntry, integration_version: str, changed_at: str | None = None) -> dict[str, Any]:
    """The configuration as a file. It holds code hashes and addresses; the panel says so. `changed_at` is when this
    configuration was last saved: that is what the file is named after, not the moment of the export."""
    return {
        "format": EXPORT_FORMAT,
        "format_version": EXPORT_FORMAT_VERSION,
        "integration_version": integration_version,
        "entry_version": entry.version,
        "exported_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "changed_at": changed_at,
        "title": entry.title,
        **capture(entry),
    }


def read_payload(payload: Any) -> dict[str, Any]:
    """The configuration inside an export file, checked; raises BackupError."""
    if not isinstance(payload, dict) or payload.get("format") != EXPORT_FORMAT:
        raise BackupError("import_not_vigil")
    if payload.get("format_version") != EXPORT_FORMAT_VERSION:
        raise BackupError("import_format_version")
    version = payload.get("entry_version")
    if version != ENTRY_VERSION:
        raise BackupError("import_entry_version", {"found": str(version), "expected": str(ENTRY_VERSION)})
    return check_state(payload)


class ConfigBackups:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, backups_store_key(entry.entry_id))
        self._current: dict[str, Any] | None = None
        # The storage format and the Vigil version the current configuration was last written by; a version that
        # is kept carries those of its own state, so it is clear what an old one was made by.
        self._meta: dict[str, Any] = {}
        self._versions: list[dict[str, Any]] = []
        # When the current configuration became the current one (the last save); older stores take the newest version's time.
        self.changed_at: str | None = None

    async def async_start(self) -> None:
        """Load what is kept, and note a configuration that changed while Vigil was not watching (a change made
        outside the panel, or the migration of an update)."""
        stored = await self._store.async_load() or {}
        self._current = stored.get("current")
        self._versions = list(stored.get("versions") or [])
        self.changed_at = stored.get("changed_at") or (self._versions[-1]["time"] if self._versions else _now())
        self._trim()
        running = (await async_get_integration(self.hass, DOMAIN)).version.string
        before_meta = stored.get("meta") or {"entry_version": self.entry.version, "integration_version": None}
        actual = capture(self.entry)
        self._meta = {"entry_version": self.entry.version, "integration_version": running}
        if self._current is None:
            self._current = actual
            await self._save()
            return
        upgraded = before_meta.get("entry_version") != self.entry.version or (
            before_meta.get("integration_version") not in (None, running))
        if self._current != actual:
            await self._push(self._current, actual, "upgrade" if upgraded else "external", before_meta)
        else:
            await self._save()  # (the meta may have changed)

    async def async_changed(self) -> None:
        """The entry was updated: keep the state before as a version."""
        actual = capture(self.entry)
        if self._current is None or self._current == actual:
            return
        reason = self.hass.data.get(_PENDING, {}).pop(self.entry.entry_id, "edit")
        await self._push(self._current, actual, reason, self._meta)

    async def _push(self, before: dict[str, Any], after: dict[str, Any], reason: str, before_meta: dict[str, Any]) -> None:
        summary = diff(before, after)
        if not summary["empty"]:
            self._versions.append({
                "id": f"{datetime.now(UTC):%Y%m%dT%H%M%S%f}",
                "time": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "reason": reason,
                "entry_version": before_meta.get("entry_version", self.entry.version),
                "integration_version": before_meta.get("integration_version"),
                "summary": {k: summary[k] for k in ("items", "settings", "counts")},
                "state": before,
            })
            self._trim()
        self._current = after
        self.changed_at = _now()
        self._meta = {**self._meta, "entry_version": self.entry.version}
        await self._save()

    def keep(self) -> int:
        try:
            value = int(self.entry.data.get(CONF_BACKUP_VERSIONS, DEFAULT_BACKUP_VERSIONS))
        except (TypeError, ValueError):
            return DEFAULT_BACKUP_VERSIONS
        return min(max(value, BACKUP_VERSIONS_RANGE[0]), BACKUP_VERSIONS_RANGE[1])

    def _trim(self) -> None:
        """Only the newest `keep()` versions stay (fewer when the setting is lowered)."""
        del self._versions[:-self.keep()]

    async def _save(self) -> None:
        await self._store.async_save({"current": self._current, "meta": self._meta, "versions": self._versions, "changed_at": self.changed_at})

    # ---- reading

    def listing(self) -> list[dict[str, Any]]:
        """Newest first; the state itself stays out of the answer. A version made by another storage format cannot
        be put back (it would need a migration), and the list says so."""
        return [
            {**{k: v[k] for k in ("id", "time", "reason", "entry_version", "summary")},
             "integration_version": v.get("integration_version"),
             "restorable": v["entry_version"] == ENTRY_VERSION}
            for v in reversed(self._versions)
        ]

    def version(self, version_id: str) -> dict[str, Any] | None:
        return next((v for v in self._versions if v["id"] == version_id), None)

    def state_of(self, version_id: str) -> dict[str, Any]:
        """The configuration of a version, ready to apply; raises BackupError."""
        found = self.version(version_id)
        if found is None:
            raise BackupError("backup_unknown")
        if found["entry_version"] != ENTRY_VERSION:
            raise BackupError("import_entry_version", {"found": str(found["entry_version"]), "expected": str(ENTRY_VERSION)})
        return check_state(copy.deepcopy(found["state"]))

    def change_for(self, state: dict[str, Any]) -> dict[str, Any]:
        """What applying `state` would change in the live configuration."""
        return diff(capture(self.entry), state)

    async def async_remove(self) -> None:
        await self._store.async_remove()


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def backups_store_key(entry_id: str) -> str:
    return f"{DOMAIN}.backups.{entry_id}"
