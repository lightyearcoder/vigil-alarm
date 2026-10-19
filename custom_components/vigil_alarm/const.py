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
SUBENTRY_PANEL = "panel"

# Modes available in release 1; the rest of the code derives everything from
# the enabled modes, so a mode can be added here later.
MODES = ("home", "away", "night", "vacation", "custom")
DEFAULT_MODES = ("home", "away", "night")  # what a new installation turns on, and what a stored entry without modes means
DEFAULT_EXIT_DELAY = {"home": 0, "away": 60, "night": 10, "vacation": 60, "custom": 30}
# Bits of `modes_mask` in the profile of a panel (read by the ESPHome firmware).
MODE_BITS = {"home": 1, "away": 2, "night": 4, "vacation": 8, "custom": 16}

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
NOTIFICATION_CATEGORIES = ("alarm", "pending", "arming", "fault", "technical", "duress")
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
CONF_BACKUP_VERSIONS = "backup_versions"  # how many versions of the configuration are kept (see backups.py)
DEFAULT_BACKUP_VERSIONS = 10
BACKUP_VERSIONS_RANGE = (1, 50)
CONF_MIN_CODE_LENGTH = "min_code_length"
MIN_CODE_LENGTH_FLOOR = 4  # the lowest value the setting accepts
MIN_CODE_LENGTH_CEILING = 12
CONF_SCREEN_OFF_SECONDS = "screen_off_seconds"  # how long a panel screen stays on without touch
DEFAULT_SCREEN_OFF_SECONDS = 30
SCREEN_OFF_RANGE = (5, 3600)
CONF_SCREEN_OFF_ON_ALARM = "screen_off_on_alarm"  # may the screen go dark while the alarm is going off
DEFAULT_SCREEN_OFF_ON_ALARM = False

CONF_CODE = "code"
CONF_CODE_HASH = "code_hash"
CONF_CODE_SALT = "code_salt"
CONF_TAGS = "tags"
CONF_ALLOWED_MODES = "allowed_modes"
CONF_MAY_BYPASS = "may_bypass"  # a user may bypass sensors; users saved before this existed keep the right
CONF_MAY_BYPASS_TAMPER = "may_bypass_tamper"
CONF_DURESS_HASH = "duress_hash"  # a second code per user: disarms like the normal one, and tells the channels quietly
CONF_DURESS_SALT = "duress_salt"
CONF_PERMANENT_BYPASS = "permanent_bypass"  # on a sensor: a manual bypass stays after disarming
CONF_CHIME = "chime"  # on a sensor: sound the chime when it opens while the alarm is off

# The window after the siren starts in which a valid code means "false alarm" (0 = off), and the chime.
CONF_ABORT_SECONDS = "abort_seconds"
DEFAULT_ABORT_SECONDS = 60
ABORT_SECONDS_RANGE = (0, 600)
CONF_CHIME_ENTITY = "chime_entity"  # what sounds for the chime: a siren, switch, light, button or script
CONF_CHIME_SECONDS = "chime_seconds"
DEFAULT_CHIME_SECONDS = 2
CHIME_SECONDS_RANGE = (1, 30)
CHIME_DOMAINS = ("siren", "switch", "light", "button", "input_button", "script")
ALARM_PATH_MAX = 200  # sensors kept in the path of one alarm

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
    "startup_settled",
    "code_locked_permanent",
    "selftest_checked",
    "selftest_reminder",
    "selftest_siren_tested",
    "practice_started",
    "practice_ended",
    "alarm_cancelled",
    "duress_used",
    "alarm_sensor_seen",
    "alarm_memory_cleared",
    "chime",
    "walktest_started",
    "walktest_finished",
    "panel_refused",
    "user_refused",
    "panel_unlocked",
    "panel_lock_cleared",
    "panel_offline",
    "panel_online",
]

# Control points (panels, tablets): the register and the profile each one gets.
CONF_PANEL_ID = "panel_id"
CONF_LANGUAGE = "language"
CONF_CAN_DISARM = "can_disarm"
CONF_CAN_BYPASS = "can_bypass"
CONF_CAN_SILENCE = "can_silence"
CONF_SENSOR_LIST = "sensor_list"
CONF_UNLOCK_SECONDS = "unlock_seconds"
CONF_BLOCKED = "blocked"
CONF_WATCH = "watch"  # tell the administrators when this panel drops out; a register entry without it is watched
CONF_HA_USER = "ha_user"  # a tablet: the Home Assistant user it is logged in as
SENSOR_LIST_CHOICES = ("always", "code", "never")
DEFAULT_UNLOCK_SECONDS = 60
UNLOCK_SECONDS_RANGE = (10, 600)
PROFILE_VERSION = 1
PANEL_OFFLINE_SECONDS = 600  # without a connection for this long: a Repair and a message

# The lockout after wrong codes goes in steps. Settings (all in Settings, card "Locking"): after `lock_tries_1`
# wrong codes the first lock lasts `lock_wait_1` minutes; after that `lock_tries_2` wrong codes give the second
# lock, then `lock_tries_3` the third; then `lock_tries_4` more wrong codes lock for good (until an administrator
# unlocks the panel). A right code starts all over.
LOCK_DEFAULTS = {
    "lock_tries_1": 3, "lock_wait_1": 5,
    "lock_tries_2": 2, "lock_wait_2": 15,
    "lock_tries_3": 2, "lock_wait_3": 60,
    "lock_tries_4": 1,
}
LOCK_TRIES_RANGE = (1, 10)
LOCK_WAIT_RANGE = (1, 1440)  # minutes

STARTUP_GRACE = 10  # seconds after HA start before sensor states are trusted
# After a restart a sensor that is still "unavailable" (an MQTT or Zigbee integration that is not up yet) is not
# reported as lost straight away: Vigil waits until every sensor is there, or this long (a setting), and only then
# reports the ones that are really gone.
CONF_STARTUP_WAIT = "startup_wait_seconds"
DEFAULT_STARTUP_WAIT = 120
STARTUP_WAIT_RANGE = (10, 900)
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
SERVICE_UNLOCK_PANEL = "unlock_panel"
ATTR_SENSOR = "sensor"
