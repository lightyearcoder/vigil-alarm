# Vigil Alarm: user guide

This guide explains how to set up and use Vigil Alarm. For installation see the
[README](../README.md). A Dutch version is in
[gebruikershandleiding.nl.md](gebruikershandleiding.nl.md).

> Vigil Alarm is not a certified alarm system. Test it regularly and do not rely on it as your
> only protection.

## Contents

1. [How it fits together](#how-it-fits-together)
2. [Setting it up, step by step](#setting-it-up-step-by-step)
3. [Using the alarm every day](#using-the-alarm-every-day)
4. [What happens during an alarm](#what-happens-during-an-alarm)
5. [Reference: the panel, tab by tab](#reference-the-panel-tab-by-tab)
6. [Automations and blueprints](#automations-and-blueprints)
7. [Automatic arming](#automatic-arming)
8. [Self-monitoring](#self-monitoring)
9. [Restarts and updates](#restarts-and-updates)
10. [Troubleshooting](#troubleshooting)
11. [Limits to know about](#limits-to-know-about)

## How it fits together

| Part | What it is |
|---|---|
| **Alarm** | One `alarm_control_panel` entity. States: *disarmed*, *arming* (exit delay), *armed home / away / night*, *pending* (entry delay) and *triggered*. |
| **Modes** | *Home* (you are in, the outside is guarded), *Away* (nobody home, everything is guarded) and *Night* (you sleep, the outside is guarded). Each mode has its own exit delay. |
| **Sensor** | One detector, linked to a `binary_sensor` (on = open or alarm). Every sensor has a **class**. |
| **Sensor group** | Decides **in which modes** the intrusion sensors in it are watching. |
| **Confirmation rule** | Optional. An alarm only follows when several different sensors trigger within a time window. |
| **User** | A person with a code, optionally limited to certain modes. |
| **Notification** | One `notify` service that receives messages, optionally delayed (escalation). |
| **Siren** | Optional. Something that makes noise during an alarm. |

### Sensor classes

| Class | Behaviour |
|---|---|
| **Intrusion** | Watches in the modes of its sensor groups. Type *instant* (alarm at once), *delayed* (entry delay first, for the front door) or *follower* (only alarms when a delayed sensor was opened first, for example a hallway PIR behind the front door). |
| **Fire** | Always watches, in every mode, also when the alarm is off. Alarm at once. |
| **Gas** | Always watches. Choose the kind of gas: carbon monoxide, natural gas, LPG or other. With natural gas or LPG Vigil never switches the flash light, because of the risk of sparks. |
| **Tamper** | Always watches. A tamper contact that opens raises an alarm. |
| **Water** | Always watches. A *technical alarm*: it never changes the alarm state, it only publishes events and an "alarm active" sensor. |

### Sensor groups: which sensors watch in which mode

A sensor group is a list of modes. An intrusion sensor is in one or more groups and watches in
every mode in which one of its groups is active. Two groups are created for you:

| Group | Active in | For |
|---|---|---|
| **Perimeter** | Home, Away, Night | doors and windows |
| **Interior** | Away | motion sensors |

So in *Home* only the doors and windows count, and you can walk around freely. In *Away* the
motion sensors count as well. You can add groups, for example *Basement* for *Night* only.

This is also why Vigil does not use Home Assistant areas for this: an area says **where** a
sensor sits, a sensor group says **how you want to use it**. A door contact and a PIR in the
same room belong in different groups.

The **Overview** tab shows "What each mode watches", so you can check the result.

## Setting it up, step by step

Open **Vigil Alarm** in the sidebar (only administrators see it). Saving anything reloads Vigil Alarm;
the alarm state is kept.

1. **Check the settings** (tab *Settings*): modes, exit delays, default entry delay, alarm
   duration and whether a code is needed to arm.
2. **Add your sensors.** The quick way is *Sensors → Find sensors*: Vigil lists the door, window, motion, smoke, gas, water and tamper sensors that Home Assistant already knows, with the battery and tamper sensor of the same device. Tick the ones you want, change a name if you like, tick *Entrance* for doors you walk through (they get an entry delay) and add them in one go. Nothing is saved until you press the button at the bottom. Without sensor groups, press *Create default groups* first (Perimeter for doors and windows, Interior for motion). To add one by hand use *Sensors → Add sensor*:
   - Name it ("Front door"). The name decides the entity names (`sensor.front_door_status`).
   - Pick the `binary_sensor`. For a door contact or motion sensor the panel suggests the right
     sensor group by itself.
   - Choose the class and, for intrusion, the type and the sensor groups.
   - Has the device a tamper contact as well (most Zigbee door contacts do)? Fill it in under *Tamper entity*. Vigil adds a tamper sensor named "Front door (tamper)" by itself: always watching, with its own bypass switch. It follows the sensor when you rename, change or delete it, and has no row of its own in the table.
   - *If open when exit delay ends* decides what happens to a door that is still open when the
     alarm arms: **bypass with a notice** (default; it is guarded again once it closes), **wait
     until closed**, **refuse to arm**, or **start entry delay**.
   - *When the sensor becomes unreachable*: **block arming** (default for intrusion and
     tamper), **notify only** (default for fire, gas and water), **raise alarm** or **arm
     anyway (bypass)**. Fire and gas can never be bypassed.
   - Optionally add a battery sensor; Vigil then warns when it runs low.
3. **Add a user** (tab *Users*): a name and a code. Without any user, no code is needed at all.
   A user can be limited to certain modes, and can be allowed to bypass tamper sensors.
4. **Add a notification** (tab *Notifications*): pick a `notify` service and the kinds of
   message it should get. With a *delay* the channel only sends alarm messages when the alarm is
   still active after that time: that is an escalation channel for a second person or device.
5. **Optional: a confirmation rule** (tab *Confirmation rules*): choose the instant intrusion
   sensors, how many must trigger, and in what time window.
6. **Optional: a siren** (tab *Sirens*). See below.
7. **Look at *Ready for use?*** at the top of the *Overview* tab. It names what is still missing (a user with a code, a notification channel, a mode that nothing watches, sensors without a battery sensor) and has a button to the right place. If you have no notification channel yet and Home Assistant knows your phone, one button adds it and sends a test message.
8. **Test everything** with the *Test* buttons and by arming and opening a door. Use the
   [test guide](installatie-en-testen.nl.md) (Dutch) for a full test plan with virtual sensors.

### Sirens

A siren has an on/off entity (`siren`, `switch` or `light`) and optional extras: a flash light,
a tone selection entity and a volume entity. Per cause (intrusion, fire, gas, tamper) you can
give a tone and volume. They are set just before the siren sounds and restored afterwards. The
siren stops when the alarm is switched off and after a maximum duration. A siren that stops by
itself can be switched on again every N seconds.

Many sirens cannot report whether they are really on. Then `siren_started` has
`verified: false`, and a command that fails gives `siren_failed` and a notification.

**Preset for the Sonoff SNZB-09P (Zigbee2MQTT):** pick the siren's on/off switch under
*Siren*, then choose the preset. Vigil fills in tones (classic for intrusion, warning for fire,
emergency for gas, rapid for tamper), volume, duration, and looks for the tone, volume, flash
light, battery and power-mode entities of the same device. If something is not found you pick
it yourself. With ZHA or another integration, choose the on/off entity and fill in the rest by
hand.

## Using the alarm every day

### Arming and disarming

Use the alarm panel card (or the tile card, or the Companion app), the *arm* actions in an
automation, or the [dashboard](../examples/dashboard.yaml). Enter your code if one is needed.

- **Arming** starts the exit delay (state *arming*), then the alarm is *armed*. Walk out.
- **Disarming** always needs a code when users exist. During the entry delay (*pending*) you
  have the entry delay time to enter it.
- A user can be limited to certain modes; arming another mode is refused.

### When arming is refused

Vigil tells you why: *an alarm condition is open* (a fire or tamper sensor is on), *a sensor is
unavailable* (an intrusion sensor is unreachable and set to block), or *a sensor is open* (a
sensor set to refuse). The attribute `refuse_reason` and the notification say which sensors. Fix
the sensor, or bypass it.

### Bypassing a sensor

Bypass leaves one sensor out until the alarm is switched off (or until you un-bypass it).

- In the panel and dashboard: the **Bypass** switch of the sensor (administrators only).
- By action: `vigil_alarm.bypass` and `vigil_alarm.unbypass` with the sensor entity and, for people who are
  not administrators, a code. That code is only needed if arming needs one too (the setting
  *code required to arm*). Tamper sensors can only be bypassed by administrators and by users
  who have that right.
- Fire and gas sensors can never be bypassed.

### A touch panel

With the ESPHome panel (Guition 4848) you arm, disarm and bypass sensors without a phone. It shows
only the modes that are on in Vigil, asks for a code the way Vigil does and can switch language.
Installation and options are in [esphome/README.md](../esphome/README.md). Every panel has its own
`source` (for example *panel garage*), which shows in the history as *Anna (panel garage)*. A wrong
code gives the event `code_rejected`, never with the code itself. After 5 wrong codes within 5 minutes all codes are locked for 5 minutes (event `code_locked`); an administrator in the UI can still operate the alarm.

### Silence and acknowledge

- `vigil_alarm.silence` stops the sirens while the alarm stays active.
- `vigil_alarm.acknowledge` cancels the pending escalation messages: you have seen it.

Both need a user code, or an administrator in the interface.

## What happens during an alarm

An example with the alarm armed in *Away* and the front door (a delayed sensor) opening:

| Moment | What happens |
|---|---|
| Door opens | State *pending*. Event `pending_started`. Notification "Entry delay started". |
| Within the entry delay | Disarm with a code: no alarm. |
| Entry delay ends | State *triggered*, cause *intrusion*. Event `triggered`. Notifications go out, sirens sound, "Intrusion alarm" turns on. |
| After the delay of an escalation channel | If the alarm is still active and not acknowledged, that channel sends its message. |
| Disarm, or the alarm duration ends | Sirens stop, `trigger_ended`, state back to *disarmed* or *armed*. |

An instant sensor skips the entry delay. Fire, gas and tamper alarm at once, in every state. A
more serious cause replaces a less serious one (`trigger_cause_changed`): the order is fire,
then gas, tamper, sensor fault and intrusion.

With a **confirmation rule**, a single trigger of one of its sensors raises no alarm. It
publishes `sensor_unconfirmed` (and a notification if you chose to be told). When the required
number of different sensors trigger within the window, the alarm is raised with `confirmed_by`
in the event.

## Reference: the panel, tab by tab

Actions in the lists are icon buttons (edit, copy, delete, test); hover for the name. Rules and users have no copy button. Some fields have an ⓘ: click it for a fuller explanation.

| Tab | What you do there |
|---|---|
| **Overview** | *Ready for use?* (what is still missing), a *Dashboard* card with a button that copies a dashboard with your own entity ids, alarm state, attention points (low batteries, unreachable devices), what each mode watches, and the live status of every sensor. |
| **Sensors** | *Find sensors* proposes sensors from Home Assistant; add, edit, copy and delete sensors. Under each name a sentence says how the sensor reacts and when it is watching. The table shows battery level in its own column. One entity can belong to only one sensor. The *Tamper entity* field links the tamper signal of the same device: Vigil creates a separate tamper sensor that can be bypassed on its own. You can also create a standalone tamper sensor. |
| **Sensor groups** | Which sensors watch in which modes. A group can *suggest itself* for new door contacts or motion sensors. A group that is still in use cannot be deleted. |
| **Confirmation rules** | Several sensors must trigger within a time window. A sensor that is in a rule cannot be deleted. |
| **Users** | (Cannot be copied.) Name, code, allowed modes, right to bypass tamper. Codes are stored hashed and never shown. Leave the code empty when editing to keep it. |
| **Notifications** | `notify` service, kinds of message (alarm, entry delay, arming and disarming, faults and notices, technical alarms), delay, high priority. *Test* sends a test message. |
| **Sirens** | See above. *Test* sounds the siren for 3 seconds (refused during a real alarm). |
| **Settings** | Modes, exit delays, entry delay, alarm duration, battery limit, code required to arm, minimum code length (4 to 12 characters, default 4; applies to new and changed codes, existing codes keep working). |
| **About** | A "new" badge after an update, version, links to the user guide and GitHub, release notes (newest first) and a button that copies the details for a bug report. |

The language of the **notification texts** follows the Home Assistant system language (Settings →
System → General). The panel follows your own profile language (English and Dutch).

## Automations and blueprints

Everything beyond notifications and sirens is yours to automate. Vigil publishes the event
entity `event.<name>_alarm_events`; the [README](../README.md#for-automations) lists all events
and their data.

The included [blueprints](../README.md#blueprints) cover the common cases:

- **Flash lights during an alarm** saves the state of your lights, flashes them while the alarm
  is triggered and restores them afterwards, also when the alarm is switched off. Choose which
  causes flash (gas is off by default). The default of 2 seconds on and 2 seconds off stays
  well below the rate that matters for photosensitive people. For Hue, use a room or zone
  (group) instead of single lamps; groups are disabled by default in Home Assistant, so enable
  them first.
- **Announce alarm events with speech** speaks a message when the alarm arms, disarms, starts
  the entry delay or goes off. Leave a message empty to stay silent for that event.
- **Run your own actions on alarm events** is the general building block: choose events and add
  any actions, with `event_type` and `data` available.
- **Remind when arriving at an armed home** sends a message when someone comes home while the
  alarm is armed. It does not disarm.

### Automatic arming

**Arm when everyone has left** and **Arm at a set time** arm the alarm for you. They never
disarm: disarming always needs a person with a code.

Arming needs a code unless *Code required to arm* is switched off in the panel. You have two
choices:

1. Switch *Code required to arm* off. Then anyone who can reach the alarm entity can arm it
   (disarming still needs a code). This is the simplest option and carries no secret.
2. Keep the code requirement and put a code in the blueprint. That code is stored **as plain
   text** in the automation. Make a separate Vigil user for it, limited to the one mode the
   automation uses, and never use your own code.

If arming is refused (for example because a door is open), you can get a message that says
why. If you leave the message field empty, nothing is sent.

## Self-monitoring

Real faults (an unreachable sensor, a low battery, a siren that is unavailable or on battery power) also appear under *Settings → System → Repairs* and go away by themselves when fixed. Missing settings are not repairs; *Ready for use?* shows those.

- **Battery:** give a sensor or siren a battery sensor. Vigil reports `battery_low` when the
  level drops to the limit (default 20%, a setting) and `battery_ok` when it recovers.
- **Sensors:** an unreachable sensor is handled by its *when unreachable* setting, and reported
  with `supervision_lost` and `supervision_restored`.
- **Sirens:** Vigil reports when a siren becomes unavailable and, with a power-mode entity,
  when it runs on its battery (the value that means "on battery" is a setting, default
  `battery`; check what your device reports). Add the tamper contact of a siren as a tamper
  sensor.
- Problems that exist at startup are listed in the `problems` attribute of the alarm without an
  event; events follow on changes. The overview shows them under *Attention*.

## Restarts and updates

- The alarm state and running timers are saved. After a restart the alarm is in the same state;
  an entry delay that ran out during the restart becomes an alarm, with the correct time.
- For the first 10 seconds after Home Assistant starts, sensor states are not trusted yet, so
  sensors that have not loaded do not cause false faults. Arming in that time is refused with
  "still starting up".
- Updating Vigil Alarm through HACS needs a Home Assistant restart. Your configuration is
  migrated automatically.

## Troubleshooting

See also **[My alarm does not do what I expect](troubleshooting.md)**.

| Problem | What to do |
|---|---|
| **No "Vigil" in the sidebar** | Only administrators see it. Hard-refresh the browser, restart Home Assistant, and look in the log for lines with `vigil`. |
| **The panel stays empty or says it could not be loaded** | The integration is not running: look under Settings → Devices & services for an error. Refresh the browser. |
| **Arming is refused** | Read the reason in the notification or the `refuse_reason` attribute, and check the sensors named there. |
| **A sensor is reported unreachable** | Check the device. For a short time you can set *when unreachable* to *arm anyway (bypass)*. |
| **No notification arrives** | Use *Test* on the notification. Check that the `notify` service exists and that the kind of message is ticked. |
| **The siren does not sound** | Use *Test* on the siren. Check the on/off entity and the siren's *Sound for* causes. Some sirens stop by themselves after their own duration; see *repeat every*. |
| **An automation does not react** | Trigger on the event entity (not on the alarm state) and check `event_type` in the automation trace. |
| **A blueprint cannot arm** | Arming needs a code. See [Automatic arming](#automatic-arming). |

For a bug report, include what you did, what you expected, what happened and the log lines
with `vigil` (Settings → System → Logs). For more detail add to `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.vigil_alarm: debug
```

## Limits to know about

- Vigil Alarm is **not certified** for any alarm, fire-detection or insurance standard.
- It runs inside Home Assistant. If Home Assistant is down or restarting, there is no alarm.
- Everything is configured by Home Assistant administrators, in the panel. There is no other
  way to edit sensors and users; this is on purpose.
- **Tags** can be stored on a user but have **no function**. Operate the alarm
  with a code.
- Your own code only protects the alarm entity. Anyone who is a Home Assistant administrator
  can change the configuration.
- Test regularly, including a real alarm and your notification route, and replace batteries
  when Vigil tells you to.
