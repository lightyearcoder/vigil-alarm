# Vigil Alarm: installing on Home Assistant OS and testing

This guide is for Home Assistant OS (HAOS). You place the `vigil_alarm` folder in the configuration folder, add a test package with virtual sensors and then work through the tests. Everything is done without real sensors or a real siren. It is the English version of [installation-and-testing.nl.md](installation-and-testing.nl.md).

**Note:** this is a test version of a self-built integration, not a certified alarm system. Expect differences in a real installation and report them (see chapter 7).

---

## 1. Preparation

1. Check your version: **Settings → About**. At least 2026.2.3.
2. Make a backup: **Settings → System → Backups → Create backup**. Wait until it is done.
3. Unzip `vigil-alarm.zip` on your Mac. You get a folder `vigil-alarm`. In it is `custom_components/vigil_alarm`. Only that folder `vigil_alarm` is copied.

## 2. Putting the files on Home Assistant

You need access to the configuration folder. The easiest way on a Mac is the Samba add-on.

1. **Settings → Add-ons → Add-on store**, search for **Samba share** and install it.
2. Open the add-on, tab **Configuration**: fill in a user name and password and save. Start the add-on (tab **Info**).
3. In Finder: **Go → Connect to Server** (⌘K) and type `smb://homeassistant.local` (if that does not work, use the IP address of your Home Assistant). Log in with the details you just chose.
4. Open the share **config**. If you see `configuration.yaml` there, you are in the right place.
5. If the folder `custom_components` does not exist yet, create it.
6. Copy the folder `vigil_alarm` (from `vigil-alarm/custom_components/`) into `config/custom_components/`. The result is `config/custom_components/vigil_alarm/manifest.json`. Check that exactly this path is right: one folder too many or too few is the most common mistake.

*Alternative:* the **Terminal & SSH** add-on with `scp -r custom_components/vigil_alarm root@homeassistant.local:/config/custom_components/`.

## 3. Placing the test package

The test package (`docs/vigil_test_package.yaml`) makes virtual sensors: a front door, two PIRs, a smoke detector, a tamper contact and a water detector, a battery level, a power mode and a virtual siren. You operate them with switches on a dashboard.

1. In the share **config**, create a folder `packages`.
2. Copy `vigil_test_package.yaml` (from `vigil-alarm/docs/`) into it.
3. Open `configuration.yaml` and make sure this is in it (if there is already a `homeassistant:` block, add only the `packages` lines):

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
4. **Developer tools → YAML → Check configuration.** The result must be "Configuration valid".
5. **Developer tools → YAML → Restart** (or **Settings → System → Restart**). A full restart is needed for the new integration; reloading YAML alone is not enough.

After the restart, among others `binary_sensor.vigil_test_front_door` and `switch.vigil_test_siren` exist.

## 4. Adding and setting up the integration

Everything is possible as an administrator only.

1. **Settings → Devices & services → Add integration**, search for **Vigil Alarm**. If you cannot find it, hard refresh the browser (⌘⇧R) and look at chapter 8.
2. Fill in for the test (short times make tests faster):
   - Name: `Vigil Alarm` (leave it, the entity names in this guide assume it)
   - Modes: home, away, night
   - Exit delay home `0`, away `20`, night `5`
   - Default entry delay `15`
   - Alarm duration `0`, battery threshold `20`, code required to arm: on
3. Click **Vigil Alarm** in the sidebar (the shield with a little house; only visible to administrators). If you do not see it, hard refresh the browser. It has the tabs **Overview, Partitions, Sensor groups, Sensors, Confirmation rules, Users, Notifications, Sirens, Panels, Log, Settings, Backup** and **About**. At the top of the Overview is the card **Ready for use?**: it shows what is still missing and has a button to the right place for each point. On each tab, add the items below with the button at the top. Every row has buttons to edit, copy or delete. You edit sensors, users and so on only here; under *Devices & services* there is only the alarm itself (with the button *Reconfigure* for the basic settings).
   Each time you save something, Vigil reloads itself. That takes a few seconds; the alarm state is kept.

**Users** (add a user)

| Name | Code | Allowed modes | May bypass tamper |
|---|---|---|---|
| Anna | 1234 | empty (all) | on |
| Bob | 5678 | home only | off |

**Sensor groups.** A sensor group decides in which modes the sensors in it are watching. A new installation has none yet. On the Overview, in the card **Ready for use?**, click **Create the default groups** (or in the window *Find sensors*). Vigil then creates two groups, which you simply use:

| Name | Active in modes | For |
|---|---|---|
| Perimeter | home, away, night | doors and windows |
| Interior | away | motion (PIR) |

If Home Assistant is set to another language, they have other names, for example *Buitenschil* and *Binnen* (Dutch), *Außenhaut* and *Innenraum* (German), *Périmètre* and *Intérieur* (French), *Perimetro* and *Interni* (Italian) or *Perímetro* and *Interior* (Spanish). Vigil does not create a kind you already have a second time.

*Did you already install the previous version?* Then at startup Vigil converts your old "modes per sensor" into sensor groups by itself, with names such as "Away" and "Home + Away + Night". Behaviour does not change; you can rename them and check them on the Sensor groups tab. Also look at "What each mode watches" on the Overview.

**Sensors** (add a sensor, or find them with the button **Find sensors**, see test 26; the name determines the entity names, so keep to these names). For an intrusion sensor, choose which sensor groups it is in. If you choose a door contact or motion sensor as the entity, the panel proposes the right group itself.

| Name | Entity | Class | Type | Sensor group | When open at the end of the exit delay |
|---|---|---|---|---|---|
| Front door | binary_sensor.vigil_test_front_door | intrusion | delayed | Perimeter | bypass with a notice |
| Living PIR | binary_sensor.vigil_test_living_pir | intrusion | instant | Interior | wait until closed |
| Kitchen PIR | binary_sensor.vigil_test_kitchen_pir | intrusion | instant | Interior | wait until closed |
| Smoke | binary_sensor.vigil_test_smoke | fire | | | |
| Tamper | binary_sensor.vigil_test_tamper | tamper | | | |
| Water | binary_sensor.vigil_test_water | water | | | |

For "Front door" leave **Battery sensor** empty. For **Kitchen PIR** fill in `sensor.vigil_test_battery_level` as the battery sensor.

**Confirmation rule:** (only sensors of the type *instant* are offered; Front door is delayed and so does not take part) name `Downstairs`, sensors Living PIR and Kitchen PIR, required 2, time window 60 s, notify when unconfirmed: on.

**Notification channel 1:** name `Persistent`, service `persistent_notification`, all messages on, delay 0. This notification appears in the Home Assistant sidebar (the bell), so you do not need a phone. Later you can add a second channel with your phone (`mobile_app_...`).

**Notification channel 2 (escalation):** name `Escalation`, service `persistent_notification`, only "Alarm", delay 30 s.

**Siren:** name `Test siren`, on/off `switch.vigil_test_siren`, sounds for everything, maximum duration `60`, switch on again `0`, battery sensor `sensor.vigil_test_battery_level`, power mode `sensor.vigil_test_siren_power_mode`. For the first test, do not give the siren a tone or volume of its own.

## 5. Making a dashboard

**The example dashboard:** make a new dashboard (**Settings → Dashboards → Add dashboard → New dashboard from scratch**), open it, choose the pencil at the top right, the three dots and **Raw configuration editor**. Paste the contents of `examples/dashboard.yaml` (from the zip) and save. The example sensors in the card *Sensors* are named as in chapter 4 (Front door, Living PIR, Smoke, Tamper); change them if you use other names.

**A test dashboard for the switches:** make a second view or a new dashboard with an **Entities card** with:

`input_boolean.vigil_test_front_door`, `..._living_pir`, `..._kitchen_pir`, `..._smoke`, `..._tamper`, `..._water`, `..._lamp`, `input_number.vigil_test_battery`, `input_select.vigil_test_power`, `switch.vigil_test_siren`, `light.vigil_test_lamp`.

Also keep **Developer tools → Actions** open: that is where you call the services.

## 6. The tests

After each test put everything back: all test switches off, alarm disarmed. The code is always `1234` unless stated otherwise. "Notification" means: look in the bell in the sidebar. The notification texts are in the **system language** (Settings → System → General); in this guide they are given in English, with another system language they are in that language (for example "Single trigger without confirmation").

| # | Do | Expected |
|---|---|---|
| **1. Basics** | Open the integration | A device "Vigil Alarm" and a device per sensor (Front door, Living PIR, …). Alarm state `disarmed`. Every sensor shows status "Closed". |
| **2. Arm home** | Alarm panel: Home, code 1234 | Immediately `armed_home` (exit delay 0). Last event: `armed`, by Anna. Disarming with code 1234 works. |
| **3. Exit delay** | Arm Away | State `arming`, after 20 s `armed_away`. The attribute `delay_end` shows the end time. |
| **4. Entry delay** | Armed away, switch Front door on | State `pending`. Disarm with the code within 15 s: no alarm. Again: let the 15 s run out: `triggered`, cause `intrusion`, notification "ALARM: intrusion (Front door)…", siren on, "Intrusion alarm" on. |
| **5. Confirmation rule** | Armed away, only Living PIR on | No alarm; notification "Single trigger without confirmation". Then within 60 s Kitchen PIR on as well: `triggered`, `confirmed_by` contains both. |
| **6. Open at arming** | Front door on, Living PIR on, then Arm Away | After 20 s `armed_away`. Front door status "Bypassed at arming" with a notification, Living PIR "Waiting until closed". Living PIR off: it is watched again. |
| **7. Fire** | Smoke on (not armed) | Immediately `triggered`, cause `fire`, siren on. Arming is refused. Smoke off, disarm with the code. |
| **8. Bypass** | Call the action `vigil_alarm.bypass` with sensor `binary_sensor.vigil_test_living_pir` (without a code) and look at the entity "Living PIR Bypassed" (read only, there is no switch). Do the same with sensor `binary_sensor.vigil_test_kitchen_pir` and `vigil_alarm.unbypass`. Try `vigil_alarm.bypass` for `binary_sensor.vigil_test_smoke`. | As an administrator in the interface you do not need a code. Living PIR shows "Bypassed" and its *Bypassed* indicator turns on. Smoke has no *Bypassed* indicator and the action is refused (fire cannot be bypassed). The bypass ends when you disarm. The rule that Bob may not bypass tamper applies to ordinary users; as an administrator you can bypass tamper, and that is intended. This distinction is covered by the automatic tests. |
| **9. Codes and rights** | Bob (5678): Home works, Away does not. Wrong code. No code. | Bob can only do home. A wrong code and a missing code give an error. Disarming is never possible without a code. |
| **10. Escalation** | Let the alarm go off (test 4) and do not disarm | The notification of `Persistent` immediately, after 30 s also that of `Escalation`. With a second alarm that you disarm within 30 s the escalation notification does not come. Also try the action `vigil_alarm.acknowledge` (code 1234) within 30 s: no escalation. |
| **11. Siren** | Action `vigil_alarm.test_siren` (duration 5). During an alarm: `vigil_alarm.silence` with a code. | The test siren is on for 5 s and switches off by itself. During an alarm the test is refused. After `silence`, `switch.vigil_test_siren` goes off while the alarm state stays `triggered`. After the maximum duration (60 s) the siren goes off. |
| **12. Restart** | Armed away. Restart Home Assistant. | After the restart still `armed_away`. |
| **13. Alarm during restart** | Armed away, Front door on (entry delay 15 s), restart Home Assistant immediately | A restart takes longer than 15 s. After startup the state is `triggered`. The attribute `t` of `sensor.vigil_alarm_last_event` (at the event `triggered`) shows the moment the entry delay ran out, not the moment of startup. |
| **14. Startup** | Right after a restart, try to arm | First 10 s: "still starting up". No false faults or alarms because of sensors that have not loaded yet. |
| **15. Unreachable sensor** | Developer tools → States: set `binary_sensor.vigil_test_living_pir` to `unavailable` by hand. Try to arm Away. | Arming Away is refused (reason: sensor unreachable). Arming Home works. Restore by switching the matching switch on and off. |
| **16. Water** | Water on (also when armed) | "Water alarm" on with the sensor in the attribute. The alarm state does not change. Water off: ended. |
| **17. Battery and power** | `input_number.vigil_test_battery` to 15. Then `input_select.vigil_test_power` to `battery`. | Two notifications: "Battery low: Kitchen PIR (15%)" and "…: Test siren (15%)" (sensor and siren use the same sensor in the test). For the power mode: "Siren Test siren has lost mains power…". The attribute `problems` of the alarm shows both. Putting them back gives "Battery OK again" and "mains power again". |
| **18. Administrator only** | Make a user without administrator rights. Log in as that user. | The user can use the alarm panel (with a code) but cannot configure the integration. |
| **19. Language** | **Settings → System → General → Language** to Dutch, test an alarm | The text of the notifications follows the **system language**, not the language of your user profile. The names in the interface follow your profile language. |
| **20. Changing** | Change a sensor, a sensor group and the exit delay | The integration reloads itself; the alarm state stays as it was (invalid combinations are refused with a reason). |

### Extra tests: preset, blueprints and dashboard

**Preparation for the blueprints:** copy the folder `vigil_alarm` from `vigil-alarm/blueprints/automation/` to `config/blueprints/automation/` (create the folders if they do not exist). You get `config/blueprints/automation/vigil_alarm/flash_lights_on_alarm.yaml` and five other files. Then reload the automations: **Developer tools → YAML → Reload automations**. (With a public GitHub repository you can also import them with the buttons in the README.) Make an automation via **Settings → Automations → Create automation → Use blueprint**.

| # | Do | Expected |
|---|---|---|
| **21. Preset** | Sirens tab, *Add siren*. Choose `switch.vigil_test_siren` as the siren, and under *Preset* "Sonoff SNZB-09P (Zigbee2MQTT)". | Tone, volume and duration are filled in (for intrusion `siren_classic` and `high`, for fire `siren_warning` and `max`; value on battery power `battery`). Under the field it says "No other entities found for this device; choose them yourself", because the virtual siren is not a Zigbee device. Saving without a tone and volume entity gives an error (a tone or volume needs an entity): then fill in `select` entities or clear the tones and volumes. The field *Preset* itself is not saved (editing shows it empty again). If you have a real SNZB-09P with Zigbee2MQTT, choose the `siren_on` switch and check that the other entities are found. |
| **22. Blueprint: flash lights** | Make an automation with "Vigil - Flash lights during an alarm": Vigil events = `event.vigil_alarm_alarm_events`, alarm = `alarm_control_panel.vigil_alarm`, lights = `light.vigil_test_lamp`, flash on fire. Then switch `input_boolean.vigil_test_smoke` on. | `light.vigil_test_lamp` goes on and off every 2 seconds as long as the alarm is active. Disarm with code 1234: the flashing stops and the lamp is as it was before the alarm. Also do the test with the lamp on before the alarm: afterwards it is on again. |
| **23. Blueprint: arm at a set time** | Automation "Vigil - Arm at a set time": time in two minutes, mode Night, code 1234 (in this test house that is Anna). | At that time the alarm goes to *arming* and then `armed_night`. If an intrusion sensor that watches in Night is unreachable, arming is refused and the alarm stays off (with a message if you choose a notify entity). Delete the automation after the test. |
| **24. Blueprint: events** | Automation "Vigil - Run your own actions on alarm events": events `triggered` and `disarmed`, action "Notification" via `persistent_notification.create` with message `{{ event_type }} {{ data.cause | default('') }}`. | With an alarm "triggered fire" appears in the notifications, with disarming "disarmed". |
| **25. Dashboard** | Paste the example dashboard (chapter 5). Switch Smoke on. | The alarm panel card shows the alarm; "Status" names cause *fire* and sensor *Smoke*; the card "Needs attention" appears only when something is wrong (for example Living PIR on `unavailable`); the log card shows the events; the button "Silence the siren" silences the siren after confirmation. |

### Extra tests: setting up, codes and checks

| # | Do | Expected |
|---|---|---|
| **26. Find sensors** | Sensors tab, button *Find sensors*. | A wide window with the sensors found (door, window, motion, smoke, heat, gas, water, safety, tamper) of real or test devices, with the entity and the integration under each name. Sensors you already have are not shown, and nothing is ticked at the start: you tick what you want. Vigil's own indicators are not in it. For a door contact "Entrance" is on or off; the battery and tamper sensor of the same device are under "Included". Nothing has been saved yet. In the column *Sensor groups* you tick the groups per sensor (it starts at the proposal; only the groups of the chosen partition are offered), or choose a group for all ticked sensors with *Set group for ticked…*. *Ignore* on a row (for example a Hue room that appears as a second motion sensor) hides it; the button *Show N ignored* brings it back and *Restore* undoes it. An ignored sensor is also left out of the "new sensors" notice. |
| **27. Adding several at once** | Tick two sensors and click *Add 2*. Then do it again with a name that already exists. | The first time both are in the list at once (with a tamper item of its own if a tamper sensor belongs to it). The second time you get a clear error with the name of the sensor and nothing is saved. |
| **28. Discovery data** | In the search window click *Copy discovery data* and paste it somewhere. | A list with, per entity, only domain, device class, integration, a device number, category and unit. No names, entity ids or addresses. |
| **29. Ready for use?** | Look at the Overview. Solve a point (for example add a user with a code). | Every point has the button *Go there* (or *Create the default groups*). First come the points that are "Fix first", then the advice. When a point is solved, it disappears. When everything is in order it says "Everything is set up". |
| **30. Phone as a channel** | Delete all notification channels. If you have the Home Assistant app on your phone, look at the Overview. | At the point about the notification channel there is the button *Add phone: <name of your phone>*. It creates the channel and sends a test notification. Then there is a channel and the point disappears. |
| **31. Wrong codes** | Arm five times within five minutes with a wrong code. Then try the right code. | After the fifth wrong code there is an event `code_locked`. For five minutes the right code is refused too. Then it works again. An administrator without a code in the panel can operate as usual. |
| **32. Minimum code length** | Settings: set the minimum code length to 6. Add a user with a 4 digit code. | The user is refused with the message that the code must be at least 6 characters. Values outside 4 to 12 are refused. |
| **33. Alarm indicators and entity names** | Look at the entities of Vigil. | There are always the binary sensors for intrusion, fire, gas, tamper and water, even if you have no sensor of that class. The entity ids end in the English name (for example `binary_sensor.vigil_alarm_intrusion_alarm`), also when Home Assistant is in Dutch. |
| **34. Checking a code** | Call the action `vigil_alarm.check_code` with a right and a wrong code. | A right code gives no error. A wrong code gives an error and counts towards the lockout (test 31). |
| **35. Battery low as on/off** | On a sensor, set a `binary_sensor` with device class battery as the battery sensor. Switch it on. | The notification "Battery low: <name>" comes (without a percentage) and the sensor is in the attribute `problems`. If you switch it off, "Battery OK again" comes. In the sensor list, Battery says "low" or "ok". |
| **36. Copying the dashboard** | Overview, card *Dashboard*, button *Copy dashboard*. Paste it in a new dashboard (raw configuration editor). | The dashboard shows your sensors and alarm entities with the right entity ids; all cards work without changing example names. |
| **37. Sensor list on the touch panel** | Do you have the ESPHome panel? In Vigil set the panel's *Sensor list* to *only after unlocking*, give it an installer code and look at the sensor list on the panel. | Without a code you only see how many sensors are open; with the installer code of the panel the list is visible until the unlock time has passed. See `esphome/README.md`. |
| **38. What is new** | After an update of Vigil: open the panel. | On the tab *About* there is a badge "new" until you look at it. The first time in a browser there is no badge. |
| **39. Diagnostics** | Devices & services → Vigil Alarm → ⋮ → Download diagnostics. | A file with settings, items and the state. User names, codes and tags are not in it. |
| **40. Repairs** | Set `binary_sensor.vigil_test_living_pir` to `unavailable` by hand, or set the test battery to 15. Look under Settings → System → Repairs. | There is a repair "Sensor not reachable: Living PIR" (or "Battery low: … (15%)"). If you fix it, it disappears by itself. Missing settings (such as a notification channel) give no repair; they are in *Ready for use?*. |
| **41. Log** | Arm and disarm the alarm, let a sensor trigger. Open the tab *Log*. | The events are there, newest on top, with a readable name, the item (for example Front door), who did it and the result. No codes are in it. |
| **42. Downloading the log** | Click *Download (JSON Lines)* and *Download (CSV)*. Open the files in a text editor or Excel. | JSON Lines has one object per line; CSV opens with the columns `time, event, source, user, item, result, detail`. Times end in `Z` (UTC). The file starts with the oldest event. |
| **43. Keeping the log** | Restart Home Assistant, then look at the log. In *Settings* set the number of days to 1 and then to an invalid value (0). | After the restart the old events are still there. 0 is refused with the message that it must be between 1 and 3650. |
| **44. Self-test card** | Overview, card *Self-test*. | The last quiet check (within an hour after starting, then daily), the last siren test ("not yet" as long as you have not tested) and when the next one is due. |
| **45. Test siren now** | Click *Test siren now* (only visible when a siren is set up). | The siren sounds for 2 seconds. In the log there is `selftest_siren_tested`, the card shows the new time. During a real alarm the test is refused. |
| **46. Reminder** | In *Settings* set the interval to 1 day and wait until it has passed. Look at your phone. | You get a reminder on the channels with faults and notices. On a phone with the app there is a button *Test siren*; it makes the siren sound. After 3 days a second reminder follows. |
| **47. Missing channel** | Remove a `notify` service of a channel (for example by removing the app of an old phone) and wait for the daily check (or restart). | A repair about the missing notification channel comes and the card names the channel. If you fix it, the repair disappears. |
| **48. Overdue** | Leave a reminder unanswered for 10 days. | There is a repair that the siren test is overdue. A test removes it at once. |
| **49. Self-test settings** | Set the siren time to 9 and then the last hour before the first hour. | 9 is refused (1 to 5); the last hour must be after the first. Interval 0 switches the reminder off; the card says so. |
| **50. Setting up the heartbeat** | Make a check at a monitoring service (for example Healthchecks.io), paste the ping URL in *Settings → Heartbeat address* and save. Look at the Overview. | The card *Heartbeat* shows the interval. Within a minute there is a time at *Last success* and the check at the service is green. An address that does not start with http:// or https:// is refused. |
| **51. Test now** | Click *Test now*. | A message that the heartbeat has arrived, and the time of *Last success* is updated. |
| **52. Heartbeat with the alarm off** | Leave the alarm off and look at the service after ten minutes. | The calls also come in while the alarm is off. |
| **53. Failing** | Set a wrong address (for example with an extra letter in the key) and click *Test now*. Do that three times. | The card shows "Failed" with the reason (for example HTTP 404). After three times a repair "Heartbeat cannot be sent" comes. If you fix the address and test again, it disappears. |
| **54. Secret** | Download the diagnostics and search for a part of your ping URL. Also look in the Home Assistant log. | The URL is nowhere in it; in the diagnostics it says "redacted". |
| **55. Proving an outage** | Switch Home Assistant off for longer than the period plus the grace time of your check. | The service sends you a message. If you switch Home Assistant on again, the check turns green again. |
| **56. Registering a panel** | Tab *Panels → Add panel*: name, panel id (device name), modes, sensor list *only after unlocking*, installer code. Then look at Entities for `sensor.<panel_id>_profile`. | The panel is in the list with a badge. The profile sensor exists, has `profile_version` 1 and contains no sensor names without unlocking (only numbers). No code or hash is in it. |
| **57. Enforced by Vigil** | For the panel switch *May disarm* off and call `vigil_alarm.disarm` with `source` = the panel id and a valid code. | The call is refused; in the log there is `panel_refused`. Without that panel id as `source` the same call simply works. |
| **58. Unlocking and clearing the lock** | At the panel press *Unlock*. Then enter a wrong code three times on the panel and press *Clear lock*. | After *Unlock* the profile contains the sensor names until the unlock time has passed. After three wrong codes the panel is locked (default); *Clear lock* solves that, also after a restart. |
| **59. ESPHome panel with profile** | Flash the panel (`esphome/README.md`). Look first before you add the panel in Vigil, then after. | Before registration: *Not linked* with the panel id. After: only the allowed modes as buttons, the language of the panel, when locked only 'Open: n'. The installer code opens the sensor list and the info page; bypassing asks for a user code. On the tab *Panels* are hardware and firmware version. |
| **60. Panel blocked or not reachable** | Set the panel to *Blocked*. Then switch the block off again and take the power off the panel for 10 minutes. | Blocked: the panel shows *Blocked* and does nothing. After 10 minutes without a connection: repair *Panel not reachable* and a notification; as soon as it is back `panel_online` comes. The alarm itself does not change. |
| **61. Vigil card on a tablet** | Make an ordinary user, register a panel with that user, log the tablet in and put `type: custom:vigil-card` on a dashboard (see `docs/tablet.md`). | The card shows the state and only the modes of the profile. Arming and disarming with a code work; a wrong code gives an error on the keypad. The sensor list opens with the installer code and without it shows only a number. If you open the dashboard as an administrator, it says *Not linked*. |
| **62. Tablet offline** | Leave the Vigil card open for a while, then close the browser on the tablet and wait 10 minutes. | The panel in Vigil shows *Vigil card active* as long as the card is open. After 10 minutes of silence: repair *Panel not reachable* and a notification. If you open the card again, the repair disappears within a minute. |
| **63. Phone as a panel** | In Home Assistant make an ordinary account (an administrator is allowed too; it is in the list as *(admin)*). Under *Panels* add a row with that account in *Home Assistant account (tablet or phone)*. Log in on your phone as that account and put the Vigil card on a dashboard. | The card shows the controls according to the settings of that row. If you choose an administrator account or an account that already belongs to another panel, an error follows. |
| **64. Any code works, no code no operation** | Arm on that phone with the code of another user. Then try to disarm without a code. | With any valid code it works and the history shows for example *Bob (cleo-phone)*. Without a code it says *A code is required*. Five wrong codes block only that phone, not the tablet or the automations. |
| **65. Other accounts refused** | Log in as an ordinary account that is not registered anywhere (for example a child's) and try to arm or disarm, also with a valid code. | It is refused with *User is not registered* and `user_refused` is in the log, without a lockout. An administrator, a registered account, an automation and the ESPHome panel work as usual. |
| **66. Existing installation** | On an installation without a registered account (only ESPHome panels): operate the alarm with an ordinary account with a valid code. | Nothing changes after the update; the filter only starts as soon as an account is registered under *Panels*. |
| **67. Which code?** | On the panel (or the Vigil card) open the keyboard to disarm and then the one for *View sensors*. | Under the dots it says in grey *Enter your user code*, with the sensor list *Enter the installer code*. An error replaces the text in red. |
| **68. Order of the sensor list** | Open a door and a window and look at the sensor list on the panel. | Open sensors that can be bypassed are at the top, then unreachable ones, open fire and gas sensors, bypassed ones and last the closed sensors. |
| **69. Language of a new panel** | Under *Panels* add a panel. | The field *Language* has Nederlands, English, Deutsch, Français, Italiano and Español and is set to the language of your Home Assistant account (otherwise English; a language other than these six gives English). You first choose the kind of device: for *ESPHome panel* the form asks for the panel id, for *Tablet or phone* for the Home Assistant account. |
| **70. Back button on the info page** | On the panel open the info page (tab *Info*, installer code). | At the bottom are the tabs; with *Alarm* you go back to the main screen and the unlock is forgotten. |
| **71. The first tap wakes up** | Let the screen of the panel go off and tap where a button is (for example *Away*). | The screen turns on, but the button is not operated. A second tap does it. If the screen turns on because the alarm changes, the first tap works at once. |
| **72. No jump before going off** | Leave an alarm in entry delay or alarm and watch the panel until the screen goes off. Then tap. | The screen no longer jumps to another screen just before going off. After the tap the disarm screen is there (in entry delay or alarm), otherwise the main screen. |
| **73. Screen time and alarm** | In *Settings*, *Panel screen*, set the time to 20 seconds and leave *Also switch the screen off during an alarm* off. Arm and see whether the screen stays on during the countdown and goes off 20 seconds after arming. Cause an alarm: the screen stays on and shows ALARM. Switch the setting on and cause an alarm again: the screen goes off after 20 seconds. | The screen only goes off when disarmed and fully armed (and with an alarm if you switched that on), never during the countdown. |
| **74. Too long on the keyboard** | With the alarm disarmed open the keyboard and leave it. | After the set time the panel goes back to the main screen (visible), after the same time again the screen goes off. |
| **75. Lockout in steps** | In *Settings*, *Locking*, for a fast test set all the numbers to 1 and the waiting times to 1 minute. Enter a wrong code on the panel, wait a minute, enter a wrong code again, and so on. Then check that the fourth wrong code locks the panel permanently, also after a restart of Home Assistant, and that *Clear lock* opens it. Also enter a good code after one or two wrong codes. | Each step lasts the set time; the fourth wrong code gives `code_locked_permanent` and the panel stays closed until *Clear lock*; then everything starts again at the first step. A good code sets the counter back to zero. Afterwards put the defaults back (3, 5, 2, 15, 2, 60, 1). |
| **76. Sensor list with a user code** | On the panel open the sensor list and enter the code of an ordinary Vigil user. Then open the tab *Info* with the same code. | The list opens with the user code; the info page asks for the installer code and refuses the user code. |
| **77. Right to bypass** | Make two users: one with and one without *May bypass sensors*. In the sensor list try to bypass and restore a sensor with both codes. | Without the right, bypassing and restoring are refused with a message. With the right both work; for a tamper sensor *May bypass tamper* is also needed. |
| **78. Messages for wrong codes** | On the panel enter three wrong codes (default) and look at the message for the third. Then try again, also with the good code. | The third wrong code itself already gives "Too many wrong codes. Try again in 5 min" (in the language of the panel); the attempts after that do not count and name the minutes left. With a permanent lockout it says that an administrator must clear it. |
| **79. Restart without false messages** | Restart Home Assistant completely while the alarm is off (and later again while it is armed). Look at your fault channels and at the log. | No `supervision_lost` for sensors that come back within the waiting time; the log shows `startup_settled` with the waiting time. Remove a sensor on purpose: after the waiting time the message does follow. |
| **80. New main screen** | Switch the alarm off with everything closed and look at the panel. Then open a door or window. | A green ring with a shield with a tick, *Disarmed*, *All closed*, three tiles (*Home*, *Away*, *Night*) and at the bottom the tabs *Alarm*, *Sensors*, *Info*. With an open sensor the ring turns amber with an exclamation mark, it says *Open: 1* and the tab *Sensors* has a badge with 1. The names are nowhere on this screen. |
| **81. Countdown in the ring** | Arm on *Away* with an exit delay of 60 seconds. Then let someone enter (entry delay). | The ring is full with the number 60 in the middle and empties in 60 seconds; at 0 the alarm is armed. Under it is *Leave the house now* (no seconds in the text). On entry the ring is orange, starts full and counts down, with *Disarm with your code*. |
| **82. Alarm** | Cause an alarm. | A red frame around the screen, a redder background, a red ring with a bell, *ALARM* with the cause, a big green button *Disarm*. The keypad does not open by itself. |
| **83. Keypad and tabs** | Press *Disarm* and tap digits; press the delete key and the tick. Then open the sensor list and the info page via the tabs. Set the sensor list in Vigil to *never*. | Only asterisks in the field, the tick key is green, the keypad has no tabs and top left is a back arrow. The other pages have the tabs, the active tab has the colour of the state. With *never* the tab *Sensors* is gone. |
| **84. No connection** | Switch Home Assistant off or take the panel off the network. | The ring turns grey with a no-Wi-Fi icon and the title *No connection*; top right is the Wi-Fi icon (crossed out in red as long as there is no connection). |
| **85. Icons** | Check that all icons are a drawing. | No empty squares. If there are, the font with the icons was not downloaded while compiling: check the internet connection of ESPHome and compile again. |
| **86. New look of the card** | Open the Vigil card on a phone (narrow) and on a tablet (wide). Arm with a countdown and cause an alarm. | On the phone everything is below each other; on the tablet in two columns (ring left, buttons or keypad right). Same colours and countdown ring as the panel; with an alarm a red frame. Also check in a light theme that the text stays readable. |
| **87. Monitoring per panel** | Add a panel of the kind *Tablet or phone* and look at the field *Watch whether this panel is reachable*. Switch the kind to *ESPHome panel* and back. Open the Vigil card on a phone and then close the browser; wait 10 minutes. Then switch watching on for a tablet that you close. Open an existing panel from before this version. | For a tablet or phone the field is off by default, for an ESPHome panel on (it follows the kind, until you change it yourself). With watching off you get no repair and no notification, and the list shows *Not watched*. With watching on they do come after 10 minutes. An existing panel is still on. |
| **88. Keyboard on the card** | Open the Vigil card in a browser with a keyboard, press *Away* (or *Disarm*) and type the code with the keyboard. Try Backspace, Enter and Escape. Then type in another input field on the dashboard while the keypad is open. | The digits appear as dots, Backspace deletes one, Enter confirms and Escape closes the keypad. Another input field gets its own keys and the keypad does not react to them. |
| **89. Backup on a change** | In the Vigil panel open the tab *Backup*. Then add a sensor and look again. Click the eye icon (*View*) at that version. In the message *Saved* quickly click *Undo* (or use the arrow icon *Restore* in the tab). | After the change there is a version at the top with *Sensors: 1 added* and in the column *Vigil version* the version it was made with. *View* shows the change with the name of the sensor. *Restore* first shows *Sensors: 1 removed* and asks for confirmation. After that the sensor is gone and there is a version *Restored*; restoring that brings the sensor back. |
| **90. At most 10 versions** | Make more than 10 changes (for example keep changing a name). | The tab never shows more than the set number (default 10), the oldest falls off. Lower the number in *Settings* (card *Backup*): the oldest versions disappear. |
| **91. Exporting and importing** | Click *Export configuration* (a file is downloaded). Add a sensor. Choose *Import configuration…* and the file. Then try another file (for example a photo or a text file). | The overview shows *Sensors: 1 removed*; after *Apply* the sensor is gone and the previous state is a version *Import* in the backups. A file that is not a Vigil export is refused with a clear message and nothing changes. |
| **92. Why can't I arm?** | Leave a tamper sensor open while the alarm is off (trigger it, wait for the alarm and disarm while it is still open). Look at the tab *Overview* of the Vigil panel. Then try to arm with the Vigil card or the touch panel. | The card *Why can't I arm?* names the sensor and the modes. On the card and the panel it says *Cannot arm: … is open* and (if the panel may bypass) the button *Bypass and arm* appears. |
| **93. Bypass and arm** | Press *Bypass and arm* and enter the code of a user with the right to bypass (and for tamper also that right). Repeat with a user without that right. Repeat with an open smoke detector. | With the right: the sensor is bypassed in the list and the alarm arms. Without the right: a message that the right is missing and the alarm stays off. An open smoke detector can never be bypassed: the refusal remains and nothing changes. |
| **94. New sensors found** | In Home Assistant add a new door or motion sensor (or switch on one that was off). Wait a few seconds. Then click *Not now*. | On the tab *Sensors* there is the badge *1 new* and on the Overview the card *New sensors found* with the name. *Review and add* opens the list with only that sensor. After *Not now* the badge and card disappear, and the sensor is still in *Find sensors*. Nothing was added by itself. |
| **95. Wizard** | Click the card *Set up Vigil* (or *Setup wizard*) and go through all steps. Add something in one step and cancel in another. | After a form (saved or cancelled) the wizard is on the same step again. The step *Ready for use?* shows what is still missing. *Continue later* closes it; on the Overview there is then *Resume the wizard*. |
| **96. Export with time** | Click *Export configuration*, wait a moment and click again. | The file name contains the date and time of the last change of the configuration (not of exporting), for example `vigil-alarm-2026-10-18-13-27-05.json`. Exporting again without a change gives the same name. |
| **97. Practice mode** | Switch the alarm off and click *Start practice mode*. Arm, open a door and let the alarm go off. Then disarm. | No siren sounds and you get no notification, but panel and Vigil card show the alarm as usual. At the top is the chip *Practice mode*. In the log the events have `practice`. After disarming practice mode is off; a next alarm sounds the siren again. |
| **98. Walk test** | Switch the alarm off and click *Start walk test*. Open a door or window and walk past a motion sensor, but deliberately leave one sensor out. Click *Stop the test*. | Every sensor that reacts is ticked off at once. After stopping the skipped sensor is under *Not seen* with *did not react*. Fire, gas, water and tamper sensors do not take part. In the log there is `walktest_finished`. |
| **99. Practising only with the alarm off** | Arm the alarm and then try *Start practice mode* or *Start walk test*. Start a walk test, and then arm. | Both are refused with the message that the alarm must be off first. Arming stops a running walk test. |
| **100. Alarm memory with route** | Arm on *Home*. Open the front door (counts) and, before the alarm goes off or after, a motion sensor that only watches in *Away*. Let the alarm go off, open another sensor and disarm with a code. | On the Overview there is *Last alarm* with the sensors in the order in which they opened, with room and at each step *Counted* or *Did not count*. In the log, for the sensor that did not count, there is a line *Sensor opened during alarm*. On the Vigil card (with the sensor list unlocked) there is *Last alarm: …* with the route. |
| **101. Clearing and keeping the memory** | Restart Home Assistant after test 100. Check the card, then click *Clear alarm memory*. Then do an entry delay that you disarm in time. | The memory is still there after the restart; after clearing it is gone (and *Alarm memory cleared* is in the log). An entry delay that you disarm in time leaves nothing. During a running alarm you cannot clear. |
| **102. Cancelling a false alarm** | Let an intrusion alarm go off and disarm within 60 seconds with a code. Do it again and now wait 70 seconds. | First time: log `alarm_cancelled`, card *Cancelled as a false alarm*, and a message *Alarm cancelled: false alarm by …* to the alarm channels. Second time: simply disarmed, not cancelled. If you set the window to 0, it is never cancelled. |
| **103. Duress code** | For a user make a duress code (first a channel with the kind of message *Duress*; without a channel Vigil refuses the code). Arm and disarm with the duress code. | The alarm simply goes off, nothing is visible on panel, card or event entity. The channel gets *SILENT ALARM: … used the duress code …*. In the log there is `duress_used`. The same code as another code is refused. |
| **104. Duress code during an alarm** | Let an intrusion alarm go off and disarm within 60 seconds with the duress code. | The alarm goes off, the siren stops, only the silent message goes out and **no** *cancelled*. |
| **105. Chime** | Tick *Chime* on a sensor (door contact or motion sensor) and under *Partitions* (form of the partition) choose a siren, switch or lamp. Open the door with the alarm off. Arm the alarm and open the door again. | Off: short tone, no notification, nothing in the log. Armed: no tone. A door that flickers quickly gives only one tone. |
| **106. Vacation and Custom** | Under *Partitions* (form of the partition) switch the modes *Vacation* and *Custom* on and make (or choose) a sensor group that is active in that mode. Arm with the card or with `alarm_control_panel.alarm_arm_vacation` / `alarm_arm_custom_bypass`. | Own exit delay; then state *Vacation* or *Custom* (in Home Assistant `armed_custom_bypass`). Only sensors of the groups of that mode give an alarm. Card and info page show the new mode with a colour of its own. |
| **107. Panel with five buttons** | Flash the panel with the firmware of 0.5.4 and look at the buttons with the alarm disarmed. | Five buttons in one row (smaller text): Home, Away, Night, Vacation, Custom. A user who may use only one mode sees only that button. |
| **108. Alarm memory on the panel** | Let an alarm go off, disarm and look at the main screen of the panel. | Under *Disarmed* it says *Last alarm: 14:03 Front door > Hall* (only if the panel may show sensor names). After *Clear* in the admin panel the line is gone. |
| **109. 24 hour audible and 24 hour silent** | Make a sensor of the type *24 hour audible* and one of *24 hour silent*. Open them with the alarm off. | Audible: siren and notification with cause *24 hour alarm*, also disarmed; arming is refused as long as it is open. Silent: no siren, but a notification to the *Technical* channels and a line in the log; the alarm state does not change. |
| **110. Permanent bypass** | On a sensor tick *Keep the bypass after disarming (permanent)*. Bypass it with the action `vigil_alarm.bypass`, arm and disarm the alarm. Restart Home Assistant. Then remove the bypass yourself with `vigil_alarm.unbypass`. | After disarming and after the restart the sensor is still *bypassed* and gives no alarm; the overview has a card *Permanently bypassed* and card and panel show *Bypassed: …* under Disarmed. Only after removing the bypass is it watching again. A sensor without the tick is active again after disarming. |
| **111. Six languages** | Set the **profile** of Home Assistant (User profile → Language) in turn to Deutsch, Français, Italiano and Español. Open the Vigil panel and, if you have the card, the Vigil card. Then set the **system language** to one of the four and let an alarm go off. | The admin panel and the card are completely in that language (no Dutch or English left-overs, no `{name}` or other braces in the text). The notification is in the system language; the default sensor groups are called for example *Außenhaut* / *Innenbereich*. Another language (for example Portuguese) shows English. Report strange or wrong translations. |
| **112. Language on the touch panel** | Flash the panel with the firmware of 0.5.6. Under *Panels* choose in turn the four new languages for the panel and look at the screen, the keyboard, the sensor list and the info page. | All texts are in the chosen language and fit on the screen (no accents are shown: *Ueberbruecken*, *Desactive*). A panel with older firmware shows English for the new languages. |
| **113. Garage apart from the house** | Under *Partitions* make a partition *Garage* (only *Away*), put the garage door sensor in it and give it a sensor group that is active in *Away*. Arm *Garage* with `alarm_control_panel.alarm_arm_away` and open the front door, then the garage door. | The house stays disarmed and the front door gives no alarm; the garage door gives an alarm, only in the partition *Garage*. The entity *All* is `armed_away` with `status: mixed`; the card shows *Mixed*. |
| **114. Arming and disarming all** | Arm *All* on *Away* while a door of the house is open. Close the door and try again. Then disarm *All*. | First time: refused and **no** partition is armed. Second time: both armed. Disarming disarms both. |
| **115. Fire is for the whole house** | With both partitions armed: open the smoke detector. Then disarm the garage with a code. | One fire alarm for both partitions, one siren and one notification (with the partition name). Disarming in one partition ends the alarm in both. |
| **116. Rights per partition** | Limit a user to *House* (field *Partitions*). With her code try to arm *Garage*, and then the house. | The garage is refused (message *This partition (Garage) may not be used*, in the language of Home Assistant), the house works. |
| **117. Sensor groups per partition** | Make a second partition. Open the tab *Sensor groups*: for the new partition nothing is there yet; choose *Create the default groups*. Give a sensor of the garage one of those groups and then try to give a sensor of the house that same group. | There is a table per partition. The groups of the garage are called for example *Perimeter (Garage)* and offer only the modes of the garage. The sensor of the house cannot choose the group (it is not in the list). Deleting the partition *Garage* is refused as long as there are sensors or groups in it. |
| **118. Partition in the log** | Arm and disarm *Garage* and open the log. Then let the smoke detector go off. | The lines of arming and disarming have the name *Garage* at *Partition*; the line of the smoke detector has none. Also with one partition there is a name. The CSV has a column `partition`. |
| **119. Partition choice required** | Make a new panel, a new user, siren and notification channel and try to save without choosing partitions. | Saving is refused until you tick partitions or *All partitions*. Existing items with an empty list show *All partitions* ticked. |
| **120. Default partition** | Give a panel two partitions and choose a default partition. Try a default partition outside its partitions. | The form offers only the partitions of the panel and *All*; another choice is refused. |
| **121. Panel shows the partition** | Open the panel (or the tablet card) with one partition and with several. | At the top is *Vigil Alarm* with the logo; the partition name or *All* is always visible, also with one partition (*only this partition*). With several partitions there is a row of buttons. |
| **122. Switching and All** | On the panel choose another partition, and then *All*. Arm and disarm. | State, modes and sensors follow the chosen partition; *All* arms all partitions (all or nothing); the state *Mixed* shows *Disarm* and the mode buttons. |
| **123. Jumping back** | In *Settings → Panel screen* set the return time to 30 seconds, switch partition and touch nothing for 30 seconds. Then set the time to 0. | The panel jumps back to the default partition; at 0 it stays. |
| **124. Watching a number** | Add a sensor of the type *24 hours, silent* on a real temperature sensor (a freezer or a cup of warm water): upper limit just above the current value, time 60 seconds. Warm the sensor, wait. Cool it again. Then try the same with the voltage of the power sensor: lower limit just under the mains voltage, time 60 seconds, and switch the power off for two minutes. Also try `unavailable` (unplug the sensor). | After the time the sensor is open, the *Technical* channels get a message and the log has `technical_alarm_started`; the alarm state does not change. Back within the limits it is closed at once (`technical_alarm_ended`). A short peak shorter than the time gives nothing. An unavailable sensor follows the choice for unavailable sensors. |
| **125. Handler report** | Make an automation from the blueprint *Run your own actions* with the event `technical_alarm_started`, the action *wait* until a helper switch is on, and *Also act in practice mode* on. Cause a technical alarm (for example open a water sensor). Wait ten minutes. Then switch the helper on. | While the automation waits nothing is reported, however long. After the switch the run ends and there is no fault. Open *Settings → Automations* and turn the automation off while it waits: Vigil gives `handler_stalled`, a message to the fault channels, a line in *Ready for use?* and a Repair. Turn it on again and let a run finish: the Repair goes away. |
| **126. Quiet handler test** | On the *Self-test* card press *Test the automations (quiet)* with the blueprints for flash lights and speech in place. | Nothing flashes and nothing is said. After a minute the card says how many answered; the log has `handler_test` and `handler_test_done`. Turn one automation off and test again: it is named as switched off. |
| **127. Weekly test with the real actions** | Switch on *Test the automations that react to the alarm every week* in *Settings → Self-test*, then press *Test with the real actions* (alarm off). | Practice mode is on during the test: the lights flash three times, there is no siren and Vigil sends no messages; speech stays quiet unless you chose *Also act in practice mode*. Afterwards practice mode is off again. With the alarm armed the button gives an error. |
| **128. Practice variable** | Build an automation with the blueprint *Run your own actions* that makes a light flash always and sounds a siren only when `{{ not practice }}`. Start practice mode and let the alarm go off. | The light flashes, the siren stays quiet. Outside practice mode both happen. |
| **129. Four partitions per page** | Give a panel more than four partitions (six, say). Look at the row at the top of the panel and use the arrows. | Four partitions on the first page. On the last page the remaining partitions come first, then *All* directly after them, and the right arrow stays at the far right. *All* is not on the first page. Choosing *All* from another place (the Vigil card) brings its page into view. |
| **130. Blueprints per partition** | In the blueprints *Announce alarm events with speech*, *Run your own actions on alarm events* and *Flash lights during an alarm* choose one partition under *Only for these partitions* (it is required). Cause an alarm in that partition and in another one. | Only the chosen partition speaks, runs the actions and flashes the lights. With more than one partition the speech starts with the partition name (*Name the partition*). Disarming another partition does not put the lights back while the chosen one is still sounding. The quiet handler test (step 126) still reaches all of them. |
| **131. Bypass indicator** | Bypass a sensor with the action `vigil_alarm.bypass`. Look for a switch for it under *Settings, Devices & services*. | There is no bypass switch. `binary_sensor.<sensor>_bypassed` (diagnostic) turns on and off with the bypass; fire and gas sensors have none. After the update from 0.6 the old switches are gone. |
| **132. Tamper contact of a siren** | Add or edit a siren and choose a binary sensor under *Tamper entity*. Open the contact. Rename the siren. Delete the siren. | A sensor "<siren> (tamper)" appears, always watching (also with the alarm off: alarm and message). It follows the new name and disappears with the siren. |

## 7. What you report back

For each test that turns out differently:

- the test number and what you did;
- what you expected and what happened;
- the log lines with `vigil`: **Settings → System → Logs**, search for `vigil`. For more detail put this in `configuration.yaml`:

  ```yaml
  logger:
    default: warning
    logs:
      custom_components.vigil_alarm: debug
  ```
- for forms: a screenshot.

## 8. If it does not work

For an alarm that does something other than you expect, see [My alarm does not do what I expect](troubleshooting.md).

- **"Vigil Alarm" is not in the list:** check the path `config/custom_components/vigil_alarm/manifest.json`, restart fully and refresh the browser. Look in the log for `vigil`.
- **The sidebar shows no "Vigil":** only administrators see it. Hard refresh, restart Home Assistant fully and look in the log for an error from `vigil`. There is no second way to configure; if the panel stays away, send the log line.
- **The panel stays empty or shows "could not be loaded":** the integration is not active (look under *Devices & services* for an error). Refresh the browser.
- **Error when opening the first form (name and basic settings):** usually a JSON or translation error or a version difference. Send the log line.
- **Entities are named differently than in this guide:** the names follow from what you filled in. Check the real names under **Settings → Devices & services → Vigil Alarm**.
- **Test switches disappear after a restart:** use the helpers from the test package, not loose states from the Developer tools.

## 9. Cleaning up

1. Remove the integration: **Settings → Devices & services → Vigil Alarm → ⋮ → Delete**.
2. Remove `custom_components/vigil_alarm` and `packages/vigil_test_package.yaml` from the share **config**, and if needed remove the `packages` lines from `configuration.yaml`.
3. Restart Home Assistant. Switch the Samba add-on off if you no longer need it.
