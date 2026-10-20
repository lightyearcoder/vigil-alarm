# Backlog

Ideas for later, in no particular order. Nothing here is promised; an item moves to a release when somebody asks for it.

## Security and trust
- **Stronger panel identity.** The panel key (0.6.6) is a shared secret sent unchanged with every call. A code that changes per call (an HMAC over a counter or the time) would make an overheard call useless. More firmware work, and of limited use while the ESPHome API is encrypted.
- **A code in a blueprint is stored as plain text** in the automation (the user guide says so). A route without a stored code, for example a separate restricted user, would remove that weak spot.
- **Hash chain in the log.** Each line holds the hash of the one before, so a changed or missing part of the log is noticed and the panel can say the log is no longer complete.

## Reliability
- **A test message with proof of delivery.** Vigil checks that a notification service exists, not that the message arrived. Real confirmation needs the phone to answer, for example through an action in the notification.

## Left aside on purpose
- **"All on / all off" for a group of partitions.** Needs a design choice first: what a group is, which mode applies, what happens when one partition cannot arm, and where the button goes (a button on the panel needs new firmware).
- **The test plan in German, French, Italian and Spanish** (English and Dutch exist). Translate when somebody asks.
- **File size.** `vigil-panel.js` (about 1975 lines), `panel.py` (1273) and `manager.py` (1169) are the places where a change gets hard first. Split them (for `vigil-panel.js` one file per tab) when they are touched often again.
- **Tests for the browser side.** The backend is well tested; the panel and the card are mostly not. The Playwright smoke tests used while building (panel, key dialog) live outside the repository and should move into it, with more checks per tab.
- **Arm after closing** (an idea seen in Alarmo). The exit delay ends as soon as the entrance door closes, instead of running its full time. Handy, but it changes the core of arming (what if the door closes with someone still inside, or a sensor flaps), so it needs a design and failure scenarios first.
- **Show only the options that fit the kind of sensor** in the sensor dialog, to keep it simple for new users.
- **Tag reader** (waiting for the hardware choice). Design so far: Vigil listens to the Home Assistant event `tag_scanned` and matches the tag id with the tags already stored on a user (the field exists, and does nothing now). A setting per partition, off by default: *tags off*, *arm only* or *arm and disarm*; the rights are those of the user. Log `tag_used` and `tag_unknown`; unknown tags count towards the lockout like a wrong code; the reader's `device_id` ties it to a panel. No new panel firmware needed; a reader on the Guition panel itself would be a second step. Reader: PN532 (I2C/SPI) is the usual choice; avoid 125 kHz readers. Open question: which mode a tag arms (fixed per partition, or chosen by the tag). A tag id can be copied, so a tag is weaker than a code; say so in the guide.
