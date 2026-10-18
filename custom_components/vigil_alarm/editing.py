"""Validation and normalisation of sensors, rules, users, notifications and sirens.

One place for the rules, used by the config flows (the standard HA dialogs) and
by the admin panel. Both hand in the same raw form values and get back the
title and data to store, or an EditError with a message code per field.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .items import Item, items_of
from .const import (
    CONF_MIN_CODE_LENGTH,
    CONF_BLOCKED,
    CONF_WATCH,
    CONF_HA_USER,
    CONF_CAN_BYPASS,
    CONF_CAN_DISARM,
    CONF_CAN_SILENCE,
    CONF_LANGUAGE,
    CONF_PANEL_ID,
    CONF_SENSOR_LIST,
    CONF_UNLOCK_SECONDS,
    DEFAULT_UNLOCK_SECONDS,
    SENSOR_LIST_CHOICES,
    UNLOCK_SECONDS_RANGE,
    MIN_CODE_LENGTH_FLOOR,
    CONF_ALLOWED_MODES,
    CONF_BATTERY_ENTITY,
    CONF_COMPANION_OF,
    CONF_TAMPER_ENTITY,
    CONF_CATEGORIES,
    CONF_CAUSES,
    CONF_CLS,
    CONF_CODE,
    CONF_CODE_HASH,
    CONF_CODE_SALT,
    CONF_DURESS_HASH,
    CONF_DURESS_SALT,
    CONF_CHIME,
    CONF_DELAY,
    CONF_ENTRY_DELAY,
    CONF_GAS_TYPE,
    CONF_MAY_BYPASS,
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
    SUBENTRY_PANEL,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
)
from .credentials import code_matches, duress_matches, hash_code
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
    if kind == SUBENTRY_PANEL:
        return name, await _panel(hass, entry, sub, name, raw)
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
    if data.get(CONF_CLS) != "intrusion" or not data.get(CONF_CHIME):
        data.pop(CONF_CHIME, None)  # the chime is for doors and windows (intrusion sensors)
    else:
        data[CONF_CHIME] = True
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
    data.pop(CONF_COMPANION_OF, None)  # only Vigil sets this
    mine = {sub.subentry_id, *(c for c, _ in _companions(entry, sub.subentry_id))} if sub else set()
    if any(
        s.data.get("entity_id") == data["entity_id"]
        for sid, s in items_of(entry).items()
        if s.subentry_type == SUBENTRY_SENSOR and sid not in mine
    ):
        raise EditError({"entity_id": "entity_in_use"})  # one entity, one sensor: no double alarms
    tamper = data.get(CONF_TAMPER_ENTITY) or None
    if not tamper or data[CONF_CLS] == "tamper":
        data.pop(CONF_TAMPER_ENTITY, None)
    else:
        own = {sub.subentry_id} | {c for c, _ in _companions(entry, sub.subentry_id)} if sub else set()
        if tamper == data["entity_id"]:
            raise EditError({CONF_TAMPER_ENTITY: "tamper_same_entity"})
        if any(
            s.data.get("entity_id") == tamper
            for sid, s in items_of(entry).items()
            if s.subentry_type == SUBENTRY_SENSOR and sid not in own
        ):
            raise EditError({CONF_TAMPER_ENTITY: "tamper_entity_in_use"})
    if any(o.title == name for o in _others(entry, SUBENTRY_SENSOR, sub)):
        raise EditError({CONF_NAME: "name_in_use"})
    _check_core(entry, SUBENTRY_SENSOR, sub, name, data)
    return data


def _companions(entry: ConfigEntry, parent_id: str) -> list[tuple[str, Item]]:
    return [
        (sid, s) for sid, s in items_of(entry).items()
        if s.subentry_type == SUBENTRY_SENSOR and s.data.get(CONF_COMPANION_OF) == parent_id
    ]


def companion_id(entry: ConfigEntry, parent_id: str) -> str | None:
    found = _companions(entry, parent_id)
    return found[0][0] if found else None


def plan_companion(
    hass: HomeAssistant, entry: ConfigEntry, parent_id: str, parent_name: str, parent_data: dict[str, Any]
) -> tuple[str, dict[str, Any]] | None:
    """The tamper sensor that goes with a sensor: (title, data), or None if it has no tamper contact.

    The tamper contact of a door contact is a sensor of its own (class tamper: always watching,
    its own bypass), but the person who adds the door contact only fills in one form.
    """
    tamper = parent_data.get(CONF_TAMPER_ENTITY)
    if not tamper:
        return None
    word = "sabotage" if str(hass.config.language).startswith("nl") else "tamper"
    title = f"{parent_name} ({word})"
    existing = companion_id(entry, parent_id)
    if any(
        s.title == title for sid, s in items_of(entry).items()
        if s.subentry_type == SUBENTRY_SENSOR and sid not in (parent_id, existing)
    ):
        raise EditError({CONF_NAME: "name_in_use"})
    return title, {"entity_id": tamper, CONF_CLS: "tamper", CONF_COMPANION_OF: parent_id}


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
        CONF_MAY_BYPASS: bool(raw.get(CONF_MAY_BYPASS, False)),
        CONF_MAY_BYPASS_TAMPER: bool(raw.get(CONF_MAY_BYPASS_TAMPER, False)),
    }
    code = (raw.get(CONF_CODE) or "").strip()
    if code:
        minimum = max(MIN_CODE_LENGTH_FLOOR, int(entry.data.get(CONF_MIN_CODE_LENGTH, MIN_CODE_LENGTH_FLOOR)))
        if len(code) < minimum:
            raise EditError({CONF_CODE: "code_too_short"}, {"min": minimum})
        data[CONF_CODE_HASH], data[CONF_CODE_SALT] = await hass.async_add_executor_job(hash_code, code)
        data["code_numeric"] = code.isdigit()
        for other in others:
            if await hass.async_add_executor_job(code_matches, code, other.data) or await hass.async_add_executor_job(duress_matches, code, other.data):
                errors[CONF_CODE] = "code_in_use"
        if sub and sub.data.get(CONF_DURESS_HASH) and await hass.async_add_executor_job(duress_matches, code, sub.data):
            errors[CONF_CODE] = "code_in_use"
    elif sub and sub.data.get(CONF_CODE_HASH) and not raw.get("remove_code"):
        for key in (CONF_CODE_HASH, CONF_CODE_SALT, "code_numeric"):
            data[key] = sub.data[key]
    if not data.get(CONF_CODE_HASH) and not data[CONF_TAGS]:
        errors["base"] = "no_credential"
    duress = (raw.get("duress_code") or "").strip()
    if duress:
        minimum = max(MIN_CODE_LENGTH_FLOOR, int(entry.data.get(CONF_MIN_CODE_LENGTH, MIN_CODE_LENGTH_FLOOR)))
        if len(duress) < minimum:
            errors["duress_code"] = "code_too_short"
        elif not data.get(CONF_CODE_HASH):
            errors["duress_code"] = "duress_needs_code"
        else:
            data[CONF_DURESS_HASH], data[CONF_DURESS_SALT] = await hass.async_add_executor_job(hash_code, duress)
            own = await hass.async_add_executor_job(code_matches, duress, data)
            same = own or any(
                [await hass.async_add_executor_job(code_matches, duress, o.data) for o in others]
                + [await hass.async_add_executor_job(duress_matches, duress, o.data) for o in others]
            )
            if same:
                errors["duress_code"] = "code_in_use"
    elif sub and sub.data.get(CONF_DURESS_HASH) and not raw.get("remove_duress") and data.get(CONF_CODE_HASH):
        data[CONF_DURESS_HASH], data[CONF_DURESS_SALT] = sub.data[CONF_DURESS_HASH], sub.data[CONF_DURESS_SALT]
    if CONF_DURESS_HASH in data and "duress_code" not in errors and not any(
        s.subentry_type == SUBENTRY_NOTIFICATION and "duress" in (s.data.get(CONF_CATEGORIES) or [])
        for s in items_of(entry).values()
    ):
        errors["duress_code"] = "duress_no_channel"  # a silent alarm that reaches nobody is worse than none
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


PANEL_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")


def _free_panel_id(name: str, others: list[Item]) -> str:
    """A panel id from the name of a tablet or phone: lower case letters, digits and dashes, and not in use."""
    base = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower())
    base = base.strip("-")[:50] or "device"
    taken = {o.data.get(CONF_PANEL_ID) for o in others}
    candidate, n = base, 2
    while candidate in taken:
        candidate, n = f"{base}-{n}", n + 1
    return candidate


async def _panel(
    hass: HomeAssistant, entry: ConfigEntry, sub: Item | None, name: str, raw: dict[str, Any]
) -> dict[str, Any]:
    """A control point in the register: what it is called and what it may do."""
    others = _others(entry, SUBENTRY_PANEL, sub)
    errors: dict[str, str] = {}
    # A tablet or phone is found by its Home Assistant account; its panel id is only a label for the history and
    # the profile sensor, so the form does not ask for it: it follows from the name, and stays as it is when edited.
    # An ESPHome panel is found by its panel id, the name of the ESPHome device.
    by_account = raw.get("device") == "account" or (raw.get("device") is None and bool(raw.get(CONF_HA_USER)))
    panel_id = str(raw.get(CONF_PANEL_ID) or "").strip()
    if by_account:
        if sub and sub.data.get(CONF_HA_USER) and sub.data.get(CONF_PANEL_ID):
            panel_id = sub.data[CONF_PANEL_ID]
        elif not panel_id:
            panel_id = _free_panel_id(name, others)
    if not panel_id:
        errors[CONF_PANEL_ID] = "required"
    elif not PANEL_ID_PATTERN.match(panel_id):
        errors[CONF_PANEL_ID] = "panel_id_invalid"
    elif any(o.data.get(CONF_PANEL_ID) == panel_id for o in others):
        errors[CONF_PANEL_ID] = "panel_id_in_use"
    if any(o.title == name for o in others):
        errors[CONF_NAME] = "name_in_use"
    modes = list(entry.data.get(CONF_MODES, []))
    chosen = [m for m in modes if m in (raw.get(CONF_ALLOWED_MODES) or modes)]
    if not chosen:
        errors[CONF_ALLOWED_MODES] = "no_modes"
    sensor_list = raw.get(CONF_SENSOR_LIST) or "code"
    if sensor_list not in SENSOR_LIST_CHOICES:
        errors[CONF_SENSOR_LIST] = "unknown_choice"
    try:
        seconds = int(raw.get(CONF_UNLOCK_SECONDS, DEFAULT_UNLOCK_SECONDS))
    except (TypeError, ValueError):
        seconds = 0
    if not UNLOCK_SECONDS_RANGE[0] <= seconds <= UNLOCK_SECONDS_RANGE[1]:
        errors[CONF_UNLOCK_SECONDS] = "unlock_range"
    ha_user = str(raw.get(CONF_HA_USER) or "").strip() if by_account or raw.get("device") is None else ""
    if by_account and not ha_user:
        errors[CONF_HA_USER] = "required"
    if ha_user:
        account = await hass.auth.async_get_user(ha_user)
        if account is None or account.system_generated or not account.is_active:
            errors[CONF_HA_USER] = "ha_user_unknown"
        elif any(o.data.get(CONF_HA_USER) == ha_user for o in others):
            errors[CONF_HA_USER] = "ha_user_in_use"
    language = raw.get(CONF_LANGUAGE) or ""
    if language not in ("", "nl", "en"):
        errors[CONF_LANGUAGE] = "unknown_choice"
    data: dict[str, Any] = {
        CONF_PANEL_ID: panel_id,
        CONF_LANGUAGE: language,
        # all modes chosen is stored as "all", so a mode added later is allowed too
        CONF_ALLOWED_MODES: [] if len(chosen) == len(modes) else chosen,
        CONF_CAN_DISARM: bool(raw.get(CONF_CAN_DISARM, True)),
        CONF_CAN_BYPASS: bool(raw.get(CONF_CAN_BYPASS, True)),
        CONF_CAN_SILENCE: bool(raw.get(CONF_CAN_SILENCE, True)),
        CONF_SENSOR_LIST: sensor_list,
        CONF_UNLOCK_SECONDS: seconds,
        CONF_BLOCKED: bool(raw.get(CONF_BLOCKED, False)),
        CONF_WATCH: bool(raw.get(CONF_WATCH, True)),
    }
    if ha_user:
        data[CONF_HA_USER] = ha_user
    code = (raw.get(CONF_CODE) or "").strip()
    if code:
        minimum = max(MIN_CODE_LENGTH_FLOOR, int(entry.data.get(CONF_MIN_CODE_LENGTH, MIN_CODE_LENGTH_FLOOR)))
        if len(code) < minimum:
            errors[CONF_CODE] = "code_too_short"
        else:
            data[CONF_CODE_HASH], data[CONF_CODE_SALT] = await hass.async_add_executor_job(hash_code, code)
    elif sub and sub.data.get(CONF_CODE_HASH) and not raw.get("remove_code"):
        data[CONF_CODE_HASH], data[CONF_CODE_SALT] = sub.data[CONF_CODE_HASH], sub.data[CONF_CODE_SALT]
    if errors:
        raise EditError(errors, {"min": max(MIN_CODE_LENGTH_FLOOR, int(entry.data.get(CONF_MIN_CODE_LENGTH, MIN_CODE_LENGTH_FLOOR))),
                                 "low": UNLOCK_SECONDS_RANGE[0], "high": UNLOCK_SECONDS_RANGE[1]})
    return data
