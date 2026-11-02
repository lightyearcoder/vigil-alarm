"""The admin panel: what is sent to it (the stored configuration and the live state)."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_ABORT_SECONDS,
    CONF_BACKUP_VERSIONS,
    CONF_CHIME_SECONDS,
    CONF_CODE_HASH,
    CONF_CODE_SALT,
    CONF_DURESS_HASH,
    CONF_DURESS_SALT,
    CONF_HEARTBEAT_INTERVAL,
    CONF_KEY_HASH,
    CONF_LOG_RETENTION_DAYS,
    CONF_MIN_CODE_LENGTH,
    CONF_MODES,
    CONF_PARTITION_NAME,
    CONF_PARTITION_RETURN_SECONDS,
    CONF_SCREEN_OFF_ON_ALARM,
    CONF_SCREEN_OFF_SECONDS,
    CONF_STARTUP_WAIT,
    DEFAULT_ABORT_SECONDS,
    DEFAULT_BACKUP_VERSIONS,
    DEFAULT_CHIME_SECONDS,
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_LOG_RETENTION_DAYS,
    DEFAULT_MODES,
    DEFAULT_PARTITION_RETURN_SECONDS,
    DEFAULT_SCREEN_OFF_ON_ALARM,
    DEFAULT_SCREEN_OFF_SECONDS,
    DEFAULT_SELFTEST,
    DEFAULT_STARTUP_WAIT,
    DOMAIN,
    LOCK_DEFAULTS,
    MIN_CODE_LENGTH_FLOOR,
    PRIMARY_PARTITION,
    SUBENTRY_PANEL,
    SUBENTRY_SENSOR,
    SUBENTRY_USER,
)
from .editing import notify_services
from .items import Item, items_of
from .manager import all_enabled_modes, partition_data, partition_ids
from .panel_forms import _VERSION, KINDS, TYPE_OF, form_schema, settings_schema
from .presets import siren_preset_ids

# ------------------------------------------------------------- serialisation


def _public(sub: Item) -> dict[str, Any]:
    """What the panel may see of a subentry: never the hash or the salt of a code."""
    data = dict(sub.data)
    has_code = bool(data.pop(CONF_CODE_HASH, None))
    has_duress = bool(data.pop(CONF_DURESS_HASH, None))
    has_key = bool(data.pop(CONF_KEY_HASH, None))
    data.pop(CONF_CODE_SALT, None)
    data.pop(CONF_DURESS_SALT, None)
    data.pop("code_numeric", None)
    if sub.subentry_type == SUBENTRY_USER:
        data.setdefault("may_bypass", True)  # a user saved before the right existed keeps it, until you untick it
    out = {"id": sub.subentry_id, "title": sub.title, "data": data}
    if sub.subentry_type in (SUBENTRY_USER, SUBENTRY_PANEL):
        out["has_code"] = has_code
        if sub.subentry_type == SUBENTRY_PANEL:
            out["has_key"] = has_key
        if sub.subentry_type == SUBENTRY_USER:
            out["has_duress"] = has_duress
    return out


def _entry_for(hass: HomeAssistant) -> ConfigEntry | None:
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    return entries[0] if entries else None


def _partitions(hass: HomeAssistant, entry: ConfigEntry) -> list[dict[str, Any]]:
    registry = er.async_get(hass)
    manager = getattr(entry, "runtime_data", None)
    out = []
    for pid in partition_ids(entry):
        sub = items_of(entry).get(pid)
        uid = entry.entry_id if pid == PRIMARY_PARTITION else f"{entry.entry_id}_partition_{pid}"
        out.append({
            "id": pid,
            "name": (manager.partitions[pid].name if manager is not None and pid in manager.partitions
                     else sub.title if sub else entry.data.get(CONF_PARTITION_NAME) or ""),
            "primary": pid == PRIMARY_PARTITION,
            "modes": list(partition_data(entry, pid).get(CONF_MODES) or ([] if pid == PRIMARY_PARTITION else DEFAULT_MODES)),
            "entity": registry.async_get_entity_id("alarm_control_panel", DOMAIN, uid),
        })
    return out


def _snapshot(hass: HomeAssistant, entry: ConfigEntry, users: list[Any]) -> dict[str, Any]:
    registry = er.async_get(hass)
    sensor_entities: dict[str, dict[str, str | None]] = {}
    for sid, sub in items_of(entry).items():
        if sub.subentry_type != SUBENTRY_SENSOR:
            continue
        sensor_entities[sid] = {
            "bypass": registry.async_get_entity_id("binary_sensor", DOMAIN, f"{entry.entry_id}_{sid}_bypassed"),
            "status": registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{sid}_status"),
        }
    return {
        "version": _VERSION,
        "entry": {"id": entry.entry_id, "title": entry.title, "data": {CONF_STARTUP_WAIT: DEFAULT_STARTUP_WAIT, **LOCK_DEFAULTS, CONF_MIN_CODE_LENGTH: MIN_CODE_LENGTH_FLOOR, CONF_SCREEN_OFF_SECONDS: DEFAULT_SCREEN_OFF_SECONDS, CONF_SCREEN_OFF_ON_ALARM: DEFAULT_SCREEN_OFF_ON_ALARM, CONF_PARTITION_RETURN_SECONDS: DEFAULT_PARTITION_RETURN_SECONDS, CONF_ABORT_SECONDS: DEFAULT_ABORT_SECONDS, CONF_CHIME_SECONDS: DEFAULT_CHIME_SECONDS, CONF_LOG_RETENTION_DAYS: DEFAULT_LOG_RETENTION_DAYS, CONF_BACKUP_VERSIONS: DEFAULT_BACKUP_VERSIONS, CONF_HEARTBEAT_INTERVAL: DEFAULT_HEARTBEAT_INTERVAL, **DEFAULT_SELFTEST, **entry.data}},
        "items": {
            kind: [_public(s) for s in items_of(entry).values() if s.subentry_type == TYPE_OF[kind]]
            for kind in KINDS
        },
        "forms": form_schema(all_enabled_modes(entry) or list(DEFAULT_MODES), entry.data),
        # The partitions, the first one first. The first has no item: it is the entry itself.
        "partitions": _partitions(hass, entry),
        "settings_form": settings_schema(),
        "sensor_entities": sensor_entities,
        "alarm_entity": registry.async_get_entity_id("alarm_control_panel", DOMAIN, entry.entry_id),
        "alarm_all_entity": registry.async_get_entity_id("alarm_control_panel", DOMAIN, f"{entry.entry_id}_all"),
        "notify_services": notify_services(hass),
        # Who a tablet or phone can be: every active account that is not a system account. An administrator
        # too: that is the administrator's own responsibility (see the guides), and Vigil then treats the account
        # on that device as an ordinary one: no administrator shortcuts, a code for every disarm and bypass.
        "ha_users": [
            {"id": u.id, "name": (u.name or u.id) + (" (admin)" if u.is_admin else "")}
            for u in sorted(users, key=lambda u: (u.name or "").lower())
            if u.is_active and not u.system_generated
        ],
        "siren_presets": siren_preset_ids(),
    }


def _live(entry: ConfigEntry) -> dict[str, Any] | None:
    manager = getattr(entry, "runtime_data", None)
    if manager is None:  # reloading
        return None
    return {
        "state": manager.engine.state,
        "mode": manager.engine.mode,
        "sensors": {z: manager.sensor_status(z) for z in manager.config.sensors},
        # Per partition: its name, state, mode and (while disarmed) what would stop arming. The fields above are
        # those of the first partition, which is all an installation with one partition has.
        "partitions": {
            pid: {
                "name": part.name, "state": part.engine.state, "mode": part.engine.mode,
                "blockers": {m: b for m in part.config.modes if (b := manager.arm_blockers(m, sync=False, partition=pid))}
                if part.engine.state == "disarmed" else {},
            }
            for pid, part in manager.partitions.items()
        },
        "combined": manager.combined().state,
        "problems": manager.supervisor.problems(),
        "panels": manager.panels.status(),
        "new_sensors": manager.new_sensors.entities,
        "practice_until": manager.practice.until,
        "walktest": manager.walktest.status(),
        "alarm_memory": manager.alarmmemory.view(),
        # Sensors that are left out for good (permanent bypass): the Overview names them so they are not forgotten.
        "permanent_bypassed": [
            {"id": z, "name": manager._sensor_name.get(z, z), "entity_id": manager._sensor_entity.get(z)}
            for z, sensor in manager.config.sensors.items()
            if sensor.permanent_bypass and manager.sensor_is_bypassed(z)
        ],
        # Per mode what would stop arming now (only while disarmed; the panel shows it as "why can't I arm?").
        "blockers": {m: b for m in manager.config.modes if (b := manager.arm_blockers(m, sync=False))} if manager.engine.state == "disarmed" else {},
    }


