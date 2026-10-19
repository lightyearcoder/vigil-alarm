"""The scenes the panel simulator takes a picture of.

Every scene has a name, the C++ that sets what Home Assistant would have told the panel (the `vigil::ctx`
struct, see esphome/vigil_alarm/vigil_panel.h), and a view: which page of the panel is on the screen.

views:  main | keypad | sensors | info
"""

# What every scene starts from: a connected, linked, working panel with all three modes, disarmed.
BASE = r"""
auto &c = vigil::ctx;
c = vigil::Context();
c.lang = %(lang)s;
c.ha_connected = true;
c.state = "disarmed";
c.profile_version = vigil::PROFILE_VERSION;
c.panel_id = "vigil_panel_hallway";
c.device_name = "vigil-panel-hallway";
c.modes_mask = 7;
c.can_disarm = true;
c.can_bypass = true;
c.has_admin_code = true;
c.sensor_list = vigil::LIST_ALWAYS;
c.code_arm_required = true;
c.sensors =
    "Voordeur|binary_sensor.voordeur|closed|1\n"
    "Achterdeur|binary_sensor.achterdeur|closed|1\n"
    "Woonkamer raam|binary_sensor.woonkamer_raam|closed|1\n"
    "Keuken raam|binary_sensor.keuken_raam|closed|1\n"
    "Beweging gang|binary_sensor.beweging_gang|closed|1\n"
    "Beweging woonkamer|binary_sensor.beweging_woonkamer|closed|1\n"
    "Rookmelder zolder|binary_sensor.rook_zolder|closed|0\n";
"""

OPEN_ONE = r"""
c.sensors =
    "Voordeur|binary_sensor.voordeur|closed|1\n"
    "Achterdeur|binary_sensor.achterdeur|closed|1\n"
    "Woonkamer raam|binary_sensor.woonkamer_raam|open|1\n"
    "Keuken raam|binary_sensor.keuken_raam|closed|1\n"
    "Beweging gang|binary_sensor.beweging_gang|closed|1\n"
    "Beweging woonkamer|binary_sensor.beweging_woonkamer|bypassed|1\n"
    "Rookmelder zolder|binary_sensor.rook_zolder|unavailable|0\n";
c.open_total = 1;
"""

# (name, view, extra C++ after BASE, pending action for the keypad, digits typed, error text)
SCENES = [
    ("disarmed", "main", "", 0, "", ""),
    ("not-ready", "main", OPEN_ONE + 'c.faults_total = 1;', 0, "", ""),
    ("arming", "main", 'c.state = "arming"; c.mode = "away"; c.delay_end = c.now + 42;', 0, "", ""),
    ("armed-home", "main", 'c.state = "armed_home"; c.mode = "home"; c.changed_by = "Anna";', 0, "", ""),
    ("armed-away", "main", 'c.state = "armed_away"; c.mode = "away"; c.changed_by = "Anna"; c.changed_via = "vigil-panel-garage";', 0, "", ""),
    ("armed-night", "main", 'c.state = "armed_night"; c.mode = "night"; c.changed_by = "Anna";', 0, "", ""),
    ("pending", "main", 'c.state = "pending"; c.mode = "away"; c.cause_sensor = "Voordeur"; c.delay_end = c.now + 21;', 0, "", ""),
    ("triggered", "main", 'c.state = "triggered"; c.mode = "away"; c.cause = "intrusion"; c.cause_sensor = "Beweging gang";', 0, "", ""),
    ("keypad-arm", "keypad", "", 2, "", ""),
    ("keypad-digits", "keypad", "", 4, "12", ""),
    ("keypad-error", "keypad", "", 4, "1234", "Ongeldige code"),
    ("sensors", "sensors", OPEN_ONE, 0, "", ""),
    ("info", "info", "", 0, "", ""),
    ("offline", "main", 'c.ha_connected = false; c.state = "";', 0, "", ""),
    ("not-linked", "main", 'c.profile_version = 0;', 0, "", ""),
    ("blocked", "main", 'c.blocked = true; c.modes_mask = 0;', 0, "", ""),
    # Arming was refused because a tamper contact is open: the text says so, and one button bypasses and arms.
    ("refused", "main", 'c.message = vigil::parse_refusal("Arming refused: alarm_condition (Sabotage voordeur).").text; '
     'c.refused_action = vigil::ARM_AWAY;', 0, "", ""),
    # Armed on a panel without a code: the panel is known, the person is not.
    ("armed-away-nocode", "main", 'c.state = "armed_away"; c.mode = "away"; c.changed_via = "vigil-panel-garage";', 0, "", ""),
    # Release 0.5.4: five modes in one row (smaller text), and the alarm memory under the state.
    ("disarmed-five-modes", "main", 'c.modes_mask = 31; c.last_alarm = "14:03 Voordeur > Gang > Woonkamer";', 0, "", ""),
    ("armed-vacation", "main", 'c.state = "armed_vacation"; c.mode = "vacation"; c.changed_by = "Anna";', 0, "", ""),
    ("armed-custom", "main", 'c.state = "armed_custom_bypass"; c.mode = "custom"; c.changed_by = "Anna";', 0, "", ""),
    ("triggered-alarm24", "main", 'c.state = "triggered"; c.mode = "away"; c.cause = "alarm24"; c.cause_sensor = "Paniekknop";', 0, "", ""),
    # Release 0.5.5: disarmed, but a sensor is still bypassed for good.
    ("disarmed-permanent-bypass", "main", 'c.last_alarm = "14:03 Voordeur > Gang"; c.bypassed = "Raam zolder";', 0, "", ""),
]
