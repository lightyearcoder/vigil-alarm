"""Upgrades of stored configuration.

Version 1 stored the modes in which an intrusion sensor is watching on the
sensor itself. Version 2 keeps them on sensor groups: each distinct set of modes
that was in use becomes a group, so nothing changes in behaviour. Confirmation
rules stored their sensors under the key "zones"; they now use "sensors".
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import (
    CONF_CLS,
    CONF_GROUP_MODES,
    CONF_MODES,
    CONF_SENSOR_GROUPS,
    CONF_SENSOR_MODES,
    CONF_SENSORS,
    CONF_SUGGEST_FOR,
    DEFAULT_MODES,
    SUBENTRY_RULE,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
)
from .items import OPTION_KEY, new_id, stored
from .messages import mode_name

ENTRY_VERSION = 3


def default_groups(language: str, modes: list[str]) -> dict[str, dict[str, Any]]:
    """The two groups a new installation starts with: doors and windows, and motion."""
    nl = language.startswith("nl")
    perimeter = ("Buitenschil" if nl else "Perimeter", [m for m in modes])
    interior = ("Binnen" if nl else "Interior", [m for m in modes if m == "away"])
    groups: dict[str, dict[str, Any]] = {}
    for (title, group_modes), suggest in ((perimeter, "contacts"), (interior, "motion")):
        if not group_modes:
            continue
        groups[new_id()] = stored(
            SUBENTRY_SENSOR_GROUP, title, {CONF_GROUP_MODES: group_modes, CONF_SUGGEST_FOR: suggest}
        )
    return groups


def _title(language: str, modes: list[str]) -> str:
    return " + ".join(mode_name(language, m) for m in modes)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.version > ENTRY_VERSION:
        return False  # saved by a newer version of Vigil
    if entry.version == 1:
        _v1_to_v2(hass, entry)
    if entry.version <= 2:
        _v2_to_v3(hass, entry)
    hass.config_entries.async_update_entry(entry, version=ENTRY_VERSION)
    return True


def _v1_to_v2(hass: HomeAssistant, entry: ConfigEntry) -> None:
    language = hass.config.language
    enabled = list(entry.data.get(CONF_MODES, DEFAULT_MODES))
    group_for: dict[tuple[str, ...], str] = {}
    taken = {s.title for s in entry.subentries.values()}
    for sub in list(entry.subentries.values()):
        if sub.subentry_type == SUBENTRY_RULE and "zones" in sub.data:
            rule = {k: v for k, v in sub.data.items() if k != "zones"}
            rule[CONF_SENSORS] = list(sub.data["zones"])
            hass.config_entries.async_update_subentry(entry, sub, data=rule)
            continue
        if sub.subentry_type != SUBENTRY_SENSOR or CONF_SENSOR_MODES not in sub.data:
            continue
        data: dict[str, Any] = dict(sub.data)
        saved_modes = data.pop(CONF_SENSOR_MODES)
        old_modes = tuple(m for m in enabled if m in saved_modes)
        if data.get(CONF_CLS) == "intrusion" and old_modes:
            if old_modes not in group_for:
                title = _title(language, list(old_modes))
                while title in taken:
                    title += " "
                taken.add(title)
                group = ConfigSubentry(
                    data=MappingProxyType({CONF_GROUP_MODES: list(old_modes)}),
                    subentry_type=SUBENTRY_SENSOR_GROUP,
                    title=title,
                    unique_id=None,
                )
                hass.config_entries.async_add_subentry(entry, group)
                group_for[old_modes] = group.subentry_id
            data[CONF_SENSOR_GROUPS] = [group_for[old_modes]]
        hass.config_entries.async_update_subentry(entry, sub, data=data)


def _v2_to_v3(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Move the items from config subentries (always listed on Devices & services) to the options.

    The entities and devices that hung under a subentry are first attached to the entry itself:
    removing a subentry would remove them, and they must keep their ids and history.
    """
    items = {
        sid: stored(sub.subentry_type, sub.title, dict(sub.data)) for sid, sub in entry.subentries.items()
    }
    hass.config_entries.async_update_entry(entry, options={**entry.options, OPTION_KEY: items})
    ent_reg = er.async_get(hass)
    for ent in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if ent.config_subentry_id is not None:
            ent_reg.async_update_entity(ent.entity_id, config_subentry_id=None)
    dev_reg = dr.async_get(hass)
    for dev in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        for sid in list(dev.config_entries_subentries.get(entry.entry_id, ())):
            if sid is None:
                continue
            dev_reg.async_update_device(
                dev.id, add_config_entry_id=entry.entry_id, add_config_subentry_id=None
            )
            dev_reg.async_update_device(
                dev.id, remove_config_entry_id=entry.entry_id, remove_config_subentry_id=sid
            )
    for sid in list(entry.subentries):
        hass.config_entries.async_remove_subentry(entry, sid)
