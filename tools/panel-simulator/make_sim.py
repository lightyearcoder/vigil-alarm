#!/usr/bin/env python3
"""Make the folder the panel simulator is built from.

  make_sim.py <firmware folder> <work folder> [--lang nl|en] [--size 480x480]

The firmware folder is esphome/vigil_alarm of this repository. The work folder gets a copy of it with the two
parts of the hardware swapped out (the real clock and wifi are not there on a PC), plus `sim.yaml`: an ESPHome
"host" device with a memory display (the `snapshot` display) that runs every scene of scenes.py and takes a
picture of each.
"""
import argparse
import pathlib
import re
import shutil

import scenes

p = argparse.ArgumentParser()
p.add_argument("firmware")
p.add_argument("work")
p.add_argument("--lang", default="nl")
p.add_argument("--size", default="480x480")
a = p.parse_args()
w, h = a.size.split("x")
work = pathlib.Path(a.work)
dest = work / "vigil_alarm"
if dest.exists():
    shutil.rmtree(dest)
shutil.copytree(a.firmware, dest, ignore=shutil.ignore_patterns("guition*", "__pycache__"))

# No Wi-Fi and no Home Assistant clock on a PC: a fixed address, a fixed signal, the clock of the PC.
panel = (dest / "vigil-panel.yaml").read_text()
panel = re.sub(
    r"  - platform: wifi_info\n    ip_address:\n      id: wifi_ip\n      internal: true\n      on_value:\n        - script.execute: refresh_texts\n",
    "  - platform: template\n    id: wifi_ip\n    internal: true\n    lambda: 'return std::string(\"192.168.1.50\");'\n",
    panel)
panel = re.sub(
    r"  - platform: wifi_signal\n    id: wifi_rssi\n    internal: true\n    update_interval: 10s\n    on_value:\n      - script.execute: refresh_texts\n",
    "  - platform: template\n    id: wifi_rssi\n    internal: true\n    update_interval: 60s\n    lambda: 'return -52.0;'\n",
    panel)
panel = panel.replace("time:\n  - platform: homeassistant\n    id: ha_time", "time:\n  - platform: host\n    id: ha_time")
# Nobody is connected to the simulator, but the panel must think Home Assistant is there.
panel = re.sub(r"api\.connected:\n\s+state_subscription_only: true", "lambda: 'return true;'", panel)
(dest / "vigil-panel.yaml").write_text(panel)

lang = "vigil::NL" if a.lang == "nl" else "vigil::EN"
steps = []
for i, (name, view, extra, action, digits, err) in enumerate(scenes.SCENES, 1):
    code = (scenes.BASE % {"lang": lang}) + "\nc.now = (double) ::time(nullptr);\n" + extra
    code = code.replace("c.state = \"disarmed\";", "c.state = \"disarmed\";", 1)
    steps.append("      - lambda: |-\n" + "\n".join("          " + l for l in code.splitlines()) + "\n")
    steps.append("      - script.execute: reset_ui\n      - script.execute: refresh_texts\n      - script.execute: refresh_ui\n")
    if view == "keypad":
        steps.append(f"      - lambda: |-\n          id(pending_action) = {action};\n          id(pending_name) = \"Woonkamer raam\";\n"
                     "      - script.execute: open_keypad\n")
        if digits:
            steps.append(f"      - lvgl.textarea.update:\n          id: pin_text\n          text: \"{digits}\"\n")
        if err:
            steps.append(f"      - lvgl.label.update:\n          id: lbl_kp_err\n          text: \"{err}\"\n")
    elif view == "sensors":
        steps.append("      - script.execute: show_sensors\n")
    elif view == "info":
        steps.append("      - script.execute: show_info\n")
    steps.append("      - delay: 600ms\n")
    steps.append(f"      - snapshot.take:\n          filename: \"{i:02d}-{name}.bmp\"\n")
steps.append("      - lambda: |-\n          fflush(stdout);\n          std::exit(0);\n")

(work / "sim.yaml").write_text(f"""substitutions:
  name: vigil-panel-hallway
  friendly_name: Vigil panel sim
  hardware_id: sim
  screen_width: "{w}"
  screen_height: "{h}"

esphome:
  name: ${{name}}

host:

logger:
  level: INFO

api:

light:
  - platform: monochromatic
    name: Backlight
    id: display_backlight
    output: backlight_output
    restore_mode: ALWAYS_ON

output:
  - platform: template
    id: backlight_output
    type: float
    write_action:
      - lambda: ""

display:
  - platform: snapshot
    id: tft_display
    dimensions:
      width: {w}
      height: {h}
    update_interval: never
    auto_clear_enabled: false

lvgl:
  displays:
    - tft_display

packages:
  vigil: !include vigil_alarm/vigil-panel.yaml

script:
  - id: sim_run
    then:
{''.join(steps)}
interval:
  - interval: 3s
    startup_delay: 3s
    then:
      - if:
          condition:
            script.is_running: sim_run
          then:
            - logger.log: "scenes running"
          else:
            - script.execute: sim_run
""")
print("ok", len(scenes.SCENES), "scenes")
