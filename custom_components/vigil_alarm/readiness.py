"""The "ready for use?" check and the default sensor groups.

The check looks at the configuration only; it changes nothing. Every finding has a code that the
panel shows as text, a level ("problem": the alarm does not protect yet, "advice": it works but
could be better), optional values for the text, and where to go to fix it.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_BATTERY_ENTITY,
    CONF_CODE_ARM_REQUIRED,
    CONF_CODE_HASH,
    CONF_GROUP_MODES,
    CONF_MODES,
    CONF_SENSOR_GROUPS,
    CONF_SUGGEST_FOR,
    CONF_TAMPER_ENTITY,
    CONF_COMPANION_OF,
    DEFAULT_MODES,
    SUBENTRY_NOTIFICATION,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
    SUBENTRY_SIREN,
    SUBENTRY_PARTITION,
    CONF_PARTITION,
    PRIMARY_PARTITION,
    SUBENTRY_USER,
)
from .editing import notify_services
from .items import Item, channel_services, items_of, new_id, save_stored, stored, stored_items
from .manager import partition_data
from .languages import GROUP_NAMES, language_of

MAX_NAMES = 3
PHONE_PREFIX = "mobile_app_"


def phone_services(hass: HomeAssistant, entry: ConfigEntry) -> list[str]:
    """notify services of the Home Assistant app on a phone that no channel uses yet."""
    used = {s for i in items_of(entry).values() if i.subentry_type == SUBENTRY_NOTIFICATION for s in channel_services(i.data)}
    return [n for n in notify_services(hass) if n.startswith(PHONE_PREFIX) and n not in used]


def phone_title(service: str) -> str:
    return service.removeprefix(PHONE_PREFIX).replace("_", " ").strip().title() or service


def _names(items: list[Item]) -> str:
    titles = sorted(i.title for i in items)
    shown = ", ".join(titles[:MAX_NAMES])
    return shown + (f" +{len(titles) - MAX_NAMES}" if len(titles) > MAX_NAMES else "")


def _finding(code: str, level: str, go: str, **params: Any) -> dict[str, Any]:
    return {"code": code, "level": level, "go": go, "params": {k: str(v) for k, v in params.items()}}


def async_readiness(hass: HomeAssistant, entry: ConfigEntry) -> list[dict[str, Any]]:
    """Everything that stops the alarm from protecting, or could make it better. Empty = ready."""
    items = items_of(entry)
    of = lambda kind: [i for i in items.values() if i.subentry_type == kind]  # noqa: E731
    sensors = [s for s in of(SUBENTRY_SENSOR) if not s.data.get(CONF_COMPANION_OF)]
    groups = of(SUBENTRY_SENSOR_GROUP)
    modes = list(entry.data.get(CONF_MODES, DEFAULT_MODES))
    found: list[dict[str, Any]] = []

    if not sensors:
        found.append(_finding("no_sensors", "problem", "sensor"))
    intrusion = [s for s in sensors if s.data.get("cls") == "intrusion"]
    if not groups:
        found.append(_finding("no_sensor_groups", "problem", "create_groups"))
    else:
        # Every partition on its own: a mode of the garage is not watched by the sensors of the house.
        parts = [(PRIMARY_PARTITION, "", modes)] + [
            (i.subentry_id, i.title, list(i.data.get(CONF_MODES, DEFAULT_MODES)))
            for i in items.values() if i.subentry_type == SUBENTRY_PARTITION
        ]
        known = {p for p, _t, _m in parts}
        for pid, title, pmodes in parts:
            mine = [s for s in intrusion if (s.data.get(CONF_PARTITION) if s.data.get(CONF_PARTITION) in known
                                              else PRIMARY_PARTITION) == pid]
            if not mine:
                if pid != PRIMARY_PARTITION:
                    found.append(_finding("partition_empty", "problem", "sensor", partition=title))
                continue
            watched = {
                mode
                for s in mine
                for gid in s.data.get(CONF_SENSOR_GROUPS) or []
                for g in groups
                if g.subentry_id == gid
                for mode in g.data.get(CONF_GROUP_MODES) or []
            }
            unwatched = [m for m in pmodes if m not in watched]
            if unwatched and pid == PRIMARY_PARTITION:
                found.append(_finding("mode_unwatched", "problem", "sensor_group", modes=", ".join(unwatched)))
            elif unwatched:
                found.append(_finding("partition_unwatched", "problem", "sensor_group", partition=title, modes=", ".join(unwatched)))
    if not any(u.data.get(CONF_CODE_HASH) for u in of(SUBENTRY_USER)):
        found.append(_finding("no_user_code", "problem", "user"))
    if any(u.data.get(CONF_CODE_HASH) for u in of(SUBENTRY_USER)) and not entry.data.get(CONF_CODE_ARM_REQUIRED, True):
        found.append(_finding("arm_without_code", "advice", "settings"))
    if not of(SUBENTRY_NOTIFICATION):
        phones = phone_services(hass, entry)
        finding = _finding("no_notification", "problem", "add_phone" if phones else "notification")
        finding["phones"] = [{"service": n, "title": phone_title(n)} for n in phones]
        found.append(finding)
    if not of(SUBENTRY_SIREN):
        found.append(_finding("no_siren", "advice", "siren"))

    guarded = [s for s in sensors if s.data.get("cls") in ("intrusion", "fire", "gas", "water")]
    no_battery = [s for s in guarded if not s.data.get(CONF_BATTERY_ENTITY)]
    if no_battery:
        found.append(_finding("battery_missing", "advice", "sensor", n=len(no_battery), names=_names(no_battery)))

    # A tamper contact on the same device that is not connected to anything.
    registry = er.async_get(hass)
    used = {i.data.get(k) for i in items.values() for k in ("entity_id", CONF_TAMPER_ENTITY)}
    unlinked: list[Item] = []
    for s in guarded:
        if s.data.get(CONF_TAMPER_ENTITY):
            continue
        ent = registry.async_get(s.data.get("entity_id") or "")
        if ent is None or not ent.device_id:
            continue
        if any(
            e.domain == "binary_sensor"
            and (e.device_class or e.original_device_class) == "tamper"
            and e.entity_id not in used
            for e in er.async_entries_for_device(registry, ent.device_id)
        ):
            unlinked.append(s)
    if unlinked:
        found.append(_finding("tamper_unlinked", "advice", "sensor", n=len(unlinked), names=_names(unlinked)))
    manager = getattr(entry, "runtime_data", None)
    if manager is not None:
        for problem in manager.panels.problems():
            code = problem.pop("code")
            found.append(_finding(code, "advice", "panel", **problem))
    return found


def _group_names(language: str) -> dict[str, str]:
    return GROUP_NAMES[language_of(language)]


def async_create_default_groups(hass: HomeAssistant, entry: ConfigEntry, partition: str = PRIMARY_PARTITION) -> list[str]:
    """Add the two usual groups to a partition, but only the kinds that partition does not have yet. A group of
    another partition than the first gets the name of the partition behind its name. Returns the new ids."""
    items = items_of(entry)
    mine = [
        i for i in items.values()
        if i.subentry_type == SUBENTRY_SENSOR_GROUP and (i.data.get(CONF_PARTITION) or PRIMARY_PARTITION) == partition
    ]
    have = {i.data.get(CONF_SUGGEST_FOR) for i in mine}
    taken = {i.title for i in items.values() if i.subentry_type == SUBENTRY_SENSOR_GROUP}
    modes = list(partition_data(entry, partition).get(CONF_MODES) or DEFAULT_MODES)
    suffix = ""
    if partition != PRIMARY_PARTITION:
        suffix = f" ({items[partition].title})"
    wanted = {"contacts": modes, "motion": ["away"] if "away" in modes else modes}
    working = stored_items(entry)
    created: list[str] = []
    for kind, name in _group_names(hass.config.language).items():
        name += suffix
        if kind in have or name in taken:
            continue
        gid = new_id()
        data = {CONF_GROUP_MODES: wanted[kind], CONF_SUGGEST_FOR: kind}
        if partition != PRIMARY_PARTITION:
            data[CONF_PARTITION] = partition
        working[gid] = stored(SUBENTRY_SENSOR_GROUP, name, data)
        created.append(gid)
    if created:
        save_stored(hass, entry, working)
    return created
