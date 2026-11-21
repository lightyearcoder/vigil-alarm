"""The tag reader of a panel: a tag held in front of it arms or disarms, with the rights of that panel.

The reader is a small ESPHome device of its own (a PN532 next to the door). It fires the event `esphome.vigil_tag`
with its own name and the number of the tag. Vigil finds the panel that has this reader, finds the user whose tag it
is, and arms (when the alarm is off) or disarms, as that user, with the source of the panel. All the rules of the panel
and of the user (partitions, modes, the right to disarm) hold as they do for a code. The tag number is never logged.

Be honest about what this protects: the number of a Mifare tag is not a secret and can be copied, so a tag is a weaker
proof than a code. That is why disarming with a tag alone is a setting of the reader, and why an unknown tag counts as a
wrong code for the lock.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import CALLBACK_TYPE, Event, callback

from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import CONF_PANEL_ID, CONF_READER_DISARM, CONF_READER_MODE, CONF_TAGS, READER_EVENT
from .errors import VigilError
from .manager_config import SIGNAL_UPDATE

if TYPE_CHECKING:
    from .manager import VigilManager

SAME_TAG_SECONDS = 3  # a tag that stays in front of the reader is one scan, not a switch on and off


def _norm(tag: str) -> str:
    return "".join(ch for ch in str(tag).upper() if ch.isalnum())


class TagReaders:
    def __init__(self, hass, manager: VigilManager) -> None:
        self.hass = hass
        self.manager = manager
        self._unsub: CALLBACK_TYPE | None = None
        self._last: dict[str, tuple[str, float]] = {}  # reader -> (tag, when)
        # reader -> how many scans were refused (only in memory): the state sensor of the reader shows it as an attribute,
        # and the reader flashes red when it goes up.
        self.refused: dict[str, int] = {}

    def _refuse(self, source: str) -> None:
        self.refused[source] = self.refused.get(source, 0) + 1
        async_dispatcher_send(self.hass, SIGNAL_UPDATE.format(self.manager.entry.entry_id))

    def start(self) -> None:
        if self._unsub is None:
            self._unsub = self.hass.bus.async_listen(READER_EVENT, self._on_event)

    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        self._last.clear()

    @callback
    def _on_event(self, event: Event) -> None:
        self.hass.async_create_task(self.async_scan(event.data.get("reader"), event.data.get("tag"), event.data.get("key")))

    def _user_of(self, tag: str):
        wanted = _norm(tag)
        return next(
            (u for u in self.manager.users if wanted and any(_norm(t) == wanted for t in u.data.get(CONF_TAGS) or [])),
            None,
        )

    async def async_scan(self, reader: str | None, tag: str | None, key: str | None = None) -> None:
        manager = self.manager
        panel = manager.panels.for_reader(str(reader or ""))
        tag = str(tag or "").strip()
        if panel is None or not tag:
            return
        source = panel.data[CONF_PANEL_ID]
        try:
            # A reader that has a key must send it, like a panel: the name of the reader is only text, and anyone who can
            # fire an event in Home Assistant could use it. The refusal is logged by the check.
            manager.panels.verify_key(source, None if key is None else str(key), None)
        except VigilError:
            self._refuse(source)
            return
        now = manager._wall()
        previous = self._last.get(source)
        self._last[source] = (tag, now)
        if previous and previous[0] == tag and now - previous[1] < SAME_TAG_SECONDS:
            return
        if manager.lockout.refusal(source):  # a locked panel does not look at tags either
            self._refuse(source)
            return
        user = self._user_of(tag)
        if user is None:
            if locked := manager.lockout.record_failure(source):
                manager.publish_lock(locked, source, "tag")
            manager.publish("tag_rejected", source=source, panel=panel.title)
            self._refuse(source)
            return
        manager.lockout.record_success(source)
        partition = manager.panels.partition_for(source, None)
        parts = list(manager.partitions.values()) if partition == "all" else [manager.partition(partition)]
        active = any(p.engine.state != "disarmed" for p in parts)
        try:
            if active:
                if not panel.data.get(CONF_READER_DISARM, True):
                    manager.publish("panel_refused", source=source, panel=panel.title, action="disarm", reason="tag_disarm")
                    self._refuse(source)
                    return
                await manager.async_disarm(None, source, None, tag_user=user)
            else:
                await manager.async_arm(
                    panel.data.get(CONF_READER_MODE) or manager.panels.allowed_modes(panel)[0], None, source, None,
                    tag_user=user,
                )
        except VigilError:
            self._refuse(source)  # refused (a sensor is open, the user may not): the reason is in the log
