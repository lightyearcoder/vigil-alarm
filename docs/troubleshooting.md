# My alarm does not do what I expect

Find what you see below. For each symptom: the likely causes, where to check, and what to do.

**Always look first:**

- **Overview** in the panel: the *Ready for use?* card names what is missing in the settings. *Attention* names sensors with an empty battery or that are unreachable. *What each mode watches* shows which sensors take part in which mode.
- **Last event:** the entity `sensor.vigil_alarm_last_event` and the event log (`event.vigil_alarm_alarm_events`) tell you what happened and why something was refused.
- **Attributes of the alarm** (`alarm_control_panel.vigil_alarm`): `open_sensors`, `bypassed_sensors`, `faults`, `problems`, `refuse_reason`.

## The alarm will not arm

| You see | Cause | What to do |
|---|---|---|
| `refuse_reason: sensor_open` | A watched sensor is open (a window, for example). | Close it, or choose on the sensor what happens when it is open at arming (bypass, wait until closed, refuse). |
| `refuse_reason: sensor_unavailable` | A sensor is unreachable (empty battery, out of range). | See *Attention* for which one. Fix it, or bypass it. |
| `refuse_reason: alarm_condition` | A fire, gas or tamper alarm is active. | Fix the cause and disarm first. |
| `refuse_reason: not_disarmed` | The alarm is already armed or in its exit delay. | Disarm first. |
| An error about the code | Wrong code, too short, not allowed for that mode, or locked (see below). | Check the user on the *Users* tab. |

## The alarm does not go off on an open door or motion

1. **Is the alarm really armed?** During the exit delay (`arming`) nothing is watched yet.
2. **Is the sensor in a sensor group?** An intrusion sensor without a group watches nothing. If *What each mode watches* says "no sensor group", create the default groups (card *Ready for use?*).
3. **Is the group active in this mode?** *Interior* applies to Away only, for example. In Home a motion sensor never triggers.
4. **Is the sensor bypassed?** Then it is listed under `bypassed_sensors`. A bypass ends when you disarm.
5. **Is the type "delayed"?** Then you get the entry delay (`pending`) first, and the alarm only goes off if you do not disarm in time.
6. **Is there a confirmation rule?** Then the alarm only goes off when enough different sensors trigger within the time window. A single sensor only gives the "without confirmation" notice.
7. **Is the sensor unreachable?** Then it cannot trigger. See *Attention*.
8. **Is it the right entity?** In *Developer tools → States*, check that the entity really turns `on` when the door opens.

## No notification on my phone

1. Is there a **notification channel**? If not, *Ready for use?* says so and offers your phone.
2. Are the right **categories** on? Only messages in those categories are sent (alarm, pending, fault, technical).
3. Is there a **delay**? An escalation channel with a 30 second delay only notifies after 30 seconds, and not if you disarm or acknowledge first.
4. Use the channel's **test button**. If the test does not arrive, the problem is Home Assistant or the app, not the alarm: check the notification permission of the app on your phone.
5. Is the **service** right? It must be an existing `notify.` service.

## The siren does not sound

1. Is a siren set up, and does it sound for *this cause* (intrusion, fire, gas, tamper, fault)?
2. Try the action `vigil_alarm.test_siren`. If it does not sound, the entity itself is the problem (unreachable, empty battery).
3. Was the siren **silenced** with `vigil_alarm.silence`? Then the alarm stays active but the siren is quiet.
4. Has the **maximum duration** passed? The siren stops by itself after that.

## My code is refused

- **Too short:** the minimum length is in *Settings* (4 to 12 characters).
- **Locked:** after some wrong codes Vigil locks that place in steps (by default 5, then 15, then 60 minutes), including for the right code. Wait a moment; the event log shows `code_locked`. If it shows `code_locked_permanent`, the panel stays closed until an administrator presses *Clear lock* under Panels. The numbers are under *Settings*, *Locking*.
- **Not allowed:** the user may only use certain modes. Check *Allowed modes*. Disarming always works with a valid code.

## False alarms

- Give doors the type **delayed** with an entry delay, so you can disarm in time.
- Let a motion sensor watch in Away only (group *Interior*).
- Use a **confirmation rule**: an alarm only when two motion sensors trigger within a minute.
- For a notification, check the event log to see which sensor it was.

## No battery or tamper notifications

- The sensor needs a **battery sensor**. *Ready for use?* names sensors without one. A device that only reports "battery low" (on/off) works too.
- If the device has a **tamper sensor**, enter it on the sensor. The card names tamper sensors that are not connected to anything.

## A refusal is in English, or in another language than I expected

When a standard Home Assistant card (for example the tile with the arm buttons) shows a refusal, the text is in the language **Home Assistant is set to** (*Settings, System, General*), not in the language of your profile, and without a user name: *Mode Custom is not allowed to be armed by you.* Vigil has the texts in six languages (English for any other). The Vigil card and the touch panel show the refusal in the language of the panel.

## The entities are named differently than I expected

Vigil's entity ids always end in the English name, also when Home Assistant is set to another language (for example `binary_sensor.vigil_alarm_intrusion_alarm`). What you see in the interface follows your own language. Check the real names under *Settings → Devices & services → Vigil Alarm*. If you come from an older version, update your automations and dashboards to the new ids (see the release notes).

## The panel is empty

Hard refresh the browser (Ctrl+F5) and check that the integration is running under *Devices & services*. Otherwise look in the log (*Settings → System → Logs*, search for `vigil`).

## Still not working?

Download the diagnostics (*Devices & services → Vigil Alarm → ⋮ → Download diagnostics*), which hold no codes or names of people, and report it on GitHub (see the *About* tab).

## I keep getting a siren test reminder

The reminder repeats until a test is done. Tap *Test siren* in the message, use *Test siren now* on the Overview tab, or call `vigil_alarm.test_siren`. To stop the reminders, set the interval under *Settings* to 0.

## The heartbeat fails

The *Heartbeat* card on the Overview tab names the reason: *no connection* (Home Assistant cannot reach the internet or the address is wrong), *no answer within 10 seconds*, or *HTTP 404* and similar (the service does not know the address; copy it again). Correct it under *Settings* and click *Test now*.
