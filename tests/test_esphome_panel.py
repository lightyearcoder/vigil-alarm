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

import pytest

ROOT = Path(__file__).resolve().parent.parent
ESPHOME_DIR = ROOT / "esphome"

SECRETS = (
    "wifi_ssid: test\n"
    "wifi_password: testtesttest\n"
    'vigil_panel_garage_ota_password: "test-password"\n'
    'vigil_panel_garage_encryption_key: "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="\n'
)


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is not installed")
def test_the_panel_logic(tmp_path):
    binary = tmp_path / "panel_logic"
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", f"-I{ESPHOME_DIR}",
         str(ROOT / "tests" / "esphome" / "panel_logic.cpp"), "-o", str(binary)],
        check=True,
    )
    result = subprocess.run([str(binary)], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "ok"


def test_every_language_has_every_text():
    """A text with an empty column would show up blank on the panel."""
    header = (ESPHOME_DIR / "vigil_panel.h").read_text()
    start = header.index("static const Text TEXTS[]")
    table = header[start : header.index("};", start)]
    for line in table.splitlines():
        if line.strip().startswith("{\"") and "{\"" in line.split(", {", 1)[-1]:
            texts = line.split(", {", 1)[1].rsplit("}", 2)[0]
            assert texts.count('"') == 4, f"two texts expected: {line}"
            assert '""' not in texts, f"empty text: {line}"
    assert all(ord(c) < 128 for c in table), "the built-in fonts only have plain ASCII letters"


def test_every_service_the_panel_calls_exists():
    yaml = (ESPHOME_DIR / "vigil-panel.yaml").read_text()
    services = (ROOT / "custom_components" / "vigil_alarm" / "services.yaml").read_text()
    for name in ("arm", "disarm", "bypass", "unbypass", "check_code"):
        assert f"action: vigil_alarm.{name}" in yaml
        assert f"\n{name}:" in "\n" + services


def test_the_attributes_the_panel_reads_exist():
    yaml = (ESPHOME_DIR / "vigil-panel.yaml").read_text()
    attrs = [
        line.split(":", 1)[1].strip()
        for line in yaml.splitlines()
        if line.strip().startswith("attribute:")
    ]
    assert attrs
    source = (ROOT / "custom_components" / "vigil_alarm" / "alarm_control_panel.py").read_text()
    native = {"supported_features", "code_arm_required", "changed_by"}  # from Home Assistant itself
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
    for path in ESPHOME_DIR.glob("*.yaml"):
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
    text = (ESPHOME_DIR / "vigil-panel.yaml").read_text()
    field = text[text.index("id: pin_text\n            width"):]
    field = field[: field.index("- label:")]
    assert "password_mode: true" in field and "text_color: 0xFFFFFF" in field
    assert "lv_textarea_set_password_show_time(id(pin_text), 0)" in text  # no digit flashes up
    assert 'lv_textarea_set_password_bullet(id(pin_text), "*")' in text


def test_the_sensor_list_is_locked_by_default_and_forgets_the_code():
    yaml = (ESPHOME_DIR / "vigil-panel.yaml").read_text()
    assert "sensor_list: code" in yaml  # the safe default
    assert 'parse_sensor_list("${sensor_list}")' in yaml
    assert "lock_sensors" in yaml and "unlock_timer" in yaml
    idle = yaml[yaml.index("on_idle:"):yaml.index("pages:")]
    assert "sensors_unlocked = false" in idle and 'unlock_code) = ""' in idle  # also when the screen idles
    assert "script.execute: lock_sensors" in yaml[yaml.index("id: btn_sens_back"):]  # and when leaving the list
