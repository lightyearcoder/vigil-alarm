# Changelog

## 0.2.0

- **Breaking:** the integration is now called `vigil_alarm` (it was `vigil`), and entity ids always end on the English name. Remove the old Vigil integration from Settings > Devices & services, restart Home Assistant, add Vigil Alarm again, and update your own automations and dashboards to the new entity ids.
- An entity can only be used by one sensor, so a door contact or its tamper contact can no longer be added twice by accident.
- A sensor can have a tamper entity: Vigil adds the tamper sensor for it by itself (always watching, its own bypass switch), so a door contact with a tamper contact needs one form instead of two.
- The tables for sensors, groups, rules, users, notifications and sirens use the full width of the page.
- The sensors table has a separate Battery column; a level at or below the battery limit is highlighted.
- The sensor form has a short hint and an (i) button with the full explanation of "If open when exit delay ends" and of the tamper entity.
- The panel's edit, copy, delete and test buttons are icons, so the tables have more room; users can no longer be copied.
- New About tab in the Vigil panel: logo, version and Home Assistant version side by side, links with icons, release notes and a button that copies the details for a bug report.
- Touch panel for ESPHome (Guition 4848): arm, disarm, sensors and bypass, Dutch and English. See `esphome/`.
- New actions `vigil_alarm.arm` and `vigil_alarm.disarm`, and an optional `source` on the control actions: the history shows who did it, for example "Anna (panel garage)".
- The touch panel shows the list of sensors only after a code by default (`sensor_list`: `code`, `always` or `never`), and no sensor or people names on the main page while the alarm is on. New action `vigil_alarm.check_code`.
- The minimum length of a code is a setting (4 to 12, default 4); shorter codes are refused.
- Entity ids always end on the English name (`..._fire_alarm`, `..._bypass`, `..._status`), whatever language Home Assistant runs in; the shown names stay translated.
- The alarm entities for intrusion, fire, gas, tamper and water always exist, also without a sensor of that class.
- New event `code_rejected` for a wrong code, with the source but never the code.
- Five wrong codes within five minutes lock all codes for five minutes (event `code_locked`), so a PIN cannot be guessed through the services.
- Bypassing needs a code only when arming does (a code is required to arm). Silence and acknowledge always need one.
- Extra attributes on the alarm for displays: `mode` and text versions of the open sensors, faults and the sensor list.

## 0.1.0 (first release)

- Alarm entity with Home, Away and Night, exit and entry delays, codes per user.
- Sensors in the classes intrusion (instant, delayed, follower), fire, gas, water and tamper.
- Sensor groups decide in which modes intrusion sensors watch; confirmation rules.
- Notifications through `notify` services with escalation.
- Sirens with tone and volume per cause; preset for the Sonoff SNZB-09P (Zigbee2MQTT).
- Self-monitoring of sensors, batteries and sirens.
- Alarm state and timers survive restarts.
- Admin panel in the sidebar with live status (English and Dutch).
- The parts of the alarm are no longer listed under the integration on Devices & services; everything is edited in the Vigil panel.
- Event entity for automations; six blueprints; example dashboard.
