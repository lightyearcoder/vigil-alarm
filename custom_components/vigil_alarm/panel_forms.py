"""The admin panel: names, addresses and the form of every kind (what the panel shows to fill in)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .const import (
    ABORT_SECONDS_RANGE,
    ALL_PARTITIONS,
    BACKUP_VERSIONS_RANGE,
    CHIME_DOMAINS,
    CHIME_SECONDS_RANGE,
    CONF_BATTERY_ENTITY,
    CONF_FOR,
    CONF_MAINS_POWERED,
    CONF_MAX_VALUE,
    CONF_MIN_VALUE,
    CONF_PERMANENT_BYPASS,
    CONF_TAMPER_ENTITY,
    DEFAULT_ABORT_SECONDS,
    DEFAULT_CHIME_SECONDS,
    DEFAULT_EXIT_DELAY,
    DEFAULT_MODES,
    DEFAULT_PARTITION_RETURN_SECONDS,
    DEFAULT_SCREEN_OFF_ON_ALARM,
    DEFAULT_SOUND,
    DEFAULT_SOUND_CHANGES,
    DEFAULT_SOUND_DELAYS,
    DEFAULT_SOUND_VOLUME,
    DEFAULT_UNLOCK_SECONDS,
    HEARTBEAT_INTERVAL_RANGE,
    LOCK_TRIES_RANGE,
    LOCK_WAIT_RANGE,
    LOG_RETENTION_CEILING,
    LOG_RETENTION_FLOOR,
    MIN_CODE_LENGTH_CEILING,
    MIN_CODE_LENGTH_FLOOR,
    MODES,
    NOTIFICATION_CATEGORIES,
    PARTITION_RETURN_RANGE,
    PRIMARY_PARTITION,
    PROFILE_CAUSES,
    SCREEN_OFF_RANGE,
    SELFTEST_RANGES,
    SENSOR_LIST_CHOICES,
    SIREN_CAUSES,
    SOUND_VOLUME_RANGE,
    STARTUP_WAIT_RANGE,
    SUBENTRY_NOTIFICATION,
    SUBENTRY_PANEL,
    SUBENTRY_PARTITION,
    SUBENTRY_RULE,
    SUBENTRY_SENSOR,
    SUBENTRY_SENSOR_GROUP,
    SUBENTRY_SIREN,
    SUBENTRY_USER,
    SUGGEST_FOR,
    UNLOCK_SECONDS_RANGE,
)
from .languages import LANGUAGES
from .vigil_core.model import (
    AT_ARM_OPEN,
    CLASSES,
    GAS_TYPES,
    ON_UNAVAILABLE,
    SENSOR_TYPES,
)


def _event_labels() -> dict[str, dict[str, str]]:
    """The names of the event types, in each language, from the translation files."""
    out: dict[str, dict[str, str]] = {}
    for lang in LANGUAGES:
        data = json.loads((Path(__file__).parent / "translations" / f"{lang}.json").read_text(encoding="utf-8"))
        out[lang] = data["entity"]["event"]["alarm_events"]["state_attributes"]["event_type"]["state"]
    return out


_EVENT_LABELS = _event_labels()
_VERSION = json.loads((Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))["version"]
# The names the panel uses, and the subentry types they are stored under.
TYPE_OF = {
    "sensor": SUBENTRY_SENSOR,
    "sensor_group": SUBENTRY_SENSOR_GROUP,
    "rule": SUBENTRY_RULE,
    "user": SUBENTRY_USER,
    "notification": SUBENTRY_NOTIFICATION,
    "siren": SUBENTRY_SIREN,
    "panel": SUBENTRY_PANEL,
    "partition": SUBENTRY_PARTITION,
}
KINDS = tuple(TYPE_OF)


# --------------------------------------------------------------- form schema


def _f(key: str, type_: str, **kw: Any) -> dict[str, Any]:
    return {"key": key, "type": type_, **kw}


def form_schema(modes: list[str], house: Mapping[str, Any] | None = None) -> dict[str, list[dict[str, Any]]]:
    """Describe the forms; the panel renders them (labels live in the panel).

    `house` is the first partition: a new partition starts with its modes and times."""
    house = house or {}
    house_modes = [m for m in modes if m in (house.get("modes") or DEFAULT_MODES)] or list(modes)

    def delay(mode: str) -> Any:
        return house.get(f"exit_delay_{mode}", DEFAULT_EXIT_DELAY.get(mode, 0))

    intrusion = {"cls": ["intrusion"]}
    return {
        "sensor": [
            _f("name", "text", required=True),
            _f("entity_id", "entity", domains=["binary_sensor", "sensor"], required=True),
            _f("cls", "select", options=list(CLASSES), default="intrusion", required=True),
            _f("type", "select", options=list(SENSOR_TYPES), default="instant", show_if=intrusion),
            _f("partition", "partition", default=PRIMARY_PARTITION, show_if=intrusion),
            _f("tamper_partition", "partition", default=ALL_PARTITIONS, show_if={"cls": ["tamper"]}),
            _f("sensor_groups", "sensor_groups", default=[], required=True, show_if=intrusion),
            _f("at_arm_open", "select", options=list(AT_ARM_OPEN), default="bypass", show_if=intrusion),
            _f("entry_delay", "number", unit="s", min=0, max=600, show_if=intrusion),
            _f("gas_type", "select", options=list(GAS_TYPES), default="other", show_if={"cls": ["gas"]}),
            _f(CONF_MIN_VALUE, "number", show_if={"cls": ["silent24"]}),
            _f(CONF_MAX_VALUE, "number", show_if={"cls": ["silent24"]}),
            _f(CONF_FOR, "number", unit="s", min=0, default=0, show_if={"cls": ["silent24"]}),
            _f("on_unavailable", "select", options=["default", *ON_UNAVAILABLE], default="default"),
            _f(CONF_MAINS_POWERED, "boolean", default=False, show_if={"cls": ["intrusion", "fire", "gas", "water"]}),
            _f(CONF_BATTERY_ENTITY, "entity", domains=["sensor", "binary_sensor"], show_if={CONF_MAINS_POWERED: [False]}),
            _f(CONF_TAMPER_ENTITY, "entity", domains=["binary_sensor"], show_if={"cls": ["intrusion", "fire", "gas", "water", "alarm24", "silent24"]}),
            _f("chime", "boolean", default=False, show_if=intrusion),
            _f(CONF_PERMANENT_BYPASS, "boolean", default=False, show_if={"cls": ["intrusion", "tamper", "water", "alarm24", "silent24"]}),
        ],
        "sensor_group": [
            _f("name", "text", required=True),
            _f("partition", "partition", default=PRIMARY_PARTITION),
            _f("modes", "multiselect", options=modes, default=[], required=True),
            _f("suggest_for", "select", options=["", *SUGGEST_FOR], default=""),
        ],
        "rule": [
            _f("name", "text", required=True),
            _f("sensors", "sensors", required=True),
            _f("required", "number", default=2, min=2, max=10, required=True),
            _f("window", "number", default=60, unit="s", min=0, max=3600, required=True),
            _f("escalate", "boolean", default=False),
        ],
        "user": [
            _f("name", "text", required=True),
            _f("code", "password"),
            _f("duress_code", "password"),
            _f("tags", "tags", default=[]),
            _f("partitions", "partitions", default=[], required=True),
            _f("allowed_modes", "multiselect", options=modes, default=[]),
            _f("may_bypass", "boolean", default=False),
            _f("may_bypass_tamper", "boolean", default=False, show_if={"may_bypass": [True]}),
        ],
        "notification": [
            _f("name", "text", required=True),
            _f("services", "notify", default=[], required=True),
            _f("categories", "multiselect", options=list(NOTIFICATION_CATEGORIES),
               default=["alarm", "pending", "fault", "technical"], required=True),
            _f("delay", "number", default=0, unit="s", min=0, max=3600),
            _f("priority", "boolean", default=False),
            _f("partitions", "partitions", default=[], required=True),
        ],
        "panel": [
            _f("name", "text", required=True),
            _f("device", "select", options=["esphome", "account"], default="esphome", required=True),
            _f("panel_id", "text", required=True, show_if={"device": ["esphome"]}),
            _f("ha_user", "ha_user", required=True, show_if={"device": ["account"]}),
            _f("language", "select", options=list(LANGUAGES), default="en"),
            _f("partitions", "partitions", default=[], required=True),
            _f("default_partition", "default_partition", default="", required=True),
            _f("allowed_modes", "multiselect", options=modes, default=[]),
            _f("can_disarm", "boolean", default=True),
            _f("can_bypass", "boolean", default=True),
            _f("can_silence", "boolean", default=True),
            _f("sensor_list", "select", options=list(SENSOR_LIST_CHOICES), default="code"),
            _f("unlock_seconds", "number", unit="s", min=UNLOCK_SECONDS_RANGE[0], max=UNLOCK_SECONDS_RANGE[1], default=DEFAULT_UNLOCK_SECONDS),
            _f("sound", "boolean", default=DEFAULT_SOUND, show_if={"device": ["esphome"]}),
            _f("sound_changes", "boolean", default=DEFAULT_SOUND_CHANGES, show_if={"device": ["esphome"], "sound": [True]}),
            _f("sound_delays", "boolean", default=DEFAULT_SOUND_DELAYS, show_if={"device": ["esphome"], "sound": [True]}),
            _f("sound_volume", "number", unit="%", min=SOUND_VOLUME_RANGE[0], max=SOUND_VOLUME_RANGE[1], default=DEFAULT_SOUND_VOLUME, show_if={"device": ["esphome"], "sound": [True]}),
            _f("code", "password"),
            _f("watch", "boolean", default=True),
            _f("blocked", "boolean", default=False),
        ],
        "partition": [
            _f("name", "text", required=True),
            _f("modes", "multiselect", options=list(MODES), default=house_modes, required=True),
            *[_f(f"exit_delay_{m}", "number", unit="s", min=0, max=3600, default=delay(m), show_if={"modes": [m]}) for m in MODES],
            _f("default_entry_delay", "number", unit="s", min=0, max=3600, default=house.get("default_entry_delay", 30)),
            _f("trigger_time", "number", unit="s", min=0, max=86400, default=house.get("trigger_time")),
            _f("chime_entity", "entity", domains=list(CHIME_DOMAINS)),
        ],
        "siren": [
            _f("name", "text", required=True),
            _f("preset", "preset"),  # not stored: fills the fields below for a known device
            _f("control", "entity", domains=["siren", "switch", "light"], required=True),
            _f("causes", "multiselect", options=list(SIREN_CAUSES), default=list(SIREN_CAUSES), required=True),
            _f("max_duration", "number", default=180, unit="s", min=0, max=3600),
            _f("repeat_every", "number", default=0, unit="s", min=0, max=3600),
            _f("light", "entity", domains=["switch", "light"]),
            _f("partitions", "partitions", default=[], required=True),
            _f("tone_entity", "entity", domains=["select", "input_select"]),
            _f("volume_entity", "entity", domains=["number", "input_number", "select", "input_select"]),
            _f("battery_entity", "entity", domains=["sensor"]),
            _f(CONF_TAMPER_ENTITY, "entity", domains=["binary_sensor"]),
            _f("power_entity", "entity", domains=["sensor", "select"]),
            _f("power_battery_value", "text"),
            *[_f(f"{cause}.tone", "text", group=cause) for cause in PROFILE_CAUSES],
            *[_f(f"{cause}.volume", "text", group=cause) for cause in PROFILE_CAUSES],
        ],
    }


def settings_schema() -> list[dict[str, Any]]:
    """The settings form. A `section` puts the field on its own card in the panel."""
    st = SELFTEST_RANGES
    return [
        _f("abort_seconds", "number", unit="s", min=ABORT_SECONDS_RANGE[0], max=ABORT_SECONDS_RANGE[1], default=DEFAULT_ABORT_SECONDS, section="alarm"),
        _f("chime_seconds", "number", unit="s", min=CHIME_SECONDS_RANGE[0], max=CHIME_SECONDS_RANGE[1], default=DEFAULT_CHIME_SECONDS, section="chime"),
        _f("startup_wait_seconds", "number", unit="s", min=STARTUP_WAIT_RANGE[0], max=STARTUP_WAIT_RANGE[1], section="startup"),
        _f("code_arm_required", "boolean", section="codes"),
        _f("min_code_length", "number", min=MIN_CODE_LENGTH_FLOOR, max=MIN_CODE_LENGTH_CEILING, section="codes"),
        _f("lock_tries_1", "number", min=LOCK_TRIES_RANGE[0], max=LOCK_TRIES_RANGE[1], section="lock"),
        _f("lock_wait_1", "number", unit="min", min=LOCK_WAIT_RANGE[0], max=LOCK_WAIT_RANGE[1], section="lock"),
        _f("lock_tries_2", "number", min=LOCK_TRIES_RANGE[0], max=LOCK_TRIES_RANGE[1], section="lock"),
        _f("lock_wait_2", "number", unit="min", min=LOCK_WAIT_RANGE[0], max=LOCK_WAIT_RANGE[1], section="lock"),
        _f("lock_tries_3", "number", min=LOCK_TRIES_RANGE[0], max=LOCK_TRIES_RANGE[1], section="lock"),
        _f("lock_wait_3", "number", unit="min", min=LOCK_WAIT_RANGE[0], max=LOCK_WAIT_RANGE[1], section="lock"),
        _f("lock_tries_4", "number", min=LOCK_TRIES_RANGE[0], max=LOCK_TRIES_RANGE[1], section="lock"),
        _f("screen_off_seconds", "number", unit="s", min=SCREEN_OFF_RANGE[0], max=SCREEN_OFF_RANGE[1], section="screen"),
        _f("screen_off_on_alarm", "boolean", default=DEFAULT_SCREEN_OFF_ON_ALARM, section="screen"),
        _f("partition_return_seconds", "number", unit="s", min=PARTITION_RETURN_RANGE[0], max=PARTITION_RETURN_RANGE[1], default=DEFAULT_PARTITION_RETURN_SECONDS, section="screen"),
        _f("battery_threshold", "number", unit="%", min=1, max=100, section="battery"),
        _f("log_retention_days", "number", unit="d", min=LOG_RETENTION_FLOOR, max=LOG_RETENTION_CEILING, section="log"),
        _f("backup_versions", "number", min=BACKUP_VERSIONS_RANGE[0], max=BACKUP_VERSIONS_RANGE[1], section="backup"),
        _f("selftest_interval_days", "number", unit="d", min=st["selftest_interval_days"][0], max=st["selftest_interval_days"][1], section="selftest"),
        _f("selftest_siren_seconds", "number", unit="s", min=st["selftest_siren_seconds"][0], max=st["selftest_siren_seconds"][1], section="selftest"),
        _f("selftest_auto", "boolean", default=False, section="selftest"),
        _f("selftest_handlers", "boolean", default=False, section="selftest"),
        _f("selftest_window_start", "number", unit="h", min=st["selftest_window_start"][0], max=st["selftest_window_start"][1], section="selftest"),
        _f("selftest_window_end", "number", unit="h", min=st["selftest_window_end"][0], max=st["selftest_window_end"][1], section="selftest"),
        _f("heartbeat_url", "text", section="heartbeat"),
        _f("heartbeat_interval_minutes", "number", unit="min", min=HEARTBEAT_INTERVAL_RANGE[0], max=HEARTBEAT_INTERVAL_RANGE[1], section="heartbeat"),
    ]


