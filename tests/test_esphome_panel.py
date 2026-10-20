"""The ESPHome touch panel: its logic in C++ and its YAML.

The logic (vigil_panel.h) is plain C++ and runs here with g++. The YAML is checked with
`esphome config` when ESPHome is installed. A real build and the screen itself can only be tried
on the panel.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import re

import pytest

ROOT = Path(__file__).resolve().parent.parent
ESPHOME_DIR = ROOT / "esphome"
FIRMWARE_DIR = ESPHOME_DIR / "vigil_alarm"  # the firmware; the folder above has the devices

SECRETS = (
    "wifi_ssid: test\n"
    "wifi_password: testtesttest\n"
    'vigil_panel_garage_encryption_key: "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="\n'
)


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is not installed")
def test_the_panel_logic(tmp_path):
    binary = tmp_path / "panel_logic"
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", f"-I{FIRMWARE_DIR}",
         str(ROOT / "tests" / "esphome" / "panel_logic.cpp"), "-o", str(binary)],
        check=True,
    )
    result = subprocess.run([str(binary)], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "ok"


def test_every_language_has_every_text():
    """A text with an empty column would show up blank on the panel."""
    header = (FIRMWARE_DIR / "vigil_panel.h").read_text()
    start = header.index("static const Text TEXTS[]")
    table = header[start : header.index("};", start)]
    for line in table.splitlines():
        if line.strip().startswith("{\"") and "{\"" in line.split(", {", 1)[-1]:
            texts = line.split(", {", 1)[1].rsplit("}", 2)[0]
            assert texts.count('"') == 12, f"six texts expected (nl, en, de, fr, it, es): {line}"
            assert '""' not in texts, f"empty text: {line}"
    assert all(ord(c) < 128 for c in table), "the built-in fonts only have plain ASCII letters"


def test_every_service_the_panel_calls_exists():
    yaml = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    services = (ROOT / "custom_components" / "vigil_alarm" / "services.yaml").read_text()
    for name in ("arm", "disarm", "bypass", "unbypass", "unlock_panel", "select_partition"):
        assert f"action: vigil_alarm.{name}" in yaml
        assert f"\n{name}:" in "\n" + services


def test_the_attributes_the_panel_reads_exist():
    yaml = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    attrs = [
        line.split(":", 1)[1].strip()
        for line in yaml.splitlines()
        if line.strip().startswith("attribute:")
    ]
    assert attrs
    package = ROOT / "custom_components" / "vigil_alarm"
    source = (package / "alarm_control_panel.py").read_text() + (package / "panels.py").read_text()
    native = {"changed_by"}  # from Home Assistant itself
    for attr in attrs:
        assert attr in native or f'"{attr}"' in source, f"the panel reads {attr}, Vigil does not set it"


def _esphome_installed() -> bool:
    # -I and another folder: the esphome folder of this repository must not look like the package.
    probe = subprocess.run(
        [sys.executable, "-I", "-c", "import esphome.core"], capture_output=True, cwd=tempfile.gettempdir()
    )
    return probe.returncode == 0


@pytest.mark.skipif(not _esphome_installed(), reason="ESPHome is not installed")
def test_the_example_panel_is_valid_esphome(tmp_path):
    work = tmp_path / "config"
    shutil.copytree(ESPHOME_DIR, work)
    (work / "secrets.yaml").write_text(SECRETS)
    result = subprocess.run(
        [sys.executable, "-I", "-m", "esphome", "config", str(work / "example-garage.yaml")],
        capture_output=True, text=True, cwd=work,
    )
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-3000:]


def test_label_lambdas_return_a_std_string_not_a_plain_literal():
    """ESPHome calls `.c_str()` on what a label `text:` lambda returns; `const char *` does not compile."""
    import re

    bad = []
    for path in ESPHOME_DIR.rglob("*.yaml"):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            m = re.search(r"text: !lambda '(return .*)'\s*$", line)
            if not m:
                continue
            body = m.group(1)
            literal = re.search(r'return\s+"', body) or re.search(r'\?\s*"[^"]*"\s*:\s*"', body)
            if literal and "std::string" not in body:
                bad.append(f"{path.name}:{number}: {line.strip()}")
    assert bad == []


def test_the_pin_field_is_readable_and_shows_stars_only():
    text = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    field = text[text.index("id: pin_text\n            width"):]
    field = field[: field.index("- label:")]
    assert "password_mode: true" in field and "text_color: 0xFFFFFF" in field
    assert "lv_textarea_set_password_show_time(id(pin_text), 0)" in text  # no digit flashes up
    assert 'lv_textarea_set_password_bullet(id(pin_text), "*")' in text


def test_the_panel_gets_its_settings_from_the_profile_not_from_the_yaml():
    yaml = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    top = yaml[: yaml.index("esphome:")]
    for gone in ("language:", "allow_bypass:", "sensor_list:", "sensor_unlock:", "  source:"):
        assert gone not in top, f"{gone} is set in Vigil now, not in the firmware"
    assert "unlock_code" not in yaml and "check_code" not in yaml
    assert "source: ${name}" in yaml  # the device name is the panel id and the source


def test_the_default_profile_entity_is_the_one_vigil_makes():
    pytest.importorskip("homeassistant")  # this job has no Home Assistant; the full run has
    from custom_components.vigil_alarm.panels import profile_object_id

    assert profile_object_id("vigil-panel-garage") == "vigil_panel_garage_profile"
    assert "sensor.${ name | replace(\"-\", \"_\") }_profile" in (FIRMWARE_DIR / "vigil-panel.yaml").read_text()


def test_the_panel_reports_what_vigil_reads():
    """Vigil finds these by the name of the entity: Hardware ID, Capabilities, Firmware version, Profile version."""
    pytest.importorskip("homeassistant")  # this job has no Home Assistant; the full run has
    from custom_components.vigil_alarm.panels import REPORTED

    yaml = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    assert set(REPORTED) == {"Hardware ID", "Capabilities", "Firmware version", "Profile version"}
    for name in REPORTED:
        assert f"name: {name}\n" in yaml


def test_the_hardware_file_names_the_hardware_and_the_screen():
    hardware = (FIRMWARE_DIR / "guition-4848.yaml").read_text()
    for needed in ("hardware_id:", "screen_width:", "screen_height:", "id: display_backlight"):
        assert needed in hardware
    assert "width: ${screen_width}" in hardware and "height: ${screen_height}" in hardware


def test_the_list_and_the_info_open_with_the_admin_code_and_are_forgotten():
    yaml = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    assert "action: vigil_alarm.unlock_panel" in yaml
    assert "lock_sensors" in yaml and "unlock_timer" in yaml
    idle = yaml[yaml.index("  - id: reset_ui"):yaml.index("  - id: set_connected")]
    assert "sensors_unlocked = false" in idle and "on_info_page) = false" in idle  # also when the screen goes dark
    assert "script.execute: reset_ui" in yaml[yaml.index("  - id: wake\n"):yaml.index("  - id: reset_ui")]  # and not before
    wake = yaml[yaml.index("  - id: wake\n"):yaml.index("  - id: reset_ui")]
    # the backlight fades out (1 s): reset only after the delay, or the screen jumps while it is still visible
    assert wake.index("light.turn_off") < wake.index("delay: 1500ms") < wake.rindex("script.execute: reset_ui")
    # leaving the list or the info is the Alarm tab: it forgets the unlock
    assert "script.execute: lock_sensors" in yaml[yaml.index("id: nav_alarm\n"):yaml.index("id: nav_sens\n")]
    assert "script.execute: open_sensors" in yaml[yaml.index("id: nav_sens\n"):yaml.index("id: nav_info\n")]
    assert "script.execute: open_info" in yaml[yaml.index("id: nav_info\n"):yaml.index("id: alarm_frame")]
    assert "ha_profile_unlocked" in yaml  # and when Vigil locks the panel again


def test_the_screen_time_and_the_steady_state_rule_come_from_vigil():
    yaml = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    wake = yaml[yaml.index("  - id: wake\n"):yaml.index("  - id: reset_ui")]
    assert "attribute: screen_off_seconds" in yaml and "attribute: screen_off_on_alarm" in yaml
    assert wake.count("delay: !lambda 'return id(screen_off_ms);'") == 2  # once, and once more after an open page
    # an open keypad, list or info goes back to the main page first (visible), the screen goes dark later
    first, second = wake.index("keypad_open) || id(on_sensors_page)"), wake.index("screen_may_sleep")
    assert first < second < wake.index("light.turn_off")
    assert "script.stop: wake" in wake  # counting down, or an alarm that must stay visible: no dark screen


def test_the_error_phrases_of_the_panel_and_the_card_match_vigils_own_texts():
    """The panel and the card translate what Vigil answers by looking for phrases; they must stay in the texts."""
    import json
    import re

    header = (FIRMWARE_DIR / "vigil_panel.h").read_text(encoding="utf-8")
    card = (ROOT / "custom_components/vigil_alarm/frontend/vigil-card.js").read_text(encoding="utf-8")
    rows = re.findall(r'\{\{([^}]*)\}, "(err_[a-z_]+)"\}', header)
    card_rows = re.findall(r'\[\[([^\]]*)\], "(err_[a-z_]+)"\]', card)
    assert len(rows) == len(card_rows) == 10

    def phrases(row):
        return re.findall(r'"((?:[^"\\]|\\.)*)"', row[0])

    texts = {}
    for lang in ("en", "nl", "de", "fr", "it", "es"):
        data = json.loads((ROOT / f"custom_components/vigil_alarm/translations/{lang}.json").read_text(encoding="utf-8"))
        texts[lang] = " ".join(v["message"] for v in data["exceptions"].values())
    for fw, cd in zip(rows, card_rows):
        nl, en, *others = phrases(fw)  # the firmware follows enum Language: nl, en, de, fr, it, es
        assert [en, nl, *others] == phrases(cd), (en, "the same table in both")  # the card: en, nl, de, fr, it, es
        assert fw[-1] == cd[-1]
        for lang, phrase in zip(("en", "nl", "de", "fr", "it", "es"), [en, nl, *others]):
            assert phrase in texts[lang], (lang, phrase)


def test_every_icon_the_panel_draws_is_in_the_icon_font():
    """The icons are glyphs of one font that holds only the codes listed in the YAML; a code that is missing there
    shows as an empty square on the panel."""
    import re

    yaml = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    header = (FIRMWARE_DIR / "vigil_panel.h").read_text()
    font = yaml[yaml.index("glyphs: &icon_glyphs"):yaml.index("time:\n  - platform: homeassistant")]
    listed = set(re.findall(r'"\\U(000F[0-9A-F]{4})"', font))
    used = set(re.findall(r'"\\U(000F[0-9A-F]{4})"', header))
    used |= set(re.findall(r'text: "\\U(000F[0-9A-F]{4})"', yaml[yaml.index("lvgl:\n"):]))
    assert used, "no icons found"
    assert used <= listed, f"not in the icon font: {sorted(used - listed)}"
    assert yaml.count("glyphs: *icon_glyphs") == 2  # three sizes, one list


def test_the_look_and_the_layout_follow_the_size_of_the_screen():
    yaml = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    # the sizes come from the substitutions, which come from screen_width and screen_height of the hardware file
    for name in ("ring_d", "key_w", "key_h", "keypad_h", "content_w", "nav_h"):
        assert f"  {name}:" in yaml.split("esphome:")[0]
    assert "screen_width" in yaml.split("esphome:")[0] and "480" not in yaml.split("lvgl:")[1].replace("0x", "")
    # the main page is a column that grows with the screen; the tabs are on top of every page
    assert "flex_grow: 1" in yaml and "id: nav\n" in yaml
    assert "hide(id(nav), id(keypad_open))" in yaml  # no tabs on the keypad


def test_the_colours_of_the_panel_are_the_colours_of_the_card():
    """One look for card and panel: the state colours must be the same in both."""
    import re

    header = (FIRMWARE_DIR / "vigil_panel.h").read_text()
    card = (ROOT / "custom_components" / "vigil_alarm" / "frontend" / "vigil-card.js").read_text().lower()
    for name in ("COL_OK", "COL_WARN", "COL_ENTRY", "COL_ALARM", "COL_HOME", "COL_AWAY", "COL_NIGHT"):
        value = re.search(rf"{name} = 0x([0-9A-F]{{6}});", header).group(1).lower()
        assert f"#{value}" in card, f"{name} (#{value}) is not a colour of the card"


def test_the_panel_and_the_card_can_bypass_and_arm_after_a_refusal():
    """Arming refused because something stops it: both show what, and one button bypasses and arms (`bypass_open`)."""
    yaml = (ROOT / "esphome/vigil_alarm/vigil-panel.yaml").read_text()
    card = (ROOT / "custom_components/vigil_alarm/frontend/vigil-card.js").read_text()
    services = (ROOT / "custom_components/vigil_alarm/services.yaml").read_text()
    assert "bypass_open:" in yaml and "id: btn_force" in yaml and "parse_refusal(message)" in yaml
    assert "bypass_open: true" in card and 'data-act="force"' in card
    assert "bypass_open:" in services


def test_every_call_the_panel_makes_to_vigil_carries_its_key():
    """The panel sends `key: ${panel_key}` next to `source` in every Home Assistant action, and the key is empty
    (nothing sent) until the device file sets it; the example shows how, commented out so it still builds."""
    yaml = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    assert yaml.count("source: ${name}") == yaml.count("key: ${panel_key}") >= 6
    assert 'panel_key: ""' in yaml
    example = (ROOT / "esphome" / "example-garage.yaml").read_text()
    assert "# panel_key: !secret vigil_panel_garage_key" in example


def test_the_info_page_says_whether_a_panel_key_is_set_and_never_shows_it():
    yaml = (FIRMWARE_DIR / "vigil-panel.yaml").read_text()
    header = (FIRMWARE_DIR / "vigil_panel.h").read_text()
    assert yaml.count("id: lbl_info_key") == 2  # the label is updated and is made on the page
    assert 'std::string("${panel_key}").empty()' in yaml  # only whether it is empty is looked at
    assert 'tr("panel_key") + (' in yaml and '+ "${panel_key}"' not in yaml
    for key in ("panel_key", "key_set", "key_not_set"):
        row = re.search(r'\{"%s", \{(.*)\}\},' % key, header)
        assert row and len(re.findall(r'"[^"]*"', row.group(1))) == 6  # one text per language
