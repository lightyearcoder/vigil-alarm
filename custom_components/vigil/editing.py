"""Validation and normalisation of sensors, rules, users, notifications and sirens.

One place for the rules, used by the config flows (the standard HA dialogs) and
by the admin panel. Both hand in the same raw form values and get back the
title and data to store, or an EditError with a message code per field.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .items import Item, items_of
from .const import (
    CONF_ALLOWED_MODES,
    CONF_BATTERY_ENTITY,
    CONF_CATEGORIES,
    CONF_CAUSES,
    CONF_CLS,
    CONF_CODE,
    CONF_CODE_HASH,
    CONF_CODE_SALT,
    CONF_DELAY,
    CONF_ENTRY_DELAY,
    CONF_GAS_TYPE,
    CONF_MAY_BYPASS_TAMPER,
    CONF_MAX_DURATION,
    CONF_ON_UNAVAILABLE,
    CONF_REPEAT_EVERY,
    CONF_REQUIRED,
    CONF_SERVICE,
    CONF_TAGS,
    CONF_TONE,
    CONF_TONE_ENTITY,
    CONF_TYPE,
    CONF_VOLUME,
    CONF_VOLUME_ENTITY,
    CONF_WINDOW,
    CONF_AT_ARM_OPEN,
    CONF_GROUP_MODES,
    CONF_SENSOR_GROUPS,
    CONF_SENSOR_MODES,
    CONF_SUGGEST_FOR,
    SUGGEST_FOR,
    CONF_MODES,
    CONF_SENSORS,
    PROFILE_CAUSES,
    SUBENTRY_RULE,
    SUBENTRY_NOTIFICATION,
    SUBENTRY_SIREN,
    SUBENTRY_USER,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
)
from .credentials import code_matches, hash_code
from .manager import build_config
from .vigil_core import ConfigError

CONF_NAME = "name"


class EditError(Exception):
    """Invalid input. `errors` maps a field (or "base") to a message code."""

    def __init__(self, errors: dict[str, str], placeholders: dict[str, str] | None = None) -> None:
        super().__init__(str(errors))
        self.errors = errors
        self.placeholders = placeholders or {}


class _Trial:
    """A subentry that is not saved yet, to validate it together with the others."""

    def __init__(self, subentry_type: str, title: str, data: dict[str, Any]) -> None:
        self.subentry_type = subentry_type
        self.title = title
        self.data = data


class _TrialEntry:
    """An entry with other data, to validate a change before saving it."""

    def __init__(self, entry: ConfigEntry, data: dict[str, Any]) -> None:
        self.data = data
        self.options = entry.options


def _others(entry: ConfigEntry, kind: str, sub: Item | None) -> list[Item]:
    return [
        s for sid, s in items_of(entry).items()
        if s.subentry_type == kind and (sub is None or sid != sub.subentry_id)
    ]


def _check_core(entry: ConfigEntry, kind: str, sub: Item | None, title: str, data: dict[str, Any]) -> None:
    try:
        key = sub.subentry_id if sub else "__new__"
        build_config(entry, {key: _Trial(kind, title, data)})  # type: ignore[dict-item]
    except ConfigError as err:
        raise EditError({"base": "invalid_config"}, {"error": str(err)}) from err


async def async_prepare(
    hass: HomeAssistant, entry: ConfigEntry, kind: str, sub: Item | None, raw: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """Return (title, data) to store for this input, or raise EditError."""
    name = str(raw.get(CONF_NAME) or "").strip()
    if not name:
        raise EditError({CONF_NAME: "name_required"})
    if kind == SUBENTRY_SENSOR:
        return name, _sensor(entry, sub, name, raw)
    if kind == SUBENTRY_SENSOR_GROUP:
        return name, _sensor_group(entry, sub, name, raw)
    if kind == SUBENTRY_RULE:
        return name, _rule(entry, sub, name, raw)
    if kind == SUBENTRY_USER:
        return name, await _user(hass, entry, sub, name, raw)
    if kind == SUBENTRY_NOTIFICATION:
        return name, _notification(hass, entry, sub, name, raw)
    if kind == SUBENTRY_SIREN:
        return name, _siren(entry, sub, name, raw)
    raise EditError({"base": "unknown_kind"})


def _sensor(entry: ConfigEntry, sub: Item | None, name: str, raw: dict[str, Any]) -> dict[str, Any]:
    data = {k: v for k, v in raw.items() if k != CONF_NAME}
    if data.get(CONF_ON_UNAVAILABLE) in ("default", "", None):
        data.pop(CONF_ON_UNAVAILABLE, None)
    data.pop(CONF_SENSOR_MODES, None)  # modes come from the sensor groups now
    if data.get(CONF_CLS) != "intrusion":
        for key in (CONF_TYPE, CONF_SENSOR_GROUPS, CONF_AT_ARM_OPEN, CONF_ENTRY_DELAY):
            data.pop(key, None)
    else:
        groups = list(data.get(CONF_SENSOR_GROUPS) or [])
        known = {sid for sid, s in items_of(entry).items() if s.subentry_type == SUBENTRY_SENSOR_GROUP}
        if not groups:
            raise EditError({CONF_SENSOR_GROUPS: "no_sensor_group"})
        if any(g not in known for g in groups):
            raise EditError({CONF_SENSOR_GROUPS: "unknown_sensor_group"})
        data[CONF_SENSOR_GROUPS] = groups
    if data.get(CONF_CLS) != "gas":
        data.pop(CONF_GAS_TYPE, None)
    if data.get(CONF_ENTRY_DELAY) in (None, ""):
        data.pop(CONF_ENTRY_DELAY, None)
    else:
        data[CONF_ENTRY_DELAY] = float(data[CONF_ENTRY_DELAY])
    if not data.get(CONF_BATTERY_ENTITY):
        data.pop(CONF_BATTERY_ENTITY, None)
    if not data.get("entity_id"):
        raise EditError({"entity_id": "required"})
    if CONF_CLS not in data:
        raise EditError({CONF_CLS: "required"})
    if any(o.title == name for o in _others(entry, SUBENTRY_SENSOR, sub)):
        raise EditError({CONF_NAME: "name_in_use"})
    _check_core(entry, SUBENTRY_SENSOR, sub, name, data)
    return data


def _sensor_group(entry: ConfigEntry, sub: Item | None, name: str, raw: dict[str, Any]) -> dict[str, Any]:
    enabled = list(entry.data.get(CONF_MODES, []))
    modes = [m for m in enabled if m in (raw.get(CONF_GROUP_MODES) or [])]
    if not modes:
        raise EditError({CONF_GROUP_MODES: "no_modes"})
    if len(modes) != len(set(raw.get(CONF_GROUP_MODES) or [])):
        raise EditError({CONF_GROUP_MODES: "unknown_mode"})
    data: dict[str, Any] = {CONF_GROUP_MODES: modes}
    suggest = raw.get(CONF_SUGGEST_FOR)
    if suggest:
        if suggest not in SUGGEST_FOR:
            raise EditError({CONF_SUGGEST_FOR: "unknown_suggestion"})
        data[CONF_SUGGEST_FOR] = suggest
    if any(o.title == name for o in _others(entry, SUBENTRY_SENSOR_GROUP, sub)):
        raise EditError({CONF_NAME: "name_in_use"})
    _check_core(entry, SUBENTRY_SENSOR_GROUP, sub, name, data)
    return data


def _rule(entry: ConfigEntry, sub: Item | None, name: str, raw: dict[str, Any]) -> dict[str, Any]:
    data = {k: v for k, v in raw.items() if k != CONF_NAME}
    data[CONF_SENSORS] = list(data.get(CONF_SENSORS) or [])
    data[CONF_REQUIRED] = int(data.get(CONF_REQUIRED, 2))
    data[CONF_WINDOW] = float(data.get(CONF_WINDOW, 60))
    data["escalate"] = bool(data.get("escalate", False))
    wrong = [
        items_of(entry)[z].title
        for z in data[CONF_SENSORS]
        if z in items_of(entry) and items_of(entry)[z].data.get(CONF_TYPE, "instant") != "instant"
    ]
    if wrong:
        raise EditError({CONF_SENSORS: "sensor_not_instant"}, {"sensors": ", ".join(wrong)})
    if any(o.title == name for o in _others(entry, SUBENTRY_RULE, sub)):
        raise EditError({CONF_NAME: "name_in_use"})
    _check_core(entry, SUBENTRY_RULE, sub, name, data)
    return data


async def _user(
    hass: HomeAssistant, entry: ConfigEntry, sub: Item | None, name: str, raw: dict[str, Any]
) -> dict[str, Any]:
    others = _others(entry, SUBENTRY_USER, sub)
    errors: dict[str, str] = {}
    data: dict[str, Any] = {
        CONF_TAGS: [t.strip() for t in (raw.get(CONF_TAGS) or []) if t and t.strip()],
        CONF_ALLOWED_MODES: list(raw.get(CONF_ALLOWED_MODES) or []),
        CONF_MAY_BYPASS_TAMPER: bool(raw.get(CONF_MAY_BYPASS_TAMPER, False)),
    }
    code = (raw.get(CONF_CODE) or "").strip()
    if code:
        data[CONF_CODE_HASH], data[CONF_CODE_SALT] = await hass.async_add_executor_job(hash_code, code)
        data["code_numeric"] = code.isdigit()
        for other in others:
            if await hass.async_add_executor_job(code_matches, code, other.data):
                errors[CONF_CODE] = "code_in_use"
    elif sub and sub.data.get(CONF_CODE_HASH) and not raw.get("remove_code"):
        for key in (CONF_CODE_HASH, CONF_CODE_SALT, "code_numeric"):
            data[key] = sub.data[key]
    if not data.get(CONF_CODE_HASH) and not data[CONF_TAGS]:
        errors["base"] = "no_credential"
    for tag in data[CONF_TAGS]:
        if any(tag in o.data.get(CONF_TAGS, []) for o in others):
            errors[CONF_TAGS] = "tag_in_use"
    if any(o.title == name for o in others):
        errors[CONF_NAME] = "name_in_use"
    if errors:
        raise EditError(errors)
    return data


def _notification(
    hass: HomeAssistant, entry: ConfigEntry, sub: Item | None, name: str, raw: dict[str, Any]
) -> dict[str, Any]:
    data = {k: v for k, v in raw.items() if k != CONF_NAME}
    data[CONF_DELAY] = float(data.get(CONF_DELAY) or 0)
    data["priority"] = bool(data.get("priority", False))
    if data.get(CONF_SERVICE) not in notify_services(hass):
        raise EditError({CONF_SERVICE: "service_not_found"})
    if not data.get(CONF_CATEGORIES):
        raise EditError({CONF_CATEGORIES: "no_categories"})
    if any(o.title == name for o in _others(entry, SUBENTRY_NOTIFICATION, sub)):
        raise EditError({CONF_NAME: "name_in_use"})
    return data


def notify_services(hass: HomeAssistant) -> list[str]:
    return sorted(
        n for n in hass.services.async_services_for_domain("notify")
        if n != "send_message"  # entity based, no service name to call
    )


def _siren(entry: ConfigEntry, sub: Item | None, name: str, raw: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {
        k: v for k, v in raw.items() if k not in (CONF_NAME, "preset") and k not in PROFILE_CAUSES and v not in (None, "")
    }
    for cause in PROFILE_CAUSES:
        profile = {k: v for k, v in (raw.get(cause) or {}).items() if v not in (None, "")}
        if profile:
            data[cause] = profile
    data[CONF_MAX_DURATION] = float(data.get(CONF_MAX_DURATION, 180))
    data[CONF_REPEAT_EVERY] = float(data.get(CONF_REPEAT_EVERY, 0))
    if not data.get("control"):
        raise EditError({"control": "required"})
    if not data.get(CONF_CAUSES):
        raise EditError({CONF_CAUSES: "no_causes"})
    if any(o.title == name for o in _others(entry, SUBENTRY_SIREN, sub)):
        raise EditError({CONF_NAME: "name_in_use"})
    if any(CONF_TONE in data.get(c, {}) for c in PROFILE_CAUSES) and CONF_TONE_ENTITY not in data:
        raise EditError({"base": "tone_without_entity"})
    if any(CONF_VOLUME in data.get(c, {}) for c in PROFILE_CAUSES) and CONF_VOLUME_ENTITY not in data:
        raise EditError({"base": "volume_without_entity"})
    return data
