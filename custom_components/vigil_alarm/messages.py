"""Texts of the notifications.

Home Assistant's translation files cannot hold free-form message templates for
a custom integration, so the notification texts live here, per language. To
add a language, add a dictionary to MESSAGES (missing keys fall back to English).
"""

from __future__ import annotations

from typing import Any

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "title": "Vigil Alarm",
        "triggered": "ALARM: {cause} ({sensor})",
        "cause_changed": "Alarm changed to: {cause} ({sensor})",
        "pending": "Entry delay started by {sensor}, until {end}",
        "armed": "Armed ({mode}){by}",
        "disarmed": "Disarmed{by}",
        "arm_refused": "Arming refused: {reason} ({sensors})",
        "supervision_lost": "Sensor lost: {sensor}",
        "supervision_restored": "Sensor back: {sensor}",
        "unconfirmed": "Single trigger without confirmation: {sensor} (rule {rule})",
        "unconfirmed_escalated": "Unconfirmed trigger in rule {rule}: {sensors}",
        "bypassed_at_arm": "Armed with {sensor} bypassed ({reason})",
        "technical_started": "{cause} alarm: {sensor}",
        "technical_ended": "{cause} alarm over: {sensor} ({reason})",
        "restore_failed": "Saved alarm state was unusable; started disarmed",
        "siren_failed": "Siren {siren} failed ({error})",
        "siren_unavailable": "Siren {siren} is unavailable",
        "siren_available": "Siren {siren} is available again",
        "siren_power_lost": "Siren {siren} lost mains power and runs on its battery",
        "siren_power_restored": "Siren {siren} is on mains power again",
        "battery_low": "Battery low: {name} ({level}%)",
        "battery_ok": "Battery ok again: {name}",
        "silenced": "Alarm silenced{by}",
        "acknowledged": "Alarm acknowledged{by}",
        "test": "Test notification from Vigil Alarm",
        "no_siren": "No siren is connected.",
        "cause.intrusion": "intrusion",
        "cause.fire": "fire",
        "cause.gas": "gas",
        "cause.tamper": "tamper",
        "cause.fault": "sensor fault",
        "cause.water": "water",
        "reason.not_disarmed": "not disarmed",
        "reason.alarm_condition": "an alarm condition is open",
        "reason.sensor_unavailable": "a sensor is unavailable",
        "reason.sensor_open": "a sensor is open",
        "reason.open": "was open",
        "reason.unavailable": "was unavailable",
        "reason.closed": "closed",
        "reason.bypassed": "bypassed",
        "by": " by {user}",
    },
    "nl": {
        "title": "Vigil Alarm",
        "triggered": "ALARM: {cause} ({sensor})",
        "cause_changed": "Alarm gewijzigd naar: {cause} ({sensor})",
        "pending": "Inlooptijd gestart door {sensor}, tot {end}",
        "armed": "Ingeschakeld ({mode}){by}",
        "disarmed": "Uitgeschakeld{by}",
        "arm_refused": "Inschakelen geweigerd: {reason} ({sensors})",
        "supervision_lost": "Sensor valt weg: {sensor}",
        "supervision_restored": "Sensor weer bereikbaar: {sensor}",
        "unconfirmed": "Eén melding zonder bevestiging: {sensor} (regel {rule})",
        "unconfirmed_escalated": "Onbevestigde melding door regel {rule}: {sensors}",
        "bypassed_at_arm": "Ingeschakeld met {sensor} omzeild ({reason})",
        "technical_started": "{cause}alarm: {sensor}",
        "technical_ended": "{cause}alarm voorbij: {sensor} ({reason})",
        "restore_failed": "Bewaarde alarmstatus was onbruikbaar; gestart als uitgeschakeld",
        "siren_failed": "Sirene {siren} faalt ({error})",
        "siren_unavailable": "Sirene {siren} is onbereikbaar",
        "siren_available": "Sirene {siren} is weer bereikbaar",
        "siren_power_lost": "Sirene {siren} heeft geen netstroom meer en draait op batterij",
        "siren_power_restored": "Sirene {siren} heeft weer netstroom",
        "battery_low": "Batterij bijna leeg: {name} ({level}%)",
        "battery_ok": "Batterij weer in orde: {name}",
        "silenced": "Alarm gedempt{by}",
        "acknowledged": "Alarm bevestigd{by}",
        "test": "Testmelding van Vigil Alarm",
        "no_siren": "Er is geen sirene gekoppeld.",
        "cause.intrusion": "inbraak",
        "cause.fire": "brand",
        "cause.gas": "gas",
        "cause.tamper": "sabotage",
        "cause.fault": "sensorstoring",
        "cause.water": "water",
        "reason.not_disarmed": "niet uitgeschakeld",
        "reason.alarm_condition": "een alarmmelding staat open",
        "reason.sensor_unavailable": "een sensor is onbereikbaar",
        "reason.sensor_open": "een sensor staat open",
        "reason.open": "stond open",
        "reason.unavailable": "was onbereikbaar",
        "reason.closed": "gesloten",
        "reason.bypassed": "omzeild",
        "by": " door {user}",
    },
}


def text(language: str, key: str) -> str:
    base = language.split("-")[0]
    return MESSAGES.get(language, MESSAGES.get(base, {})).get(key) or MESSAGES["en"][key]


def render(language: str, key: str, **params: Any) -> str:
    return text(language, key).format(**params)


MODE_NAMES = {
    "en": {"home": "Home", "away": "Away", "night": "Night"},
    "nl": {"home": "Thuis", "away": "Weg", "night": "Nacht"},
}


def mode_name(language: str, mode: str) -> str:
    names = MODE_NAMES.get(language.split("-")[0], MODE_NAMES["en"])
    return names.get(mode, mode)
