"""Helpers to build a Vigil config entry with sensors, rules and users."""

from __future__ import annotations

from homeassistant.config_entries import ConfigSubentryData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vigil_alarm.const import DOMAIN
from custom_components.vigil_alarm.credentials import hash_code

PANEL = "alarm_control_panel.vigil_alarm"
EVENTS = "event.vigil_alarm_alarm_events"


def user_data(code: str | None = None, **extra) -> dict:
    data = {"tags": [], "allowed_modes": [], "may_bypass_tamper": False, **extra}
    if code:
        data["code_hash"], data["code_salt"] = hash_code(code)
        data["code_numeric"] = code.isdigit()
    return data


def sub(kind: str, title: str, data: dict, sid: str) -> ConfigSubentryData:
    return ConfigSubentryData(subentry_type=kind, title=title, data=data, subentry_id=sid, unique_id=None)


def make_entry(*, users=True, extra_subentries=(), **data) -> MockConfigEntry:
    base = {
        "modes": ["home", "away", "night"],
        "exit_delay_home": 0,
        "exit_delay_away": 60,
        "exit_delay_night": 10,
        "default_entry_delay": 30,
        "trigger_time": 0,
        "code_arm_required": True,
    }
    base.update(data)
    subs = [
        sub("zone", "Front door", {"entity_id": "binary_sensor.front_door", "cls": "intrusion",
            "type": "delayed", "sensor_groups": ["g_all"], "at_arm_open": "bypass"}, "front"),
        sub("zone", "Living PIR", {"entity_id": "binary_sensor.living_pir", "cls": "intrusion",
            "type": "instant", "sensor_groups": ["g_away"], "at_arm_open": "wait_clear"}, "living"),
        sub("zone", "Smoke", {"entity_id": "binary_sensor.smoke", "cls": "fire"}, "smoke"),
        sub("zone", "Tamper", {"entity_id": "binary_sensor.tamper", "cls": "tamper"}, "tamper"),
    ]
    subs.extend([
        sub("sensor_group", "All modes", {"modes": ["home", "away", "night"]}, "g_all"),
        sub("sensor_group", "Away only", {"modes": ["away"]}, "g_away"),
        sub("sensor_group", "Home only", {"modes": ["home"]}, "g_home"),
    ])
    if users:
        subs.append(sub("user", "Anna", user_data("1234", allowed_modes=[]), "anna"))
        subs.append(sub("user", "Bob", user_data("5678", allowed_modes=["home"]), "bob"))
    subs.extend(extra_subentries)
    items = {d["subentry_id"]: {"type": d["subentry_type"], "title": d["title"], "data": d["data"]} for d in subs}
    return MockConfigEntry(domain=DOMAIN, title="Vigil Alarm", data=base, options={"items": items},
                           unique_id=DOMAIN, version=3)
