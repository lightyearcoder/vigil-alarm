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
- **Splitting `vigil-panel.js` further** (about 1900 lines, one file per tab). Worth doing once the file is touched often again; more frontend tests first.
