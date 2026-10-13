# Changelog

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
