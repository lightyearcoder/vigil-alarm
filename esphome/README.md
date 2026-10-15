# Vigil touch panel (ESPHome)

A touch panel for Vigil Alarm: arm, disarm, see what is open and bypass a sensor, without a phone.
It runs on an ESP32 with an LVGL display and follows Vigil completely: it shows only the modes you
switched on, asks for a code only when Vigil does, and shows the same state and sensors as Home
Assistant. It does not decide anything itself, it is a control point.

Made for ESPHome 2026.9. The hardware file is for the **Guition ESP32-S3-4848S040** (480x480).
Other displays work with another hardware file, see below.

## What it does

- **Main page**: the state in a large coloured card (green disarmed, teal Home, blue Away, violet
  Night, amber arming, orange waiting for a code, red alarm), the open sensors, and the buttons.
  The buttons are *Home*, *Away* and *Night*, but only the modes that are switched on in Vigil. When
  the alarm is on, there is one button: *Disarm*.
- **Keypad**: opens by itself during the entry delay and during an alarm. Wrong code, a refused
  arming and other errors are shown with the text Home Assistant gives.
- **Sensors**: all sensors with their state and a *Bypass* or *Restore* button. Fire and gas
  sensors have no button, they can never be bypassed.
- **Settings**: language (Dutch or English, remembered), connection and Wi-Fi info.
- The screen goes dark after 30 seconds and lights up on touch and when the alarm changes. After 30
  seconds without touch the panel forgets a half typed code and returns to the main page.

### Codes

- **Disarming** always asks for a code.
- **Arming and bypassing** ask for a code only if *a code is required to arm* is on in Vigil
  (Settings tab). If it is off, one tap is enough, also for bypassing.
- The keypad has digits only: give users a numeric code.

### What a passer-by can see

Someone standing at the panel should not learn what your house watches. With the default
`sensor_list: code` the Sensors button asks for a code first, and the list stays open for
`sensor_unlock` (the code is also used for bypassing, so you do not have to enter it twice). It is
forgotten when you leave the list, when the screen goes idle and when the time is up. While the alarm
is on, the main page shows no sensor names and no names of people, also not which sensor tripped.
With the alarm off it does show the open sensors, because those are what keep you from arming.
The code is checked with the action `vigil_alarm.check_code`; a wrong code counts towards the
lockout like any other.

### Who did it

Every panel has a `source`, for example `panel garage`. It is shown in the history of Vigil as
*Anna (panel garage)*, or just *panel garage* when no code was needed. A wrong code is published
as the event `code_rejected` with that source, never with the code itself.

## Installing

1. Copy the files of this folder into your ESPHome folder: `vigil-panel.yaml`,
   `vigil-panel-row.yaml`, `vigil-panel-row-script.yaml`, `vigil_panel.h`, `guition-4848.yaml` and
   `example-garage.yaml` (rename that last one).
2. In the new file change `name`, `friendly_name` and `source`. Add the encryption key and an
   OTA password to your `secrets.yaml`. Keep both: the key protects the link with Home Assistant (the
   codes pass through it), the password stops others on your network from flashing the panel.
3. Install it on the panel (the first time through USB).
4. In Home Assistant: **Settings → Devices & services → ESPHome → the device → Configure** and
   switch on **Allow the device to perform Home Assistant actions**. Without it the buttons do
   nothing.

For a second panel copy the example file again, with another `name` and another `source`.

## Options

Set these as `substitutions:` in your file, above the packages:

| Substitution | Default | Meaning |
|---|---|---|
| `alarm_entity` | `alarm_control_panel.vigil_alarm` | The Vigil alarm, if you renamed it. |
| `source` | `panel` | How this panel is called in the history. |
| `language` | `"0"` | First language: `"0"` Nederlands, `"1"` English. After that the panel remembers its setting. |
| `allow_bypass` | `"true"` | `"false"` hides the bypass buttons. |
| `sensor_list` | `code` | Who sees the list of sensors: `code` only after a code, `always` everyone, `never` nobody (the button is gone). |
| `sensor_unlock` | `60s` | How long the list stays open after a code (with `code`). |
| `backlight_timeout` | `30s` | How long the screen stays on. |
| `idle_timeout` | `30s` | Time without touch before the panel returns to the main page. |

## Another display

`vigil-panel.yaml` is for the screen only. For other hardware make a file like `guition-4848.yaml`
with the display, the touch screen and `lvgl:` with the `touchscreens:`. It must provide:

- a light with the id `display_backlight`,
- a touch screen that runs `script.execute: wake` on touch.

The layout is made for 480x480. Another size needs other widths in `vigil-panel.yaml`.

## Another language

All texts are in `vigil_panel.h`, one line per text with a column per language. Add a column and an
entry in `LANGUAGES`, and a button on the settings page. Use plain ASCII: the built-in fonts have no
accented letters.

## What the panel reads from Vigil

Everything comes from the attributes of the alarm entity: `mode`, `delay_end`, `changed_by`,
`cause`, `cause_sensor`, `open_now_text`, `open_sensors_text`, `faults_text`, `problems_count`,
`panel_sensors` and Home Assistant's own `supported_features` and `code_arm_required`. They are plain
text on purpose, because ESPHome cannot read lists. The panel calls `vigil_alarm.arm`, `vigil_alarm.disarm`,
`vigil_alarm.bypass` and `vigil_alarm.unbypass` with its `source`.

## Not on the panel

Silencing a siren, a tag reader and a speaker. Disarming silences everything anyway.

## Tests

`tests/test_esphome_panel.py` runs the logic of `vigil_panel.h` with a C++ compiler and validates the
example with `esphome config`. A build and the screen itself can only be tried on the panel.
