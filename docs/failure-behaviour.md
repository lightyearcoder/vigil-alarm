# What Vigil does when something goes wrong

Every line below is a scenario that is tested automatically (`tests/ha/test_failure_scenarios.py` and the tests it points to), so this page is what the alarm does, not what it is meant to do. The one thing no test can change: **Vigil runs inside Home Assistant. When Home Assistant is not running, there is no alarm.** The [heartbeat](user-guide.md) tells you that it is down; it cannot take over.

Dutch: [wat Vigil doet bij storingen](failure-behaviour.nl.md).

## When Home Assistant restarts or stops

| Situation | What Vigil does |
|---|---|
| Restart during the **exit delay** | The delay carries on; it ends at the original time, it does not start again. |
| The exit delay **ended while Home Assistant was down** | The alarm is armed on start. |
| Restart while **armed** | Still armed, in the same mode, by the same user (the user is kept over a restart since 0.6.4). The sensors are watched again as soon as they are trusted (see below). |
| A door was **opened while Home Assistant was down** | When Vigil is back and sees the open sensor, the entry delay starts. |
| Restart during the **entry delay** | The entry delay carries on and ends at the original time. Restarting three times in a row changes nothing. Disarming after the restart stops it. |
| Restart during the **alarm** | The alarm is still on; the cause and sensor are kept; the right code disarms it, a wrong code does not. The siren sounds again and notifications that were waiting to escalate still escalate, without repeating the ones already sent. |
| The alarm's **siren time ran out while Home Assistant was down** | The alarm has ended on start and the system is armed again, not disarmed. |
| The saved state is **unusable** | Vigil starts disarmed and logs `state_restore_failed`. |
| Sensors are not there yet right after a start | For a short grace period Vigil does not call that a fault and does not arm; after that, a sensor that is still missing is reported as unreachable. |

## Sensors

| Situation | What Vigil does |
|---|---|
| A sensor becomes **unavailable while armed** | It is reported (`supervision_lost`, and a Repair) and does **not** sound the alarm; when it is back, `supervision_restored`. A sensor that is unavailable *before* arming refuses the arming, unless its *When unreachable* setting says otherwise. |
| A sensor reports the **same state twice** (a new attribute, a battery update) | Nothing changes: the entry delay does not start again and no second event is made. |
| A door **opens and closes again** in the entry delay | The alarm still ends in an alarm after the entry delay; closing the door does not cancel it, only a code does. |
| A **second sensor** goes off during the alarm | One alarm: no second alarm starts. |
| **Smoke** during an intrusion alarm | It is not lost: the alarm shows the fire cause as well. |

## Commands

| Situation | What Vigil does |
|---|---|
| The same **arm command twice** during the exit delay | The delay is not extended. |
| **Disarm twice** | Harmless; the system is disarmed. |
| **Disarm during the exit delay** | The arming is cancelled and stays cancelled. |

## When the rest of the installation fails

| Situation | What Vigil does |
|---|---|
| The **phone cannot be reached** (the notify service fails) | The failure is reported and logged; the alarm is not affected. |
| The **siren cannot be switched on** | Reported and logged; the alarm is not affected, and it can still be disarmed. |
| Both at the same time | The alarm still triggers, shows its state on the panels and card, and can be disarmed with a code. |

## What is not covered

- Home Assistant itself being down, or the network between Home Assistant and a Zigbee or Z-Wave stick being down: see the heartbeat and the supervision of unreachable sensors.
- A power cut: Vigil only knows what Home Assistant tells it. Put the host, the router and the Zigbee or Z-Wave stick on a UPS if you rely on the alarm.
- Certification: Vigil is not a certified alarm system.
