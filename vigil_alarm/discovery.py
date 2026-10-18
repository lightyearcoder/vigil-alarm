"""Find sensors in the entity registry that can be added to the alarm.

Generic on purpose: only standard Home Assistant data is used (domain, device class, the device an
entity belongs to, entity category, unit). Nothing here knows about a specific integration, so
Zigbee2MQTT, ZHA, Z-Wave, Matter and others are treated the same way.

The result is a proposal. Nothing is saved until the person confirms it in the panel.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import (
    CONF_BATTERY_ENTITY,
    CONF_SUGGEST_FOR,
    CONF_TAMPER_ENTITY,
    DOMAIN,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
)
from .items import items_of

# device class of a binary_sensor -> (alarm class, zone). zone is the group the panel proposes.
PRIMARY: dict[str, tuple[str, str | None]] = {
    "door": ("intrusion", "perimeter"),
    "window": ("intrusion", "perimeter"),
    "garage_door": ("intrusion", "perimeter"),
    "opening": ("intrusion", "perimeter"),
    "motion": ("intrusion", "interior"),
    "occupancy": ("intrusion", "interior"),
    "presence": ("intrusion", "interior"),
    "smoke": ("fire", None),
    "gas": ("gas", None),
    "carbon_monoxide": ("gas", None),
    "moisture": ("water", None),
}
# Opening sensors are the ones people walk through; the panel offers "entrance" for them.
ENTRANCE_CLASSES = {"door", "garage_door", "opening"}


def _device_class(entry: er.RegistryEntry) -> str | None:
    return entry.device_class or entry.original_device_class


def _usable(entry: er.RegistryEntry) -> bool:
    # Vigil's own entities (its alarm indicators) are not sensors to watch.
    return entry.disabled_by is None and entry.hidden_by is None and entry.platform != DOMAIN


def _used_entities(vigil: ConfigEntry) -> set[str]:
    used: set[str] = set()
    for item in items_of(vigil).values():
        if item.subentry_type != SUBENTRY_SENSOR:
            continue
        for key in ("entity_id", CONF_BATTERY_ENTITY, CONF_TAMPER_ENTITY):
            if item.data.get(key):
                used.add(item.data[key])
    return used


def _name(hass: HomeAssistant, entry: er.RegistryEntry, devices: dr.DeviceRegistry) -> str:
    device = devices.async_get(entry.device_id) if entry.device_id else None
    if device is not None:
        return device.name_by_user or device.name or entry.entity_id
    return entry.name or entry.original_name or entry.entity_id


def async_discover(hass: HomeAssistant, vigil: ConfigEntry) -> dict[str, Any]:
    """Candidates grouped by device, with the battery and tamper entity of the same device."""
    registry = er.async_get(hass)
    devices = dr.async_get(hass)
    used = _used_entities(vigil)
    # The groups the person marked as "suggest for new sensors" decide where a proposal goes.
    groups = {"perimeter": [], "interior": []}
    for gid, item in items_of(vigil).items():
        if item.subentry_type == SUBENTRY_SENSOR_GROUP:
            kind = {"contacts": "perimeter", "motion": "interior"}.get(item.data.get(CONF_SUGGEST_FOR))
            if kind:
                groups[kind].append(gid)

    primaries: list[er.RegistryEntry] = []
    batteries: dict[str, list[er.RegistryEntry]] = {}
    tampers: dict[str, list[er.RegistryEntry]] = {}
    low_flags: dict[str, list[er.RegistryEntry]] = {}
    for ent in registry.entities.values():
        if not _usable(ent):
            continue
        cls = _device_class(ent)
        if ent.domain == "binary_sensor" and cls in PRIMARY:
            primaries.append(ent)
        elif ent.domain == "binary_sensor" and cls == "tamper":
            tampers.setdefault(ent.device_id or "", []).append(ent)
        elif ent.domain == "sensor" and cls == "battery" and ent.device_id:
            if ent.unit_of_measurement in (None, "%"):
                batteries.setdefault(ent.device_id, []).append(ent)
        elif ent.domain == "binary_sensor" and cls == "battery" and ent.device_id:
            low_flags.setdefault(ent.device_id, []).append(ent)  # "battery low", on = low

    candidates: list[dict[str, Any]] = []
    claimed_tampers: set[str] = set()
    for ent in sorted(primaries, key=lambda e: e.entity_id):
        cls = _device_class(ent)
        alarm_class, zone = PRIMARY[cls]  # type: ignore[index]
        battery = tamper = None
        if ent.device_id:
            # A percentage is better than a "battery low" flag; use the flag only when there is no percentage.
            both = batteries.get(ent.device_id) or low_flags.get(ent.device_id) or []
            battery = next(iter(sorted(both, key=lambda e: e.entity_id)), None)
            tamper = next(iter(sorted(tampers.get(ent.device_id, []), key=lambda e: e.entity_id)), None)
            if tamper is not None:
                claimed_tampers.add(tamper.entity_id)
        candidates.append(
            {
                "entity_id": ent.entity_id,
                "name": _name(hass, ent, devices),
                "device_class": cls,
                "platform": ent.platform,
                "cls": alarm_class,
                "zone": zone,
                "entrance": cls in ENTRANCE_CLASSES,
                "groups": groups.get(zone or "", []),
                "battery_entity": battery.entity_id if battery else None,
                "tamper_entity": tamper.entity_id if tamper else None,
                "in_use": ent.entity_id in used,
            }
        )

    # A tamper contact on a device with no primary sensor on it is offered on its own.
    loose = [
        {
            "entity_id": t.entity_id,
            "name": _name(hass, t, devices),
            "device_class": "tamper",
            "platform": t.platform,
            "in_use": t.entity_id in used,
        }
        for ents in tampers.values()
        for t in sorted(ents, key=lambda e: e.entity_id)
        if t.entity_id not in claimed_tampers
    ]
    return {"candidates": candidates, "tamper_only": loose}


def async_report(hass: HomeAssistant) -> dict[str, Any]:
    """An anonymous list for testers: no names, no addresses, only what discovery looks at.

    Entities are numbered per device so that "these belong together" survives, without any id
    that could say where the device is or what it is called.
    """
    registry = er.async_get(hass)
    device_numbers: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    for ent in registry.entities.values():
        if ent.domain not in ("binary_sensor", "sensor") or not _usable(ent):
            continue
        cls = _device_class(ent)
        if cls not in PRIMARY and cls not in ("tamper", "battery"):
            continue
        number = None
        if ent.device_id:
            number = device_numbers.setdefault(ent.device_id, len(device_numbers) + 1)
        rows.append(
            {
                "domain": ent.domain,
                "device_class": cls,
                "platform": ent.platform,
                "device": number,
                "entity_category": ent.entity_category.value if ent.entity_category else None,
                "unit": ent.unit_of_measurement,
            }
        )
    rows.sort(key=lambda r: (r["device"] or 0, r["domain"], r["device_class"] or ""))
    return {"entities": rows}
