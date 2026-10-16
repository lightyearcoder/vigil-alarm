"""Constants for Vigil Alarm."""

from __future__ import annotations

DOMAIN = "vigil_alarm"

# The stored subentry type keeps its historical name so existing installations keep working.
SUBENTRY_SENSOR = "zone"
# Stored under its historical name, like SUBENTRY_SENSOR.
SUBENTRY_RULE = "group"
SUBENTRY_SENSOR_GROUP = "sensor_group"
SUBENTRY_USER = "user"
SUBENTRY_NOTIFICATION = "notification"
SUBENTRY_SIREN = "siren"

# Modes available in release 1; the rest of the code derives everything from
# the enabled modes, so a mode can be added here later.
MODES = ("home", "away", "night")
DEFAULT_EXIT_DELAY = {"home": 0, "away": 60, "night": 10}

CONF_MODES = "modes"
CONF_EXIT_DELAY = "exit_delay_{mode}"
CONF_DEFAULT_ENTRY_DELAY = "default_entry_delay"
CONF_TRIGGER_TIME = "trigger_time"
CONF_CODE_ARM_REQUIRED = "code_arm_required"

CONF_ENTITY_ID = "entity_id"
CONF_CLS = "cls"
CONF_TYPE = "type"
CONF_SENSOR_MODES = "modes"  # only in installations from before sensor groups; see migration.py
CONF_SENSOR_GROUPS = "sensor_groups"
CONF_GROUP_MODES = "modes"
CONF_SUGGEST_FOR = "suggest_for"
SUGGEST_FOR = ("contacts", "motion")
CONF_ENTRY_DELAY = "entry_delay"
CONF_AT_ARM_OPEN = "at_arm_open"
CONF_ON_UNAVAILABLE = "on_unavailable"
CONF_GAS_TYPE = "gas_type"

CONF_SENSORS = "sensors"
CONF_REQUIRED = "required"
CONF_WINDOW = "window"
CONF_ESCALATE = "escalate"

CONF_SERVICE = "service"
CONF_CATEGORIES = "categories"
CONF_DELAY = "delay"
CONF_PRIORITY = "priority"
NOTIFICATION_CATEGORIES = ("alarm", "pending", "arming", "fault", "technical")
DEFAULT_CATEGORIES = ("alarm", "pending", "fault", "technical")

CONF_CONTROL = "control"
CONF_LIGHT = "light"
CONF_TONE_ENTITY = "tone_entity"
CONF_VOLUME_ENTITY = "volume_entity"
CONF_MAX_DURATION = "max_duration"
CONF_REPEAT_EVERY = "repeat_every"
CONF_CAUSES = "causes"
CONF_TONE = "tone"
CONF_VOLUME = "volume"
SIREN_CAUSES = ("intrusion", "fire", "gas", "tamper", "fault")
# Profile sections in the siren flow; a sensor fault sounds like an intrusion.
PROFILE_CAUSES = ("intrusion", "fire", "gas", "tamper")
FLAMMABLE_GAS = ("natural_gas", "lpg")

CONF_BATTERY_ENTITY = "battery_entity"
CONF_TAMPER_ENTITY = "tamper_entity"  # on a sensor: its own tamper contact, kept as a companion sensor
CONF_COMPANION_OF = "companion_of"  # on the companion: the id of the sensor it belongs to
CONF_POWER_ENTITY = "power_entity"
CONF_POWER_BATTERY_VALUE = "power_battery_value"
CONF_BATTERY_THRESHOLD = "battery_threshold"
DEFAULT_BATTERY_THRESHOLD = 20

CONF_SELFTEST_INTERVAL = "selftest_interval_days"  # 0 = no reminders
CONF_SELFTEST_SECONDS = "selftest_siren_seconds"
CONF_SELFTEST_AUTO = "selftest_auto"
CONF_SELFTEST_FROM = "selftest_window_start"  # hour of the day
CONF_SELFTEST_TO = "selftest_window_end"
DEFAULT_SELFTEST = {
    CONF_SELFTEST_INTERVAL: 30,
    CONF_SELFTEST_SECONDS: 2,
    CONF_SELFTEST_AUTO: False,
    CONF_SELFTEST_FROM: 9,
    CONF_SELFTEST_TO: 20,
}
SELFTEST_RANGES = {  # setting -> (lowest, highest)
    CONF_SELFTEST_INTERVAL: (0, 365),
    CONF_SELFTEST_SECONDS: (1, 5),
    CONF_SELFTEST_FROM: (0, 23),
    CONF_SELFTEST_TO: (1, 24),
}
CONF_HEARTBEAT_URL = "heartbeat_url"  # a secret; empty = off
CONF_HEARTBEAT_INTERVAL = "heartbeat_interval_minutes"
DEFAULT_HEARTBEAT_INTERVAL = 5
HEARTBEAT_INTERVAL_RANGE = (1, 1440)
HEARTBEAT_URL_MAX = 2048
CONF_LOG_RETENTION_DAYS = "log_retention_days"
DEFAULT_LOG_RETENTION_DAYS = 90
LOG_RETENTION_FLOOR = 1
LOG_RETENTION_CEILING = 3650
CONF_MIN_CODE_LENGTH = "min_code_length"
MIN_CODE_LENGTH_FLOOR = 4  # the lowest value the setting accepts
MIN_CODE_LENGTH_CEILING = 12

CONF_CODE = "code"
CONF_CODE_HASH = "code_hash"
CONF_CODE_SALT = "code_salt"
CONF_TAGS = "tags"
CONF_ALLOWED_MODES = "allowed_modes"
CONF_MAY_BYPASS_TAMPER = "may_bypass_tamper"

# Event vocabulary of the event entity (the public extension contract).
EVENT_TYPES = [
    "armed",
    "arming_started",
    "arm_refused",
    "disarmed",
    "pending_started",
    "triggered",
    "trigger_cause_changed",
    "trigger_ended",
    "sensor_faulted",
    "sensor_unconfirmed",
    "sensor_unconfirmed_escalated",
    "sensor_bypassed",
    "sensor_bypassed_at_arm",
    "sensor_unbypassed",
    "bypass_refused",
    "supervision_lost",
    "supervision_restored",
    "technical_alarm_started",
    "technical_alarm_ended",
    "state_restore_failed",
    "notification_failed",
    "siren_started",
    "siren_stopped",
    "siren_failed",
    "siren_unavailable",
    "siren_available",
    "siren_power_lost",
    "siren_power_restored",
    "battery_low",
    "battery_ok",
    "alarm_silenced",
    "alarm_acknowledged",
    "code_rejected",
    "code_locked",
    "selftest_checked",
    "selftest_reminder",
    "selftest_siren_tested",
]

CODE_MAX_FAILURES = 5  # wrong codes within CODE_FAILURE_WINDOW seconds lock all codes
CODE_FAILURE_WINDOW = 300
CODE_LOCK_SECONDS = 300

STARTUP_GRACE = 10  # seconds after HA start before sensor states are trusted
STORAGE_VERSION = 1
SAVE_DELAY = 1.0
PBKDF2_ITERATIONS = 100_000

SERVICE_ARM = "arm"
SERVICE_DISARM = "disarm"
SERVICE_CHECK_CODE = "check_code"
SERVICE_BYPASS = "bypass"
SERVICE_UNBYPASS = "unbypass"
SERVICE_TEST_NOTIFICATION = "test_notification"
SERVICE_TEST_SIREN = "test_siren"
SERVICE_SILENCE = "silence"
SERVICE_ACKNOWLEDGE = "acknowledge"
ATTR_SENSOR = "sensor"
