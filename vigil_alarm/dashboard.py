"""A dashboard for this installation, with the real entity ids filled in.

It uses only standard Home Assistant cards. The person copies it into a new dashboard
(raw configuration editor), so nothing here changes anything in Home Assistant.
"""

from __future__ import annotations

from typing import Any

import yaml
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import CONF_COMPANION_OF, DOMAIN, SUBENTRY_SENSOR
from .items import items_of

HEADER = """\
# Dashboard for Vigil Alarm, made for this installation.
# Settings > Dashboards > Add dashboard > "New dashboard from scratch", open it, then
# top right: pencil > three dots > "Raw configuration editor". Paste everything below and save.
"""


def async_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> str:
    registry = er.async_get(hass)
    eid = entry.entry_id

    def find(domain: str, unique: str) -> str | None:
        return registry.async_get_entity_id(domain, DOMAIN, unique)

    alarm = find("alarm_control_panel", eid) or "alarm_control_panel.vigil_alarm"
    alarms = [
        e for e in (
            *(find("binary_sensor", f"{eid}_active_{cls}") for cls in ("intrusion", "fire", "tamper", "gas")),
            find("binary_sensor", f"{eid}_technical"),
        ) if e
    ]
    last_event = find("sensor", f"{eid}_last_event")
    events = find("event", f"{eid}_events")

    status_rows: list[dict[str, Any]] = []
    bypass_rows: list[dict[str, Any]] = []
    for sid, item in items_of(entry).items():
        if item.subentry_type != SUBENTRY_SENSOR or item.data.get(CONF_COMPANION_OF):
            continue
        status = find("sensor", f"{eid}_{sid}_status")
        bypass = find("switch", f"{eid}_{sid}_bypass")
        if status:
            status_rows.append({"entity": status, "name": item.title})
        if bypass:
            bypass_rows.append({"entity": bypass, "name": item.title})

    content = (
        "{% set a = '" + alarm + "' %}\n"
        "**{{ states(a) | replace('_', ' ') | capitalize }}**\n"
        "{% if state_attr(a, 'changed_by') %} (by {{ state_attr(a, 'changed_by') }}){% endif %}\n\n"
        "{% if state_attr(a, 'cause') %}Alarm cause: **{{ state_attr(a, 'cause') }}**\n"
        "{% if state_attr(a, 'cause_sensor') %}, sensor: **{{ state_attr(a, 'cause_sensor') }}**{% endif %}\n{% endif %}\n"
        "{% if state_attr(a, 'open_sensors') %}Open: {{ state_attr(a, 'open_sensors') | join(', ') }}\n{% endif %}\n"
        "{% if state_attr(a, 'bypassed_sensors') %}Bypassed: {{ state_attr(a, 'bypassed_sensors') | join(', ') }}\n{% endif %}\n"
    )
    cards: list[dict[str, Any]] = [
        {"type": "alarm-panel", "entity": alarm, "name": "Alarm", "states": ["arm_home", "arm_away", "arm_night"]},
        {"type": "markdown", "title": "Status", "content": content},
    ]
    if alarms or last_event:
        rows: list[dict[str, Any]] = [{"entity": e} for e in alarms]
        if last_event:
            rows.append({"entity": last_event, "name": "Last event"})
        cards.append({"type": "entities", "title": "Alarms", "show_header_toggle": False, "entities": rows})
    if status_rows:
        rows = [{"type": "section", "label": "Status"}, *status_rows]
        if bypass_rows:
            rows += [{"type": "section", "label": "Bypass (leave a sensor out for now)"}, *bypass_rows]
        cards.append({"type": "entities", "title": "Sensors", "show_header_toggle": False, "entities": rows})
    if events:
        cards.append({"type": "logbook", "title": "History", "hours_to_show": 48, "target": {"entity_id": events}})
    cards.append({
        "type": "button", "name": "Silence the siren", "icon": "mdi:bell-off",
        "tap_action": {"action": "perform-action", "perform_action": "vigil_alarm.silence",
                       "confirmation": {"text": "Silence the siren?"}},
    })
    board = {"title": "Alarm", "views": [{"title": "Alarm", "path": "alarm", "icon": "mdi:shield-home", "cards": cards}]}
    return HEADER + yaml.safe_dump(board, sort_keys=False, allow_unicode=True, width=100)
