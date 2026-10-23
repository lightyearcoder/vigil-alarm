"""Presets: ready-made settings for known devices. Data only; the panel applies them to the siren form.

Everything here is a suggestion the person can still change. Entities are only suggested when they
belong to the same device as the siren/switch the person picked as the control.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

# role -> (entity domain, the Zigbee2MQTT expose name that appears in the entity's unique id)
_Z2M_SNZB_09P_ROLES = {
    "light": ("switch", "alarm_light_enable"),
    "tone_entity": ("select", "alarm_sound_type"),
    "volume_entity": ("select", "alarm_volume_level"),
    "battery_entity": ("sensor", "battery"),
    "power_entity": ("sensor", "power_supply_mode"),
}

SIREN_PRESETS: dict[str, dict[str, Any]] = {
    # Values checked against the Zigbee2MQTT device page for the SNZB-09P (exposes and allowed values).
    "sonoff_snzb_09p_z2m": {
        "roles": _Z2M_SNZB_09P_ROLES,
        "values": {
            "max_duration": 180,
            "power_battery_value": "battery",
            "intrusion": {"tone": "siren_classic", "volume": "high"},
            "fire": {"tone": "siren_warning", "volume": "max"},
            "gas": {"tone": "siren_emergency", "volume": "max"},
            "tamper": {"tone": "siren_rapid", "volume": "high"},
        },
    },
}

# The frient / Develco SMSZB-120 smoke alarm: its siren is one switch (`alarm`, the simple command); tone, volume, flash
# light and power mode are not settable. It stops by itself after its own `max_duration` (240 s by default).
SIREN_PRESETS["frient_smszb_120_z2m"] = {
    "roles": {"battery_entity": ("sensor", "battery")},
    "values": {"max_duration": 240},
}


def siren_preset_ids() -> list[str]:
    return list(SIREN_PRESETS)


def siren_suggestion(hass: HomeAssistant, preset_id: str, control: str | None) -> dict[str, Any] | None:
    """The values and the entities (found on the control's device) for a preset, or None if unknown."""
    preset = SIREN_PRESETS.get(preset_id)
    if preset is None:
        return None
    values: dict[str, Any] = {k: (dict(v) if isinstance(v, dict) else v) for k, v in preset["values"].items()}
    found: list[str] = []
    registry = er.async_get(hass)
    own = registry.async_get(control) if control else None
    if own is not None and own.device_id:
        siblings = [e for e in er.async_entries_for_device(registry, own.device_id) if not e.disabled]
        for role, (domain, expose) in preset["roles"].items():
            match = next(
                (e for e in siblings if e.domain == domain and _is_expose(e.unique_id, expose)), None
            )
            if match:
                values[role] = match.entity_id
                found.append(role)
    return {"values": values, "found": found}


def _is_expose(unique_id: str, expose: str) -> bool:
    """Zigbee2MQTT unique ids look like `0x00124b0012345678_alarm_sound_type_zigbee2mqtt`."""
    parts = unique_id.split("_", 1)[-1]
    return parts == expose or parts.startswith(f"{expose}_")
